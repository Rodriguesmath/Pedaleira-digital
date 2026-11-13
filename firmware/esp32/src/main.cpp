/******************************************************************************/
/**
 * @file main.cpp
 * @brief Dual-mode Arduino / ESP-IDF entrypoint for ESP32 Inter-MCU Bridge.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 ******************************************************************************/

#include "pedal_config.h"
#include "inter_mcu_proto.h"
#include "pedal_bridge.h"

#include <stdio.h>
#include <string.h>

#if defined(ARDUINO)
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>

static inter_mcu_fsm_t s_fsm;
static pedal_state_t s_pedal_state;
static WiFiClient s_wifi_client;
static PubSubClient s_mqtt_client(s_wifi_client);

static uint32_t s_last_heartbeat_ms = 0;
static uint32_t s_last_state_pub_ms = 0;

static void mqtt_callback(char *topic, byte *payload, unsigned int length)
{
    (void)topic;
    char cmd_json[256];
    if (length >= sizeof(cmd_json)) {
        length = sizeof(cmd_json) - 1U;
    }
    memcpy(cmd_json, payload, length);
    cmd_json[length] = '\0';

    uint8_t tx_frame[INTER_MCU_MAX_FRAME_LEN];
    int frame_len = pedal_bridge_parse_json_cmd_and_apply(&s_pedal_state, cmd_json,
                                                         tx_frame, sizeof(tx_frame));
    if (frame_len > 0) {
        Serial2.write(tx_frame, (size_t)frame_len);
    }
}

static void publish_state_mqtt(void)
{
    if (!s_mqtt_client.connected()) {
        return;
    }
    char json_buf[512];
    size_t len = pedal_bridge_serialize_state_json(&s_pedal_state, json_buf, sizeof(json_buf));
    if (len > 0) {
        s_mqtt_client.publish(CONFIG_MQTT_TOPIC_STATE, json_buf);
    }
}

void setup(void)
{
    Serial.begin(115200);
    Serial.println("[ESP32] Initializing Pedaleira Inter-MCU Bridge...");

    inter_mcu_fsm_init(&s_fsm);
    pedal_bridge_state_init(&s_pedal_state);

    Serial2.begin(CONFIG_PEDAL_UART_BAUD_RATE, SERIAL_8N1,
                  CONFIG_PEDAL_UART_RX_PIN, CONFIG_PEDAL_UART_TX_PIN);

    /* Wi-Fi and MQTT setup */
    if (strlen(CONFIG_WIFI_SSID) > 0) {
        WiFi.mode(WIFI_STA);
        WiFi.begin(CONFIG_WIFI_SSID, CONFIG_WIFI_PASS);
    }

    s_mqtt_client.setServer(CONFIG_MQTT_BROKER_HOST, CONFIG_MQTT_BROKER_PORT);
    s_mqtt_client.setCallback(mqtt_callback);

    /* Initial GET_STATE request to synchronize mirror with STM32 */
    uint8_t tx_frame[INTER_MCU_MAX_FRAME_LEN];
    size_t len = pedal_bridge_encode_get_state(tx_frame, sizeof(tx_frame));
    if (len > 0) {
        Serial2.write(tx_frame, len);
    }

    s_last_heartbeat_ms = millis();
    s_last_state_pub_ms = millis();
    Serial.println("[ESP32] Bridge ready. Waiting for STM32 and MQTT packets.");
}

void loop(void)
{
    uint32_t now = millis();

    /* 1. Ingest UART bytes from STM32 */
    while (Serial2.available() > 0) {
        uint8_t b = (uint8_t)Serial2.read();
        inter_mcu_fsm_feed_byte(&s_fsm, b, now);
    }

    /* 2. Process received packets */
    inter_mcu_packet_t pkt;
    while (inter_mcu_fsm_pop_packet(&s_fsm, &pkt)) {
        bool changed = pedal_bridge_handle_packet(&s_pedal_state, &pkt, now);
        if (changed) {
            publish_state_mqtt();
        }
    }

    /* 3. Maintain MQTT connection */
    if (WiFi.status() == WL_CONNECTED) {
        if (!s_mqtt_client.connected()) {
            if (s_mqtt_client.connect(CONFIG_MQTT_CLIENT_ID)) {
                s_mqtt_client.subscribe(CONFIG_MQTT_TOPIC_CMD);
                publish_state_mqtt();
            }
        } else {
            s_mqtt_client.loop();
        }
    }

    /* 4. Periodic 1000ms Heartbeat to STM32 */
    if ((now - s_last_heartbeat_ms) >= CONFIG_PEDAL_HEARTBEAT_INTERVAL_MS) {
        s_last_heartbeat_ms = now;
        uint8_t tx_frame[INTER_MCU_MAX_FRAME_LEN];
        size_t len = pedal_bridge_encode_heartbeat(tx_frame, sizeof(tx_frame));
        if (len > 0) {
            Serial2.write(tx_frame, len);
        }
    }

    /* 5. Periodic state publication */
    if ((now - s_last_state_pub_ms) >= CONFIG_PEDAL_STATE_PUBLISH_INTERVAL_MS) {
        s_last_state_pub_ms = now;
        publish_state_mqtt();
    }
}

