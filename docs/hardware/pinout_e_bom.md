# Pinout e BOM de bancada - Rev.4.8

Autoria: Rodrigues M. Lima. **Condicionado a firmware e validação física.** O CS4272 é um CI em adaptador passivo, sem auxiliares instalados.

Fonte vigente: [esquemática](../../output/rev4_8/pedaleira_digital_rev4_8.pdf), [BOM completa](../../output/rev4_8/BOM_rev4_8.csv), [auditoria](../../output/rev4_8/AUDITORIA_ELETRICA.md), [checklist](../../output/rev4_8/CHECKLIST_MONTAGEM.md).

## CS4272 TSSOP-28

| Terminal físico | Nome/função | Rede |
|---|---|---|
| 1 | XTO | NC |
| 2 | XTI | GND |
| 3 | MCLK | MCLK |
| 4 | LRCK | LRCK |
| 5 | SCLK | BCLK |
| 6 | SDOUT | ADC_DATA |
| 7 | SDIN | DAC_DATA |
| 8 | DGND | GND |
| 9 | VD | +3V3 |
| 10 | VL | +3V3 |
| 11 | SCL/CCLK | I2C_SCL |
| 12 | SDA/CDIN | I2C_SDA |
| 13 | AD0/CS | GND |
| 14 | /RST | CODEC_RST |
| 15 | VCOM | VCOM |
| 16 | AINA- | AINA_N |
| 17 | AINA+ | AINA_P |
| 18 | AINB+ | AINB_CM |
| 19 | AINB- | AINB_CM |
| 20 | VA | +5VA |
| 21 | AGND | GND |
| 22 | FILT+ | FILT |
| 23 | AMUTEC | NC |
| 24 | AOUTA- | AOUTA_N |
| 25 | AOUTA+ | AOUTA_P |
| 26 | AOUTB+ | NC |
| 27 | AOUTB- | NC |
| 28 | BMUTEC | NC |

## WeAct V1.2 - header / GPIO / pino LQFP100 / AF

| Terminal físico | Nome/função | Rede |
|---|---|---|
| P1.4 | PE0 / 97 / AF10 | MCLK |
| P2.5 | PE4 / 3 / AF8 | LRCK |
| P2.6 | PE5 / 4 / AF8 | BCLK |
| P2.7 | PE6 / 5 / AF8 | DAC_DATA |
| P2.17 | PA0 / 22 / AF10 | ADC_DATA |
| P1.6 | PB8 / 95 / AF4 | I2C_SCL |
| P1.5 | PB9 / 96 / AF4 | I2C_SDA |
| P1.38 | PD10 / 57 / GPIO | CODEC_RST |
| P1.40 | PD8 / 55 / AF7 | UART_TX |
| P1.39 | PD9 / 56 / AF7 | UART_RX |
| P2.11 | PC0 / 15 | SW_OD |
| P2.12 | PC1 / 16 | SW_EQ |
| P2.13 | PC2_C / 17 | SW_DLY |
| P2.14 | PC3_C / 18 | SW_MUTE |
| P2.30 | PE7 / 37 | LED_OD |
| P2.31 | PE8 / 38 | LED_EQ |
| P2.32 | PE9 / 39 | LED_DLY |
| P2.38 | PE15 / 45 | LED_STAT |
| P1.2 | 5V entrada | +5V_USB |
| P2.2 | 3V3 saída | +3V3 |
| P1.1 | GND | GND |

## ESP32 - nomes serigrafados, não numeração ordinal de DevKit genérico

| Terminal físico | Nome/função | Rede |
|---|---|---|
| RX2 | GPIO16 RX2 | UART_TX |
| TX2 | GPIO17 TX2 | UART_RX |
| VIN | VIN / 5V | +5V_USB |
| GND | GND | GND |

PC2_C/PC3_C precisam do switch interno fechado para uso como GPIO PC2/PC3. PE4/PE5/PE6 são **AF8**, não AF10. Pull-ups I2C 4,7 kohm são **externos**. Há dois TL072: U1 existente e U3 novo, ambos alimentados entre +RAW e -VA_OP. Não usar NE5532 como substituto presumido nem conectar fones na saída.

Valores, quantidades, encapsulamentos e situação de cada componente constam na BOM gerada. Custos antigos não foram revalidados e não são orçamento desta revisão. A versão anterior deste documento está em backup_rev4_7.
