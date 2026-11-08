# Montagem em perfboard — revisão 4.9

Autoria: Rodrigues M. Lima. Proposta para **placa de ilhas individuais**, malha 2,54 mm. Não é layout de PCB, não há roteamento industrial ou garantia de estabilidade. O estado NÃO APROVADO exige montar e qualificar por subconjuntos, conforme TESTES_BANCADA_REV49.md. Não instalar o CS4272 antes da aprovação das alimentações.

## Disposição física recomendada

Da esquerda para a direita: jack de guitarra e buffer; drivers e interface ADC junto do adaptador CS4272; receptor DAC/filtro e jack de saída. Em uma faixa separada, do outro lado do codec: STM32 e sinais digitais curtos; ESP32 mais afastado da entrada de guitarra, com antena livre de metal e fios.

Na borda oposta ao jack de guitarra: J1, fusível, diodo de potência, CW7805 e dissipador. Não colocar o dissipador aquecendo os TL072, capacitores de bias ou adaptador TSSOP. Fixar mecanicamente antes de conectar: terminais TO-220 não devem sustentar dissipador ou placas. Confirmar TAB/GND e eventual isolamento do chassi pelo fabricante real.

Reservar espaço para retirar os soquetes DIP-8 e o adaptador CS4272, acessar todos os TP e trocar valores durante ensaios. Não fechar a caixa antes de passar nos testes de fonte e oscilações.

## Ordem de montagem

1. Marcar ilhas e coordenadas no papel, desenhar o lado das soldas espelhado e conferir separadamente ao esquema. Não usar o desenho funcional como mapa automático de ilhas.
2. Fixar conectores, porta-fusível, suporte do regulador/dissipador e soquetes vazios. Montar o barramento real de GND e conferir continuidade.
3. Montar J1/F1/D1/C33. Testar polaridade e tensões sem qualquer CI/placa sensível.
4. Montar CW/C21/C22/C37/R21/D8 somente após confirmar pinagem, com dissipador. Ensaiar a carga e estabilidade do regulador.
5. Distribuir +5V em três ramais e GND de retorno adequados: STM32, ESP32 e codec. Não levar potência do ESP através da placa STM32 ou do jack de áudio.
6. Montar R22/R23/C38/C39 para VREF_OP e R27/R28/C40/C41 para ADC_BIAS. Identificar cada referência por nome; cores de fio não substituem labels. Medir sem instalar TL072/codec.
7. Montar C1/R26/R3 e clamps da guitarra, depois os soquetes dos dois TL072 e redes de feedback. Desacoplar diretamente entre pinos 8 e 4.
8. Montar a interface ADC, seus capacitores de acoplamento bipolares, R18/R20 de 1,5 kΩ, resistores de bias, filtro e clamps. Testar com carga fictícia antes de conectar AIN do codec.
9. Montar receptor DAC, saída e bleeder; C5 positivo para o filtro/OP, negativo para P10. Testar com fonte de sinal diferencial apropriada e carga de 100 kΩ.
10. Somente após tensões e transientes aprovados, instalar o adaptador CS4272 e conectar clocks/dados curtos. Verificar todos os 28 pinos, não apenas os nomes “alimentação/áudio”.
11. Montar chaves e LEDs, conferir continuidade dos jacks/SPDT, identificação física dos headers e revisão das placas. Programação USB com VBUS isolado do barramento externo.
12. Executar a sequência de testes, registrar capturas e atualizar a documentação após qualquer troca de componente ou jumper. Não remover o gate de áudio apenas para “tentar som”.

## GND e alimentação

Usar GND contínuo de baixa impedância, com ligações curtas e fio de seção apropriada para a corrente de ~1 A. Fonte/regulador e retornos das placas não devem compartilhar trechos longos finos com retorno da guitarra. Alimentação em estrela é uma estratégia de corrente, não autorização para dividir GND em ilhas desconectadas.

Unir AGND e DGND do codec com trecho muito curto na região do adaptador e manter retornos de clocks próximos do caminho dos sinais. A corrente não pode fazer volta passando pelo jack para voltar à MCU. Nunca colocar resistor, diodo ou ferrite separando retornos críticos sem projeto específico.

VREF_OP e ADC_BIAS são nós de sinal/bias, não GND e não fornecem corrente às placas ou LEDs. VCOM só recebe os capacitores locais e ponto de teste. Não usar malha do cabo de guitarra como retorno de alimentação. Chassi/bare grounding deve ser planejado com os jacks e equipamento externo para evitar laços; não desconectar aterramento de proteção do equipamento de bancada.

