from pathlib import Path
import numpy as np,json,csv,itertools
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'output/auditoria_rev49/VALIDACAO'
# Deliberately conservative commercial cap ranges. Exact purchase series unconfirmed.
params={'R_adc_fraction':.01,'R_load_bias_fraction':.001,'C_coupling_fraction':.20,'C_input_fraction':.10,'C_C0G_fraction':.05,'R_output_fraction':.01,'C_output_filter_fraction':.05,'C_reference_fraction':.20,'temperature_K':300,'seed':4910}
(O/'tolerancias_parametros.json').write_text(json.dumps(params,indent=2))
def hadc(f,r,c,cd,rb):
 w=2j*np.pi*f;z=1/(1/37000+1/(2*rb)+w*cd)
 return 2*z/(2*r+2/(w*c)+z)
def hout(f,r,c,cout,load):
 s=2j*np.pi*f;zout=1/(1/load+1/1e6)+1/(s*cout)
 A=np.array([[2/r+s*c,-1/r],[-1/r,1/r+s*c+1/zout]],complex)
 v=np.linalg.solve(A,[1/r,0]);return v[1]*(1/(1/load+1/1e6))/zout
rows=[]
for sr,sc,sd,sb in itertools.product([-1,1],repeat=4):
 r=1500*(1+.01*sr);c=10e-6*(1+.2*sc);cd=730e-12*(1+.05*sd);rb=1e5*(1+.001*sb)
 rows.append(dict(kind='ADC',corner=f'{sr},{sc},{sd},{sb}',gain20=abs(hadc(20,r,c,cd,rb)),gain1k=abs(hadc(1000,r,c,cd,rb)),gain20k=abs(hadc(20000,r,c,cd,rb)),pole_loaded_Hz=(1/37000+1/(2*rb)+1/(2*r))/(2*np.pi*cd)))
for sr,sc,so in itertools.product([-1,1],repeat=3):
 for load in [1e3,1e4,1e5,1e6]:
  r=220*(1+.01*sr);c=2.2e-9*(1+.05*sc);co=10e-6*(1+.2*so)
  rows.append(dict(kind='OUT',corner=f'{sr},{sc},{so}',load=load,gain20=abs(hout(20,r,c,co,load)),gain1k=abs(hout(1000,r,c,co,load)),gain20k=abs(hout(20000,r,c,co,load)),pole_loaded_Hz=None))
with (O/'capacitores_cantos.csv').open('w',newline='') as f:w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
rng=np.random.default_rng(4910);x=rng.uniform(-1,1,(10000,4));mc=[abs(hadc(20000,1500*(1+.01*a),10e-6*(1+.2*b),730e-12*(1+.05*c),1e5*(1+.001*d))) for a,b,c,d in x]
r={'method':'Analytical complex impedances and scipy root solving; not SPICE','ADC_20k_gain_corner_min_max':[min(r['gain20k'] for r in rows if r['kind']=='ADC'),max(r['gain20k'] for r in rows if r['kind']=='ADC')],'ADC_MC_20k_gain_percentiles':np.percentile(mc,[0,1,50,99,100]).tolist(),'output_unloaded_3dB_Hz':brentq(lambda f:abs(hout(f,220,2.2e-9,10e-6,1e20))-2**-.5,1e4,1e6),'VREF_tau_max_s':1100*1.01*470e-6*1.2,'ADC_BIAS_tau_max_s':6240*1.001*100e-6*1.2,'ADC_BIAS_hypothetical_DC_current_uA_to_shift_mV':{str(i):i*6.24 for i in [1,8,10]},'resistor_1M_thermal_noise_nV_sqrtHz':float(np.sqrt(4*1.380649e-23*300*1e6)*1e9),'limits':['ADC37k purely resistive; does not model switched capacitor dynamics','Capacitor purchased tolerances not confirmed; ranges are explicit assumptions','Hypothetical leakage current sensitivity is NOT codec input current specification','Common/coupled tolerances intentionally bounded; independent resistor mismatch handled in analogico_cantos.csv']}
(O/'capacitores_resultados.json').write_text(json.dumps(r,indent=2))
# Purchasing errata: same topology and values, no revision410 declaration.
m=json.loads((ROOT/'docs/hardware/rev4_9/circuito_rev4_9.json').read_text());orig=json.loads(json.dumps(m));changes=[]
for a in m['components']:
 before=json.loads(json.dumps(a))
 if a['ref'] in ['R1','R2','R7','R8','R19']:a['package']=a['package'].replace('1%','0,1%')
 if a['ref']=='R8':a['function']=a['function'].replace('ganho diferencial 1','ganho diferencial 0,499')
 if a['ref']=='U5':a['package']='TO-220; fabricante e pinagem CW7805 a confirmar'
 if a['ref']=='U3':a['value']='TL072';a['note']+=' Sufixo/fabricante do exemplar a confirmar; sem equivalência automática ao TI CP.'
 if a['value']=='BAT85':a['package']='Axial; confirmar fabricante: Nexperia DO-34/SOD68'
 assert a['pins']==before['pins']
 for k in a:
  if a[k]!=before[k]:changes.append(dict(ref=a['ref'],field=k,before=before[k],after=a[k]))
(O/'circuito_rev49_errata_documental.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));(O/'errata_documental.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
with (O/'BOM_REV49_ERRATA.csv').open('w',newline='',encoding='utf-8-sig') as f:
 fields=['ref','kind','value','package','function','min_spec','note'];w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(m['components'])
assert all(a['pins']==b['pins'] for a,b in zip(m['components'],orig['components']))
print(json.dumps(r,indent=2));print('errata fields',len(changes))
