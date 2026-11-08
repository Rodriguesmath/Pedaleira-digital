#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
output_dir=output/auditoria_rev49/VALIDACAO/embedded
mkdir -p "$output_dir"
host_cxx=${CXX:-g++}
case "$("$host_cxx" -dumpmachine)" in
    arm*) host_cxx=/tmp/pedaleira-host-cxx/usr/bin/g++ ;;
esac
# This workspace keeps the native compiler extracted locally, without sudo.
if [ "$host_cxx" = /tmp/pedaleira-host-cxx/usr/bin/g++ ]; then
    set -- -B/usr/lib/gcc/x86_64-redhat-linux/16/ -isystem /usr/lib/gcc/x86_64-redhat-linux/16/include -L/tmp/pedaleira-host-cxx/usr/lib64 -fno-use-linker-plugin
else
    set --
fi
"$host_cxx" "$@" -std=c++17 -O1 -g -pthread -fno-omit-frame-pointer -Wall -Wextra -Werror -Itests/embedded_host/stubs -Ifirmware/stm32/Core/Inc tests/embedded_host/test_uart_mute.cpp firmware/stm32/Core/Src/InterMcuUart.cpp firmware/stm32/Core/Src/Cs4272.cpp -o "$output_dir/test_uart_mute"
"$output_dir/test_uart_mute"
python3 tests/test_stm32_cpp_dsp_quality.py
