from pathlib import Path
import json,csv,shutil,hashlib,platform
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'output/auditoria_rev49';V=D/'VALIDACAO';S=D/'SIMULACOES'
r=pd.read_csv(S/'matriz_transientes.csv');ac=json.loads((S/'ac_resultados.json').read_text());p=json.loads((V/'alimentacao_resultados.json').read_text());k=json.loads((V/'analogico_calculos.json').read_text());startup=json.loads((S/'partida_resultados.json').read_text());findings=[
('A01','ALTO','F5, firmware: SAI4/PLL3/BDMA ausentes; gate0','Sistema não processa áudio físico. Confirmado por fontes/.ioc, não falha de ligação.','PENDENTE: implementar transporte com buffers/cache/erros e validar clocks antes de /RST.'),
('A02','ALTO','F2,D9–D12 BAT85','Vf máximo0,32V a1mA/25°C já excede janela absoluta ±0,3V do ADC. R1,5k limita corrente, não prova tensão segura.','PENDENTE: proteção/ordem de trilhos deve ser qualificada ou redesenhada. Dano efetivo NÃO CONFIRMADO.'),
('A03','ALTO','F4,C5/J3 e F1,VREF_OP','Sem mute físico, variação DC atravessa C5. Envelope simplificado novo chega a−6,071/+2,980V; número não é previsão garantida do TL072.','PENDENTE: manter saída desconectada em partida/corte; dimensionar mute físico e testar antes de conectar equipamento externo.'),
('A04','ALTO','F1,U5 CW7805 sem identidade','Pinagem, corrente, estabilidade e térmica do componente real não documentadas. Aproximar peloST não qualificaCW.','PENDENTE: identificar peça e testar com carga artificial/semcodec. Não presumir dano nem substituirCI automaticamente.'),
('F01','ALTO','Bsp.cpp/main.cpp: UART115200','Polling10ms semFIFO/IRQ perdia bytes a86,8µs/byte.','CORRIGIDO: ISR+ring512eventos, erros/overflow contados; testeshost e compilaçãoARM. Medir ISR real pendente.'),
('F02','ALTO','InterMcuUart.cpp: slotúnico','Pacote posterior sobrescrevia o anterior antes do consumo.','CORRIGIDO: fila8, pausa de consumo quando cheia e descarte contado. Capacidade finita, semRTS.'),
('F03','ALTO','main.cpp:SW4/UARTmute','Leitura física apagava mute remoto a cada10ms quando transporte habilitado.','CORRIGIDO: estado remoto persistente, OR comSW4/gate, atualização coerente DSP/codec.'),
('F04','ALTO','Cs4272.cpp: erroI2C após /RST','Erro podia retornar deixando codec fora de reset e perder janelaCPEN.','CORRIGIDO: falha de escrita e errofatal reassumemRSTLOW; mocktimeout/NACK executado.'),
('F05','ALTO','Bsp.cpp TIMINGR0x10909CEC','A137,5MHz, contagensLOW/HIGH dão3,447/2,284µs e~174,5kHz antes filtros, incompatíveis comCS4272máx100kHz/LOW4,7/HIGH4µs(p21).','CORRIGIDO: ver cálculo/documentação e testes no apêndice embarcado; captura de barramento ainda necessária.'),
('D01','MÉDIO','F1/cálculoRAWmáximo','Limite12,3V assumia Vf mínimo0,3V sem garantia.','CORRIGIDO no cálculo: usar12,6V; Pproxy7,236W, Tjproxy97,9°C a40°C comθtotal8°C/W.'),
('D02','MÉDIO','BOM R1/R2/R7/R8/R19','package1% contradiz requisito0,1%.','CORRIGIDO em BOM_REV49_ERRATA.csv/JSONerrata, semalterar redes/valores.'),
('D03','MÉDIO','BOM U5/U3','IdentidadeST L7805CV atribuída aoCW e sufixoTL072CP presumido.','CORRIGIDO nos metadadoserrata; identificação física continua pendente.'),
('D04','BAIXO','BOM R8','Função dizia ganho1; rede ePDF conferem0,499.','CORRIGIDO na errata, não trocar valores.'),
('D05','BAIXO','BOM BAT85','DO35 declarado; Nexperia consultado éDO34/SOD68.','CORRIGIDO como encapsulamento condicionado ao fabricante comprado.'),
('F06','MÉDIO','Protocolo/skill/testeCRC','Vetores incorretos e teste sóchecava tipo inteiro.','CORRIGIDO: vetores6B/D0/9C e comparação fixa; parserC++ real exercitado.'),
('P01','MÉDIO','STATE_REPORT/ACK/despacho','Tamanhos5/1 divergem contrato11/2; parâmetros desconhecidos recebemACK.','PENDENTE: alinhar/versionar contrato e validar faixas/status antes doESP. Não ocultado por testesCRC.'),
('P02','MÉDIO','pedaleira.ioc','Esqueleto64MHz diverge BSP550MHz; não configuraSAI/I2C/UART/GPIO.','PENDENTE: sincronizar projetoCube ou manter geração equivalente antes de regenerar firmware.'),
('P03','NÃO CONFIRMADO','F2: ADC com1,5kΩ/ramo','Difere figura12(91Ω+topologia distinta). Carga37k não representa entrada comutada.','Exigir THD/assentamento/estabilidade reais; não afirmar oscilação nem alterar valores por aparência.'),
('P04','NÃO CONFIRMADO','F1/F3: ADC_BIAS↔VCOM','Erro divisor≤2,621mV; VCOM sótípico0,48VA. Matching50mV não garantido.','Medir com≥10MΩ; ponta1MΩ pode introduzir58,5mV de erro.50mV é critério de projeto.'),
('P05','NÃO CONFIRMADO','F5: buck/ESPUSB/GPIO16/17','WeAct1A total nãoé1A livre; móduloESP real nãoidentificado.','Qualificar consumo/ruído e módulo. USBVBUS isolado; não paralelar fontes.'),
('P06','NÃO CONFIRMADO','F2: proteção guitarra/ruído','Modelo genérico indica compressão de diodos com sinais altos. Fuga/captador/temperatura reais ausentes.','Modelo sem os4diodos serve apenas de sensibilidade; NÃO autoriza remover proteção.'),
]
verdict={'verdict':'NÃO APROVADO','confidence':{'connectivity_and_nodal_gains':'alta','firmware_local_fixes':'alta em testes host/compilação; sem bancada','12V_analog_model':'moderada e condicional','CW7805_ADC_dynamic_protection_audio_quality':'insuficiente para liberação'},'rev410_generated':False,'reason_no_rev410':'Falhas físicas/proteção e transporte permanecem sem correção/qualificação demonstrada; não emitir revisão como se corrigida. Errata documental e firmware entregues separadamente.','physical_tests':False,'seven_pages_inspected':True,'connected_pins':256,'nc_pins':9,'nets':57,'physical_components':106,'ERC_violations':0,'transient_matrix_cases':len(r),'transient_matrix_failed':int((r.status!='OK').sum()),'startup_vendor_incomplete':sum(not q['complete'] for q in startup if q['model']=='TI'),'startup_surrogate_complete':sum(q['complete'] for q in startup if q['model']=='bounded'),'known_blockers':[x[0] for x in findings if x[0] in ['A01','A02','A03','A04','P01']]}
(D/'RESULTADO_AUDITORIA.json').write_text(json.dumps(verdict,ensure_ascii=False,indent=2))
text='''# Auditoria elétrica independente da pedaleira digital — revisão 4.9

Data: 2026-11-07. Autoria do projeto: Rodrigues M. Lima. Escopo: sete folhas, modelo físico, KiCad, BOM e firmware do repositório. Nenhum ensaio físico foi realizado.

## Veredito e decisão de revisão

**NÃO APROVADO para funcionamento completo ou conexão a equipamento externo.** Confiança alta na conectividade e nas relações nodais; moderada nas simulações analógicas parciais; insuficiente para garantir proteção do ADC, CW7805 real, THD/assentamento do codec ou transporte digital. Testes progressivos de subconjuntos com carga fictícia são possíveis seguindo o roteiro anexo.

**Não foi emitida revisão4.10 de hardware/PDF.** Há defeitos confirmados ainda sem correção física demonstrada e o transporteSAI/DMA não existe. Criar outro PDF não resolveria essas pendências. As correções comprovadas de firmware e de metadados estão entregues separadamente, com testes, sem declarar uma esquemática corrigida ou validada. Nenhum valor passivo ou ligação elétrica foi alterado. A revisão4.9 original foi preservada com hashes e backup; a errata documental é explicitamente distinta.

O ganho DAC0,499 foi confirmado por KCL independente e por excitações SPICE separadas. U1A/U3A são seguidores e U3B inversor. Não há justificativa para alterar esses ganhos. A fonte12V permanece;9V falha no limite inferior de modo comum adotado paraTL072clássico.12V não é mínimo absoluto matemático nem garantia automática de swing em qualquer exemplar.

## Evidência executada nesta auditoria

- KiCad10.0.7: novoERC, zero violações, zero exclusões/checagens ignoradas; nova exportaçãoXML. Aviso de instalação local sobre api.v1.schema.json ausente foi preservado no log; ERC e exportação concluíram. Nenhuma supressão foi usada.
- ComparaçãoXML↔modelo:106componentes,265terminais físicos =256ligados+9NC,57redes, nenhuma divergência de pinos ou partições. Conferência geométrica de fios/portas visíveis também passou. Isso não substitui inspeção da montagem perfboard.
- PyMuPDF: sete folhasA4paisagem renderizadas e inspecionadas, textos/designadores extraídos; nenhum componente esperado ausente. Cores/símbolos/posição preservados. Texto dePDF não foi usado como prova de conectividade.
- ngspice47:165transientes da matriz +8análisesAC +6ensaios complementares +8tentativas de partida.165/165 da matriz concluíram; as4partidas com modeloTI falharam e foram mantidas como falhas. As4partidas com modelo simplificado concluíram, sem qualificar oTL072 real.
- PythonNumPy/SciPy/pandas/Matplotlib: KCL,48cantos de resistores,300000amostrasMC(seed490410),48cantos capacitivos/cargas e10000amostrasMC(seed4910), térmica/referências/clocks. MC não substituiu limites determinísticos.
- Firmware: testesC++executáveis dos fontes reais com mockBSP/HAL; compilaçãoARM de4fontes; nove testes existentes; DSP nativo com bypass/mute,480000amostras e impulso de delay20ms(960amostras). Não se mediu desempenho noCortexM7 e não se fez link/execução da imagem completa.

## Achados com severidade e estado

|ID|Severidade|Local/evidência|Conclusão|Correção/estado|
|---|---|---|---|---|
'''
for row in findings:text+='|'+'|'.join(row)+'|\n'
text+='''
## Matriz SPICE e limites dos modelos

O macromodelo oficialTI TL072.301(1989), originalmente caracterizado a±15V, foi mantido; duas expressõesPOLY foram convertidas algebricamente em fontesB compatíveis comngspice. Original/adaptação estão no pacote. Não substituímos silenciosamente o modelo. Resultados com10,5/11,3/12,6V são exploratórios: o macro não garante modo comum/swing/temperatura a essas alimentações.

ADC: frequência100/1000/5000/10000/20000Hz × amplitudes50/100/250/500mVpk e1Vpk × trêsRAW.1Vpk é SOBRECARGA fora do nominal≤0,5Vpk. DAC: mesma grade de amplitudes diferenciais, mais2,65125Vpk diferencial(FS superior5,3025Vpp), cada perna com metade da amplitude. A amplitudeDAC não é amplitude de cada pino. Alimentação5V fixa na matriz; limites4,75/5,25V e razão de bias tratados analiticamente, sequência5V/RAW separada em partida.

Guitarra eDAC são excitados separadamente, evitando atribuir acoplamento por referência ao ganho de outro estágio. A cargaADC é37kΩ diferencial, não um CS4272 transistor-level/comutado. FontesDAC ideais não reproduzem distorção nemZout100Ω típicos do chip; cargas≥100k mantêm essa aproximação pequena. Diodos são modelos genéricos, sem corner garantido de fabricante. O regulador é fonte ideal nos ensaios de sinal, não modelo de estabilidade CW.

Amplitude fundamental,offset,extremos,assimetria e razão harmônicaH2..H7 foram obtidos por mínimos quadrados nos últimos6períodos de cada transiente (tempos adaptativos, evitando FFT irregular). DC de operação pré-carrega capacitores: os165casos NÃO medem tempo de partida. Oslogs contêm análisesopDC. A razão harmônica do modelo não éTHD+N medido da pedaleira.

'''
text+='|Caminho/amplitude|Ganho mínimo..máximo|H2..H7 mínimo..máximo (%)|\n|---|---:|---:|\n'
for (path,a),g in r.groupby(['path','stimulus_peak_V']):text+=f'|{path}, {a:g}Vpk|{g.gain.min():.6f}..{g.gain.max():.6f}|{g.THD_2to7_percent.min():.6g}..{g.THD_2to7_percent.max():.6g}|\n'
text+='''
Na sensibilidade de1kHz, retirar SOMENTE no modelo os quatro diodos de guitarra reduz razão harmônica prevista para≈0,00065% a0,5Vpk. Isso aponta compressão na proteção como hipótese relevante para medir; não prova qualidade real nem autoriza remover os diodos.1Vpk não é aprovado por parecer aceitável em um macro.

### AC e cargas

'''
text+='|Caminho/carga|Ganho1kHz(dB)|Ganho20kHz(dB)|Variação20k–1k(dB)|Fase20k(°)|\n|---|---:|---:|---:|---:|\n'
for tag in ['ac_adc_load100000','ac_dac_load100000','ac_dac_load1000000','ac_dac_load10000','ac_dac_load1000']:
 a=ac[tag];text+=f'|{tag}|{a["1000"]["gain_dB"]:.5f}|{a["20000"]["gain_dB"]:.5f}|{a["20000"]["gain_dB"]-a["1000"]["gain_dB"]:.5f}|{a["20000"]["phase_deg"]:.3f}|\n'
