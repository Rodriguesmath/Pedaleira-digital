# Checkpoints - revisão 4.10

## Retomada 2026-11-12

Base Git: 1c73c02; branch codex/rev410-auditoria. Originais 4.9 preservados.
Cota consultada: janela de 5h 47% restante, semanal 92% restante. O salvamento aos 10% foi solicitado pelo usuário.

CHECKPOINT A: EM CORREÇÃO / BLOCKED. Não autoriza início de B.
Pendências: identidade do CW7805, UART entre domínios USB, orçamento 3V3 e reset sob perda de alimentação.
A pergunta sobre a marcação completa do CW7805 foi enviada; outras correções continuam.

CHECKPOINT B: NÃO INICIADO, depende de PASS A.
CHECKPOINT C: NÃO INICIADO, depende de PASS B.

Este arquivo é diário de trabalho, não certificado de aprovação.

## Decisão do usuário: CW7805

2026-11-12: informou ser genérico de três pinos, retirado de placa de aparelho alimentado em corrente alternada. Escolheu manter o CW7805 genérico e registrar qualificação pendente. Em seguida pediu para não se preocupar com os limites porque regula em 5 V. Mantido o componente e a saída nominal de 5 V como premissa; isso não fornece fabricante/pinagem/SOA/estabilidade/térmica rastreáveis. Não atribuir parâmetros ST nem converter essa origem em garantia elétrica. Não repetir pergunta de substituição.

Nova consulta de cota após mudança de modelo: 98% restante na janela de5h e100% semanal; não foi acionado crédito de reset pelo agente.

## CHECKPOINT A - encerramento solicitado pelo usuário

Data: 2026-11-12. **Decisão: BLOCKED para o conjunto.** Etapa encerrada para transferência ao Gemini Antigravity Flash 3.8 High. Não é PASS A; B e C não iniciadas.

- Objetivo: separar os domínios USB/analógico e impedir alimentação cruzada pela UART.
- Fontes alteradas: docs/hardware/rev4_10 (modelo, geradores, validadores e roteiro de reprodução).
- Artefatos alterados: candidato PDF de oito folhas, KiCad, BOM, conexões, relatórios e evidências em output/REV410_ENTREGA.
- Alterações elétricas: headers externos 5V/VIN em NC; VD/VL no domínio STM; UART ISO7721DR; J5 aberto por padrão entre CW e VA; J4 só para carga artificial. Valores/ganhos originais preservados.
- Justificativa: três fontes independentes não podem compartilhar seus positivos ou alimentar placas desligadas pelos sinais.
- Testes realmente executados: 11 alimentação + 12 UART + 12 CAD independente; conectividade visual 288 terminais/61 redes; ERC com todas as severidades, zero violações e zero exclusões.
- Revisão independente: REVISOES/CAD_A_INDEPENDENTE.md; os 114 componentes e 277 terminais conectados correspondem à BOM/modelo/XML.
- Preservação: hashes de todos os arquivos originais 4.9 conferidos; git diff de firmware contra 1c73c02 vazio.
- Riscos restantes: reset na perda de VA; AIN/clamps durante queda; ausência de mute físico; capacidade livre 3V3/variante ESP; CW mantido genérico com qualificação pendente por escolha do usuário.
- Condição de ensaio inicial: somente subconjuntos USB, J5 aberto e codec fisicamente ausente; J5 sozinho não isola o codec.
- Nenhuma montagem, compra, medição, flash ou nova simulação SPICE de ADC/mute foi executada.
- Retomada: PROMPT_GEMINI_ANTIGRAVITY_REV410.md, também copiado na entrega. Não repetir a discussão da troca do CW; a decisão já foi tomada.
- Commit correspondente: localizar a mensagem `chore(hardware): salva checkpoint 4.10A e handoff Gemini` em git log da branch codex/rev410-auditoria.

