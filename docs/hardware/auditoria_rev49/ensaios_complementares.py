"""Reuse documented SPICE deck, inject DAC branches independently and test a 9V supply.
Does not import simular_matriz (which has top-level execution)."""
from pathlib import Path
import json,subprocess,gzip
import numpy as np
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'output/auditoria_rev49/SIMULACOES';N=json.loads((D/'node_map.json').read_text());W=['HI_Z','IN_BUF','DRV_P','DRV_N','AINA_P','AINA_N','DAC_P','DAC_N','DAC_BUF','JACK_OUT','VREF_OP','ADC_BIAS','VCOM'];results=[]
def run(tag,txt):
 (D/(tag+'.cir')).write_text(txt);p=subprocess.run(['/tmp/pedaleira-local/usr/bin/ngspice','-b',tag+'.cir'],cwd=D,capture_output=True,text=True);(D/(tag+'.log')).write_text(p.stdout+'\n'+p.stderr);f=D/(tag+'.txt');x=np.loadtxt(f,skiprows=1)
 with gzip.open(str(f)+'.gz','wt') as z:z.write(f.read_text())
 f.unlink();return x
base=(D/'ac_dac_load100000.cir').read_text()
for mode,ap,an in [('plus',1,0),('minus',0,1),('common',1,1)]:
 tag='DAC_'+mode;lines=base.replace('ac_dac_load100000.txt',tag+'.txt').splitlines()
 lines=[f'Vdp {N["AOUTA_P"]} 0 DC 2.5 AC {ap}' if l.startswith('Vdp ') else f'Vdn {N["AOUTA_N"]} 0 DC 2.5 AC {an}' if l.startswith('Vdn ') else l for l in lines];x=run(tag,'\n'.join(lines)+'\n');i=W.index('DAC_BUF');v=x[:,1+2*i]+1j*x[:,2+2*i];at=np.argmin(abs(x[:,0]-1000));results.append(dict(case=tag,f_Hz=float(x[at,0]),gain_real=float(v[at].real),gain_imag=float(v[at].imag),magnitude=float(abs(v[at]))))
base=(D/'adc_r10.5_f1000_a0.5.cir').read_text();tag='9V_heuristic_rejected';txt=base.replace('adc_r10.5_f1000_a0.5.txt',tag+'.txt').replace('0 10.5\n','0 7.65\n');x=run(tag,txt);q=x[x[:,0]>.006];results.append(dict(case=tag,physical_CM_requirement_pass=False,model_does_not_validate_common_mode=True,IN_BUF_min=float(q[:,W.index('IN_BUF')+1].min()),IN_BUF_max=float(q[:,W.index('IN_BUF')+1].max())))
# Sensitivity of nominal .5V guitar distortion to generic protection diodes. Not a removal recommendation.
for amp in [.5,1]:
 base=(D/f'adc_r11.3_f1000_a{amp}.cir').read_text();tag=f'clamp_sensitivity_no_guitar_diodes_a{amp}';txt='\n'.join(l for l in base.splitlines() if not l.startswith(('D6 ','D7 ','D13 ','D14 '))).replace(f'adc_r11.3_f1000_a{amp}.txt',tag+'.txt');x=run(tag,txt+'\n');q=x[x[:,0]>.006];t=q[:,0];y=q[:,W.index('AINA_P')+1]-q[:,W.index('AINA_N')+1];A=np.column_stack([np.ones_like(t)]+[f(2*np.pi*1000*k*t) for k in range(1,8) for f in [np.sin,np.cos]]);c=np.linalg.lstsq(A,y,rcond=None)[0];h=np.hypot(c[1::2],c[2::2]);results.append(dict(case=tag,gain=float(h[0]/amp),THD_percent=float(100*np.linalg.norm(h[1:])/h[0]),note='Generic diode sensitivity only, not permission to remove protections'))
(D/'complementares.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
