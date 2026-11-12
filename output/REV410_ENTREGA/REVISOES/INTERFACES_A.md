# Verificação independente D — UART, Rev4.10A

2026-11-12. Escopo: UART full-duplex 115200 bit/s entre STM32H723/WeAct e ESP32 com USBs independentes. Não foram alterados CAD ou firmware por este verificador; não houve montagem, medição, SPICE ou compra. Os parâmetros abaixo provêm de documentos oficiais e os resultados numéricos são cálculos reproduzíveis.

**Proposta final recomendada: 1 × Texas Instruments ISO7721DR, sem sufixo F, encapsulamento D/SOIC-8.** Esta alternativa substitui a proposta de 2 × SN74LVC1G07DBVR porque mantém cada entrada/saída externa no domínio que a alimenta e interrompe o caminho DC do sinal através de barreira capacitiva. Elimina o divisor que reduz HIGH e a necessidade de extrapolar Ioff para fuga de saída alimentada. Não se afirma disponibilidade de estoque ou componente já adquirido. O componente é adicional necessário se se pretende deixar UART conectada nos oito estados; jumpers TX/RX abertos continuam sendo a contenção de ensaio sem esse componente.

**Este parecer não concede PASS A global.** A decisão do usuário de conservar CW7805 genérico permanece respeitada: identidade, pinagem e qualificação pendentes não são supridas pelo isolador. UART corrigida também não resolve sequenciamento/reset, proteção analógica ou mute do codec. Testar um modelo de estados não é provar conectividade do CAD: a auditoria das partições reais cabe ao coordenador.

## 1. Conexão da solução recomendada

