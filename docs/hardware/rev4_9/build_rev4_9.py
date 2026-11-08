#!/usr/bin/env python3
"""Rev4.9: single physical pin/net model -> editable JSON, BOM, PDF and KiCad.
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
OUT=Path(os.environ.get('PEDALEIRA_REV49_OUT',str(ROOT/'output/rev4_9'))).resolve();OUT.mkdir(parents=True,exist_ok=True)
MODEL=Path(__file__).with_name('circuito_rev4_9.json')
# Sheet order follows the audio path; supporting power stays on sheet 7.
OLD_TO_NEW={i:i for i in range(1,8)}
PAGES={1:'Fonte única, regulador e referência OP',2:'Guitarra e condicionamento ADC completo',3:'Codec CS4272 e referências analógicas',4:'Receptor DAC e saída de linha',5:'STM32, ESP32 e distribuição digital',6:'Chaves e indicadores',7:'Desacoplamento e alimentação dos TL072'}
model=json.loads(MODEL.read_text());components=model['components'];byref={c['ref']:c for c in components}
assert len(byref)==len(components)
with (OUT/'BOM_rev4_9.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['Referência','Componente','Valor','Quantidade','Encapsulamento','Função','Situação','Especificações mínimas','Observações','Fundamentação'])
 for a in components:w.writerow([a['ref'],a['kind'],a['value'],1,a['package'],a['function'],a['status'],a['min_spec'],a['note'],a['basis']])
(OUT/'circuito_rev4_9.json').write_text(MODEL.read_text())
# PDF: electrical symbols and every terminal are rendered directly from the model.
fonts=Path('/home/rodrigues/.local/share/fonts/msttcorefonts')
for n,f in [('T','Times.TTF'),('TB','Timesbd.TTF')]:pdfmetrics.registerFont(TTFont(n,str(fonts/f)))
pdfmetrics.registerFont(TTFont('HB','/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf'))
cv=canvas.Canvas(str(OUT/'pedaleira_digital_rev4_9.pdf'),pagesize=(842,595))
cv.setTitle('Pedaleira Digital - Esquemática elétrica rev 4.9');cv.setAuthor('Rodrigues M. Lima')
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

notes={
1:['12 V DC regulados (11,4..12,6 V). A opção 9 V não foi aprovada. VREF_OP não é GND nem VCOM.',
   'CW7805: fabricante/pinagem/corrente pendentes. Dissipador ≤2 °C/W; validar carga antes de instalar o codec.'],
2:['Entrada nominal ≤0,5 V de pico. U3A: +1; U3B: -1. C2/C16 isolam VREF_OP (~5,65 V) de ADC_BIAS (~2,4 V).',
   'ADC: 1,5 kΩ por perna, 680 pF diferencial e 100 pF para GND. Clamps BAT85; verificar transientes em bancada.'],
3:['MCLK externo: XTI em GND, XTO em NC. AD0=GND: endereço I2C 0x10 (7 bits).',
   'VCOM sem carga externa; ADC_BIAS independente em 0,48 × +5V. Validar diferença para VCOM ≤50 mV.'],
4:['Ganho diferencial nominal 0,499. R1/R2/R7/R8: razões casadas 0,1%. + de C5 para LP2.',
   'Carga externa ≥100 kΩ. Manter amplificador externo em mute durante a partida e o desligamento.'],
5:['+5V do CW7805 em ramais separados para as placas e VA do codec; GND comum. USB VBUS deve estar isolado.',
   '+3V3 vem do conversor onboard WeAct. Verificar carga, ruído e 3,2..3,4 V antes de ligar VD/VL do codec.'],
6:['C=contato comum; 1=usado; 2=NC. GPIO pull-up; fechado=LOW. SW4 deve comandar mute, não bypass.',
   'Confirmar pads PC2_C/PC3_C e GPIO16/17 livres no modelo real do ESP32.'],
7:['Os dois TL072 usam pino 8 em +RAW e pino 4 em GND real. Não existe alimentação negativa.',
   '100 nF a poucos milímetros de cada CI. Referência OP filtrada na F1. Projeto ainda não aprovado para áudio.']}
exec(compile(Path(__file__).with_name('layout_connected.py').read_text(),'layout_connected.py','exec'))
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
 for x,caption,value in [(233,'NÚMERO DO DOCUMENTO','PD-EA-001'),(303,'REVISÃO','4.9'),(322,'DATA','2026-11-07'),(355,'FOLHA',f'{sheet} / 7'),(377,'FORMATO','A4 / 297 × 210')]:
  text(x,262.3,caption,2.5,'#404040');text(x,266.8,value,2.8,font='TB')
 text(233,271.8,'AUTORIA / PROJETO',2.5,'#404040');text(233,276.2,'Rodrigues M. Lima')
 text(313,271.8,'STATUS DO DOCUMENTO',2.5,'#404040');text(313,276.2,'Não aprovado')
 text(368,271.8,'ESCALA',2.5,'#404040');text(368,276.2,'Sem escala')

for sheet,title in PAGES.items():
 cv.setFillColor('#FFFCF8');cv.rect(0,0,842,595,fill=1,stroke=0)
 approved_frame_and_legend(sheet,title);draw_sheet(sheet)
 yy=489
 for s in notes[sheet]:
  for row in wrap(s,399,6.5):txt(40,yy,row,6.5);yy+=8
 assert yy<553,(sheet,yy)
 cv.showPage()
cv.save()
assert rendered==set(byref),(rendered^set(byref))
assert terminal_rendered=={(a['ref'],p) for a in components for p in a['pins']}
nets=defaultdict(list)
for a in components:
 for p,n in a['pins'].items():
  if n is not None:nets[n].append((a['ref'],p))
assert all(len(v)>=2 for v in nets.values()),[(n,v) for n,v in nets.items() if len(v)<2]
(OUT/'netlist_rev4_9.json').write_text(json.dumps(nets,ensure_ascii=False,indent=2))
(OUT/'render_coverage.json').write_text(json.dumps({'components':len(rendered),'physical_terminals':len(terminal_rendered),'all_rendered':True},indent=2))
save_connected_layout()
print('PDF/BOM/physical model:',len(components),'components,',len(nets),'nets')
