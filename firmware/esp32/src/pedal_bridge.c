#include "pedal_bridge.h"
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void pedal_bridge_state_init(pedal_state_t *state)
{
    if (state == NULL) {
        return;
    }
    memset(state, 0, sizeof(pedal_state_t));

    state->sw1 = false;
    state->sw2 = false;
    state->sw3 = false;
    state->sw4 = false;

    state->master_volume = 80U;
    state->master_bypass = false;
    state->remote_mute = false;
    state->transport_ready = true;
    state->effective_mute = false;

    state->overdrive.enabled = false;
    state->overdrive.drive = 50U;
    state->overdrive.tone = 50U;
    state->overdrive.level = 70U;

    state->equalizer.enabled = false;
    state->equalizer.low = 0;
    state->equalizer.mid = 0;
    state->equalizer.treble = 0;

    state->delay.enabled = false;
    state->delay.time_ms = 350U;
    state->delay.feedback = 30U;
    state->delay.mix = 30U;
}

void pedal_bridge_update_effective_mute(pedal_state_t *state)
{
    if (state == NULL) {
        return;
    }
    state->effective_mute = state->remote_mute || state->sw4 || (!state->transport_ready);
}

static int32_t clamp_param_value(uint8_t module, uint8_t param_id, int32_t val)
{
    int32_t lo = 0;
    int32_t hi = 1;

    switch (module) {
        case INTER_MCU_MODULE_GLOBAL:
            if (param_id == INTER_MCU_PARAM_GLOBAL_MASTER_VOLUME) {
                hi = 100;
            }
            return (val < lo) ? lo : ((val > hi) ? hi : val);

        case INTER_MCU_MODULE_OVERDRIVE:
            if (param_id != INTER_MCU_PARAM_OVERDRIVE_ENABLE) {
                hi = 100;
            }
            return (val < lo) ? lo : ((val > hi) ? hi : val);

        case INTER_MCU_MODULE_EQUALIZER:
            if (param_id != INTER_MCU_PARAM_EQUALIZER_ENABLE) {
                lo = -12;
                hi = 12;
            }
            return (val < lo) ? lo : ((val > hi) ? hi : val);

        case INTER_MCU_MODULE_DELAY:
            if (param_id == INTER_MCU_PARAM_DELAY_TIME) {
                lo = 20;
                hi = 1000;
            } else if (param_id == INTER_MCU_PARAM_DELAY_FEEDBACK) {
                hi = 95;
            } else if (param_id == INTER_MCU_PARAM_DELAY_MIX) {
                hi = 100;
            }
            return (val < lo) ? lo : ((val > hi) ? hi : val);

        default:
            return val;
    }
}

