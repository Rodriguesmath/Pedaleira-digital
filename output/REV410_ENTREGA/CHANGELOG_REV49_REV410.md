# Alterações efetivas 4.9 -> candidato 4.10 (Fases A e B fechadas no projeto elétrico; Gate B)

- Originais 4.9 e firmware preservados integralmente; hashes base em `BASE_REV49_SHA256.txt`.
- Headers `STM5V` e `ESPVIN` agora NC externos; USBs independentes; `VD/VL` exclusivamente em `+3V3_STM`.
- Orçamento `+3V3_STM` calculado em pior caso (329,4 mA vs buck mínimo WeAct `SY8088AAC` 1000 mA); inspeção física do exemplar pendente.
- `U5 CW7805` isolado para `+5VA` via `J4/J5`, mantendo valores nominais analógicos e restrições explícitas de bancada.
- UART direta substituída por `U6 ISO7721DR` dual-supply (`SOIC-8`), `C42/C43`, `R29..R32` (Folha 8).
- Folha 9 adicionada (25 componentes: `U7 TL431ACZ`, `Q1..Q3 2N3904/2N3906`, `Q4 2N3904`, `Q5..Q8 2N7000`, `D15 1N4148`, `C44 10uF`, `R33..R41`, `R43..R47`):
  - Supervisor `+5VA` com histerese (`4,602 V` subida / `4,516 V` queda), mantendo `I_K >= 1,0 mA` em `U7`.
  - Intertravamento `/RST` forçando `CODEC_RST <= 0,03 V` quando `+5VA < 4,52 V`, zero backpower para `+3V3_STM` e subida rápida dentro da janela `1 ms` de `Cs4272.cpp`.
  - Contenção off-state `D15/R43/C44/Q4..Q8` para `AINA_P`, `AINA_N`, `ADC_BIAS` (`R47 = 47 ohm`) e `AINB_CM` sem carregar `VCOM`.
- **Fase 4.10B implementada (Blocker 3 + Blocker 4)**:
  - **Blocker 3 ([ANALISE_ADC.md](file:///home/rodrigues/Pedaleira-digital/output/REV410_ENTREGA/ANALISE_ADC.md))**: `D9..D12` (`BAT85`) removidos; adicionados bias `R48..R53`, `C45..C48`, `Q9`, `Q10` (Folha 10A) e grampos `Q11..Q14` (Folha 2B) mantendo `AINA_P/N` em `[+0,298 V, +4,991 V]` nos 4 cantos com **0,0000 mA** injetados em `+5VA` (`THD 0,000878% @ 0 dBFS`).
  - **Blocker 4 ([PROJETO_MUTE_FISICO.md](file:///home/rodrigues/Pedaleira-digital/output/REV410_ENTREGA/PROJETO_MUTE_FISICO.md))**: `C5 -> OUT_PRE`, `R6 = 47 kohm`, `K1 Omron G5V-1-DC12` (`Relay_THT:Relay_SPDT_Omron_G5V-1`), `D16 1N4148` (Folha 4B), supervisor `+RAW` (`U8 TL431ACZ`, `Q15`), AND 3 entradas + fast-dump (`Q16..Q19`, `Q22`), temporizador `C49 = 47 uF` / `D17 BZX55C4V7` e Schmitt `Q20/Q21` (Folha 10B/10C).
- Projeto CAD conectado com **183 componentes**, **454 terminais**, **96 redes**, **10 folhas A4 paisagem**, autoria `Rodrigues M. Lima`, **0 violações ERC** no KiCad 10.
- **Próxima etapa**: Fase 4.10C (`A410-08` footprints completos na BOM e `MANIFESTO_SHA256.txt`) quando autorizada pelo usuário, seguida dos pré-requisitos físicos de bancada.
