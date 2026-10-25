/******************************************************************************/
/**
 * @file DspDelay.cpp
 * @addtogroup DSP_DELAY
 * @brief Implementacao da linha de atraso digital (DaisySP DelayLine).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - DspDelay.hpp
 *
 * \n <b>Observacoes:</b>
 * - Buffer estatico de 48000 amostras flutuantes em memoria RAM AXI.
 * - Interpolacao hermite/linear para modulacao continua sem artifacts de pitch.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "DspDelay.hpp"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dDEFAULT_SAMPLE_RATE               48000.0f
#define dDEFAULT_DELAY_MS                   350.0f
#define dDEFAULT_FEEDBACK                   0.40f
#define dDEFAULT_MIX                        0.35f
#define dTIME_SMOOTHING_FACTOR              0.005f

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
/** @brief Construtor padrao da classe DspDelay.
 ******************************************************************************/
DspDelay::DspDelay()
    : sampleRate_(dDEFAULT_SAMPLE_RATE)
    , delayTimeMs_(dDEFAULT_DELAY_MS)
    , targetDelaySamples_(16800.0f)
    , currentDelaySamples_(16800.0f)
    , feedback_(dDEFAULT_FEEDBACK)
    , mix_(dDEFAULT_MIX)
    , isEnabled_(false)
    , writeIndex_(0U)
    , delayBuffer_{0.0f}
{
    Init(dDEFAULT_SAMPLE_RATE);
}

/******************************************************************************/
/** @brief Inicializa o buffer de delay, taxa de amostragem e ponteiros.
 * @param sampleRate: Taxa de amostragem em Hertz.
 * @retval Nenhum.
 ******************************************************************************/
void DspDelay::Init(float sampleRate)
{
    sampleRate_ = sampleRate;
    isEnabled_ = false;

    Reset();
    SetDelayTimeMs(dDEFAULT_DELAY_MS);
    SetFeedback(dDEFAULT_FEEDBACK);
    SetMix(dDEFAULT_MIX);
}

/******************************************************************************/
/** @brief Limpa o conteudo de todo o buffer circular de atraso.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void DspDelay::Reset(void)
{
    u32 i;

    for(i = 0U; i < dDSP_DELAY_MAX_SAMPLES; i++)
    {
        delayBuffer_[i] = 0.0f;
    }

    writeIndex_ = 0U;
}

/******************************************************************************/
/** @brief Configura o tempo de atraso em milissegundos (20 a 1000 ms).
 * @param delayTimeMs: Tempo desejado em milissegundos.
 * @retval Nenhum.
 ******************************************************************************/
void DspDelay::SetDelayTimeMs(float delayTimeMs)
{
    delayTimeMs_ = fclamp(delayTimeMs, dDSP_DELAY_MIN_TIME_MS, dDSP_DELAY_MAX_TIME_MS);
    targetDelaySamples_ = (delayTimeMs_ * 0.001f) * sampleRate_;

    if(targetDelaySamples_ >= (float)(dDSP_DELAY_MAX_SAMPLES - 1U))
    {
        targetDelaySamples_ = (float)(dDSP_DELAY_MAX_SAMPLES - 2U);
    }
}

/******************************************************************************/
/** @brief Configura a taxa de realimentacao das repeticoes (0.0 a 0.95).
 * @param feedback: Coeficiente de feedback normalizado.
 * @retval Nenhum.
 ******************************************************************************/
void DspDelay::SetFeedback(float feedback)
{
    feedback_ = fclamp(feedback, 0.0f, dDSP_DELAY_MAX_FEEDBACK);
}

/******************************************************************************/
/** @brief Configura o equilibrio entre sinal direto e sinal com atraso (Dry/Wet).
 * @param mix: Proporcao de mix [0.0 = 100% direto, 1.0 = 100% eco].
 * @retval Nenhum.
 ******************************************************************************/
void DspDelay::SetMix(float mix)
{
    mix_ = fclamp(mix, 0.0f, 1.0f);
}

/******************************************************************************/
/** @brief Habilita ou desabilita o efeito de delay.
 * @param enabled: true para ativar o efeito, false para bypass.
 * @retval Nenhum.
 ******************************************************************************/
void DspDelay::SetEnabled(bool enabled)
{
    isEnabled_ = enabled;
}

/******************************************************************************/
/** @brief Verifica se o efeito de delay esta habilitado.
 * @retval bool: true se ativo, false em bypass.
 ******************************************************************************/
bool DspDelay::IsEnabled(void) const
{
    return isEnabled_;
}

/******************************************************************************/
/** @brief Processa uma amostra inserindo no buffer circular e aplicando mix.
 * @param inVal: Amostra de entrada.
 * @retval float: Amostra processada com eco e sinal direto.
 ******************************************************************************/
float DspDelay::Process(float inVal)
{
    if(isEnabled_ == false)
    {
        return inVal;
    }

    // Suavizacao exponencial da mudanca de tempo para evitar cliques
    currentDelaySamples_ += dTIME_SMOOTHING_FACTOR * (targetDelaySamples_ - currentDelaySamples_);

    // 1. Leitura interpolada da amostra atrasada
    float delayedSample = ReadSampleInterpolated(currentDelaySamples_);

    // 2. Gravacao com realimentacao no buffer circular
    float sampleToWrite = inVal + (delayedSample * feedback_);
    delayBuffer_[writeIndex_] = sampleToWrite;

    // 3. Avanco do indice de escrita com contencao circular
    writeIndex_++;
    if(writeIndex_ >= dDSP_DELAY_MAX_SAMPLES)
    {
        writeIndex_ = 0U;
    }

    // 4. Balanco Dry / Wet de saida
    return (inVal * (1.0f - mix_)) + (delayedSample * mix_);
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Leitura do buffer circular com interpolacao fracionaria linear.
 * @param delaySamples: Distancia do atraso em amostras fracionarias.
 * @retval float: Amostra interpolada.
 ******************************************************************************/
float DspDelay::ReadSampleInterpolated(float delaySamples) const
{
    float readPos = (float)writeIndex_ - delaySamples;

    while(readPos < 0.0f)
    {
        readPos += (float)dDSP_DELAY_MAX_SAMPLES;
    }

    while(readPos >= (float)dDSP_DELAY_MAX_SAMPLES)
    {
        readPos -= (float)dDSP_DELAY_MAX_SAMPLES;
    }

    u32 index0 = (u32)readPos;
    if(index0 >= dDSP_DELAY_MAX_SAMPLES)
    {
        index0 = 0U;
    }

    u32 index1 = index0 + 1U;
    if(index1 >= dDSP_DELAY_MAX_SAMPLES)
    {
        index1 = 0U;
    }

    float frac = readPos - (float)index0;

    return (delayBuffer_[index0] * (1.0f - frac)) + (delayBuffer_[index1] * frac);
}

/** @} DOXYGEN GROUP TAG END OF FILE */