void pedal_bridge_apply_param(pedal_state_t *state, uint8_t module, uint8_t param_id, int32_t val)
{
    if (state == NULL) {
        return;
    }

    val = clamp_param_value(module, param_id, val);

    switch (module) {
        case INTER_MCU_MODULE_GLOBAL:
            if (param_id == INTER_MCU_PARAM_GLOBAL_MASTER_VOLUME) {
                state->master_volume = (uint8_t)val;
            } else if (param_id == INTER_MCU_PARAM_GLOBAL_MASTER_BYPASS) {
                state->master_bypass = (val != 0);
            } else if (param_id == INTER_MCU_PARAM_GLOBAL_MASTER_MUTE) {
                state->remote_mute = (val != 0);
                pedal_bridge_update_effective_mute(state);
            }
            break;

        case INTER_MCU_MODULE_OVERDRIVE:
            if (param_id == INTER_MCU_PARAM_OVERDRIVE_ENABLE) {
                state->overdrive.enabled = (val != 0);
            } else if (param_id == INTER_MCU_PARAM_OVERDRIVE_DRIVE) {
                state->overdrive.drive = (uint8_t)val;
            } else if (param_id == INTER_MCU_PARAM_OVERDRIVE_TONE) {
                state->overdrive.tone = (uint8_t)val;
            } else if (param_id == INTER_MCU_PARAM_OVERDRIVE_LEVEL) {
                state->overdrive.level = (uint8_t)val;
            }
            break;

        case INTER_MCU_MODULE_EQUALIZER:
            if (param_id == INTER_MCU_PARAM_EQUALIZER_ENABLE) {
                state->equalizer.enabled = (val != 0);
            } else if (param_id == INTER_MCU_PARAM_EQUALIZER_LOW) {
                state->equalizer.low = (int8_t)val;
            } else if (param_id == INTER_MCU_PARAM_EQUALIZER_MID) {
                state->equalizer.mid = (int8_t)val;
            } else if (param_id == INTER_MCU_PARAM_EQUALIZER_TREBLE) {
                state->equalizer.treble = (int8_t)val;
            }
            break;

        case INTER_MCU_MODULE_DELAY:
            if (param_id == INTER_MCU_PARAM_DELAY_ENABLE) {
                state->delay.enabled = (val != 0);
            } else if (param_id == INTER_MCU_PARAM_DELAY_TIME) {
                state->delay.time_ms = (uint16_t)val;
            } else if (param_id == INTER_MCU_PARAM_DELAY_FEEDBACK) {
                state->delay.feedback = (uint8_t)val;
            } else if (param_id == INTER_MCU_PARAM_DELAY_MIX) {
                state->delay.mix = (uint8_t)val;
            }
            break;

        default:
            break;
    }
}

bool pedal_bridge_handle_packet(pedal_state_t *state, const inter_mcu_packet_t *pkt, uint32_t current_tick_ms)
{
    if (state == NULL || pkt == NULL) {
        return false;
    }

    switch (pkt->cmd) {
        case INTER_MCU_CMD_STATE_REPORT:
            if (pkt->length >= 5U) {
                state->sw1 = (pkt->payload[0] != 0U);
                state->sw2 = (pkt->payload[1] != 0U);
                state->sw3 = (pkt->payload[2] != 0U);
                state->sw4 = (pkt->payload[3] != 0U);

                state->overdrive.enabled = state->sw1;
                state->equalizer.enabled = state->sw2;
                state->delay.enabled = state->sw3;

                pedal_bridge_update_effective_mute(state);
                state->master_volume = pkt->payload[4];

                state->state_reports_count++;
                state->last_state_report_rx_tick = current_tick_ms;
                return true;
            }
            return false;

        case INTER_MCU_CMD_SWITCH_EVENT:
            if (pkt->length >= 2U) {
                uint8_t sw_id = pkt->payload[0];
                bool active = (pkt->payload[1] != 0U);

                switch (sw_id) {
                    case INTER_MCU_SWITCH_SW1:
                        state->sw1 = active;
                        state->overdrive.enabled = active;
                        break;
                    case INTER_MCU_SWITCH_SW2:
                        state->sw2 = active;
                        state->equalizer.enabled = active;
                        break;
                    case INTER_MCU_SWITCH_SW3:
                        state->sw3 = active;
                        state->delay.enabled = active;
                        break;
                    case INTER_MCU_SWITCH_SW4:
                        state->sw4 = active;
                        pedal_bridge_update_effective_mute(state);
                        break;
                    default:
                        break;
                }
                state->switch_events_count++;
                return true;
            }
            return false;

        case INTER_MCU_CMD_ACK:
            state->acks_count++;
            state->last_ack_rx_tick = current_tick_ms;
            return true;

        case INTER_MCU_CMD_NACK:
            state->nacks_count++;
            return true;

        case INTER_MCU_CMD_HEARTBEAT:
            state->heartbeats_count++;
            state->last_heartbeat_rx_tick = current_tick_ms;
            return true;

        default:
            return false;
    }
}

size_t pedal_bridge_encode_get_state(uint8_t *out_buf, size_t max_buf_len)
{
    return inter_mcu_build_frame(INTER_MCU_CMD_GET_STATE, NULL, 0U, out_buf, max_buf_len);
}

