# AUDITORIA REV49

Autoria: Rodrigues M. Lima. Data: 2026-11-07.

**VEREDITO: NÃO APROVADO — REQUER CORREÇÕES.** O conjunto está documentado e verificável, mas não liberado para instalar o codec e operar áudio. Há um roteiro para qualificar os subconjuntos em bancada. Não houve teste físico. O CW7805 não foi identificado; transporte SAI/BDMA ainda não existe; partida, desligamento e estabilidade precisam ser qualificados. Esses impedimentos não são escondidos pelo ERC limpo.

## Arquitetura e decisão sobre 9 V

A proposta 4.9 usa uma única fonte **12 V DC regulados ±5%, ≥1,5 A**, centro positivo, F1 e D1 Schottky. Mantém dois TL072, CS4272 em adaptador passivo, CW7805 e ambas as placas. Não acrescenta CI nem gera trilho negativo. A troca da fonte de 9 por 12 V é a alternativa mínima escolhida; **não ligar 9 V esperando o desempenho dimensionado para 12 V**.

TI SLOS080W §5.3 dá, para a família clássica correspondente, entrada recomendada a partir de V−+4 V; §5.8 caracteriza modo comum e swing em ±15 V. A versão H tem limites diferentes e não foi tomada como equivalente. Em 9 V ±5%, supondo queda de proteção de 0,3..0,9 V, +RAW pode cair a 7,65 V. Meia referência =3,825 V, já abaixo de 4 V sem áudio; com ±0,5 V fica pior. Mesmo no nominal de 8,3 V, 4,15−0,5=3,65 V. Não basta observar a alimentação total mínima. A operação com driver diretamente em VCOM≈2,4 V é inadequada a essa faixa de entrada.

A +12 V, +RAW foi delimitado conservadoramente em 10,5..12,3 V; queda de D1 é uma hipótese de projeto a confirmar no componente e corrente reais. O fabricante/sufixo dos TL072 também precisa ser confirmado. A simulação a 9 V não reproduziu corretamente a perda de modo comum: isso é **limitação do macromodelo**, não evidência de aprovação de 9 V.

## Problemas e suspeitas investigados

| Item rev4.8 | Conclusão | Ação 4.9 / pendência |
|---|---|---|
| TC1044S não faz parte do estoque | Confirmado pelo usuário | Removido U4 e rede negativa; nenhum CI novo |
| TL072 em alimentação simples com VCOM nas entradas | Incompatível com limite inferior de modo comum | Bias OP elevado; isolação AC do ADC |
| 9 V com meia referência | Margem insuficiente no envelope requerido | Fonte simples de 12 V; 9 V rejeitado |
| VCOM usado como distribuição genérica de bias | Saída com corrente típica de apenas 1 µA | VCOM sem carga; ADC_BIAS independente de 0,48×VA |
| C18/C19=4,7 nF | Não equivalem aos 470 pF da figura 12; dependem da topologia | Nova topologia explicitada, 22 pF com 10 kΩ; comparação AC executada |
| Canal ADC B omitido/flutuante | Suspeita descartada na 4.8 após conferir netlist | Continua polarizado e mutado; bias agora ADC_BIAS |
| Entrada A negativa sem sinal complementar | Era uma perna sem sinal, não um curto automático | U3B agora gera −1, U3A +1 |
| Receptor DAC centrado em GND | Não serve ao TL072 com alimentação simples | Centrado em VREF_OP, ganho 0,499 |
| Rede de saída 1k/4,7n/1,5n | Queda em agudos e impedância maiores | 220 Ω/2,2 nF por seção, carga ≥100 kΩ |
| C5 bipolar | Correto para o circuito antigo sem DC; não universal | Agora eletrolítico, positivo para LP2, que tem DC ~VREF_OP |
| ADC acoplado por capacitores, partida/desligamento | Risco de transientes confirmado em modelo exploratório | R18/R20=1,5 kΩ, clamps BAT85 e filtro recalculado; ensaio obrigatório |
| XTI em GND e XTO em NC | Suspeita descartada | Mantidos, conforme S1 §5.2.3 para MCLK externo |
| PLL1 VCO=25/5×220=1100 MHz | Acima do máximo 836 MHz da tabela 39 do STM32H723 | Corrigido M5/N110/P1/Q2/R2: VCO550, CPU550; validar em placa |
| AF10 aplicada a PE4/5/6 | Erro confirmado | Corrigido AF8; PE0/PA0 continuam AF10 |
| 03h=30h | ATAPI=0000 deixa ambos DACs em mute | Corrigido 39h, Soft/ZeroCross e rotas A←L/B←R |
| 06h=00h com ADC I2S | Formato ADC errado | Corrigido 14h: I2S, canal B mutado, HPF ligado |
| Aguardar 10 ms após /RST antes de CPEN | Não garante escrever dentro de 10 ms | Pós-reset 1 ms, timeout I2C 3 ms; relógios devem existir antes |
| Código assume transporte de áudio | SAI/PLL3/BDMA/callbacks não implementados | Gate seguro em zero e /RST mantido LOW; não há áudio alegado |
| SW4 fazia bypass | Não correspondia a mute | Corrigido master mute; liberação de áudio continua bloqueada |
| ESP32 funcional | Apenas README no diretório | Nenhuma ponte Wi-Fi/MQTT implementada foi alegada |

