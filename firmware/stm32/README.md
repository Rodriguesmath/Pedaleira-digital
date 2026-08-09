# Firmware STM32

![STM32](https://img.shields.io/badge/MCU-STM32H723VG-03234B?style=flat-square&logo=stmicroelectronics&logoColor=white)
![C](https://img.shields.io/badge/Language-C-A8B9CC?style=flat-square&logo=c&logoColor=white)
![STM32CubeIDE](https://img.shields.io/badge/IDE-STM32CubeIDE-03234B?style=flat-square&logo=stmicroelectronics&logoColor=white)
![Status](https://img.shields.io/badge/Status-em%20desenvolvimento-yellow?style=flat-square)

## Sobre

Firmware responsável pelo processamento digital de áudio da pedaleira,
rodando em um STM32H723VG. É aqui que o sinal do instrumento é capturado,
processado (equalização, distorção, modulação, delay, reverb, entre outros
efeitos a definir) e enviado de volta como saída de áudio, em tempo real.

Recebe da [ESP32](../esp32) as configurações de efeitos e parâmetros
definidas pela aplicação externa via MQTT.

## Estrutura

```
.
├── Core/       # Código da aplicação (main, HAL config, handlers de interrupção)
├── Drivers/    # HAL e CMSIS da ST
├── *.ioc       # Configuração do STM32CubeMX
└── *.ld        # Linker scripts (Flash / RAM)
```

## Hardware

| Função                | Componente  |
|------------------------|-------------|
| Processamento de áudio | STM32H723VG |
| Codec de áudio         | CS4272      |

## Ambiente

Projeto gerenciado via STM32CubeIDE (arquivos `.project` / `.cproject`
presentes na raiz desta pasta).
