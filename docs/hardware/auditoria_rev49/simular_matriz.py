"""Independent excitations, actual rev49 pin model and TI macro; no codec transistor model.
Run with bundled Python; outputs relative to repository. No revision49 file mutated.
"""
from pathlib import Path
import json,subprocess,gzip,csv,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3]; D=ROOT/'output/auditoria_rev49/SIMULACOES';D.mkdir(parents=True,exist_ok=True)
M=json.loads((ROOT/'output/rev4_9/circuito_rev4_9.json').read_text());P={a['ref']:a for a in M['components']}
N={n:('0' if n=='GND' else 'n'+str(i)) for i,n in enumerate(sorted({n for a in P.values() for n in a['pins'].values() if n}))};N['+5V']='v5'
(D/'node_map.json').write_text(json.dumps(N,indent=2));(D/'TL072_TI.301').write_bytes((ROOT/'output/rev4_9/simulacao/TL072_TI.301').read_bytes());(D/'TL072_TI_original.301').write_bytes((ROOT/'output/rev4_9/simulacao/TL072_TI_original.301').read_bytes())
W=['HI_Z','IN_BUF','DRV_P','DRV_N','AINA_P','AINA_N','DAC_P','DAC_N','DAC_BUF','JACK_OUT','VREF_OP','ADC_BIAS','VCOM']
val=lambda v:v.replace('bipolar','').replace('Mohm','Meg').replace('ohm','').replace('F','').replace(' ','')
def deck(tag,path='adc',raw=11.3,hz=1000,amp=.5,load=100000,ac=False):
 l=[tag,'.include TL072_TI.301','.options reltol=1e-5 abstol=1e-11',f'Vrail {N["+RAW"]} 0 {raw}','V5 v5 0 5',f'Vcom0 vc0 0 2.4',f'Rcom vc0 {N["VCOM"]} 25k']
 a=amp if path=='adc' else 0;dp=amp if path=='dac' else 0
 l += [f'Vg {N["JACK_IN"]} 0 DC 0 AC {1 if path=="adc" else 0} SIN(0 {a} {hz})',f'Vdp {N["AOUTA_P"]} 0 DC 2.5 AC {.5 if path=="dac" else 0} SIN(2.5 {dp/2} {hz})',f'Vdn {N["AOUTA_N"]} 0 DC 2.5 AC {.5 if path=="dac" else 0} 180 SIN(2.5 {-dp/2} {hz})','.model D4148 D(Is=2.5n N=1.75 Rs=.6 Cjo=4p Tt=4n)','.model DBAT85 D(Is=200n N=1.05 Rs=2 Cjo=10p)']
 for a in P.values():
  if (a['sheet'] in (2,4) and a['kind'] in ('R','C','CB','CP','D')) or a['ref'] in ['R22','R23','C38','C39','C14','C15','R10','C34','R27','R28','C40','C41']:
   l.append(a['ref']+' '+' '.join(N[a['pins'][p]] for p in ('1','2'))+' '+(('DBAT85' if a['value']=='BAT85' else 'D4148') if a['kind']=='D' else val(a['value'])))
 for r,u,ps in [('U1','A',('3','2','1')),('U1','B',('5','6','7')),('U3','A',('3','2','1')),('U3','B',('5','6','7'))]:
  l.append('X'+r+u+' '+' '.join(N[P[r]['pins'][p]] for p in (*ps[:2],'8','4',ps[2]))+' TL072')
 l += [f'RADC {N["AINA_P"]} {N["AINA_N"]} 37k',f'Rload {N["JACK_OUT"]} 0 {load}', '.control','set wr_vecnames','set wr_singlescale','op','print '+' '.join('v('+N[n]+')' for n in W)]
 if ac:l += ['ac dec 100 1 30Meg','wrdata '+tag+'.txt '+' '.join('v('+N[n]+')' for n in W)]
 else:l += [f'tran {1/(hz*200):.12g} {12/hz:.12g}', 'wrdata '+tag+'.txt '+' '.join('v('+N[n]+')' for n in W)]
 l+=['quit','.endc','.end'];(D/(tag+'.cir')).write_text('\n'.join(l)+'\n')
 p=subprocess.run(['/tmp/pedaleira-local/usr/bin/ngspice','-b',tag+'.cir'],cwd=D,capture_output=True,text=True);(D/(tag+'.log')).write_text(p.stdout+'\n'+p.stderr)
 f=D/(tag+'.txt')
 if p.returncode or not f.exists():return None
 x=np.loadtxt(f,skiprows=1)
 with gzip.open(str(f)+'.gz','wt') as g:g.write(f.read_text())
 f.unlink();return x
