/******************************************************************************/
/**
 * @file AssertTypes.hpp
 * @addtogroup ASSERT_TYPES
 * @brief Tipos padronizados de dados e constantes booleanas do Laboratorio ASSERT.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 * @copyright Equipe Pedaleira Digital
 * @note Normas de codificacao: Assert Capacita v1.0 - Polo de Inovacao IFPB.
 * @{
 ******************************************************************************/
#ifndef _ASSERT_TYPES_HPP_
#define _ASSERT_TYPES_HPP_

/*******************************************************************************
 * INCLUDES NECESSARIOS
 ******************************************************************************/
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/*******************************************************************************
 * CONFIGURACOES
 ******************************************************************************/

/*******************************************************************************
 * DEFINES PUBLICOS
 ******************************************************************************/
/// Definicao de valor booleano verdadeiro para compilador e pre-processador
#ifndef dTRUE
#define dTRUE                               1
#endif

/// Definicao de valor booleano falso para compilador e pre-processador
#ifndef dFALSE
#define dFALSE                              0
#endif

/*******************************************************************************
 * TIPOS DE DADOS PUBLICOS
 ******************************************************************************/
/// Tipos inteiros sem sinal
typedef uint8_t                             u8;
typedef uint16_t                            u16;
typedef uint32_t                            u32;
typedef uint64_t                            u64;

/// Tipos inteiros com sinal
typedef int8_t                              s8;
typedef int16_t                             s16;
typedef int32_t                             s32;
typedef int64_t                             s64;

/// Tipos de ponto flutuante
typedef float                               f32;
typedef double                              f64;

/*******************************************************************************
 * PROTOTIPOS PUBLICOS
 ******************************************************************************/

#endif /* _ASSERT_TYPES_HPP_ */
/** @} DOXYGEN GROUP TAG END OF FILE */
