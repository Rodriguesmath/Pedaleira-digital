/******************************************************************************/
/**
 * @file DspDelay.hpp
 * @addtogroup DSP_DELAY
 * @brief Linha de atraso digital (Delay) com realimentacao e interpolacao linear.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_DELAY_HPP_
#define _DSP_DELAY_HPP_

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
/// Capacidade maxima do buffer circular de atraso em amostras (1.0s a 48 kHz)
#define dDSP_DELAY_MAX_SAMPLES              48000U

/// Tempo minimo de atraso em milissegundos
#define dDSP_DELAY_MIN_TIME_MS              20.0f

/// Tempo maximo de atraso em milissegundos
#define dDSP_DELAY_MAX_TIME_MS              1000.0f

/// Realimentacao maxima segura para prevencao de instabilidade
#define dDSP_DELAY_MAX_FEEDBACK             0.95f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class DspDelay
 * @brief Modulo de eco e repeticao digital com buffer estatico e controle dry/wet.
 ******************************************************************************/
class DspDelay
{
public:
    DspDelay();
    ~DspDelay() = default;

    void Init(float sampleRate);
    void Reset(void);
    void SetDelayTimeMs(float delayTimeMs);
    void SetFeedback(float feedback);
    void SetMix(float mix);
    void SetEnabled(bool enabled);
    bool IsEnabled(void) const;

    float Process(float inVal);

private:
    float sampleRate_;
    float delayTimeMs_;
    float targetDelaySamples_;
    float currentDelaySamples_;
    float feedback_;
    float mix_;
    bool isEnabled_;
    u32 writeIndex_;

    // Buffer circular estatico alocado em BSS (zero dynamic allocation)
    float delayBuffer_[dDSP_DELAY_MAX_SAMPLES];

    float ReadSampleInterpolated(float delaySamples) const;
};

#endif /* _DSP_DELAY_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
