from pathlib import Path
import shutil,json,hashlib,zipfile,subprocess,difflib
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'output/auditoria_rev49'
for group in ['FONTES_EXECUTAVEIS','REFERENCIA_REV49','FIRMWARE_CORRIGIDO']:(D/group).mkdir(exist_ok=True)
for source in ['docs/hardware/auditoria_rev49','tests/embedded_host','tests/hardware_audit']:
 dest=D/'FONTES_EXECUTAVEIS'/source
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(ROOT/source,dest,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
for name in ['pedaleira_digital_rev4_9.pdf','circuito_rev4_9.json','BOM_rev4_9.csv','CONEXOES_COMPLETAS_REV49.csv','diagram_layout.json']:
 shutil.copy2(ROOT/'output/rev4_9'/name,D/'REFERENCIA_REV49'/name)
shutil.copytree(ROOT/'output/rev4_9/kicad',D/'REFERENCIA_REV49/kicad',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.kicad_prl','*.lck'))
paths=['firmware/stm32/Core/Inc/Bsp.hpp','firmware/stm32/Core/Inc/InterMcuUart.hpp','firmware/stm32/Core/Inc/UartRxRing.hpp','firmware/stm32/Core/Inc/MasterMuteGate.hpp','firmware/stm32/Core/Inc/Cs4272I2cTiming.hpp','firmware/stm32/Core/Src/Bsp.cpp','firmware/stm32/Core/Src/InterMcuUart.cpp','firmware/stm32/Core/Src/Cs4272.cpp','firmware/stm32/Core/Src/main.cpp']
patch=[]
for name in paths:
 dest=D/'FIRMWARE_CORRIGIDO'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
 baseline=ROOT/'output/rev4_9/firmware_corrigido'/name.removeprefix('firmware/')
 if baseline.exists():old=baseline.read_text()
 else:
  p=subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,capture_output=True,text=True);old=p.stdout if p.returncode==0 else ''
 patch+=difflib.unified_diff(old.splitlines(True),(ROOT/name).read_text().splitlines(True),fromfile='a/'+name if old else '/dev/null',tofile='b/'+name)
(D/'VALIDACAO/firmware_correcao_sobre_rev49.patch').write_text(''.join(patch))
# Documentation changes are explicitly separate from hardware.
for name in ['docs/code/protocolo_comunicacao.md','.agents/skills/inter-mcu-protocol/SKILL.md','tests/test_stm32_cpp_dsp_quality.py','docs/hardware/rev4_9/test_dsp_host.cpp']:
 dest=D/'FONTES_EXECUTAVEIS'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json' and '__pycache__' not in p.parts}
(D/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2))
zpath=ROOT/'output/auditoria_rev49_completa.zip'
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,6) as z:
 for name in list(manifest)+['MANIFEST_SHA256.json']:z.write(D/name,'auditoria_rev49/'+name)
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 for name,digest in manifest.items():assert hashlib.sha256(z.read('auditoria_rev49/'+name)).hexdigest()==digest
print(len(manifest),'files; zip',zpath.stat().st_size,'bytes; CRC and all hashes OK')
