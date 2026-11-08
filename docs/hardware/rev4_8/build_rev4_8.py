#!/usr/bin/env python3
"""Rev4.8: single physical pin/net model -> editable JSON, BOM, PDF and KiCad.
Original revision 4.7 is deliberately not imported or overwritten.
"""
from pathlib import Path
import os,shutil
import json,csv,math,uuid,hashlib
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(os.environ.get('PEDALEIRA_REV48_OUT',str(ROOT/'output/rev4_8'))).resolve();OUT.mkdir(parents=True,exist_ok=True)
MODEL=Path(__file__).with_name('circuito_rev4_8.json')
# Sheet order follows the audio path; supporting power stays on sheet 7.
OLD_TO_NEW={1:1,6:2,3:3,2:4,4:5,5:6,7:7}
PAGES={1:'Entrada de instrumento e alimentação dos TL072',2:'Condicionamento diferencial para o ADC',3:'Codec CS4272 e referências analógicas',4:'Receptor diferencial do DAC e saída P10',5:'STM32, ESP32 e interfaces digitais',6:'Chaves e indicadores',7:'Alimentação do codec e desacoplamento'}
model=json.loads(MODEL.read_text());components=model['components'];byref={c['ref']:c for c in components}
assert len(byref)==len(components)
with (OUT/'BOM_rev4_8.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Referência','Componente','Valor','Quantidade','Encapsulamento','Função','Situação','Observações','Fundamentação'])
 for a in components:w.writerow([a['ref'],a['kind'],a['value'],1,a['package'],a['function'],a['status'],a['note'],a['basis']])
(OUT/'circuito_rev4_8.json').write_text(MODEL.read_text())
# PDF: electrical symbols and every terminal are rendered directly from the model.
fonts=Path('/home/rodrigues/.local/share/fonts/msttcorefonts')
for n,f in [('T','Times.TTF'),('TB','Timesbd.TTF')]:pdfmetrics.registerFont(TTFont(n,str(fonts/f)))
pdfmetrics.registerFont(TTFont('HB','/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf'))
cv=canvas.Canvas(str(OUT/'pedaleira_digital_rev4_8.pdf'),pagesize=(842,595))
cv.setTitle('Pedaleira Digital - Esquemática elétrica rev 4.8');cv.setAuthor('Rodrigues M. Lima')
BLUE='#0000FF'; NAVY='#000080'; MAROON='#800000'; BLACK='#000000'; rendered=set(); terminal_rendered=set()
def txt(x,y,s,size=7,color=BLACK,font='T',align='left'):
 cv.setFillColor(color);cv.setFont(font,size)
 getattr(cv,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,595-y,str(s).replace('uF','µF').replace('kohm','kΩ').replace('Mohm','MΩ').replace('ohm','Ω'))
def ln(x,y,x2,y2,color=NAVY,w=.6):
 cv.setStrokeColor(color);cv.setLineWidth(w);cv.line(x,595-y,x2,595-y2)
def poly(pts,color=BLUE,w=.65):
 for a,b in zip(pts,pts[1:]):ln(*a,*b,color,w)
def circle(x,y,r=.95):
 cv.setStrokeColor(BLUE);cv.setFillColor('#FFFFFF');cv.circle(x,595-y,r,stroke=1,fill=1)
def wrap(s,width,size=6.5):
 lines=[];cur=''
 for word in s.split():
  test=(cur+' '+word).strip()
  if pdfmetrics.stringWidth(test,'T',size)>width and cur:lines.append(cur);cur=word
  else:cur=test
 if cur:lines.append(cur)
 return lines
