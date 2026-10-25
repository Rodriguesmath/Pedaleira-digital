/******************************************************************************/
/**
 * @file DspSvf.cpp
 * @addtogroup DSP_SVF
 * @brief Implementacao do filtro State Variable Filter (DaisySP).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - DspSvf.hpp
 *
 * \n <b>Observacoes:</b>
 * - Baseado na topologia trapezoidal bilineada Chamberlin/Zavalishin.
 * - Calcula simultaneamente saidas passa-baixas, passa-altas, passa-faixa e notch.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "DspSvf.hpp"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dDEFAULT_SAMPLE_RATE               48000.0f
#define dDEFAULT_CUTOFF_FREQ                1000.0f
#define dDEFAULT_RESONANCE                  0.5f
#define dNYQUIST_MARGIN                     0.49f

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
/** @brief Construtor padrao da classe DspSvf.
 ******************************************************************************/
DspSvf::DspSvf()
    : sampleRate_(dDEFAULT_SAMPLE_RATE)
    , freq_(dDEFAULT_CUTOFF_FREQ)
    , res_(dDEFAULT_RESONANCE)
    , drive_(0.0f)
    , gCoeff_(0.0f)
    , hCoeff_(0.0f)
    , rDamp_(1.0f)
    , stateLow_(0.0f)
    , stateBand_(0.0f)
    , outLow_(0.0f)
    , outHigh_(0.0f)
    , outBand_(0.0f)
    , outNotch_(0.0f)
    , outPeak_(0.0f)
{
    Init(dDEFAULT_SAMPLE_RATE);
}

/******************************************************************************/
/** @brief Inicializa o estado interno e coeficientes do filtro.
 * @param sampleRate: Taxa de amostragem em Hertz.
 * @retval Nenhum.
 ******************************************************************************/
void DspSvf::Init(float sampleRate)
{
    sampleRate_ = sampleRate;
    stateLow_ = 0.0f;
    stateBand_ = 0.0f;
    outLow_ = 0.0f;
    outHigh_ = 0.0f;
    outBand_ = 0.0f;
    outNotch_ = 0.0f;
    outPeak_ = 0.0f;
    drive_ = 0.0f;

    SetRes(dDEFAULT_RESONANCE);
    SetFreq(dDEFAULT_CUTOFF_FREQ);
}

/******************************************************************************/
/** @brief Configura a frequencia de corte do filtro.
 * @param freq: Frequencia em Hz [20 Hz a 0.49*Fs].
 * @retval Nenhum.
 ******************************************************************************/
void DspSvf::SetFreq(float freq)
{
    freq_ = fclamp(freq, dDSP_SVF_MIN_FREQ, (sampleRate_ * dNYQUIST_MARGIN));

    float wd = dDSP_PI * freq_;
    float wa = 2.0f * sampleRate_ * tanf(wd / sampleRate_);
    gCoeff_ = wa / (2.0f * sampleRate_);
    hCoeff_ = 1.0f / (1.0f + (rDamp_ * gCoeff_) + (gCoeff_ * gCoeff_));
}

/******************************************************************************/
/** @brief Configura a ressonancia do filtro.
 * @param res: Ressonancia no intervalo normalizado [0.0, 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspSvf::SetRes(float res)
{
    res_ = fclamp(res, 0.0f, 1.0f);
    rDamp_ = 2.0f * (1.0f - res_);

    if(rDamp_ < dDSP_SVF_MIN_DAMPING)
    {
        rDamp_ = dDSP_SVF_MIN_DAMPING;
    }

    hCoeff_ = 1.0f / (1.0f + (rDamp_ * gCoeff_) + (gCoeff_ * gCoeff_));
}

/******************************************************************************/
/** @brief Configura a saturacao no caminho de realimentacao do filtro.
 * @param drive: Intensidade de saturacao [0.0, 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspSvf::SetDrive(float drive)
{
    drive_ = fclamp(drive, 0.0f, 1.0f);
}

/******************************************************************************/
/** @brief Processa uma amostra de audio pelo filtro e atualiza todas as saidas.
 * @param inVal: Amostra de entrada.
 * @retval float: Amostra de saida do filtro passa-baixas (Low).
 ******************************************************************************/
float DspSvf::Process(float inVal)
{
    float inputSample = inVal;

    if(drive_ > 0.0f)
    {
        inputSample = SoftClip(inputSample * (1.0f + drive_));
    }

    float hp = (inputSample - (rDamp_ * stateBand_) - (gCoeff_ * stateBand_) - stateLow_) * hCoeff_;
    float bp = (gCoeff_ * hp) + stateBand_;
    stateBand_ = (gCoeff_ * hp) + bp;
    float lp = (gCoeff_ * bp) + stateLow_;
    stateLow_ = (gCoeff_ * bp) + lp;

    outLow_ = lp;
    outHigh_ = hp;
    outBand_ = bp;
    outNotch_ = hp + lp;
    outPeak_ = lp - hp;

    return outLow_;
}

/******************************************************************************/
/** @brief Retorna o valor atual da saida passa-baixas (Low-Pass).
 * @retval float: Amostra filtrada passa-baixas.
 ******************************************************************************/
float DspSvf::Low(void) const
{
    return outLow_;
}

/******************************************************************************/
/** @brief Retorna o valor atual da saida passa-altas (High-Pass).
 * @retval float: Amostra filtrada passa-altas.
 ******************************************************************************/
float DspSvf::High(void) const
{
    return outHigh_;
}

/******************************************************************************/
/** @brief Retorna o valor atual da saida passa-faixa (Band-Pass).
 * @retval float: Amostra filtrada passa-faixa.
 ******************************************************************************/
float DspSvf::Band(void) const
{
    return outBand_;
}

/******************************************************************************/
/** @brief Retorna o valor atual da saida notch (Rejeita-faixa).
 * @retval float: Amostra filtrada notch.
 ******************************************************************************/
float DspSvf::Notch(void) const
{
    return outNotch_;
}

/******************************************************************************/
/** @brief Retorna o valor atual da saida peaking.
 * @retval float: Amostra filtrada peaking.
 ******************************************************************************/
float DspSvf::Peak(void) const
{
    return outPeak_;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/** @} DOXYGEN GROUP TAG END OF FILE */
