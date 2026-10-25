/******************************************************************************/
/**
 * @file main.cpp
 * @addtogroup MAIN
 * @brief Ponto de entrada C++ da aplicacao da Pedaleira Digital (ASSERT Capacita).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - Bsp.hpp
 * - Cs4272.hpp
 * - DspEngine.hpp
 * - InterMcuUart.hpp
 * - PedalLeds.hpp
 * - PedalSwitches.hpp
 * - main.h
 *
 * \n <b>Observacoes:</b>
 * - Orquestra a execucao orientada a objetos das classes de hardware e DSP.
 * - Gerencia o loop de eventos periodicos e o sincronismo inter-MCU.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao C++ no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "Bsp.hpp"
#include "Cs4272.hpp"
#include "DspEngine.hpp"
#include "InterMcuUart.hpp"
#include "PedalLeds.hpp"
#include "PedalSwitches.hpp"
#include "main.h"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dMAIN_DISPATCH_PERIOD_MS            10U
#define dMAIN_HEARTBEAT_PERIOD_MS           1000U

#define dMODULE_GLOBAL                      0x00U
#define dMODULE_OVERDRIVE                   0x01U
#define dMODULE_EQUALIZER                   0x02U
#define dMODULE_DELAY                       0x03U

#define dPARAM_GLOBAL_MASTER_VOLUME         0x01U
#define dPARAM_GLOBAL_MASTER_BYPASS         0x02U
#define dPARAM_GLOBAL_MASTER_MUTE           0x03U

#define dPARAM_OVERDRIVE_ENABLE             0x00U
#define dPARAM_OVERDRIVE_DRIVE              0x01U
#define dPARAM_OVERDRIVE_TONE               0x02U
#define dPARAM_OVERDRIVE_LEVEL              0x03U

#define dPARAM_EQUALIZER_ENABLE             0x00U
#define dPARAM_EQUALIZER_LOW                0x01U
#define dPARAM_EQUALIZER_MID                0x02U
#define dPARAM_EQUALIZER_TREBLE             0x03U

#define dPARAM_DELAY_ENABLE                 0x00U
#define dPARAM_DELAY_TIME                   0x01U
#define dPARAM_DELAY_FEEDBACK               0x02U
#define dPARAM_DELAY_MIX                    0x03U

#define dSWITCH_EVENT_PAYLOAD_SIZE          2U
#define dACK_PAYLOAD_SIZE                   1U

/*******************************************************************************
 * CONSTANTES
 ******************************************************************************/

/*******************************************************************************
 * ESTRUTURAS DE DADOS LOCAIS
 ******************************************************************************/
/// Instancias estaticas das classes principais do sistema
static DspEngine dspEngine;
static PedalLeds& pedalLeds = PedalLeds::GetInstance();
static PedalSwitches& pedalSwitches = PedalSwitches::GetInstance();
static Cs4272& codecCs4272 = Cs4272::GetInstance();
static InterMcuUart& interMcuUart = InterMcuUart::GetInstance();

/// Estrutura local com estado interno do laco de despacho principal
static struct
{
    u32 lastDispatchTick;
    u32 lastHeartbeatTick;
    bool isRunning;
} mainState;

/*******************************************************************************
 * PROTOTIPOS LOCAIS
 ******************************************************************************/
static void Main_DispatchSwitches(void);
static void Main_DispatchUart(void);
static void Main_DispatchHeartbeat(void);

/*******************************************************************************
 * FUNCOES PUBLICAS
 ******************************************************************************/

/******************************************************************************/
/** @brief Ponto de entrada principal da aplicacao da pedaleira.
 * @param Nenhum.
 * @retval int: Codigo de retorno do sistema.
 ******************************************************************************/
int main(void)
{
    // 1. Inicializacao unificada de baixo nivel de hardware via BSP
    bspStatus_t bspInitStatus = Bsp::Init();
    if(bspInitStatus != eBSP_STATUS_OK)
    {
        Bsp::ErrorHandler();
    }

    // 2. Inicializacao das classes de componentes perifericos e DSP
    pedalLeds.Init();
    pedalSwitches.Init();
    codecCs4272.Init();
    interMcuUart.Init();
    dspEngine.Init(dDSP_ENGINE_DEFAULT_SAMPLE_RATE);

    mainState.isRunning = true;
    mainState.lastDispatchTick = Bsp::GetTick();
    mainState.lastHeartbeatTick = Bsp::GetTick();

    // 3. Sincronizacao inicial dos efeitos com a posicao fisica das chaves
    Main_DispatchSwitches();

    // 4. Laco infinito de despacho periodico
    while(mainState.isRunning == true)
    {
        u32 currentTick = Bsp::GetTick();

        // Tarefa rapida (10 ms): Debounce de chaves e parsing UART
        if((currentTick - mainState.lastDispatchTick) >= dMAIN_DISPATCH_PERIOD_MS)
        {
            mainState.lastDispatchTick = currentTick;

            pedalSwitches.Process();
            Main_DispatchSwitches();

            interMcuUart.ProcessRx();
            Main_DispatchUart();
        }

        // Tarefa lenta (1000 ms): Heartbeat de conectividade e sinalizacao
        if((currentTick - mainState.lastHeartbeatTick) >= dMAIN_HEARTBEAT_PERIOD_MS)
        {
            mainState.lastHeartbeatTick = currentTick;
            Main_DispatchHeartbeat();
        }
    }

    return 0;
}

