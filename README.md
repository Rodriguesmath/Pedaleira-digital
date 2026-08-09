# Pedaleira Digital

![STM32](https://img.shields.io/badge/MCU-STM32H723VG-03234B?style=flat-square&logo=stmicroelectronics&logoColor=white)
![ESP32](https://img.shields.io/badge/Connectivity-ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-660066?style=flat-square&logo=mqtt&logoColor=white)
![C](https://img.shields.io/badge/Language-C-A8B9CC?style=flat-square&logo=c&logoColor=white)
![Status](https://img.shields.io/badge/Status-em%20desenvolvimento-yellow?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

## Sobre o projeto

Este é o repositório de uma pedaleira de efeitos para instrumentos musicais
(guitarra/baixo) processada de forma totalmente digital. Diferente das
pedaleiras analógicas tradicionais, todo o processamento de sinal — desde a
captação até a saída — é feito em software, rodando sobre um microcontrolador
dedicado a DSP.

O projeto é dividido em duas frentes de hardware que se comunicam entre si:

- **STM32H7xx** — responsável pelo processamento digital de áudio em tempo
  real: aquisição do sinal, aplicação dos efeitos (equalização, distorção,
  modulação, delay, reverb, entre outros a definir) e geração da saída de
  áudio. É o coração da pedaleira, onde o sinal é efetivamente processado.

- **ESP32** — responsável pela camada de comunicação e conectividade. Atua
  como ponte entre a pedaleira e uma aplicação externa (mobile/desktop) via
  MQTT, permitindo configurar remotamente os efeitos ativos, ajustar
  parâmetros de equalização e demais features da aplicação. O ESP32 repassa
  essas configurações para a STM32 através de uma interface de comunicação
  entre os dois microcontroladores.

A interação física com a pedaleira segue o padrão de uma pedaleira real:
botões (footswitches) para acionar e alternar entre os efeitos, com a
vantagem de que toda a configuração fina (ganho, frequências, mix, presets)
pode ser feita remotamente pela aplicação, sem necessidade de displays ou
potenciômetros físicos para cada parâmetro.

> O projeto está em fase inicial de desenvolvimento. Arquitetura, escopo de
> efeitos e protocolo de comunicação entre STM32 e ESP32 ainda estão sendo
> definidos e podem mudar.

## Arquitetura (visão geral)

```
[Instrumento] -> [STM32H7xx: captação e DSP] -> [Saída de áudio]
                          ^
                          | (interface STM32 <-> ESP32)
                          v
                    [ESP32: MQTT] <-> [Aplicação de configuração]
```

## Estrutura do repositório

```
.
├── firmware/
│   ├── stm32/        # Firmware do processamento de áudio (STM32H7xx, STM32CubeIDE)
│   └── esp32/        # Firmware de comunicação MQTT (ESP-IDF, a adicionar)
├── app/
│   ├── backend/      # Serviço de intermediação com a pedaleira via MQTT
│   └── frontend/     # Aplicação de configuração dos efeitos
└── docs/
    ├── code/         # Documentação relacionada ao firmware/software
    ├── hardware/      # Esquemáticos, PCB e documentação de hardware
    └── components/    # Datasheets e documentação dos componentes utilizados
```

## Hardware

| Função                  | Componente     |
|--------------------------|----------------|
| Processamento de áudio   | STM32H723VG    |
| Comunicação / MQTT       | ESP32          |
| Codec de áudio           | CS4272         |

## Status

- [x] Estrutura inicial do repositório e do firmware STM32
- [ ] Pipeline de aquisição e saída de áudio (codec CS4272)
- [ ] Primeiros efeitos digitais (equalização, distorção)
- [ ] Firmware ESP32 (MQTT)
- [ ] Interface STM32 <-> ESP32
- [ ] Aplicação de configuração
