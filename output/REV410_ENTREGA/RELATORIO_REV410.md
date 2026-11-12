# Revisão 4.10 - checkpoint de trabalho A

2026-11-12. **Veredito: REPROVADO para o conjunto; CHECKPOINT A BLOCKED.** Candidato editável salvo; B e C não iniciadas. Não é aprovação para funcionamento completo nem aprovação documental integral para ensaios do conjunto.

## Alterações e evidências

Placas saíram da carga CW e usamUSB independentes; VD/VL pertencem a +3V3_STM. UART foi corrigida documentalmente com ISO7721DR; positivos permanecem separados. J5 aberto por padrão seccionaCW->VA, sem fingir que isola sinaisADC. Mantidos todos os valores originais e topologias de ganho.114 componentes, 288 terminais e 61 redes; oito folhas A4 paisagem e autoria Rodrigues M. Lima.

Foram executados11 testes de alimentação/candidato,12 cálculos independentesUART e validação gráfica de conectividade. Logs e resultados ficam emVALIDACAO_A eREVISOES. ERC/XML atuais e revisão independente devem ser consultados emkicad eREVISOES/CAD_A_INDEPENDENTE.md; não usar um log anterior como se cobrisse uma nova exportação. Passar ERC não resolve os bloqueios elétricos.

Orçamento CW calculado59.0377mA e dissipação proxy conservadora0.564246W, contra aproximadamente 0,909 A / 7,236 W na4.9. Nenhum parâmetro térmico de fabricante foi atribuído aoCW genérico. Não houve montagem, compra, medição ou simulação física doCW.

## Bloqueios e decisão de escopo

Usuário manteveCW genérico e qualificação pendente. Ainda faltam pinagem/limites rastreáveis ou qualificação externa; a proveniência de placaAC não demonstra esses dados. Também permanecem reset automático na perdaVA, proteçãoADC durante queda, mute físico e capacidade livre3V3. Condições de isolamento autorizam preparar ensaios de subconjuntos; não fecham o gate do conjunto.

A missão exige PASS A antes de B e PASS B antes de C. Não foram criados ANALISE_ADC.md/PROJETO_MUTE_FISICO.md com projetos fictícios, nem simulações para uma correção não realizada. Os achadosADC/mute da 4.9 continuam explícitos na matriz de riscos. O usuário pode retomar deste checkpoint após resolver o bloqueio de alimentação ou redefinir formalmente o escopo dos gates; não se marcou FAIL comoPASS.

## Componentes adicionais e custo

U6 ISO7721DR, adaptador SOIC-8 / DIP-8, dois capacitores de 100 nF, dois resistores de 10 kΩ, dois resistores de 47 kΩ e header/shunt J5. Aquisição/estoque/custo não confirmados; aumento de uma pequena submontagem de interface. Não foram inventados preços. CW, TL072 e codec e valores originais mantidos.

## Retomada

Ler CHECKPOINTS.md, MATRIZ_RISCOS.csv, REVISOES/CAD_A_INDEPENDENTE.md e scripts emdocs/hardware/rev4_10. Preservar firmware e originais4.9. A pasta contém trabalho parcial rastreável e candidato PDF claramente marcado Em revisão - fase A. Não tratar este checkpoint como entrega final 4.10 aprovada.

## Encerramento e transferência

O usuário encerrou esta etapa e solicitou um prompt para o Gemini Antigravity Flash 3.8 High concluir as correções. O prompt está incluído na pasta e nas fontes. Nenhum gate foi promovido para PASS por causa do encerramento.
