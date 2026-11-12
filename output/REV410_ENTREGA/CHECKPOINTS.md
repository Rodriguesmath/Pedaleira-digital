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
