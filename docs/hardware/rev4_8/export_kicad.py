#!/usr/bin/env python3
"""Create an embedded-symbol KiCad project from the same physical model as the PDF."""
from pathlib import Path
import os,shutil
import json,uuid,math
ROOT=Path(__file__).resolve().parents[3];OUT=Path(os.environ.get('PEDALEIRA_REV48_OUT',str(ROOT/'output/rev4_8'))).resolve();D=OUT/'kicad';D.mkdir(exist_ok=True)
m=json.loads((OUT/'circuito_rev4_8.json').read_text());parts=m['components'];byref={a['ref']:a for a in parts}
if (OUT/'diagram_layout.json').exists():
 import runpy
 runpy.run_path(str(Path(__file__).with_name('export_connected_kicad.py')),run_name='__main__')
 raise SystemExit(0)
# Placements are saved by the renderer: sharing them avoids schematic drift.
placements=json.loads((OUT/'placements.json').read_text())
uid=lambda:str(uuid.uuid4())
q=lambda s:json.dumps(str(s),ensure_ascii=False)
f=lambda x:f'{x:.5f}'.rstrip('0').rstrip('.')
S=25.4/72
snap=lambda v:round(v/1.27)*1.27
LIBS=[]
root=uid();project='pedaleira_digital_rev4_8'
def effect(size=1.27,hide=False):return f'(effects (font (size {size} {size})){" hide" if hide else ""})'
def prop(name,value,x,y,hide=False):return f'(property {q(name)} {q(value)} (at {f(x)} {f(y)} 0) {effect(1.27,hide)})'
def pol(points):return '(polyline (pts '+' '.join(f'(xy {f(x*S)} {f(-y*S)})' for x,y in points)+') (stroke (width 0.2) (type default)) (fill (type none)))'
def rec(x1,y1,x2,y2):return f'(rectangle (start {f(x1*S)} {f(-y1*S)}) (end {f(x2*S)} {f(-y2*S)}) (stroke (width 0.2) (type default)) (fill (type background)))'
def geometry(a):
 k=a['kind'];pins=list(a['pins']);points={};art=[]
 if k in ('R','C','CP','CB','D','LED','SW','J'):
  for p,x,ang in [(pins[0],-28,0),(pins[1],28,180)]:points[p]=(x,0,ang,24)
  if k=='R':art=[pol([(-4,0),(-3.3,-1.7),(-2,1.7),(-.7,-1.7),(.7,1.7),(2,-1.7),(3.3,1.7),(4,0)])]
  elif k in ('C','CP','CB'):
   points[pins[0]]=(-28,0,0,26.2);points[pins[1]]=(28,0,180,26.2)
   art=[pol([(-1.8,-5),(-1.8,5)]),pol([(1.8,-5),(1.8,5)]),pol([(-4,0),(-1.8,0)]),pol([(1.8,0),(4,0)])]
   if k=='CP':
    art[1]=f'(arc (start {f(3*S)} {f(5*S)}) (mid {f(.75*S)} 0) (end {f(3*S)} {f(-5*S)}) (stroke (width 0.2) (type default)) (fill (type none)))'
    art[3]=pol([(.75,0),(4,0)])
    art += [pol([(-8,-8),(-8,-4)]),pol([(-10,-6),(-6,-6)])]
  elif k in ('D','LED'):
   art=[pol([(-3,-3),(-3,3),(3,0),(-3,-3)]),pol([(3,-3.7),(3,3.7)]),pol([(-4,0),(-3,0)]),pol([(3,0),(4,0)])]
   if k=='LED':art += [pol([(0,-5),(4,-9),(2,-9)]),pol([(4,-4),(8,-8),(6,-8)])]
  elif k=='SW':
   points={pins[0]:(-28,0,0,24),pins[1]:(28,0,180,24),pins[2]:(28,-6,180,24)}
   art=[pol([(-4,0),(3,-4.2)])]
   for x,y in [(-4,0),(4,0),(4,-6)]:art += [f'(circle (center {f(x*S)} {f(-y*S)}) (radius 0.335) (stroke (width 0.15) (type default)) (fill (type none)))']
  else:art=[rec(-4,-7,4,7)]
 else:
  half=math.ceil(len(pins)/2);pitch=15;w=136 if a['ref']=='H_STM32' else 115 if k=='CODEC' else 96;h=max(45,(half-1)*pitch+26)
  art=[rec(-w/2,-h/2,w/2,h/2)]
  for i,p in enumerate(pins):
   left=i<half;idx=i if left else len(pins)-1-i
   points[p]=(-w/2-30 if left else w/2+30,-h/2+13+idx*pitch,0 if left else 180,30)
 return {p:(snap(x*S)/S,snap(y*S)/S,a,snap(l*S)/S) for p,(x,y,a,l) in points.items()},art

def lib(a):
 r=a['ref'];pts,art=geometry(a);pins=[]
 for p,(x,y,ang,length) in pts.items():
  t=a['types'].get(p,'passive')
  if a['kind']=='OP':t='output' if p in ('1','7') else 'power_in' if p in ('4','8') else 'input'
  if a['kind']=='PUMP':t='power_in' if p in ('1','3','8') else 'power_out' if p=='5' else 'passive'
  if r=='J4':t='power_out' if p=='1' else 'power_in'
  n=a['names'].get(p,p if a['kind'] not in ('R','C','CP','CB','D','LED','SW','J') else '~')
  pins += [f'(pin {t} line (at {f(x*S)} {f(-y*S)} {ang}) (length {f(length*S)}) (name {q(n)} {effect(1.0)}) (number {q(p)} {effect(.85)}))']
 definition=f'(symbol {q("rev48:"+r)} (pin_names (offset 0.6)) (exclude_from_sim no) (in_bom yes) (on_board yes) '+prop('Reference',r,0,-10)+prop('Value',a['value'],0,10)+f'(symbol {q(r+"_0_1")} '+''.join(art)+f') (symbol {q(r+"_1_1")} '+''.join(pins)+'))'
 LIBS.append(definition.replace(q('rev48:'+r),q(r),1));return definition

