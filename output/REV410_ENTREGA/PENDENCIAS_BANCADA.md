# Condições e pré-requisitos físicos de bancada (não executados)

Este roteiro separa os **Gates A e B do projeto elétrico/SPICE (PASS)** dos **pré-requisitos físicos antes de energizar ou liberar hardware real**. Nenhuma medição em bancada ou montagem física foi realizada nesta entrega documental.

1. Conferir na placa física real: modelo do regulador buck `U2` da WeAct H723 (`SY8088` 1A vs `XT3410` 1,5A vs `TLV62569` 2A), variante do módulo ESP32 (GPIO16/17 livres sem PSRAM), continuidade e ausência de pontes `5 V`.
2. Manter `J5` SEM shunt e codec `U2` REMOVIDO durante a qualificação inicial do `CW7805` genérico em bancada; identificar empiricamente `IN/GND/OUT/TAB` na amostra real, testar carga artificial (`100 ohm / 1 W` em `J4`) e estabilidade térmica antes de fechar `J5`.
3. Verificar compatibilidade de aterramento (`GND` comum) entre fontes USB dos hosts, fonte `12 V` e instrumento/amplificador; nunca usar `VREF_OP` como retorno.
4. Confirmar em bancada, antes de instalar o codec CS4272 e conectar amplificador definitivo: casamento de `Vbe` ($\Delta V_{be} < 20\text{ mV}$) nos pares `Q9/Q11..Q14` do clamp ativo (`ANALISE_ADC.md`), tempos de atuação/liberação/repique do relé `K1` (`Omron G5V-1-DC12`, `PROJETO_MUTE_FISICO.md`) com osciloscópio (`pop < 5 mV`) e aprovação integral da **Fase C** (`A410-08` footprints + `MANIFESTO_SHA256.txt`).