# Physical layout in points, exported to KiCad in mm with exact equivalent terminals.
placements={}
for sheet in PAGES:
 parts=[a for a in components if a['sheet']==sheet]
 if sheet==3:
  placements['U2']=(sheet,180,245,'chip')
  others=[a for a in parts if a['ref']!='U2']
  for i,a in enumerate(others):placements[a['ref']]=(sheet,605,126+i*65,'passive')
 elif sheet==4:
  placements['H_STM32']=(sheet,180,210,'chip');placements['H_ESP32']=(sheet,585,135,'chip')
  others=[a for a in parts if not a['ref'].startswith('H_')]
  for i,a in enumerate(others):placements[a['ref']]=(sheet,480+(i%2)*160,290+(i//2)*65,'passive')
 else:
  # ICs occupy their own lower band; passives in consistent three-column rows.
  passives=[a for a in parts if a['kind'] not in ('OP','PUMP','REG') and a['ref']!='R21']
  for i,a in enumerate(passives):placements[a['ref']]=(sheet,145+(i%3)*260,110+(i//3)*65,'passive')
  ics=[a for a in parts if a['kind'] in ('OP','PUMP','REG')]
  yy=110+math.ceil(len(passives)/3)*65
  for i,a in enumerate(ics):placements[a['ref']]=(sheet,170+i*350,yy+40,'chip')
placements['R21']=(7,520,410,'passive')
# Shared notes: these are also embedded in the native CAD sheets.
notes={
1:['U1/U3 pino 8 = +RAW; pino 4 = -VA_OP. A alimentação negativa é uma alteração obrigatória desta revisão.',
   'C3/C8: positivo no GND. C7: positivo no CAP+. Não interligar -VA_OP ao GND. +RAW esperado: 7,8 a 8,7 V.',
   'U1A: pinos 3 (+), 2 (-), 1 (OUT), seguidor. Zin ~1 Mohm; fc de entrada ~1,59 Hz.'],
2:['U1B: pinos 5 (+)=DAC_P, 6 (-)=DAC_N, 7= DAC_BUF; alimentação comum à folha 1.',
   'Vout ~ AOUTA+ - AOUTA-. R1/R2/R7/R8 = 100 kohm, preferir casamento 0,1%. C10/C11/C5 são bipolares.',
   'Rede RC preservada em valor e movida após U1B. Carga >=100 kohm preferida; não é saída para fones.'],
3:['U2: vista elétrica funcional com numeração física TSSOP-28. Conferir marca do pino 1 no CI e no adaptador.',
   'XTI em GND; XTO aberto: MCLK externo. AD0 em GND: endereço I2C 7 bits 0x10 (byte escrita 0x20).',
   'AINB+ e AINB- ligados ao mesmo bias; canal B mutado. Saídas B e MUTEC: NC; nunca aterrar saídas DAC.'],
4:['SAI4 A = master TX; SAI4 B = slave RX síncrono interno a A. PE4/PE5/PE6 usam AF8; PE0/PA0 usam AF10.',
   'I2S: Fs=48 kHz; MCLK=12,288 MHz (256 Fs); BCLK=3,072 MHz (64 Fs); 2 slots x 32 bits, 24 bits úteis.',
   'I2S: MSB um BCLK após transição LRCK; L em LRCK baixo. Amostrar na borda de subida; dados mudam na descida.',
   'Firmware atual NÃO atende: revisar AF, sequência de reset, 0x03 ATAPI e 0x06 ADC_DIF. Ver auditoria.'],
5:['Chaves SPDT: C = comum, 1 = contato usado, 2 = não conectado. Confirmar os terminais físicos por continuidade.',
   'PC0..PC3: GPIO_PULLUP; contato fechado = LOW; debounce em firmware. LEDs: 1=A, 2=K.'],
6:['Rede de feedback copiada de DS593F2 fig.12: 634 ohm vai ao pino ADC, após 91 ohm; C18/C19 vão à saída do driver; compensação 4,7 nF ajustada para TL072.',
   'U3A: 3=ADC_P_IN, 2=FB_P, 1=DRV_P. U3B: 5=ADC_N_IN, 6=FB_N, 7=DRV_N; pinos 8/4 na folha 7.',
   'VCOM é apenas bias de alta impedância. Entrada mono por uma perna: limitar guitarra a 1 V de pico; menor uso da faixa ADC.'],
7:['VA=+5VA (4,75..5,25 V); VD=VL=+3V3 (VD >=3,1 V); GND comum contínuo, com retornos analógicos curtos.',
   '100 nF junto a cada pino; reservas de 1 uF próximas. Nenhum ferrite é obrigatório; avaliar EMI na montagem.',
   '+5VA vem de U5, +5V_USB alimenta apenas as placas; nunca unir as duas redes. Não usar VCOM como alimentação.',
   'Veredito condicionado: medir alimentação negativa, clipping/estabilidade e clocks; corrigir firmware antes do teste de áudio.']}

def terminal(a,p,x,y,side='left'):
 terminal_rendered.add((a['ref'],str(p)))
 net=a['pins'][str(p)]
 if net is None:
  ln(x-2,y-2,x+2,y+2,BLUE);ln(x-2,y+2,x+2,y-2,BLUE);return
 if net=='GND' and side not in ('chip_left','chip_right'):
  ln(x,y,x,y+3,MAROON)
  for dy,w in [(3,4),(5,2.7),(7,1.3)]:ln(x-w,y+dy,x+w,y+dy,MAROON)
  txt(x,y+15,'GND',6.3,MAROON,align='center')
 else:
  # Underlined net identifiers, without decorative arrows.
  align='right' if side in ('left','chip_left') else 'left'
  tx=x-2 if side in ('left','chip_left') else x+2
  txt(tx,y-3,net,6.8,MAROON,align=align)
  ww=pdfmetrics.stringWidth(net,'T',6.8)
  ln(tx-ww if align=='right' else tx,y-1,tx if align=='right' else tx+ww,y-1,MAROON,.35)

def passive(a,x,y):
 rendered.add(a['ref']);k=a['kind']
 marker=' *' if a['status']=='novo' else ' [tipo]' if a['status'].startswith('substituído') else ''
 txt(x,y-13,a['ref']+marker,8,BLACK if k=='SW' else NAVY,align='center')
 txt(x,y+20,a['value'],7,NAVY if k!='SW' else BLACK,align='center')
 pins=list(a['pins']);left,right=pins[:2]
 ln(x-28,y,x-4,y);ln(x+4,y,x+28,y)
 if k=='R':poly([(x-4,y),(x-3.3,y-1.7),(x-2,y+1.7),(x-.7,y-1.7),(x+.7,y+1.7),(x+2,y-1.7),(x+3.3,y+1.7),(x+4,y)])
 elif k in ('C','CP','CB'):
  ln(x-1.8,y-5,x-1.8,y+5,BLUE)
  if k=='CP':
   p=cv.beginPath();p.moveTo(x+3,595-y+5);p.curveTo(x,595-y+2,x,595-y-2,x+3,595-y-5)
   cv.setStrokeColor(BLUE);cv.drawPath(p)
   txt(x-9,y-7,'+',7,BLUE);txt(x+6,y-7,'-',7,BLUE)
  else:ln(x+1.8,y-5,x+1.8,y+5,BLUE)
  ln(x-4,y,x-1.8,y,BLUE);ln(x+(.75 if k=='CP' else 1.8),y,x+4,y,BLUE)
 elif k in ('D','LED'):
  poly([(x-3,y-3),(x-3,y+3),(x+3,y),(x-3,y-3)]);ln(x+3,y-3.7,x+3,y+3.7,BLUE);ln(x-4,y,x-3,y,BLUE);ln(x+3,y,x+4,y,BLUE)
  if k=='LED':
   for xx,dy in [(x,-5),(x+4,-4)]:
    ln(xx,y+dy,xx+4,y+dy-4,BLUE);poly([(xx+2,y+dy-4),(xx+4,y+dy-4),(xx+4,y+dy-2)])
 elif k=='SW':
  # Actual SPDT symbol, unused throw shown and marked NC.
  circle(x-4,y);circle(x+4,y);circle(x+4,y-6)
  ln(x-3.4,y-.4,x+3,y-4.2,BLUE);ln(x+4,y-6,x+28,y-6)
  terminal(a,pins[2],x+28,y-6,'right')
 else:
  cv.setFillColor('#FFFFB0');cv.setStrokeColor(MAROON);cv.rect(x-4,595-y-7,8,14,fill=1,stroke=1)
 for pin,px,side in [(left,x-28,'left'),(right,x+28,'right')]:
  txt(px+3 if side=='left' else px-3,y+7,pin,5.5,align='left' if side=='left' else 'right');terminal(a,pin,px,y,side)
 for i,s in enumerate(wrap(a['function'],225,6.7)[:2]):txt(x,y+32+i*8,s,6.7,align='center')

def chip(a,x,y):
 if a['kind']=='OP':
  rendered.add(a['ref'])
  for unit,pp,pn,po,dy in [('A','3','2','1',-12),('B','5','6','7',43)]:
   yy=y+dy
   cv.setFillColor('#FFFFB0');cv.setStrokeColor(BLUE)
   p=cv.beginPath();p.moveTo(x-12,595-yy+14);p.lineTo(x-12,595-yy-14);p.lineTo(x+14,595-yy);p.close();cv.drawPath(p,fill=1,stroke=1)
   txt(x,yy-20,a['ref']+unit+(' *' if a['status']=='novo' else ''),8,NAVY,align='center')
   for pin,sy,polarity in [(pn,yy-8,'-'),(pp,yy+8,'+')]:
    ln(x-30,sy,x-12,sy,BLACK);txt(x-9,sy+2,polarity,8)
    txt(x-21,sy-3,pin,5.7);terminal(a,pin,x-30,sy,'chip_left')
   ln(x+14,yy,x+30,yy,BLACK);txt(x+20,yy-3,po,5.7);terminal(a,po,x+30,yy,'chip_right')
  txt(x+125,y+8,a['value'],7,align='center')
  for pin,dy in [('8',-8),('4',23)]:
   yy=y+dy;xx=x+125
   ln(xx,yy,xx,yy-6,MAROON);ln(xx-4,yy-6,xx+4,yy-6,MAROON)
   txt(xx+6,yy,pin,6);terminal(a,pin,xx,yy-6,'chip_right')
  return
 rendered.add(a['ref']);pins=list(a['pins']);half=math.ceil(len(pins)/2);pitch=15
 w=136 if a['ref']=='H_STM32' else 115 if a['kind']=='CODEC' else 96
 h=max(45,(half-1)*pitch+26)
 cv.setFillColor('#FFFFB0');cv.setStrokeColor(MAROON);cv.setLineWidth(.6);cv.rect(x-w/2,595-y-h/2,w,h,fill=1,stroke=1)
 txt(x,y-h/2-13,a['ref']+(' *' if a['status']=='novo' else ''),8,NAVY,align='center')
 txt(x,y-h/2-3,a['value'],7,align='center')
 for i,p in enumerate(pins):
  left=i<half;idx=i if left else len(pins)-1-i
  yy=y-h/2+13+idx*pitch
  xx=x-w/2 if left else x+w/2;end=xx-30 if left else xx+30
  ln(xx,yy,end,yy,BLACK)
  name=a['names'].get(p,p)
  tag=' [S]' if a['types'].get(p)=='output' else ' [E/S]' if a['types'].get(p)=='bidirectional' else ''
  txt(xx+3 if left else xx-3,yy+2,name+tag,6.1,align='left' if left else 'right')
  txt((xx+end)/2,yy-3,p,5.7,align='center');terminal(a,p,end,yy,'chip_left' if left else 'chip_right')
 # Pin mapping of op amps uses a true symbol in dedicated inset on following page.
 if a['kind']=='OP':
  txt(x,y+h/2+12,'A: 3(+), 2(-), 1(S)  |  B: 5(+), 6(-), 7(S)',6.5,align='center')

# Readable sheet notes; detailed calculations remain in the audit document.
notes={
1:['Entrada P10: buffer U1A, seguido pelo condicionamento na F2. C1/R3: fc ≈ 1,59 Hz; Zin ≈ 1 MΩ.',
   'U1 e U3: pino 8 em +RAW, pino 4 em -VA_OP. C3/C8: terminal positivo no GND.'],
2:['Entrada IN_BUF da F1; saídas AINA_P/N para o codec na F3. VCOM é referência de bias, não alimentação.',
   'U3: alimentação indicada nesta folha; desacoplamento na F7. Estabilidade e limite de sinal: ver auditoria.'],
3:['MCLK externo: XTI em GND e XTO em NC. AD0 em GND: endereço I2C de 7 bits = 0x10.',
   'Canal B sem uso: entradas no mesmo bias; saídas B e MUTEC em NC. Números indicam pinos físicos.'],
4:['U1B: receptor diferencial com ganho unitário. R1/R2/R7/R8: preferir casamento de 0,1%.',
   'C5/C10/C11 bipolares. Saída para carga ≥100 kΩ; não destinada a fones. Alimentação U1 na F1.'],
5:['SAI4: TX master e RX síncrono. I2S: 48 kHz; MCLK 12,288 MHz; BCLK 3,072 MHz.',
   'Conferir firmware e pads PC2_C/PC3_C conforme auditoria. +5V_USB é independente de +5VA.'],
6:['Chaves: C = comum; 1 = contato utilizado; 2 = NC. GPIO com pull-up; contato fechado = LOW.',
   'LEDs: ânodo à esquerda e cátodo à direita. Confirmar terminais físicos por continuidade.'],
7:['+5VA alimenta o codec; +5V_USB alimenta as placas. Não unir essas redes. GND é comum.',
   'Capacitores de 100 nF junto aos pinos; reservas de 1 µF próximas. Validação de bancada pendente.']}

exec(compile(Path(__file__).with_name('layout_connected.py').read_text(), 'layout_connected.py', 'exec'))

def approved_frame_and_legend(sheet,title):
 # Exact virtual-sheet geometry of the approved revision before conditioning.
 sx=842/420;sy=595/297
 def line(x,y,X,Y,w=.25):ln(x*sx,y*sy,X*sx,Y*sy,BLACK,w*sx)
 def box(x,y,w,h,lw=.24):
  cv.setStrokeColor(BLACK);cv.setLineWidth(lw*sx);cv.rect(x*sx,595-(y+h)*sy,w*sx,h*sy,stroke=1,fill=0)
 def text(x,y,value,size=2.8,color=BLACK,font='T',align='left'):
  txt(x*sx,y*sy,value,size*1.18*sx,color,font,align)
 box(3,12,414,273);box(10,19,400,259)
 for i in range(4):
  x=3+414*(i+.5)/4;y=12+273*(i+.5)/4
  text(x,16.7,str(i+1),2.7/1.18,align='center');text(x,282.7,str(i+1),2.7/1.18,align='center')
  text(6.5,y+.9,'ABCD'[i],2.7/1.18,align='center');text(413.5,y+.9,'ABCD'[i],2.7/1.18,align='center')
 for i in range(1,4):
  x=3+414*i/4;y=12+273*i/4
  for y1,y2 in [(12,19),(278,285)]:line(x,y1,x,y2,.2)
  for x1,x2 in [(3,10),(410,417)]:line(x1,y,x2,y,.2)
 box(230,250,180,28,.35)
 for y in (259,268):line(230,y,410,y)
 for x in (300,319,352,374):line(x,259,x,268)
 for x in (310,365):line(x,268,x,278)
 text(233,253.4,'TÍTULO DA FOLHA',2.5,'#404040')
 text(233,257.8,title,3.1,NAVY)
 for x,caption,value in [(233,'NÚMERO DO DOCUMENTO','PD-EA-001'),(303,'REVISÃO','4.8'),(322,'DATA','2026-11-07'),(355,'FOLHA',f'{sheet} / 7'),(377,'FORMATO','A4 / 297 × 210')]:
  text(x,262.3,caption,2.5,'#404040');text(x,266.8,value,2.8,font='TB')
 text(233,271.8,'AUTORIA / PROJETO',2.5,'#404040');text(233,276.2,'Rodrigues M. Lima')
 text(313,271.8,'STATUS DO DOCUMENTO',2.5,'#404040');text(313,276.2,'Condicionado')
 text(368,271.8,'ESCALA',2.5,'#404040');text(368,276.2,'Sem escala')

for sheet,title in PAGES.items():
 cv.setFillColor('#FFFCF8');cv.rect(0,0,842,595,fill=1,stroke=0)
 approved_frame_and_legend(sheet,title)
 draw_sheet(sheet)
 yy=489
 for s in notes[sheet]:
  for row in wrap(s,399,6.5):
   txt(40,yy,row,6.5);yy+=8
 assert yy<553,(sheet,yy)
 cv.showPage()
cv.save()
assert rendered==set(byref)
assert terminal_rendered=={(a['ref'],p) for a in components for p in a['pins']}
(OUT/'render_coverage.json').write_text(json.dumps({'components':len(rendered),'physical_terminals':len(terminal_rendered),'all_rendered':True},indent=2))
# A real connectivity model, independently checked; this is not a claim of PCB validation.
nets=defaultdict(list)
for a in components:
 assert set(a['nc'])=={p for p,n in a['pins'].items() if n is None},a['ref']
 for p,n in a['pins'].items():
  if n is not None:nets[n].append((a['ref'],p))
assert all(len(v)>=2 for v in nets.values()),[(n,v) for n,v in nets.items() if len(v)<2]
assert byref['U2']['pins']['20']=='+5VA' and byref['U2']['pins']['9']==byref['U2']['pins']['10']=='+3V3'
assert byref['U2']['pins']['13']=='GND' and byref['U2']['pins']['2']=='GND'
assert all(byref[r]['pins']['4']=='-VA_OP' and byref[r]['pins']['8']=='+RAW' for r in ('U1','U3'))
assert byref['C8']['pins']['1']==byref['C3']['pins']['1']=='GND'
assert byref['R17']['pins']['2']=='AINA_P' and byref['R19']['pins']['2']=='AINA_N'
(OUT/'netlist_rev4_8.json').write_text(json.dumps(nets,ensure_ascii=False,indent=2))
print(f'PDF/BOM/model generated: {len(components)} physical components, {len(nets)} nets.')

(OUT/'placements.json').write_text(json.dumps(placements,indent=2))

save_connected_layout()
