/******************************************************************************/
/**
 * @file InterMcuUart.cpp
 * @addtogroup INTER_MCU_UART
 * @brief Implementacao da classe C++ de comunicacao serial inter-MCU.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - InterMcuUart.hpp
 * - Bsp.hpp
 * - main.h
 *
 * \n <b>Observacoes:</b>
 * - Utiliza a interface USART3 (PD8 TX, PD9 RX) conectada ao ESP32.
 * - Quadro: [SYNC1, SYNC2, CMD, LEN, PAYLOAD, CRC8].
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "InterMcuUart.hpp"
#include "Bsp.hpp"
#include "main.h"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dCRC_INITIAL_VALUE                  0x00U
#define dCRC_MSB_MASK                       0x80U
#define dCRC_BITS_IN_BYTE                   8U
#define dTEMP_CRC_BUFFER_SIZE               (dINTER_MCU_UART_MAX_PAYLOAD + 2U)

/*******************************************************************************
 * CONSTANTES
 ******************************************************************************/

/*******************************************************************************
 * ESTRUTURAS DE DADOS LOCAIS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS LOCAIS
 ******************************************************************************/

/*******************************************************************************
 * FUNCOES PUBLICAS
 ******************************************************************************/

/******************************************************************************/
/** @brief Retorna a instancia estatica unica (Singleton) de InterMcuUart.
 * @retval InterMcuUart&: Referencia a instancia global.
 ******************************************************************************/
InterMcuUart& InterMcuUart::GetInstance(void)
{
    static InterMcuUart instance;
    return instance;
}

/******************************************************************************/
/** @brief Construtor padrao da classe InterMcuUart.
 ******************************************************************************/
InterMcuUart::InterMcuUart()
    : rxState_(eINTER_MCU_UART_RX_STATE_SYNC1)
    , currentCmd_(0U)
    , currentLen_(0U)
    , payloadIndex_(0U)
    , payloadBuffer_{0U}
    , packets_{}
    , packetHead_(0U)
    , packetTail_(0U)
    , packetCount_(0U)
    , packetDrops_(0U)
    , lastByteTick_(0U)
    , packetsReceived_(0U)
    , packetsTransmitted_(0U)
    , crcErrors_(0U)
    , isInitialized_(false)
{
}

/******************************************************************************/
/** @brief Inicializa buffers e maquina de estados de recepcao serial.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void InterMcuUart::Init(void)
{
    rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
    currentCmd_ = 0U;
    currentLen_ = 0U;
    payloadIndex_ = 0U;
    packetHead_ = 0U;
    packetTail_ = 0U;
    packetCount_ = 0U;
    packetDrops_ = 0U;
    lastByteTick_ = Bsp::GetTick();
    packetsReceived_ = 0U;
    packetsTransmitted_ = 0U;
    crcErrors_ = 0U;

    for(u8 i = 0U; i < (u8)dINTER_MCU_UART_MAX_PAYLOAD; i++)
    {
        payloadBuffer_[i] = 0U;
    }

    isInitialized_ = true;
}

/******************************************************************************/
/** @brief Monta o quadro binario com CRC-8 e transmite pela interface serial.
 * @param cmd: Identificador do comando a ser transmitido.
 * @param pPayload: Ponteiro para o buffer com os dados do payload.
 * @param payloadLen: Quantidade de bytes de payload (0 a 64).
 * @retval bool: true se o quadro foi transmitido, false se parametros invalidos.
 ******************************************************************************/
