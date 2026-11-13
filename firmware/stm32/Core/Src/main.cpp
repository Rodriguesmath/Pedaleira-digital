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
#include "MasterMuteGate.hpp"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
// Safety gate: audio transport ready with SAI4 + BDMA in D3 SRAM4.
#define dMAIN_AUDIO_TRANSPORT_READY          1U

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
static MasterMuteGate masterMuteGate;
static PedalLeds& pedalLeds = PedalLeds::GetInstance();
static PedalSwitches& pedalSwitches = PedalSwitches::GetInstance();
static Cs4272& codecCs4272 = Cs4272::GetInstance();
static InterMcuUart& interMcuUart = InterMcuUart::GetInstance();

static float s_audioInBlock[dBSP_AUDIO_BLOCK_SAMPLES];
static float s_audioOutBlock[dBSP_AUDIO_BLOCK_SAMPLES];

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
static bool Main_ApplyMute(void);
static void Main_AudioBlockCallback(const s32 *pRx, s32 *pTx, u32 frameCount);
static inline u32 Main_EnterCritical(void);
static inline void Main_ExitCritical(u32 primask);

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

    // Aguarda estabilizacao dos clocks SAI4 (MCLK, SCK, FS) em silencio antes do codec
    Bsp::DelayMs(10U);

    // 2. Inicializacao das classes de componentes perifericos e DSP
    pedalLeds.Init();
    pedalSwitches.Init();
    dspEngine.Init(dDSP_ENGINE_DEFAULT_SAMPLE_RATE);
    dspEngine.SetMasterMute(true);

#if (dMAIN_AUDIO_TRANSPORT_READY != 0U)
    if(codecCs4272.Init() != eCS4272_STATUS_OK)
    {
        Bsp::ErrorHandler();
    }
#endif
    interMcuUart.Init();

    mainState.isRunning = true;
    mainState.lastDispatchTick = Bsp::GetTick();
    mainState.lastHeartbeatTick = Bsp::GetTick();

    // 3. Registra o callback de audio apenas apos DSP e codec inicializados (zero race)
    Bsp::SetAudioCallback(Main_AudioBlockCallback);

    // 4. Sincronizacao inicial dos efeitos com a posicao fisica das chaves
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

        }

        // ISR buffers RX during TX/I2C; drain and dispatch without a 10 ms gate.
        interMcuUart.ProcessRx();
        Main_DispatchUart();

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
static bool Main_ApplyMute(void)
{
    static bool codecMuteKnown = false;
    static bool codecMute = true;
    const bool mute = masterMuteGate.Effective(
        pedalSwitches.IsActive(ePEDAL_SWITCHES_SW4), dMAIN_AUDIO_TRANSPORT_READY != 0U);
    dspEngine.SetMasterMute(mute);
    if(codecCs4272.IsInitialized() && (!codecMuteKnown || (codecMute != mute)))
    {
        if(codecCs4272.SetMute(mute) != eCS4272_STATUS_OK)
        {
            dspEngine.SetMasterMute(true);
            Bsp::ErrorHandler(); // Error handler asserts codec reset LOW.
            return false;
        }
        codecMute = mute;
        codecMuteKnown = true;
    }
    return true;
}

