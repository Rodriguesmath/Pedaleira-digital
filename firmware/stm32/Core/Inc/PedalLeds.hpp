/******************************************************************************/
/**
 * @file PedalLeds.hpp
 * @addtogroup PEDAL_LEDS
 * @brief Classe C++ para controle dos LEDs indicadores da pedaleira digital.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _PEDAL_LEDS_HPP_
#define _PEDAL_LEDS_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/
/// Habilita ou desabilita o suporte ao LED onboard da placa WeAct
#define dPEDAL_LEDS_ENABLE_ONBOARD          dTRUE

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Quantidade total de LEDs suportados pelo modulo
#define dPEDAL_LEDS_TOTAL_COUNT             5U

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Identificadores dos LEDs do sistema
typedef enum
{
    ePEDAL_LEDS_OVERDRIVE,
    ePEDAL_LEDS_EQUALIZER,
    ePEDAL_LEDS_DELAY,
    ePEDAL_LEDS_STATUS,
    ePEDAL_LEDS_ONBOARD,
    ePEDAL_LEDS_COUNT
} pedalLedsId_t;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class PedalLeds
 * @brief Classe responsavel pela gestao dos estados dos LEDs da pedaleira.
 ******************************************************************************/
class PedalLeds
{
public:
    PedalLeds();
    ~PedalLeds() = default;

    static PedalLeds& GetInstance(void);

    void Init(void);
    void Set(pedalLedsId_t ledId, bool state);
    void Toggle(pedalLedsId_t ledId);
    bool Get(pedalLedsId_t ledId) const;
    void AllOff(void);
    void AllOn(void);

private:
    bool states_[ePEDAL_LEDS_COUNT];
    bool isInitialized_;

    void UpdateHardware(pedalLedsId_t ledId);
};

#endif /* _PEDAL_LEDS_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