/******************************************************************************/
/** @brief Ponto de tratamento de erro invocado pelo subsistema HAL da ST.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
extern "C" void Error_Handler(void)
{
    Bsp::ErrorHandler();
}

#ifdef USE_FULL_ASSERT
/******************************************************************************/
/** @brief Callback para falhas de assert dos parametros do HAL.
 * @param file: Ponteiro para o nome do arquivo onde ocorreu a falha.
 * @param line: Numero da linha onde ocorreu a falha.
 * @retval Nenhum.
 ******************************************************************************/
extern "C" void assert_failed(uint8_t *file, uint32_t line)
{
    (void)file;
    (void)line;
    Bsp::ErrorHandler();
}
#endif

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Verifica mudancas nas chaves fisicas e sincroniza LEDs, DSP e UART.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
static void Main_DispatchSwitches(void)
{
    // SW1: Overdrive
    bool sw1Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW1);
    pedalLeds.Set(ePEDAL_LEDS_OVERDRIVE, sw1Active);
    dspEngine.SetOverdriveEnable(sw1Active);

    // SW2: Equalizador 3-Bandas
    bool sw2Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW2);
    pedalLeds.Set(ePEDAL_LEDS_EQUALIZER, sw2Active);
    dspEngine.SetEqualizerEnable(sw2Active);

    // SW3: Delay
    bool sw3Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW3);
    pedalLeds.Set(ePEDAL_LEDS_DELAY, sw3Active);
    dspEngine.SetDelayEnable(sw3Active);

    // SW4: Master Bypass / Mute
    bool sw4Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW4);
    pedalLeds.Set(ePEDAL_LEDS_STATUS, sw4Active);
    dspEngine.SetMasterBypass(sw4Active);

    // Notificacao de eventos caso alguma chave tenha comutado
    u8 indexSwitch;
    u8 eventPayload[dSWITCH_EVENT_PAYLOAD_SIZE];

    for(indexSwitch = 0U; indexSwitch < (u8)ePEDAL_SWITCHES_COUNT; indexSwitch++)
    {
        if(pedalSwitches.HasChanged((pedalSwitchesId_t)indexSwitch) == true)
        {
            bool isActive = pedalSwitches.IsActive((pedalSwitchesId_t)indexSwitch);
            eventPayload[0] = (u8)(indexSwitch + 1U);
            if(isActive == true)
            {
                eventPayload[1] = 1U;
            }
            else
            {
                eventPayload[1] = 0U;
            }

            interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_SWITCH_EVENT,
                                    eventPayload,
                                    dSWITCH_EVENT_PAYLOAD_SIZE);
        }
    }
}

