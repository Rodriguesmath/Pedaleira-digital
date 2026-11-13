#!/usr/bin/env python3
"""Export the routed functional layout, including split opamp units, to KiCad.
Artwork and native wire/pin geometry share the PDF drawing description.
"""
from pathlib import Path
import os,json,uuid,math,shutil
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(os.environ.get('PEDALEIRA_REV410_OUT',str(ROOT/'output/REV410_ENTREGA'))).resolve();D=OUT/'kicad';D.mkdir(exist_ok=True)
m=json.loads((OUT/'circuito_rev4_10.json').read_text());byref={a['ref']:a for a in m['components']}
l=json.loads((OUT/'diagram_layout.json').read_text());instances=l['instances'];project='pedaleira_digital_rev4_10'
S=.254;OX=19.05;OY=12.7
_uuid_sequence=iter(range(1000000))
uid=lambda:str(uuid.uuid5(uuid.NAMESPACE_URL,'pedaleira/rev4.10/'+str(next(_uuid_sequence))));q=lambda s:json.dumps(str(s),ensure_ascii=False)
f=lambda n:f'{n:.5f}'.rstrip('0').rstrip('.') if n else '0'
def eff(size=1.27,hide=False,align=None):return f'(effects (font (size {f(size)} {f(size)}))'+(f' (justify {align})' if align and align!='center' else '')+(' hide' if hide else '')+')'
def prop(k,v,x,y):return f'(property {q(k)} {q(v)} (at {f(x)} {f(y)} 0) {eff(1.27,True)})'
def xy(x,y):return x*S+OX,y*S+OY
def point(x,y):return f'(xy {f(x)} {f(y)})'
def local(x,y,c):return (x-c[0])*S,-(y-c[1])*S

def graphic(a,c=None):
 def trans(x,y):return local(x,y,c) if c else xy(x,y)
 k=a['kind']
 if k=='polygon':
  pts=[trans(*v) for v in a['points']];pts.append(pts[0])
  return '(polyline (pts '+' '.join(point(*v) for v in pts)+') (stroke (width 0.1) (type default)) (fill (type outline)))'
 if k=='line':
  p=[trans(*v) for v in a['points']]
  return '(polyline (pts '+' '.join(point(*v) for v in p)+f') (stroke (width {f(a.get("width",.6)*S)}) (type default)) (fill (type none)))'
 if k=='circle':
  x,y=trans(*a['at']);return f'(circle (center {f(x)} {f(y)}) (radius {f(a["radius"]*S)}) (stroke (width 0.15) (type default)) (fill (type none)))'
 if k in ('rect','block'):
  x,y,w,h=a['rect'];x1,y1=trans(x,y);x2,y2=trans(x+w,y+h)
  if c:return f'(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width 0.15) (type default)) (fill (type background)))'
  return '(polyline (pts '+' '.join(point(*trans(*p)) for p in [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)])+') (stroke (width 0.1) (type default)) (fill (type none)))'
 if k=='text':
  x,y=trans(*a['at']);size=a['size']*S*.75;align=a.get('align','left')
  text=a['text'].replace('uF','µF').replace('kohm','kΩ').replace('Mohm','MΩ').replace('ohm','Ω')
  # Glyph baseline differs from reportlab; preserve a small baseline correction.
  y+=size*.3 if c else -size*.3
  return f'(text {q(text)} (at {f(x)} {f(y)} 0) {eff(size,False,align)}'+(')' if c else f' (uuid {q(uid())}))')
 return ''

# Split and deduplicate collinear conductors at every electrical contact.
def routed_sheet(sh):
 segments=[];contacts=set()
 for a in instances:
  if a['sheet']==sh:contacts.update(tuple(v) for v in a['pins'].values())
 for p in l['ports']:
  if p['sheet']==sh:contacts.add(tuple(p['at']))
 if sh==1:contacts.update([(335,135),(115,170)])
 for r in l['routes']:
  if r['sheet']!=sh:continue
  for a,b in zip(r['points'],r['points'][1:]):
   a=tuple(a);b=tuple(b)
   if a!=b:segments.append((r['net'],a,b));contacts.update([a,b])
 def on(p,a,b):return min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1])
 for n,a,b in segments:
  for N,c,d in segments:
   if a[0]==b[0] and c[1]==d[1]:
    pt=(a[0],c[1])
    if on(pt,a,b) and on(pt,c,d):
     assert n==N,('crossed nets',sh,n,N,pt)
     contacts.add(pt)
 edges=set()
 for n,a,b in segments:
  pts=sorted(p for p in contacts if on(p,a,b))
  for c,d in zip(pts,pts[1:]):edges.add((n,c,d))
 return sorted(edges)