bool InterMcuUart::SendPacket(u8 cmd, const u8 *pPayload, u8 payloadLen)
{
    if(payloadLen > (u8)dINTER_MCU_UART_MAX_PAYLOAD)
    {
        return false;
    }

    if((payloadLen > 0U) && (pPayload == nullptr))
    {
        return false;
    }

    u8 crcBuffer[dTEMP_CRC_BUFFER_SIZE];
    crcBuffer[0] = cmd;
    crcBuffer[1] = payloadLen;

    u8 i;
    for(i = 0U; i < payloadLen; i++)
    {
        crcBuffer[i + 2U] = pPayload[i];
    }

    u8 calculatedCrc = CalculateCrc8(crcBuffer, (u8)(payloadLen + 2U));

    // Transmissao sincronizada do quadro
    Bsp::Usart3WriteByte(dINTER_MCU_UART_SYNC1);
    Bsp::Usart3WriteByte(dINTER_MCU_UART_SYNC2);
    Bsp::Usart3WriteByte(cmd);
    Bsp::Usart3WriteByte(payloadLen);

    for(i = 0U; i < payloadLen; i++)
    {
        Bsp::Usart3WriteByte(pPayload[i]);
    }

    Bsp::Usart3WriteByte(calculatedCrc);

    packetsTransmitted_++;

    return true;
}

/******************************************************************************/
/** @brief Processa bytes pendentes na interface serial alimentando a FSM.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void InterMcuUart::ProcessRx(void)
{
    const u32 now = Bsp::GetTick();
    if((rxState_ != eINTER_MCU_UART_RX_STATE_SYNC1) &&
       ((now - lastByteTick_) >= dINTER_MCU_UART_RX_TIMEOUT_MS))
    {
        rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
    }
    u16 event;
    // Leave bytes queued while decoded-packet storage is full.
    while((packetCount_ < dINTER_MCU_UART_PACKET_QUEUE_SIZE) &&
          Bsp::Usart3ReadEvent(&event))
    {
        lastByteTick_ = now;
        if(event > 0xFFU)
        {
            rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
            payloadIndex_ = 0U;
        }
        else
        {
            RxByteCallback((u8)event);
        }
    }
}

/******************************************************************************/
/** @brief Informa se ha um pacote valido pendente para leitura.
 * @retval bool: true se ha novo pacote, false caso contrario.
 ******************************************************************************/
bool InterMcuUart::HasNewPacket(void) const
{
    return packetCount_ != 0U;
}

/******************************************************************************/
/** @brief Extrai o conteudo do ultimo pacote valido recebido e limpa o flag.
 * @param pCmd: Ponteiro para armazenar o byte do comando.
 * @param pPayload: Buffer de saida para armazenar o payload.
 * @param pPayloadLen: Ponteiro para armazenar o tamanho retornado.
 * @retval bool: true se pacote extraido, false se nao havia pacote.
 ******************************************************************************/
bool InterMcuUart::GetPacket(u8 *pCmd, u8 *pPayload, u8 *pPayloadLen)
{
    if((packetCount_ == 0U) || (pCmd == nullptr) || (pPayload == nullptr) || (pPayloadLen == nullptr))
    {
        return false;
    }

    *pCmd = packets_[packetTail_].cmd;
    *pPayloadLen = packets_[packetTail_].length;

    u8 i;
    for(i = 0U; i < packets_[packetTail_].length; i++)
    {
        pPayload[i] = packets_[packetTail_].payload[i];
    }

    packetTail_ = (u8)((packetTail_ + 1U) % dINTER_MCU_UART_PACKET_QUEUE_SIZE);
    packetCount_--;

    return true;
}

/******************************************************************************/
/** @brief Callback para recepcao de byte individual oriundo de ISR ou polling.
 * @param byteRx: Byte recebido na interface serial.
 * @retval Nenhum.
 ******************************************************************************/
