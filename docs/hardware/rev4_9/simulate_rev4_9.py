from pathlib import Path
import json,os,subprocess,zipfile
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(os.environ.get('PEDALEIRA_REV49_OUT',str(ROOT/'output/rev4_9')));D=OUT/'simulacao';D.mkdir(exist_ok=True)
m=json.loads((OUT/'circuito_rev4_9.json').read_text());P={a['ref']:a for a in m['components']}
model=zipfile.ZipFile(OUT/'fontes/TL072_TI_PSpice.zip').read('TL072.301').decode('ascii').replace('\x1a','').replace('\r','')
(D/'TL072_TI_original.301').write_text(model)
model=model.replace('EGND 99  0 POLY(2) (3,0) (4,0) 0 .5 .5','BGND 99 0 V=.5*(V(3)+V(4))').replace('FB    7 99 POLY(5) VB VC VE VLP VLN 0 4.715E6 -5E6 5E6 5E6 -5E6','BFB 7 99 I=4.715E6*I(VB)-5E6*I(VC)+5E6*I(VE)+5E6*I(VLP)-5E6*I(VLN)')
(D/'TL072_TI.301').write_text('* POLY expressions converted algebraically to B sources for ngspice.\n'+model)
N={n:('0' if n=='GND' else 'n'+str(i)) for i,n in enumerate(sorted({n for a in P.values() for n in a['pins'].values() if n is not None}))}
N['+5V']='v5'
(D/'node_map.json').write_text(json.dumps(N,indent=2))
def node(n):return N[n]
def val(v):return v.replace('bipolar','').replace('Mohm','Meg').replace('ohm','').replace('F','').replace(' ','')
def run(tag,raw=11.3,cf=None,startup=False):
 lines=['Rev4.9 '+tag,'.include '+('OP_STARTUP.lib' if startup else 'TL072_TI.301'),'.options reltol=1e-5 abstol=1e-11']
 if startup:
  lines += [f'Vrail {node("+RAW")} 0 PWL(0 0 5m {raw} 4 {raw} 4.005 0)','V5 v5 0 PWL(0 0 5m 5 4 5 4.05 0)',f'Ecom vc0 0 v5 0 .48']
 else:
  lines += [f'Vrail {node("+RAW")} 0 {raw}','V5 v5 0 5','Vcom0 vc0 0 2.4']
 if startup:
  (D/'OP_STARTUP.lib').write_text('.subckt TL072 p n vp vn out\nEerr err 0 p n 200000\nRdom err dom 10k\nCdom dom 0 1.061u\nBlim src 0 V=max(V(vn),min(V(vp),V(dom)))\nRo src out 50\n.ends\n')
 lines += [f'Rcom vc0 {node("VCOM")} 25k',f'Vguitar {node("JACK_IN")} 0 DC 0 AC 1 SIN(0 .5 1000)',f'Vdp {node("AOUTA_P")} 0 DC 2.5 AC .5 SIN(2.5 1.2 1000)',f'Vdn {node("AOUTA_N")} 0 DC 2.5 AC .5 180 SIN(2.5 -1.2 1000)','.model D4148 D(Is=2.5n N=1.75 Rs=.6 Cjo=4p Tt=4n)','.model Dprot D(Is=1p N=1 Rs=1 Cjo=5p)','.model DBAT85 D(Is=200n N=1.05 Rs=2 Cjo=10p)']
 selected=[a for a in P.values() if a['sheet'] in (2,4) and a['kind'] in ('R','C','CB','CP','D') or a['ref'] in ['R22','R23','C38','C39','C14','C15','R10','C34','R27','R28','C40','C41']]
 for a in selected:
  pins=[node(a['pins'][p]) for p in ('1','2')]
  v=val(a['value'])
  if cf and a['ref'] in ['C18','C19']:v=cf
  lines.append(a['ref']+' '+' '.join(pins)+' '+(('DBAT85' if a['value']=='BAT85' else 'D4148') if a['kind']=='D' else v))
 for r,u,ps in [('U1','A',('3','2','1')),('U1','B',('5','6','7')),('U3','A',('3','2','1')),('U3','B',('5','6','7'))]:
  a=P[r];lines.append('X'+r+u+' '+' '.join(node(a['pins'][p]) for p in (*ps[:2],'8','4',ps[2]))+' TL072')
 if startup:
  lines=[v for v in lines if not v.startswith(('Vguitar ','Vdp ','Vdn '))]
  lines += [f'Vguitar {node("JACK_IN")} 0 0',f'Edp {node("AOUTA_P")} 0 v5 0 .5',f'Edn {node("AOUTA_N")} 0 v5 0 .5']
 lines += [f'RADC {node("AINA_P")} {node("AINA_N")} 37k',f'Rload {node("JACK_OUT")} 0 100k']
 for i,n in enumerate(['AINA_P','AINA_N']):
  lines += [f'Dhi{i} {node(n)} v5 Dprot',f'Dlo{i} 0 {node(n)} Dprot']
 wanted=['ADC_BIAS','VREF_OP','IN_BUF','DRV_P','DRV_N','AINA_P','AINA_N','VCOM','DAC_BUF','JACK_OUT']
 expr=' '.join('v('+node(n)+')' for n in wanted)
 lines+=['.control','set wr_vecnames','set wr_singlescale']
 if not startup:lines+=['op',f'print {expr}']
 if startup:lines+=['tran 100u 8 uic',f'wrdata {tag}_tran.txt {expr} i(V5)']
 else:lines+=['ac dec 120 1 30Meg',f'let adc = v({node("AINA_P")})-v({node("AINA_N")})',f'wrdata {tag}_ac.txt adc v({node("JACK_OUT")})','tran 1u 20m',f'wrdata {tag}_tran.txt {expr}']
 lines += ['quit','.endc','.end']
 (D/(tag+'.cir')).write_text('\n'.join(lines)+'\n')
 r=subprocess.run([os.environ.get('NGSPICE_BIN','/tmp/pedaleira-local/usr/bin/ngspice'),'-b',tag+'.cir'],cwd=D,text=True,capture_output=True)
 (D/(tag+'.log')).write_text(r.stdout+'\n'+r.stderr)
 assert r.returncode==0,(tag,r.stderr)
 return wanted
