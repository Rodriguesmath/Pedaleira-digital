/******************************************************************************/
/**
 * @file Bsp.hpp
 * @addtogroup BSP
 * @brief Camada de abstracao de hardware (BSP) em C++ para WeAct MiniSTM32H723 V1.2.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _BSP_HPP_
#define _BSP_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"
#include "main.h"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/
/// Frequencia do oscilador externo HSE de cristal em Hz (25 MHz na placa WeAct)
#define dBSP_HSE_FREQ_HZ                    25000000UL

/// Frequencia maxima da CPU Cortex-M7 em Hz (550 MHz no modo VOS0)
#define dBSP_SYSCLK_FREQ_HZ                 550000000UL

/// Frequencia dos barramentos AHB1, AHB2, AHB3 e AHB4 em Hz (275 MHz maximo)
#define dBSP_HCLK_FREQ_HZ                   275000000UL

/// Frequencia do barramento APB1 em Hz (137.5 MHz maximo)
#define dBSP_APB1_FREQ_HZ                   137500000UL

/// Habilita ou desabilita o cache de instrucoes L1 (I-Cache)
#define dBSP_USE_ICACHE                     dTRUE

/// Habilita ou desabilita o cache de dados L1 (D-Cache)
#define dBSP_USE_DCACHE                     dTRUE

/// Habilita ou desabilita o contador de ciclos DWT (CYCCNT) para delays precisos
#define dBSP_USE_DWT                        dTRUE

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Codigo de erro padrao para falha critica de hardware
#define dBSP_ERROR_CRITICAL                 0xFFFFFFFFUL

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Codigos de status retornados pelas rotinas da camada BSP
typedef enum
{
    eBSP_STATUS_OK,
    eBSP_STATUS_ERROR,
    eBSP_STATUS_CLOCK_ERROR,
    eBSP_STATUS_I2C_ERROR,
    eBSP_STATUS_CODEC_ERROR
} bspStatus_t;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/
#ifdef __cplusplus
extern "C"
{
#endif

void SysTick_Handler(void);
void USART3_IRQHandler(void);

#ifdef __cplusplus
}
#endif

/******************************************************************************/
/**
 * @class Bsp
 * @brief Camada estatica de gerenciamento do hardware da placa STM32H723.
 ******************************************************************************/
class Bsp
{
public:
    Bsp() = delete;
    ~Bsp() = delete;

    static bspStatus_t Init(void);
    static void DelayMs(u32 ms);
    static void DelayUs(u32 us);
    static u32 GetTick(void);

    static void LedOnboardSet(bool state);
    static void LedOnboardToggle(void);

    static void Usart3WriteByte(u8 data);
    static bool Usart3ReadByte(u8 *pData);

    static void ErrorHandler(void);

    static I2C_HandleTypeDef* GetI2c1Handle(void);
    static USART_TypeDef* GetUsart3Handle(void);

private:
    static bool isInitialized_;
    static bool ledOnboardState_;

    static void SystemClockConfig(void);
    static void MpuConfig(void);
    static void CacheConfig(void);
    static void DwtConfig(void);
    static void GpioConfig(void);
    static void I2c1Config(void);
    static void Usart3Config(void);
};

#endif /* _BSP_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
