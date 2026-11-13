#ifndef PEDAL_BRIDGE_H
#define PEDAL_BRIDGE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "inter_mcu_proto.h"

#ifdef __cplusplus
extern "C" {
#endif

/* DSP Module State Mirror */
typedef struct {
    /* Physical switches state (from STM32 hardware switches SW1..SW4) */
    bool sw1; /* Overdrive physical switch */
    bool sw2; /* Equalizer physical switch */
    bool sw3; /* Delay physical switch */
    bool sw4; /* Master Mute physical switch (true = muted) */

    /* Global settings */
    uint8_t master_volume; /* 0..100 % */
    bool master_bypass;    /* Master DSP bypass */
    bool remote_mute;      /* Remote mute commanded via MQTT/app */
    bool transport_ready;  /* Audio transport ready flag (default: true) */
    bool effective_mute;   /* Hardware Master Gate: remote_mute || sw4 || !transport_ready */

    /* Overdrive parameters */
    struct {
        bool enabled;      /* Active state (mirrored from sw1) */
        uint8_t drive;     /* 0..100 % */
        uint8_t tone;      /* 0..100 % */
        uint8_t level;     /* 0..100 % */
    } overdrive;

    /* 3-Band Equalizer parameters */
    struct {
        bool enabled;      /* Active state (mirrored from sw2) */
        int8_t low;        /* -12..+12 dB */
        int8_t mid;        /* -12..+12 dB */
        int8_t treble;     /* -12..+12 dB */
    } equalizer;

    /* Delay parameters */
    struct {
        bool enabled;      /* Active state (mirrored from sw3) */
        uint16_t time_ms;  /* 20..1000 ms */
        uint8_t feedback;  /* 0..95 % */
        uint8_t mix;       /* 0..100 % */
    } delay;

    /* Diagnostic and protocol telemetry */
    uint32_t last_heartbeat_rx_tick;
    uint32_t last_state_report_rx_tick;
    uint32_t last_ack_rx_tick;
    uint32_t state_reports_count;
    uint32_t switch_events_count;
    uint32_t acks_count;
    uint32_t nacks_count;
    uint32_t heartbeats_count;
} pedal_state_t;

/**
 * @brief Initialize the pedal bridge state mirror to default values.
 */
void pedal_bridge_state_init(pedal_state_t *state);

/**
 * @brief Recalculate effective mute based on Hardware Master Gate rules:
 *        effective_mute = remote_mute || sw4 || !transport_ready.
 */
void pedal_bridge_update_effective_mute(pedal_state_t *state);

/**
 * @brief Process an incoming packet received from STM32 and update the state mirror.
 * @return true if state was modified or packet handled, false otherwise.
 */
bool pedal_bridge_handle_packet(pedal_state_t *state, const inter_mcu_packet_t *pkt, uint32_t current_tick_ms);

/**
 * @brief Apply a single parameter value directly to the state mirror.
 */
void pedal_bridge_apply_param(pedal_state_t *state, uint8_t module, uint8_t param_id, int32_t val);

/* Encoders for commands to STM32 */

/**
 * @brief Encode CMD_GET_STATE request frame.
 */
size_t pedal_bridge_encode_get_state(uint8_t *out_buf, size_t max_buf_len);

/**
 * @brief Encode CMD_HEARTBEAT keep-alive frame.
 */
size_t pedal_bridge_encode_heartbeat(uint8_t *out_buf, size_t max_buf_len);

/**
 * @brief Encode CMD_SET_PARAM with 1-byte uint8 value.
 */
size_t pedal_bridge_encode_set_param_u8(uint8_t module, uint8_t param_id, uint8_t val,
                                        uint8_t *out_buf, size_t max_buf_len);

/**
 * @brief Encode CMD_SET_PARAM with 1-byte int8 value (e.g. EQ gains).
 */
size_t pedal_bridge_encode_set_param_s8(uint8_t module, uint8_t param_id, int8_t val,
                                        uint8_t *out_buf, size_t max_buf_len);

/**
 * @brief Encode CMD_SET_PARAM with 2-byte uint16 Little-Endian value (e.g. Delay time ms).
 */
size_t pedal_bridge_encode_set_param_u16(uint8_t module, uint8_t param_id, uint16_t val,
                                         uint8_t *out_buf, size_t max_buf_len);

/* Zero-heap JSON Serialization & Parsing */

/**
 * @brief Serialize state mirror to JSON string for MQTT publication (pedaleira/state).
 * @return Number of characters written (excluding null terminator), or 0 on error.
 */
size_t pedal_bridge_serialize_state_json(const pedal_state_t *state, char *out_buf, size_t max_buf_len);

/**
 * @brief Parse JSON command string from MQTT (pedaleira/cmd) and generate binary frame for STM32.
 *        Supports {"module":..., "param":..., "value":...} and friendly keys (e.g. {"drive": 80}).
 * @return Length of encoded binary frame, or negative error code (< 0) on failure.
 */
int pedal_bridge_parse_json_cmd(const char *json_str, uint8_t *out_frame_buf, size_t max_frame_len);

/**
 * @brief Parse JSON command string, update local mirror immediately, and encode binary frame.
 * @return Length of encoded binary frame, or negative error code (< 0) on failure.
 */
int pedal_bridge_parse_json_cmd_and_apply(pedal_state_t *state, const char *json_str,
                                          uint8_t *out_frame_buf, size_t max_frame_len);

#ifdef __cplusplus
}
#endif

#endif /* PEDAL_BRIDGE_H */
