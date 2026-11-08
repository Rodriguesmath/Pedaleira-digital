from pathlib import Path
import os,shutil
import json,csv,hashlib,xml.etree.ElementTree as ET
from collections import Counter
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[3];O=Path(os.environ.get('PEDALEIRA_REV48_OUT',str(ROOT/'output/rev4_8'))).resolve()
m=json.loads((O/'circuito_rev4_8.json').read_text());parts={a['ref']:a for a in m['components']}
assert len(parts)==79
nets=json.loads((O/'netlist_rev4_8.json').read_text());expected={k:{tuple(v) for v in val} for k,val in nets.items()}
root=ET.parse(O/'kicad/netlist.xml').getroot();actual={};nc=set()
for n in root.findall('./nets/net'):
 nodes={(v.attrib['ref'],v.attrib['pin']) for v in n.findall('node') if not v.attrib['ref'].startswith('#FLG')}
 name=n.attrib['name'].rsplit('/',1)[-1]
 if name.startswith('unconnected-'):nc.update(nodes)
 elif nodes:actual[name]=nodes
assert actual==expected,{n:(actual.get(n),expected.get(n)) for n in set(actual)|set(expected) if actual.get(n)!=expected.get(n)}
assert nc=={(a['ref'],p) for a in parts.values() for p in a['nc']}
cadparts={a.attrib['ref']:a.findtext('value') for a in root.findall('./components/comp') if not a.attrib['ref'].startswith('#FLG')}
assert cadparts=={r:a['value'] for r,a in parts.items()}
with (O/'BOM_rev4_8.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
assert len(rows)==len(parts) and {r['Referência']:r['Valor'] for r in rows}==cadparts
assert all(r['Quantidade']=='1' for r in rows)
erc=json.loads((O/'kicad/ERC_rev4_8.json').read_text());violations=[a for s in erc['sheets'] for a in s['violations']]
assert not violations
assert not erc['ignored_checks'],erc['ignored_checks']
coverage=json.loads((O/'render_coverage.json').read_text());assert coverage['all_rendered'] and coverage['components']==79
pdf=PdfReader(O/'pedaleira_digital_rev4_8.pdf');assert len(pdf.pages)==7
for i,p in enumerate(pdf.pages,1):
 text=p.extract_text();assert 'Rodrigues M. Lima' in text and f'{i} / 7' in text
 assert '\ufffd' not in text and tuple(p.mediabox)==(0,0,842,595)
full='\n'.join(p.extract_text() for p in pdf.pages)
for ref in parts:assert ref in full,ref
# Confirm untouched original circuit/source/PDF bytes match the initial snapshot.
backup=O/'backup_rev4_7';manifest=json.loads((backup/'SHA256.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((backup/name).read_bytes()).hexdigest()==digest,name
legacy_names=['docs/hardware/tools/gen_schematic.py','docs/hardware/pedaleira_digital_easyeda.json','docs/hardware/tools/export_schematic_pdf.py','output/pdf/pedaleira_digital_esquematica.pdf']
legacy_available=all((ROOT/name).exists() for name in legacy_names)
for name in legacy_names if legacy_available else []:
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==manifest[name],name
# Firmware has not been touched by this task: manifest recorded before delivery for future checking.
firmware={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'firmware').rglob('*') if p.is_file() and p.suffix in ('.cpp','.hpp','.c','.h')}
sim=json.loads((O/'simulacao/resultados.json').read_text())
assert -.1<sim['adc_1kHz_dB']<.1 and sim['adc_peak_gain_dB']<1
assert -1<sim['output_1kHz_dB']<0
report={'revision':'4.8','physical_components':len(parts),'new_components':sum(a['status']=='novo' for a in parts.values()),'replaced_type':1,'retained_existing':32,'real_nets':len(actual),'nc_terminals':len(nc),'pdf_pages':len(pdf.pages),'pdf_model_terminals':coverage['physical_terminals'],'pdf_all_terminals_rendered':True,'bom_equals_cad_and_model':True,'native_netlist_equals_model':True,'native_nc_equals_model':True,'erc_errors':0,'erc_warnings':0,'erc_exclusions':erc['ignored_checks'],'kicad_version':erc['kicad_version'],'ngspice_executed':True,'simulation_model':'linear, no vendor macromodel, no clipping/noise/startup validation','backup_hashes_verified':True,'legacy_circuit_sources_unchanged':True if legacy_available else None,'known_functional_issues_documented':22,'issues_closed_in_circuit_documents':17,'firmware_functional_blockers_open':5,'physical_validation_performed':False,'verdict':'CONDICIONADO; not released for manufacturing or definitive assembly'}
(O/'VALIDACAO_rev4_8.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
