#include "inter_mcu_proto.h"
#include <string.h>

uint8_t inter_mcu_crc8(const uint8_t *data, size_t length)
{
    uint8_t crc = 0x00U;
    if (data == NULL) {
        return 0x00U;
    }

    for (size_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8U; bit++) {
            if ((crc & 0x80U) != 0U) {
                crc = (uint8_t)((crc << 1U) ^ INTER_MCU_CRC_POLY);
            } else {
                crc = (uint8_t)(crc << 1U);
            }
        }
    }
    return crc;
}

void inter_mcu_fsm_init(inter_mcu_fsm_t *fsm)
{
    if (fsm == NULL) {
        return;
    }
    memset(fsm, 0, sizeof(inter_mcu_fsm_t));
    fsm->state = INTER_MCU_RX_STATE_SYNC1;
}

void inter_mcu_fsm_reset(inter_mcu_fsm_t *fsm)
{
    if (fsm == NULL) {
        return;
    }
    fsm->state = INTER_MCU_RX_STATE_SYNC1;
    fsm->current_cmd = 0U;
    fsm->current_len = 0U;
    fsm->payload_index = 0U;
}

void inter_mcu_fsm_check_timeout(inter_mcu_fsm_t *fsm, uint32_t current_tick_ms)
{
    if (fsm == NULL) {
        return;
    }
    if (fsm->state != INTER_MCU_RX_STATE_SYNC1) {
        uint32_t delta = current_tick_ms - fsm->last_byte_tick_ms;
        if (delta >= INTER_MCU_RX_TIMEOUT_MS) {
            fsm->state = INTER_MCU_RX_STATE_SYNC1;
            fsm->timeouts++;
        }
    }
}

bool inter_mcu_fsm_feed_byte(inter_mcu_fsm_t *fsm, uint8_t byte, uint32_t current_tick_ms)
{
    if (fsm == NULL) {
        return false;
    }

    if (fsm->state != INTER_MCU_RX_STATE_SYNC1) {
        uint32_t delta = current_tick_ms - fsm->last_byte_tick_ms;
        if (delta >= INTER_MCU_RX_TIMEOUT_MS) {
            fsm->state = INTER_MCU_RX_STATE_SYNC1;
            fsm->timeouts++;
        }
    }
    fsm->last_byte_tick_ms = current_tick_ms;

    bool packet_queued = false;

    switch (fsm->state) {
        case INTER_MCU_RX_STATE_SYNC1:
            if (byte == INTER_MCU_SYNC1) {
                fsm->state = INTER_MCU_RX_STATE_SYNC2;
            }
            break;

        case INTER_MCU_RX_STATE_SYNC2:
            if (byte == INTER_MCU_SYNC2) {
                fsm->state = INTER_MCU_RX_STATE_CMD;
            } else if (byte == INTER_MCU_SYNC1) {
                /* Preserve SYNC2 state on repeated 0xAA (e.g. 0xAA 0xAA 0x55) */
                fsm->state = INTER_MCU_RX_STATE_SYNC2;
            } else {
                fsm->state = INTER_MCU_RX_STATE_SYNC1;
            }
            break;

        case INTER_MCU_RX_STATE_CMD:
            fsm->current_cmd = byte;
            fsm->state = INTER_MCU_RX_STATE_LEN;
            break;

        case INTER_MCU_RX_STATE_LEN:
            fsm->current_len = byte;
            fsm->payload_index = 0U;

            if (byte > INTER_MCU_MAX_PAYLOAD) {
                fsm->length_errors++;
                fsm->state = INTER_MCU_RX_STATE_SYNC1;
            } else if (byte == 0U) {
                fsm->state = INTER_MCU_RX_STATE_CRC;
            } else {
                fsm->state = INTER_MCU_RX_STATE_PAYLOAD;
            }
            break;

        case INTER_MCU_RX_STATE_PAYLOAD:
            fsm->payload_buffer[fsm->payload_index] = byte;
            fsm->payload_index++;

            if (fsm->payload_index >= fsm->current_len) {
                fsm->state = INTER_MCU_RX_STATE_CRC;
            }
            break;

        case INTER_MCU_RX_STATE_CRC: {
            uint8_t crc_buf[INTER_MCU_MAX_PAYLOAD + 2U];
            crc_buf[0] = fsm->current_cmd;
            crc_buf[1] = fsm->current_len;
            for (uint8_t i = 0; i < fsm->current_len; i++) {
                crc_buf[i + 2U] = fsm->payload_buffer[i];
            }

            uint8_t expected_crc = inter_mcu_crc8(crc_buf, (size_t)fsm->current_len + 2U);
            if (expected_crc == byte) {
                if (fsm->queue_count < INTER_MCU_QUEUE_SIZE) {
                    inter_mcu_packet_t *pkt = &fsm->queue[fsm->queue_head];
                    pkt->cmd = fsm->current_cmd;
                    pkt->length = fsm->current_len;
                    for (uint8_t i = 0; i < fsm->current_len; i++) {
                        pkt->payload[i] = fsm->payload_buffer[i];
                    }
                    pkt->is_valid = true;
                    fsm->queue_head = (uint8_t)((fsm->queue_head + 1U) % INTER_MCU_QUEUE_SIZE);
                    fsm->queue_count++;
                    fsm->packets_received++;
                    packet_queued = true;
                } else {
                    fsm->packet_drops++;
                }
            } else {
                fsm->crc_errors++;
            }

            fsm->state = INTER_MCU_RX_STATE_SYNC1;
            break;
        }

        default:
            fsm->state = INTER_MCU_RX_STATE_SYNC1;
            break;
    }

    return packet_queued;
}

bool inter_mcu_fsm_has_packet(const inter_mcu_fsm_t *fsm)
{
    if (fsm == NULL) {
        return false;
    }
    return (fsm->queue_count > 0U);
}

bool inter_mcu_fsm_pop_packet(inter_mcu_fsm_t *fsm, inter_mcu_packet_t *out_pkt)
{
    if (fsm == NULL || out_pkt == NULL || fsm->queue_count == 0U) {
        return false;
    }

    *out_pkt = fsm->queue[fsm->queue_tail];
    fsm->queue_tail = (uint8_t)((fsm->queue_tail + 1U) % INTER_MCU_QUEUE_SIZE);
    fsm->queue_count--;
    return true;
}

size_t inter_mcu_build_frame(uint8_t cmd, const uint8_t *payload, uint8_t length,
                             uint8_t *out_buf, size_t max_buf_len)
{
    if (length > INTER_MCU_MAX_PAYLOAD) {
        return 0;
    }
    if (length > 0U && payload == NULL) {
        return 0;
    }

    size_t total_len = (size_t)length + INTER_MCU_FRAME_OVERHEAD;
    if (out_buf == NULL || max_buf_len < total_len) {
        return 0;
    }

    out_buf[0] = INTER_MCU_SYNC1;
    out_buf[1] = INTER_MCU_SYNC2;
    out_buf[2] = cmd;
    out_buf[3] = length;

    for (uint8_t i = 0; i < length; i++) {
        out_buf[4U + i] = payload[i];
    }

    uint8_t crc = inter_mcu_crc8(&out_buf[2], (size_t)length + 2U);
    out_buf[4U + length] = crc;

    return total_len;
}