#elif defined(ESP_PLATFORM)
/* Pure ESP-IDF Entrypoint */
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "mqtt_client.h"

static const char *TAG = "PEDAL_BRIDGE";
static inter_mcu_fsm_t s_fsm;
static pedal_state_t s_pedal_state;
static esp_mqtt_client_handle_t s_mqtt_client = NULL;

static uint32_t get_time_ms(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000ULL);
}

static void uart_rx_task(void *pvParameters)
{
    (void)pvParameters;
    uint8_t rx_buf[128];
    uint32_t last_heartbeat = get_time_ms();

    /* Send initial GET_STATE */
    uint8_t tx_frame[INTER_MCU_MAX_FRAME_LEN];
    size_t len = pedal_bridge_encode_get_state(tx_frame, sizeof(tx_frame));
    if (len > 0) {
        uart_write_bytes(CONFIG_PEDAL_UART_NUM, (const char *)tx_frame, len);
    }

    while (1) {
        int rx_len = uart_read_bytes(CONFIG_PEDAL_UART_NUM, rx_buf, sizeof(rx_buf), 20 / portTICK_PERIOD_MS);
        uint32_t now = get_time_ms();

        if (rx_len > 0) {
            for (int i = 0; i < rx_len; i++) {
                inter_mcu_fsm_feed_byte(&s_fsm, rx_buf[i], now);
            }
        }

        inter_mcu_packet_t pkt;
        while (inter_mcu_fsm_pop_packet(&s_fsm, &pkt)) {
            bool state_changed = pedal_bridge_handle_packet(&s_pedal_state, &pkt, now);
            if (state_changed && s_mqtt_client != NULL) {
                char json_buf[512];
                size_t jlen = pedal_bridge_serialize_state_json(&s_pedal_state, json_buf, sizeof(json_buf));
                if (jlen > 0) {
                    esp_mqtt_client_publish(s_mqtt_client, CONFIG_MQTT_TOPIC_STATE, json_buf, 0, 1, 0);
                }
            }
        }

        /* 1000ms Heartbeat */
        if ((now - last_heartbeat) >= CONFIG_PEDAL_HEARTBEAT_INTERVAL_MS) {
            last_heartbeat = now;
            size_t hlen = pedal_bridge_encode_heartbeat(tx_frame, sizeof(tx_frame));
            if (hlen > 0) {
                uart_write_bytes(CONFIG_PEDAL_UART_NUM, (const char *)tx_frame, hlen);
            }
        }
    }
}

extern "C" void app_main(void)
{
    ESP_LOGI(TAG, "Starting ESP32 Inter-MCU Bridge under ESP-IDF...");

    inter_mcu_fsm_init(&s_fsm);
    pedal_bridge_state_init(&s_pedal_state);

    const uart_config_t uart_config = {
        .baud_rate = CONFIG_PEDAL_UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 0,
        .source_clk = UART_SCLK_DEFAULT,
    };

    ESP_ERROR_CHECK(uart_driver_install(CONFIG_PEDAL_UART_NUM, CONFIG_PEDAL_UART_RX_BUF_SIZE * 2,
                                        CONFIG_PEDAL_UART_TX_BUF_SIZE * 2, 0, NULL, 0));
    ESP_ERROR_CHECK(uart_param_config(CONFIG_PEDAL_UART_NUM, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(CONFIG_PEDAL_UART_NUM, CONFIG_PEDAL_UART_TX_PIN,
                                CONFIG_PEDAL_UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));

    xTaskCreate(uart_rx_task, "uart_rx_task", 4096, NULL, 10, NULL);
}

#else
/* Fallback / Mock Entrypoint for Host or Unconfigured Builds */
int main(void)
{
    printf("ESP32 Inter-MCU Bridge application built outside Arduino/ESP-IDF environment.\n");
    return 0;
}
#endif
