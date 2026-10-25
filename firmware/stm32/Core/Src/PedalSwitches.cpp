/******************************************************************************/
/**
 * @file PedalSwitches.cpp
 * @addtogroup PEDAL_SWITCHES
 * @brief Implementacao da classe C++ de leitura de chaves fisicas com debounce.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - PedalSwitches.hpp
 * - main.h (HAL GPIO e Systick)
 *
 * \n <b>Observacoes:</b>
 * - Pinos PC0..PC3 com Pull-Up interno. Nivel LOW indica chave ligada.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "PedalSwitches.hpp"
#include "main.h"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dPIN_SW1                            GPIO_PIN_0
#define dPORT_SW1                           GPIOC

#define dPIN_SW2                            GPIO_PIN_1
#define dPORT_SW2                           GPIOC

#define dPIN_SW3                            GPIO_PIN_2
#define dPORT_SW3                           GPIOC

#define dPIN_SW4                            GPIO_PIN_3
#define dPORT_SW4                           GPIOC

#define dPROCESS_TICK_STEP_MS               1U

/*******************************************************************************
 * CONSTANTES
 ******************************************************************************/
/// Tabela de pinos GPIO das chaves
static const uint16_t switchPins[ePEDAL_SWITCHES_COUNT] =
{
    dPIN_SW1,
    dPIN_SW2,
    dPIN_SW3,
    dPIN_SW4
};

/// Tabela de portas GPIO das chaves
static GPIO_TypeDef * const switchPorts[ePEDAL_SWITCHES_COUNT] =
{
    dPORT_SW1,
    dPORT_SW2,
    dPORT_SW3,
    dPORT_SW4
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
/** @brief Retorna a instancia estatica unica (Singleton) de PedalSwitches.
 * @retval PedalSwitches&: Referencia a instancia global.
 ******************************************************************************/
PedalSwitches& PedalSwitches::GetInstance(void)
{
    static PedalSwitches instance;
    return instance;
}

/******************************************************************************/
/** @brief Construtor padrao da classe PedalSwitches.
 ******************************************************************************/
PedalSwitches::PedalSwitches()
    : states_{ePEDAL_SWITCHES_STATE_OPEN}
    , rawStates_{ePEDAL_SWITCHES_STATE_OPEN}
    , debounceCounters_{0U}
    , hasChanged_{false}
    , lastTick_(0U)
    , isInitialized_(false)
{
}

/******************************************************************************/
/** @brief Inicializa o estado das chaves e faz a primeira leitura dos pinos.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void PedalSwitches::Init(void)
{
    u8 indexSwitch;
    pedalSwitchesState_t initialState;

    for(indexSwitch = 0U; indexSwitch < (u8)ePEDAL_SWITCHES_COUNT; indexSwitch++)
    {
        initialState = ReadPhysicalPin((pedalSwitchesId_t)indexSwitch);
        states_[indexSwitch] = initialState;
        rawStates_[indexSwitch] = initialState;
        debounceCounters_[indexSwitch] = 0U;
        hasChanged_[indexSwitch] = false;
    }

    lastTick_ = HAL_GetTick();
    isInitialized_ = true;
}

/******************************************************************************/
/** @brief Processa a contagem de debounce digital para todas as chaves.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void PedalSwitches::Process(void)
{
    if(isInitialized_ == false)
    {
        return;
    }

    u32 currentTick = HAL_GetTick();
    u32 elapsedTicks = currentTick - lastTick_;

    if(elapsedTicks >= dPROCESS_TICK_STEP_MS)
    {
        lastTick_ = currentTick;

        u8 indexSwitch;
        for(indexSwitch = 0U; indexSwitch < (u8)ePEDAL_SWITCHES_COUNT; indexSwitch++)
        {
            pedalSwitchesState_t currentRaw = ReadPhysicalPin((pedalSwitchesId_t)indexSwitch);

            if(currentRaw != states_[indexSwitch])
            {
                if(currentRaw == rawStates_[indexSwitch])
                {
                    debounceCounters_[indexSwitch] += elapsedTicks;

                    if(debounceCounters_[indexSwitch] >= (u32)dPEDAL_SWITCHES_DEBOUNCE_TIME_MS)
                    {
                        states_[indexSwitch] = currentRaw;
                        hasChanged_[indexSwitch] = true;
                        debounceCounters_[indexSwitch] = 0U;
                    }
                }
                else
                {
                    rawStates_[indexSwitch] = currentRaw;
                    debounceCounters_[indexSwitch] = 0U;
                }
            }
            else
            {
                rawStates_[indexSwitch] = currentRaw;
                debounceCounters_[indexSwitch] = 0U;
            }
        }
    }
}

/******************************************************************************/
/** @brief Verifica se a chave indicada esta na posicao ativa (fechada para GND).
 * @param switchId: Identificador da chave conforme pedalSwitchesId_t.
 * @retval bool: true se a chave estiver ativa, false se em repouso.
 ******************************************************************************/
bool PedalSwitches::IsActive(pedalSwitchesId_t switchId) const
{
    if(switchId < ePEDAL_SWITCHES_COUNT)
    {
        return (states_[switchId] == ePEDAL_SWITCHES_STATE_CLOSED);
    }
    return false;
}

/******************************************************************************/
/** @brief Informa se houve mudanca de estado e limpa o flag de transicao.
 * @param switchId: Identificador da chave conforme pedalSwitchesId_t.
 * @retval bool: true se comutou desde a ultima leitura, false caso contrario.
 ******************************************************************************/
bool PedalSwitches::HasChanged(pedalSwitchesId_t switchId)
{
    if(switchId < ePEDAL_SWITCHES_COUNT)
    {
        bool changed = hasChanged_[switchId];
        hasChanged_[switchId] = false;
        return changed;
    }
    return false;
}

/******************************************************************************/
/** @brief Retorna o estado logico atual da chave indicada.
 * @param switchId: Identificador da chave conforme pedalSwitchesId_t.
 * @retval pedalSwitchesState_t: Estado atual (aberta ou fechada).
 ******************************************************************************/
pedalSwitchesState_t PedalSwitches::GetState(pedalSwitchesId_t switchId) const
{
    if(switchId < ePEDAL_SWITCHES_COUNT)
    {
        return states_[switchId];
    }
    return ePEDAL_SWITCHES_STATE_OPEN;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Leitura instantanea do nivel fisico no pino de entrada da chave.
 * @param switchId: Identificador da chave conforme pedalSwitchesId_t.
 * @retval pedalSwitchesState_t: Estado instantaneo lido no pino.
 ******************************************************************************/
pedalSwitchesState_t PedalSwitches::ReadPhysicalPin(pedalSwitchesId_t switchId) const
{
    if(switchId < ePEDAL_SWITCHES_COUNT)
    {
        GPIO_PinState readVal = HAL_GPIO_ReadPin(switchPorts[switchId], switchPins[switchId]);

        if(readVal == GPIO_PIN_RESET)
        {
            return ePEDAL_SWITCHES_STATE_CLOSED;
        }
        else
        {
            return ePEDAL_SWITCHES_STATE_OPEN;
        }
    }
    return ePEDAL_SWITCHES_STATE_OPEN;
}

/** @} DOXYGEN GROUP TAG END OF FILE */
