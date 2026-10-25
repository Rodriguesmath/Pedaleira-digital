/******************************************************************************/
/**
 * @file DspSvf.hpp
 * @addtogroup DSP_SVF
 * @brief Filtro de Variavel de Estado (State Variable Filter) baseado no DaisySP.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_SVF_HPP_
#define _DSP_SVF_HPP_

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
/// Frequencia minima de corte do filtro em Hz
#define dDSP_SVF_MIN_FREQ                   20.0f

/// Fator de amortecimento minimo para estabilidade
#define dDSP_SVF_MIN_DAMPING                0.001f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class DspSvf
 * @brief Classe de filtro SVF que fornece simultaneamente saidas LP, HP, BP e Notch.
 ******************************************************************************/
class DspSvf
{
public:
    DspSvf();
    ~DspSvf() = default;

    void Init(float sampleRate);
    void SetFreq(float freq);
    void SetRes(float res);
    void SetDrive(float drive);
    float Process(float inVal);

    float Low(void) const;
    float High(void) const;
    float Band(void) const;
    float Notch(void) const;
    float Peak(void) const;

private:
    float sampleRate_;
    float freq_;
    float res_;
    float drive_;
    float gCoeff_;
    float hCoeff_;
    float rDamp_;
    float stateLow_;
    float stateBand_;
    float outLow_;
    float outHigh_;
    float outBand_;
    float outNotch_;
    float outPeak_;
};

#endif /* _DSP_SVF_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
