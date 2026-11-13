/******************************************************************************/
/**
 * @file Bsp.cpp
 * @addtogroup BSP
 * @brief Implementacao da classe C++ BSP para WeAct Studio MiniSTM32H723 V1.2.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - Bsp.hpp
 *
 * \n <b>Observacoes:</b>
 * - Clock do sistema configurado em 550 MHz (HSE 25 MHz, PLL1, VOS0, 3WS).
 * - Caches L1 I-Cache e D-Cache habilitados para maxima performance DSP.
 * - Contador de ciclos DWT CYCCNT ativado para temporizacao em microssegundos.
 * - MPU configurada com protecao de regioes de memoria padrao.
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
#include "UartRxRing.hpp"
#include "Cs4272I2cTiming.hpp"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#if (dBSP_SYSCLK_FREQ_HZ != 550000000UL)
#error "Configuracao incorreta: a frequencia SYSCLK deve ser 550 MHz"
#endif

#if (dBSP_HSE_FREQ_HZ != 25000000UL)
#error "Configuracao incorreta: o cristal HSE da placa WeAct e de 25 MHz"
#endif

// Clock: HSE/5 * 110 = 550 MHz VCO (PLL1 limit: 836 MHz).
// P=1 preserves 550 MHz CPU without the former out-of-range 1.1 GHz VCO.
// Constantes de clock e temporizacao
#define dPLL_M_VALUE                        5U
#define dPLL_N_VALUE                        110U
#define dPLL_P_VALUE                        1U
#define dPLL_Q_VALUE                        2U
#define dPLL_R_VALUE                        2U

#define dDWT_LAR_UNLOCK_KEY                 0xC5ACCE55UL
#define dCYCLES_PER_MICROSECOND             (dBSP_SYSCLK_FREQ_HZ / 1000000UL)

// Mapeamento de pinos dos LEDs da pedaleira
#define dPIN_LED1                           GPIO_PIN_7
#define dPORT_LED1                          GPIOE
#define dPIN_LED2                           GPIO_PIN_8
#define dPORT_LED2                          GPIOE
#define dPIN_LED3                           GPIO_PIN_9
#define dPORT_LED3                          GPIOE
#define dPIN_LED4                           GPIO_PIN_15
#define dPORT_LED4                          GPIOE
#define dPIN_LED_ONBOARD                    GPIO_PIN_3
#define dPORT_LED_ONBOARD                   GPIOE

// Mapeamento de pinos das chaves de acionamento
#define dPIN_SW1                            GPIO_PIN_0
#define dPORT_SW1                           GPIOC
#define dPIN_SW2                            GPIO_PIN_1
#define dPORT_SW2                           GPIOC
#define dPIN_SW3                            GPIO_PIN_2
#define dPORT_SW3                           GPIOC
#define dPIN_SW4                            GPIO_PIN_3
#define dPORT_SW4                           GPIOC

// Mapeamento de pinos do Codec Cirrus Logic CS4272
#define dPIN_CS4272_RST                     GPIO_PIN_10
#define dPORT_CS4272_RST                    GPIOD
#define dPIN_I2C1_SCL                       GPIO_PIN_8
#define dPORT_I2C1_SCL                      GPIOB
#define dPIN_I2C1_SDA                       GPIO_PIN_9
#define dPORT_I2C1_SDA                      GPIOB
#define dPIN_SAI4_MCLK                      GPIO_PIN_0
#define dPORT_SAI4_MCLK                     GPIOE
#define dPIN_SAI4_FS                        GPIO_PIN_4
#define dPORT_SAI4_FS                       GPIOE
#define dPIN_SAI4_SCK                       GPIO_PIN_5
#define dPORT_SAI4_SCK                      GPIOE
#define dPIN_SAI4_SDA                       GPIO_PIN_6
#define dPORT_SAI4_SDA                      GPIOE
#define dPIN_SAI4_SDB                       GPIO_PIN_0
#define dPORT_SAI4_SDB                      GPIOA

// Mapeamento de pinos da USART3 de comunicacao com ESP32
#define dPIN_USART3_TX                      GPIO_PIN_8
#define dPORT_USART3_TX                     GPIOD
#define dPIN_USART3_RX                      GPIO_PIN_9
#define dPORT_USART3_RX                     GPIOD
#define dINTER_MCU_UART_BAUDRATE            115200UL

// CS4272 is Standard-mode only: <=100 kHz, derived for explicit HSI64.
#define dI2C1_TIMING_VALUE                  Cs4272I2cTiming::Register

/*******************************************************************************
 * CONSTANTES
 ******************************************************************************/

