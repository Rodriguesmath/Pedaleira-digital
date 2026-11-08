#ifndef HOST_MAIN_H
#define HOST_MAIN_H
#include <cstdint>
struct I2C_HandleTypeDef {};
enum HAL_StatusTypeDef { HAL_OK, HAL_ERROR, HAL_BUSY, HAL_TIMEOUT };
enum GPIO_PinState { GPIO_PIN_RESET, GPIO_PIN_SET };
#define GPIO_PIN_10 1024U
#define GPIOD nullptr
#define I2C_MEMADD_SIZE_8BIT 1U
void HAL_GPIO_WritePin(void*, uint16_t, GPIO_PinState);
HAL_StatusTypeDef HAL_I2C_Mem_Write(I2C_HandleTypeDef*, uint16_t, uint16_t, uint16_t, uint8_t*, uint16_t, uint32_t);
HAL_StatusTypeDef HAL_I2C_Mem_Read(I2C_HandleTypeDef*, uint16_t, uint16_t, uint16_t, uint8_t*, uint16_t, uint32_t);
#endif
