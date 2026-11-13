#ifndef INTER_MCU_PROTO_H
#define INTER_MCU_PROTO_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Framing and Protocol Constants */
#define INTER_MCU_SYNC1                 0xAAU
#define INTER_MCU_SYNC2                 0x55U
#define INTER_MCU_MAX_PAYLOAD           64U
#define INTER_MCU_FRAME_OVERHEAD        5U  /* SYNC1 + SYNC2 + CMD + LEN + CRC */
#define INTER_MCU_MAX_FRAME_LEN         (INTER_MCU_MAX_PAYLOAD + INTER_MCU_FRAME_OVERHEAD)
#define INTER_MCU_CRC_POLY              0x07U
#define INTER_MCU_RX_TIMEOUT_MS         20U
#define INTER_MCU_QUEUE_SIZE            8U

/* Command IDs */
typedef enum {
    INTER_MCU_CMD_SET_PARAM             = 0x01,
    INTER_MCU_CMD_GET_STATE             = 0x02,
    INTER_MCU_CMD_STATE_REPORT          = 0x03,
    INTER_MCU_CMD_SWITCH_EVENT          = 0x04,
    INTER_MCU_CMD_ACK                   = 0x05,
    INTER_MCU_CMD_NACK                  = 0x06,
    INTER_MCU_CMD_HEARTBEAT             = 0x07
} inter_mcu_cmd_t;

/* Module IDs */
typedef enum {
    INTER_MCU_MODULE_GLOBAL             = 0x00,
    INTER_MCU_MODULE_OVERDRIVE          = 0x01,
    INTER_MCU_MODULE_EQUALIZER          = 0x02,
    INTER_MCU_MODULE_DELAY              = 0x03
} inter_mcu_module_t;

/* Global Module Parameters */
typedef enum {
    INTER_MCU_PARAM_GLOBAL_MASTER_VOLUME = 0x01,
    INTER_MCU_PARAM_GLOBAL_MASTER_BYPASS = 0x02,
    INTER_MCU_PARAM_GLOBAL_MASTER_MUTE   = 0x03
} inter_mcu_param_global_t;

/* Overdrive Module Parameters */
typedef enum {
    INTER_MCU_PARAM_OVERDRIVE_ENABLE    = 0x00,
    INTER_MCU_PARAM_OVERDRIVE_DRIVE     = 0x01,
    INTER_MCU_PARAM_OVERDRIVE_TONE      = 0x02,
    INTER_MCU_PARAM_OVERDRIVE_LEVEL     = 0x03
} inter_mcu_param_overdrive_t;

/* Equalizer Module Parameters */
typedef enum {
    INTER_MCU_PARAM_EQUALIZER_ENABLE    = 0x00,
    INTER_MCU_PARAM_EQUALIZER_LOW       = 0x01,
    INTER_MCU_PARAM_EQUALIZER_MID       = 0x02,
    INTER_MCU_PARAM_EQUALIZER_TREBLE    = 0x03
} inter_mcu_param_equalizer_t;

/* Delay Module Parameters */
typedef enum {
    INTER_MCU_PARAM_DELAY_ENABLE        = 0x00,
    INTER_MCU_PARAM_DELAY_TIME          = 0x01,
    INTER_MCU_PARAM_DELAY_FEEDBACK      = 0x02,
    INTER_MCU_PARAM_DELAY_MIX           = 0x03
} inter_mcu_param_delay_t;

/* Switch IDs */
typedef enum {
    INTER_MCU_SWITCH_SW1                = 1,
    INTER_MCU_SWITCH_SW2                = 2,
    INTER_MCU_SWITCH_SW3                = 3,
    INTER_MCU_SWITCH_SW4                = 4
} inter_mcu_switch_id_t;

/* Packet Struct */
typedef struct {
    uint8_t cmd;
    uint8_t length;
    uint8_t payload[INTER_MCU_MAX_PAYLOAD];
    bool is_valid;
} inter_mcu_packet_t;

/* RX FSM State Enum */
typedef enum {
    INTER_MCU_RX_STATE_SYNC1            = 0,
    INTER_MCU_RX_STATE_SYNC2,
    INTER_MCU_RX_STATE_CMD,
    INTER_MCU_RX_STATE_LEN,
    INTER_MCU_RX_STATE_PAYLOAD,
    INTER_MCU_RX_STATE_CRC
} inter_mcu_rx_state_t;

/* RX FSM Context */
typedef struct {
    inter_mcu_rx_state_t state;
    uint8_t current_cmd;
    uint8_t current_len;
    uint8_t payload_index;
    uint8_t payload_buffer[INTER_MCU_MAX_PAYLOAD];
    uint32_t last_byte_tick_ms;

    inter_mcu_packet_t queue[INTER_MCU_QUEUE_SIZE];
    uint8_t queue_head;
    uint8_t queue_tail;
    uint8_t queue_count;

    uint32_t packets_received;
    uint32_t packets_transmitted;
    uint32_t crc_errors;
    uint32_t length_errors;
    uint32_t packet_drops;
    uint32_t timeouts;
} inter_mcu_fsm_t;

/* Public Protocol API */

/**
 * @brief Calculate CRC-8 CCITT (poly 0x07, init 0x00) over data buffer.
 */
uint8_t inter_mcu_crc8(const uint8_t *data, size_t length);

/**
 * @brief Initialize or re-initialize FSM context and queues.
 */
void inter_mcu_fsm_init(inter_mcu_fsm_t *fsm);

/**
 * @brief Reset RX FSM state to SYNC1 without clearing queue or telemetry counters.
 */
void inter_mcu_fsm_reset(inter_mcu_fsm_t *fsm);

/**
 * @brief Check and enforce RX timeout (20ms) against current system tick.
 */
void inter_mcu_fsm_check_timeout(inter_mcu_fsm_t *fsm, uint32_t current_tick_ms);

/**
 * @brief Feed a single received byte into the RX FSM.
 * @return true if a complete and valid packet was successfully received and queued.
 */
bool inter_mcu_fsm_feed_byte(inter_mcu_fsm_t *fsm, uint8_t byte, uint32_t current_tick_ms);

/**
 * @brief Check if at least one decoded packet is pending in the queue.
 */
bool inter_mcu_fsm_has_packet(const inter_mcu_fsm_t *fsm);

/**
 * @brief Pop next available packet from the queue.
 * @return true if a packet was retrieved, false if queue is empty.
 */
bool inter_mcu_fsm_pop_packet(inter_mcu_fsm_t *fsm, inter_mcu_packet_t *out_pkt);

/**
 * @brief Build a framed packet [SYNC1, SYNC2, CMD, LEN, PAYLOAD, CRC8].
 * @return Total bytes written to out_buf, or 0 on parameter error / buffer too small.
 */
size_t inter_mcu_build_frame(uint8_t cmd, const uint8_t *payload, uint8_t length,
                             uint8_t *out_buf, size_t max_buf_len);

#ifdef __cplusplus
}
#endif

#endif /* INTER_MCU_PROTO_H */