/*******************************************************************************
 * ESTRUTURAS DE DADOS LOCAIS
 ******************************************************************************/
/// Instancia do manipulador I2C1 do barramento de controle do codec
I2C_HandleTypeDef hi2c1;
static UartRxRing usart3RxRing;

extern "C"
{
__attribute__((section(".ram_d3"), aligned(32)))
s32 saiRxDmaBuf[dBSP_AUDIO_BUFFER_SIZE];

__attribute__((section(".ram_d3"), aligned(32)))
s32 saiTxDmaBuf[dBSP_AUDIO_BUFFER_SIZE];
}

bool Bsp::isInitialized_ = false;
bool Bsp::ledOnboardState_ = false;
bspAudioBlockCallback_t Bsp::audioBlockCallback_ = nullptr;
volatile u32 Bsp::audioBlockCount_ = 0U;
volatile u32 Bsp::audioHardwareErrors_ = 0U;

/*******************************************************************************
 * PROTOTIPOS LOCAIS
 ******************************************************************************/

/*******************************************************************************
 * FUNCOES PUBLICAS
 ******************************************************************************/

/******************************************************************************/
/** @brief Inicializacao completa do hardware (Clocks, Caches, MPU e Perifericos).
 * @param Nenhum.
 * @retval bspStatus_t: Codigo de status da inicializacao do sistema.
 ******************************************************************************/
bspStatus_t Bsp::Init(void)
{
    isInitialized_ = false;
    ledOnboardState_ = false;

    // 1. Configuracao da Unidade de Protecao de Memoria (MPU)
    MpuConfig();

    // 2. Inicializacao basica do subsistema HAL da ST
    HAL_Init();

    // 3. Ativacao das memorias Cache L1 da CPU ARM Cortex-M7
    CacheConfig();

    // 4. Configuracao da arvore de clock para 550 MHz
    SystemClockConfig();

    // 5. Inicializacao do contador de ciclos DWT
    DwtConfig();

    // 6. Configuracao dos pinos de entrada e saida (GPIO)
    GpioConfig();

    // 7. Inicializacao dos controladores de comunicacao de baixo nivel
    I2c1Config();
    Usart3Config();

    // 8. Inicializacao do transporte de audio SAI4 + BDMA
    Sai4Config();

    isInitialized_ = true;

    return eBSP_STATUS_OK;
}

/******************************************************************************/
/** @brief Bloqueia a execucao pelo numero especificado de milissegundos.
 * @param ms: Quantidade de milissegundos para espera.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::DelayMs(u32 ms)
{
    HAL_Delay(ms);
}

/******************************************************************************/
/** @brief Bloqueia a execucao pelo numero especificado de microssegundos via DWT.
 * @param us: Quantidade de microssegundos para espera.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::DelayUs(u32 us)
{
    u32 startCycles;
    u32 waitCycles;

    startCycles = DWT->CYCCNT;
    waitCycles = us * (u32)dCYCLES_PER_MICROSECOND;

    while((DWT->CYCCNT - startCycles) < waitCycles)
    {
        // Aguarda contagem de ciclos do nucleo
    }
}

/******************************************************************************/
/** @brief Obtem a contagem atual de milissegundos a partir do Systick.
 * @param Nenhum.
 * @retval u32: Valor atual do contador de ticks em milissegundos.
 ******************************************************************************/
u32 Bsp::GetTick(void)
{
    return HAL_GetTick();
}

/******************************************************************************/
/** @brief Ajusta o estado logico do LED onboard da placa WeAct (PE3, ativo LOW).
 * @param state: true para acender o LED, false para apagar.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::LedOnboardSet(bool state)
{
    ledOnboardState_ = state;

    if(state == true)
    {
        HAL_GPIO_WritePin(dPORT_LED_ONBOARD, dPIN_LED_ONBOARD, GPIO_PIN_RESET);
    }
    else
    {
        HAL_GPIO_WritePin(dPORT_LED_ONBOARD, dPIN_LED_ONBOARD, GPIO_PIN_SET);
    }
}

/******************************************************************************/
/** @brief Inverte o estado logico atual do LED onboard da placa WeAct.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::LedOnboardToggle(void)
{
    if(ledOnboardState_ == true)
    {
        LedOnboardSet(false);
    }
    else
    {
        LedOnboardSet(true);
    }
}

/******************************************************************************/
/** @brief Transmite um byte individual pela interface serial USART3 (PD8).
 * @param data: Byte a ser transmitido.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::Usart3WriteByte(u8 data)
{
    // Aguarda liberacao do registrador de transmissao / TX FIFO
    while((USART3->ISR & (u32)USART_ISR_TXE_TXFNF) == 0U)
    {
        // Aguarda envio
    }

    USART3->TDR = (u32)data;
}

/******************************************************************************/
/** @brief Le um byte pendente no registrador de recepcao da USART3 (PD9).
 * @param pData: Ponteiro para armazenar o byte lido.
 * @retval bool: true se havia byte disponivel, false se fila vazia.
 ******************************************************************************/
