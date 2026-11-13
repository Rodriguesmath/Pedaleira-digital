# Revisão adversarial independente — checkpoint 4.10A

Data: 2026-11-12. Papel E. Escopo exclusivamente alimentação e contenção de riscos anteriores à fase B. Nenhum CAD, componente ou firmware foi alterado por esta revisão. Não foi projetado mute ou novo condicionamento ADC.

**Decisão: BLOCKED para o conjunto conectado.** A arquitetura USB independente é coerente e reduz o problema térmico do CW. A documentação disponível ainda não demonstra a segurança das interfaces e do regulador físico. É possível isolar fisicamente os riscos e qualificar subconjuntos; essa contenção precisa aparecer no CAD e nas condições de ensaio, sem ser apresentada como operação da pedaleira completa.

## Evidências efetivamente verificadas

- Missão integral no anexo `d2259877-0c5a-4aef-9a4f-365af81cdb67/Texto colado.txt`, incluindo a proibição de iniciar B antes de PASS A.
- `output/auditoria_rev49/AUDITORIA_REV49.md`, `RESULTADO_AUDITORIA.json`, errata e cálculo da alimentação; fontes originais do codec, TL072 e WeAct.
- `output/REV410_ENTREGA/ANALISE_CW7805.md` e cálculos independentes em `VALIDACAO_A/calculos.json`.
- Script independente `docs/hardware/rev4_10/validar_alimentacao.py`: oito estados, 24 transições dirigidas de uma fonte, 32 cantos de corrente/dissipação e oito verificações automatizadas passaram. Passar esses testes confirma aritmética e cobertura, não segurança física.
- Consulta direta ao documento primário [Cirrus DS593F2, outubro/2021](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf). Páginas citadas são a numeração impressa do documento.
- `docs/audits` não existe nesta árvore; as evidências foram localizadas em `docs/hardware/auditoria_rev49` e `output/auditoria_rev49`. Nenhuma ausência foi preenchida com conteúdo presumido.

## Achados adversariais

| ID | Severidade | Evidência | Impacto | Correção ou contenção verificável | Estado |
|---|---|---|---|---|---|
| EA01 | ALTO | CW7805 físico sem fabricante, pinagem/TAB e especificação identificados | Regulação, estabilidade e conexão de montagem não demonstradas, mesmo a 59 mA | Identificar a peça com evidência rastreável; se impossível, selecionar formalmente componente rastreável. Até lá remover CW e codec dos ensaios sensíveis; não ligar um componente de pinagem presumida | Aberto, informação externa necessária |
| EA02 | ALTO | UART une dois domínios USB; TX ocioso pode estar HIGH com receptor desligado | Segurança power-off, corrente de injeção e alimentação parasita não demonstradas | Isolar fisicamente TX e RX para ensaios independentes; operação permanente exige interface com limites de power-off documentados ou outra contenção demonstrada | Aberto |
| EA03 | ALTO | CS4272 pode ter VD/VL ativos e VA ausente, ou VA ativo e VD/VL ausentes | Falta garantia de estado de interfaces e reset durante todas as transições; não é prova automática de dano | Manter reset assertado por condição física quando qualquer trilho não estiver válido; só liberar após alimentação e clocks estáveis; contenção temporária: codec ausente e todas as suas linhas de sinais desconectadas | Aberto |
| EA04 | ALTO | Drivers TL072 usam RAW; VA e referências têm partidas/descargas próprias | RST não desconecta pinos analógicos. Sinais e cargas dos capacitores podem permanecer enquanto VA cai | Para fase A, retirar CS4272 e isolar todos os sinais analógicos antes de testar alimentação. Não usar a promessa de futura proteção B para marcar A seguro com codec conectado | Aberto; não foi projetada a correção B |
| EA05 | MÉDIO | Buck WeAct anunciado como 1 A total; corrente livre não medida/documentada por composição | 28 mA digitais adicionais não foram somados a um máximo de consumo comprovado da placa | Confirmar variante da placa, curva/capacidade do regulador e orçamento completo; alternativamente fonte 3,3 V rastreável, selecionada formalmente | Aberto |
| EA06 | MÉDIO | Datasheet CS4272 não diz que VA deve sempre anteceder VD/VL, nem fornece limite de diferença entre trilhos na tabela absoluta | Proibir uma sequência específica como se fosse requisito Cirrus seria uma especificação inventada | Registrar ausência de garantia detalhada, respeitar reset e limites individuais; consultar fabricante se for indispensável uma garantia de operação parcial | Corrigido conceitualmente nesta revisão |
| EA07 | MÉDIO | Ainda não existe neste escopo prova por CAD da separação dos três 5 V | Notas de texto podem coexistir com rede antiga unida | Auditar XML real: USB_STM_5V, USB_ESP_5V e VA_CW_5V não podem pertencer à mesma partição, inclusive por D8, jumpers ou conectores | Aguardando CAD real |

