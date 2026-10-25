/******************************************************************************/
/**
 * @file DspMath.hpp
 * @addtogroup DSP_MATH
 * @brief Funcoes matematicas auxiliares e constantes para processamento de audio.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_MATH_HPP_
#define _DSP_MATH_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"
#include <cmath>

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Constante Pi em precisao simples
#define dDSP_PI                             3.14159265358979323846f

/// Constante 2*Pi em precisao simples
#define dDSP_TWO_PI                         6.28318530717958647692f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/** @brief Restringe um valor de ponto flutuante dentro de um intervalo [min, max].
 * @param inVal: Valor de entrada.
 * @param minVal: Limite inferior.
 * @param maxVal: Limite superior.
 * @retval float: Valor limitado ao intervalo.
 ******************************************************************************/
inline float fclamp(float inVal, float minVal, float maxVal)
{
    if(inVal < minVal)
    {
        return minVal;
    }
    else if(inVal > maxVal)
    {
        return maxVal;
    }
    else
    {
        return inVal;
    }
}

/******************************************************************************/
/** @brief Limitador suave simetrico polinomial de 3a ordem (DaisySP SoftLimit).
 * @param inVal: Sinal de entrada.
 * @retval float: Sinal com limitacao suave entre [-1.0, 1.0].
 ******************************************************************************/
inline float SoftLimit(float inVal)
{
    if(inVal <= -3.0f)
    {
        return -1.0f;
    }
    else if(inVal >= 3.0f)
    {
        return 1.0f;
    }
    else
    {
        return (inVal * (27.0f + (inVal * inVal))) / (27.0f + (9.0f * inVal * inVal));
    }
}

/******************************************************************************/
/** @brief Ceifador suave (soft clipping cubico simetrico).
 * @param inVal: Sinal de entrada.
 * @retval float: Sinal com saturacao suave.
 ******************************************************************************/
inline float SoftClip(float inVal)
{
    if(inVal <= -1.0f)
    {
        return -0.66666667f;
    }
    else if(inVal >= 1.0f)
    {
        return 0.66666667f;
    }
    else
    {
        return inVal - ((inVal * inVal * inVal) * 0.33333333f);
    }
}

#endif /* _DSP_MATH_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