## Capacitores e redes locais

C21/C22 ficam a poucos milímetros do CW. C37 próximo à distribuição, sujeito à qualificação de inrush. C23/C24 junto de VA20, C25/C26 junto de VD9 e C27/C28 junto de VL10; retorno curto ao GND correspondente. C12/C13 FILT+ e C14/C15 VCOM junto do codec, sem relógios atravessando essa região.

C29/C30 junto do DIP U1 e C31/C32 junto de U3. O capacitor de 100 nF deve ligar efetivamente os trilhos no CI, e não ficar na outra ponta de um fio longo. As reservas eletrolíticas complementam, não substituem, os cerâmicos.

C18/C19 de 22 pF têm a mesma ordem de grandeza de capacitâncias parasitas da montagem: colocá-los diretamente nos caminhos de realimentação, com terminais curtos. Não deixar feedback dar volta pela perfboard. C20/C35/C36 e BAT85 devem ficar junto aos pinos AIN/adaptador; R18/R20 limitam corrente e isolam a carga capacitiva. C2/C16 são bipolares e precisam ter tensão adequada para a diferença DC dos domínios.

Para pequenas capacitâncias de áudio/RF, usar C0G ou filme; evitar cerâmica de alta dependência de tensão. Confirmar capacitância por medição quando necessário; “104” não é 100 pF (é 100 nF), “101” é 100 pF, “681” é 680 pF, “220” é 22 pF, “222” é 2,2 nF.

## Fios, jumpers e clocks

Priorizar fios curtos no lado dos componentes e pontes isoladas no lado das soldas. Evitar empilhar terminais descobertos em ilhas vizinhas. Usar fios de potência adequados à corrente; terminais de resistores finos não devem virar barramento de ~1 A.

MCLK/BCLK/LRCK/dados entre STM32 e codec: alvo de poucos centímetros, preferencialmente até ~3 cm no protótipo, acompanhados de retorno GND. Evitar passar por baixo da entrada de guitarra, VREF_OP, VCOM ou feedback dos OPs. Não criar stubs longos nos TP de clock. Se houver ringing, medir antes de adicionar resistores; qualquer terminação acrescentada precisa entrar no esquema/BOM e ser revalidada.

Não usar flat cable longo compartilhando relógio rápido e entrada analógica. UART para ESP pode ser mais longa, mas deve ir com GND e longe dos nós de alta impedância. Antena Wi-Fi e correntes de rádio não devem ficar sobre o buffer da guitarra.

A WeAct V1.2 tem conversor buck/indutor onboard. A perfboard não adiciona indutores ou conversores; afastar fisicamente a região onboard da entrada analógica. Se a restrição do projeto proibir até esse indutor, a arquitetura precisa ser revista antes da montagem.

## Pontos de teste

| TP | Nó | Uso |
|---|---|---|
| TP1 | +RAW | tensão após diodo |
| TP2 | +5V | CW e degrau de carga |
| TP3 | +3V3 | saída onboard e carga digital |
| TP4 | VREF_OP | meia alimentação dos OPs |
| TP5 | VCOM | referência interna sem carga |
| TP6 | IN_BUF | saída do buffer guitarra |
| TP7 | AINA_P | ADC positivo, inclusive transientes |
| TP8 | AINA_N | ADC negativo, inclusive transientes |
| TP9 | DAC_BUF | receptor diferencial com bias |
| TP10 | GND | referência real da medição |
| TP11 | ADC_BIAS | bias independente 0,48×5 V |

Identificar TP pelo número e nome. Para conferir a diferença AIN+−AIN−, usar dois canais referenciados ao GND e função matemática/diferencial adequada; não colocar a garra GND em AIN−.

## Inspeção final

Conferir ilhas sob lupa e continuidade ponto a ponto usando CONEXOES_COMPLETAS_REV49.csv. Anotar qualquer componente substituído e comparar seus limites. Confirmar polaridade dos eletrolíticos, direção de cada diodo, ausência de entradas sem bias e retenção mecânica de conectores/dissipador. Capturar partida/desligamento antes de conectar equipamento externo. O pop previsto no P10 precisa de mute/desconexão externos até que uma solução física seja implementada e testada.
