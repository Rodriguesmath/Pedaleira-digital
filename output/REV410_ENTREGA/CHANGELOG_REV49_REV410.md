# Alterações efetivas 4.9 -> candidato 4.10 (Fase A fechada no projeto elétrico)

- Originais 4.9 e firmware preservados integralmente; hashes base em `BASE_REV49_SHA256.txt`.
- Headers `STM5V` e `ESPVIN` agora NC externos; USBs independentes; `VD/VL` exclusivamente em `+3V3_STM`.
- Orçamento `+3V3_STM` calculado em pior caso (329,4 mA vs buck mínimo WeAct `SY8088AAC` 1000 mA); inspeção física do exemplar pendente.
- `U5 CW7805` isolado para `+5VA` via `J4/J5`, mantendo valores nominais analógicos e restrições explícitas de bancada.
- UART direta substituída por `U6 ISO7721DR` dual-supply (`SOIC-8`), `C42/C43`, `R29..R32` (Folha 8).
- Folha 9 adicionada (25 componentes: `U7 TL431ACZ`, `Q1..Q3 2N3904/2N3906`, `Q4 2N3904`, `Q5..Q8 2N7000`, `D15 1N4148`, `C44 10uF`, `R33..R41`, `R43..R47`):
  - Supervisor `+5VA` com histerese (sobe ~4,60 V, cai ~4,52 V), mantendo `I_K >= 1,0 mA` em `U7`.
  - Intertravamento `/RST` que força `CODEC_RST <= 0,03 V` sempre que `+5VA < 4,52 V`, com zero backpower para `+3V3_STM` e subida rápida (< 200 ns) na janela `1 ms` do firmware `Cs4272.cpp`.
  - Contenção off-state `D15/R43/C44/Q4..Q8` para `AINA_P`, `AINA_N`, `ADC_BIAS` (via `R47 = 47 ohm`) e `AINB_CM` sem carregar `VCOM`.
- Projeto CAD conectado com 139 componentes, 347 terminais, 73 redes, 9 folhas A4 paisagem, autoria `Rodrigues M. Lima`, **0 violações ERC** no KiCad 10.
- Próxima etapa desbloqueada pelo Gate A do projeto: Fase 4.10B (`ANALISE_ADC.md` e `PROJETO_MUTE_FISICO.md`).