static void Main_DispatchSwitches(void)
{
    // SW1: Overdrive
    bool sw1Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW1);
    pedalLeds.Set(ePEDAL_LEDS_OVERDRIVE, sw1Active);
    {
        const u32 primask = Main_EnterCritical();
        dspEngine.SetOverdriveEnable(sw1Active);
        Main_ExitCritical(primask);
    }

    // SW2: Equalizador 3-Bandas
    bool sw2Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW2);
    pedalLeds.Set(ePEDAL_LEDS_EQUALIZER, sw2Active);
    {
        const u32 primask = Main_EnterCritical();
        dspEngine.SetEqualizerEnable(sw2Active);
        Main_ExitCritical(primask);
    }

    // SW3: Delay
    bool sw3Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW3);
    pedalLeds.Set(ePEDAL_LEDS_DELAY, sw3Active);
    {
        const u32 primask = Main_EnterCritical();
        dspEngine.SetDelayEnable(sw3Active);
        Main_ExitCritical(primask);
    }

    // SW4: Master Mute; no audio is released before transport exists.
    bool sw4Active = pedalSwitches.IsActive(ePEDAL_SWITCHES_SW4);
    pedalLeds.Set(ePEDAL_LEDS_STATUS, sw4Active);
    Main_ApplyMute();

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
                                const u32 primask = Main_EnterCritical();
                                dspEngine.SetMasterVolume(volNorm);
                                Main_ExitCritical(primask);
                                if(codecCs4272.IsInitialized() == true)
                                {
                                    codecCs4272.SetMasterVolume(paramVal);
                                }
                            }
                            else if(paramId == dPARAM_GLOBAL_MASTER_BYPASS)
                            {
                                bool isBypass = (paramVal != 0U);
                                const u32 primask = Main_EnterCritical();
                                dspEngine.SetMasterBypass(isBypass);
                                Main_ExitCritical(primask);
                            }
                            else if(paramId == dPARAM_GLOBAL_MASTER_MUTE)
                            {
                                masterMuteGate.SetRemote(paramVal != 0U);
                                Main_ApplyMute();
                            }
                        }
                        else if(module == dMODULE_OVERDRIVE)
                        {
                            const u32 primask = Main_EnterCritical();
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
                            Main_ExitCritical(primask);
                        }
                        else if(module == dMODULE_EQUALIZER)
                        {
                            s8 gainDb = (s8)paramVal; // Faixa com sinal [-12 dB a +12 dB]
                            const u32 primask = Main_EnterCritical();
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
                            Main_ExitCritical(primask);
                        }
                        else if(module == dMODULE_DELAY)
                        {
                            if(paramId == dPARAM_DELAY_ENABLE)
                            {
                                const u32 primask = Main_EnterCritical();
                                dspEngine.SetDelayEnable(paramVal != 0U);
                                Main_ExitCritical(primask);
                            }
                            else if(paramId == dPARAM_DELAY_TIME)
                            {
                                if(payloadLength >= 4U)
                                {
                                    u16 timeMs = (u16)payloadBuffer[2] | ((u16)payloadBuffer[3] << 8U);
                                    const u32 primask = Main_EnterCritical();
                                    dspEngine.SetDelayTimeMs((float)timeMs);
                                    Main_ExitCritical(primask);
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
                                const u32 primask = Main_EnterCritical();
                                dspEngine.SetDelayFeedback((float)paramVal * 0.01f);
                                Main_ExitCritical(primask);
                            }
                            else if(paramId == dPARAM_DELAY_MIX)
                            {
                                const u32 primask = Main_EnterCritical();
                                dspEngine.SetDelayMix((float)paramVal * 0.01f);
                                Main_ExitCritical(primask);
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
    // PE15 belongs to master mute; heartbeat only uses the onboard LED.
    Bsp::LedOnboardToggle();

    interMcuUart.SendPacket((u8)eINTER_MCU_UART_CMD_HEARTBEAT, nullptr, 0U);
}

/******************************************************************************/
/** @brief Entra em secao critica curta mascarando interrupcoes via PRIMASK.
 * @param Nenhum.
 * @retval u32: Estado anterior de PRIMASK para posterior restauracao.
 ******************************************************************************/
static inline u32 Main_EnterCritical(void)
{
    u32 primask = __get_PRIMASK();
    __disable_irq();
    return primask;
}

/******************************************************************************/
/** @brief Restaura o estado anterior das interrupcoes a partir de PRIMASK.
 * @param primask: Estado retornado por Main_EnterCritical.
 * @retval Nenhum.
 ******************************************************************************/
static inline void Main_ExitCritical(u32 primask)
{
    if(primask == 0U)
    {
        __enable_irq();
    }
}

/******************************************************************************/
/** @brief Callback invocado pelo BDMA a cada metade do buffer (64 amostras).
 * @param pRx: Ponteiro para bloco recebido da SAI4_Block_B (24-bit em slot 32-bit).
 * @param pTx: Ponteiro para bloco de transmissao para SAI4_Block_A.
 * @param frameCount: Quantidade de quadros estereo (64).
 * @retval Nenhum.
 ******************************************************************************/
static void Main_AudioBlockCallback(const s32 *pRx, s32 *pTx, u32 frameCount)
{
    if((codecCs4272.IsInitialized() == false) || (dspEngine.IsMasterMuted() == true))
    {
        for(u32 i = 0U; i < (frameCount * dBSP_AUDIO_CHANNELS); i++)
        {
            pTx[i] = 0;
        }
        return;
    }

    constexpr float kInvScale24 = 1.0f / 8388608.0f;
    constexpr float kScale24 = 8388607.0f;

    for(u32 i = 0U; i < frameCount; i++)
    {
        const u32 raw24 = (u32)pRx[i * dBSP_AUDIO_CHANNELS] & 0x00FFFFFFUL;
        const s32 signed24 = (s32)((raw24 ^ 0x00800000UL) - 0x00800000L);
        s_audioInBlock[i] = (float)signed24 * kInvScale24;
    }

    dspEngine.ProcessBlock(s_audioInBlock, s_audioOutBlock, frameCount);

    for(u32 i = 0U; i < frameCount; i++)
    {
        float outSample = s_audioOutBlock[i];
        if(outSample > 1.0f)
        {
            outSample = 1.0f;
        }
        else if(outSample < -1.0f)
        {
            outSample = -1.0f;
        }

        const s32 rawOut = (s32)(outSample * kScale24);
        pTx[i * dBSP_AUDIO_CHANNELS] = rawOut;
        pTx[(i * dBSP_AUDIO_CHANNELS) + 1U] = rawOut;
    }
}

/** @} DOXYGEN GROUP TAG END OF FILE */