bool Bsp::Usart3ReadEvent(u16 *pEvent)
{
    return (pEvent != nullptr) && usart3RxRing.Pop(*pEvent);
}

u32 Bsp::Usart3RxDroppedBytes(void)
{
    return usart3RxRing.DroppedBytes();
}

u32 Bsp::Usart3RxHardwareErrors(void)
{
    return usart3RxRing.HardwareErrors();
}

/******************************************************************************/
/** @brief Define o callback de processamento de bloco de audio do SAI4.
 * @param callback: Ponteiro para funcao de processamento.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::SetAudioCallback(bspAudioBlockCallback_t callback)
{
    audioBlockCallback_ = callback;
}

/******************************************************************************/
/** @brief Retorna o total de blocos de audio processados via BDMA.
 * @param Nenhum.
 * @retval u32: Contagem de interrupcoes de bloco (Half e Transfer Complete).
 ******************************************************************************/
u32 Bsp::AudioBlockCount(void)
{
    return audioBlockCount_;
}

/******************************************************************************/
/** @brief Retorna o total de erros de hardware detectados no canal BDMA de audio.
 * @param Nenhum.
 * @retval u32: Contagem de eventos de Transfer Error.
 ******************************************************************************/
u32 Bsp::AudioHardwareErrors(void)
{
    return audioHardwareErrors_;
}

/******************************************************************************/
/** @brief Tratador de erro critico de execucao de hardware da BSP.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::ErrorHandler(void)
{
    __HAL_RCC_GPIOD_CLK_ENABLE();
    HAL_GPIO_WritePin(dPORT_CS4272_RST, dPIN_CS4272_RST, GPIO_PIN_RESET);
    __disable_irq();

    while(1)
    {
        // Trava no laco com piscada rapida de socorro no LED onboard
        HAL_GPIO_TogglePin(dPORT_LED_ONBOARD, dPIN_LED_ONBOARD);
        for(volatile u32 delayCount = 0U; delayCount < 2000000UL; delayCount++)
        {
            // Espera ocupada simples
        }
    }
}

/******************************************************************************/
/** @brief Obtem o ponteiro do manipulador HAL do periferico I2C1.
 * @retval I2C_HandleTypeDef*: Ponteiro para a estrutura do I2C1.
 ******************************************************************************/
I2C_HandleTypeDef* Bsp::GetI2c1Handle(void)
{
    return &hi2c1;
}

/******************************************************************************/
/** @brief Obtem o endereco base do periferico USART3.
 * @retval USART_TypeDef*: Ponteiro para os registradores da USART3.
 ******************************************************************************/
USART_TypeDef* Bsp::GetUsart3Handle(void)
{
    return USART3;
}

/******************************************************************************/
/** @brief Tratadores de interrupcao CMSIS com ligacao C padrao.
 ******************************************************************************/
