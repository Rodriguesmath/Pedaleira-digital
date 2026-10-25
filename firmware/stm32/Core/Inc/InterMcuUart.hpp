/******************************************************************************/
/**
 * @file InterMcuUart.hpp
 * @addtogroup INTER_MCU_UART
 * @brief Classe C++ para comunicacao serial binaria inter-MCU com CRC-8 CCITT.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _INTER_MCU_UART_HPP_
#define _INTER_MCU_UART_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/
/// Taxa de transmissao da interface UART inter-microcontroladores em bits/s
#define dINTER_MCU_UART_BAUDRATE            115200UL

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Primeiro byte fixo de sincronismo do quadro binario
#define dINTER_MCU_UART_SYNC1               0xAAU

/// Segundo byte fixo de sincronismo do quadro binario
#define dINTER_MCU_UART_SYNC2               0x55U

/// Tamanho maximo permitido para o payload de dados em bytes
#define dINTER_MCU_UART_MAX_PAYLOAD         64U

/// Polinomio padrao do CRC-8 CCITT (x^8 + x^2 + x + 1)
#define dINTER_MCU_UART_CRC_POLY            0x07U

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Comandos suportados pelo protocolo serial da pedaleira
typedef enum
{
    eINTER_MCU_UART_CMD_SET_PARAM           = 0x01,
    eINTER_MCU_UART_CMD_GET_STATE           = 0x02,
    eINTER_MCU_UART_CMD_STATE_REPORT        = 0x03,
    eINTER_MCU_UART_CMD_SWITCH_EVENT        = 0x04,
    eINTER_MCU_UART_CMD_ACK                 = 0x05,
    eINTER_MCU_UART_CMD_NACK                = 0x06,
    eINTER_MCU_UART_CMD_HEARTBEAT           = 0x07
} interMcuUartCmd_t;

/// Estados da maquina de estados de recepcao e parsing
typedef enum
{
    eINTER_MCU_UART_RX_STATE_SYNC1,
    eINTER_MCU_UART_RX_STATE_SYNC2,
    eINTER_MCU_UART_RX_STATE_CMD,
    eINTER_MCU_UART_RX_STATE_LEN,
    eINTER_MCU_UART_RX_STATE_PAYLOAD,
    eINTER_MCU_UART_RX_STATE_CRC
} interMcuUartRxState_t;

/// Estrutura para armazenamento do pacote decodificado
typedef struct
{
    u8 cmd;
    u8 length;
    u8 payload[dINTER_MCU_UART_MAX_PAYLOAD];
    bool isValid;
} interMcuUartPacket_t;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class InterMcuUart
 * @brief Gerenciador do canal de comunicacao serial full-duplex STM32 <-> ESP32.
 ******************************************************************************/
class InterMcuUart
{
public:
    InterMcuUart();
    ~InterMcuUart() = default;

    static InterMcuUart& GetInstance(void);

    void Init(void);
    bool SendPacket(u8 cmd, const u8 *pPayload, u8 payloadLen);
    void ProcessRx(void);
    bool HasNewPacket(void) const;
    bool GetPacket(u8 *pCmd, u8 *pPayload, u8 *pPayloadLen);
    void RxByteCallback(u8 byteRx);

    static u8 CalculateCrc8(const u8 *pData, u8 length);

    u32 GetPacketsReceived(void) const;
    u32 GetPacketsTransmitted(void) const;
    u32 GetCrcErrors(void) const;

private:
    interMcuUartRxState_t rxState_;
    u8 currentCmd_;
    u8 currentLen_;
    u8 payloadIndex_;
    u8 payloadBuffer_[dINTER_MCU_UART_MAX_PAYLOAD];
    interMcuUartPacket_t lastPacket_;
    bool hasNewPacket_;
    u32 packetsReceived_;
    u32 packetsTransmitted_;
    u32 crcErrors_;
    bool isInitialized_;
};

#endif /* _INTER_MCU_UART_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
