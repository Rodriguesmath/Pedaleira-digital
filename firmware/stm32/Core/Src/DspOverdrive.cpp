/******************************************************************************/
/**
 * @file DspOverdrive.cpp
 * @addtogroup DSP_OVERDRIVE
 * @brief Implementacao do bloco de efeito de distorcao e overdrive.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - DspOverdrive.hpp
 *
 * \n <b>Observacoes:</b>
 * - Utiliza a funcao SoftLimit para emulacao da saturacao natural de valvulas.
 * - Inclui estagio de filtragem dinamica de tom via DspSvf.
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "DspOverdrive.hpp"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dDEFAULT_SAMPLE_RATE               48000.0f
#define dDEFAULT_DRIVE                      0.5f
#define dDEFAULT_TONE                       0.5f
#define dDEFAULT_LEVEL                      0.8f
#define dTONE_FILTER_RESONANCE              0.2f

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
/** @brief Construtor padrao da classe DspOverdrive.
 ******************************************************************************/
DspOverdrive::DspOverdrive()
    : sampleRate_(dDEFAULT_SAMPLE_RATE)
    , drive_(dDEFAULT_DRIVE)
    , tone_(dDEFAULT_TONE)
    , level_(dDEFAULT_LEVEL)
    , preGain_(1.0f)
    , isEnabled_(false)
    , toneFilter_()
{
    Init(dDEFAULT_SAMPLE_RATE);
}

/******************************************************************************/
/** @brief Inicializa o bloco de overdrive e o filtro interno de tonalidade.
 * @param sampleRate: Taxa de amostragem em Hertz.
 * @retval Nenhum.
 ******************************************************************************/
void DspOverdrive::Init(float sampleRate)
{
    sampleRate_ = sampleRate;
    isEnabled_ = false;

    toneFilter_.Init(sampleRate_);
    toneFilter_.SetRes(dTONE_FILTER_RESONANCE);

    SetDrive(dDEFAULT_DRIVE);
    SetTone(dDEFAULT_TONE);
    SetLevel(dDEFAULT_LEVEL);
}

/******************************************************************************/
/** @brief Configura a intensidade de distorcao / ganho de entrada.
 * @param drive: Intensidade no intervalo normalizado [0.0, 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspOverdrive::SetDrive(float drive)
{
    drive_ = fclamp(drive, 0.0f, 1.0f);
    // Mapeamento linear para ganho de pre-amplificacao [1.0 a 25.0]
    preGain_ = dDSP_OVERDRIVE_MIN_GAIN + (drive_ * (dDSP_OVERDRIVE_MAX_GAIN - dDSP_OVERDRIVE_MIN_GAIN));
}

/******************************************************************************/
/** @brief Configura a frequencia de corte do controle de tonalidade.
 * @param tone: Tonalidade no intervalo normalizado [0.0, 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspOverdrive::SetTone(float tone)
{
    tone_ = fclamp(tone, 0.0f, 1.0f);
    float cutoffHz = dDSP_OVERDRIVE_TONE_MIN_FREQ + (tone_ * (dDSP_OVERDRIVE_TONE_MAX_FREQ - dDSP_OVERDRIVE_TONE_MIN_FREQ));
    toneFilter_.SetFreq(cutoffHz);
}

/******************************************************************************/
/** @brief Configura o nivel de volume de saida do bloco de distorcao.
 * @param level: Volume de saida no intervalo normalizado [0.0, 1.0].
 * @retval Nenhum.
 ******************************************************************************/
void DspOverdrive::SetLevel(float level)
{
    level_ = fclamp(level, 0.0f, 1.0f);
}

/******************************************************************************/
/** @brief Habilita ou desabilita o processamento do efeito de overdrive.
 * @param enabled: true para ativar o efeito, false para bypass.
 * @retval Nenhum.
 ******************************************************************************/
void DspOverdrive::SetEnabled(bool enabled)
{
    isEnabled_ = enabled;
}

/******************************************************************************/
/** @brief Verifica se o efeito de overdrive esta habilitado.
 * @retval bool: true se ativo, false se em bypass.
 ******************************************************************************/
bool DspOverdrive::IsEnabled(void) const
{
    return isEnabled_;
}

/******************************************************************************/
/** @brief Processa uma amostra de audio aplicando saturacao nao-linear e tom.
 * @param inVal: Amostra de entrada.
 * @retval float: Amostra processada (ou original caso desabilitado).
 ******************************************************************************/
float DspOverdrive::Process(float inVal)
{
    if(isEnabled_ == false)
    {
        return inVal;
    }

    // 1. Amplificacao de entrada com pre-gain
    float pre = inVal * preGain_;

    // 2. Ceifamento suave cubico (DaisySP SoftLimit)
    float clipped = SoftLimit(pre);

    // 3. Filtragem de agudos/tom (Low-pass do SVF)
    float filtered = toneFilter_.Process(clipped);

    // 4. Ajuste de nivel de saida
    return filtered * level_;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/** @} DOXYGEN GROUP TAG END OF FILE */
