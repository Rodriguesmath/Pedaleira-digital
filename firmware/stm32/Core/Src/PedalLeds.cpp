/******************************************************************************/
/**
 * @file PedalLeds.cpp
 * @addtogroup PEDAL_LEDS
 * @brief Implementacao da classe C++ de controle dos LEDs da pedaleira.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - PedalLeds.hpp
 * - main.h (HAL GPIO)
 *
 * \n <b>Observacoes:</b>
 * - Os LEDs 1 a 4 (PE7, PE8, PE9, PE15) sao ativos em nivel HIGH.
 * - O LED onboard da WeAct MiniSTM32H723 (PE3) e ativo em nivel LOW.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "PedalLeds.hpp"
#include "main.h"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dPIN_LED_OVERDRIVE                  GPIO_PIN_7
#define dPORT_LED_OVERDRIVE                 GPIOE

#define dPIN_LED_EQUALIZER                  GPIO_PIN_8
#define dPORT_LED_EQUALIZER                 GPIOE

#define dPIN_LED_DELAY                      GPIO_PIN_9
#define dPORT_LED_DELAY                     GPIOE

#define dPIN_LED_STATUS                     GPIO_PIN_15
#define dPORT_LED_STATUS                    GPIOE

#define dPIN_LED_ONBOARD                    GPIO_PIN_3
#define dPORT_LED_ONBOARD                   GPIOE

/*******************************************************************************
 * CONSTANTES
 ******************************************************************************/
/// Tabela de mapeamento de pinos GPIO dos LEDs
static const uint16_t ledPins[ePEDAL_LEDS_COUNT] =
{
    dPIN_LED_OVERDRIVE,
    dPIN_LED_EQUALIZER,
    dPIN_LED_DELAY,
    dPIN_LED_STATUS,
    dPIN_LED_ONBOARD
};

/// Tabela de mapeamento de portas GPIO dos LEDs
static GPIO_TypeDef * const ledPorts[ePEDAL_LEDS_COUNT] =
{
    dPORT_LED_OVERDRIVE,
    dPORT_LED_EQUALIZER,
    dPORT_LED_DELAY,
    dPORT_LED_STATUS,
    dPORT_LED_ONBOARD
};

/// Tabela de polaridade ativa de cada LED (true = ativo alto, false = ativo baixo)
static const bool ledActiveHigh[ePEDAL_LEDS_COUNT] =
{
    true,
    true,
    true,
    true,
    false
};

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
/** @brief Retorna a instancia estatica unica (Singleton) de PedalLeds.
 * @retval PedalLeds&: Referencia a instancia global.
 ******************************************************************************/
PedalLeds& PedalLeds::GetInstance(void)
{
    static PedalLeds instance;
    return instance;
}

/******************************************************************************/
/** @brief Construtor padrao da classe PedalLeds.
 ******************************************************************************/
PedalLeds::PedalLeds()
    : states_{false}
    , isInitialized_(false)
{
}

/******************************************************************************/
/** @brief Inicializa o estado logico e fisico dos LEDs do sistema.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void PedalLeds::Init(void)
{
    u8 indexLed;

    for(indexLed = 0U; indexLed < (u8)ePEDAL_LEDS_COUNT; indexLed++)
    {
        states_[indexLed] = false;
        UpdateHardware((pedalLedsId_t)indexLed);
    }

    isInitialized_ = true;
}

/******************************************************************************/
/** @brief Configura o estado logico de um LED especifico.
 * @param ledId: Identificador do LED conforme pedalLedsId_t.
 * @param state: true para aceso, false para apagado.
 * @retval Nenhum.
 ******************************************************************************/
void PedalLeds::Set(pedalLedsId_t ledId, bool state)
{
    if(ledId < ePEDAL_LEDS_COUNT)
    {
        states_[ledId] = state;
        UpdateHardware(ledId);
    }
}

/******************************************************************************/
/** @brief Inverte o estado logico atual de um LED especifico.
 * @param ledId: Identificador do LED conforme pedalLedsId_t.
 * @retval Nenhum.
 ******************************************************************************/
void PedalLeds::Toggle(pedalLedsId_t ledId)
{
    if(ledId < ePEDAL_LEDS_COUNT)
    {
        states_[ledId] = !states_[ledId];
        UpdateHardware(ledId);
    }
}

/******************************************************************************/
/** @brief Retorna o estado logico atual de um LED.
 * @param ledId: Identificador do LED conforme pedalLedsId_t.
 * @retval bool: true para aceso, false para apagado.
 ******************************************************************************/
bool PedalLeds::Get(pedalLedsId_t ledId) const
{
    if(ledId < ePEDAL_LEDS_COUNT)
    {
        return states_[ledId];
    }
    return false;
}

/******************************************************************************/
/** @brief Apaga todos os LEDs do sistema.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void PedalLeds::AllOff(void)
{
    u8 indexLed;

    for(indexLed = 0U; indexLed < (u8)ePEDAL_LEDS_COUNT; indexLed++)
    {
        states_[indexLed] = false;
        UpdateHardware((pedalLedsId_t)indexLed);
    }
}

/******************************************************************************/
/** @brief Acende todos os LEDs do sistema.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void PedalLeds::AllOn(void)
{
    u8 indexLed;

    for(indexLed = 0U; indexLed < (u8)ePEDAL_LEDS_COUNT; indexLed++)
    {
        states_[indexLed] = true;
        UpdateHardware((pedalLedsId_t)indexLed);
    }
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Escreve o nivel eletrico correspondente no pino fisico do GPIO.
 * @param ledId: Identificador do LED conforme pedalLedsId_t.
 * @retval Nenhum.
 ******************************************************************************/
void PedalLeds::UpdateHardware(pedalLedsId_t ledId)
{
    if(ledId < ePEDAL_LEDS_COUNT)
    {
        bool isLogicOn = states_[ledId];
        GPIO_PinState pinState;

        if(ledActiveHigh[ledId] == true)
        {
            if(isLogicOn == true)
            {
                pinState = GPIO_PIN_SET;
            }
            else
            {
                pinState = GPIO_PIN_RESET;
            }
        }
        else
        {
            if(isLogicOn == true)
            {
                pinState = GPIO_PIN_RESET;
            }
            else
            {
                pinState = GPIO_PIN_SET;
            }
        }

        HAL_GPIO_WritePin(ledPorts[ledId], ledPins[ledId], pinState);
    }
}

/** @} DOXYGEN GROUP TAG END OF FILE */
