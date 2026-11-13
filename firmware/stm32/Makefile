################################################################################
# Makefile for STM32H723VGT6 - Pedaleira Digital MVP Firmware
# Toolchain: GNU Arm Embedded Toolchain (arm-none-eabi-*)
################################################################################

TARGET = pedaleira_stm32_mvp
BUILD_DIR = build

PREFIX = arm-none-eabi-
CC = $(PREFIX)gcc
CXX = $(PREFIX)g++
AS = $(PREFIX)gcc -x assembler-with-cpp
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size
HEX = $(CP) -O ihex
BIN = $(CP) -O binary -S

MCU = -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard

C_DEFS = \
	-DSTM32H723xx \
	-DUSE_HAL_DRIVER

C_INCLUDES = \
	-ICore/Inc \
	-IDrivers/STM32H7xx_HAL_Driver/Inc \
	-IDrivers/STM32H7xx_HAL_Driver/Inc/Legacy \
	-IDrivers/CMSIS/Device/ST/STM32H7xx/Include \
	-IDrivers/CMSIS/Include

OPT = -O2

CFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -Wextra -Werror -Wno-unused-parameter -fdata-sections -ffunction-sections
CXXFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -std=c++17 -Wall -Wextra -Werror -Wno-unused-parameter -fdata-sections -ffunction-sections -fno-exceptions -fno-rtti
ASFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections

LDSCRIPT = STM32H723VGTX_FLASH.ld
LDFLAGS = $(MCU) -T$(LDSCRIPT) -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--cref -Wl,--gc-sections

C_SOURCES = \
	Core/Src/stm32h7xx_it.c \
	Core/Src/stm32h7xx_hal_msp.c \
	Core/Src/system_stm32h7xx.c \
	Core/Src/sysmem.c \
	Core/Src/syscalls.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_cortex.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_dma.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_dma_ex.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_exti.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_flash.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_flash_ex.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_gpio.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_hsem.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_i2c.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_i2c_ex.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_mdma.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_pwr.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_pwr_ex.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_rcc.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_rcc_ex.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_tim.c \
	Drivers/STM32H7xx_HAL_Driver/Src/stm32h7xx_hal_tim_ex.c

CPP_SOURCES = \
	Core/Src/Bsp.cpp \
	Core/Src/Cs4272.cpp \
	Core/Src/DspCrossfade.cpp \
	Core/Src/DspDelay.cpp \
	Core/Src/DspEngine.cpp \
	Core/Src/DspEqualizer.cpp \
	Core/Src/DspOverdrive.cpp \
	Core/Src/DspSvf.cpp \
	Core/Src/InterMcuUart.cpp \
	Core/Src/main.cpp \
	Core/Src/PedalLeds.cpp \
	Core/Src/PedalSwitches.cpp

ASM_SOURCES = \
	Core/Startup/startup_stm32h723vgtx.s

OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))

OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(CPP_SOURCES:.cpp=.o)))
vpath %.cpp $(sort $(dir $(CPP_SOURCES)))

OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(ASM_SOURCES:.s=.o)))
vpath %.s $(sort $(dir $(ASM_SOURCES)))

.PHONY: all clean

all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin

$(BUILD_DIR)/%.o: %.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) $< -o $@

$(BUILD_DIR)/%.o: %.cpp Makefile | $(BUILD_DIR)
	$(CXX) -c $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/%.o: %.s Makefile | $(BUILD_DIR)
	$(AS) -c $(ASFLAGS) $< -o $@

$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) Makefile $(LDSCRIPT)
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

$(BUILD_DIR)/%.hex: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(HEX) $< $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(BIN) $< $@

$(BUILD_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR)
