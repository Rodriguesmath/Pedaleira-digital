# Conexões revisão 4.9

A tabela CSV acompanhante cobre todos os terminais físicos. GND é a mesma rede em todas as folhas; VREF_OP, ADC_BIAS e VCOM são redes diferentes. As coordenadas/folhas efetivas vêm de diagram_layout.json; U1 e U3 são divididos em unidades, sem duplicar os CIs.

## STM32 ↔ CS4272

| Rede | GPIO / pino LQFP100 | Header WeAct V1.2 | AF | CS4272 TSSOP-28 | Direção |
|---|---|---|---|---|---|
| MCLK | PE0 / 97 | P1.4 | AF10 | 3 MCLK | STM→codec |
| LRCK | PE4 / 3 | P2.5 | AF8 | 4 LRCK | STM→codec |
| BCLK | PE5 / 4 | P2.6 | AF8 | 5 SCLK | STM→codec |
| DAC_DATA | PE6 / 5 | P2.7 | AF8 | 7 SDIN | STM→codec |
| ADC_DATA | PA0 / 22 | P2.17 | AF10 | 6 SDOUT | codec→STM |
| I2C_SCL | PB8 / 95 | P1.6 | AF4 OD | 11 SCL | STM→codec |
| I2C_SDA | PB9 / 96 | P1.5 | AF4 OD | 12 SDA | bidirecional |
| CODEC_RST | PD10 / 57 | P1.38 | saída GPIO | 14 /RST | STM→codec |

## STM32 ↔ ESP32

| Rede | STM32 / header | ESP32 pelo nome serigrafado | Direção |
|---|---|---|---|
| UART_TX | PD8 / P1.40, AF7 USART3_TX | GPIO16 RX2 | STM→ESP |
| UART_RX | PD9 / P1.39, AF7 USART3_RX | GPIO17 TX2 | ESP→STM |
| +5V | ramal CW7805 independente | VIN/5V confirmado | alimentação |
| GND | retorno comum | GND | referência |

UART 115200 8N1, níveis 3,3 V; não transmitir áudio por UART. Confirmar WROOM sem conflito PSRAM em 16/17. O ESP32 não é alimentado através do header de 5 V da STM32: os dois ramais saem do regulador. USB de programação com VBUS isolado; não unir fontes.

## Alimentação

| Rede | Origem | Destinos | Critério antes de instalar CIs |
|---|---|---|---|
| 12V_IN | J1 centro positivo | F1→D1 | 11,4..12,6 V |
| +RAW | D1 cátodo | TL072 pino 8, U5 IN, R22 | 10,5..12,3 V no envelope adotado |
| +5V | CW7805 OUT confirmado | U2 VA20, WeAct P1.2, ESP VIN | alvo 4,85..5,15 V; obrigatório 4,75..5,25 V |
| +3V3 | WeAct P2.2, conversor onboard | U2 VD9/VL10, pull-ups, GPIO | alvo 3,2..3,4 V; VD ≥3,1 V |
| VREF_OP | R22/R23/C38/C39 | bias guitarra, U3B+, receptor DAC | 0,495..0,505 × +RAW sem carga excessiva |
| ADC_BIAS | R27/R28/C40/C41 | R15/R16 e canal ADC B | ~0,48 × +5V; conferir diferença para VCOM ≤50 mV |
| VCOM | U2 pino 15 | C14/C15 e TP5 apenas | típico 0,48 × VA; sem carga externa |
| GND | J1 retorno | pinos 4 dos TL072 e todos os retornos | continuidade, sem interrupções |

A placa WeAct já contém um conversor chaveado com indutor. Não foi adicionado conversor nem indutor à perfboard. A proibição literal de qualquer indutor, incluindo o onboard, é incompatível com manter essa placa intacta.

## Quatro canais de amplificador

| Unidade | Entradas | Saída | Função |
|---|---|---|---|
| U1A | 3 HI_Z; 2 IN_BUF | 1 IN_BUF | buffer guitarra +1 |
| U1B | 5 DAC_P; 6 DAC_N | 7 DAC_BUF | receptor diferencial, ganho 0,499, bias VREF_OP |
| U3A | 3 IN_BUF; 2 FB_P | 1 DRV_P | driver positivo +1 |
| U3B | 5 VREF_OP; 6 FB_N | 7 DRV_N | inversor −1 por R24/R19 |

Ambos DIP-8: 8=+RAW, 4=GND; nenhum canal está sem uso.

## Conectores e comandos

J1: 1 positivo da fonte 12 V, 2 GND. J2: 1 TIP guitarra, 2 sleeve/GND. J3: 1 TIP saída AC, 2 sleeve/GND. J4: 1 distribuição +5V, 2 GND, **não é porta USB**. Os números funcionais dos jacks devem ser identificados por continuidade no componente comprado.

SW1..4: C comum, 1 para GND, 2 NC. PC0/P2.11, PC1/P2.12, PC2_C/P2.13, PC3_C/P2.14. Confirmar fechamento dos switches analógicos internos dos pads _C. LEDs em PE7/P2.30, PE8/P2.31, PE9/P2.32, PE15/P2.38; resistor 330 Ω e cátodo no GND. SW4 é mute.

