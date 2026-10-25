/******************************************************************************/
/**
 * @file DspEqualizer.cpp
 * @addtogroup DSP_EQUALIZER
 * @brief Implementacao do equalizador de 3 bandas com filtros SVF.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - DspEqualizer.hpp
 *
 * \n <b>Observacoes:</b>
 * - Utiliza tres estagios SVF dedicados para as faixas de grave, medio e agudo.
 * - Converte os ganhos de dB [-12 dB a +12 dB] para escala linear sem alocacao dinamica.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "DspEqualizer.hpp"
#include <cmath>

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dDEFAULT_SAMPLE_RATE               48000.0f
#define dLOW_BAND_RESONANCE                 0.25f
#define dMID_BAND_RESONANCE                 0.50f
#define dHIGH_BAND_RESONANCE                0.25f

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
/** @brief Construtor padrao da classe DspEqualizer.
 ******************************************************************************/
DspEqualizer::DspEqualizer()
    : sampleRate_(dDEFAULT_SAMPLE_RATE)
    , lowGainDb_(0.0f)
    , midGainDb_(0.0f)
    , trebleGainDb_(0.0f)
    , lowGainLinear_(1.0f)
    , midGainLinear_(1.0f)
    , trebleGainLinear_(1.0f)
    , isEnabled_(false)
    , svfLow_()
    , svfMid_()
    , svfHigh_()
{
    Init(dDEFAULT_SAMPLE_RATE);
}

/******************************************************************************/
/** @brief Inicializa os tres filtros de bandas e coeficientes de ganho.
 * @param sampleRate: Taxa de amostragem em Hertz.
 * @retval Nenhum.
 ******************************************************************************/
void DspEqualizer::Init(float sampleRate)
{
    sampleRate_ = sampleRate;
    isEnabled_ = false;

    // Inicializacao dos tres filtros SVF
    svfLow_.Init(sampleRate_);
    svfLow_.SetFreq(dDSP_EQ_LOW_FREQ_HZ);
    svfLow_.SetRes(dLOW_BAND_RESONANCE);

    svfMid_.Init(sampleRate_);
    svfMid_.SetFreq(dDSP_EQ_MID_FREQ_HZ);
    svfMid_.SetRes(dMID_BAND_RESONANCE);

    svfHigh_.Init(sampleRate_);
    svfHigh_.SetFreq(dDSP_EQ_HIGH_FREQ_HZ);
    svfHigh_.SetRes(dHIGH_BAND_RESONANCE);

    SetLowGain(0.0f);
    SetMidGain(0.0f);
    SetTrebleGain(0.0f);
}

/******************************************************************************/
/** @brief Configura o ganho da banda de graves em decibeis (-12 a +12 dB).
 * @param gainDb: Ganho desejado em dB.
 * @retval Nenhum.
 ******************************************************************************/
void DspEqualizer::SetLowGain(float gainDb)
{
    lowGainDb_ = fclamp(gainDb, dDSP_EQ_MIN_GAIN_DB, dDSP_EQ_MAX_GAIN_DB);
    lowGainLinear_ = DbToLinear(lowGainDb_);
}

/******************************************************************************/
/** @brief Configura o ganho da banda de medios em decibeis (-12 a +12 dB).
 * @param gainDb: Ganho desejado em dB.
 * @retval Nenhum.
 ******************************************************************************/
void DspEqualizer::SetMidGain(float gainDb)
{
    midGainDb_ = fclamp(gainDb, dDSP_EQ_MIN_GAIN_DB, dDSP_EQ_MAX_GAIN_DB);
    midGainLinear_ = DbToLinear(midGainDb_);
}

/******************************************************************************/
/** @brief Configura o ganho da banda de agudos em decibeis (-12 a +12 dB).
 * @param gainDb: Ganho desejado em dB.
 * @retval Nenhum.
 ******************************************************************************/
void DspEqualizer::SetTrebleGain(float gainDb)
{
    trebleGainDb_ = fclamp(gainDb, dDSP_EQ_MIN_GAIN_DB, dDSP_EQ_MAX_GAIN_DB);
    trebleGainLinear_ = DbToLinear(trebleGainDb_);
}

/******************************************************************************/
/** @brief Habilita ou desabilita o equalizador de 3 bandas.
 * @param enabled: true para ativar, false para bypass.
 * @retval Nenhum.
 ******************************************************************************/
void DspEqualizer::SetEnabled(bool enabled)
{
    isEnabled_ = enabled;
}

/******************************************************************************/
/** @brief Verifica se o equalizador esta habilitado.
 * @retval bool: true se ativo, false em bypass.
 ******************************************************************************/
bool DspEqualizer::IsEnabled(void) const
{
    return isEnabled_;
}

/******************************************************************************/
/** @brief Processa uma amostra aplicando as curvas de equalizacao parametrica.
 * @param inVal: Amostra de entrada.
 * @retval float: Amostra equalizada (ou sinal puro em bypass).
 ******************************************************************************/
float DspEqualizer::Process(float inVal)
{
    if(isEnabled_ == false)
    {
        return inVal;
    }

    // Processamento de cada filtro SVF para isolamento de banda
    svfLow_.Process(inVal);
    float lowSignal = svfLow_.Low();

    svfMid_.Process(inVal);
    float midSignal = svfMid_.Band();

    svfHigh_.Process(inVal);
    float highSignal = svfHigh_.High();

    // Recomposicao aditiva com ponderacao dos ganhos lineares
    float outSample = inVal +
                      ((lowGainLinear_ - 1.0f) * lowSignal) +
                      ((midGainLinear_ - 1.0f) * midSignal) +
                      ((trebleGainLinear_ - 1.0f) * highSignal);

    return outSample;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Converte ganho em decibeis para multiplicador linear.
 * @param gainDb: Ganho em decibeis.
 * @retval float: Multiplicador linear correspondente.
 ******************************************************************************/
float DspEqualizer::DbToLinear(float gainDb)
{
    return std::pow(10.0f, gainDb * 0.05f);
}

/** @} DOXYGEN GROUP TAG END OF FILE */
