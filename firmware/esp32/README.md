# Firmware ESP32

![ESP32](https://img.shields.io/badge/MCU-ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-660066?style=flat-square&logo=mqtt&logoColor=white)
![Status](https://img.shields.io/badge/Status-a%20iniciar-lightgrey?style=flat-square)

## Sobre

Firmware responsável pela conectividade da pedaleira. Atua como ponte entre
a [STM32](../stm32), onde o áudio é processado, e uma aplicação externa
(mobile/desktop), via MQTT.

Recebe da aplicação as configurações de efeitos, equalização e demais
parâmetros, e repassa essas informações para a STM32 através da interface
de comunicação entre os dois microcontroladores.

## Status

Firmware ainda não iniciado.