## Pinagem integral dos CIs e módulos


### U2 — CS4272

| Pino | Nome | Rede | Folha |
|---|---|---|---|
| 1 | XTO | NC | 3 |
| 2 | XTI | GND | 3 |
| 3 | MCLK | MCLK | 3 |
| 4 | LRCK | LRCK | 3 |
| 5 | SCLK | BCLK | 3 |
| 6 | SDOUT | ADC_DATA | 3 |
| 7 | SDIN | DAC_DATA | 3 |
| 8 | DGND | GND | 3 |
| 9 | VD | +3V3 | 3 |
| 10 | VL | +3V3 | 3 |
| 11 | SCL/CCLK | I2C_SCL | 3 |
| 12 | SDA/CDIN | I2C_SDA | 3 |
| 13 | AD0/CS | GND | 3 |
| 14 | /RST | CODEC_RST | 3 |
| 15 | VCOM | VCOM | 3 |
| 16 | AINA- | AINA_N | 3 |
| 17 | AINA+ | AINA_P | 3 |
| 18 | AINB+ | AINB_CM | 3 |
| 19 | AINB- | AINB_CM | 3 |
| 20 | VA | +5V | 3 |
| 21 | AGND | GND | 3 |
| 22 | FILT+ | FILT | 3 |
| 23 | AMUTEC | NC | 3 |
| 24 | AOUTA- | AOUTA_N | 3 |
| 25 | AOUTA+ | AOUTA_P | 3 |
| 26 | AOUTB+ | NC | 3 |
| 27 | AOUTB- | NC | 3 |
| 28 | BMUTEC | NC | 3 |

### U1 — TL072

| Pino | Nome | Rede | Folha |
|---|---|---|---|
| 1 | OUT A | IN_BUF | 2 |
| 2 | IN- A | IN_BUF | 2 |
| 3 | IN+ A | HI_Z | 2 |
| 4 | V- | GND | 7 |
| 5 | IN+ B | DAC_P | 4 |
| 6 | IN- B | DAC_N | 4 |
| 7 | OUT B | DAC_BUF | 4 |
| 8 | V+ | +RAW | 7 |

### U3 — TL072CP

| Pino | Nome | Rede | Folha |
|---|---|---|---|
| 1 | OUT A | DRV_P | 2 |
| 2 | IN- A | FB_P | 2 |
| 3 | IN+ A | IN_BUF | 2 |
| 4 | V- | GND | 7 |
| 5 | IN+ B | VREF_OP | 2 |
| 6 | IN- B | FB_N | 2 |
| 7 | OUT B | DRV_N | 2 |
| 8 | V+ | +RAW | 7 |

### U5 — CW7805

| Pino | Nome | Rede | Folha |
|---|---|---|---|
| 1 | IN | +RAW | 1 |
| 2 | GND / TAB | GND | 1 |
| 3 | OUT | +5V | 1 |

### H_STM32 — WeAct STM32H723 V1.2

| Pino | Nome | Rede | Folha |
|---|---|---|---|
| P1.4 | PE0 / 97 / AF10 | MCLK | 5 |
| P2.5 | PE4 / 3 / AF8 | LRCK | 5 |
| P2.6 | PE5 / 4 / AF8 | BCLK | 5 |
| P2.7 | PE6 / 5 / AF8 | DAC_DATA | 5 |
| P2.17 | PA0 / 22 / AF10 | ADC_DATA | 5 |
| P1.6 | PB8 / 95 / AF4 | I2C_SCL | 5 |
| P1.5 | PB9 / 96 / AF4 | I2C_SDA | 5 |
| P1.38 | PD10 / 57 / GPIO | CODEC_RST | 5 |
| P1.40 | PD8 / 55 / AF7 | UART_TX | 5 |
| P1.39 | PD9 / 56 / AF7 | UART_RX | 5 |
| P2.11 | PC0 / 15 | SW_OD | 5 |
| P2.12 | PC1 / 16 | SW_EQ | 5 |
| P2.13 | PC2_C / 17 | SW_DLY | 5 |
| P2.14 | PC3_C / 18 | SW_MUTE | 5 |
| P2.30 | PE7 / 37 | LED_OD | 5 |
| P2.31 | PE8 / 38 | LED_EQ | 5 |
| P2.32 | PE9 / 39 | LED_DLY | 5 |
| P2.38 | PE15 / 45 | LED_STAT | 5 |
| P1.2 | 5V entrada | +5V | 5 |
| P2.2 | 3V3 saída | +3V3 | 5 |
| P1.1 | GND | GND | 5 |

### H_ESP32 — ESP32 DevKit V1

| Pino | Nome | Rede | Folha |
|---|---|---|---|
| RX2 | GPIO16 RX2 | UART_TX | 5 |
| TX2 | GPIO17 TX2 | UART_RX | 5 |
| VIN | VIN / 5V | +5V | 5 |
| GND | GND | GND | 5 |
