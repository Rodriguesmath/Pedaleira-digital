/******************************************************************************/
/**
 * @file PedalSwitches.hpp
 * @addtogroup PEDAL_SWITCHES
 * @brief Classe C++ para debounce e leitura das chaves fisicas de retencao.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _PEDAL_SWITCHES_HPP_
#define _PEDAL_SWITCHES_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/
/// Tempo de debounce em milissegundos para confirmacao de estado
#define dPEDAL_SWITCHES_DEBOUNCE_TIME_MS    20U

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Quantidade total de chaves fisicas do pedal
#define dPEDAL_SWITCHES_TOTAL_COUNT         4U

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Identificadores das chaves fisicas
typedef enum
{
    ePEDAL_SWITCHES_SW1,
    ePEDAL_SWITCHES_SW2,
    ePEDAL_SWITCHES_SW3,
    ePEDAL_SWITCHES_SW4,
    ePEDAL_SWITCHES_COUNT
} pedalSwitchesId_t;

/// Estados estaveis possiveis de uma chave fisica
typedef enum
{
    ePEDAL_SWITCHES_STATE_OPEN,
    ePEDAL_SWITCHES_STATE_CLOSED
} pedalSwitchesState_t;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class PedalSwitches
 * @brief Gerenciador com debounce digital para leitura das 4 chaves mecanicas.
 ******************************************************************************/
class PedalSwitches
{
public:
    PedalSwitches();
    ~PedalSwitches() = default;

    static PedalSwitches& GetInstance(void);

    void Init(void);
    void Process(void);
    bool IsActive(pedalSwitchesId_t switchId) const;
    bool HasChanged(pedalSwitchesId_t switchId);
    pedalSwitchesState_t GetState(pedalSwitchesId_t switchId) const;

private:
    pedalSwitchesState_t states_[ePEDAL_SWITCHES_COUNT];
    pedalSwitchesState_t rawStates_[ePEDAL_SWITCHES_COUNT];
    u32 debounceCounters_[ePEDAL_SWITCHES_COUNT];
    bool hasChanged_[ePEDAL_SWITCHES_COUNT];
    u32 lastTick_;
    bool isInitialized_;

    pedalSwitchesState_t ReadPhysicalPin(pedalSwitchesId_t switchId) const;
};

#endif /* _PEDAL_SWITCHES_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