size_t pedal_bridge_encode_heartbeat(uint8_t *out_buf, size_t max_buf_len)
{
    return inter_mcu_build_frame(INTER_MCU_CMD_HEARTBEAT, NULL, 0U, out_buf, max_buf_len);
}

size_t pedal_bridge_encode_set_param_u8(uint8_t module, uint8_t param_id, uint8_t val,
                                        uint8_t *out_buf, size_t max_buf_len)
{
    uint8_t payload[3];
    payload[0] = module;
    payload[1] = param_id;
    payload[2] = val;
    return inter_mcu_build_frame(INTER_MCU_CMD_SET_PARAM, payload, 3U, out_buf, max_buf_len);
}

size_t pedal_bridge_encode_set_param_s8(uint8_t module, uint8_t param_id, int8_t val,
                                        uint8_t *out_buf, size_t max_buf_len)
{
    uint8_t payload[3];
    payload[0] = module;
    payload[1] = param_id;
    payload[2] = (uint8_t)val;
    return inter_mcu_build_frame(INTER_MCU_CMD_SET_PARAM, payload, 3U, out_buf, max_buf_len);
}

size_t pedal_bridge_encode_set_param_u16(uint8_t module, uint8_t param_id, uint16_t val,
                                         uint8_t *out_buf, size_t max_buf_len)
{
    uint8_t payload[4];
    payload[0] = module;
    payload[1] = param_id;
    payload[2] = (uint8_t)(val & 0xFFU);
    payload[3] = (uint8_t)((val >> 8U) & 0xFFU);
    return inter_mcu_build_frame(INTER_MCU_CMD_SET_PARAM, payload, 4U, out_buf, max_buf_len);
}

size_t pedal_bridge_serialize_state_json(const pedal_state_t *state, char *out_buf, size_t max_buf_len)
{
    if (state == NULL || out_buf == NULL || max_buf_len == 0U) {
        return 0;
    }

    int written = snprintf(out_buf, max_buf_len,
        "{\"switches\":{\"sw1\":%d,\"sw2\":%d,\"sw3\":%d,\"sw4\":%d},"
        "\"global\":{\"volume\":%u,\"bypass\":%d,\"remote_mute\":%d,\"effective_mute\":%d},"
        "\"overdrive\":{\"enabled\":%d,\"drive\":%u,\"tone\":%u,\"level\":%u},"
        "\"equalizer\":{\"enabled\":%d,\"low\":%d,\"mid\":%d,\"treble\":%d},"
        "\"delay\":{\"enabled\":%d,\"time_ms\":%u,\"feedback\":%u,\"mix\":%u}}",
        state->sw1 ? 1 : 0, state->sw2 ? 1 : 0, state->sw3 ? 1 : 0, state->sw4 ? 1 : 0,
        (unsigned)state->master_volume, state->master_bypass ? 1 : 0,
        state->remote_mute ? 1 : 0, state->effective_mute ? 1 : 0,
        state->overdrive.enabled ? 1 : 0, (unsigned)state->overdrive.drive,
        (unsigned)state->overdrive.tone, (unsigned)state->overdrive.level,
        state->equalizer.enabled ? 1 : 0, (int)state->equalizer.low,
        (int)state->equalizer.mid, (int)state->equalizer.treble,
        state->delay.enabled ? 1 : 0, (unsigned)state->delay.time_ms,
        (unsigned)state->delay.feedback, (unsigned)state->delay.mix);

    if (written <= 0 || (size_t)written >= max_buf_len) {
        return 0;
    }
    return (size_t)written;
}

