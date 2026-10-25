/******************************************************************************/
/**
 * @file DspOverdrive.hpp
 * @addtogroup DSP_OVERDRIVE
 * @brief Algoritmo de distorcao / overdrive baseado em soft clipping (DaisySP).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_OVERDRIVE_HPP_
#define _DSP_OVERDRIVE_HPP_

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
/// Ganho minimo do estagio de pre-amplificacao
#define dDSP_OVERDRIVE_MIN_GAIN             1.0f

/// Ganho maximo do estagio de pre-amplificacao
#define dDSP_OVERDRIVE_MAX_GAIN             25.0f

/// Frequencia minima de corte do controle de tom em Hz
#define dDSP_OVERDRIVE_TONE_MIN_FREQ        800.0f

/// Frequencia maxima de corte do controle de tom em Hz
#define dDSP_OVERDRIVE_TONE_MAX_FREQ        10000.0f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class DspOverdrive
 * @brief Emulador de distorcao e overdrive analogo com controle de ganho, tom e nivel.
 ******************************************************************************/
class DspOverdrive
{
public:
    DspOverdrive();
    ~DspOverdrive() = default;

    void Init(float sampleRate);
    void SetDrive(float drive);
    void SetTone(float tone);
    void SetLevel(float level);
    void SetEnabled(bool enabled);
    bool IsEnabled(void) const;

    float Process(float inVal);

private:
    float sampleRate_;
    float drive_;
    float tone_;
    float level_;
    float preGain_;
    bool isEnabled_;
    DspSvf toneFilter_;
};

#endif /* _DSP_OVERDRIVE_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