## Referências distintas e estabilidade DC

GND é o retorno real. VREF_OP é R22/R23=2,2 kΩ/2,2 kΩ, C38=470 µF+C39=100 nF. ADC_BIAS é R27/R28=13 kΩ/12 kΩ, 0,1%, C40=100 µF+C41=100 nF, a partir dos 5 V. VCOM é exclusivamente a saída interna de U2/15 com C14=1 µF+C15=100 nF e TP5.

| Grandeza | Nominal | Envelope/hipótese |
|---|---|---|
| +RAW | 11,3 V | 10,5..12,3 V, fonte e diodo nas hipóteses indicadas |
| VREF_OP | 5,65 V | 5.1975..6.2115 V com 1% no divisor |
| VREF_OP Zdc | 1,1 kΩ | Capacitor reduz impedância AC; não é terra de potência |
| Corrente do divisor OP | 2.568 mA | 2,39..2,80 mA aproximadamente |
| τ OP | 0,517 s | ±20% do eletrolítico domina; esperar ≥5 s |
| ADC_BIAS | 2,4 V | 2.2776..2.5226 V, VA 4,75..5,25 V |
| Zdc ADC_BIAS / τ | 6,24 kΩ / 0,624 s | 0,48×VA; confirmar diferença para VCOM ≤50 mV |
| VCOM | típico 0,48×VA | Datasheet não dá min/max; não inventar faixa garantida |

A 20 Hz, C38 tem |Z|≈16,9 Ω. Uma corrente AC de bias de 0,5 V/1 MΩ=0,5 µA daria ~8,5 µV na referência; cargas reais de retorno e a fonte precisam ser medidas. Os divisores não fornecem corrente de alimentação. A simulação inclui impedância de saída de VCOM de 25 kΩ e a nova rede ADC não a carrega.

## Estágio da guitarra e headroom

C1=100 nF filme, R3=1 MΩ, R26=1 kΩ: corte aproximado 1.592 Hz, ganho +1, impedância nominal de entrada próxima a 1 MΩ na banda. D6/D13 e D14/D7 formam dois diodos em série por sentido contra VREF_OP. Um único 1N4148 por sentido mostrou compressão indesejada perto de 0,5 V no modelo e foi descartado. Os clamps novos reduzem esse efeito nominal, sem serem proteção contra surto de rede ou fonte conectada ao jack.

Com áudio ≤0,5 Vpk e divisor a 1%, a margem de entrada para V−+4 V é ≥0.6975 V antes de offsets. Admitindo 13 mV de offset e 7 nA×1 MΩ=7 mV de erro quente, restam cerca de 0,677 V. Os números são relativos ao limite inferior da família TI, não uma garantia de qualquer TL072 genérico. Limites de swing de ±15 V não foram extrapolados como garantia a 12 V. Para avaliar headroom, foi reservada heuristicamente margem de 3 V nas saídas e 4 V nas entradas; a confirmação é em bancada.