res={'model':'TI TL072.301, 1989 vendor macromodel characterized at ±15 V; +12 V results exploratory, not part qualification; codec/regulator/clamps approximated','physical_tests':False,'simulations':{}}
for tag,raw,cf in [('nominal',11.3,None),('min_supply',10.5,None),('9V_rejected',7.65,None),('cf470p',11.3,'470p'),('cf4n7',11.3,'4.7n')]:
 wanted=run(tag,raw,cf);v=np.loadtxt(D/(tag+'_ac.txt'),skiprows=1);f=v[:,0];a=v[:,1]+1j*v[:,2];o=v[:,3]+1j*v[:,4]
 db=lambda z:20*np.log10(np.maximum(np.abs(z),1e-20))
 at=lambda z,hz:float(np.interp(np.log10(hz),np.log10(f),db(z)))
 r={**{f'ADC_{hz:g}Hz_dB':at(a,hz) for hz in [20,1000,20000,6144000]},**{f'OUT_{hz:g}Hz_dB':at(o,hz) for hz in [20,1000,20000]},'ADC_peak_dB':float(max(db(a)))}
 t=np.loadtxt(D/(tag+'_tran.txt'),skiprows=1);mask=t[:,0]>.01
 for i,n in enumerate(wanted,1):r[n+'_min']=float(t[mask,i].min());r[n+'_max']=float(t[mask,i].max())
 res['simulations'][tag]=r
wanted=run('startup',startup=True)
t=np.loadtxt(D/'startup_tran.txt',skiprows=1)
res['startup_model']='Exploratory bounded one-pole model; TI macro failed at zero-rail startup. Not a vendor startup prediction.'
res['startup']={n:{'min':float(t[:,i].min()),'max':float(t[:,i].max())} for i,n in enumerate(wanted,1)}
(D/'resultados.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(2,1,figsize=(10,7))
for tag in ['nominal','cf470p','cf4n7']:
 v=np.loadtxt(D/(tag+'_ac.txt'),skiprows=1);ax[0].semilogx(v[:,0],20*np.log10(np.maximum(np.abs(v[:,1]+1j*v[:,2]),1e-20)),label=tag)
ax[0].set(xlim=(10,1e7),ylim=(-80,10),ylabel='ADC diferencial / guitarra (dB)');ax[0].legend();ax[0].grid(True)
for n in ['VREF_OP','AINA_P','AINA_N','VCOM']:
 i=wanted.index(n)+1;ax[1].plot(t[:,0],t[:,i],label=n)
ax[1].set(xlim=(0,8),xlabel='Tempo (s)',ylabel='Partida exploratória (V)');ax[1].legend();ax[1].grid(True)
fig.tight_layout();fig.savefig(D/'simulacao_rev49.png',dpi=150)
