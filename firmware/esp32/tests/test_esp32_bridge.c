/******************************************************************************/
/**
 * @file test_esp32_bridge.c
 * @brief Host unit test suite for ESP32 Inter-MCU Protocol & Pedal Bridge.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 ******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "inter_mcu_proto.h"
#include "pedal_bridge.h"

static int s_tests_run = 0;
static int s_tests_passed = 0;

#define RUN_TEST(fn) do { \
    printf("  [RUN] %s...\n", #fn); \
    s_tests_run++; \
    fn(); \
    s_tests_passed++; \
    printf("  [PASS] %s\n", #fn); \
} while(0)

#define ASSERT_TRUE(cond) do { \
    if (!(cond)) { \
        fprintf(stderr, "ASSERTION FAILED at %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        exit(1); \
    } \
} while(0)

#define ASSERT_EQ(a, b) do { \
    if ((a) != (b)) { \
        fprintf(stderr, "ASSERTION FAILED at %s:%d: %s == %s (0x%lX != 0x%lX)\n", \
                __FILE__, __LINE__, #a, #b, (unsigned long)(a), (unsigned long)(b)); \
        exit(1); \
    } \
} while(0)

/* Test 1: CRC-8 CCITT Deterministic Test Vectors */
static void test_crc8_ccitt_vectors(void)
{
    /* Vector 0: empty buffer -> 0x00 */
    ASSERT_EQ(inter_mcu_crc8(NULL, 0), 0x00U);
    uint8_t dummy = 0;
    ASSERT_EQ(inter_mcu_crc8(&dummy, 0), 0x00U);

    /* Vector 1: CMD_HEARTBEAT (0x07), LEN=0 -> [0x07, 0x00] -> CRC = 0x6B */
    const uint8_t vec1[] = {0x07U, 0x00U};
    ASSERT_EQ(inter_mcu_crc8(vec1, sizeof(vec1)), 0x6BU);

    /* Vector 2: CMD_SET_PARAM Overdrive Drive 75% -> [0x01, 0x03, 0x01, 0x01, 0x4B] -> CRC = 0xD0 */
    const uint8_t vec2[] = {0x01U, 0x03U, 0x01U, 0x01U, 0x4BU};
    ASSERT_EQ(inter_mcu_crc8(vec2, sizeof(vec2)), 0xD0U);

    /* Vector 3: CMD_SWITCH_EVENT (SW1 ON) -> [0x04, 0x02, 0x01, 0x01] -> CRC = 0x9C */
    const uint8_t vec3[] = {0x04U, 0x02U, 0x01U, 0x01U};
    ASSERT_EQ(inter_mcu_crc8(vec3, sizeof(vec3)), 0x9CU);

    /* Vector 4: CMD_SET_PARAM Global Volume 80% -> [0x01, 0x03, 0x00, 0x01, 0x50] -> CRC = 0xFA */
    const uint8_t vec4[] = {0x01U, 0x03U, 0x00U, 0x01U, 0x50U};
    ASSERT_EQ(inter_mcu_crc8(vec4, sizeof(vec4)), 0xFAU);
}

/* Test 2: Frame Building and Complete Roundtrip */
static void test_frame_builder_and_fsm(void)
{
    inter_mcu_fsm_t fsm;
    inter_mcu_fsm_init(&fsm);

    uint8_t frame_buf[INTER_MCU_MAX_FRAME_LEN];
    const uint8_t payload[] = {0x01U, 0x01U, 0x4BU}; /* Overdrive Drive 75 */
    size_t frame_len = inter_mcu_build_frame(INTER_MCU_CMD_SET_PARAM, payload, 3U,
                                             frame_buf, sizeof(frame_buf));

    ASSERT_EQ(frame_len, 8U);
    ASSERT_EQ(frame_buf[0], 0xAAU);
    ASSERT_EQ(frame_buf[1], 0x55U);
    ASSERT_EQ(frame_buf[2], 0x01U);
    ASSERT_EQ(frame_buf[3], 0x03U);
    ASSERT_EQ(frame_buf[4], 0x01U);
    ASSERT_EQ(frame_buf[5], 0x01U);
    ASSERT_EQ(frame_buf[6], 0x4BU);
    ASSERT_EQ(frame_buf[7], 0xD0U);

    /* Feed into FSM */
    uint32_t tick = 1000U;
    bool completed = false;
    for (size_t i = 0; i < frame_len; i++) {
        completed = inter_mcu_fsm_feed_byte(&fsm, frame_buf[i], tick);
        tick += 1U;
    }

    ASSERT_TRUE(completed);
    ASSERT_TRUE(inter_mcu_fsm_has_packet(&fsm));

    inter_mcu_packet_t pkt;
    ASSERT_TRUE(inter_mcu_fsm_pop_packet(&fsm, &pkt));
    ASSERT_EQ(pkt.cmd, INTER_MCU_CMD_SET_PARAM);
    ASSERT_EQ(pkt.length, 3U);
    ASSERT_EQ(pkt.payload[0], 0x01U);
    ASSERT_EQ(pkt.payload[1], 0x01U);
    ASSERT_EQ(pkt.payload[2], 0x4BU);
    ASSERT_TRUE(pkt.is_valid);
}