Guitarras ativas ou captadores fortes podem exceder 0,5 Vpk. Reduzir nível no instrumento/usar atenuador de alta impedância antes dos testes; não prometer ausência de clipping para qualquer instrumento. Ruído: resistor 1 MΩ isolado tem ~129 nV/√Hz a 300 K, ou ~18 µVrms em 20 kHz; o captador em paralelo muda o resultado. TL072 clássico não assegura o piso de ruído de 114 dB do codec. 24 bits é o formato, não resolução efetiva garantida.

## ADC diferencial e filtros

U3A copia IN_BUF; U3B inverte a parte AC em torno de VREF_OP, com R24/R19=10 kΩ/10 kΩ (0,1%). U3A usa R17=10 kΩ e C18 em paralelo no feedback; C18 não é, sozinho, o filtro passa-baixas do sinal. C19 em paralelo com R19 limita o ganho inversor em HF. C2/C16=10 µF bipolares removem o DC ~5,65 V e as entradas são recolocadas em ADC_BIAS por 100 kΩ. Não ligar o bias OP diretamente ao ADC.

A figura 12 da Cirrus usa uma topologia de feedback depois de 91 Ω, 634 Ω e 470 pF. **A 4.9 não é uma cópia dessa figura**: a proteção de transientes e a alimentação simples levaram a R18/R20=1,5 kΩ, clamps e rede RC própria. O custo é impedância maior que a recomendada, exigindo comprovação de THD/estabilidade com o modulador real. O modelo usa apenas 37 kΩ diferenciais, não reproduz a amostragem a 6,144 MHz. Logo, não se declara essa interface qualificada somente pela AC.

O par de capacitores de acoplamento equivale a 5 µF diferenciais. Com entrada mínima 37 kΩ, dois biases de 100 kΩ e 3 kΩ em série, fc≈0.930 Hz. O divisor resistivo carregado reduz ganho de 2 para cerca de 1,82. O filtro usa C20=680 pF entre pinos e C35/C36=100 pF para GND: Cdiff equivalente=730 pF, Rdiff=3 kΩ, fc sem carga≈72673.5 Hz. A simulação contém carga e diodos; não substituir esse cálculo aproximado pelo resultado completo.

Com R19=10 kΩ: 22 pF→723,4 kHz; 470 pF→33,86 kHz; 4,7 nF→3,386 kHz. A escolha é específica deste circuito; não é troca automática dos valores da figura 12. Resultados comparativos vêm abaixo. Os 1,5 kΩ também limitam a corrente extrema calculada para 12,3 V/1,485 kΩ≈8,28 mA, abaixo do limite absoluto de corrente de 10 mA. **Isso não garante sozinho o limite de tensão nos pinos**; a Vf real dos BAT85 e as sequências de rails precisam ser verificadas.

Full scale diferencial ADC: nominal 5,65 Vpp, mínimo conservador 5,0825 Vpp e máximo 6,2475 Vpp conforme tolerância de VA e escala do datasheet. Para guitarra de 0,5 Vpk, a simulação entrega ~1,82 Vpp diferenciais, cerca de −9,8 dBFS nominal: há headroom e perda de aproveitamento da faixa, documentada. Não recuperar essa perda por ganho digital esperando recuperar SNR analógico.

## DAC, saída, offset e carga

R1/R7=100 kΩ; R2/R8=49,9 kΩ, razões casadas 0,1%. A expressão DC/AC ideal é Vout=VREF_OP+0,499×(AOUTA+−AOUTA−). C10/C11 bipolares isolam o DC do codec. Cada saída DAC vê carga muito acima de 3 kΩ. No pior full scale de 1,01×5,25=5,3025 Vpp, o receptor varia ±1,324 V. Com +RAW mínimo e tolerância de referência, excursões ficam a aproximadamente 3,87 V dos trilhos: há margem de projeto sobre a reserva heurística de 3 V, sem alegar swing garantido a 12 V.

