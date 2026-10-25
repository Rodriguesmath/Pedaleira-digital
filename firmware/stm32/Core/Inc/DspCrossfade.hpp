/******************************************************************************/
/**
 * @file DspCrossfade.hpp
 * @addtogroup DSP_CROSSFADE
 * @brief Modulo de transicao suave entre dois sinais de audio (DaisySP CrossFade).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_CROSSFADE_HPP_
#define _DSP_CROSSFADE_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"
#include "DspMath.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Incremento linear padrao por amostra para transicao suave (~10 ms a 48 kHz)
#define dDSP_CROSSFADE_DEFAULT_STEP         0.002f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Curvas de interpolacao disponiveis para crossfade
typedef enum
{
    eCROSSFADE_CURVE_LINEAR,
    eCROSSFADE_CURVE_CONSTANT_POWER
} crossfadeCurve_t;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class DspCrossfade
 * @brief Gerenciador de transicao suave para prevencao de pop/clique no bypass.
 ******************************************************************************/
class DspCrossfade
{
public:
    DspCrossfade();
    ~DspCrossfade() = default;

    void Init(void);
    void SetCurve(crossfadeCurve_t curve);
    void SetPos(float pos);
    void SetTargetPos(float targetPos);
    void SetStep(float step);
    float GetPos(void) const;
    float GetTargetPos(void) const;

    float Process(float inA, float inB);

private:
    float pos_;
    float targetPos_;
    float step_;
    crossfadeCurve_t curve_;
    float gainA_;
    float gainB_;

    void CalculateGains(void);
};

#endif /* _DSP_CROSSFADE_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
