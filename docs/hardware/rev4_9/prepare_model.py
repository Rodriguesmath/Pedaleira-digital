from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
m=json.loads((ROOT/'docs/hardware/rev4_8/circuito_rev4_8.json').read_text())
m['revision']='4.9';m['architecture']='12 V regulated single supply; no negative rail; 9 V rejected for required headroom';m['release_status']='NÃO APROVADO — REQUER CORREÇÕES'
removed={'U4','C7','C8','C9','R9','C3','C17'}
m['components']=[a for a in m['components'] if a['ref'] not in removed]
p={a['ref']:a for a in m['components']}
for a in p.values():
 a['pins']={k:('GND' if n=='-VA_OP' else '+5V' if n in ('+5VA','+5V_USB') else n) for k,n in a['pins'].items()}
 a['sheet']={1:2,2:4,3:3,4:5,5:6,6:2,7:7}[a['sheet']]
 a['status']='já disponível' if a['ref'] in ['U1','U2','U3','U5','H_STM32','H_ESP32'] else 'necessário adquirir / conferir estoque'
 a['basis']='Projeto rev4.9; ver AUDITORIA_REV49.md'
 a['note']=''
 a['min_spec']='Resistor 1%, 0,25 W' if a['kind']=='R' else 'Capacitor não polarizado, ≥25 V' if a['kind'] in ('C','CB') else 'Eletrolítico ≥25 V, 105 °C' if a['kind']=='CP' else 'Conferir identificação e encapsulamento físico'
 a['nc']=[k for k,v in a['pins'].items() if v is None]
def change(ref,**kw):p[ref].update(kw)
def add(ref,kind,value,pins,sheet,function,package='THT',spec='Conforme relatório'):
 a=dict(ref=ref,kind=kind,value=value,pins={str(k):v for k,v in pins.items()},sheet=sheet,function=function,package=package,status='necessário adquirir / conferir estoque',min_spec=spec,note='',basis='Projeto rev4.9',names={},types={},nc=[])
 p[ref]=a;m['components'].append(a)
change('J1',value='12 V DC',pins={'1':'12V_IN','2':'GND'},sheet=1,function='Fonte externa 12 V regulados, 1,5 A; centro positivo',min_spec='11,4..12,6 V; fonte isolada; NÃO usar 9 V nesta revisão')
change('D1',value='1N5822',pins={'1':'FUSED_IN','2':'+RAW'},sheet=1,package='DO-201AD',min_spec='Schottky 3 A, 40 V; conferir fabricante')
change('C33',value='220 uF',sheet=1,function='Reserva após proteção de polaridade')
change('U5',value='CW7805',sheet=1,function='5 V comum para VA e placas; CW sob confirmação',min_spec='Confirmar fabricante: vista frontal usual 1=IN, 2=GND/TAB, 3=OUT; ensaiar 0,9 A e térmica',note='Não aplicar pinagem do L7805 ao CW desconhecido sem confirmar. Dissipador obrigatório.')
for r in ['C21','C22','R21']:change(r,sheet=1)
change('R21',value='910 ohm',function='Carga mínima de 5,5 mA para ensaio isolado do regulador')
change('C22',value='100 nF',min_spec='Cerâmico local ≥25 V')
change('U1',pins={'1':'IN_BUF','2':'IN_BUF','3':'HI_Z','4':'GND','5':'DAC_P','6':'DAC_N','7':'DAC_BUF','8':'+RAW'})
change('U3',pins={'1':'DRV_P','2':'FB_P','3':'IN_BUF','4':'GND','5':'VREF_OP','6':'FB_N','7':'DRV_N','8':'+RAW'})
change('R3',pins={'1':'HI_Z','2':'VREF_OP'},function='Bias de alta impedância do buffer da guitarra')
change('C1',pins={'1':'JACK_IN','2':'INPUT_AC'},min_spec='100 nF filme, ≥50 V')
change('R1',value='100 kohm',pins={'1':'DAC_AC_P','2':'DAC_P'},min_spec='0,1%, mesmo lote/conjunto com R2/R7/R8')
change('R2',value='49.9 kohm',pins={'1':'DAC_P','2':'VREF_OP'},min_spec='0,1%, casar razões R2/R1 e R8/R7')
change('R8',value='49.9 kohm',min_spec='0,1%, casar razões R8/R7 e R2/R1')
change('R7',min_spec='100 kΩ, 0,1%')
change('C5',kind='CP',value='10 uF',pins={'1':'LP2','2':'JACK_OUT'},function='Bloqueio DC; positivo para o receptor DAC',package='Radial eletrolítico ≥25 V',min_spec='10 µF, ≥25 V; + no lado FILT2')
change('SW4',function='Master mute')
change('D5',function='Master mute')
change('R6',value='1 Mohm',min_spec='1 MΩ, 1%, 0,25 W',function='Descarga do conector de saída')
change('R4',value='220 ohm');change('R5',value='220 ohm');change('C4',value='2.2 nF',min_spec='C0G ou filme ≥25 V');change('C6',value='2.2 nF',min_spec='C0G ou filme ≥25 V')
for r,pre,ain in [('C2','ADC_P_AC','AINA_P'),('C16','ADC_N_AC','AINA_N')]:
 change(r,kind='CB',value='10 uF',pins={'1':pre,'2':ain},package='Bipolar radial / filme',min_spec='10 µF bipolar ≥25 V; diferença DC ~3,25 V nominal',function='Isolação DC entre driver e ADC')
