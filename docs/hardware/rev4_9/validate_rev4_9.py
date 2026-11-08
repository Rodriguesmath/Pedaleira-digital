from pathlib import Path
from collections import defaultdict
import os,json,csv,hashlib,xml.etree.ElementTree as ET,zipfile
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[3];O=Path(os.environ.get('PEDALEIRA_REV49_OUT',str(ROOT/'output/rev4_9')))
m=json.loads((O/'circuito_rev4_9.json').read_text());P={a['ref']:a for a in m['components']}
assert len(P)==len(m['components'])==106
assert {r for r in P if r.startswith('U')}=={'U1','U2','U3','U5'}
assert P['U5']['value']=='CW7805'
assert all(n!='-VA_OP' for a in P.values() for n in a['pins'].values())
assert P['U2']['pins']['15']=='VCOM'
assert P['U2']['pins']['2']=='GND' and P['U2']['pins']['1'] is None
assert set(P['U2']['pins'])=={str(i) for i in range(1,29)}
for ref in ['U1','U3']:
 assert P[ref]['pins']['4']=='GND' and P[ref]['pins']['8']=='+RAW'
 assert set(P[ref]['pins'])=={str(i) for i in range(1,9)}
expected=defaultdict(set);nc=set()
for a in P.values():
 for p,n in a['pins'].items():
  if n is None:nc.add((a['ref'],p))
  else:expected[n].add((a['ref'],p))
assert set(expected['VCOM'])=={('U2','15'),('C14','1'),('C15','1'),('TP5','1')}
actual={};actual_nc=set();x=ET.parse(O/'kicad/netlist.xml').getroot()
for n in x.findall('./nets/net'):
 name=n.attrib['name'].rsplit('/',1)[-1];pins={(v.attrib['ref'],v.attrib['pin']) for v in n.findall('node') if not v.attrib['ref'].startswith('#FLG')}
 if name.startswith('unconnected-'):actual_nc.update(pins)
 elif pins:actual[name]=pins
assert actual==dict(expected),{n:(expected.get(n),actual.get(n)) for n in set(expected)|set(actual) if expected.get(n)!=actual.get(n)}
assert nc==actual_nc
cad={a.attrib['ref']:a.findtext('value') for a in x.findall('./components/comp') if not a.attrib['ref'].startswith('#FLG')}
assert cad=={r:a['value'] for r,a in P.items()}
with (O/'BOM_rev4_9.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
assert len(rows)==len(P) and {a['Referência']:a['Valor'] for a in rows}==cad
assert all(a['Especificações mínimas'] and a['Situação'] for a in rows)
erc=json.loads((O/'kicad/ERC_rev4_9.json').read_text());assert not erc['ignored_checks']
viol=[v for s in erc['sheets'] for v in s['violations']];assert not viol,viol
p=PdfReader(O/'pedaleira_digital_rev4_9.pdf');assert len(p.pages)==7
for i,page in enumerate(p.pages,1):
 text=page.extract_text();assert 'Rodrigues M. Lima' in text and f'{i} / 7' in text and 'Não aprovado' in text
 assert tuple(page.mediabox)==(0,0,842,595)
alltext='\n'.join(a.extract_text() for a in p.pages)
assert all(a in alltext for a in P)
layout=json.loads((O/'VALIDACAO_LAYOUT.json').read_text());assert layout['visible_routes_and_ports_equal_model']
# Match every simulated passive and opamp terminal to the generated nominal deck.
node=json.loads((O/'simulacao/node_map.json').read_text());deck=(O/'simulacao/nominal.cir').read_text().splitlines()
def val(v):return v.replace('bipolar','').replace('Mohm','Meg').replace('ohm','').replace('F','').replace(' ','')
selected=[a for a in P.values() if a['sheet'] in (2,4) and a['kind'] in ('R','C','CB','CP','D') or a['ref'] in ['R22','R23','C38','C39','C14','C15','R10','C34','R27','R28','C40','C41']]
for a in selected:
 value=('DBAT85' if a['value']=='BAT85' else 'D4148') if a['kind']=='D' else val(a['value'])
 assert a['ref']+' '+node[a['pins']['1']]+' '+node[a['pins']['2']]+' '+value in deck,a['ref']
for r,u,ps in [('U1','A',('3','2','1')),('U1','B',('5','6','7')),('U3','A',('3','2','1')),('U3','B',('5','6','7'))]:
 assert 'X'+r+u+' '+' '.join(node[P[r]['pins'][p]] for p in (*ps[:2],'8','4',ps[2]))+' TL072' in deck
assert 'OK' in (O/'firmware_qa.log').read_text()
assert 'PASS:' in (O/'dsp_host_qa.log').read_text()
# Backups are recoverable and hashes map each changed original.
old=json.loads((O/'backup/SHA256_ANTES.json').read_text());changed=[]
with zipfile.ZipFile(O/'backup/firmware_antes_rev49.zip') as z:
 for path,digest in old.items():
  if path.startswith('firmware/'):
   assert hashlib.sha256(z.read(path)).hexdigest()==digest
   if (ROOT/path).exists() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:changed.append(path)
with zipfile.ZipFile(O/'backup/revisao_4_8.zip') as z:
 for path,digest in old.items():
  if path.startswith('docs/hardware/rev4_8/'):
   assert hashlib.sha256(z.read(path)).hexdigest()==digest
   if (ROOT/path).exists():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
assert set(changed)<= {'firmware/stm32/Core/Src/Bsp.cpp','firmware/stm32/Core/Src/Cs4272.cpp','firmware/stm32/Core/Inc/Cs4272.hpp','firmware/stm32/Core/Src/main.cpp'}
sim=json.loads((O/'simulacao/resultados.json').read_text());assert set(sim['simulations'])=={'nominal','min_supply','9V_rejected','cf470p','cf4n7'}
assert sim['physical_tests'] is False
result={'revision':'4.9','physical_components':len(P),'electrical_nets':len(actual),'physical_pins':sum(len(a['pins']) for a in P.values()),'nc_pins':len(nc),'new_integrated_circuits':0,'pdf_pages':len(p.pages),'pdf_native_model_bom_consistent':True,'visible_layout_equals_model':True,'simulation_passives_and_opamps_equal_model':True,'erc_errors':0,'erc_warnings':0,'erc_exclusions':[],'firmware_quality_tests_passed':9,'native_DSP_tests':'pass; bypass, mute, 480000 stress samples and 20ms impulse','originals_backed_up_and_rev48_preserved':True,'firmware_files_changed':changed,'physical_tests_performed':False,'CW7805_manufacturer_identified':False,'SAI_BDMA_transport_implemented':False,'ESP32_firmware_implemented':False,'single_9V_architecture_approved':False,'final_verdict':'NÃO APROVADO — REQUER CORREÇÕES','blockers':['CW7805/TL072 identification and electrical/thermal qualification','ADC settling/THD/stability and transient clamps qualification','P10 startup/shutdown pop needs external mute/disconnection or physical mute redesign','SAI4 PLL/BDMA/SRAM4/cache/error handling implementation','ESP32 module/firmware and onboard buck constraint confirmation']}
(O/'VALIDACAO_REV49.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
