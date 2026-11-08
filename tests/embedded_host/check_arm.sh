#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
output_dir=output/auditoria_rev49/VALIDACAO/embedded
mkdir -p "$output_dir"
arm_cxx=${ARM_CXX:-arm-none-eabi-g++}
"$arm_cxx" --version
for source in Bsp InterMcuUart Cs4272 main; do
    "$arm_cxx" -std=c++17 -mcpu=cortex-m7 -mthumb -mfpu=fpv5-d16 -mfloat-abi=hard -O2 -Wall -Wextra -Werror -Wno-unused-parameter -DSTM32H723xx -DUSE_HAL_DRIVER -Ifirmware/stm32/Core/Inc -Ifirmware/stm32/Drivers/STM32H7xx_HAL_Driver/Inc -Ifirmware/stm32/Drivers/CMSIS/Device/ST/STM32H7xx/Include -Ifirmware/stm32/Drivers/CMSIS/Include -c "firmware/stm32/Core/Src/$source.cpp" -o "$output_dir/$source.arm.o"
    printf 'PASS: Cortex-M7 object %s\n' "$source"
done
arm_nm=$(dirname "$(readlink -f "$(command -v "$arm_cxx")")")/arm-none-eabi-nm
"$arm_nm" "$output_dir/Bsp.arm.o" > "$output_dir/Bsp.arm.symbols.txt"
python3 - <<'PY'
from pathlib import Path
s=Path('output/auditoria_rev49/VALIDACAO/embedded/Bsp.arm.symbols.txt').read_text()
assert ' T USART3_IRQHandler' in s
assert '__atomic_' not in s
print('PASS: strong USART3 ISR; lock-free atomics compile without atomic helper calls')
PY