/* Internal JSON Lexical Helper (Zero-Heap) */
static bool json_find_key(const char *json, const char *key, const char **val_start, size_t *val_len)
{
    if (json == NULL || key == NULL || val_start == NULL || val_len == NULL) {
        return false;
    }

    size_t key_len = strlen(key);
    const char *p = json;

    while (*p != '\0') {
        if (*p == '\"') {
            if (strncmp(p + 1, key, key_len) == 0 && p[1 + key_len] == '\"') {
                const char *q = p + 1 + key_len + 1;
                while (*q != '\0' && (*q == ' ' || *q == '\t' || *q == '\r' || *q == '\n')) {
                    q++;
                }
                if (*q == ':') {
                    q++;
                    while (*q != '\0' && (*q == ' ' || *q == '\t' || *q == '\r' || *q == '\n')) {
                        q++;
                    }
                    if (*q == '\"') {
                        /* String value */
                        q++;
                        *val_start = q;
                        while (*q != '\0' && *q != '\"') {
                            q++;
                        }
                        *val_len = (size_t)(q - *val_start);
                        return true;
                    } else {
                        /* Number / boolean value */
                        *val_start = q;
                        while (*q != '\0' && *q != ',' && *q != '}' &&
                               *q != ' ' && *q != '\t' && *q != '\r' && *q != '\n') {
                            q++;
                        }
                        *val_len = (size_t)(q - *val_start);
                        return true;
                    }
                }
            }
        }
        p++;
    }

    return false;
}

static bool json_get_int(const char *json, const char *key, int32_t *out_val)
{
    const char *val_start = NULL;
    size_t val_len = 0;
    if (!json_find_key(json, key, &val_start, &val_len) || val_len == 0) {
        return false;
    }

    if (*val_start == 't' || *val_start == 'T') {
        *out_val = 1;
        return true;
    }
    if (*val_start == 'f' || *val_start == 'F') {
        *out_val = 0;
        return true;
    }

    char tmp[32];
    if (val_len >= sizeof(tmp)) {
        return false;
    }
    memcpy(tmp, val_start, val_len);
    tmp[val_len] = '\0';

    char *endptr = NULL;
    long v = strtol(tmp, &endptr, 10);
    if (endptr == tmp) {
        return false;
    }
    *out_val = (int32_t)v;
    return true;
}

static bool json_str_equals(const char *val_start, size_t val_len, const char *target)
{
    size_t target_len = strlen(target);
    if (val_len != target_len) {
        return false;
    }
    for (size_t i = 0; i < val_len; i++) {
        if (tolower((unsigned char)val_start[i]) != tolower((unsigned char)target[i])) {
            return false;
        }
    }
    return true;
}

