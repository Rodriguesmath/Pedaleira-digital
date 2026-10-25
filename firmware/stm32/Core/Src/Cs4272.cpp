/******************************************************************************/
/**
 * @file Cs4272.cpp
 * @addtogroup CS4272
 * @brief Implementacao da classe C++ de controle do codec Cirrus Logic CS4272.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @details
 * \n <b>Ferramentas:</b>
 * - STM32CubeIDE / GCC ARM C++17.
 *
 * \n <b>Dependencias:</b>
 * - Cs4272.hpp
 * - Bsp.hpp
 * - main.h (HAL I2C e GPIO)
 *
 * \n <b>Observacoes:</b>
 * - Linha de reset conectada ao pino PD10 (ativo em LOW).
 * - Barramento de controle I2C1 (PB8 SCL, PB9 SDA).
 *
 * Changelog
 * @version <b>1.0.0 - 25/10/2026</b> \n Equipe Pedaleira Digital \n Primeira versao no padrao ASSERT.
 *
 * @{
 ******************************************************************************/

/*******************************************************************************
 * INCLUDES
 ******************************************************************************/
#include "Cs4272.hpp"
#include "Bsp.hpp"
#include "main.h"

/*******************************************************************************
 * DEFINES LOCAIS
 ******************************************************************************/
#define dPIN_CODEC_RESET                    GPIO_PIN_10
#define dPORT_CODEC_RESET                   GPIOD

#define dRESET_PULSE_LOW_MS                 5U
#define dRESET_POST_DELAY_MS                10U

#define dREG_MODE_CTRL_1_SLAVE_I2S          0x01U
#define dREG_DAC_CTRL_DEFAULT               0x00U
#define dREG_DAC_VOL_CTRL_DEFAULT           0x30U
#define dREG_ADC_CTRL_DEFAULT               0x00U
#define dREG_MODE_CTRL_2_CPEN_PDN           0x03U
#define dREG_MODE_CTRL_2_CPEN_ACTIVE        0x02U

#define dDAC_ATTENUATION_MAX                127U
#define dDAC_ATTENUATION_MUTE               0xFFU
#define dPERCENT_MAX                        100U

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
/** @brief Retorna a instancia estatica unica (Singleton) do driver Cs4272.
 * @retval Cs4272&: Referencia a instancia global.
 ******************************************************************************/
Cs4272& Cs4272::GetInstance(void)
{
    static Cs4272 instance;
    return instance;
}

/******************************************************************************/
/** @brief Construtor padrao da classe Cs4272.
 ******************************************************************************/
Cs4272::Cs4272()
    : masterVolume_(dCS4272_DEFAULT_VOLUME_PERCENT)
    , isMuted_(false)
    , isInitialized_(false)
{
}

/******************************************************************************/
/** @brief Inicializa o codec CS4272 com sequencia de reset e configuracao I2C.
 * @param Nenhum.
 * @retval cs4272Status_t: Codigo de status da operacao.
 ******************************************************************************/
