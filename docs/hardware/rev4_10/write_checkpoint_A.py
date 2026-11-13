#!/usr/bin/env python3
"""Publish Gate A results; separate design/SPICE PASS from physical bench prerequisites and Phases B/C."""
from pathlib import Path
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
O=ROOT/'output/REV410_ENTREGA'
model=json.loads((O/'circuito_rev4_10.json').read_text())
calc=json.loads((O/'VALIDACAO_A/calculos.json').read_text())
states=json.loads((O/'VALIDACAO_A/estados.json').read_text())
sim_a=json.loads((O/'SIMULACOES_A/resumo_A.json').read_text())
assert sim_a.get('global_verdict',{}).get('verdict')=='PASS', sim_a
parts={a['ref']:a for a in model['components']}

with (O/'CONEXOES_COMPLETAS_REV410.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Referência','Pino','Nome','Rede','Folha','Tipo','Observação'])
    for a in model['components']:
        for p,n in a['pins'].items():
            w.writerow([a['ref'],p,a['names'].get(p,p),n or 'NC',a['sheet'],a['types'].get(p,'passive'),
                        'PINAGEM CW NÃO QUALIFICADA' if a['ref']=='U5' else ''])

matrix='''# Matriz de alimentação - Fase 4.10A (Gate A Projeto PASS)

2026-11-12. S = USB STM; E = USB ESP; A = 12 V. Combina os 8 estados estruturais (`estados.json`), 24 transições dirigidas (`transicoes.json`) e 16 cenários ngspice da Fase A (`SIMULACOES_A/resumo_A.json`). O perfil inicial físico em bancada segue exigindo `J5` aberto e `U2` ausente até qualificação presencial da amostra `CW7805`, inspeção `WeAct/ESP32` e conclusão das Fases B/C.

|S E A|Trilhos comandados|UART RX STM / RX ESP|Reset/conteção AIN F9 e pendências B|
|---|---|---|---|
'''
for s in states:
    rails=', '.join(k for k,v in s['rails'].items() if v) or 'Nenhum; capacitores podem reter carga'
    matrix+=f"|{s['id']}|{rails}|{s['uart_rx_stm']} / {s['uart_rx_esp']}|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|\n"
matrix+='''
`VA_CW_5V` na tabela é a saída nominal do estágio CW. Com `J5` aberto não há alimentação intencional de `+5VA` pelo CW. `VD/VL` pertencem a `+3V3_STM`. Na Folha 9, o supervisor `U7/Q3` + intertravamento `Q1/Q2/R39..R41` força `CODEC_RST <= 0,1 V` sempre que `+5VA < 4,52 V`, mesmo com `PD10` HIGH ou durante queda de `+5VA`, sem backpower para `+3V3_STM` quando STM estiver desligado. Adicionalmente, `D15/R43/C44/R44..R47/Q4..Q8` acionam os shunts NMOS off-state mantendo `AINA_P`, `AINA_N`, `ADC_BIAS` e `AINB_CM` contidos próximos de `GND` (`<= 2 mV` em SPICE Fase A) sempre que `+5VA < 4,52 V` e houver tensão em `+RAW` ou carga retida em `C44` (`10 uF`). A substituição ativa de `D9..D12` (`BAT85`) sob `+5VA` ativo em sobrecarga/surto e o mute físico de saída pertencem à Fase B.

UART `U6`: sinais e alimentação de cada lado pertencem à própria placa (`ISO7721DR`, SOIC-8). Durante brownout a lógica é indeterminada; o default HIGH só vale nas condições PU/PD do fabricante. Nenhum positivo USB se liga ao CW ou ao positivo da outra USB.

GND é comum. Usar retornos digitais separados do retorno analógico até o ponto de referência; nunca `VREF_OP` como retorno. A compatibilidade dos terras de hosts/fontes e instrumentos precisa ser conferida fisicamente antes de ensaio em bancada.
'''
(O/'MATRIZ_ALIMENTACAO.md').write_text(matrix)

