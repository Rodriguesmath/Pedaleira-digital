/******************************************************************************/
/**
 * @file Cs4272.hpp
 * @addtogroup CS4272
 * @brief Classe C++ para controle e configuracao do codec de audio Cirrus Logic CS4272.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _CS4272_HPP_
#define _CS4272_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include "AssertTypes.hpp"

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/
/// Volume master padrao inicial ao inicializar o codec (0 a 100%)
#define dCS4272_DEFAULT_VOLUME_PERCENT      80U

/// Tempo maximo de espera em milissegundos para transacoes no barramento I2C
#define dCS4272_I2C_TIMEOUT_MS              100U

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Endereco de barramento I2C do codec CS4272 em formato de 7 bits (AD0 em GND)
#define dCS4272_I2C_ADDR_7BIT               0x10U

/// Endereco de barramento I2C do codec CS4272 em formato alinhado para 8 bits
#define dCS4272_I2C_ADDR_8BIT               0x20U

/// Registradores de configuracao interna do Cirrus Logic CS4272
#define dCS4272_REG_MODE_CTRL_1             0x01U
#define dCS4272_REG_DAC_CTRL                0x02U
#define dCS4272_REG_DAC_VOL_CTRL            0x03U
#define dCS4272_REG_DAC_VOL_A               0x04U
#define dCS4272_REG_DAC_VOL_B               0x05U
#define dCS4272_REG_ADC_CTRL                0x06U
#define dCS4272_REG_MODE_CTRL_2             0x07U
#define dCS4272_REG_CHIP_ID                 0x08U

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Codigos de status das operacoes do driver CS4272
typedef enum
{
    eCS4272_STATUS_OK,
    eCS4272_STATUS_ERROR,
    eCS4272_STATUS_TIMEOUT,
    eCS4272_STATUS_PARAM_ERROR
} cs4272Status_t;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

/******************************************************************************/
/**
 * @class Cs4272
 * @brief Driver orientado a objetos para inicializacao, volume e reset do CS4272.
 ******************************************************************************/
class Cs4272
{
public:
    Cs4272();
    ~Cs4272() = default;

    static Cs4272& GetInstance(void);

    cs4272Status_t Init(void);
    void HardwareReset(void);
    cs4272Status_t WriteRegister(u8 regAddr, u8 regVal);
    cs4272Status_t ReadRegister(u8 regAddr, u8 *pRegVal);
    cs4272Status_t SetMasterVolume(u8 volumePercent);
    cs4272Status_t SetMute(bool muteState);
    bool IsInitialized(void) const;

private:
    u8 masterVolume_;
    bool isMuted_;
    bool isInitialized_;

    static u8 PercentToAttenuation(u8 volumePercent);
};

#endif /* _CS4272_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
