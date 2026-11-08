from pathlib import Path
import json,csv,math,hashlib,os
ROOT=Path(__file__).resolve().parents[3];O=Path(os.environ.get('PEDALEIRA_REV49_OUT',str(ROOT/'output/rev4_9')))
m=json.loads((O/'circuito_rev4_9.json').read_text());P={a['ref']:a for a in m['components']};sim=json.loads((O/'simulacao/resultados.json').read_text());nom=sim['simulations']['nominal']
calc={'source_nom_V':12,'source_min_V':11.4,'source_max_V':12.6,'D1_forward_assumed_min_V':.3,'D1_forward_assumed_max_V':.9,'RAW_nom_V':11.3,'RAW_min_V':10.5,'RAW_max_V':12.3,'VREF_OP_nom_V':5.65,'VREF_OP_min_with_1pct_V':10.5*.495,'VREF_OP_max_with_1pct_V':12.3*.505,'ADC_BIAS_nom_V':2.4,'ADC_BIAS_min_with_0p1pct_V':4.75*(12000*.999)/(13000*1.001+12000*.999),'ADC_BIAS_max_with_0p1pct_V':5.25*(12000*1.001)/(13000*.999+12000*1.001),'VREF_OP_DC_Thevenin_ohm':1100,'VREF_OP_tau_s':1100*470e-6,'VREF_OP_divider_mA':11.3/4400*1000,'ADC_BIAS_DC_Thevenin_ohm':6240,'ADC_BIAS_tau_s':6240*100e-6,'ADC_nominal_input_peak_V':.5,'ADC_input_cm_headroom_lower_V':10.5*.495-.5-4,'DAC_gain':49900/100000,'ADC_differential_full_scale_min_Vpp':1.07*4.75,'ADC_differential_full_scale_nom_Vpp':1.13*5,'ADC_differential_full_scale_max_Vpp':1.19*5.25,'DAC_max_pin_diff_Vpp':1.01*5.25,'DAC_max_receiver_output_Vpeak':.499*1.01*5.25/2,'input_C1_R3_f3_Hz':1/(2*math.pi*1e6*100e-9),'ADC_coupling_cap_pair_uF_equiv':5,'ADC_coupling_f3_approx_Hz':1/(2*math.pi*(37000*200000/(237000)+3000)*5e-6),'ADC_diff_RF_f3_unloaded_Hz':1/(2*math.pi*3000*(680e-12+100e-12/2)),'inverter_feedback_pole_22p_Hz':1/(2*math.pi*10000*22e-12),'inverter_feedback_pole_470p_Hz':1/(2*math.pi*10000*470e-12),'inverter_feedback_pole_4n7_Hz':1/(2*math.pi*10000*4.7e-9),'ADC_series_fault_current_upper_A':12.3/(1500*.99),'5V_current_budget_A':.35+.5+.053+5/910+5/25000,'CW_conservative_Iq_A':.008,'sink_theta_C_per_W':2,'i2c_tr_200pF_ns':.8473*4700*200e-12*1e9}
calc['CW_dissipation_worst_W']=(12.3-5)*calc['5V_current_budget_A']+12.3*.008
calc['CW_Tj_proxy_at_40C_C']=40+calc['CW_dissipation_worst_W']*(5+1+2)
calc['PLL3_M']=2;calc['PLL3_N']=31;calc['PLL3_FRACN']=3746;calc['PLL3_Q']=8
calc['audio_kernel_candidate_Hz']=25e6/2*(31+3746/8192)/8
calc['kernel_error_ppm']=(calc['audio_kernel_candidate_Hz']/49.152e6-1)*1e6
(O/'CALCULOS_REV49.json').write_text(json.dumps(calc,ensure_ascii=False,indent=2))
refs='''# Referências primárias e uso

- S1: [Cirrus CS4272 DS593F2, outubro/2021](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf). pp.5–6 pinagem TSSOP; p.9 limites; pp.10/14 DAC/ADC; p.17 VCOM e correntes; pp.27–29 clocks/reset; pp.32–34 analógico; pp.38–44 registradores. Cópia local: CS4272_DS593F2.pdf.
- S2: [TI TL07xx SLOS080W, julho/2025](https://www.ti.com/lit/ds/symlink/tl072.pdf). Seções 5.3, 5.8 e 5.9. **TL072 clássico DIP**, não transferir limites do TL072H. O fornecedor e sufixo dos exemplares ainda precisam ser confirmados.
- S3: [ST STM32H723 DS13313](https://www.st.com/resource/en/datasheet/stm32h723vg.pdf). Tabela de AF e LQFP100; comparar à placa real.
- S4: [ST RM0468](https://www.st.com/resource/en/reference_manual/rm0468-stm32h723733-stm32h725735-and-stm32h730-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf). RCC, SAI4, BDMA/DMAMUX2, SRAM4/D3 e SYSCFG_PMCR. O navegador não abriu integralmente o arquivo de 20 MB; macros pertinentes foram conferidas também nos headers CMSIS/HAL locais. Não se afirma implementação ou configuração periférica validada em hardware.
- S5: [WeAct MiniSTM32H723, hardware oficial](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723/tree/master/Hardware). PDF V1.2 fornecido pelo usuário, cópia local. P1/P2 e circuito de 5 V→3V3 com XT3410AFMR e L1=2,2 µH.
- S6: [ST L78 DS0422 rev.38](https://www.st.com/resource/en/datasheet/l78.pdf). Pinagem usual, aplicação, carga mínima, faixa 7805 e térmica. **Referência conservadora de família; não identifica o CW7805 possuído.**
- S7: [Espressif ESP32 DevKitC V4](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html). Alimentações mutuamente exclusivas e GPIO16/17 condicionados ao módulo. Não comprova o DevKit genérico do usuário.
- S8: [TI SLOJ067, macromodelo TL072](https://www.ti.com/lit/zip/sloj067). Arquivo de 1989, caracterizado em ±15 V. Duas expressões POLY foram convertidas algebricamente para fontes B; original e adaptação incluídos. Não valida a partida em 0 V nem garante modelos/clones a +12 V.
- S9: [Vishay 1N5820/21/22](https://www.vishay.com/docs/88526/1n5820.pdf). Seleção da proteção de entrada 3 A/40 V.
- S10: [Nexperia BAT85](https://www.nexperia.com/product/BAT85). Clamps Schottky PTH; confirmar Vf, fuga e capacitância do fabricante comprado. Modelo da simulação é aproximado, não macromodelo qualificado de diodo.

Fontes consultadas em 2026-11-07. O TC1044 aparece apenas nos arquivos históricos da 4.8; não pertence à arquitetura 4.9. Não foram obtidas especificações confirmadas para o CW7805 do usuário.
'''
(O/'fontes/REFERENCIAS_REV49.md').write_text(refs)
# Exhaustive pin-level connection table, including real drawing sheets and split units.
l=json.loads((O/'diagram_layout.json').read_text());pos={(a['ref'],p):a['sheet'] for a in l['instances'] for p in a['pins']}
with (O/'CONEXOES_COMPLETAS_REV49.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Referência','Pino físico/funcional','Nome','Rede','Folha','Tipo'])
 for a in m['components']:
  for p,n in a['pins'].items():w.writerow([a['ref'],p,a['names'].get(p,''),n or 'NC',pos[(a['ref'],p)],a['types'].get(p,'passive')])