int pedal_bridge_parse_json_cmd_and_apply(pedal_state_t *state, const char *json_str,
                                          uint8_t *out_frame_buf, size_t max_frame_len)
{
    if (json_str == NULL || out_frame_buf == NULL || max_frame_len == 0U) {
        return -1;
    }

    uint8_t module = 0xFFU;
    uint8_t param_id = 0xFFU;
    int32_t val = 0;
    bool is_u16 = false;

    /* 1. Try structured {"module": ..., "param": ..., "value": ...} */
    const char *mod_start = NULL;
    size_t mod_len = 0;
    if (json_find_key(json_str, "module", &mod_start, &mod_len)) {
        if (json_str_equals(mod_start, mod_len, "global")) {
            module = INTER_MCU_MODULE_GLOBAL;
        } else if (json_str_equals(mod_start, mod_len, "overdrive") ||
                   json_str_equals(mod_start, mod_len, "od")) {
            module = INTER_MCU_MODULE_OVERDRIVE;
        } else if (json_str_equals(mod_start, mod_len, "equalizer") ||
                   json_str_equals(mod_start, mod_len, "eq")) {
            module = INTER_MCU_MODULE_EQUALIZER;
        } else if (json_str_equals(mod_start, mod_len, "delay")) {
            module = INTER_MCU_MODULE_DELAY;
        } else {
            int32_t m = 0;
            if (json_get_int(json_str, "module", &m) && m >= 0 && m <= 3) {
                module = (uint8_t)m;
            }
        }

        const char *param_start = NULL;
        size_t param_len = 0;
        if (json_find_key(json_str, "param", &param_start, &param_len)) {
            int32_t p = 0;
            if (json_get_int(json_str, "param", &p) && p >= 0 && p <= 255) {
                param_id = (uint8_t)p;
            } else if (module == INTER_MCU_MODULE_GLOBAL) {
                if (json_str_equals(param_start, param_len, "volume")) param_id = INTER_MCU_PARAM_GLOBAL_MASTER_VOLUME;
                else if (json_str_equals(param_start, param_len, "bypass")) param_id = INTER_MCU_PARAM_GLOBAL_MASTER_BYPASS;
                else if (json_str_equals(param_start, param_len, "mute")) param_id = INTER_MCU_PARAM_GLOBAL_MASTER_MUTE;
            } else if (module == INTER_MCU_MODULE_OVERDRIVE) {
                if (json_str_equals(param_start, param_len, "enable")) param_id = INTER_MCU_PARAM_OVERDRIVE_ENABLE;
                else if (json_str_equals(param_start, param_len, "drive")) param_id = INTER_MCU_PARAM_OVERDRIVE_DRIVE;
                else if (json_str_equals(param_start, param_len, "tone")) param_id = INTER_MCU_PARAM_OVERDRIVE_TONE;
                else if (json_str_equals(param_start, param_len, "level")) param_id = INTER_MCU_PARAM_OVERDRIVE_LEVEL;
            } else if (module == INTER_MCU_MODULE_EQUALIZER) {
                if (json_str_equals(param_start, param_len, "enable")) param_id = INTER_MCU_PARAM_EQUALIZER_ENABLE;
                else if (json_str_equals(param_start, param_len, "low") || json_str_equals(param_start, param_len, "bass")) param_id = INTER_MCU_PARAM_EQUALIZER_LOW;
                else if (json_str_equals(param_start, param_len, "mid")) param_id = INTER_MCU_PARAM_EQUALIZER_MID;
                else if (json_str_equals(param_start, param_len, "treble")) param_id = INTER_MCU_PARAM_EQUALIZER_TREBLE;
            } else if (module == INTER_MCU_MODULE_DELAY) {
                if (json_str_equals(param_start, param_len, "enable")) param_id = INTER_MCU_PARAM_DELAY_ENABLE;
                else if (json_str_equals(param_start, param_len, "time") || json_str_equals(param_start, param_len, "time_ms")) param_id = INTER_MCU_PARAM_DELAY_TIME;
                else if (json_str_equals(param_start, param_len, "feedback")) param_id = INTER_MCU_PARAM_DELAY_FEEDBACK;
                else if (json_str_equals(param_start, param_len, "mix")) param_id = INTER_MCU_PARAM_DELAY_MIX;
            }
        }

        if (!json_get_int(json_str, "value", &val)) {
            return -2;
        }

        if (module == INTER_MCU_MODULE_DELAY && param_id == INTER_MCU_PARAM_DELAY_TIME) {
            is_u16 = true;
        }
    }

    /* 2. Try friendly keys */
    if (module == 0xFFU || param_id == 0xFFU) {
        if (json_get_int(json_str, "volume", &val) || json_get_int(json_str, "master_volume", &val)) {
            module = INTER_MCU_MODULE_GLOBAL;
            param_id = INTER_MCU_PARAM_GLOBAL_MASTER_VOLUME;
        } else if (json_get_int(json_str, "bypass", &val) || json_get_int(json_str, "master_bypass", &val)) {
            module = INTER_MCU_MODULE_GLOBAL;
            param_id = INTER_MCU_PARAM_GLOBAL_MASTER_BYPASS;
        } else if (json_get_int(json_str, "mute", &val) || json_get_int(json_str, "remote_mute", &val)) {
            module = INTER_MCU_MODULE_GLOBAL;
            param_id = INTER_MCU_PARAM_GLOBAL_MASTER_MUTE;
        } else if (json_get_int(json_str, "overdrive_enable", &val) || json_get_int(json_str, "overdrive", &val)) {
            module = INTER_MCU_MODULE_OVERDRIVE;
            param_id = INTER_MCU_PARAM_OVERDRIVE_ENABLE;
        } else if (json_get_int(json_str, "drive", &val) || json_get_int(json_str, "overdrive_drive", &val)) {
            module = INTER_MCU_MODULE_OVERDRIVE;
            param_id = INTER_MCU_PARAM_OVERDRIVE_DRIVE;
        } else if (json_get_int(json_str, "tone", &val) || json_get_int(json_str, "overdrive_tone", &val)) {
            module = INTER_MCU_MODULE_OVERDRIVE;
            param_id = INTER_MCU_PARAM_OVERDRIVE_TONE;
        } else if (json_get_int(json_str, "level", &val) || json_get_int(json_str, "overdrive_level", &val)) {
            module = INTER_MCU_MODULE_OVERDRIVE;
            param_id = INTER_MCU_PARAM_OVERDRIVE_LEVEL;
        } else if (json_get_int(json_str, "equalizer_enable", &val) || json_get_int(json_str, "equalizer", &val)) {
            module = INTER_MCU_MODULE_EQUALIZER;
            param_id = INTER_MCU_PARAM_EQUALIZER_ENABLE;
        } else if (json_get_int(json_str, "low", &val) || json_get_int(json_str, "bass", &val)) {
            module = INTER_MCU_MODULE_EQUALIZER;
            param_id = INTER_MCU_PARAM_EQUALIZER_LOW;
        } else if (json_get_int(json_str, "mid", &val)) {
            module = INTER_MCU_MODULE_EQUALIZER;
            param_id = INTER_MCU_PARAM_EQUALIZER_MID;
        } else if (json_get_int(json_str, "treble", &val)) {
            module = INTER_MCU_MODULE_EQUALIZER;
            param_id = INTER_MCU_PARAM_EQUALIZER_TREBLE;
        } else if (json_get_int(json_str, "delay_enable", &val) || json_get_int(json_str, "delay", &val)) {
            module = INTER_MCU_MODULE_DELAY;
            param_id = INTER_MCU_PARAM_DELAY_ENABLE;
        } else if (json_get_int(json_str, "delay_time", &val) || json_get_int(json_str, "time_ms", &val) ||
                   json_get_int(json_str, "time", &val)) {
            module = INTER_MCU_MODULE_DELAY;
            param_id = INTER_MCU_PARAM_DELAY_TIME;
            is_u16 = true;
        } else if (json_get_int(json_str, "feedback", &val) || json_get_int(json_str, "delay_feedback", &val)) {
            module = INTER_MCU_MODULE_DELAY;
            param_id = INTER_MCU_PARAM_DELAY_FEEDBACK;
        } else if (json_get_int(json_str, "mix", &val) || json_get_int(json_str, "delay_mix", &val)) {
            module = INTER_MCU_MODULE_DELAY;
            param_id = INTER_MCU_PARAM_DELAY_MIX;
        }
    }

    if (module == 0xFFU || param_id == 0xFFU) {
        return -3; /* Unknown command key/format */
    }

    val = clamp_param_value(module, param_id, val);

    if (state != NULL) {
        pedal_bridge_apply_param(state, module, param_id, val);
    }

    size_t frame_len = 0;
    if (is_u16) {
        frame_len = pedal_bridge_encode_set_param_u16(module, param_id, (uint16_t)val,
                                                      out_frame_buf, max_frame_len);
    } else if (module == INTER_MCU_MODULE_EQUALIZER &&
               param_id >= INTER_MCU_PARAM_EQUALIZER_LOW &&
               param_id <= INTER_MCU_PARAM_EQUALIZER_TREBLE) {
        frame_len = pedal_bridge_encode_set_param_s8(module, param_id, (int8_t)val,
                                                     out_frame_buf, max_frame_len);
    } else {
        frame_len = pedal_bridge_encode_set_param_u8(module, param_id, (uint8_t)val,
                                                     out_frame_buf, max_frame_len);
    }

    if (frame_len == 0) {
        return -4; /* Buffer too small or encode failed */
    }

    return (int)frame_len;
}

int pedal_bridge_parse_json_cmd(const char *json_str, uint8_t *out_frame_buf, size_t max_frame_len)
{
    return pedal_bridge_parse_json_cmd_and_apply(NULL, json_str, out_frame_buf, max_frame_len);
}
