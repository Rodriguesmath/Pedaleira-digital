/******************************************************************************/
/**
 * @file DspEngine.cpp
 * @addtogroup DSP_ENGINE
 * @brief Implementacao do pipeline de processamento DSP da Pedaleira Digital.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - DspEngine.hpp
 *
 * \n <b>Observacoes:</b>
 * - Orquestra a cadeia serial de audio: Entrada -> Overdrive -> EQ -> Delay -> Master.
 * - Suporta processamento amostra por amostra ou por blocos DMA.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "DspEngine.hpp"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dDEFAULT_MASTER_VOLUME             0.80f

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
/** @brief Construtor padrao da classe DspEngine.
 ******************************************************************************/
DspEngine::DspEngine()
    : sampleRate_(dDSP_ENGINE_DEFAULT_SAMPLE_RATE)
    , masterVolume_(dDEFAULT_MASTER_VOLUME)
    , isMasterBypass_(false)
    , isMasterMuted_(false)
    , overdrive_()
    , equalizer_()
    , delay_()
    , bypassCrossfade_()
{
    Init(dDSP_ENGINE_DEFAULT_SAMPLE_RATE);
}

/******************************************************************************/
/** @brief Inicializa o motor de audio e todos os blocos de efeito encadeados.
 * @param sampleRate: Taxa de amostragem em Hertz.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::Init(float sampleRate)
{
    sampleRate_ = sampleRate;
    masterVolume_ = dDEFAULT_MASTER_VOLUME;
    isMasterBypass_ = false;
    isMasterMuted_ = false;

    overdrive_.Init(sampleRate_);
    equalizer_.Init(sampleRate_);
    delay_.Init(sampleRate_);
    bypassCrossfade_.Init();
    bypassCrossfade_.SetPos(0.0f); // 0.0 = sinal processado ativo
}

/******************************************************************************/
/** @brief Processa uma amostra individual de audio pela cadeia de efeitos.
 * @param inSample: Amostra normalizada de entrada [-1.0, 1.0].
 * @retval float: Amostra processada final de saida.
 ******************************************************************************/
float DspEngine::ProcessSample(float inSample)
{
    if(isMasterMuted_ == true)
    {
        return 0.0f;
    }

    float drySignal = inSample;
    float currentSample = inSample;

    // 1. Bloco Overdrive / Distorcao
    currentSample = overdrive_.Process(currentSample);

    // 2. Bloco Equalizador de 3 Bandas
    currentSample = equalizer_.Process(currentSample);

    // 3. Bloco Delay / Eco Digital
    currentSample = delay_.Process(currentSample);

    // 4. Selecao de Master Bypass com crossfade anti-pop
    float wetSignal = currentSample;
    float mixedSignal = bypassCrossfade_.Process(wetSignal, drySignal);

    // 5. Volume Master e ceifamento de seguranca
    float finalOutput = mixedSignal * masterVolume_;
    return fclamp(finalOutput, -1.0f, 1.0f);
}

/******************************************************************************/
/** @brief Processa um bloco continuo de amostras de audio.
 * @param pIn: Ponteiro para o buffer de entrada.
 * @param pOut: Ponteiro para o buffer de saida.
 * @param blockSize: Quantidade de amostras a processar.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::ProcessBlock(const float *pIn, float *pOut, u32 blockSize)
{
    if((pIn == nullptr) || (pOut == nullptr))
    {
        return;
    }

    u32 i;
    for(i = 0U; i < blockSize; i++)
    {
        pOut[i] = ProcessSample(pIn[i]);
    }
}

/******************************************************************************/
/** @brief Habilita ou desabilita o modulo de overdrive.
 * @param enable: true para ativar, false para bypass.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetOverdriveEnable(bool enable)
{
    overdrive_.SetEnabled(enable);
}

/******************************************************************************/
/** @brief Ajusta o ganho de drive do overdrive.
 * @param drive: Intensidade [0.0 a 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetOverdriveDrive(float drive)
{
    overdrive_.SetDrive(drive);
}

/******************************************************************************/
/** @brief Ajusta o tom do filtro do overdrive.
 * @param tone: Frequencia relativa de tonalidade [0.0 a 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetOverdriveTone(float tone)
{
    overdrive_.SetTone(tone);
}

/******************************************************************************/
/** @brief Ajusta o volume de saida individual do overdrive.
 * @param level: Nivel de saida [0.0 a 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetOverdriveLevel(float level)
{
    overdrive_.SetLevel(level);
}

/******************************************************************************/
/** @brief Informa se o overdrive esta habilitado.
 * @retval bool: true se habilitado, false em bypass.
 ******************************************************************************/