Não foi atribuído um diodo interno universal a GPIO STM32 ou ESP32. O comportamento power-off depende do tipo de pad e do circuito real. Sem Ioff, impedância série e curva do pad, não existe cálculo numérico confiável da corrente injetada. `null` nos resultados representa ausência de limite demonstrado, não corrente zero.

## Sequenciamento e reset do CS4272: o que a fonte permite concluir

DS593F2 p9 especifica VA 4,75–5,25 V, VD 3,1–5,25 V e VL 2,37–5,25 V para operação; os máximos absolutos individuais são −0,3 a +6 V. Entradas digitais exigem −0,3 a VL+0,3 V; entradas analógicas, GND−0,3 a VA+0,3 V, simultaneamente ao limite de corrente de ±10 mA. Reset não revoga esses limites.

O §5.2.1, p27, manda manter RST LOW até alimentação, MCLK e LRCK estarem estáveis; então liberar RST, escrever CPEN/PDN e configurar antes da operação. Isso dá uma condição funcional de inicialização. Não define um isolador power-off nem garante que um pino sem alimentação aceite qualquer nível aplicado. Também não prova que VA=0 com VD/VL presentes seja proibido por si só: essa alegação não deve ser feita.

O pull-down R13=10 kΩ é útil quando o STM está desligado ou em alta impedância. Se PD10 já estiver HIGH e somente a fonte analógica falhar, o pull-down não vence a saída ativa. Logo, firmware anterior com reset inicial LOW não constitui, sozinho, intertravamento de alimentação. Para retorno abrupto da fonte, precisa haver condição física de retenção/assertion ou comportamento power-good documentado. Não foi selecionado supervisor, transistor ou relé sem limites e disponibilidade.

Os pinos AMUTEC/BMUTEC são saídas de controle de mute externo; DS593F2 §5.5, p34, não os descreve como isolamento de alimentação ou desconexão dos pinos AIN. Não usá-los como substituto de um gate de alimentação. O projeto de mute permanece fora desta fase.

## VD/VL: alternativas reais e suas limitações

1. **VD e VL na saída 3,3 V da WeAct:** menor alteração e sem CI extra; I²C, MCLK, LRCK, BCLK e SDIN têm origem no mesmo domínio que os pinos digitais do codec. A demanda digital é até 28 mA nas condições da tabela p17. Isso elimina a divergência estática direta de alimentação entre STM e VL; não prova comportamento interno do codec com VA ausente, corrente livre do buck ou ausência de transientes.
2. **VD em 5 V analógicos e VL em 3,3 V STM:** as faixas recomendadas permitem esses valores individualmente. A tabela p17 fornece 49 mA máximos para VD/VL ambos em 5 V, mas não caracteriza diretamente a repartição de corrente nessa combinação mista. VD não deve ser ligado em 5 V apenas para contornar um orçamento desconhecido; cria mais um sequenciamento a documentar. Nenhuma vantagem indispensável demonstrada.
3. **VD/VL em 3,3 V originados do ESP:** transfere o problema para I²C/SAI e adiciona dependência de uma placa ESP genérica não identificada. Não preferível.
4. **Regulador adicional de 3,3 V no domínio analógico:** permitiria co-alimentar o codec, mas passaria a exigir contenção nas interfaces com STM USB desligado. Componente não disponível não pode aparecer na BOM como já existente. É alternativa de projeto, não solução implementada.

A primeira opção é a candidata mínima, ainda condicional. Não confundir capacidade total de 1 A da placa com 1 A disponível externamente. O orçamento anterior de 350 mA era uma reserva, não corrente máxima caracterizada do hardware real.

## CW7805: efeito térmico comprovável e limites da identificação

A carga normal máxima conservadora proposta é 53 mA em VA mais 5,8275 mA no bleeder e 0,21021 mA no divisor ADC: **59,0377 mA**, sem inventar corrente de partida ou fuga dos clamps. TL072 e divisor OP saem de RAW e não são carga da saída CW.