refs=defaultdict(list)
for a in instances:
 points=list(a['pins'].values());a['center']=[round((min(p[j] for p in points)+max(p[j] for p in points))/10)*5 for j in (0,1)]
 refs[a['ref']].append(a)
def pin_type(r,p):
 a=byref[r];k=a['kind']
 if k=='OP':return 'output' if p in ('1','7') else 'power_in' if p in ('4','8') else 'input'
 if k=='PUMP':return 'power_in' if p in ('1','3','8') else 'power_out' if p=='5' else 'passive'
 return a['types'].get(p,'passive')
LIBS={}
for ref,units in refs.items():
 t=f'(symbol {q("rev410:"+ref)} (pin_names (offset 0) hide) (pin_numbers hide) (in_bom yes) (on_board yes) '+prop('Reference',ref,0,0)+prop('Value',byref[ref]['value'],0,0)
 for a in units:
  unit=a['unit'];c=a['center'];t+=f'(symbol {q(ref+"_"+str(unit)+"_1")} '
  t+=''.join(graphic(g,c) for g in a['art'])
  for p,pt in a['pins'].items():
   x,y=local(*pt,c)
   name=byref[ref]['names'].get(p,p)
   t+=f'(pin {pin_type(ref,p)} line (at {f(x)} {f(y)} 0) (length 0) (name {q(name)} {eff(1.0)}) (number {q(p)} {eff(1.0)}))'
  t+=')'
 t+=')';LIBS[ref]=t
# Source declarations follow the diode and negative-rail RC filter; no BOM parts.
for i in range(1,4):
 ref='#FLG0'+str(i)
 LIBS[ref]=f'(symbol {q("rev410:"+ref)} (pin_names (offset 0) hide) (pin_numbers hide) (in_bom no) (on_board no) '+prop('Reference',ref,0,0)+prop('Value','PWR_FLAG',0,0)+f'(symbol {q(ref+"_1_1")} (pin power_out line (at 0 0 90) (length 0) (name "pwr" {eff(1,True)}) (number "1" {eff(1,True)}))))'