CMRR depende do casamento das razões, carga e layout; não prometer CMRR ideal. Redes de precisão ou resistores medidos são preferíveis. U1B não aciona fones; a carga prevista é ≥100 kΩ. R4/R5=220 Ω, C4/C6=2,2 nF. Dois polos interagem; sem carga H(s)=1/[R4·R5·C4·C6·s²+(R4·C4+R4·C6+R5·C6)·s+1]. Saída de baixa frequência tem impedância próxima a 440 Ω, mais 1/(jωC5).

C5 eletrolítico 10 µF com + no LP2, R6=1 MΩ e carga 100 kΩ: Rdescarga≈90,9 kΩ, fc≈0,175 Hz, τ≈0,91 s. DC no jack deve ficar <10 mV após estabilização. A partida/desligamento pode produzir volts de transiente na saída AC; firmware mute não elimina toda variação da referência. Manter o equipamento externo mutado/desconectado nesses eventos. Se silêncio automático for requisito, é necessária uma solução física de mute/disconexão ainda não implementada.

## CW7805, distribuição e térmica

O CW não foi convertido silenciosamente em L7805. Pinagem desenhada é a usual TO-220 vista frontal 1 IN / 2 GND e TAB / 3 OUT, **condicional à identificação**. Confirmar também se o TAB é GND antes de aparafusar ao chassi. A família ST serve de referência: saída conservadora 4,75..5,25 V, carga mínima 5 mA; dropout típico ~2 V não é um máximo garantido do CW desconhecido. A +RAW mínima 10,5 V oferece 5,25 V de folga sobre a saída máxima, mas isso não substitui datasheet/ensaio do exemplar.

C21=330 nF e C22=100 nF locais; C37=1000 µF é reserva e exige ensaio de inrush. R21=910 Ω mantém 5,49 mA e dissipa 27,5 mW nominal. D8, ânodo OUT/cátodo IN, protege descarga reversa. F1 limita falhas de entrada, não garante sobrecorrente segura de cada CI.

Um único CW alimenta **o mesmo +5V elétrico** para VA e ambas as placas; os ramais são separados fisicamente em estrela. Não se vende esse arranjo como dois reguladores independentes. Não há +5V_USB externo unido ao barramento. Reserva de corrente: STM32+codec digital+GPIO 350 mA, ESP 500 mA de orçamento de pico, VA 53 mA, bleeder e divisor ADC: total 0.9087 A. Esses são orçamentos, não medições nem consumo garantido dos módulos.

P≈(12,3−5)·0.9087+12,3·8 mA = 6.732 W. Sem dissipador, 50 °C/W da família daria elevação >300 °C: inviável. Com θJC proxy=5, θCS=1 e dissipador ≤2 °C/W, Tj estimado a 40 °C ambiente é 93.9 °C. **Parâmetros proxy não identificam o CW.** Validar 0,6 A contínuos/0,92 A de pico, carga transitória, temperatura e ausência de oscilação; revisar se a placa real exigir mais. Uma fonte 12 V ≥1,5 A e dissipador grande são componentes adicionais necessários. O custo térmico é uma limitação explícita da opção sem novo CI chaveado.

+3V3 vem do header P2.2 WeAct, cuja origem foi conferida no esquema V1.2: buck XT3410 e L1 de 2,2 µH. Deve fornecer reserva para ID do codec (máx.28 mA) e GPIO/LEDs, além da placa. O documento prova a existência do circuito, não a corrente livre/qualidade do exemplar. Medir 3,2..3,4 V sob DSP/Wi-Fi e nunca VD<3,1 V. Se “sem indutores” incluir o conversor interno dessa placa, o requisito é incompatível com mantê-la intacta; não foi afirmado atendimento literal.

## Clock, interfaces e firmware

PLL1 também foi auditada: a configuração anterior M5/N220/P2 escondia VCO=1100 MHz atrás de uma saída CPU=550 MHz. O limite do H723 é 836 MHz (S3 tabela 39). A correção aplicada M5/N110/P1/Q2/R2 mantém CPU550, Q275 e R275 MHz, com VCO550 MHz dentro da faixa. Não houve medição do clock da placa.

