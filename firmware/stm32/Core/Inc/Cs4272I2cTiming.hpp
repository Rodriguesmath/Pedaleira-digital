/******************************************************************************/
/**
 * @file Cs4272I2cTiming.hpp
 * @brief Derived Standard-mode timing for CS4272 (100 kHz maximum).
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 */
#ifndef CS4272_I2C_TIMING_HPP
#define CS4272_I2C_TIMING_HPP
#include <cstdint>
namespace Cs4272I2cTiming
{
    // HSI64 explicitly enabled at DIV1; DNF=0, analog filter enabled.
    // Budget includes HSI +/-5%, rise <=1 us, fall <=300 ns,
    // widened analog-filter delay budget 50..260 ns (AN4235 model).
    // DS13313 table 106 specifies spike filtering 50..80 ns for H723;
    // 260 ns is an intentionally wider calculation assumption, not its spec.
    constexpr uint32_t Presc = 7U;   // tPRESC = 8/64 MHz = 125 ns nominal.
    constexpr uint32_t SclDel = 12U; // 13*tPRESC = 1.625 us setup window.
    constexpr uint32_t SdaDel = 4U;  // 4*tPRESC = 0.500 us hold delay.
    constexpr uint32_t SclHigh = 39U; // 40*tPRESC = 5.000 us before sync.
    constexpr uint32_t SclLow = 47U; // 48*tPRESC = 6.000 us before sync.
    constexpr uint32_t Register = (Presc << 28U) | (SclDel << 20U) |
                                  (SdaDel << 16U) | (SclHigh << 8U) | SclLow;
}
#endif