rows=[];acs={};start=time.time()
for path in ['adc','dac']:
 for raw in [10.5,11.3,12.6]:
  for hz in [100,1000,5000,10000,20000]:
   for amp in ([.05,.1,.25,.5,1] if path=='adc' else [.05,.1,.25,.5,1,2.65125]):
    tag=f'{path}_r{raw}_f{hz}_a{amp}';x=deck(tag,path,raw,hz,amp);r=dict(case=tag,path=path,raw_V=raw,hz=hz,stimulus_peak_V=amp,stimulus_definition='guitar single-ended' if path=='adc' else 'DAC differential',nominal_permitted=amp<=.5 if path=='adc' else True,status='OK' if x is not None else 'FAILED')
    if x is not None:
     q=x[x[:,0]>6/hz];t=q[:,0];y=q[:,W.index('AINA_P')+1]-q[:,W.index('AINA_N')+1] if path=='adc' else q[:,W.index('JACK_OUT')+1]
     # LS harmonic fit on adaptive timesteps; not FFT on uneven time grid.
     A=np.column_stack([np.ones_like(t)]+[f(2*np.pi*hz*k*t) for k in range(1,8) for f in [np.sin,np.cos]])
     coef=np.linalg.lstsq(A,y,rcond=None)[0];h=np.hypot(coef[1::2],coef[2::2]);r.update(offset_V=float(coef[0]),fundamental_peak_V=float(h[0]),gain=float(h[0]/amp),THD_2to7_percent=float(100*np.linalg.norm(h[1:])/h[0]),min_V=float(y.min()),max_V=float(y.max()),asymmetry_V=float(y.max()+y.min()-2*coef[0]))
     for n in W:r[n+'_min']=float(q[:,W.index(n)+1].min());r[n+'_max']=float(q[:,W.index(n)+1].max())
    rows.append(r)
 print(path,len(rows),'cases',round(time.time()-start,1),'s',flush=True)
 for load in [1000,10000,100000,1000000]:
  tag=f'ac_{path}_load{load}';x=deck(tag,path,load=load,ac=True)
  if x is not None:
   f=x[:,0];v=lambda n:x[:,1+2*W.index(n)]+1j*x[:,2+2*W.index(n)];y=v('AINA_P')-v('AINA_N') if path=='adc' else v('JACK_OUT');acs[tag]={str(h):dict(gain_dB=float(np.interp(np.log10(h),np.log10(f),20*np.log10(np.maximum(abs(y),1e-30)))),phase_deg=float(np.interp(np.log10(h),np.log10(f),np.unwrap(np.angle(y))*180/np.pi))) for h in [20,1000,20000,6144000]}
   plt.semilogx(f,20*np.log10(np.maximum(abs(y),1e-30)),label=f'{path}, {load/1000:g}k load')
keys=list(dict.fromkeys(k for r in rows for k in r))
with (D/'matriz_transientes.csv').open('w',newline='') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
(D/'ac_resultados.json').write_text(json.dumps(acs,indent=2));(D/'resumo.json').write_text(json.dumps(dict(cases=len(rows),failed=sum(r['status']!='OK' for r in rows),elapsed_s=time.time()-start,physical_tests=False,notes=['ADC 1Vpk is overload exploration, outside declared nominal .5Vpk','DAC amplitude is differential peak: each leg half this value','TI macro characterized at +/-15V; rail/common-mode guarantees NOT proven','Codec ADC is 37k resistor only; no switched-cap, digital filtering or THD model','Diodes generic, not guaranteed worstcase manufacturer models','THD is harmonic fit of model, not real hardware THD','DC operating point precharges references; matrix does not simulate turn-on']),indent=2))
plt.xlim(10,1e7);plt.ylim(-85,10);plt.xlabel('Frequency / Hz');plt.ylabel('Transfer / dB');plt.grid();plt.legend(fontsize=6);plt.tight_layout();plt.savefig(D/'resposta_ac.png',dpi=150)
print('DONE',len(rows),flush=True)