Pinagem e sentido completos em CONEXOES_REV49.md/CSV. I2C 100 kHz, R11/R12=4,7 kΩ: tr≈796 ns com 200 pF, abaixo de 1 µs; não afirmar 400 kHz nessa capacitância. VL=3,3 V mantém interfaces digitais compatíveis. XTI=GND e XTO=NC estão corretos para clock externo. Não usar MUTEC como GPIO de 3,3 V: pode subir a VA.

MCLK=12,288 MHz=256Fs, BCLK=3,072 MHz=64Fs, Fs=48 kHz, I2S dois slots de 32 bits/24 válidos. PLL3 candidato com HSE25 MHz: M=2, N=31, FRACN=3746, Q=8 (entrada PLL=12,5 MHz) fornece 49151992.797852 Hz, erro aritmético -0.146528 ppm. É alvo calculado para kernel ~49,152 MHz, **não configuração de SAI aplicada/testada**. Validar divisor MCLK/OSR/frame no RM0468 e escopo; erro do cristal soma-se ao arredondamento.

**SAI4 usa BDMA/DMAMUX2**, requests A=15 e B=16, conforme headers locais. Não planejar automaticamente DMA1/2 e buffers em DTCM. Reservar ping-pong em SRAM4/D3 acessível ao BDMA, alinhar 32 bytes e resolver cache/MPU. Blocos de 32 frames: janela 666,7 µs, 366.667 ciclos a 550 MHz; meta de DSP <25%=91.667 ciclos/bloco. Latência total inclui ADC/DAC e filas: <2 ms é meta a medir, não resultado.

Arquitetura prevista: BDMA RX/TX, half/full IRQ somente publicando flags/índices, processamento em blocos fora da UART, normalização correta de 24 bits/alinhamento, clamp final antes de converter, zeros e contador de erro ao underrun/overrun. Não fazer I2C, Wi-Fi, logs bloqueantes ou alocação de heap na ISR. Overdrive, EQ, delay e mute existem como classes; isso não prova uma cadeia real de áudio.

Firmware alterado: PLL1 com VCO dentro da faixa, AF8/AF10 separado; /RST inicial LOW; 03h=39h, 06h=14h; pós-reset 1 ms e timeout I2C 3 ms; mute inicial; SW4 master mute; gate dMAIN_AUDIO_TRANSPORT_READY=0 impede liberar codec sem transporte. A implementação de PLL3/SAI/BDMA/IRQ e a ponte ESP32 ainda estão ausentes. O main envia STATE_REPORT de 5 bytes e ACK de 1 byte, enquanto o contrato da skill descreve 11 e 2 bytes: alinhar/versionar os payloads antes de implementar o ESP; CRC correto não prova compatibilidade semântica. Não basta alterar o gate para 1. As mudanças preservam o framing UART AA 55 CMD LEN PAYLOAD CRC8, polinômio 0x07, e a cadeia DSP.

## Resultados executados e limites

- PDF vetorial, BOM e CAD gerados do mesmo modelo, com todos os terminais representados. Validação da rede visível é independente dos rótulos internos do CAD.
- ERC do KiCad e comparação de netlist pino a pino constam de VALIDACAO_REV49.json; nenhum erro crítico é ocultado por exclusões.
- Quality gate existente: 9 testes passaram, inclusive compilação sintática C++17 e CRC. O executável g++ do ambiente aponta para toolchain ARM; isso não é prova de execução nativa nem hardware.
- Teste C++17 nativo x86-64 executado com GCC extraído localmente: bypass transparente, mute, 480.000 amostras de stress finitas/limitadas e impulso de delay em 960 amostras (20 ms), pico 0,992188. Fonte test_dsp_host.cpp e log incluídos; não mede tempo de CPU no STM32.
- ngspice executou OP, AC e transientes de sinal com o macromodelo TI adaptado. O modelo foi caracterizado a ±15 V; o uso a +12 V é exploratório. A partida com esse modelo falhou ao partir de zero: a mensagem da tentativa está registrada em simulacao/LIMITACOES.txt e a análise de envelope usa um modelo limitado de um polo explicitamente distinto.
- O modelo do codec é resistivo (37 kΩ), sem modulador comutado, sem ruído/clipping digital. CW, WeAct, ESP e o sequenciamento real não foram simulados como dispositivos completos.