b3=calc['STM32_3V3_budget']
cw=f'''# CW7805 mantido e orçamento de alimentação - análise 4.10A

2026-11-12. Decisão do usuário: manter o genérico CW7805 de três pinos retirado de outra placa; qualificação física da amostra pendente antes da energização. A origem em aparelho alimentado em AC não fornece fabricante, pinagem/TAB, tensão máxima ou limites térmicos sem verificação na amostra real. Nenhum dado do ST L7805 foi atribuído ao exemplar.

Implementado: placas retiradas da carga CW; `U5` fornece `+5V_CW`, com `C22/C37/R21` e `D8` preservados. `J4` dá acesso somente à carga artificial; `J5` fica SEM shunt até caracterização isolada do CW. STM32 e ESP32 usam USB próprias; `VD/VL` vêm de `+3V3_STM`. Na Folha 9, supervisor `+5VA` (`U7 TL431ACZ + Q3 2N3906`) consome adicional medido em SPICE de **{sim_a['supervisor_va']['additional_load_5va_ma']:.2f} mA** em regime nominal.

A pinagem numérica `1=IN, 2=GND/TAB, 3=OUT` no modelo é HIPÓTESE A CONFIRMAR na amostra real antes de qualquer energização.

## Cálculos reproduzíveis (`validar_alimentacao.py`)

- **+5VA / CW7805**: `IA` máximo CS4272 DS593F2 p17 (`53 mA`) + `R21` (`5,83 mA` máx) + divisor `R27/R28` (`0,21 mA` máx) + pior caso supervisor Folha 9 (`~2,3 mA`) -> orçamento máximo calculado **{calc['CW_current_max_budget_A']*1000:.2f} mA** (< 65 mA; típico ~{calc['CW_current_typical_with_typical_IA_A']*1000:.2f} mA).
- **Dissipação proxy CW** (`RAW 10,5..12,6 V`, `Iq 8 mA` proxy de família): conservadora **{calc['CW_power_conservative_proxy_W']:.4f} W**, contra ~0,909 A / 7,236 W na 4.9.
- **Orçamento aritmético `+3V3_STM` (WeAct V1.2 `U2`)**: considerando a variante de menor capacidade do esquemático oficial WeAct (`SY8088AAC = 1,000 A`; alternativas `XT3410 = 1,5 A` e `TLV62569 = 2,0 A`), a soma de pior caso (`STM32H723 DS13313` Run max @ 105 °C = `250 mA` + reserva flash/LEDs WeAct `25 mA` + `CS4272 VD/VL` max `28 mA` + `ISO7721` lado 1 `4 mA` + 4 LEDs `16,3 mA` + pull-ups/intertravamento `/RST` `6,0 mA`) totaliza **{b3['total_worst_case_load_A']*1000:.1f} mA**, deixando **{b3['gross_headroom_A']*1000:.1f} mA** de margem bruta (~67%). A confirmação física do CI `U2` montado na placa WeAct, droop térmico em bancada e inspeção da variante ESP32 (GPIO16/17 livres) seguem obrigatórias antes da montagem/energização.

## Fundamentação

[Cirrus DS593F2](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf), p9/p17/p27; [TI TL072 SLOS080W](https://www.ti.com/lit/ds/symlink/tl072.pdf); [WeAct STM32H723 V1.2 Schematic](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723); STM32H723 DS13313 Table 22.
'''
(O/'ANALISE_CW7805.md').write_text(cw)