Última consulta de cota: 16% restante na janela de5h; 87% semanal. Limiar pedido:10%. Trabalho salvo no encerramento solicitado pelo usuário, sem acionar reset de cota.

## CHECKPOINT GATE A - Projeto Elétrico & SPICE APROVADOS / Bancada Condicionada

Data: 2026-11-12. **Decisão:**
- **Projeto elétrico & SPICE Fase 4.10A:** **PASS** (autoriza execução da Fase 4.10B).
- **Pré-requisitos físicos de amostra em bancada:** **CONDICIONADOS** (`A410-01` pinagem/estabilidade do exemplar `CW7805` com `J5` aberto e codec ausente; `A410-05_hw` inspeção física do buck `U2` da WeAct V1.2 e droop térmico; `A410-07_hw` inspeção ESP32 GPIO16/17 livres).
- **Escopo implementado na Fase A (Folha 9, 25 componentes adicionados -> total 139 componentes, 347 terminais, 73 redes, 9 folhas)**:
  - Supervisor `+5VA` (`U7 TL431ACZ` + `Q3 2N3906`, `R33..R38`): histerese `4,602 V` subida / `4,516 V` queda, `I_K = 1,34 mA >= 1,0 mA`, carga nominal `+5VA` = `1,82 mA` (`+5VA` máx total `61,34 mA < 65 mA`).
  - Intertravamento `/RST` (`Q1/Q2 2N3904`, `R39..R41`): força `CODEC_RST <= 0,03 V` sempre que `+5VA < 4,52 V`, backpower com `+3V3_STM = 0 V` de `0,000000 V`, subida rápida dentro da janela `1 ms` do firmware `Cs4272.cpp`.
  - Contenção off-state / sem VA (`D15 1N4148`, `R43 47 ohm`, `C44 10 uF`, `R44..R47`, `Q4 2N3904`, `Q5..Q8 2N7000`): contém `AINA_P`, `AINA_N`, `ADC_BIAS` (via `R47 = 47 ohm`) e `AINB_CM` em `<= 1,1 mV` sem VA; pico inrush `250,51 mA`; THD diferencial impacto `0,000514%`; sem carga adicional em `VCOM`.
  - Footprints oficiais KiCad locais em `docs/hardware/rev4_10/Package_TO_SOT_THT.pretty/TO-92_Inline.kicad_mod` (`U7, Q1..Q8`) além de `Package_SO` (`U6`).
- **Verificações executadas (`sh docs/hardware/rev4_10/run_A.sh`)**: `13/13` testes `validar_alimentacao.py`, `12/12` testes `test_interfaces_indep.py`, `16/16` cenários ngspice `simular_A.py`, `11/11` testes independentes `auditar_cad_A.py --export`, **0 violações ERC** no KiCad 10 (`ignored_checks = []`), `validate_layout.py` 100% consistente.
- **Preservação**: `docs/hardware/rev4_9/`, `output/rev4_9/` e `firmware/` intactos.
- **Próxima etapa**: Fase 4.10B (`ANALISE_ADC.md` Blocker 3 + `PROJETO_MUTE_FISICO.md` Blocker 4 + validação B3/B4).

## CHECKPOINT GATE B - Projeto Elétrico & SPICE B3/B4 APROVADOS / Fase C e Bancada Pendentes

Data: 2026-11-12. **Decisão:**
- **Projeto elétrico, CAD, ERC & SPICE Fase 4.10B (Blockers 3 + 4):** **PASS** (Gate B aprovado; autoriza execução da Fase 4.10C quando solicitada).
- **Teto global do estado atual:** **EM REVISÃO - GATE B** (teto máximo após Fase C antes de ensaios físicos de placa continua `APROVADO DOCUMENTALMENTE PARA ENSAIOS CONTROLADOS`).
- **Pendências explícitas mantidas**:
  - **Pré-requisitos físicos de bancada**: `A410-01` (pinagem/estabilidade do exemplar `CW7805` com `J5` aberto e codec ausente), `A410-05_hw` (inspeção IC buck `U2` WeAct V1.2 e droop), `A410-07_hw` (inspeção física ESP32 GPIO16/17 livres) e verificação física em osciloscópio do relé `G5V-1-DC12` (`operate/release/bounce`) + casamento térmico `Q9/Q11`, `Q10/Q12`.
  - **Fase 4.10C (pendente, pausada por solicitação do usuário)**: `A410-08` (footprints oficiais KiCad em todos os componentes restantes da BOM, consolidação final e geração de `MANIFESTO_SHA256.txt`).