void InterMcuUart::RxByteCallback(u8 byteRx)
{
    u8 crcBuffer[dTEMP_CRC_BUFFER_SIZE];
    u8 calculatedCrc;
    u8 i;

    switch(rxState_)
    {
        case eINTER_MCU_UART_RX_STATE_SYNC1:
            if(byteRx == (u8)dINTER_MCU_UART_SYNC1)
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_SYNC2;
            }
            break;

        case eINTER_MCU_UART_RX_STATE_SYNC2:
            if(byteRx == (u8)dINTER_MCU_UART_SYNC2)
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_CMD;
            }
            else if(byteRx == (u8)dINTER_MCU_UART_SYNC1)
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_SYNC2;
            }
            else
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
            }
            break;

        case eINTER_MCU_UART_RX_STATE_CMD:
            currentCmd_ = byteRx;
            rxState_ = eINTER_MCU_UART_RX_STATE_LEN;
            break;

        case eINTER_MCU_UART_RX_STATE_LEN:
            currentLen_ = byteRx;
            payloadIndex_ = 0U;

            if(byteRx > (u8)dINTER_MCU_UART_MAX_PAYLOAD)
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
            }
            else if(byteRx == 0U)
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_CRC;
            }
            else
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_PAYLOAD;
            }
            break;

        case eINTER_MCU_UART_RX_STATE_PAYLOAD:
            payloadBuffer_[payloadIndex_] = byteRx;
            payloadIndex_++;

            if(payloadIndex_ >= currentLen_)
            {
                rxState_ = eINTER_MCU_UART_RX_STATE_CRC;
            }
            break;

        case eINTER_MCU_UART_RX_STATE_CRC:
            crcBuffer[0] = currentCmd_;
            crcBuffer[1] = currentLen_;

            for(i = 0U; i < currentLen_; i++)
            {
                crcBuffer[i + 2U] = payloadBuffer_[i];
            }

            calculatedCrc = CalculateCrc8(crcBuffer, (u8)(currentLen_ + 2U));

            if(calculatedCrc == byteRx)
            {
                if(packetCount_ < dINTER_MCU_UART_PACKET_QUEUE_SIZE)
                {
                    interMcuUartPacket_t& packet = packets_[packetHead_];
                    packet.cmd = currentCmd_;
                    packet.length = currentLen_;
                    for(i = 0U; i < currentLen_; i++)
                    {
                        packet.payload[i] = payloadBuffer_[i];
                    }
                    packet.isValid = true;
                    packetHead_ = (u8)((packetHead_ + 1U) % dINTER_MCU_UART_PACKET_QUEUE_SIZE);
                    packetCount_++;
                }
                else
                {
                    packetDrops_++;
                }
                packetsReceived_++;
            }
            else
            {
                crcErrors_++;
            }

            rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
            break;

        default:
            rxState_ = eINTER_MCU_UART_RX_STATE_SYNC1;
            break;
    }
}

/******************************************************************************/
/** @brief Calcula o checksum CRC-8 CCITT sobre um bloco contiguo de bytes.
 * @param pData: Ponteiro para o buffer de bytes de entrada.
 * @param length: Quantidade de bytes a processar.
 * @retval u8: Checksum CRC-8 calculado.
 ******************************************************************************/
u8 InterMcuUart::CalculateCrc8(const u8 *pData, u8 length)
{
    u8 crc = dCRC_INITIAL_VALUE;
    u8 byteIndex;
    u8 bitIndex;

    if(pData != nullptr)
    {
        for(byteIndex = 0U; byteIndex < length; byteIndex++)
        {
            crc ^= pData[byteIndex];

            for(bitIndex = 0U; bitIndex < (u8)dCRC_BITS_IN_BYTE; bitIndex++)
            {
                if((crc & (u8)dCRC_MSB_MASK) != 0U)
                {
                    crc = (u8)((crc << 1U) ^ (u8)dINTER_MCU_UART_CRC_POLY);
                }
                else
                {
                    crc = (u8)(crc << 1U);
                }
            }
        }
    }

    return crc;
}

/******************************************************************************/
/** @brief Retorna o total de pacotes validos recebidos.
 * @retval u32: Total de pacotes.
 ******************************************************************************/
u32 InterMcuUart::GetPacketsReceived(void) const
{
    return packetsReceived_;
}

/******************************************************************************/
/** @brief Retorna o total de pacotes transmitidos.
 * @retval u32: Total de pacotes.
 ******************************************************************************/
u32 InterMcuUart::GetPacketsTransmitted(void) const
{
    return packetsTransmitted_;
}

/******************************************************************************/
/** @brief Retorna o total de erros de CRC detectados na recepcao.
 * @retval u32: Total de erros.
 ******************************************************************************/
u32 InterMcuUart::GetCrcErrors(void) const
{
    return crcErrors_;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/** @} DOXYGEN GROUP TAG END OF FILE */

u32 InterMcuUart::GetPacketDrops(void) const
{
    return packetDrops_;
}
