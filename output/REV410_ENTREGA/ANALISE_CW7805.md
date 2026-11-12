# CW7805 mantido - análise 4.10A

2026-11-12. Decisão do usuário: manter o genérico de três pinos retirado de outra placa; qualificação pendente. A origem em aparelho alimentado em AC não fornece fabricante, pinagem/TAB, tensão máxima, corrente, estabilidade ou limites térmicos. Saída nominal de 5 V é premissa funcional, não garantia de todos esses parâmetros. Nenhum dado do ST L7805 foi atribuído ao exemplar.

Implementado: placas retiradas da saída CW; U5 fornece +5V_CW, com C22/C37/R21 e D8 preservados. J4 dá acesso somente à carga artificial. J5 fica SEM shunt e separa +5V_CW de +5VA. R27/R28 e VA20 ficam depois de J5. STM e ESP usam USB próprias; VD/VL vêm de +3V3_STM. D8 descarrega saída CW para RAW e não arbitra fontes.

A pinagem numérica 1=IN,2=GND/TAB,3=OUT herdada do desenho é HIPÓTESE NÃO QUALIFICADA, identificada na BOM e conexões. Não é instrução liberada de montagem do exemplar desconhecido. Antes de energizar, os terminais precisam ser determinados por evidência técnica. J5 aberto não torna segura uma ligação errada do próprio CW.

## Cálculos reproduzíveis

Executar `python3 docs/hardware/rev4_10/validar_alimentacao.py`.

- VA: IA típico45mA/máximo53mA sob condições Cirrus DS593F2 p17.
- R21 máximo: 5,25/(910x0,99)=5,8275mA; divisor ADC máximo0,21021mA.
- Orçamento CW do conjunto: **59.0377mA**; típico aproximado50,6945mA. Não inclui corrente de partida ou injeção dos clamps como se fossem conhecidas.
- RAW assumido10,5..12,6V: 12V±5%, queda D1 máxima adotada0,9V; não se impõe queda mínima garantida.
- Iq8mA é PROXY comparativo de família, não especificação CW. Dissipação conservadora calculada **0.564246W**; máximo de cantos consistentes **0.559732W**.
- Com thetaJA hipotético50°C/W e ambiente40°C, Tj proxy68.21°C. Não é temperatura medida/garantida nem qualificação sem dissipador.
- A revisão4.9 orçava aproximadamente0,909A e7,236W. Essa redução elimina a justificativa automática do antigo dissipador<=2°C/W; a seleção térmica real permanece pendente.
- C37=1000uF armazena13,8mJ a5,25V; compatibilidade de capacitância/ESR, inrush e estabilidade não foram simuladas nem medidas. C21=330nF e C22=100nF preservados.

Com J5 aberto, ADC_BIAS/VA não são carga intencional do CW. Para futuro ensaio isolado, carga externa100ohm±1%/1W em J4 representa até53,03mA a5,25V, além do bleederR21; é equipamento de ensaio a providenciar, não novo componente do circuito. Codec retirado e sinais externos desconectados. Não executar ensaio supondo pinagem desconhecida ou curto IN-OUT.

## Fundamentação e pendências

[Cirrus DS593F2](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf), p9/p17/p27: VA4,75..5,25V e correntes nas condições publicadas. [TI TL072 SLOS080W](https://www.ti.com/lit/ds/symlink/tl072.pdf), p11/p15: modo comum e caracterização em±15V; não usar TL072H como se fosse o clássico. [Vishay 1N5822](https://www.vishay.com/docs/88526/1n5820.pdf): Vf condicionado, não mínimo0,3V. PDFs preservados na auditoria4.9. [WeAct oficial](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723): 1A máximo total do buck, não 1A livre.

Pinagem/fabricante/estabilidade/SOA/térmica CW continuam não demonstrados. Variações da placa ESP e capacidade livre3V3 também não foram medidas. Esses itens não serão convertidos em resultados por decisão editorial. A qualificação pendente é uma escolha registrada do usuário; não foi substituído o regulador.