def header(title,u):return f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(u)}) (paper "A4") (title_block (title {q(title)}) (rev "4.8") (company "Rodrigues M. Lima"))'
paths={};titles={1:'Fonte analogica e entrada',2:'Receptor DAC e saida',3:'CS4272 TSSOP-28',4:'Interfaces digitais',5:'Chaves e LEDs',6:'Driver ADC',7:'Desacoplamento'}
roottext=header('Pedaleira Digital Rev 4.8',root)+'(lib_symbols)'
for sh in range(1,8):
 su=uid();paths[sh]=su
 sx=30+((sh-1)%3)*80;sy=35+((sh-1)//3)*45
 roottext += f'(sheet (at {sx} {sy}) (size 65 25) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid {q(su)}) '+prop('Sheetname',titles[sh],sx,sy-2)+prop('Sheetfile',f'folha_{sh}.kicad_sch',sx,sy+28)+f'(instances (project {q(project)} (path {q("/"+root)} (page {q(sh+1)})))))'
 children=[a for a in parts if a['sheet']==sh]
 t=header(titles[sh],uid())+'(lib_symbols '+''.join(lib(a) for a in children)+')'
 for a in children:
  r=a['ref'];_,px,py,_=placements[r];x=snap(px*S);y=snap(py*S);pts,art=geometry(a);isic=a['kind'] not in ('R','C','CP','CB','D','LED','SW','J')
  t += f'(symbol (lib_id {q("rev48:"+r)}) (at {f(x)} {f(y)} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(uid())}) '+prop('Reference',r,x,y-7)+prop('Value',a['value'],x,y+7)+prop('Footprint','',x,y,True)+prop('Package_note',a['package'],x,y,True)
  t += ''.join(f'(pin {q(p)} (uuid {q(uid())}))' for p in pts)
  t += f'(instances (project {q(project)} (path {q("/"+root+"/"+su)} (reference {q(r)}) (unit 1)))))'
  for p,(dx,dy,ang,le) in pts.items():
   xx=x+dx*S;yy=y+dy*S;n=a['pins'][p]
   if n is None:t+=f'(no_connect (at {f(xx)} {f(yy)}) (uuid {q(uid())}))'
   else:
    # Global labels connect nets across all child sheets, with real electrical pins.
    orient=180 if dx<0 else 0
    t+=f'(global_label {q(n)} (shape passive) (at {f(xx)} {f(yy)} {orient}) {effect(1.05)} (uuid {q(uid())}) '+prop('Intersheetrefs','${INTERSHEET_REFS}',xx,yy,True)+')'
 # Intentional source flags: passive diode/connector feed RAW and GND, not generated by another IC.
 if sh==1:
  for i,n in enumerate(['+RAW','GND','-VA_OP']):
   rr='#FLG0'+str(i+1);x=snap(15+i*30);y=snap(170)
   flag=f'(symbol "rev48:{rr}" (pin_names (offset 0) hide) (in_bom no) (on_board no) '+prop('Reference',rr,0,0,True)+prop('Value','PWR_FLAG',0,0,True)+f'(symbol "{rr}_0_1" (polyline (pts (xy 0 0) (xy -1 -1) (xy 1 -1) (xy 0 0)) (stroke (width .15) (type default)) (fill (type none)))) (symbol "{rr}_1_1" (pin power_out line (at 0 0 90) (length 0) (name "pwr" {effect(1)}) (number "1" {effect(1)}))))'
   LIBS.append(flag.replace(q('rev48:'+rr),q(rr),1))
   # Add flag to embedded lib block by replacing its terminator using a parse-free insertion point.
   idx=t.index('(symbol (lib_id')
   # Embedded symbols end immediately before first placed symbol.
   t=t[:idx-1]+flag+')'+t[idx:]
   t+=f'(symbol (lib_id "rev48:{rr}") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {q(uid())}) '+prop('Reference',rr,x,y,True)+prop('Value','PWR_FLAG',x,y,True)+f'(instances (project {q(project)} (path {q("/"+root+"/"+su)} (reference {q(rr)}) (unit 1)))))'
   t+=f'(global_label {q(n)} (shape passive) (at {x} {y} 0) {effect(1.05)} (uuid {q(uid())}) '+prop('Intersheetrefs','${INTERSHEET_REFS}',x,y,True)+')'
 t+=')';(D/f'folha_{sh}.kicad_sch').write_text(t)
(D/f'{project}.kicad_sch').write_text(roottext+')')
(D/f'{project}.kicad_pro').write_text(json.dumps({'meta':{'filename':project+'.kicad_pro','version':1},'erc':{'erc_exclusions':[],'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2))
print(D)

(D/'rev48.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator \"kicad_symbol_editor\")'+''.join(LIBS)+')')
(D/'sym-lib-table').write_text('(sym_lib_table (lib (name \"rev48\") (type \"KiCad\") (uri \"${KIPRJMOD}/rev48.kicad_sym\") (options \"\") (descr \"Rev4.8 physical pin symbols\")))')
