# Parecer independente D — CAD real, checkpoint 4.10A

2026-11-12. **Veredito do conjunto: BLOCKED A; B/C não liberadas por este parecer.** As correções de separação das fontes e UART foram efetivamente implementadas e passam na verificação documental de conectividade. Os riscos remanescentes com codec instalado não são resolvidos pelo ERC nem pelo jumperJ5.

O usuário escolheu conservar CW7805 genérico de 3 pinos e registrar sua qualificação pendente. Essa decisão foi respeitada. A origem em aparelho alimentado pela redeAC e a expectativa de saída5V não identificam fabricante, pinagem, TAB, estabilidade ou limites do exemplar. Não foi proposto trocar o componente sem autorização nem atribuídas garantias de outro fabricante. A pendência continua no gate, sem repetir pedido de identificação ao usuário.

## Evidência atual e testes efetivamente executados

Foi lido o modelo completo de114 componentes das oito folhas, `prepare_model.py`, o layout de todos os terminais, os nove arquivosKiCad(root+8 folhas), BOM e netlist XML reexportada **deste CAD**. As partições foram comparadas por conjuntos completos de pares(referência,pino), não só pelo texto do nome das redes. Prefixos locais de folha do KiCad não foram confundidos com divergência elétrica.

Comandos reproduzíveis:

```sh
python docs/hardware/rev4_10/auditar_cad_A.py --export
python docs/hardware/rev4_10/test_interfaces_indep.py
```

`auditar_cad_A.py --export` usa KiCad10.0.8 real em `/home/rodrigues/.cache/pedaleira-tools/root/usr/bin/kicad-cli`, `LD_LIBRARY_PATH` correspondente, `sch export netlist --format kicadxml` e `sch erc --format json --severity-all`. Só grava evidências em `REVISOES/CAD_D_TEMP/`; não modifica CAD. O teste tem12 verificações e **12 passaram**. `test_interfaces_indep.py` também executou12 testes e **12 passaram**. Passar esses24 testes não é aprovação física nem PASS A global; um teste específico confirma que riscos conhecidos continuam presentes e listados.

Resultados da exportação final independente:

| Evidência | Resultado efetivo |
|---|---|
| ComponentesXML × modelo × BOM |114 referências e valores correspondem |
| Partições elétricasXML × modelo |61 conjuntos idênticos,277 terminais conectados |
| Terminais de layout × modelo |Todos os terminais, incluindoNC, representados nas8 folhas |
| ERC final independente |0 violações; `ignored_checks=[]`; nenhuma exclusão aplicada |
| Footprint realU6 |`Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` ligado noXML |
| Demais footprints |113 vazios; package notes existem, mas não são footprints verificáveis |
| Inspeção visual |PDF8 folhas renderizado viaPoppler e inspecionado; F8 final relida após ajusteR31 |

O primeiro ERC independente encontrou1warning `footprint_link_issues` por ausência de biblioteca Package_SO. O coordenador corrigiu instalando localmente o footprint e `fp-lib-table`, sem excluir a regra; a reexportação acima deu0. Atribuir footprintU6 não valida todos os 113 restantes, PCB/adaptador ou montagem. O footprint local tem pads1..4 no lado esquerdo de cima para baixo e5..8 no direito de baixo para cima, pitch1,27mm e corpo3,9×4,9mm, coerente comISO7721D; a padagem foi conferida, não houve medição física.

O log final ainda registra ausência de `/usr/share/kicad/schemas/api.v1.schema.json` na instalação extraída. KiCad produziu netlist/JSONERC e retornou sucesso; isso é limitação do ambiente/API, **não** prova de violação elétrica ou motivo para apagar o log. A evidência integral está em `CAD_D_TEMP/ERC.log`, `export.log`, `ERC_fresh.json`, `netlist_fresh.xml`, `test_cad_D.log` e `resultado_cad_D.json`. O último contém hashesSHA256 do modelo, layout, BOM e todos os esquemáticos revisados.

## Correções que passaram no CAD real

