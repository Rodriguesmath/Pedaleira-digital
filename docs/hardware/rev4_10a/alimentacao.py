#!/usr/bin/env python3
"""Fase A: cálculos, inventário e estados; não simula GPIO/CW nem aprova hardware."""
import csv, hashlib, itertools, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/REV410_ENTREGA'; V=OUT/'VALIDACAO'; V.mkdir(parents=True,exist_ok=True)
modelpath=ROOT/'output/auditoria_rev49/VALIDACAO/circuito_rev49_errata_documental.json'
m=json.loads(modelpath.read_text()); cs=m['components']
rows=[]
for c in cs:
 nets=set(x for x in c['pins'].values() if x)
 if nets & {'+RAW','+5V','+3V3','VREF_OP','ADC_BIAS','VCOM','GND'}:
  rows.append({'ref':c['ref'],'valor':c['value'],'folha':c['sheet'], 'redes49':';'.join(sorted(nets)), 'pinos':json.dumps(c['pins'],ensure_ascii=False), 'funcao':c.get('function','')})
with (OUT/'INVENTARIO_ELETRICO_REV49.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
states=[]
for s,e,a in itertools.product([0,1],repeat=3):
 risks=[]
 if s!=e: risks.append('UART: transmissor vivo pode atingir receptor desligado; Ioff nao demonstrado')
 if s!=a: risks.append('Codec: VA e VD/VL separados; ordem de trilhos nao qualificada')
 if a and not s: risks.append('Codec SDOUT/rails analogicos e STM desligado: estado de saida nao garantido')
 if s and not a: risks.append('STM SAI/I2C/RST vivos com VA ausente; RST nao isola')
 if a: risks.append('CW sem identidade; VA nao qualificada')
 if s and e and a: risks.append('Partida/corte/clamps/mute e retorno USB permanecem nao qualificados')
 states.append({'S':s,'E':e,'A':a,'D5_STM':bool(s),'D5_ESP':bool(e),'RAW':bool(a),'VA':bool(a),'VDVL':bool(s), 'UART_link_safe_proven':not(s!=e),'harness_approved':False,'risks':risks or ['Energia residual externa/capacitores: aguardar descarga e excluir audio externo']})
trans=[]
for st in states:
 x=(st['S'],st['E'],st['A'])
 for bit in range(3):
  y=list(x); y[bit]^=1
  trans.append({'from':''.join(map(str,x)),'to':''.join(map(str,y)),'changed':['USB_STM','USB_ESP','12V'][bit], 'approved_harness':False})
# 53 mA maxVA (Cirrus); bleeder and divider endpoints deliberately conservative.
i5=.053+5.25/(910*.99)+5.25/(25000*.999)
i5typ=.045+5/910+5/25000
power=(12.6-4.75)*i5+12.6*.008
par={'CW_identity_known':False,'VA_max_A_datasheet':.053,'VA_typ_A_datasheet':.045,'bleeder_ohm':910,'bleeder_tolerance':.01,'ADC_divider_total_ohm':25000,'ADC_res_tolerance':.001,'CW_Iq_proxy_A':.008,'RAW_min_assumed_V':10.5,'RAW_nom_assumed_V':11.3,'RAW_max_conservative_V':12.6,'theta_JA_proxy_K_W':50,'theta_JC_proxy_K_W':5,'theta_CS_assumed_K_W':1,'theta_SA_old_K_W':2,'WeAct_max_total_3V3_A_vendor':1,'codec_VDVL_max_A_datasheet':.028,'V5_min_assumed_V':4.75,'V5_max_assumed_V':5.25}
result={'classification':'CALCULADO, proxies CW nao validam componente','input_model_sha256':hashlib.sha256(modelpath.read_bytes()).hexdigest(),'inventory_count':len(rows),'VA_domain_max_budget_A':i5,'VA_domain_typ_budget_A':i5typ,'CW_power_worst_proxy_W':power,'CW_Tj_proxy_no_sink_at40_C':40+power*50,'CW_Tj_proxy_old_sink_at40_C':40+power*8,'theta_JA_total_for_Tj100_at40_K_W':60/power,'bleeder_max_power_W':5.25**2/(910*.99),'new_digital_load_on_CW_A':0,'UART_safe_Ioff_proven':False,'CW_A04_resolved':False,'gate_A':'BLOCKED','B_started':False,'state_count':len(states),'directed_single_source_transitions':len(trans),'states':states,'transitions':trans,'params':par}
(V/'calculos_A.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
assert len(states)==8 and len(trans)==24
assert .059<i5<.060 and .56<power<.58
assert not result['CW_A04_resolved'] and not result['B_started']
print(json.dumps({k:result[k] for k in ['gate_A','state_count','directed_single_source_transitions','VA_domain_max_budget_A','CW_power_worst_proxy_W']},ensure_ascii=False))
