#ifndef HOST_BSP_HPP
#define HOST_BSP_HPP
#include "AssertTypes.hpp"
#include "main.h"
class Bsp
{
public:
    static bool Usart3ReadEvent(u16* event);
    static void Usart3WriteByte(u8 byte);
    static u32 GetTick(void);
    static void DelayMs(u32 ms);
    static I2C_HandleTypeDef* GetI2c1Handle(void);
};
#endif