conn='''# Conexões revisão 4.9

A tabela CSV acompanhante cobre todos os terminais físicos. GND é a mesma rede em todas as folhas; VREF_OP, ADC_BIAS e VCOM são redes diferentes. As coordenadas/folhas efetivas vêm de diagram_layout.json; U1 e U3 são divididos em unidades, sem duplicar os CIs.

## STM32 ↔ CS4272

| Rede | GPIO / pino LQFP100 | Header WeAct V1.2 | AF | CS4272 TSSOP-28 | Direção |
|---|---|---|---|---|---|
| MCLK | PE0 / 97 | P1.4 | AF10 | 3 MCLK | STM→codec |
| LRCK | PE4 / 3 | P2.5 | AF8 | 4 LRCK | STM→codec |
| BCLK | PE5 / 4 | P2.6 | AF8 | 5 SCLK | STM→codec |
| DAC_DATA | PE6 / 5 | P2.7 | AF8 | 7 SDIN | STM→codec |
| ADC_DATA | PA0 / 22 | P2.17 | AF10 | 6 SDOUT | codec→STM |
| I2C_SCL | PB8 / 95 | P1.6 | AF4 OD | 11 SCL | STM→codec |
| I2C_SDA | PB9 / 96 | P1.5 | AF4 OD | 12 SDA | bidirecional |
| CODEC_RST | PD10 / 57 | P1.38 | saída GPIO | 14 /RST | STM→codec |

## STM32 ↔ ESP32

| Rede | STM32 / header | ESP32 pelo nome serigrafado | Direção |
|---|---|---|---|
| UART_TX | PD8 / P1.40, AF7 USART3_TX | GPIO16 RX2 | STM→ESP |
| UART_RX | PD9 / P1.39, AF7 USART3_RX | GPIO17 TX2 | ESP→STM |
| +5V | ramal CW7805 independente | VIN/5V confirmado | alimentação |
| GND | retorno comum | GND | referência |

UART 115200 8N1, níveis 3,3 V; não transmitir áudio por UART. Confirmar WROOM sem conflito PSRAM em 16/17. O ESP32 não é alimentado através do header de 5 V da STM32: os dois ramais saem do regulador. USB de programação com VBUS isolado; não unir fontes.

## Alimentação

| Rede | Origem | Destinos | Critério antes de instalar CIs |
|---|---|---|---|
| 12V_IN | J1 centro positivo | F1→D1 | 11,4..12,6 V |
| +RAW | D1 cátodo | TL072 pino 8, U5 IN, R22 | 10,5..12,3 V no envelope adotado |
| +5V | CW7805 OUT confirmado | U2 VA20, WeAct P1.2, ESP VIN | alvo 4,85..5,15 V; obrigatório 4,75..5,25 V |
| +3V3 | WeAct P2.2, conversor onboard | U2 VD9/VL10, pull-ups, GPIO | alvo 3,2..3,4 V; VD ≥3,1 V |
| VREF_OP | R22/R23/C38/C39 | bias guitarra, U3B+, receptor DAC | 0,495..0,505 × +RAW sem carga excessiva |
| ADC_BIAS | R27/R28/C40/C41 | R15/R16 e canal ADC B | ~0,48 × +5V; conferir diferença para VCOM ≤50 mV |
| VCOM | U2 pino 15 | C14/C15 e TP5 apenas | típico 0,48 × VA; sem carga externa |
| GND | J1 retorno | pinos 4 dos TL072 e todos os retornos | continuidade, sem interrupções |

A placa WeAct já contém um conversor chaveado com indutor. Não foi adicionado conversor nem indutor à perfboard. A proibição literal de qualquer indutor, incluindo o onboard, é incompatível com manter essa placa intacta.

## Quatro canais de amplificador

| Unidade | Entradas | Saída | Função |
|---|---|---|---|
| U1A | 3 HI_Z; 2 IN_BUF | 1 IN_BUF | buffer guitarra +1 |
| U1B | 5 DAC_P; 6 DAC_N | 7 DAC_BUF | receptor diferencial, ganho 0,499, bias VREF_OP |
| U3A | 3 IN_BUF; 2 FB_P | 1 DRV_P | driver positivo +1 |
| U3B | 5 VREF_OP; 6 FB_N | 7 DRV_N | inversor −1 por R24/R19 |

Ambos DIP-8: 8=+RAW, 4=GND; nenhum canal está sem uso.

## Conectores e comandos

J1: 1 positivo da fonte 12 V, 2 GND. J2: 1 TIP guitarra, 2 sleeve/GND. J3: 1 TIP saída AC, 2 sleeve/GND. J4: 1 distribuição +5V, 2 GND, **não é porta USB**. Os números funcionais dos jacks devem ser identificados por continuidade no componente comprado.

SW1..4: C comum, 1 para GND, 2 NC. PC0/P2.11, PC1/P2.12, PC2_C/P2.13, PC3_C/P2.14. Confirmar fechamento dos switches analógicos internos dos pads _C. LEDs em PE7/P2.30, PE8/P2.31, PE9/P2.32, PE15/P2.38; resistor 330 Ω e cátodo no GND. SW4 é mute.

## Pinagem integral dos CIs e módulos

'''
for ref in ['U2','U1','U3','U5','H_STM32','H_ESP32']:
 a=P[ref];conn+='\n### '+ref+' — '+a['value']+'\n\n| Pino | Nome | Rede | Folha |\n|---|---|---|---|\n'
 for p,n in a['pins'].items():conn+=f'| {p} | {a["names"].get(p,"")} | {n or "NC"} | {pos[(ref,p)]} |\n'