/* Test 3: RX FSM Timeout with Normal & Wraparound Ticks */
static void test_rx_timeout_and_wraparound(void)
{
    inter_mcu_fsm_t fsm;
    inter_mcu_fsm_init(&fsm);

    /* Feed partial frame at tick 100 */
    inter_mcu_fsm_feed_byte(&fsm, 0xAAU, 100U);
    inter_mcu_fsm_feed_byte(&fsm, 0x55U, 101U);
    inter_mcu_fsm_feed_byte(&fsm, 0x01U, 102U);
    ASSERT_EQ(fsm.state, INTER_MCU_RX_STATE_LEN);
    ASSERT_EQ(fsm.timeouts, 0U);

    /* Next byte arrives at tick 125 (delta = 23ms > 20ms) -> triggers timeout */
    inter_mcu_fsm_feed_byte(&fsm, 0x03U, 125U);
    ASSERT_EQ(fsm.timeouts, 1U);
    /* FSM reset to SYNC1 and since 0x03 != 0xAA, state remains SYNC1 */
    ASSERT_EQ(fsm.state, INTER_MCU_RX_STATE_SYNC1);

    /* Test tick wraparound: tick 0xFFFFFFF5 to 0x00000010 (delta = 27ms > 20ms) */
    inter_mcu_fsm_feed_byte(&fsm, 0xAAU, 0xFFFFFFF0U);
    inter_mcu_fsm_feed_byte(&fsm, 0x55U, 0xFFFFFFF5U);
    ASSERT_EQ(fsm.state, INTER_MCU_RX_STATE_CMD);

    /* Next byte arrives after 32-bit tick rollover */
    inter_mcu_fsm_feed_byte(&fsm, 0x07U, 0x00000010U);
    ASSERT_EQ(fsm.timeouts, 2U);
    ASSERT_EQ(fsm.state, INTER_MCU_RX_STATE_SYNC1);
}

/* Test 4: CRC Corruption Rejection and Immediate Recovery */
static void test_crc_corruption_recovery(void)
{
    inter_mcu_fsm_t fsm;
    inter_mcu_fsm_init(&fsm);

    /* Heartbeat with bad CRC: 0xAA, 0x55, 0x07, 0x00, BAD_CRC(0xFF) */
    const uint8_t corrupted[] = {0xAAU, 0x55U, 0x07U, 0x00U, 0xFFU};
    uint32_t tick = 500U;
    for (size_t i = 0; i < sizeof(corrupted); i++) {
        inter_mcu_fsm_feed_byte(&fsm, corrupted[i], tick++);
    }

    ASSERT_EQ(fsm.crc_errors, 1U);
    ASSERT_EQ(fsm.packets_received, 0U);
    ASSERT_TRUE(!inter_mcu_fsm_has_packet(&fsm));

    /* Immediately send valid heartbeat frame: CRC = 0x6B */
    const uint8_t valid[] = {0xAAU, 0x55U, 0x07U, 0x00U, 0x6BU};
    for (size_t i = 0; i < sizeof(valid); i++) {
        inter_mcu_fsm_feed_byte(&fsm, valid[i], tick++);
    }

    ASSERT_EQ(fsm.crc_errors, 1U);
    ASSERT_EQ(fsm.packets_received, 1U);
    ASSERT_TRUE(inter_mcu_fsm_has_packet(&fsm));

    inter_mcu_packet_t pkt;
    ASSERT_TRUE(inter_mcu_fsm_pop_packet(&fsm, &pkt));
    ASSERT_EQ(pkt.cmd, INTER_MCU_CMD_HEARTBEAT);
    ASSERT_EQ(pkt.length, 0U);
}