| Cenário | ADC 1 kHz (dB) | ADC 20 kHz (dB) | Saída 1 kHz (dB) |
|---|---:|---:|---:|
| nominal | 5.2120 | 4.9395 | -6.0804 |
| min_supply | 5.2120 | 4.9395 | -6.0804 |
| 9V_rejected | 5.2120 | 4.9395 | -6.0804 |
| cf470p | 5.2091 | 3.9912 | -6.0804 |
| cf4n7 | 4.9420 | -0.7299 | -6.0804 |

Nominal: ADC 20 Hz=5.1729 dB e 6,144 MHz=-50.67 dB. Saída 20 kHz=-6.1842 dB, relativa a 1 kHz cai ~0,104 dB. Não interpretar essa rejeição RF como THD validada.

No transiente de sinal, IN_BUF≈5.150..6.148 V; ADC+≈1.944..2.854 V; ADC−≈1.946..2.856 V; receptor DAC≈4.452..6.847 V; P10≈-1.192..1.191 V. Estímulos: guitarra 0,5 Vpk/1 kHz e DAC diferencial 4,8 Vpp/1 kHz, carga 100 kΩ.

Envelope de partida/desligamento de um polo: ADC+ mínimo -0.250 V, máximo 3.556 V; ADC− mínimo -0.249 V. A proteção aproximada ficou dentro de −0,3 V no modelo, mas diodos reais/rails podem alterar isso. A saída P10 teve mínimo -5.445 V e máximo 2.673 V: **há pop importante previsto**, não aprovado para conexão durante energização. Modelo não é garantia de sequência ou proteção em falha.

## Impedimentos de aprovação e menor caminho de fechamento

1. Identificar CW7805 e TL072 reais; confirmar pinagem, limites, capacidade e térmica. Se o CW não sustentar ~0,92 A, manter CW apenas em VA e dimensionar uma fonte digital separada: isso viola a fonte única e exige uma decisão de arquitetura posterior, não uma conexão improvisada.
2. Qualificar a interface ADC com 1,5 kΩ e clamps contra a carga comutada real. Se THD/assentamento falhar, rever isolação/proteção ou adotar driver apropriado; nenhum CI foi inserido sem essa evidência.
3. Qualificar partida/desligamento com osciloscópio, inclusive ADC, VCOM, ADC_BIAS, +5V e conector P10. Mute físico externo ou desconexão é obrigatório enquanto o pop não for resolvido; software isolado não resolve o DC transitório.
4. Implementar/testar SAI4/PLL/BDMA/SRAM4/cache/erros antes de liberar /RST e áudio. ESP32 permanece sem firmware.
5. Confirmar placa WeAct/ESP e permissividade quanto ao buck onboard. Não há validação física nem aprovação implícita do fabricante dos módulos.

Os entregáveis permitem revisar a conectividade e montar/testar subconjuntos progressivamente. A ausência de comprovação experimental, sozinha, é normal em um projeto documental; aqui o **veredito negativo decorre também de impedimentos objetivos de especificação e implementação ainda abertos**, não apenas de faltar uma medição final.

## Escopo dos símbolos de placa

H_STM32 e H_ESP32 representam placas prontas. O desenho mostra os headers usados, e não replica os componentes internos de cada placa. Os pinos não usados dos headers ficam sem jumper externo; não são uma alegação de NC do microcontrolador em seu circuito onboard. A pinagem integral dos CIs adicionados à perfboard (CS4272, TL072, CW) está representada; o esquema WeAct acompanha a entrega como referência de seus circuitos internos.

## Referências

Ver fontes/REFERENCIAS_REV49.md para URLs primárias e limites de acesso. Valores assumidos, resultados calculados e simulações estão separados em CALCULOS_REV49.json e simulacao/resultados.json. Backups integrais e hashes precedem as mudanças.
