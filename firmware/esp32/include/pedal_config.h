#ifndef PEDAL_CONFIG_H
#define PEDAL_CONFIG_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Inter-MCU Hardware Interface (UART2) */
#define CONFIG_PEDAL_UART_NUM                   2
#define CONFIG_PEDAL_UART_BAUD_RATE             115200
#define CONFIG_PEDAL_UART_TX_PIN                17      /* ESP32 TX2 -> STM32 PD9 RX */
#define CONFIG_PEDAL_UART_RX_PIN                16      /* ESP32 RX2 <- STM32 PD8 TX */
#define CONFIG_PEDAL_UART_RX_BUF_SIZE           512
#define CONFIG_PEDAL_UART_TX_BUF_SIZE           512

/* Timings */
#define CONFIG_PEDAL_HEARTBEAT_INTERVAL_MS      1000U
#define CONFIG_PEDAL_STATE_PUBLISH_INTERVAL_MS  5000U
#define CONFIG_PEDAL_UART_TIMEOUT_MS            20U

/* Wi-Fi Configuration Defaults (Placeholder - Overridable via build flags) */
#ifndef CONFIG_WIFI_SSID
#define CONFIG_WIFI_SSID                        "Pedaleira_WiFi"
#endif

#ifndef CONFIG_WIFI_PASS
#define CONFIG_WIFI_PASS                        ""
#endif

/* MQTT Broker Configuration Defaults (Placeholder - Overridable via build flags) */
#ifndef CONFIG_MQTT_BROKER_HOST
#define CONFIG_MQTT_BROKER_HOST                 "192.168.1.100"
#endif

#ifndef CONFIG_MQTT_BROKER_PORT
#define CONFIG_MQTT_BROKER_PORT                 1883
#endif

#ifndef CONFIG_MQTT_BROKER_URI
#define CONFIG_MQTT_BROKER_URI                  "mqtt://" CONFIG_MQTT_BROKER_HOST ":1883"
#endif

#ifndef CONFIG_MQTT_CLIENT_ID
#define CONFIG_MQTT_CLIENT_ID                   "pedaleira-esp32-bridge"
#endif

#ifndef CONFIG_MQTT_TOPIC_PREFIX
#define CONFIG_MQTT_TOPIC_PREFIX                "pedaleira"
#endif

/* Standard MQTT Topics */
#define CONFIG_MQTT_TOPIC_STATE                 CONFIG_MQTT_TOPIC_PREFIX "/state"
#define CONFIG_MQTT_TOPIC_CMD                   CONFIG_MQTT_TOPIC_PREFIX "/cmd"
#define CONFIG_MQTT_TOPIC_SWITCHES              CONFIG_MQTT_TOPIC_PREFIX "/switches"
#define CONFIG_MQTT_TOPIC_TELEMETRY             CONFIG_MQTT_TOPIC_PREFIX "/telemetry"

#ifdef __cplusplus
}
#endif

#endif /* PEDAL_CONFIG_H */