/* Test 5: Boundary Conditions (64 vs 65 Bytes Payload) */
static void test_payload_bounds_64_and_65(void)
{
    inter_mcu_fsm_t fsm;
    inter_mcu_fsm_init(&fsm);

    /* 64-byte payload (maximum valid) */
    uint8_t payload64[64];
    for (int i = 0; i < 64; i++) {
        payload64[i] = (uint8_t)(i + 1);
    }

    uint8_t frame64[INTER_MCU_MAX_FRAME_LEN];
    size_t frame_len = inter_mcu_build_frame(0x01U, payload64, 64U, frame64, sizeof(frame64));
    ASSERT_EQ(frame_len, 69U);

    uint32_t tick = 1000U;
    for (size_t i = 0; i < frame_len; i++) {
        inter_mcu_fsm_feed_byte(&fsm, frame64[i], tick++);
    }

    ASSERT_EQ(fsm.packets_received, 1U);
    ASSERT_EQ(fsm.length_errors, 0U);
    ASSERT_TRUE(inter_mcu_fsm_has_packet(&fsm));

    inter_mcu_packet_t pkt;
    ASSERT_TRUE(inter_mcu_fsm_pop_packet(&fsm, &pkt));
    ASSERT_EQ(pkt.length, 64U);
    ASSERT_EQ(pkt.payload[0], 1U);
    ASSERT_EQ(pkt.payload[63], 64U);

    /* 65-byte length (out of bounds -> must be rejected) */
    ASSERT_EQ(inter_mcu_build_frame(0x01U, payload64, 65U, frame64, sizeof(frame64)), 0U);

    /* Simulate rogue packet with length byte = 65 */
    inter_mcu_fsm_feed_byte(&fsm, 0xAAU, tick++);
    inter_mcu_fsm_feed_byte(&fsm, 0x55U, tick++);
    inter_mcu_fsm_feed_byte(&fsm, 0x01U, tick++);
    inter_mcu_fsm_feed_byte(&fsm, 65U, tick++);

    ASSERT_EQ(fsm.length_errors, 1U);
    ASSERT_EQ(fsm.state, INTER_MCU_RX_STATE_SYNC1);
}

/* Test 6: Delay LE uint16 Encoding / Decoding */
static void test_delay_le_u16_encoding(void)
{
    uint8_t frame_buf[INTER_MCU_MAX_FRAME_LEN];

    /* Test 500 ms (0x01F4) -> byte 2: 0xF4, byte 3: 0x01 */
    size_t len = pedal_bridge_encode_set_param_u16(INTER_MCU_MODULE_DELAY,
                                                   INTER_MCU_PARAM_DELAY_TIME,
                                                   500U, frame_buf, sizeof(frame_buf));
    ASSERT_EQ(len, 9U);
    ASSERT_EQ(frame_buf[2], INTER_MCU_CMD_SET_PARAM);
    ASSERT_EQ(frame_buf[3], 4U); /* Length = 4 */
    ASSERT_EQ(frame_buf[4], INTER_MCU_MODULE_DELAY);
    ASSERT_EQ(frame_buf[5], INTER_MCU_PARAM_DELAY_TIME);
    ASSERT_EQ(frame_buf[6], 0xF4U); /* LSB */
    ASSERT_EQ(frame_buf[7], 0x01U); /* MSB */

    /* Verify CRC calculation on this frame */
    uint8_t expected_crc = inter_mcu_crc8(&frame_buf[2], 6U);
    ASSERT_EQ(frame_buf[8], expected_crc);

    /* Test 1000 ms (0x03E8) -> byte 2: 0xE8, byte 3: 0x03 */
    len = pedal_bridge_encode_set_param_u16(INTER_MCU_MODULE_DELAY,
                                            INTER_MCU_PARAM_DELAY_TIME,
                                            1000U, frame_buf, sizeof(frame_buf));
    ASSERT_EQ(frame_buf[6], 0xE8U);
    ASSERT_EQ(frame_buf[7], 0x03U);

    /* Parse back via FSM */
    inter_mcu_fsm_t fsm;
    inter_mcu_fsm_init(&fsm);
    for (size_t i = 0; i < len; i++) {
        inter_mcu_fsm_feed_byte(&fsm, frame_buf[i], (uint32_t)i);
    }
    inter_mcu_packet_t pkt;
    ASSERT_TRUE(inter_mcu_fsm_pop_packet(&fsm, &pkt));
    uint16_t time_ms = (uint16_t)pkt.payload[2] | ((uint16_t)pkt.payload[3] << 8U);
    ASSERT_EQ(time_ms, 1000U);
}