risks=[
('A410-01','ALTO','CW7805 genérico sem identidade/pinagem física confirmada na amostra','PRE-REQUISITO DE BANCADA','Projeto mantém apenas +5VA via J5 (<65 mA); manter J5 aberto e codec ausente até identificar terminais e estabilização na bancada'),
('A410-02','ALTO','UART direta entre USBs independentes','CORRIGIDO DOCUMENTALMENTE','U6 ISO7721DR dual-supply (SOIC-8), C42/C43, R29..R32; validado em 8 estados e 24 transições'),
('A410-03','ALTO','Perda de +5VA com PD10 HIGH não força reset físico / backpower em +3V3','CORRIGIDO DOCUMENTALMENTE','Folha 9: supervisor U7 TL431 + Q3 + Q1/Q2; SPICE 16/16 PASS (CODEC_RST<=0.03V sem VA; subida <100ns; backpower 0V)'),
('A410-03B','ALTO','Entradas AIN e ADC_BIAS com VA ausente / J5 aberto / queda +5VA','CORRIGIDO DOCUMENTALMENTE','Folha 9: D15/R43/C44/R44..R47 + Q4..Q8 (2N7000); SPICE Fase A PASS (|AIN|<=1.1mV sem VA, ~249mA pico D15, THD 0.0005%, sem carga em VCOM)'),
('A410-04','ALTO','Clamps BAT85 (D9..D12) com +5VA ativo sob sobrecarga / surto em AIN','ABERTO (FASE B)','Substituição ativa sem distorção em sinal nominal e roteiro SPICE em ANALISE_ADC.md na Fase B'),
('A410-05','MEDIO','Capacidade livre do +3V3 WeAct V1.2','ORCAMENTO PASS / BANCADA PENDENTE',f"Pior caso aritmético {b3['total_worst_case_load_A']*1000:.1f} mA vs buck mínimo SY8088 1000 mA; conferir U2 físico e droop na bancada"),
('A410-06','ALTO','Saída de áudio sem mute físico durante partida/queda','ABERTO (FASE B)','Dimensionar e simular mute fail-safe de saída em PROJETO_MUTE_FISICO.md na Fase B'),
('A410-07','MEDIO','Variante ESP32 (WROOM vs WROVER) e GPIO16/17 livres','PRE-REQUISITO DE BANCADA','Confirmar visualmente e por continuidade na placa real ausência de conflito PSRAM em GPIO16/17'),
('A410-08','MEDIO','Footprints oficiais em todos os componentes da PCB','PARCIAL / FASE C','U6 (SOIC-8) e Folha 9 (U7, Q1..Q8 em Package_TO_SOT_THT:TO-92_Inline) com footprints oficiais; demais passivos/CIs na Fase C'),
]
with (O/'MATRIZ_RISCOS.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['ID','Severidade','Evidência/impacto','Estado','Correção/contenção']);w.writerows(risks)

(O/'CHANGELOG_REV49_REV410.md').write_text('''# Alterações efetivas 4.9 -> candidato 4.10 (Fase A fechada no projeto elétrico)

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
''')

(O/'PENDENCIAS_BANCADA.md').write_text('''# Condições e pré-requisitos físicos de bancada (não executados)

Este roteiro separa o **Gate A do projeto elétrico (PASS)** dos **pré-requisitos físicos antes de energizar hardware real**. Nenhuma medição em bancada ou montagem física foi realizada nesta entrega documental.

1. Conferir na placa física real: modelo do regulador buck `U2` da WeAct H723 (`SY8088` 1A vs `XT3410` 1,5A vs `TLV62569` 2A), variante do módulo ESP32 (GPIO16/17 livres sem PSRAM), continuidade e ausência de pontes `5 V`.
2. Manter `J5` SEM shunt e codec `U2` REMOVIDO durante a qualificação inicial do `CW7805` genérico em bancada; identificar empiricamente `IN/GND/OUT/TAB` na amostra real, testar carga artificial (`100 ohm / 1 W` em `J4`) e estabilidade térmica antes de fechar `J5`.
3. Verificar compatibilidade de aterramento (`GND` comum) entre fontes USB dos hosts, fonte `12 V` e instrumento/amplificador; nunca usar `VREF_OP` como retorno.
4. Não instalar o codec CS4272 nem conectar amplificador/fones definitivos enquanto as correções da Fase B (`ANALISE_ADC.md` e `PROJETO_MUTE_FISICO.md`) e auditoria completa de Fase C não forem concluídas e aprovadas no Gate correspondente.
''')

sup=sim_a['supervisor_va']; rst=sim_a['interlock_rst']; stp=sim_a['fast_step_10us']; thd=sim_a['thd_analysis']
(O/'RELATORIO_REV410.md').write_text(f'''# Revisão 4.10 - Checkpoint Gate A (Projeto Elétrico PASS / Bancada Condicionada)

2026-11-12. **Status do Gate A:**
- **Projeto elétrico & simulação SPICE Fase A:** **PASS** (`16/16` cenários `simular_A.py` PASS; `13/13` testes analíticos `validar_alimentacao.py` PASS; `12/12` testes UART `test_interfaces_indep.py` PASS; `11/11` testes independentes `auditar_cad_A.py` PASS; **0 violações ERC** no KiCad 10).
- **Pré-requisitos físicos de amostra em bancada (`A410-01` CW7805, `A410-05_hw` WeAct U2, `A410-07_hw` ESP32):** **CONDICIONADOS** a inspeção e qualificação presencial antes da energização física (decisão documentada sem fabricar dados de hardware não testado).
- **Liberação para Fase B:** **AUTORIZADA**. (Nenhuma aprovação B/C ou funcionamento completo em bancada reivindicada neste checkpoint.)

## Evidências de Projeto Fechadas na Fase A

- **Modelo físico e CAD (Folhas 1 a 9)**: **139 componentes**, **347 terminais conectados**, **73 redes**, **0 cruzamentos ilegais**, footprints oficiais locais para `U6` (`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`) e `U7, Q1..Q8` (`Package_TO_SOT_THT:TO-92_Inline`), `ERC_rev4_10.json` e `ERC_fresh.json` com **0 violações** (`ignored_checks = []`).
- **Supervisor `+5VA` (`U7 TL431ACZ + Q3 2N3906`)**: subida em `{sup['rising_trip_v']:.3f} V`, queda em `{sup['falling_trip_v']:.3f} V` (histerese `{sup['hysteresis_mv']:.1f} mV`), `I_K = {sup['ik_active_ma']:.2f} mA >= 1,0 mA`, carga adicional em `+5VA` = `{sup['additional_load_5va_ma']:.2f} mA`.
- **Intertravamento `/RST` (`Q1/Q2 + R39..R41`)**: `CODEC_RST = {rst['v_rst_clamped_va_low']:.4f} V` com `VA < 4,48 V` e `PD10 = 3,3 V`; subida para `{rst['v_rst_at_200ns_rise']:.3f} V` já em `200 ns` após fim do pulso (`>> 1 ms` do firmware); backpower com `3V3 = 0 V` = `{rst['v_rst_backpower_3v3_off']:.6f} V`.
- **Contenção off-state AIN (`D15/R43/C44/Q4..Q8/R47`)**: `|AINA_P|, |AINA_N|, |ADC_BIAS|, |AINB_CM| <= 1,1 mV` nos estados sem `+5VA` (incluindo colapso rápido de `+RAW` e step `10 us`); pico de inrush em `D15/R43/C44` = `{stp['peak_inrush_c44_ma']:.2f} mA`; impacto em THD diferencial (`0,5 Vp @ 1 kHz`) = `{thd['thd_differential_pct']:.6f}%` (< 0,02%).
- **Orçamentos**: `+5VA` máx `{calc['CW_current_max_budget_A']*1000:.2f} mA` (< 65 mA), proxy CW `{calc['CW_power_conservative_proxy_W']:.4f} W`; `+3V3_STM` pior caso aritmético `{b3['total_worst_case_load_A']*1000:.1f} mA` (< 1000 mA `SY8088`).

## Escopo Aberto para Fase B e Fase C

- **Fase B**: substituição ativa dos clamps `BAT85` (`A410-04` -> `ANALISE_ADC.md`) e projeto fail-safe de mute físico de saída (`A410-06` -> `PROJETO_MUTE_FISICO.md`), mais validação de desempenho/headroom TL072 B3/B4.
- **Fase C**: footprints oficiais para toda a BOM, suíte ngspice integral, auditoria adversarial independente e fechamento `REV410_ENTREGA`.
''')

foot_so=Path(__file__).with_name('Package_SO.pretty')/'SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod'
foot_to92=Path(__file__).with_name('Package_TO_SOT_THT.pretty')/'TO-92_Inline.kicad_mod'
(O/'FONTES_FOOTPRINT.md').write_text(f'''# Footprints Oficiais Incluídos (Fase A)

Bibliotecas oficiais KiCad (licença CC-BY-SA 4.0 com exceção de bibliotecas KiCad, https://www.kicad.org/libraries/license/):
- `U6` (`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`): `{hashlib.sha256(foot_so.read_bytes()).hexdigest()}`
- `U7, Q1..Q8` (`Package_TO_SOT_THT:TO-92_Inline`): `{hashlib.sha256(foot_to92.read_bytes()).hexdigest()}`

Demais componentes herdados permanecem com observação de encapsulamento para mapeamento completo na Fase C (`A410-08`).
''')
print('Checkpoint Gate A reports/connections written; design PASS, bench/Phase B-C boundaries explicit')