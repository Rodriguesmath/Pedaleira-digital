/******************************************************************************/
/**
 * @file DspEqualizer.hpp
 * @addtogroup DSP_EQUALIZER
 * @brief Equalizador parametrico de 3 bandas (Grave, Medio, Agudo) via DspSvf.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_EQUALIZER_HPP_
#define _DSP_EQUALIZER_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"
#include "DspMath.hpp"
#include "DspSvf.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Frequencia central padrao da banda de graves em Hz
#define dDSP_EQ_LOW_FREQ_HZ                 100.0f

/// Frequencia central padrao da banda de medios em Hz
#define dDSP_EQ_MID_FREQ_HZ                 1000.0f

/// Frequencia central padrao da banda de agudos em Hz
#define dDSP_EQ_HIGH_FREQ_HZ                4000.0f

/// Ganho minimo em dB para cada banda
#define dDSP_EQ_MIN_GAIN_DB                 -12.0f

/// Ganho maximo em dB para cada banda
#define dDSP_EQ_MAX_GAIN_DB                 12.0f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class DspEqualizer
 * @brief Equalizador de 3 bandas com filtros SVF em paralelo e ganho em decibeis.
 ******************************************************************************/
class DspEqualizer
{
public:
    DspEqualizer();
    ~DspEqualizer() = default;

    void Init(float sampleRate);
    void SetLowGain(float gainDb);
    void SetMidGain(float gainDb);
    void SetTrebleGain(float gainDb);
    void SetEnabled(bool enabled);
    bool IsEnabled(void) const;

    float Process(float inVal);

private:
    float sampleRate_;
    float lowGainDb_;
    float midGainDb_;
    float trebleGainDb_;
    float lowGainLinear_;
    float midGainLinear_;
    float trebleGainLinear_;
    bool isEnabled_;

    DspSvf svfLow_;
    DspSvf svfMid_;
    DspSvf svfHigh_;

    static float DbToLinear(float gainDb);
};

#endif /* _DSP_EQUALIZER_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