Com RAW máximo 12,6 V, saída mínima assumida 4,75 V e Iq proxy 8 mA, a dissipação conservadora é **0,564246 W**. A enumeração de cantos consistentes de tensão/carga dá 0,559732 W; usar o superior conservador é aceitável. Com θJA comparativo de 50 °C/W, a elevação seria 28,21 °C. A exigência antiga de dissipador ≤2 °C/W não é automaticamente necessária nessa nova carga.

Esses números não identificam CW. Um proxy ST não transforma estabilidade, pinagem, corrente quiescente ou resistência térmica desconhecidas em garantidas. D8 protege determinada descarga reversa entre saída e RAW; não valida pinagem do CW e não arbitra fontes USB. Fusível F1 não limita tensão de saída de um regulador defeituoso. Não foi imposto um requisito novo de suportar qualquer falha interna simples; a incerteza básica de identidade já existe em operação normal.

## Contenções viáveis sem inventar componentes disponíveis

**Contenção imediata para ensaios isolados:** CS4272 removido fisicamente; UART TX/RX desconectadas; todas as conexões STM↔codec desconectadas; drivers e receptor analógicos desconectados do soquete/adaptador do codec; jack de saída externo desconectado. GND comum pode ser mantido para instrumentação apropriada, sem usar VREF_OP como terra. Uma nota não realiza essa contenção: devem existir conectores/jumpers acessíveis e posições inequivocamente definidas, ou remoção física do módulo correspondente.

CW ainda não identificado não deve ser montado supondo pinagem. Teste futuro exige identificação/conexão determinada por evidência e carga artificial, dentro dos limites da fonte e da documentação aplicável. Alimentação de bancada regulada, limitada em corrente e com proteção documentada pode qualificar cargas separadamente, mas não passa a ser a fonte CW do projeto nem está presumida disponível.

Essa contenção isola os CIs sensíveis e autoriza preparar um roteiro de ensaio de subconjuntos; não autoriza declarar A PASS para o circuito completo conectado. Se o coordenador restringir formalmente o checkpoint a um subconjunto contido, precisa declarar a restrição e os jumpers abertos, manter o circuito completo BLOCKED e não avançar silenciosamente como se todos os riscos tivessem sido corrigidos.

**Correção permanente possível:** interface digital com comportamento power-off especificado e intertravamento/reset ligado aos domínios válidos. Pode requerer componente adicional, mas não se demonstrou que qualquer CI específico seja indispensável. Não é correto selecionar um CI somente pelo nome da função: alimentação dos dois lados, Ioff, níveis, estado desligado, largura de banda dos clocks e disponibilidade precisam ser demonstrados. Os componentes disponíveis informados não incluem tais interfaces prontas.

## Informação externa mínima que pode remover o bloqueio

- Fabricante/logotipo/marcação completa ou origem rastreável do CW7805 e documento correspondente. Se isso não for possível, decisão de seleção/aquisição de regulador identificável; não presumir disponibilidade.
- Variante exata e esquema da ESP32 DevKit, incluindo módulo, regulador, USB e pinos UART usados.
- Confirmação da variante/montagem real da WeAct e orçamento demonstrável do 3,3 V, ou dados de caracterização posterior expressamente fora desta missão.
- Caso se exija tolerância automática a qualquer estado USB sem desconexão manual, disponibilidade/seleção de contenção física de interfaces e reset. Sem esse requisito explícito de operação contínua, um procedimento de isolamento pode servir apenas a ensaios separados, não a uma pedaleira interligada.

## Critérios para a próxima auditoria do CAD

1. Conferir separação por partições de rede, não por nomes impressos: três fontes 5 V independentes; nenhum antigo jumper +5 V preservado por engano.
2. Conferir VD9/VL10, VA20, AGND21/DGND8 e retorno comum; D8 nunca pode criar caminho da USB para RAW.
3. Conferir origem de pull-ups I²C, reset físico e estado de todos os pinos de interface em cada um dos oito estados.
4. Conferir contenção dos pinos analógicos quando VA não está válida, sem substituir essa conferência por RST LOW.
5. Verificar que BOM e notas marcam componentes ainda não selecionados ou não disponíveis; nenhum placeholder pode parecer compra confirmada.
6. Só aceitar PASS A após CAD real, conectividade, condições de isolamento e revisão independente coerentes. ERC sozinho não decide esse gate.

**Resultado final desta revisão: BLOCKED A; B e C não iniciadas por este auditor.**