/* Test 7: Hardware Master Gate Synchronization (SW4 + Remote Mute) */
static void test_hardware_master_gate_sync(void)
{
    pedal_state_t state;
    pedal_bridge_state_init(&state);

    /* Baseline: transport ready, physical SW4 false, remote mute false -> unmuted */
    ASSERT_TRUE(!state.sw4);
    ASSERT_TRUE(!state.remote_mute);
    ASSERT_TRUE(!state.effective_mute);

    /* Physical switch SW4 pressed (Event: SW4 = 1) */
    inter_mcu_packet_t sw4_on = {
        .cmd = INTER_MCU_CMD_SWITCH_EVENT,
        .length = 2U,
        .payload = {INTER_MCU_SWITCH_SW4, 1U},
        .is_valid = true
    };
    pedal_bridge_handle_packet(&state, &sw4_on, 100U);
    ASSERT_TRUE(state.sw4);
    ASSERT_TRUE(state.effective_mute); /* Muted by physical hardware switch */

    /* Physical switch SW4 released (Event: SW4 = 0) */
    inter_mcu_packet_t sw4_off = {
        .cmd = INTER_MCU_CMD_SWITCH_EVENT,
        .length = 2U,
        .payload = {INTER_MCU_SWITCH_SW4, 0U},
        .is_valid = true
    };
    pedal_bridge_handle_packet(&state, &sw4_off, 200U);
    ASSERT_TRUE(!state.sw4);
    ASSERT_TRUE(!state.effective_mute); /* Unmuted */

    /* Remote mute activated via app/MQTT */
    uint8_t out_frame[INTER_MCU_MAX_FRAME_LEN];
    int rc = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"mute\": 1}", out_frame, sizeof(out_frame));
    ASSERT_TRUE(rc > 0);
    ASSERT_TRUE(state.remote_mute);
    ASSERT_TRUE(state.effective_mute); /* Muted remotely */

    /* Physical SW4 pressed while remote mute is also true */
    pedal_bridge_handle_packet(&state, &sw4_on, 300U);
    ASSERT_TRUE(state.sw4);
    ASSERT_TRUE(state.effective_mute);

    /* Remote mute cleared, but physical SW4 is still active -> Hardware Gate MUST stay muted! */
    rc = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"mute\": 0}", out_frame, sizeof(out_frame));
    ASSERT_TRUE(rc > 0);
    ASSERT_TRUE(!state.remote_mute);
    ASSERT_TRUE(state.sw4);
    ASSERT_TRUE(state.effective_mute); /* Still muted because SW4 is active! */

    /* Finally release physical SW4 -> effective mute drops */
    pedal_bridge_handle_packet(&state, &sw4_off, 400U);
    ASSERT_TRUE(!state.sw4);
    ASSERT_TRUE(!state.effective_mute);

    /* Test Transport Gate: transport not ready forces mute regardless of switches */
    state.transport_ready = false;
    pedal_bridge_update_effective_mute(&state);
    ASSERT_TRUE(state.effective_mute);

    state.transport_ready = true;
    pedal_bridge_update_effective_mute(&state);
    ASSERT_TRUE(!state.effective_mute);
}

/* Test 8: State Report Handling and Switch Events for Effects */
static void test_state_report_and_effects_switches(void)
{
    pedal_state_t state;
    pedal_bridge_state_init(&state);

    /* Simulate STATE_REPORT from STM32: [sw1=1, sw2=0, sw3=1, sw4=0, masterVol=92%] */
    inter_mcu_packet_t report = {
        .cmd = INTER_MCU_CMD_STATE_REPORT,
        .length = 5U,
        .payload = {1U, 0U, 1U, 0U, 92U},
        .is_valid = true
    };
    pedal_bridge_handle_packet(&state, &report, 1000U);

    ASSERT_TRUE(state.sw1);
    ASSERT_TRUE(!state.sw2);
    ASSERT_TRUE(state.sw3);
    ASSERT_TRUE(!state.sw4);
    ASSERT_TRUE(state.overdrive.enabled);
    ASSERT_TRUE(!state.equalizer.enabled);
    ASSERT_TRUE(state.delay.enabled);
    ASSERT_EQ(state.master_volume, 92U);
    ASSERT_TRUE(!state.effective_mute);
    ASSERT_EQ(state.state_reports_count, 1U);

    /* Switch event for SW2 (Equalizer ON) */
    inter_mcu_packet_t sw2_event = {
        .cmd = INTER_MCU_CMD_SWITCH_EVENT,
        .length = 2U,
        .payload = {INTER_MCU_SWITCH_SW2, 1U},
        .is_valid = true
    };
    pedal_bridge_handle_packet(&state, &sw2_event, 1050U);
    ASSERT_TRUE(state.sw2);
    ASSERT_TRUE(state.equalizer.enabled);
}

