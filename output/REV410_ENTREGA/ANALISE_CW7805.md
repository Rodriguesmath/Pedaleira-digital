# CW7805 mantido e orçamento de alimentação - análise 4.10A

2026-11-12. Decisão do usuário: manter o genérico CW7805 de três pinos retirado de outra placa; qualificação física da amostra pendente antes da energização. A origem em aparelho alimentado em AC não fornece fabricante, pinagem/TAB, tensão máxima ou limites térmicos sem verificação na amostra real. Nenhum dado do ST L7805 foi atribuído ao exemplar.

Implementado: placas retiradas da carga CW; `U5` fornece `+5V_CW`, com `C22/C37/R21` e `D8` preservados. `J4` dá acesso somente à carga artificial; `J5` fica SEM shunt até caracterização isolada do CW. STM32 e ESP32 usam USB próprias; `VD/VL` vêm de `+3V3_STM`. Na Folha 9, supervisor `+5VA` (`U7 TL431ACZ + Q3 2N3906`) consome adicional medido em SPICE de **1.82 mA** em regime nominal.

A pinagem numérica `1=IN, 2=GND/TAB, 3=OUT` no modelo é HIPÓTESE A CONFIRMAR na amostra real antes de qualquer energização.

## Cálculos reproduzíveis (`validar_alimentacao.py`)

- **+5VA / CW7805**: `IA` máximo CS4272 DS593F2 p17 (`53 mA`) + `R21` (`5,83 mA` máx) + divisor `R27/R28` (`0,21 mA` máx) + pior caso supervisor Folha 9 (`~2,3 mA`) -> orçamento máximo calculado **61.34 mA** (< 65 mA; típico ~52.44 mA).
- **Dissipação proxy CW** (`RAW 10,5..12,6 V`, `Iq 8 mA` proxy de família): conservadora **0.5823 W**, contra ~0,909 A / 7,236 W na 4.9.
- **Orçamento aritmético `+3V3_STM` (WeAct V1.2 `U2`)**: considerando a variante de menor capacidade do esquemático oficial WeAct (`SY8088AAC = 1,000 A`; alternativas `XT3410 = 1,5 A` e `TLV62569 = 2,0 A`), a soma de pior caso (`STM32H723 DS13313` Run max @ 105 °C = `250 mA` + reserva flash/LEDs WeAct `25 mA` + `CS4272 VD/VL` max `28 mA` + `ISO7721` lado 1 `4 mA` + 4 LEDs `16,3 mA` + pull-ups/intertravamento `/RST` `6,0 mA`) totaliza **329.4 mA**, deixando **670.6 mA** de margem bruta (~67%). A confirmação física do CI `U2` montado na placa WeAct, droop térmico em bancada e inspeção da variante ESP32 (GPIO16/17 livres) seguem obrigatórias antes da montagem/energização.

## Fundamentação

[Cirrus DS593F2](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf), p9/p17/p27; [TI TL072 SLOS080W](https://www.ti.com/lit/ds/symlink/tl072.pdf); [WeAct STM32H723 V1.2 Schematic](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723); STM32H723 DS13313 Table 22.