root=uid();sheetids={i:uid() for i in range(1,9)}
def header(title,id):return f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(id)}) (paper "A4") (title_block (title {q(title)}) (rev "4.10") (company "Rodrigues M. Lima"))'
rootdoc=header('Pedaleira Digital - Rev 4.10',root)+'(lib_symbols)(sheet_instances (path "/" (page "0")))'
for sh in range(1,9):
 su=sheetids[sh];title=l['pages'][str(sh)];sx=30+((sh-1)%3)*80;sy=35+((sh-1)//3)*45
 rootdoc+=f'(sheet (at {sx} {sy}) (size 65 25) (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0)) (uuid {q(su)}) '+prop('Sheetname',title,sx,sy-2)+prop('Sheetfile',f'folha_{sh}.kicad_sch',sx,sy+28)+f'(instances (project {q(project)} (path {q("/"+root)} (page {q(sh)})))))'
 units=[a for a in instances if a['sheet']==sh];rnames={a['ref'] for a in units}
 if sh==1:rnames|={'#FLG01','#FLG02','#FLG03'}
 doc=header(title,uid())+'(lib_symbols '+''.join(LIBS[r] for r in sorted(rnames))+')'
 # Fixed art, titles, grounds, rail bars and printed net names are copied from the PDF layout.
 for a in l['decorations']:
  if a['sheet']!=sh:continue
  if a['kind']!='junction':doc+=graphic(a)
 for a in units:
  r=a['ref'];unit=a['unit'];x,y=xy(*a['center'])
  doc+=f'(symbol (lib_id {q("rev410:"+r)}) (at {f(x)} {f(y)} 0) (unit {unit}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {q(uid())}) '+prop('Reference',r,x,y)+prop('Value',byref[r]['value'],x,y)+prop('Footprint',byref[r].get('footprint',''),x,y)+prop('Package_note',byref[r]['package'],x,y)
  doc+=''.join(f'(pin {q(p)} (uuid {q(uid())}))' for p in a['pins'])
  doc+=f'(instances (project {q(project)} (path {q("/"+root+"/"+su)} (reference {q(r)}) (unit {unit})))))'
  for p,pt in a['pins'].items():
   if byref[r]['pins'][p] is None:
    xx,yy=xy(*pt);doc+=f'(no_connect (at {f(xx)} {f(yy)}) (uuid {q(uid())}))'
 edges=routed_sheet(sh);degree=defaultdict(int)
 for net,a,b in edges:
  degree[a]+=1;degree[b]+=1
  doc+='(wire (pts '+point(*xy(*a))+' '+point(*xy(*b))+f') (stroke (width 0) (type default)) (uuid {q(uid())}))'
 for pt,d in degree.items():
  if d>=3:
   x,y=xy(*pt);doc+=f'(junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid {q(uid())}))'
 # Global names occur at real inter-sheet ports, never at every physical pin.
 portnets=set();seen=set()
 for p in l['ports']:
  if p['sheet']!=sh or p['net'] is None:continue
  net=p['net'];pt=tuple(p['at'])
  if (net,pt) in seen:continue
  seen.add((net,pt));portnets.add(net);xx,yy=xy(*pt)
  # Actual visible inter-sheet connection marker.
  pages={a['sheet'] for a in instances for pin in a['pins'] if byref[a['ref']]['pins'][pin]==net}
  if len(pages)>1:
   doc+=f'(global_label {q(net)} (shape passive) (at {f(xx)} {f(yy)} 0) {eff(.85)} (uuid {q(uid())}) '+prop('Intersheetrefs','${INTERSHEET_REFS}',xx,yy)+')'
  else:doc+=f'(label {q(net)} (at {f(xx)} {f(yy)} 0) {eff(.85)} (uuid {q(uid())}))'

 internal={byref[a['ref']]['pins'][p] for a in units for p in a['pins'] if byref[a['ref']]['pins'][p] is not None}-portnets
 for net in sorted(internal):
  pt=next(tuple(pt) for a in units for p,pt in a['pins'].items() if byref[a['ref']]['pins'][p]==net);xx,yy=xy(*pt)
  doc+=f'(label {q(net)} (at {f(xx)} {f(yy)} 0) {eff(.85)} (uuid {q(uid())}))'
 if sh==1:
  points={1:(335,135),2:(115,170),3:(770,260)}
  for i,pt in enumerate(points.values(),1):
   r='#FLG0'+str(i);x,y=xy(*pt)
   doc+=f'(symbol (lib_id {q("rev410:"+r)}) (at {f(x)} {f(y)} 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {q(uid())}) '+prop('Reference',r,x,y)+prop('Value','PWR_FLAG',x,y)+f'(instances (project {q(project)} (path {q("/"+root+"/"+su)} (reference {q(r)}) (unit 1)))))'
 (D/f'folha_{sh}.kicad_sch').write_text(doc+')')
(D/f'{project}.kicad_sch').write_text(rootdoc+')')
(D/f'{project}.kicad_pro').write_text(json.dumps({'meta':{'filename':project+'.kicad_pro','version':1},'erc':{'erc_exclusions':[],'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2))
(D/'rev410.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")'+''.join(v.replace(q('rev410:'+r),q(r),1) for r,v in LIBS.items())+')')
(D/'sym-lib-table').write_text('(sym_lib_table (lib (name "rev410") (type "KiCad") (uri "${KIPRJMOD}/rev410.kicad_sym") (options "") (descr "Rev4.10 - connected functional schematic")))')
shutil.copytree(Path(__file__).with_name('Package_SO.pretty'),D/'Package_SO.pretty',dirs_exist_ok=True)
(D/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Package_SO") (type "KiCad") (uri "${KIPRJMOD}/Package_SO.pretty") (options "") (descr "U6 footprint from official KiCad library")))')
print('KiCad: functional blocks and connected circuits exported.')
