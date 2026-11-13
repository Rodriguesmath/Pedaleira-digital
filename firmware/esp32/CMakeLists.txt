cmake_minimum_required(VERSION 3.16)

# ESP-IDF Project Definition
if(DEFINED ENV{IDF_PATH})
    include($ENV{IDF_PATH}/tools/cmake/project.cmake)
    project(pedaleira_esp32_bridge)
else()
    # Standalone CMake build for host tools/verification
    project(pedaleira_esp32_bridge C CXX)
    set(CMAKE_C_STANDARD 11)
    set(CMAKE_C_STANDARD_REQUIRED ON)
    include_directories(include)
    add_library(esp32_bridge_core STATIC
        src/inter_mcu_proto.c
        src/pedal_bridge.c
    )
    add_executable(test_esp32_bridge
        tests/test_esp32_bridge.c
        src/inter_mcu_proto.c
        src/pedal_bridge.c
    )
endif()
