/******************************************************************************/
/**
 * @file DspEngine.hpp
 * @addtogroup DSP_ENGINE
 * @brief Nucleo de processamento e encadeamento dos efeitos de audio da pedaleira.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _DSP_ENGINE_HPP_
#define _DSP_ENGINE_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"
#include "DspCrossfade.hpp"
#include "DspDelay.hpp"
#include "DspEqualizer.hpp"
#include "DspMath.hpp"
#include "DspOverdrive.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Taxa de amostragem padrao de operacao do motor DSP em Hz
#define dDSP_ENGINE_DEFAULT_SAMPLE_RATE     48000.0f

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class DspEngine
 * @brief Pipeline central que gerencia o fluxo de sinal [Overdrive -> EQ -> Delay].
 ******************************************************************************/
class DspEngine
{
public:
    DspEngine();
    ~DspEngine() = default;

    void Init(float sampleRate);
    float ProcessSample(float inSample);
    void ProcessBlock(const float *pIn, float *pOut, u32 blockSize);

    // Controles do Overdrive
    void SetOverdriveEnable(bool enable);
    void SetOverdriveDrive(float drive);
    void SetOverdriveTone(float tone);
    void SetOverdriveLevel(float level);
    bool IsOverdriveEnabled(void) const;

    // Controles do Equalizador 3-Bandas
    void SetEqualizerEnable(bool enable);
    void SetEqualizerLow(float gainDb);
    void SetEqualizerMid(float gainDb);
    void SetEqualizerTreble(float gainDb);
    bool IsEqualizerEnabled(void) const;

    // Controles do Delay
    void SetDelayEnable(bool enable);
    void SetDelayTimeMs(float timeMs);
    void SetDelayFeedback(float feedback);
    void SetDelayMix(float mix);
    bool IsDelayEnabled(void) const;

    // Controles Globais de Master
    void SetMasterVolume(float volume);
    void SetMasterBypass(bool bypass);
    void SetMasterMute(bool mute);
    float GetMasterVolume(void) const;
    bool IsMasterBypass(void) const;
    bool IsMasterMuted(void) const;

private:
    float sampleRate_;
    float masterVolume_;
    bool isMasterBypass_;
    bool isMasterMuted_;

    DspOverdrive overdrive_;
    DspEqualizer equalizer_;
    DspDelay delay_;
    DspCrossfade bypassCrossfade_;
};

#endif /* _DSP_ENGINE_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