Fonte primária [TI ISO772x, SLLSEP3G, maio/2024](https://www.ti.com/lit/ds/symlink/iso7721.pdf), p6, Fig5-4 e Tabela5-1. Usar **ISO7721DR**, nunca trocar pelo ISO7720 (ambos canais na mesma direção), ISO7721F (default LOW) ou pinagem DW16.

| Pino D8 | Função | Conectar |
|---|---|---|
| 1 | VCC1 | +3V3_STM |
| 2 | OUTA | RX STM, PD9 / P1.39 |
| 3 | INB | TX STM, PD8 / P1.40 |
| 4 | GND1 | GND comum |
| 5 | GND2 | GND comum |
| 6 | OUTB | RX ESP, GPIO16 quando livre na variante real |
| 7 | INA | TX ESP, GPIO17 quando livre na variante real |
| 8 | VCC2 | +3V3_ESP |

**Importante:** canal A vai do ESP para STM; canal B vai do STM para ESP. Adicionar 100 nF entre1–4 e entre8–5, junto ao CI (TI p31). Manter bleeder 10 kΩ ±1% em cada trilho3V3 para descarga, sem unir positivos. Pull-up47 kΩ local em INB→3V3_STM e INA→3V3_ESP é opção para definir idle durante reset do próprio transmissor. Não usar pulldown47 kΩ nos inputs desta solução: contrariaria o idle HIGH. As saídas são push-pull; remover pull-up4,7 kΩ e pulldown22 kΩ da proposta1G07. Pull-ups internos dos RX não são necessários para a função.

O projeto mantém GND comum através das demais conexões. Portanto **não existe isolamento galvânico do produto** nem imunidade garantida contra diferenças perigosas entre hosts. O benefício aqui é não haver condutor DC de TX alimentado para RX no domínio desligado. Uma ligação direta paralela TX/RX, adaptador USB-UART externo no pad, alimentação externa do GPIO ou erro de montagem anularia essa premissa. Os inputs do ISO possuem proteção ao próprio VCC; TI p25 nota3 alerta expressamente que um input fortemente acionado pode alimentar VCC flutuante por diodo interno. Por isso cada input recebe exclusivamente TX do próprio domínio e cada output vai exclusivamente ao RX do próprio domínio.

SOIC8 requer adaptador adequado para placa perfurada; não é componente DIP. Não se atribuem ao adaptador hipotético conformidade EMC ou certificação de isolamento. O datasheet p32 orienta placa de quatro camadas para obter baixo EMI; a montagem perfurada precisa de ensaio funcional/EMC e não herda essa característica.

## 2. Limites, margens e corrente

A janela **3,1–3,6 V nos dois trilhos3V3** é requisito assumido para os cálculos de UART, não medida nem consequência da existência de reguladores5V. A faixa3,1–3,4 V é subconjunto; usar3,6 V cobre o extremo superior usual de I/O e coincide com a faixa de tabelas STM. Para o ISO, p8 permite2,25–5,5 V; suas tabelas de3,3 V p15/p17 usam3,3 V±10% (2,97–3,63 V). A janela escolhida cabe nelas. A variante real ESP32, seu regulador e a disponibilidade de GPIO16/17 devem ser confirmados; PSRAM pode ocupar esses pinos.

TI p15 garante VOH≥VCCO−0,3 V a IOH=−2mA e VOL≤0,3 V a IOL=2mA. Entrada ISO exige VIH≥0,7VCCI e VIL≤0,3VCCI (p8), com histerese mínima0,1VCCI (p15). Cada VCCI é o mesmo trilho do TX ligado a esse input: **não comparar um TX de3,1 V contra limiar de um ISO alimentado por3,6 V remoto**. O único cruzamento entre trilhos ocorre internamente através da barreira.

ST DS13313 Rev5 p64 identifica PD8/PD9 como FT_h; p126 Tabela51 dá VIH0,7VDD/VIL0,3VDD (também há fronteira garantida por projeto0,47VDD+0,25 e0,4VDD−0,1, que não foi necessária). P129 Tabela52 fornece VOH≥VDD−0,4 V e VOL≤0,4 V a8mA,2,7≤VDD≤3,6 V. Espressif ESP32 Series v5.3 p52 Tabela5-3 informa VIH0,75VDD, VIL0,25VDD, VOH≥0,8VDD e VOL≤0,1VDD. **A tabela Espressif está intitulada3,3 V/25°C:** aplicar suas razões à janela3,1–3,6 V é avaliação de projeto, não qualificação garantida de todo PVT do módulo genérico. Documentação e ensaio da variante permanecem necessários.

| Caminho | Margem HIGH mínima calculada | Margem LOW mínima calculada |
|---|---:|---:|
| TX STM → input ISO local | 0,530 V | 0,530 V |
| TX ESP → input ISO local | 0,310 V | 0,620 V |
| output ISO → RX STM local | 0,630 V | 0,630 V |
| output ISO → RX ESP local | 0,475 V | 0,475 V |

Os16 pares de trilhos independentes(3,1;3,3;3,4;3,6 V) são enumerados no script. A carga input ISO é≤10µA nas condições especificadas, muito menor que os testes de drive dos MCUs. Um pull-up47k±1% opcional mais10µA carrega TX LOW em≤87,37µA a3,6 V. As fugas especificadas de RX são pequenas frente aos2mA da saída ISO; não usar essa sobra como autorização para LEDs ou cargas externas.

TI p15: ISO7721 com inputs DC HIGH consome no máximo2,1mA por domínio; DC LOW3,4mA; ambos canais a1Mbps com CL15pF,2,8mA. Reservar **4mA em cada3V3** cobre o máximo DC publicado3,4mA + bleeder10k±1%(0,36364mA a3,6V). Trata-se de orçamento conservador de projeto no regime documentado e deve somar-se ao consumo completo das placas/codec. A tabela não contém ponto115200, padrão arbitrário, brownout nem CL100pF; não inventar máximo universal interpolado. A reserva total corresponde a28,8mW para ambos lados a3,6V.

## 3. Velocidade e transições

Bit115200=8,680556µs. TI p17 fornece tpd≤18,5ns (0,21312% do bit), PWD≤5,9ns (0,06797%) e tr/tf≤3ns nas condições da Figura7-1, **CL15pF±20% incluindo fixture/sonda**, p22. Isso oferece grande margem de atraso nominal para115200, sem substituir o orçamento dos clocks e amostragemUART.

**CL100pF do estudo1G07 não herda esses timings.** Para manter evidência direta, colocar isolador perto dos headers e definir CL de saída nominal≤15pF incluindo RX, adaptador, cabos e instrumentos. O CIO STM de5pF e CIN ESP de2pF são valores típicos, não prova de capacitância máxima montada. Se o cabo exceder a condição15pF, verificar formas de onda, overshoot, atraso e erros a115200 antes de declarar validação. Não foi simulado um modelo ideal para substituir esse ensaio.

TI p8/p25: PU significaVCC≥2,25V, PDVCC≤1,7V; **1,7<VCC<2,25V é indeterminado**. Quando transmissorPD e receptorPU, default HIGH é especificado; p17 tDO≤0,3µs após VCCI cair abaixo1,7V(3,456% do bit). Não é garantia durante o trecho anterior da rampa. Quando próprio VCCO estáPD, a saída é **indeterminada**, não foi declarada alta impedância nem LOW. Como output e RX estão no mesmo trilho, a outra USB não fornece fonteDC pelo sinal. O transistor de saída local e cargas capacitivas ainda exigem verificação de transientes na montagem. Barreira não significa que toda corrente transitória capacitiva seja nula.

Não garantir recepção de frames durante energização/corte, nem usar CRC como proteção elétrica. A UART pode gerar erro/BREAK; depois dos trilhos estáveis deve descartar frames incompletos e retomar framing/CRC existente, sem reprojetar firmware nesta fase.

## 4. Oito estados e24 transições

S=USB STM; E=USB ESP; A=12V analógico. Tabela pressupõe trilhos em0V ou estáveis na janela adotada, GND comum e conexão ISO acima. Codec e CW não são aprovados por esta tabela.

| S E A | RX STM | RX ESP | Caminho DC remoto pelo sinal |
|---|---|---|---|
| 000 | Saída local indeterminada, receptoroff | Saída local indeterminada, receptoroff | Interrompido pela barreira |
| 100 | HIGH após tDO, porque ESPoff | Saída local indeterminada, receptoroff | Interrompido pela barreira |
| 010 | Saída local indeterminada, receptoroff | HIGH após tDO, porque STMoff | Interrompido pela barreira |
| 110 | Dados | Dados | Interrompido pela barreira |
| 001 | Igual000 | Igual000 | Interrompido pela barreira |
| 101 | Igual100 | Igual100 | Interrompido pela barreira |
| 011 | Igual010 | Igual010 | Interrompido pela barreira |
| 111 | Dados | Dados | Interrompido pela barreira |

O script enumera24 transições dirigidas de mudança de uma fonte. Isso confirma cobertura combinatória e a independência da UART da fonte analógica; não constitui simulação de rampas. Ao cortar S ou E, o lado ainda alimentado entra em default após atingir o limiarPD e o atraso publicado; no intervaloUVLO o estado lógico pode variar. Ao cortar A a UART não recebe fonte alternativa12V por este circuito. Inversão de ordem e cortes abruptos mantêm a separação estrutural dos positivos, condicionada à conectividade real conferida pelo coordenador. Verificar em bancada rampas lentas, assimétricas, cortes abruptos e restauração, incluindo erroUART e overshoot.

## 5. Estudo conservado:2×SN74LVC1G07DBVR

O candidato original foi de fato estudado, e não aprovado silenciosamente. TI SCES296AG(out/2025), p3 confirma1NC/2A/3GND/4Y/5VCC. VCC no **receptor**, A=TX remoto, Y=RX local, pull-upY4,7k local, pulldownY22kGND, pulldownA47kGND, bleeder3V3 10k e100nF. VCC no transmissor deixaria Y no domínio errado para parte do brownout e exige análise distinta; não misturar as duas conexões nos documentos. Este parecer supera a hipótese preliminar de alimentação pelo transmissor em ALIMENTACAO_PROPOSTA.md.

TI p5: VCC3–3,6V exige VIH2V e VIL0,8V. p6: VOL≤0,4V a16mA,VCC3V; II±5µA com **VI=5,5V ouGND,VCC0–5,5V**; Ioff±10µA com **VI ouVO=5,5V,VCC=0V**. Isso não é uma tabelaIoff em toda a rampa. Para0<VCC<1,65V não há garantia de lógica;2,0V também não aparece como intervalo válido deVIH/VIL. Não chamar essas regiões deHiZ ou LOW conhecido.

O divisor nominal22/(22+4,7)=0,823970 reduz HIGH. Com resistores±1%, pulldown mínimo21,78k e pull-up máximo4,747k, a razão mínima é0,82105 aproximadamente. A hipótese adicional de fuga de saídaY10µA com buffer alimentado, somada à pior fugaRX250nA, resulta em HIGH mínimo2,505V e margemESP mínima0,180V a3,1V. RC comCL100pF dá subida10–90≤0,860µs e cruzamento do limiarESP≤1,027µs, cerca11,83% do bit. Corrente máxima no pull-up com Y curto≤0,774mA.

**Limitação decisiva:** SCES296AG p6 não apresenta limite de fugaY em estadoHIGH/alta impedância com VCC válido(IOZ). Os10µA anteriores são orçamento a qualificar, **não especificação IOZ** e não podem ser inventados copiando Ioff. II é testado nos extremos descritos, não se deve transcrever como ensaiado explicitamente em todoVI0–5,5V. Se se assumem10µA no receptor desligado,22k±1% limitaY a0,2222V e bleeder10k±1% limita trilho a0,101V;5µA em47k±1% dáA≤0,23735V. São limites condicionais de rede, não demonstração de corrente zero nem garantia de railoff em todas as rampas. Também é necessário respeitar a razão de entrada10ns/V na tabela TI; RC das saídas para MCUs não qualifica o flancoA remoto.

Pull-up2,2k no lugar4,7k melhoraria margem/RC sem retirar a lacunaIOZ. Dois buffers push-pull corretamente alimentados poderiam retirar o divisor, mas exigem sua própria revisão de rampas/poweroff. ISO7721DR oferece evidência mais direta da separaçãoDC, estado defaultHIGH e montagemSOIC8. SN74AXC2T245 é alternativa válida já registrada pelo agenteA, mas UQFN10 torna a montagem em perfboard menos acessível. Não declarar essas alternativas adquiridas.

## 6. Evidências, resultados efetivos e pendências

Executado `python docs/hardware/rev4_10/test_interfaces_indep.py`: **12 testes passaram**. Incluem32 cantosLVC(hipóteseIOZ explícita),16 pares de trilhosISO e suas oito margens locais, orçamento de corrente/carga, timing apenas na carga publicada, oito estados e24 transições combinatórias, brownout indeterminado, verificação dos textos/fontes locais. A execução produz `FONTES_UART/calculos_interfaces.json`, com parâmetros, condições, páginas e SHA256 dos PDFs presentes. Esses testes verificam cálculo e coerência do modelo; CAD, disponibilidade, EMC, limites completos PVT do móduloESP e montagem ficam fora da prova.

Fontes preservadas em `REVISOES/FONTES_UART/`: ISO7721_TI.pdf e extração; SN74LVC1G07_TI_SCES296AG.pdf e extração; ESP32_Espressif_v5_3.pdf e extração. O PDFST oficial foi verificado pela ferramentaweb, mas as duas tentativas de download(st.com e st.com.cn) deram timeout; **não existe arquivoPDF localSTM inventado**. URL/revisão/páginas constam no JSON, com esta limitação. Links oficiais: [ISO7721 TI](https://www.ti.com/lit/ds/symlink/iso7721.pdf), [SN74LVC1G07 TI](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf), [STM32H723 ST](https://www.st.com/resource/en/datasheet/stm32h723vg.pdf), [ESP32 Espressif](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf).

Pendências: conferir implementação realCAD/BOM e mapeamento deheaders; garantir ausência de ligaçãoUART paralela; identificar varianteESP eGPIO16/17 livres; somar4mA por domínio ao orçamento3V3; obter/montarISO7721DR genuíno e adaptador; verificar capacitância/timing/overshoot/UVLO na montagem; manter qualificaçãoCW pendente e gateA global independente. Nenhuma dessas pendências foi convertida em medição ou aprovação por este parecer.
