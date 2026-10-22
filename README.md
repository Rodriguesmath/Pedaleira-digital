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

A interação física com a pedaleira utiliza chaves normais com retenção mecânica
(alavanca/gangorra) para acionar/bypassar os efeitos de forma determinística
(leitura direta de nível lógico GPIO sem dependência de estado em software), com a
vantagem de que toda a configuração fina (ganho, frequências de EQ, mix, presets)
pode ser feita remotamente pela aplicação via MQTT, sem necessidade de displays ou
potenciômetros físicos adicionais.

> O projeto é desenvolvido no âmbito da disciplina de Técnicas de Prototipagem
> do IFPB, adotando prototipagem ágil em bancada com dev boards e placa
> perfurada/ilhada (sem confecção de PCB industrial).

## Arquitetura (visão geral)

```
[Instrumento] -> [Buffer Hi-Z TL072] -> [Codec CS4272] <-> [STM32H7xx (DSP Core)] -> [Saída de áudio]
                                                                  ^
                                                                  | (UART estruturada)
                                                                  v
                                              [ESP32: Wi-Fi/MQTT] <-> [Aplicação Web/Mobile]
```

## Documentação do Projeto

- **Requisitos do Sistema**: [`docs/requisitos.md`](docs/requisitos.md) (RF01–RF07 e RNF01–RNF06)
- **Escopo e Planejamento IFPB**: [`docs/escopo.md`](docs/escopo.md) (Limites, riscos e divisões de trabalho)
- **Hardware & BOM**: [`docs/hardware/pinout_e_bom.md`](docs/hardware/pinout_e_bom.md) (Pinout STM32/ESP32, circuito Hi-Z e orçamento)
- **Protocolos de Comunicação**: [`docs/code/protocolo_comunicacao.md`](docs/code/protocolo_comunicacao.md) (UART binária e tópicos MQTT)

## Estrutura do repositório

```
.
├── firmware/
│   ├── stm32/        # Firmware do processamento de áudio (STM32H7xx, STM32CubeIDE)
│   └── esp32/        # Firmware de comunicação MQTT (ESP-IDF)
├── app/
│   ├── backend/      # Serviço de intermediação com a pedaleira via MQTT
│   └── frontend/     # Aplicação de configuração dos efeitos
└── docs/
    ├── code/         # Documentação relacionada ao firmware/software
    ├── hardware/      # Esquemáticos de bancada e documentação de hardware
    └── components/    # Datasheets e documentação dos componentes utilizados
```

## Hardware

| Função                  | Componente / Módulo |
|--------------------------|---------------------|
| Processamento de áudio   | STM32H723VG (Dev Board) |
| Comunicação / MQTT       | ESP32 DevKit        |
| Codec de áudio           | CS4272 (Breakout)   |
| Condicionamento Hi-Z     | TL072 (Amp-op JFET) |
| Acionamento físico       | Chaves com retenção mecânica (toggle) |

## Status das Milestones

- [x] **M1: Especificação & Arquitetura Inicial** (Requisitos, Escopo, Pinout/BOM e Protocolos)
- [ ] **M2: Validação Mínima de Áudio em Bancada** (Audio Pass-Through e buffer Hi-Z)
- [ ] **M3: DSP Core & Comunicação Inter-MCU** (Overdrive, EQ 3 bandas e ponte MQTT)
- [ ] **M4: Chaves Físicas com Retenção & Integração com App** (Controle físico e remoto)
- [ ] **M5: Consolidação do Protótipo Físico** (Placa perfurada, chicotes e chassi simples)
- [ ] **M6: Validação Experimental, Homologação & Entrega IFPB** (Latência, testes ao vivo)