change('R15',value='100 kohm',pins={'1':'AINA_P','2':'VCOM'},min_spec='100 kΩ 0,1%, par com R16',function='Bias do ADC positivo em VCOM')
change('R16',value='100 kohm',pins={'1':'AINA_N','2':'VCOM'},min_spec='100 kΩ 0,1%, par com R15',function='Bias do ADC negativo em VCOM')
change('R17',value='10 kohm',pins={'1':'FB_P','2':'DRV_P'},function='Realimentação DC do seguidor U3A')
change('R19',value='10 kohm',pins={'1':'FB_N','2':'DRV_N'},min_spec='10 kΩ 0,1%, razão com R24',function='Realimentação do inversor U3B')
change('C18',value='22 pF',pins={'1':'FB_P','2':'DRV_P'},min_spec='C0G ≥25 V; ensaio de estabilidade obrigatório',function='Realimentação HF de U3A; não é capacitor anti-alias isolado')
change('C19',value='22 pF',pins={'1':'FB_N','2':'DRV_N'},min_spec='C0G ≥25 V; pólo ideal com 10 kΩ ~723 kHz',function='Compensação HF do inversor')
change('R18',pins={'1':'DRV_P','2':'ADC_P_AC'},function='Isolação capacitiva de saída U3A')
change('R20',pins={'1':'DRV_N','2':'ADC_N_AC'},function='Isolação capacitiva de saída U3B')
for r in ['R18','R20']:change(r,value='1.5 kohm',min_spec='1,5 kΩ, 1%, 0,25 W; limita transientes a <9 mA no envelope de 12 V')
change('C20',value='680 pF',min_spec='680 pF C0G, 2%, ≥25 V')
change('R10',value='100 kohm',function='Bias do canal B sem uso em ADC_BIAS')
for r in ['C29','C31']:change(r,pins={'1':'+RAW','2':'GND'})
for r in ['C30','C32']:change(r,value='10 uF',kind='CP',pins={'1':'+RAW','2':'GND'},package='Radial eletrolítico ≥25 V',min_spec='10 µF ≥25 V, 105 °C')
# Header reset source current remains LOW until clocks and rails are verified.
change('J4',value='5 V distribuição',pins={'1':'+5V','2':'GND'},sheet=5,function='Ponto de distribuição vindo do CW7805; NÃO é entrada USB')
p['H_STM32']['types']['P1.2']='power_in'
change('H_ESP32',note='Confirmar modelo DevKit e GPIO16/17 livres; nunca conectar USB com alimentação externa sem isolar VBUS.')
add('F1','F','T1.25 A',{'1':'12V_IN','2':'FUSED_IN'},1,'Fusível de entrada',spec='Retardado 1,25 A, ≥32 V e porta-fusível')
add('D8','D','1N4007',{'1':'+5V','2':'+RAW'},1,'Descarga reversa do regulador','DO-41','1 A, ≥50 V; ânodo na saída de 5 V')
add('R22','R','2.2 kohm',{'1':'+RAW','2':'VREF_OP'},1,'Divisor de referência OP',spec='2,2 kΩ, 1%, 0,25 W')
add('R23','R','2.2 kohm',{'1':'VREF_OP','2':'GND'},1,'Divisor de referência OP',spec='2,2 kΩ, 1%, 0,25 W')
add('C38','CP','470 uF',{'1':'VREF_OP','2':'GND'},1,'Filtragem da referência OP','Radial','470 µF ≥16 V, tolerância ±20%; aguardar 5 s')
add('C39','C','100 nF',{'1':'VREF_OP','2':'GND'},1,'Desacoplamento HF da referência',spec='100 nF ≥25 V')
add('C37','CP','1000 uF',{'1':'+5V','2':'GND'},1,'Reserva de 5 V','Radial','1000 µF ≥10 V, 105 °C; verificar inrush e CW')
add('R24','R','10 kohm',{'1':'IN_BUF','2':'FB_N'},2,'Entrada do inversor U3B',spec='10 kΩ 0,1%, par com R19')
add('R26','R','1 kohm',{'1':'INPUT_AC','2':'HI_Z'},2,'Limitação de corrente na entrada',spec='1 kΩ 1%, 0,25 W')
add('D6','D','1N4148',{'1':'HI_Z','2':'CLAMP_P'},2,'Clamp positivo da guitarra','DO-35','Diodo pequeno sinal; capacitância e fuga baixas')
add('D7','D','1N4148',{'1':'VREF_OP','2':'CLAMP_N'},2,'Clamp negativo da guitarra','DO-35','Diodo pequeno sinal; não protege surtos de rede')
add('D13','D','1N4148',{'1':'CLAMP_P','2':'VREF_OP'},2,'Segundo diodo de clamp positivo','DO-35','Diodo pequeno sinal; em série com D6')
add('D14','D','1N4148',{'1':'CLAMP_N','2':'HI_Z'},2,'Segundo diodo de clamp negativo','DO-35','Diodo pequeno sinal; em série com D7')
for r,n in [('C35','AINA_P'),('C36','AINA_N')]:add(r,'C','100 pF',{'1':n,'2':'GND'},2,'Filtro RF de modo comum do ADC',spec='100 pF C0G, par 2%, ≥25 V')
# Independent passive ADC bias avoids startup current through VCOM (1 uA typical limit).
for r in ('R15','R16','R10'):p[r]['pins']['2' if r!='R10' else '1']='ADC_BIAS'
add('R27','R','13 kohm',{'1':'+5V','2':'ADC_BIAS'},1,'Divisor ADC, ramo superior',spec='13 kΩ 0,1%, par com R28')
add('R28','R','12 kohm',{'1':'ADC_BIAS','2':'GND'},1,'Divisor ADC, ramo inferior',spec='12 kΩ 0,1%, par com R27')
add('C40','CP','100 uF',{'1':'ADC_BIAS','2':'GND'},1,'Filtro do bias ADC','Radial','100 µF ≥10 V; esperar 5 s')
add('C41','C','100 nF',{'1':'ADC_BIAS','2':'GND'},1,'Bypass HF do bias ADC',spec='100 nF ≥25 V')
for r,a,k in [('D9','AINA_P','+5V'),('D10','GND','AINA_P'),('D11','AINA_N','+5V'),('D12','GND','AINA_N')]:
 add(r,'D','BAT85',{'1':a,'2':k},2,'Clamp externo do ADC','DO-35','Schottky pequeno sinal ≥30 V; validar Vf e transientes nos pinos')
for i,n,sh in [(1,'+RAW',1),(2,'+5V',1),(3,'+3V3',5),(4,'VREF_OP',1),(5,'VCOM',3),(6,'IN_BUF',2),(7,'AINA_P',2),(8,'AINA_N',2),(9,'DAC_BUF',4),(10,'GND',1),(11,'ADC_BIAS',1)]:
 add('TP'+str(i),'TP',n,{'1':n},sh,'Ponto de teste '+n,'Pino THT isolado','Pino de teste identificado; manter afastado de curto acidental')
for a in m['components']:
 a['nc']=[k for k,v in a['pins'].items() if v is None]
 if a['kind'] in ('D','LED'):a['names']={'1':'A','2':'K'}
Path(__file__).with_name('circuito_rev4_9.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
print(len(m['components']),'physical components')