cs4272Status_t Cs4272::Init(void)
{
    cs4272Status_t status = eCS4272_STATUS_OK;

    masterVolume_ = dCS4272_DEFAULT_VOLUME_PERCENT;
    isMuted_ = false;
    isInitialized_ = false;

    // 1. Pulso fisico de reset por hardware
    HardwareReset();

    // 2. Registrador Mode Control 2: Habilita porta de controle em Power Down
    status = WriteRegister(dCS4272_REG_MODE_CTRL_2, dREG_MODE_CTRL_2_CPEN_PDN);
    if(status != eCS4272_STATUS_OK)
    {
        return status;
    }

    // 3. Registrador Mode Control 1: Modo escravo, velocidade simples, formato I2S 24 bits
    status = WriteRegister(dCS4272_REG_MODE_CTRL_1, dREG_MODE_CTRL_1_SLAVE_I2S);
    if(status != eCS4272_STATUS_OK)
    {
        return status;
    }

    // 4. Registrador DAC Control: Filtro padrao com roll-off rapido
    status = WriteRegister(dCS4272_REG_DAC_CTRL, dREG_DAC_CTRL_DEFAULT);
    if(status != eCS4272_STATUS_OK)
    {
        return status;
    }

    // 5. Registrador DAC Volume Control: Soft Ramp e Zero Cross ativados
    status = WriteRegister(dCS4272_REG_DAC_VOL_CTRL, dREG_DAC_VOL_CTRL_DEFAULT);
    if(status != eCS4272_STATUS_OK)
    {
        return status;
    }

    // 6. Configura volume master inicial dos canais A e B
    status = SetMasterVolume(masterVolume_);
    if(status != eCS4272_STATUS_OK)
    {
        return status;
    }

    // 7. Registrador ADC Control: Dither habilitado e filtro passa-altas ativo
    status = WriteRegister(dCS4272_REG_ADC_CTRL, dREG_ADC_CTRL_DEFAULT);
    if(status != eCS4272_STATUS_OK)
    {
        return status;
    }

    // 8. Registrador Mode Control 2: Libera Power Down mantendo porta de controle ativa
    status = WriteRegister(dCS4272_REG_MODE_CTRL_2, dREG_MODE_CTRL_2_CPEN_ACTIVE);
    if(status == eCS4272_STATUS_OK)
    {
        isInitialized_ = true;
    }

    return status;
}

/******************************************************************************/
/** @brief Executa pulso de reset em nivel LOW no pino de hardware PD10.
 * @param Nenhum.
 * @retval Nenhum.
 ******************************************************************************/
void Cs4272::HardwareReset(void)
{
    HAL_GPIO_WritePin(dPORT_CODEC_RESET, dPIN_CODEC_RESET, GPIO_PIN_RESET);
    Bsp::DelayMs(dRESET_PULSE_LOW_MS);

    HAL_GPIO_WritePin(dPORT_CODEC_RESET, dPIN_CODEC_RESET, GPIO_PIN_SET);
    Bsp::DelayMs(dRESET_POST_DELAY_MS);
}

/******************************************************************************/
/** @brief Escreve um valor de 8 bits em um registrador do codec via I2C1.
 * @param regAddr: Endereco do registrador de destino.
 * @param regVal: Valor a ser gravado no registrador.
 * @retval cs4272Status_t: Codigo de status da operacao.
 ******************************************************************************/
cs4272Status_t Cs4272::WriteRegister(u8 regAddr, u8 regVal)
{
    HAL_StatusTypeDef halStatus;
    cs4272Status_t retStatus = eCS4272_STATUS_ERROR;

    halStatus = HAL_I2C_Mem_Write(Bsp::GetI2c1Handle(),
                                  dCS4272_I2C_ADDR_8BIT,
                                  (uint16_t)regAddr,
                                  I2C_MEMADD_SIZE_8BIT,
                                  &regVal,
                                  1U,
                                  dCS4272_I2C_TIMEOUT_MS);

    if(halStatus == HAL_OK)
    {
        retStatus = eCS4272_STATUS_OK;
    }
    else if(halStatus == HAL_TIMEOUT)
    {
        retStatus = eCS4272_STATUS_TIMEOUT;
    }
    else
    {
        retStatus = eCS4272_STATUS_ERROR;
    }

    return retStatus;
}

/******************************************************************************/
/** @brief Le um valor de 8 bits de um registrador do codec via I2C1.
 * @param regAddr: Endereco do registrador a ser lido.
 * @param pRegVal: Ponteiro para armazenar o valor lido.
 * @retval cs4272Status_t: Codigo de status da operacao.
 ******************************************************************************/