1. **PositivosUSB separados doCW:** H_STM32/P1.2 e H_ESP32/VIN sãoNC no modelo e em redes `unconnected-*` noXML; não há fio externo ligando os headers5V a CW ou um ao outro. As USBs pertencem às próprias placas; não há alegação de que o esquemático represente todos os circuitos internos dos módulos.
2. **DomínioCW:** U5/3,C22,R21,C37,TP2 e J4/1 pertencem a`+5V_CW`; U5/1 permanece`+RAW`. D8 vai deOUT_CW para RAW, sem caminhoUSB. J4 é carga de teste antes de J5, nunca entradaUSB. Nenhuma pinagem física CW foi qualificada pela conferência de que o desenho mantém a hipótese herdada1IN/2GND/3OUT.
3. **SeccionamentoJ5:** pino1=`+5V_CW`,pino2=`+5VA`, símbolo aberto sem shunt e metadados mandando manteraberto até qualificação. Não é curto interno noXML. Não é intertravamento automático nem proteção contra sobrevoltagem de CW quando fechado.
4. **Codec:** U2/9VD e10VL em`+3V3_STM`;20VA em`+5VA`;8DGND e21AGND emGND. Pull-upsI2C R11/R12 em STM. Não háVD/VL no ESP.
5. **UART:** U6 éISO7721DR semF,1VCC1=STM/2OUTA→RXSTM/3INB←TXSTM/4GND/5GND/6OUTB→RXESP/7INA←TXESP/8VCC2=ESP. RXSTM tem sóU6/2 eheaderP1.39; RXESP sóU6/6 eRX2. TXs incluem somenteheader/input ISO/pull-up47k local. Não existeUART direta paralela. GND1/GND2 ligados aoGND do sistema; não se afirmaisolamento galvânico do produto.
6. **UART física local:** C42/C43=100nF em seus próprios3V3/GND; R29/R30=10k bleeders;R31/R32=47k pull-ups locais dosTX. Ausência do divisoropen-drain4,7k/22k é correta. Metadados exigemCLRX≤15pF e avisam lógica de brownout indeterminada. Receptor sem alimentação tem saída local **indeterminada**, não HiZ garantida. Odefault HIGH só vale quando o próprio lado receptor estáPU e o transmissorPD, após o atraso publicado; ver `INTERFACES_A.md`.

USART3 usa **PD8/TX(chip55,headerP1.40), PD9/RX(chip56,headerP1.39),AF7**. A mençãoPA9/PA10 em versão preliminar do parecerUART foi corrigida antes desta entrega. ST DS13313Rev5 p64Tabela7 classificaambosFT_h; p79Tabela8 trazAF7USART3. As margensUART atuais usamGPIOlocal; a fugaFT_h adotada é250nA. Os limitesESP permanecem condicionados à variante e às condições da tabelaEspressif; não se inventou tolerância power-off de GPIO.

## Inspeção das oito folhas

| Folha | Conferência efetuada | Limitação relevante |
|---|---|---|
|1|12VIN/F1/D1/RAW;CW/retornoD8;J5 aberto;VREF_OP e ADC_BIAS distintos|CWcontinua genérico nãoqualificado |
|2|TL072 sinais/pinos;C2/C16;clampsBAT85;AIN/ADC_BIAS|Clamps/off/transientes não aprovados |
|3|CS4272pinagem lógica,VD/VL STM,VAseccionado,GND,XTI/XTO,VCOM/FILT|RSTnão impõecondição física aVA/clocks |
|4|DACreceptor/ganhoinalterado;C5LP2→saída|Não existe mute físico nesta fase |
|5|HeadersUSBNC,3V3 das placas,USART3/ESP,I2C/resetpulldown,J4CWteste|R13não vence PD10ativamenteHIGH |
|6|Chaves/LEDs e GPIO do modelo preservados|ConfirmarPC2_C/PC3_C evarianteESP continua requisito |
|7|BypassVA/VD/VL;TL072pinos8RAW/4GND|Bypass não desconecta sinais durantequeda |
|8|ISO7721Dmapa,pull-upslocais,bleeders,bypass,CL eGNDcomum|Capacitância/overshoot/EMC físicos não medidos |

