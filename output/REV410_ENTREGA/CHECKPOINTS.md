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