text+='''
Recomendação permanece cargaexterna≥100kΩ;10k/1k são sondas de limite, não especificação de saída. O filtroRC duplo é carregado pelo estágio seguinte: o corteconjunto semcarga calculado é≈123kHz, não dois polos independentes em328,8kHz. Os polos de altafrequência/atenuaçãoRF não comprovam rejeiçãoalias doADC comutado.

### Partida e falhas de convergência

'''
text+='|Envelope|Modelo|Concluiu8s?|Mín/max nojack(V)|\n|---|---|---|---|\n'
for a in startup:
 q=a.get('nodes',{}).get('JACK_OUT');text+=f'|{a["case"]}|{a["model"]}|{a["complete"]}|'+(f'{q["min"]:.4f} / {q["max"]:.4f}' if q else 'semvetor: falha de convergência')+'|\n'
text+='''
O substituto de partida usa um polo/limitador de trilhos identificado emOP_STARTUP.lib. O deck de partida também contém diodos internos hipotéticos Dprot nos pinos ADC, além dos BAT85 genéricos: esses elementos não são um modelo fornecido pela Cirrus e não garantem tensões/correntes de proteção do CS4272. Não contém comportamento de modo comum ou sequência real doTL072. Seus extremos são envelope exploratório; não prova de dano, segurança ou amplitude física de pop. Confirma que o circuito não possui um elemento que desconecte ojack das variações deVREF_OP. LogsTI preservam falhas; exitcode0 do programa não foi confundido com conclusão numérica.

## Pior caso e referências

RAWmáximo conservador12,6V; não impor queda mínima do diodo. I5V orçamento0,90898A inclui350mA(STM/digital/GPIO, reserva) e500mA(ESP,reserva),53mAVA e divisores. Não são correntes medidas ou máximos garantidos. P7805proxy7,236W eθJC5+θCS1+θSA2 dãoTj97,9°C a40°C ou117,9°C a60°C. Isso fundamenta dissipador≤2°C/W noambiente real, mas não qualificaCW semdatasheet real.9V reduz calor porém violaCM; retornar a9V seria correção incorreta.

RazãoADC_BIAS0,47950082..0,48049922 por resistores0,1%; VCOM não tem min/max garantidos. Matching50mV é critério do projeto. Capacitores±20% levamτmáximoADC_BIAS≈0,750s eVREF_OP≈0,627s; aguardar5s é um ponto inicial, não substitui captura e verificação de referência estável.8µA líquidos hipotéticos deslocamADC_BIAS≈49,92mV; esse número é sensibilidade, não especificação de corrente doADC.

Falhas analisadas: fonte mínima/máxima,5Vatrasado, ausênciaMCLK, configuraçãoI2C malsucedida, desconexão de carga,USBfonte única eCWemcurtoIN–OUT. Não foram executados curtos reais. A fonte não tem proteção independente contra falhaCW emcurto; não foi inventada exigência de novoCI. Nas condições nãoqualificadas, parar noensaio semcodec conforme roteiro.

## Arquivos e reprodução

`SIMULACOES/`: decks.cir,modelos originais/adaptados,logs,vetores.txt.gz,CSVJSON egráficos. `VALIDACAO/`: novoXML/ERC,comparaçãoPDF/CAD,setefolhasPNG,textos, cálculos,cantos,errataBOM,logsfirmware ebackup/hash. `FONTES/`: fontes recuperadas e inventário com falhasHTTP/timeouts explicitadas. FontesST/BAT consultadas no navegador são referenciadas nosapêndices; não afirmar que umPDFnão baixado está no pacote.

`TESTES_BANCADA_REV410.md` tem o nome solicitado e esclarece que não háREV410liberada. Só avançar uma etapa após aprovação da anterior; inicialmente não instalarCS4272 e não conectar amplificador externo.

Os scriptsfonte estão em `docs/hardware/auditoria_rev49/` e uma cópia acompanha `FONTES_EXECUTAVEIS/`. Detalhes de execução/dependências noREADME. Os testes de integridade confirmam a evidência, não convertem pendências em aprovação elétrica.

## Apêndice A — análise analógica e tabela28pinos

'''
text+=(V/'analogico.md').read_text()+'\n\n## Apêndice B — alimentação\n\n'+(V/'alimentacao.md').read_text()
e=V/'embedded/RELATORIO_EMBEDDED.md'
if e.exists():text+='\n\n## Apêndice C — firmware/pinagem e correções\n\n'+e.read_text()
(D/'AUDITORIA_REV49.md').write_text(text)
print('report',len(text),'characters; verdict',verdict['verdict'])