/* Test 9: JSON Serialization and Parsing */
static void test_json_parse_and_serialize(void)
{
    pedal_state_t state;
    pedal_bridge_state_init(&state);

    state.master_volume = 85U;
    state.overdrive.drive = 65U;
    state.equalizer.mid = -4;
    state.delay.time_ms = 420U;

    /* Serialize to JSON */
    char json_buf[512];
    size_t slen = pedal_bridge_serialize_state_json(&state, json_buf, sizeof(json_buf));
    ASSERT_TRUE(slen > 0);
    ASSERT_TRUE(strstr(json_buf, "\"volume\":85") != NULL);
    ASSERT_TRUE(strstr(json_buf, "\"drive\":65") != NULL);
    ASSERT_TRUE(strstr(json_buf, "\"mid\":-4") != NULL);
    ASSERT_TRUE(strstr(json_buf, "\"time_ms\":420") != NULL);
    ASSERT_TRUE(strstr(json_buf, "\"switches\":") != NULL);

    /* Parse structured JSON command: {"module": 1, "param": 1, "value": 75} */
    uint8_t out_frame[INTER_MCU_MAX_FRAME_LEN];
    int flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"module\": 1, \"param\": 1, \"value\": 75}",
                                                    out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 8);
    ASSERT_EQ(out_frame[2], INTER_MCU_CMD_SET_PARAM);
    ASSERT_EQ(out_frame[4], 1U);
    ASSERT_EQ(out_frame[5], 1U);
    ASSERT_EQ(out_frame[6], 75U);
    ASSERT_EQ(out_frame[7], 0xD0U); /* Matches test vector [0x01, 0x03, 0x01, 0x01, 0x4B] */
    ASSERT_EQ(state.overdrive.drive, 75U);

    /* Parse friendly JSON command: {"drive": 80} */
    flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"drive\": 80}", out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 8);
    ASSERT_EQ(out_frame[6], 80U);
    ASSERT_EQ(state.overdrive.drive, 80U);

    /* Parse friendly JSON command: {"bass": 6} */
    flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"bass\": 6}", out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 8);
    ASSERT_EQ(out_frame[4], INTER_MCU_MODULE_EQUALIZER);
    ASSERT_EQ(out_frame[5], INTER_MCU_PARAM_EQUALIZER_LOW);
    ASSERT_EQ((int8_t)out_frame[6], 6);
    ASSERT_EQ(state.equalizer.low, 6);

    /* Parse friendly JSON command: {"delay_time": 600} */
    flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"delay_time\": 600}", out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 9);
    ASSERT_EQ(out_frame[4], INTER_MCU_MODULE_DELAY);
    ASSERT_EQ(out_frame[5], INTER_MCU_PARAM_DELAY_TIME);
    ASSERT_EQ(out_frame[6], (600 & 0xFF));
    ASSERT_EQ(out_frame[7], (600 >> 8));
    ASSERT_EQ(state.delay.time_ms, 600U);

    /* Out-of-range JSON values must clamp symmetrically in state AND encoded wire frame */
    flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"volume\": -25}", out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 8);
    ASSERT_EQ(out_frame[6], 0U);
    ASSERT_EQ(state.master_volume, 0U);

    flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"bass\": -30}", out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 8);
    ASSERT_EQ((int8_t)out_frame[6], -12);
    ASSERT_EQ(state.equalizer.low, -12);

    flen = pedal_bridge_parse_json_cmd_and_apply(&state, "{\"delay_time\": 5000}", out_frame, sizeof(out_frame));
    ASSERT_EQ(flen, 9);
    ASSERT_EQ(out_frame[6], (1000 & 0xFF));
    ASSERT_EQ(out_frame[7], (1000 >> 8));
    ASSERT_EQ(state.delay.time_ms, 1000U);
}

int main(void)
{
    printf("====================================================\n");
    printf("Running ESP32 Inter-MCU Bridge C Host Verification Suite\n");
    printf("====================================================\n");

    RUN_TEST(test_crc8_ccitt_vectors);
    RUN_TEST(test_frame_builder_and_fsm);
    RUN_TEST(test_rx_timeout_and_wraparound);
    RUN_TEST(test_crc_corruption_recovery);
    RUN_TEST(test_payload_bounds_64_and_65);
    RUN_TEST(test_delay_le_u16_encoding);
    RUN_TEST(test_hardware_master_gate_sync);
    RUN_TEST(test_state_report_and_effects_switches);
    RUN_TEST(test_json_parse_and_serialize);

    printf("====================================================\n");
    printf("All %d/%d test suites passed cleanly with 0 errors!\n", s_tests_passed, s_tests_run);
    printf("====================================================\n");

    return 0;
}
