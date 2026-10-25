/******************************************************************************/
/**
 * @file DspCrossfade.cpp
 * @addtogroup DSP_CROSSFADE
 * @brief Implementacao do crossfade entre sinais de audio (DaisySP).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - DspCrossfade.hpp
 *
 * \n <b>Observacoes:</b>
 * - Suporta curvas linear e de potencia constante (seno/cosseno).
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "DspCrossfade.hpp"
#include <cmath>

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dPI_OVER_TWO                        (dDSP_PI * 0.5f)

/*******************************************************************************
 * CONSTANTES
 ******************************************************************************/

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
/** @brief Construtor padrao da classe DspCrossfade.
 ******************************************************************************/
DspCrossfade::DspCrossfade()
    : pos_(0.0f)
    , targetPos_(0.0f)
    , step_(dDSP_CROSSFADE_DEFAULT_STEP)
    , curve_(eCROSSFADE_CURVE_CONSTANT_POWER)
    , gainA_(1.0f)
    , gainB_(0.0f)
{
    Init();
}

/******************************************************************************/
/** @brief Inicializa os parametros e calcula os ganhos iniciais.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void DspCrossfade::Init(void)
{
    curve_ = eCROSSFADE_CURVE_CONSTANT_POWER;
    step_ = dDSP_CROSSFADE_DEFAULT_STEP;
    SetPos(0.0f);
}

/******************************************************************************/
/** @brief Seleciona a curva matematica de interpolacao (linear ou potencia constante).
 * @param curve: Tipo de curva conforme crossfadeCurve_t.
 * @retval Nenhum.
 ******************************************************************************/
void DspCrossfade::SetCurve(crossfadeCurve_t curve)
{
    curve_ = curve;
    CalculateGains();
}

/******************************************************************************/
/** @brief Configura a posicao imediata do cursor [0.0 = canal A, 1.0 = canal B].
 * @param pos: Posicao normalizada entre 0.0 e 1.0.
 * @retval Nenhum.
 ******************************************************************************/
void DspCrossfade::SetPos(float pos)
{
    pos_ = fclamp(pos, 0.0f, 1.0f);
    targetPos_ = pos_;
    CalculateGains();
}

/******************************************************************************/
/** @brief Configura a posicao alvo para transicao suave [0.0 = canal A, 1.0 = canal B].
 * @param targetPos: Posicao alvo normalizada entre 0.0 e 1.0.
 * @retval Nenhum.
 ******************************************************************************/
void DspCrossfade::SetTargetPos(float targetPos)
{
    targetPos_ = fclamp(targetPos, 0.0f, 1.0f);
}

/******************************************************************************/
/** @brief Configura o passo de incremento por amostra na transicao suave.
 * @param step: Passo por amostra [0.00001f a 1.0f].
 * @retval Nenhum.
 ******************************************************************************/
void DspCrossfade::SetStep(float step)
{
    step_ = fclamp(step, 0.00001f, 1.0f);
}

/******************************************************************************/
/** @brief Obtem a posicao atual do cursor de crossfade.
 * @retval float: Posicao atual entre 0.0 e 1.0.
 ******************************************************************************/
float DspCrossfade::GetPos(void) const
{
    return pos_;
}

/******************************************************************************/
/** @brief Obtem a posicao alvo da transicao suave.
 * @retval float: Posicao alvo entre 0.0 e 1.0.
 ******************************************************************************/
float DspCrossfade::GetTargetPos(void) const
{
    return targetPos_;
}

/******************************************************************************/
/** @brief Processa e interpola uma amostra entre os canais de entrada A e B.
 * @param inA: Amostra do canal A.
 * @param inB: Amostra do canal B.
 * @retval float: Amostra resultante da transicao.
 ******************************************************************************/
float DspCrossfade::Process(float inA, float inB)
{
    if(pos_ != targetPos_)
    {
        if(pos_ < targetPos_)
        {
            pos_ += step_;
            if(pos_ >= targetPos_)
            {
                pos_ = targetPos_;
            }
        }
        else
        {
            pos_ -= step_;
            if(pos_ <= targetPos_)
            {
                pos_ = targetPos_;
            }
        }

        CalculateGains();
    }

    return (inA * gainA_) + (inB * gainB_);
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Calcula os ganhos de multiplicacao dos canais A e B segundo a curva.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void DspCrossfade::CalculateGains(void)
{
    if(curve_ == eCROSSFADE_CURVE_LINEAR)
    {
        gainA_ = 1.0f - pos_;
        gainB_ = pos_;
    }
    else
    {
        // Curva de potencia constante senoidal (mantem SPL constante no ponto central)
        gainA_ = std::cos(pos_ * dPI_OVER_TWO);
        gainB_ = std::sin(pos_ * dPI_OVER_TWO);
    }
}

/** @} DOXYGEN GROUP TAG END OF FILE */
