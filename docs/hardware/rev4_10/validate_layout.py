"""Check visible conductors and real ports independently of CAD label naming."""
from pathlib import Path
from collections import defaultdict
import json,os
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(os.environ.get('PEDALEIRA_REV410_OUT',str(ROOT/'output/REV410_ENTREGA')))
m=json.loads((OUT/'circuito_rev4_10.json').read_text())
l=json.loads((OUT/'diagram_layout.json').read_text())
parts={a['ref']:a for a in m['components']};parent={}
def find(a):
 parent.setdefault(a,a)
 if parent[a]!=a:parent[a]=find(parent[a])
 return parent[a]
def join(a,b):parent[find(a)]=find(b)
def on(p,a,b):
 return min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1]) and (a[0]==b[0]==p[0] or a[1]==b[1]==p[1])
segments=[];points=defaultdict(set);pins={}
for a in l['instances']:
 for p,pt in a['pins'].items():
  key=(a['ref'],p);assert key not in pins
  node=(a['sheet'],*pt);pins[key]=node;points[a['sheet']].add(tuple(pt));find(node)
for r in l['routes']:
 for a,b in zip(r['points'],r['points'][1:]):
  a=tuple(a);b=tuple(b)
  assert a[0]==b[0] or a[1]==b[1]
  if a!=b:segments.append((r['sheet'],r['net'],a,b));points[r['sheet']].update([a,b])
for p in l['ports']:
 if p['net'] is not None:
  points[p['sheet']].add(tuple(p['at']));join((p['sheet'],*p['at']),('PORT',p['net']))
for sh,n,a,b in segments:
 for SH,N,c,d in segments:
  if sh!=SH:continue
  candidates=[a,b,c,d]
  if a[0]==b[0] and c[1]==d[1]:candidates.append((a[0],c[1]))
  for pt in candidates:
   if on(pt,a,b) and on(pt,c,d):
    assert n==N,('crossed nets',sh,n,N,pt)
    points[sh].add(pt)
for sh,n,a,b in segments:
 pts=sorted(p for p in points[sh] if on(p,a,b))
 for c,d in zip(pts,pts[1:]):join((sh,*c),(sh,*d))
expected=defaultdict(set);actual=defaultdict(set)
for ref,a in parts.items():
 for p,net in a['pins'].items():
  assert (ref,p) in pins
  if net is not None:
   expected[net].add((ref,p));actual[find(pins[(ref,p)])].add((ref,p))
  else:assert not any(on(pins[(ref,p)][1:],c,d) for sh,n,c,d in segments if sh==pins[(ref,p)][0])
assert {frozenset(v) for v in actual.values()}=={frozenset(v) for v in expected.values()},'Visible drawing differs from electrical model'
r={'all_physical_pins':len(pins),'visible_connected_nets':len(actual),'cross_net_intersections':0,'visible_routes_and_ports_equal_model':True}
(OUT/'VALIDACAO_LAYOUT.json').write_text(json.dumps(r,indent=2));print(r)