## Bloqueios restantes e contenção correta

| ID | Natureza | Evidência e impacto | Ação necessária |
|---|---|---|---|
|DA01|Qualificaçãoexterna/ensaiofuturo|CWgenérico3pinos mantido; rótulo5V não demonstra pinagem/TAB,regulação,estabilidade/térmica|Manter pendência explícita. Antes de energizarCW, estabelecer conexão por evidência/qualificação; não fecharJ5neminstalarcodec com essa premissa nãoqualificada |
|DA02|Correção deprojeto não implementada|PD10 ativo HIGH está diretamente em CODEC_RST;R13=10k só pull-down passivo|Reset físico condicionado aos trilhos/clocks ou contenção com codec fisicamenteausente. J6manual isolandoPD10 permitiriaRCTlow, mas sozinho não resolveAIN/off nem garante resposta automática à perdaVA |
|DA03|Correção/contenção não implementada com codec instalado|RAW alimentaU3;C2/C16 transferem transientes aAIN;D9/D11 vão aVA;J5 aberto não desconectaAIN nemVD/VL|Mantercodec REMOVIDO de todas as28conexões nos ensaiosiniciais; semjackentrada/saída externos. ProjetoADC/mute dafaseB continua pendente, sem apresentar reset como isolador analógico |
|DA04|Orçamento/variantefísica pendentes|3V3 STM fornececodecVD/VL eUART; disponibilidade livre do buck e modeloESP genérico não comprovados|Confirmar revisãoWeAct/ESP e reserva de corrente/capacitância; somar reservaUART4mA por domínio. Sem valores máximos inventados da placa |

**J5 aberto + codec instalado não é contenção suficiente.** A placa pode continuar recebendoVD/VL, clocks, I2C e pulsos analógicos. Codec deve estar ausente fisicamente; uma nota"resetLOW"não equivale a essa remoção. O TSSOP-28 exige soquete/adaptador removível ou deixarU2não montado, sem pontes no adaptador. Não se alega que foi fisicamente removido nesta missão, que exclui montagem/bancada. A contenção é especificação para procedimento futuro.

**J5 aberto + codec REMOVIDO** permite definir ensaios futuros separados deSTM/ESP/UART semCW12V, jack deentrada e saída externos. Nesse modo os riscos de CW e interfaces analógicas não alcançam ocodec ausente. Se12 V/CW for energizado para qualificar sua própria saída/carga artificial, a falta deidentidade/pinagem do próprioCW deve ser resolvida nesse procedimento antes de ligá-lo; J5nãoqualificaessa peça nemprotegeTL072 de erros deconexão. Não basta energizar12V através deU5 de pinagemsuposta e declararcontenção.

## Decisão de gate e possibilidade de avançar

Há **PASS das verificações topológicas e da correçãoUART documentada**, com a reserva de que cálculo não émedição. Isso é uma evidência específica do checkpoint, não o checkpointAcompleto. O modelo continua acertadamente com`release_status=BLOCKED`.

É possível preparar um subconjunto deensaio restrito, com J5 aberto/U2 ausente e apenasUSBs, e registrar a contenção. **Não aceito converter esse PASS de subconjunto em PASS A global para liberarB automaticamente:** a missão exigePASS Aantes de B e os bloqueios do conjunto descritos acima permanecem. A condição de ensaio não transforma o circuito interligado em seguro em seus oito estados; não houve execução física dessa condição. Desenvolvimento deB pode ser uma decisão explícita futura deescopo do coordenador/usuário com riscoisolado e semenergização, mas não foi autorizado por um falsoPASS deste parecer.

Resultado independente: **A do conjunto permaneceBLOCKED; entregaA é parcialmente validada e útil; B/C não iniciadas por este auditor.** Não houve novo componente analógico, alteração de firmware, simulaçãoideal apresentada como física ou aprovação parafuncionamento completo.