extern "C"
{
__attribute__((weak)) void SysTick_Handler(void)
{
    HAL_IncTick();
}

void USART3_IRQHandler(void)
{
    const u32 status = USART3->ISR;
    const u32 errors = status & (USART_ISR_ORE | USART_ISR_FE | USART_ISR_NE);
    if(errors != 0U)
    {
        USART3->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF;
        usart3RxRing.MarkHardwareError();
    }
    if((status & USART_ISR_RXNE_RXFNE) != 0U)
    {
        const u8 received = (u8)USART3->RDR;
        // Discard a byte whose framing/noise status is unreliable.
        if((errors & (USART_ISR_FE | USART_ISR_NE)) == 0U)
        {
            usart3RxRing.PushByte(received);
        }
    }
}

void BDMA_Channel0_IRQHandler(void)
{
    const u32 isr = BDMA->ISR;

    if((isr & BDMA_ISR_TEIF0) != 0U)
    {
        BDMA->IFCR = BDMA_IFCR_CTEIF0;
        Bsp::audioHardwareErrors_++;
    }

    if(((SAI4_Block_A->SR & SAI_xSR_OVRUDR) != 0U) ||
       ((SAI4_Block_B->SR & SAI_xSR_OVRUDR) != 0U))
    {
        SAI4_Block_A->CLRFR = SAI_xCLRFR_COVRUDR;
        SAI4_Block_B->CLRFR = SAI_xCLRFR_COVRUDR;
        Bsp::audioHardwareErrors_++;
    }

    if((isr & BDMA_ISR_HTIF0) != 0U)
    {
        BDMA->IFCR = BDMA_IFCR_CHTIF0;
        Bsp::audioBlockCount_++;
        if(Bsp::audioBlockCallback_ != nullptr)
        {
            Bsp::audioBlockCallback_(&saiRxDmaBuf[0],
                                     &saiTxDmaBuf[0],
                                     dBSP_AUDIO_BLOCK_SAMPLES);
        }
    }

    if((isr & BDMA_ISR_TCIF0) != 0U)
    {
        BDMA->IFCR = BDMA_IFCR_CTCIF0;
        Bsp::audioBlockCount_++;
        if(Bsp::audioBlockCallback_ != nullptr)
        {
            Bsp::audioBlockCallback_(&saiRxDmaBuf[dBSP_AUDIO_BLOCK_WORDS],
                                     &saiTxDmaBuf[dBSP_AUDIO_BLOCK_WORDS],
                                     dBSP_AUDIO_BLOCK_SAMPLES);
        }
    }
}
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Configura a arvore de clock para operacao a 550 MHz via HSE 25 MHz.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::SystemClockConfig(void)
{
    RCC_OscInitTypeDef rccOscInitStruct = {};
    RCC_ClkInitTypeDef rccClkInitStruct = {};

    // 1. Configuracao da fonte de alimentacao do nucleo para modo LDO
    HAL_PWREx_ConfigSupply(PWR_LDO_SUPPLY);

    // 2. Escala de tensao VOS0 para suportar frequencia maxima de 550 MHz
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE0);

    while(!__HAL_PWR_GET_FLAG(PWR_FLAG_VOSRDY))
    {
        // Aguarda estabilizacao do regulador de tensao
    }

    // 3. Inicializacao do oscilador externo HSE de 25 MHz e PLL1
    rccOscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    rccOscInitStruct.HSEState = RCC_HSE_ON;
    rccOscInitStruct.PLL.PLLState = RCC_PLL_ON;
    rccOscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    rccOscInitStruct.PLL.PLLM = dPLL_M_VALUE;
    rccOscInitStruct.PLL.PLLN = dPLL_N_VALUE;
    rccOscInitStruct.PLL.PLLP = dPLL_P_VALUE;
    rccOscInitStruct.PLL.PLLQ = dPLL_Q_VALUE;
    rccOscInitStruct.PLL.PLLR = dPLL_R_VALUE;
    rccOscInitStruct.PLL.PLLRGE = RCC_PLL1VCIRANGE_2;
    rccOscInitStruct.PLL.PLLVCOSEL = RCC_PLL1VCOWIDE;
    rccOscInitStruct.PLL.PLLFRACN = 0U;

    if(HAL_RCC_OscConfig(&rccOscInitStruct) != HAL_OK)
    {
        ErrorHandler();
    }

    // 4. Inicializacao dos barramentos CPU, AHB e APB (SYSCLK=550MHz, HCLK=275MHz)
    rccClkInitStruct.ClockType = (RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                                  RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2 |
                                  RCC_CLOCKTYPE_D3PCLK1 | RCC_CLOCKTYPE_D1PCLK1);
    rccClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    rccClkInitStruct.SYSCLKDivider = RCC_SYSCLK_DIV1;
    rccClkInitStruct.AHBCLKDivider = RCC_HCLK_DIV2;
    rccClkInitStruct.APB3CLKDivider = RCC_APB3_DIV2;
    rccClkInitStruct.APB1CLKDivider = RCC_APB1_DIV2;
    rccClkInitStruct.APB2CLKDivider = RCC_APB2_DIV2;
    rccClkInitStruct.APB4CLKDivider = RCC_APB4_DIV2;

    if(HAL_RCC_ClockConfig(&rccClkInitStruct, FLASH_LATENCY_3) != HAL_OK)
    {
        ErrorHandler();
    }
}