- **Escopo implementado na Fase B (Folhas 2, 4 e 10 -> total 183 componentes, 454 terminais físicos, 96 redes, 10 folhas)**:
  - **Blocker 3 (`ANALISE_ADC.md` — Clamp ativo compensado por Vbe)**: `D9..D12` (`BAT85`) integralmente removidos; adicionados divisores/seguidores `R48..R53`, `C45..C48`, `Q9 (2N3904)`, `Q10 (2N3906)` (Folha 10A) e grampos `Q11..Q14` (Folha 2B). `AINA_P/N` contido em `[+0,2979 V, +4,9910 V]` nos cantos `C1..C4` (`0..70 C`, `4,75..5,25 V`, `hFE 80..250`), **0,0000 mA** injetados em `+5VA`, THD `0,000878%` (`0 dBFS`) e `0,000096%` (`0,50 Vp`), resíduo off-state `+30,15 / -30,08 mV`. `+5VA` máx `62,74 mA` (`< 65 mA`).
  - **Blocker 4 (`PROJETO_MUTE_FISICO.md` — Mute eletromecânico fail-safe)**: `C5` atualizado para `OUT_PRE`, `R6 = 47 kohm` (`OUT_PRE..GND`), `K1` (`Omron G5V-1-DC12`, footprint `Relay_THT:Relay_SPDT_Omron_G5V-1`), flyback `D16` (`1N4148`), supervisor `+RAW` (`U8 TL431ACZ`, `Q15`, `R54..R59`), porta AND 3 entradas + descarga rápida (`Q16..Q19`, `Q22`), temporizador anti-pop (`R60`, `C49 = 47 uF`, `D17 BZX55C4V7`) e Schmitt driver (`Q20`, `Q21`, `R68..R72`). SPICE (`17/17 PASS`): unmute em `5,899 s` (`pop = 1,2321 mV < 5 mV`), `0,0000 mV` em mute, plug-pull corta bobina em `RAW = 9,00 V` com `VA = 5,00 V` íntegro, NC fecha em `8,26 ms` (`flyback = 12,30 V`), retenção `10,64 mA @ 10,5 V`, brownout `8,2 V` zera saída e drena `C49 = 4,0 mV` (`1,152 s` re-espera), queda `CODEC_RST` (`2,49 ms`) / `VA_OK` (`2,20 ms`), perda `20 Hz = -0,0027 dB`, isolação `-185,61 dB`, THD em condução `0,000066%`.
- **Verificações executadas (`sh docs/hardware/rev4_10/run_B.sh`)**: `14/14` testes `validar_alimentacao.py`, `12/12` testes `test_interfaces_indep.py`, `16/16` cenários ngspice `simular_A.py`, `17/17` cenários ngspice `simular_B.py`, `13/13` testes independentes `auditar_cad_B.py --export`, **0 violações ERC** no KiCad 10 (`ignored_checks = []`), `validate_layout.py` (`454` terminais / `96` redes / `0` cruzamentos) e auditoria adversarial `ADVERSARIAL_GATE_B.md` (`APPROVED`).
- **Preservação**: `BASE_REV49_SHA256.txt` (`97/97 OK`) e `git diff 1c73c02 -- firmware/ docs/hardware/rev4_9/ output/rev4_9/` vazio.
