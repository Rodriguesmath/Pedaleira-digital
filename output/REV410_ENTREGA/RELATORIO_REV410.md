# Revisão 4.10 - Checkpoint Gate A (Projeto Elétrico PASS / Bancada Condicionada)

2026-11-12. **Status do Gate A:**
- **Projeto elétrico & simulação SPICE Fase A:** **PASS** (`16/16` cenários `simular_A.py` PASS; `13/13` testes analíticos `validar_alimentacao.py` PASS; `12/12` testes UART `test_interfaces_indep.py` PASS; `11/11` testes independentes `auditar_cad_A.py` PASS; **0 violações ERC** no KiCad 10).
- **Pré-requisitos físicos de amostra em bancada (`A410-01` CW7805, `A410-05_hw` WeAct U2, `A410-07_hw` ESP32):** **CONDICIONADOS** a inspeção e qualificação presencial antes da energização física (decisão documentada sem fabricar dados de hardware não testado).
- **Liberação para Fase B:** **AUTORIZADA**. (Nenhuma aprovação B/C ou funcionamento completo em bancada reivindicada neste checkpoint.)

## Evidências de Projeto Fechadas na Fase A

- **Modelo físico e CAD (Folhas 1 a 9)**: **139 componentes**, **347 terminais conectados**, **73 redes**, **0 cruzamentos ilegais**, footprints oficiais locais para `U6` (`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`) e `U7, Q1..Q8` (`Package_TO_SOT_THT:TO-92_Inline`), `ERC_rev4_10.json` e `ERC_fresh.json` com **0 violações** (`ignored_checks = []`).
- **Supervisor `+5VA` (`U7 TL431ACZ + Q3 2N3906`)**: subida em `4.602 V`, queda em `4.516 V` (histerese `85.3 mV`), `I_K = 1.34 mA >= 1,0 mA`, carga adicional em `+5VA` = `1.82 mA`.
- **Intertravamento `/RST` (`Q1/Q2 + R39..R41`)**: `CODEC_RST = 0.0240 V` com `VA < 4,48 V` e `PD10 = 3,3 V`; subida para `3.000 V` já em `200 ns` após fim do pulso (`>> 1 ms` do firmware); backpower com `3V3 = 0 V` = `0.000000 V`.
- **Contenção off-state AIN (`D15/R43/C44/Q4..Q8/R47`)**: `|AINA_P|, |AINA_N|, |ADC_BIAS|, |AINB_CM| <= 1,1 mV` nos estados sem `+5VA` (incluindo colapso rápido de `+RAW` e step `10 us`); pico de inrush em `D15/R43/C44` = `250.51 mA`; impacto em THD diferencial (`0,5 Vp @ 1 kHz`) = `0.000514%` (< 0,02%).
- **Orçamentos**: `+5VA` máx `61.34 mA` (< 65 mA), proxy CW `0.5823 W`; `+3V3_STM` pior caso aritmético `329.4 mA` (< 1000 mA `SY8088`).

## Escopo Aberto para Fase B e Fase C

- **Fase B**: substituição ativa dos clamps `BAT85` (`A410-04` -> `ANALISE_ADC.md`) e projeto fail-safe de mute físico de saída (`A410-06` -> `PROJETO_MUTE_FISICO.md`), mais validação de desempenho/headroom TL072 B3/B4.
- **Fase C**: footprints oficiais para toda a BOM, suíte ngspice integral, auditoria adversarial independente e fechamento `REV410_ENTREGA`.