cs4272Status_t Cs4272::ReadRegister(u8 regAddr, u8 *pRegVal)
{
    HAL_StatusTypeDef halStatus;
    cs4272Status_t retStatus = eCS4272_STATUS_ERROR;

    if(pRegVal == nullptr)
    {
        return eCS4272_STATUS_PARAM_ERROR;
    }

    halStatus = HAL_I2C_Mem_Read(Bsp::GetI2c1Handle(),
                                 dCS4272_I2C_ADDR_8BIT,
                                 (uint16_t)regAddr,
                                 I2C_MEMADD_SIZE_8BIT,
                                 pRegVal,
                                 1U,
                                 dCS4272_I2C_TIMEOUT_MS);

    if(halStatus == HAL_OK)
    {
        retStatus = eCS4272_STATUS_OK;
    }
    else if(halStatus == HAL_TIMEOUT)
    {
        retStatus = eCS4272_STATUS_TIMEOUT;
    }
    else
    {
        retStatus = eCS4272_STATUS_ERROR;
    }

    return retStatus;
}

/******************************************************************************/
/** @brief Configura o volume master de saida analogica do DAC (0 a 100%).
 * @param volumePercent: Valor percentual de volume (0 = mudo, 100 = 0 dB).
 * @retval cs4272Status_t: Codigo de status da operacao.
 ******************************************************************************/
cs4272Status_t Cs4272::SetMasterVolume(u8 volumePercent)
{
    cs4272Status_t status;
    u8 attenuation;

    if(volumePercent > dPERCENT_MAX)
    {
        return eCS4272_STATUS_PARAM_ERROR;
    }

    masterVolume_ = volumePercent;

    if(isMuted_ == true)
    {
        attenuation = dDAC_ATTENUATION_MUTE;
    }
    else
    {
        attenuation = PercentToAttenuation(volumePercent);
    }

    status = WriteRegister(dCS4272_REG_DAC_VOL_A, attenuation);
    if(status == eCS4272_STATUS_OK)
    {
        status = WriteRegister(dCS4272_REG_DAC_VOL_B, attenuation);
    }

    return status;
}

/******************************************************************************/
/** @brief Habilita ou desabilita o mute de saida dos canais DAC.
 * @param muteState: true para silenciar, false para som liberado.
 * @retval cs4272Status_t: Codigo de status da operacao.
 ******************************************************************************/
cs4272Status_t Cs4272::SetMute(bool muteState)
{
    cs4272Status_t status;
    u8 attenuation;

    isMuted_ = muteState;

    if(muteState == true)
    {
        attenuation = dDAC_ATTENUATION_MUTE;
    }
    else
    {
        attenuation = PercentToAttenuation(masterVolume_);
    }

    status = WriteRegister(dCS4272_REG_DAC_VOL_A, attenuation);
    if(status == eCS4272_STATUS_OK)
    {
        status = WriteRegister(dCS4272_REG_DAC_VOL_B, attenuation);
    }

    return status;
}

/******************************************************************************/
/** @brief Informa se o codec foi inicializado com sucesso.
 * @retval bool: true se inicializado, false caso contrario.
 ******************************************************************************/
bool Cs4272::IsInitialized(void) const
{
    return isInitialized_;
}

/*******************************************************************************
 * FUNCOES LOCAIS
 ******************************************************************************/

/******************************************************************************/
/** @brief Converte percentual de volume (0..100) para valor de atenuacao DAC.
 * @param volumePercent: Valor percentual de 0 a 100.
 * @retval u8: Valor de atenuacao de 8 bits para os registradores de volume.
 ******************************************************************************/
u8 Cs4272::PercentToAttenuation(u8 volumePercent)
{
    u8 attenuation;

    if(volumePercent == 0U)
    {
        attenuation = dDAC_ATTENUATION_MUTE;
    }
    else
    {
        attenuation = (u8)(((u32)(dPERCENT_MAX - volumePercent) * (u32)dDAC_ATTENUATION_MAX) / (u32)dPERCENT_MAX);
    }

    return attenuation;
}

/** @} DOXYGEN GROUP TAG END OF FILE */