/******************************************************************************/
/** @brief Configura a Unidade de Protecao de Memoria (MPU).
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::MpuConfig(void)
{
    MPU_Region_InitTypeDef mpuInitStruct = {};

    HAL_MPU_Disable();

    // Regiao 0: Protecao de acesso ao espaco global de 4GB
    mpuInitStruct.Enable = MPU_REGION_ENABLE;
    mpuInitStruct.Number = MPU_REGION_NUMBER0;
    mpuInitStruct.BaseAddress = 0x00000000UL;
    mpuInitStruct.Size = MPU_REGION_SIZE_4GB;
    mpuInitStruct.SubRegionDisable = 0x87U;
    mpuInitStruct.TypeExtField = MPU_TEX_LEVEL0;
    mpuInitStruct.AccessPermission = MPU_REGION_NO_ACCESS;
    mpuInitStruct.DisableExec = MPU_INSTRUCTION_ACCESS_DISABLE;
    mpuInitStruct.IsShareable = MPU_ACCESS_SHAREABLE;
    mpuInitStruct.IsCacheable = MPU_ACCESS_NOT_CACHEABLE;
    mpuInitStruct.IsBufferable = MPU_ACCESS_NOT_BUFFERABLE;

    HAL_MPU_ConfigRegion(&mpuInitStruct);

    // Regiao 1: D3 SRAM4 (0x38000000, 16KB) Normal Non-Cacheable para buffers BDMA
    mpuInitStruct.Enable = MPU_REGION_ENABLE;
    mpuInitStruct.Number = MPU_REGION_NUMBER1;
    mpuInitStruct.BaseAddress = 0x38000000UL;
    mpuInitStruct.Size = MPU_REGION_SIZE_16KB;
    mpuInitStruct.SubRegionDisable = 0x00U;
    mpuInitStruct.TypeExtField = MPU_TEX_LEVEL1;
    mpuInitStruct.AccessPermission = MPU_REGION_FULL_ACCESS;
    mpuInitStruct.DisableExec = MPU_INSTRUCTION_ACCESS_DISABLE;
    mpuInitStruct.IsShareable = MPU_ACCESS_NOT_SHAREABLE;
    mpuInitStruct.IsCacheable = MPU_ACCESS_NOT_CACHEABLE;
    mpuInitStruct.IsBufferable = MPU_ACCESS_NOT_BUFFERABLE;

    HAL_MPU_ConfigRegion(&mpuInitStruct);
    HAL_MPU_Enable(MPU_PRIVILEGED_DEFAULT);
}

/******************************************************************************/
/** @brief Ativa as memorias cache L1 de instrucao e de dados do Cortex-M7.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::CacheConfig(void)
{
#if (dBSP_USE_ICACHE == dTRUE)
    SCB_EnableICache();
#endif

#if (dBSP_USE_DCACHE == dTRUE)
    SCB_EnableDCache();
#endif
}

/******************************************************************************/
/** @brief Inicializa o contador de ciclos DWT para suporte a delays precisos.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::DwtConfig(void)
{
#if (dBSP_USE_DWT == dTRUE)
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;

    // Desbloqueia escrita nos registradores DWT se o registrador LAR estiver disponivel
#if defined(DWT_LAR_LAR_Msk)
    DWT->LAR = dDWT_LAR_UNLOCK_KEY;
#endif

    DWT->CYCCNT = 0U;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
#endif
}

/******************************************************************************/
/** @brief Inicializa os pinos de GPIO dos LEDs, chaves, codec CS4272 e UART3.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::GpioConfig(void)
{
    GPIO_InitTypeDef gpioInitStruct = {};

    // Habilita clocks das portas GPIO necessarias
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOD_CLK_ENABLE();
    __HAL_RCC_GPIOE_CLK_ENABLE();

    // 1. LEDs (PE7, PE8, PE9, PE15 e LED Onboard PE3)
    gpioInitStruct.Pin = (dPIN_LED1 | dPIN_LED2 | dPIN_LED3 | dPIN_LED4 | dPIN_LED_ONBOARD);
    gpioInitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInitStruct.Pull = GPIO_NOPULL;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOE, &gpioInitStruct);

    // Estado seguro inicial: LEDs desligados (PE3 em nivel HIGH, demais em LOW)
    HAL_GPIO_WritePin(GPIOE, (dPIN_LED1 | dPIN_LED2 | dPIN_LED3 | dPIN_LED4), GPIO_PIN_RESET);
    HAL_GPIO_WritePin(GPIOE, dPIN_LED_ONBOARD, GPIO_PIN_SET);

    // 2. Chaves com retencao (PC0, PC1, PC2, PC3) com Pull-Up interno
    gpioInitStruct.Pin = (dPIN_SW1 | dPIN_SW2 | dPIN_SW3 | dPIN_SW4);
    gpioInitStruct.Mode = GPIO_MODE_INPUT;
    gpioInitStruct.Pull = GPIO_PULLUP;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &gpioInitStruct);

    // Fecha as chaves analogicas internas de PC2 e PC3 para roteamento dos pinos PC2_C/PC3_C
    __HAL_RCC_SYSCFG_CLK_ENABLE();
    HAL_SYSCFG_AnalogSwitchConfig(SYSCFG_SWITCH_PC2, SYSCFG_SWITCH_PC2_CLOSE);
    HAL_SYSCFG_AnalogSwitchConfig(SYSCFG_SWITCH_PC3, SYSCFG_SWITCH_PC3_CLOSE);

    // 3. Reset de hardware do Codec CS4272 (PD10)
    gpioInitStruct.Pin = dPIN_CS4272_RST;
    gpioInitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    gpioInitStruct.Pull = GPIO_NOPULL;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOD, &gpioInitStruct);
    HAL_GPIO_WritePin(GPIOD, dPIN_CS4272_RST, GPIO_PIN_RESET);

    // 4. I2C1 (PB8 SCL, PB9 SDA) com Open-Drain
    gpioInitStruct.Pin = (dPIN_I2C1_SCL | dPIN_I2C1_SDA);
    gpioInitStruct.Mode = GPIO_MODE_AF_OD;
    gpioInitStruct.Pull = GPIO_NOPULL;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpioInitStruct.Alternate = GPIO_AF4_I2C1;
    HAL_GPIO_Init(GPIOB, &gpioInitStruct);

    // 5. SAI4 Audio: PE0 (MCLK), PE4 (FS), PE5 (SCK), PE6 (SD_A)
    gpioInitStruct.Pin = dPIN_SAI4_MCLK;
    gpioInitStruct.Mode = GPIO_MODE_AF_PP;
    gpioInitStruct.Pull = GPIO_NOPULL;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpioInitStruct.Alternate = GPIO_AF10_SAI4;
    HAL_GPIO_Init(GPIOE, &gpioInitStruct);

    // PE4/PE5/PE6 expose SAI4 on AF8, unlike PE0 on AF10.
    gpioInitStruct.Pin = (dPIN_SAI4_FS | dPIN_SAI4_SCK | dPIN_SAI4_SDA);
    gpioInitStruct.Alternate = GPIO_AF8_SAI4;
    HAL_GPIO_Init(GPIOE, &gpioInitStruct);

    // 6. SAI4 Audio: PA0 (SD_B)
    gpioInitStruct.Pin = dPIN_SAI4_SDB;
    gpioInitStruct.Mode = GPIO_MODE_AF_PP;
    gpioInitStruct.Pull = GPIO_NOPULL;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpioInitStruct.Alternate = GPIO_AF10_SAI4;
    HAL_GPIO_Init(GPIOA, &gpioInitStruct);

    // 7. USART3 Inter-MCU: PD8 (TX), PD9 (RX)
    gpioInitStruct.Pin = (dPIN_USART3_TX | dPIN_USART3_RX);
    gpioInitStruct.Mode = GPIO_MODE_AF_PP;
    gpioInitStruct.Pull = GPIO_PULLUP;
    gpioInitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    gpioInitStruct.Alternate = GPIO_AF7_USART3;
    HAL_GPIO_Init(GPIOD, &gpioInitStruct);
}

/******************************************************************************/
/** @brief Inicializa o periferico I2C1 para comunicacao de controle do codec.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::I2c1Config(void)
{
    RCC_OscInitTypeDef hsiConfig = {};
    hsiConfig.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    hsiConfig.HSIState = RCC_HSI_DIV1;
    hsiConfig.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    if(HAL_RCC_OscConfig(&hsiConfig) != HAL_OK)
    {
        ErrorHandler();
    }
    DelayUs(10U); // HSI stabilization before the first control transaction.
    RCC_PeriphCLKInitTypeDef clockConfig = {};
    clockConfig.PeriphClockSelection = RCC_PERIPHCLK_I2C1;
    clockConfig.I2c123ClockSelection = RCC_I2C123CLKSOURCE_HSI;
    if(HAL_RCCEx_PeriphCLKConfig(&clockConfig) != HAL_OK)
    {
        ErrorHandler();
    }
    __HAL_RCC_I2C1_CLK_ENABLE();

    hi2c1.Instance = I2C1;
    hi2c1.Init.Timing = dI2C1_TIMING_VALUE;
    hi2c1.Init.OwnAddress1 = 0U;
    hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.OwnAddress2 = 0U;
    hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;

    if(HAL_I2C_Init(&hi2c1) != HAL_OK)
    {
        ErrorHandler();
    }

    if(HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
    {
        ErrorHandler();
    }

    if(HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0U) != HAL_OK)
    {
        ErrorHandler();
    }
}

/******************************************************************************/
/** @brief Inicializa o periferico USART3 para comunicacao com ESP32 a 115200.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::Usart3Config(void)
{
    u32 brrValue;

    __HAL_RCC_USART3_CLK_ENABLE();

    // Desabilita USART3 para permitir configuracao dos registradores
    USART3->CR1 = 0U;
    USART3->CR2 = 0U;
    USART3->CR3 = 0U;

    // Calculo do baudrate: BRR = APB1 Clock / 115200 bps
    brrValue = (u32)(dBSP_APB1_FREQ_HZ / dINTER_MCU_UART_BAUDRATE);
    USART3->BRR = brrValue;

    // RX remains interrupt-driven during blocking TX and I2C transactions.
    USART3->ICR = USART_ICR_ORECF | USART_ICR_FECF | USART_ICR_NECF;
    USART3->CR3 = USART_CR3_EIE;
    HAL_NVIC_SetPriority(USART3_IRQn, 5U, 0U);
    HAL_NVIC_EnableIRQ(USART3_IRQn);
    USART3->CR1 = ((u32)USART_CR1_TE | (u32)USART_CR1_RE | (u32)USART_CR1_UE |
                   (u32)USART_CR1_RXNEIE_RXFNEIE);
}

/******************************************************************************/
/** @brief Configura o transporte de audio SAI4 + BDMA em modo ping-pong 48 kHz.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Bsp::Sai4Config(void)
{
    // 1. Configuracao da PLL3 para barramento SAI4 (49.152 MHz)
    RCC_PeriphCLKInitTypeDef periphClkInit = {};
    periphClkInit.PeriphClockSelection = RCC_PERIPHCLK_SAI4A | RCC_PERIPHCLK_SAI4B;
    periphClkInit.Sai4AClockSelection = RCC_SAI4ACLKSOURCE_PLL3;
    periphClkInit.Sai4BClockSelection = RCC_SAI4BCLKSOURCE_PLL3;
    periphClkInit.PLL3.PLL3M = 5U;
    periphClkInit.PLL3.PLL3N = 98U;
    periphClkInit.PLL3.PLL3P = 10U;
    periphClkInit.PLL3.PLL3Q = 10U;
    periphClkInit.PLL3.PLL3R = 10U;
    periphClkInit.PLL3.PLL3RGE = RCC_PLL3VCIRANGE_2;
    periphClkInit.PLL3.PLL3VCOSEL = RCC_PLL3VCOWIDE;
    periphClkInit.PLL3.PLL3FRACN = 2490U;

    if(HAL_RCCEx_PeriphCLKConfig(&periphClkInit) != HAL_OK)
    {
        ErrorHandler();
    }

    // 2. Habilita clocks de barramento para SAI4 e BDMA / DMAMUX2
    __HAL_RCC_SAI4_CLK_ENABLE();
    __HAL_RCC_BDMA_CLK_ENABLE();

    // 3. Inicializa buffers em silencio
    for(u32 i = 0U; i < dBSP_AUDIO_BUFFER_SIZE; i++)
    {
        saiRxDmaBuf[i] = 0;
        saiTxDmaBuf[i] = 0;
    }

    // 4. Configuracao do DMAMUX2 para roteamento das requisicoes SAI4
    DMAMUX2_Channel0->CCR = BDMA_REQUEST_SAI4_B;
    DMAMUX2_Channel1->CCR = BDMA_REQUEST_SAI4_A;

    // 5. Configuracao do BDMA Canal 0 (Recepcao: SAI4_Block_B->DR -> saiRxDmaBuf)
    BDMA_Channel0->CCR = 0U;
    while((BDMA_Channel0->CCR & BDMA_CCR_EN) != 0U)
    {
        // Aguarda desabilitacao do canal
    }
    BDMA->IFCR = (BDMA_IFCR_CGIF0 | BDMA_IFCR_CGIF1);
    BDMA_Channel0->CPAR = (uint32_t)(&(SAI4_Block_B->DR));
    BDMA_Channel0->CM0AR = (uint32_t)saiRxDmaBuf;
    BDMA_Channel0->CNDTR = dBSP_AUDIO_BUFFER_SIZE;
    BDMA_Channel0->CCR = (BDMA_CCR_CIRC | BDMA_CCR_MINC |
                          BDMA_CCR_PSIZE_1 | BDMA_CCR_MSIZE_1 |
                          BDMA_CCR_PL_1 | BDMA_CCR_PL_0 |
                          BDMA_CCR_HTIE | BDMA_CCR_TCIE | BDMA_CCR_TEIE |
                          BDMA_CCR_EN);

    // 6. Configuracao do BDMA Canal 1 (Transmissao: saiTxDmaBuf -> SAI4_Block_A->DR)
    BDMA_Channel1->CCR = 0U;
    while((BDMA_Channel1->CCR & BDMA_CCR_EN) != 0U)
    {
        // Aguarda desabilitacao do canal
    }
    BDMA_Channel1->CPAR = (uint32_t)(&(SAI4_Block_A->DR));
    BDMA_Channel1->CM0AR = (uint32_t)saiTxDmaBuf;
    BDMA_Channel1->CNDTR = dBSP_AUDIO_BUFFER_SIZE;
    BDMA_Channel1->CCR = (BDMA_CCR_DIR | BDMA_CCR_CIRC | BDMA_CCR_MINC |
                          BDMA_CCR_PSIZE_1 | BDMA_CCR_MSIZE_1 |
                          BDMA_CCR_PL_1 |
                          BDMA_CCR_EN);

    // 7. Configuracao das interrupcoes do BDMA Canal 0 no NVIC
    HAL_NVIC_SetPriority(BDMA_Channel0_IRQn, 6U, 0U);
    HAL_NVIC_EnableIRQ(BDMA_Channel0_IRQn);

    // 8. Configuracao do SAI4 Bloco A (Master TX Assincrono, 24 bits em slot 32 bits)
    SAI4_Block_A->CR1 = 0U;
    while((SAI4_Block_A->CR1 & SAI_xCR1_SAIEN) != 0U)
    {
        // Aguarda desabilitacao
    }
    SAI4_Block_A->CR2 = (SAI_xCR2_FTH_0 | SAI_xCR2_FFLUSH);
    SAI4_Block_A->CLRFR = 0x7FUL;
    SAI4_Block_A->FRCR = ((63U << SAI_xFRCR_FRL_Pos) |
                          (31U << SAI_xFRCR_FSALL_Pos) |
                          SAI_xFRCR_FSDEF |
                          SAI_xFRCR_FSOFF);
    SAI4_Block_A->SLOTR = ((0x0003UL << SAI_xSLOTR_SLOTEN_Pos) |
                           (1U << SAI_xSLOTR_NBSLOT_Pos) |
                           SAI_xSLOTR_SLOTSZ_1);
    SAI4_Block_A->CR1 = ((4U << SAI_xCR1_MCKDIV_Pos) |
                         SAI_xCR1_MCKEN |
                         SAI_xCR1_OUTDRIV |
                         SAI_xCR1_DMAEN |
                         SAI_xCR1_CKSTR |
                         SAI_xCR1_DS_2 |
                         SAI_xCR1_DS_0);

    // 9. Configuracao do SAI4 Bloco B (Slave RX Sincrono com Bloco A, 24 bits)
    SAI4_Block_B->CR1 = 0U;
    while((SAI4_Block_B->CR1 & SAI_xCR1_SAIEN) != 0U)
    {
        // Aguarda desabilitacao
    }
    SAI4_Block_B->CR2 = SAI_xCR2_FFLUSH;
    SAI4_Block_B->CLRFR = 0x7FUL;
    SAI4_Block_B->FRCR = SAI4_Block_A->FRCR;
    SAI4_Block_B->SLOTR = SAI4_Block_A->SLOTR;
    SAI4_Block_B->CR1 = (SAI_xCR1_MODE_1 |
                         SAI_xCR1_MODE_0 |
                         SAI_xCR1_SYNCEN_0 |
                         SAI_xCR1_DMAEN |
                         SAI_xCR1_CKSTR |
                         SAI_xCR1_DS_2 |
                         SAI_xCR1_DS_0);

    // 10. Habilitacao dos blocos SAI: Slave B primeiro, Master A por ultimo
    SAI4_Block_B->CR1 |= SAI_xCR1_SAIEN;
    SAI4_Block_A->CR1 |= SAI_xCR1_SAIEN;
}

/** @} DOXYGEN GROUP TAG END OF FILE */
