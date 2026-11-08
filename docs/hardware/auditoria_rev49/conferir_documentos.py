from pathlib import Path
import json,xml.etree.ElementTree as ET,re,hashlib
import pymupdf as fitz
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'output/auditoria_rev49/VALIDACAO';M=json.loads((ROOT/'output/rev4_9/circuito_rev4_9.json').read_text());P={a['ref']:a for a in M['components']};doc=fitz.open(ROOT/'output/rev4_9/pedaleira_digital_rev4_9.pdf');assert len(doc)==7
pages=[]
for i,p in enumerate(doc,1):
 text=p.get_text();(O/f'folha_{i}_texto.txt').write_text(text)
 p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(O/f'folha_{i}.png')
 refs=set(re.findall(r'(?<![A-Z0-9_])(?:R|C|D|U|SW|LED|J|P|TP)\d+[AB]?(?![A-Z0-9_])',text));expected={a['ref'] for a in P.values() if a['sheet']==i};missing={r for r in expected if not re.search(r'(?<![A-Z0-9_])'+re.escape(r)+r'(?:[ABP])?(?![A-Z0-9_])',text)}
 pages.append(dict(sheet=i,size=list(p.rect),extracted_refs=sorted(refs),expected_model_refs=sorted(expected),missing_refs=sorted(missing),text_length=len(text)))
xml=ET.parse(O/'netlist_rev49.xml');actual={}
for net in xml.findall('.//nets/net'):
 name=net.get('name');name=name.rsplit('/',1)[-1]
 for node in net.findall('node'):actual[(node.get('ref'),node.get('pin'))]=name
mismatch=[]
for a in P.values():
 for p,n in a['pins'].items():
  if n and actual.get((a['ref'],p))!=n:mismatch.append(dict(ref=a['ref'],pin=p,expected=n,actual=actual.get((a['ref'],p))))
# Compare partition as well, including NC terminals that may be present as separate nets.
expected_nets={frozenset((a['ref'],p) for a in P.values() for p,n in a['pins'].items() if n==name) for name in {n for a in P.values() for n in a['pins'].values() if n}}
actual_nets={frozenset((n.get('ref'),n.get('pin')) for n in net.findall('node') if n.get('ref') in P and P[n.get('ref')]['pins'].get(n.get('pin')) is not None) for net in xml.findall('.//nets/net')};actual_nets.discard(frozenset())
r=dict(pages=pages,pdf_text_is_connectivity_proof=False,connected_pin_differences=mismatch,net_partitions_match=actual_nets==expected_nets,physical_components=len(P),connected_pins=sum(n is not None for a in P.values() for n in a['pins'].values()),nc_pins=[(a['ref'],p) for a in P.values() for p,n in a['pins'].items() if n is None],net_count=len(expected_nets))
(O/'confronto_pdf_cad.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='pages'},indent=2));assert not mismatch and r['net_partitions_match'];assert not any(p['missing_refs'] for p in pages)
# Overview only for navigation; individual pages retained at readable resolution.
from PIL import Image,ImageOps,ImageDraw
thumbs=[]
for i in range(1,8):
 im=Image.open(O/f'folha_{i}.png');im.thumbnail((842,595));thumbs.append(im)
canvas=Image.new('RGB',(842*2,595*4),'white')
for k,im in enumerate(thumbs):canvas.paste(im,((k%2)*842,(k//2)*595))
canvas.save(O/'sete_folhas.png')