/******************************************************************************/
/** @brief Trata comandos e pacotes recebidos pela interface serial com o ESP32.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
static void Main_DispatchUart(void)
{
    u8 cmdReceived;
    u8 payloadBuffer[dINTER_MCU_UART_MAX_PAYLOAD];
    u8 payloadLength;
    u8 ackPayload[dACK_PAYLOAD_SIZE];

    if(interMcuUart.HasNewPacket() == true)
    {
        if(interMcuUart.GetPacket(&cmdReceived, payloadBuffer, &payloadLength) == true)
        {
            switch(cmdReceived)
            {
                case (u8)eINTER_MCU_UART_CMD_SET_PARAM:
                    // Formato: [MODULE, PARAM_ID, VALUE...]
                    if(payloadLength >= 3U)
                    {
                        u8 module = payloadBuffer[0];
                        u8 paramId = payloadBuffer[1];
                        u8 paramVal = payloadBuffer[2];

                        if(module == dMODULE_GLOBAL)
                        {
                            if(paramId == dPARAM_GLOBAL_MASTER_VOLUME)
                            {
                                float volNorm = (float)paramVal * 0.01f;
                                dspEngine.SetMasterVolume(volNorm);
                                codecCs4272.SetMasterVolume(paramVal);
                            }
                            else if(paramId == dPARAM_GLOBAL_MASTER_BYPASS)
                            {
                                bool isBypass = (paramVal != 0U);
                                dspEngine.SetMasterBypass(isBypass);
                            }
                            else if(paramId == dPARAM_GLOBAL_MASTER_MUTE)
                            {
                                bool isMute = (paramVal != 0U);
                                dspEngine.SetMasterMute(isMute);
                                codecCs4272.SetMute(isMute);
                            }
                        }
                        else if(module == dMODULE_OVERDRIVE)
                        {
                            if(paramId == dPARAM_OVERDRIVE_ENABLE)
                            {
                                dspEngine.SetOverdriveEnable(paramVal != 0U);
                            }
                            else if(paramId == dPARAM_OVERDRIVE_DRIVE)
                            {
                                dspEngine.SetOverdriveDrive((float)paramVal * 0.01f);
                            }
                            else if(paramId == dPARAM_OVERDRIVE_TONE)
                            {
                                dspEngine.SetOverdriveTone((float)paramVal * 0.01f);
                            }
                            else if(paramId == dPARAM_OVERDRIVE_LEVEL)
                            {
                                dspEngine.SetOverdriveLevel((float)paramVal * 0.01f);
                            }
                        }
                        else if(module == dMODULE_EQUALIZER)
                        {
                            s8 gainDb = (s8)paramVal; // Faixa com sinal [-12 dB a +12 dB]
                            if(paramId == dPARAM_EQUALIZER_ENABLE)
                            {
                                dspEngine.SetEqualizerEnable(paramVal != 0U);
                            }
                            else if(paramId == dPARAM_EQUALIZER_LOW)
                            {
                                dspEngine.SetEqualizerLow((float)gainDb);
                            }
                            else if(paramId == dPARAM_EQUALIZER_MID)
                            {
                                dspEngine.SetEqualizerMid((float)gainDb);
                            }
                            else if(paramId == dPARAM_EQUALIZER_TREBLE)
                            {
                                dspEngine.SetEqualizerTreble((float)gainDb);
                            }
                        }
                        else if(module == dMODULE_DELAY)
                        {
                            if(paramId == dPARAM_DELAY_ENABLE)
                            {
                                dspEngine.SetDelayEnable(paramVal != 0U);
                            }
                            else if(paramId == dPARAM_DELAY_TIME)
                            {
                                if(payloadLength >= 4U)
                                {
                                    u16 timeMs = (u16)payloadBuffer[2] | ((u16)payloadBuffer[3] << 8U);
                                    dspEngine.SetDelayTimeMs((float)timeMs);
                                }
                                else
                                {
                                    ackPayload[0] = cmdReceived;
                                    interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_NACK,
                                                            ackPayload,
                                                            dACK_PAYLOAD_SIZE);
                                    break;
                                }
                            }
                            else if(paramId == dPARAM_DELAY_FEEDBACK)
                            {
                                dspEngine.SetDelayFeedback((float)paramVal * 0.01f);
                            }
                            else if(paramId == dPARAM_DELAY_MIX)
                            {
                                dspEngine.SetDelayMix((float)paramVal * 0.01f);
                            }
                        }

                        // Responde com ACK
                        ackPayload[0] = cmdReceived;
                        interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_ACK,
                                                ackPayload,
                                                dACK_PAYLOAD_SIZE);
                    }
                    else
                    {
                        ackPayload[0] = cmdReceived;
                        interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_NACK,
                                                ackPayload,
                                                dACK_PAYLOAD_SIZE);
                    }
                    break;

                case (u8)eINTER_MCU_UART_CMD_GET_STATE:
                    {
                        u8 statePayload[5];
                        statePayload[0] = (u8)pedalSwitches.IsActive(ePEDAL_SWITCHES_SW1);
                        statePayload[1] = (u8)pedalSwitches.IsActive(ePEDAL_SWITCHES_SW2);
                        statePayload[2] = (u8)pedalSwitches.IsActive(ePEDAL_SWITCHES_SW3);
                        statePayload[3] = (u8)pedalSwitches.IsActive(ePEDAL_SWITCHES_SW4);
                        statePayload[4] = (u8)(dspEngine.GetMasterVolume() * 100.0f);

                        interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_STATE_REPORT,
                                                statePayload,
                                                5U);
                    }
                    break;

                case (u8)eINTER_MCU_UART_CMD_HEARTBEAT:
                    interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_HEARTBEAT, nullptr, 0U);
                    break;

                default:
                    ackPayload[0] = cmdReceived;
                    interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_NACK,
                                            ackPayload,
                                            dACK_PAYLOAD_SIZE);
                    break;
            }
        }
    }
}

/******************************************************************************/
/** @brief Executa acoes periodicas de heartbeat e sinalizacao visual.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
static void Main_DispatchHeartbeat(void)
{
    pedalLeds.Toggle(ePEDAL_LEDS_STATUS);
    Bsp::LedOnboardToggle();

    interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_HEARTBEAT, nullptr, 0U);
}

/** @} DOXYGEN GROUP TAG END OF FILE */