(O/'CONEXOES_REV49.md').write_text(conn)
# Non-electrical purchasing items are deliberately not false CAD nets.
with (O/'BOM_COMPLEMENTAR_REV49.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Referência','Quantidade','Componente','Especificações mínimas','Status'])
 for r,q,v,sp in [('PS1',1,'Fonte externa isolada','12 V regulados ±5%, ≥1,5 A; centro positivo'),('HS1',1,'Dissipador CW7805','≤2 °C/W, interface térmica e fixação; conferir TAB/GND'),('SO1_SO3',2,'Soquetes DIP-8','Contato torneado para U1/U3'),('FH1',1,'Porta-fusível','Compatível com F1 T1,25 A'),('PB1',1,'Placa perfurada de ilhas','2,54 mm; separar áreas de áudio e digital'),('JMP_CAB',1,'Jumpers, fios e fixadores','Bitola para ~1 A em alimentação; conexões de clock curtas')]:w.writerow([r,q,v,sp,'necessário adquirir / conferir estoque'])
# Findings and quantitative stage report.
audit=f'''# AUDITORIA REV49

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
| VREF_OP | 5,65 V | {calc['VREF_OP_min_with_1pct_V']:.4f}..{calc['VREF_OP_max_with_1pct_V']:.4f} V com 1% no divisor |
| VREF_OP Zdc | 1,1 kΩ | Capacitor reduz impedância AC; não é terra de potência |
| Corrente do divisor OP | {calc['VREF_OP_divider_mA']:.3f} mA | 2,39..2,80 mA aproximadamente |
| τ OP | 0,517 s | ±20% do eletrolítico domina; esperar ≥5 s |
| ADC_BIAS | 2,4 V | {calc['ADC_BIAS_min_with_0p1pct_V']:.4f}..{calc['ADC_BIAS_max_with_0p1pct_V']:.4f} V, VA 4,75..5,25 V |
| Zdc ADC_BIAS / τ | 6,24 kΩ / 0,624 s | 0,48×VA; confirmar diferença para VCOM ≤50 mV |
| VCOM | típico 0,48×VA | Datasheet não dá min/max; não inventar faixa garantida |

A 20 Hz, C38 tem |Z|≈16,9 Ω. Uma corrente AC de bias de 0,5 V/1 MΩ=0,5 µA daria ~8,5 µV na referência; cargas reais de retorno e a fonte precisam ser medidas. Os divisores não fornecem corrente de alimentação. A simulação inclui impedância de saída de VCOM de 25 kΩ e a nova rede ADC não a carrega.

## Estágio da guitarra e headroom

C1=100 nF filme, R3=1 MΩ, R26=1 kΩ: corte aproximado {calc['input_C1_R3_f3_Hz']:.3f} Hz, ganho +1, impedância nominal de entrada próxima a 1 MΩ na banda. D6/D13 e D14/D7 formam dois diodos em série por sentido contra VREF_OP. Um único 1N4148 por sentido mostrou compressão indesejada perto de 0,5 V no modelo e foi descartado. Os clamps novos reduzem esse efeito nominal, sem serem proteção contra surto de rede ou fonte conectada ao jack.

Com áudio ≤0,5 Vpk e divisor a 1%, a margem de entrada para V−+4 V é ≥{calc['ADC_input_cm_headroom_lower_V']:.4f} V antes de offsets. Admitindo 13 mV de offset e 7 nA×1 MΩ=7 mV de erro quente, restam cerca de 0,677 V. Os números são relativos ao limite inferior da família TI, não uma garantia de qualquer TL072 genérico. Limites de swing de ±15 V não foram extrapolados como garantia a 12 V. Para avaliar headroom, foi reservada heuristicamente margem de 3 V nas saídas e 4 V nas entradas; a confirmação é em bancada.

Guitarras ativas ou captadores fortes podem exceder 0,5 Vpk. Reduzir nível no instrumento/usar atenuador de alta impedância antes dos testes; não prometer ausência de clipping para qualquer instrumento. Ruído: resistor 1 MΩ isolado tem ~129 nV/√Hz a 300 K, ou ~18 µVrms em 20 kHz; o captador em paralelo muda o resultado. TL072 clássico não assegura o piso de ruído de 114 dB do codec. 24 bits é o formato, não resolução efetiva garantida.

## ADC diferencial e filtros

U3A copia IN_BUF; U3B inverte a parte AC em torno de VREF_OP, com R24/R19=10 kΩ/10 kΩ (0,1%). U3A usa R17=10 kΩ e C18 em paralelo no feedback; C18 não é, sozinho, o filtro passa-baixas do sinal. C19 em paralelo com R19 limita o ganho inversor em HF. C2/C16=10 µF bipolares removem o DC ~5,65 V e as entradas são recolocadas em ADC_BIAS por 100 kΩ. Não ligar o bias OP diretamente ao ADC.

A figura 12 da Cirrus usa uma topologia de feedback depois de 91 Ω, 634 Ω e 470 pF. **A 4.9 não é uma cópia dessa figura**: a proteção de transientes e a alimentação simples levaram a R18/R20=1,5 kΩ, clamps e rede RC própria. O custo é impedância maior que a recomendada, exigindo comprovação de THD/estabilidade com o modulador real. O modelo usa apenas 37 kΩ diferenciais, não reproduz a amostragem a 6,144 MHz. Logo, não se declara essa interface qualificada somente pela AC.

O par de capacitores de acoplamento equivale a 5 µF diferenciais. Com entrada mínima 37 kΩ, dois biases de 100 kΩ e 3 kΩ em série, fc≈{calc['ADC_coupling_f3_approx_Hz']:.3f} Hz. O divisor resistivo carregado reduz ganho de 2 para cerca de 1,82. O filtro usa C20=680 pF entre pinos e C35/C36=100 pF para GND: Cdiff equivalente=730 pF, Rdiff=3 kΩ, fc sem carga≈{calc['ADC_diff_RF_f3_unloaded_Hz']:.1f} Hz. A simulação contém carga e diodos; não substituir esse cálculo aproximado pelo resultado completo.

Com R19=10 kΩ: 22 pF→723,4 kHz; 470 pF→33,86 kHz; 4,7 nF→3,386 kHz. A escolha é específica deste circuito; não é troca automática dos valores da figura 12. Resultados comparativos vêm abaixo. Os 1,5 kΩ também limitam a corrente extrema calculada para 12,3 V/1,485 kΩ≈8,28 mA, abaixo do limite absoluto de corrente de 10 mA. **Isso não garante sozinho o limite de tensão nos pinos**; a Vf real dos BAT85 e as sequências de rails precisam ser verificadas.

Full scale diferencial ADC: nominal 5,65 Vpp, mínimo conservador 5,0825 Vpp e máximo 6,2475 Vpp conforme tolerância de VA e escala do datasheet. Para guitarra de 0,5 Vpk, a simulação entrega ~1,82 Vpp diferenciais, cerca de −9,8 dBFS nominal: há headroom e perda de aproveitamento da faixa, documentada. Não recuperar essa perda por ganho digital esperando recuperar SNR analógico.

## DAC, saída, offset e carga

R1/R7=100 kΩ; R2/R8=49,9 kΩ, razões casadas 0,1%. A expressão DC/AC ideal é Vout=VREF_OP+0,499×(AOUTA+−AOUTA−). C10/C11 bipolares isolam o DC do codec. Cada saída DAC vê carga muito acima de 3 kΩ. No pior full scale de 1,01×5,25=5,3025 Vpp, o receptor varia ±1,324 V. Com +RAW mínimo e tolerância de referência, excursões ficam a aproximadamente 3,87 V dos trilhos: há margem de projeto sobre a reserva heurística de 3 V, sem alegar swing garantido a 12 V.

CMRR depende do casamento das razões, carga e layout; não prometer CMRR ideal. Redes de precisão ou resistores medidos são preferíveis. U1B não aciona fones; a carga prevista é ≥100 kΩ. R4/R5=220 Ω, C4/C6=2,2 nF. Dois polos interagem; sem carga H(s)=1/[R4·R5·C4·C6·s²+(R4·C4+R4·C6+R5·C6)·s+1]. Saída de baixa frequência tem impedância próxima a 440 Ω, mais 1/(jωC5).

C5 eletrolítico 10 µF com + no LP2, R6=1 MΩ e carga 100 kΩ: Rdescarga≈90,9 kΩ, fc≈0,175 Hz, τ≈0,91 s. DC no jack deve ficar <10 mV após estabilização. A partida/desligamento pode produzir volts de transiente na saída AC; firmware mute não elimina toda variação da referência. Manter o equipamento externo mutado/desconectado nesses eventos. Se silêncio automático for requisito, é necessária uma solução física de mute/disconexão ainda não implementada.

## CW7805, distribuição e térmica

O CW não foi convertido silenciosamente em L7805. Pinagem desenhada é a usual TO-220 vista frontal 1 IN / 2 GND e TAB / 3 OUT, **condicional à identificação**. Confirmar também se o TAB é GND antes de aparafusar ao chassi. A família ST serve de referência: saída conservadora 4,75..5,25 V, carga mínima 5 mA; dropout típico ~2 V não é um máximo garantido do CW desconhecido. A +RAW mínima 10,5 V oferece 5,25 V de folga sobre a saída máxima, mas isso não substitui datasheet/ensaio do exemplar.

C21=330 nF e C22=100 nF locais; C37=1000 µF é reserva e exige ensaio de inrush. R21=910 Ω mantém 5,49 mA e dissipa 27,5 mW nominal. D8, ânodo OUT/cátodo IN, protege descarga reversa. F1 limita falhas de entrada, não garante sobrecorrente segura de cada CI.

Um único CW alimenta **o mesmo +5V elétrico** para VA e ambas as placas; os ramais são separados fisicamente em estrela. Não se vende esse arranjo como dois reguladores independentes. Não há +5V_USB externo unido ao barramento. Reserva de corrente: STM32+codec digital+GPIO 350 mA, ESP 500 mA de orçamento de pico, VA 53 mA, bleeder e divisor ADC: total {calc['5V_current_budget_A']:.4f} A. Esses são orçamentos, não medições nem consumo garantido dos módulos.

P≈(12,3−5)·{calc['5V_current_budget_A']:.4f}+12,3·8 mA = {calc['CW_dissipation_worst_W']:.3f} W. Sem dissipador, 50 °C/W da família daria elevação >300 °C: inviável. Com θJC proxy=5, θCS=1 e dissipador ≤2 °C/W, Tj estimado a 40 °C ambiente é {calc['CW_Tj_proxy_at_40C_C']:.1f} °C. **Parâmetros proxy não identificam o CW.** Validar 0,6 A contínuos/0,92 A de pico, carga transitória, temperatura e ausência de oscilação; revisar se a placa real exigir mais. Uma fonte 12 V ≥1,5 A e dissipador grande são componentes adicionais necessários. O custo térmico é uma limitação explícita da opção sem novo CI chaveado.

+3V3 vem do header P2.2 WeAct, cuja origem foi conferida no esquema V1.2: buck XT3410 e L1 de 2,2 µH. Deve fornecer reserva para ID do codec (máx.28 mA) e GPIO/LEDs, além da placa. O documento prova a existência do circuito, não a corrente livre/qualidade do exemplar. Medir 3,2..3,4 V sob DSP/Wi-Fi e nunca VD<3,1 V. Se “sem indutores” incluir o conversor interno dessa placa, o requisito é incompatível com mantê-la intacta; não foi afirmado atendimento literal.

## Clock, interfaces e firmware

PLL1 também foi auditada: a configuração anterior M5/N220/P2 escondia VCO=1100 MHz atrás de uma saída CPU=550 MHz. O limite do H723 é 836 MHz (S3 tabela 39). A correção aplicada M5/N110/P1/Q2/R2 mantém CPU550, Q275 e R275 MHz, com VCO550 MHz dentro da faixa. Não houve medição do clock da placa.

Pinagem e sentido completos em CONEXOES_REV49.md/CSV. I2C 100 kHz, R11/R12=4,7 kΩ: tr≈796 ns com 200 pF, abaixo de 1 µs; não afirmar 400 kHz nessa capacitância. VL=3,3 V mantém interfaces digitais compatíveis. XTI=GND e XTO=NC estão corretos para clock externo. Não usar MUTEC como GPIO de 3,3 V: pode subir a VA.

MCLK=12,288 MHz=256Fs, BCLK=3,072 MHz=64Fs, Fs=48 kHz, I2S dois slots de 32 bits/24 válidos. PLL3 candidato com HSE25 MHz: M=2, N=31, FRACN=3746, Q=8 (entrada PLL=12,5 MHz) fornece {calc['audio_kernel_candidate_Hz']:.6f} Hz, erro aritmético {calc['kernel_error_ppm']:.6f} ppm. É alvo calculado para kernel ~49,152 MHz, **não configuração de SAI aplicada/testada**. Validar divisor MCLK/OSR/frame no RM0468 e escopo; erro do cristal soma-se ao arredondamento.

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
'''
for tag in ['nominal','min_supply','9V_rejected','cf470p','cf4n7']:
 r=sim['simulations'][tag];audit+=f"| {tag} | {r['ADC_1000Hz_dB']:.4f} | {r['ADC_20000Hz_dB']:.4f} | {r['OUT_1000Hz_dB']:.4f} |\n"
