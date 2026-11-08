"""Power envelopes, explicit bounded fallback. Not a TL072 startup qualification."""
from pathlib import Path
import subprocess,json,gzip
import numpy as np
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'output/auditoria_rev49/SIMULACOES';OLD=ROOT/'output/rev4_9/simulacao'
(D/'OP_STARTUP.lib').write_bytes((OLD/'OP_STARTUP.lib').read_bytes())
s=(OLD/'startup.cir').read_text();res=[];N=json.loads((D/'node_map.json').read_text());names=['ADC_BIAS','VREF_OP','IN_BUF','DRV_P','DRV_N','AINA_P','AINA_N','VCOM','DAC_BUF','JACK_OUT']
for tag,raw,t5 in [('nominal',11.3,.005),('min',10.5,.005),('max',12.6,.005),('5V_atrasado',12.6,.5)]:
 for macro in ['bounded','TI']:
  name='startup_'+tag+'_'+macro
  z=s.replace('startup_tran.txt',name+'.txt').replace('5m 11.3 4 11.3',f'5m {raw} 4 {raw}').replace('5m 5 4 5',f'{t5} 5 4 5')
  if macro=='TI':z=z.replace('.include OP_STARTUP.lib','.include TL072_TI.301')
  (D/(name+'.cir')).write_text(z);p=subprocess.run(['/tmp/pedaleira-local/usr/bin/ngspice','-b',name+'.cir'],cwd=D,capture_output=True,text=True,timeout=90);(D/(name+'.log')).write_text(p.stdout+'\n'+p.stderr)
  f=D/(name+'.txt');r=dict(case=name,model=macro,returncode=p.returncode,raw=raw,ramp5V_s=t5,qualified=False)
  if f.exists():
   x=np.loadtxt(f,skiprows=1);r['last_time_s']=float(x[-1,0]);r['complete']=bool(x[-1,0]>=7.99);r['nodes']={n:dict(min=float(x[:,i].min()),max=float(x[:,i].max())) for i,n in enumerate(names,1)}
   r['reference_level_at_3p9s_V']={n:float(x[np.argmin(abs(x[:,0]-3.9)),i]) for i,n in enumerate(names,1) if n in ['ADC_BIAS','VREF_OP']}
   with gzip.open(str(f)+'.gz','wt') as g:g.write(f.read_text())
   f.unlink()
  else:r['complete']=False
  res.append(r);print(name,r['complete'],flush=True)
(D/'partida_resultados.json').write_text(json.dumps(res,indent=2))