bool DspEngine::IsOverdriveEnabled(void) const
{
    return overdrive_.IsEnabled();
}

/******************************************************************************/
/** @brief Habilita ou desabilita o modulo de equalizacao de 3 bandas.
 * @param enable: true para ativar, false para bypass.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetEqualizerEnable(bool enable)
{
    equalizer_.SetEnabled(enable);
}

/******************************************************************************/
/** @brief Configura o ganho da banda de graves em decibeis (-12 a +12 dB).
 * @param gainDb: Ganho desejado em dB.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetEqualizerLow(float gainDb)
{
    equalizer_.SetLowGain(gainDb);
}

/******************************************************************************/
/** @brief Configura o ganho da banda de medios em decibeis (-12 a +12 dB).
 * @param gainDb: Ganho desejado em dB.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetEqualizerMid(float gainDb)
{
    equalizer_.SetMidGain(gainDb);
}

/******************************************************************************/
/** @brief Configura o ganho da banda de agudos em decibeis (-12 a +12 dB).
 * @param gainDb: Ganho desejado em dB.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetEqualizerTreble(float gainDb)
{
    equalizer_.SetTrebleGain(gainDb);
}

/******************************************************************************/
/** @brief Informa se o equalizador esta habilitado.
 * @retval bool: true se habilitado, false em bypass.
 ******************************************************************************/
bool DspEngine::IsEqualizerEnabled(void) const
{
    return equalizer_.IsEnabled();
}

/******************************************************************************/
/** @brief Habilita ou desabilita o modulo de delay.
 * @param enable: true para ativar, false para bypass.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetDelayEnable(bool enable)
{
    delay_.SetEnabled(enable);
}

/******************************************************************************/
/** @brief Configura o tempo de repeticao do delay em milissegundos.
 * @param timeMs: Tempo em milissegundos [20 a 1000 ms].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetDelayTimeMs(float timeMs)
{
    delay_.SetDelayTimeMs(timeMs);
}

/******************************************************************************/
/** @brief Configura o fator de realimentacao do delay.
 * @param feedback: Realimentacao [0.0 a 0.95].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetDelayFeedback(float feedback)
{
    delay_.SetFeedback(feedback);
}

/******************************************************************************/
/** @brief Configura o balanco entre sinal seco e eco no delay.
 * @param mix: Proporcao Dry/Wet [0.0 a 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetDelayMix(float mix)
{
    delay_.SetMix(mix);
}

/******************************************************************************/
/** @brief Informa se o delay esta habilitado.
 * @retval bool: true se habilitado, false em bypass.
 ******************************************************************************/
bool DspEngine::IsDelayEnabled(void) const
{
    return delay_.IsEnabled();
}

/******************************************************************************/
/** @brief Ajusta o volume geral master de saida da pedaleira.
 * @param volume: Volume normalizado [0.0 a 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetMasterVolume(float volume)
{
    masterVolume_ = fclamp(volume, 0.0f, 1.0f);
}

/******************************************************************************/
/** @brief Habilita ou desabilita o Master Bypass de todos os efeitos.
 * @param bypass: true para bypass geral, false para processamento ativo.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetMasterBypass(bool bypass)
{
    isMasterBypass_ = bypass;
    bypassCrossfade_.SetTargetPos(bypass ? 1.0f : 0.0f);
}

/******************************************************************************/
/** @brief Silencia a saida de audio master.
 * @param mute: true para silenciar, false para liberar som.
 * @retval Nenhum.
 ******************************************************************************/
void DspEngine::SetMasterMute(bool mute)
{
    isMasterMuted_ = mute;
}

/******************************************************************************/
/** @brief Obtem o volume geral master atual.
 * @retval float: Volume normalizado [0.0 a 1.0].
 ******************************************************************************/
float DspEngine::GetMasterVolume(void) const
{
    return masterVolume_;
}

/******************************************************************************/
/** @brief Informa se o master bypass global esta ativo.
 * @retval bool: true se em bypass geral, false se operacional.
 ******************************************************************************/
bool DspEngine::IsMasterBypass(void) const
{
    return isMasterBypass_;
}

/******************************************************************************/
/** @brief Informa se a saida de audio master esta silenciada.
 * @retval bool: true se silenciada, false se som liberado.
 ******************************************************************************/
bool DspEngine::IsMasterMuted(void) const
{
    return isMasterMuted_;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/** @} DOXYGEN GROUP TAG END OF FILE */