audit+=f'''
Nominal: ADC 20 Hz={nom['ADC_20Hz_dB']:.4f} dB e 6,144 MHz={nom['ADC_6.144e+06Hz_dB']:.2f} dB. Saída 20 kHz={nom['OUT_20000Hz_dB']:.4f} dB, relativa a 1 kHz cai ~0,104 dB. Não interpretar essa rejeição RF como THD validada.

No transiente de sinal, IN_BUF≈{nom['IN_BUF_min']:.3f}..{nom['IN_BUF_max']:.3f} V; ADC+≈{nom['AINA_P_min']:.3f}..{nom['AINA_P_max']:.3f} V; ADC−≈{nom['AINA_N_min']:.3f}..{nom['AINA_N_max']:.3f} V; receptor DAC≈{nom['DAC_BUF_min']:.3f}..{nom['DAC_BUF_max']:.3f} V; P10≈{nom['JACK_OUT_min']:.3f}..{nom['JACK_OUT_max']:.3f} V. Estímulos: guitarra 0,5 Vpk/1 kHz e DAC diferencial 4,8 Vpp/1 kHz, carga 100 kΩ.

Envelope de partida/desligamento de um polo: ADC+ mínimo {sim['startup']['AINA_P']['min']:.3f} V, máximo {sim['startup']['AINA_P']['max']:.3f} V; ADC− mínimo {sim['startup']['AINA_N']['min']:.3f} V. A proteção aproximada ficou dentro de −0,3 V no modelo, mas diodos reais/rails podem alterar isso. A saída P10 teve mínimo {sim['startup']['JACK_OUT']['min']:.3f} V e máximo {sim['startup']['JACK_OUT']['max']:.3f} V: **há pop importante previsto**, não aprovado para conexão durante energização. Modelo não é garantia de sequência ou proteção em falha.

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
'''
(O/'AUDITORIA_REV49.md').write_text(audit)
print('Audit, calculations, pin tables and supplementary BOM generated.')
