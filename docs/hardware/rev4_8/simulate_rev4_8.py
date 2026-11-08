from pathlib import Path
import os,shutil
import subprocess,json,csv
import numpy as np
ROOT=Path(__file__).resolve().parents[3];OUT=Path(os.environ.get('PEDALEIRA_REV48_OUT',str(ROOT/'output/rev4_8'))).resolve();SIM=OUT/'simulacao';SIM.mkdir(exist_ok=True)
# Explicit finite open-loop gain / dominant-pole approximation, NOT a vendor macromodel.
net='''Pedaleira rev4.8 - linear AC and operating point, finite 3MHz opamps
.subckt OP_LIN p n out
Eerr err 0 p n 200000
Rdom err dom 10k
Cdom dom 0 1.061033u
Ebuf src 0 dom 0 1
Rout src out 50
.ends
{CIRCUIT}
.control
set wr_singlescale
set wr_vecnames
op
print v(inbuf) v(adcp) v(adcn) v(ainp) v(ainn) v(dacbuf) v(jackout)
ac dec 100 1 100Meg
let adc = v(ainp)-v(ainn)
wrdata ac.txt adc v(jackout) v(dacbuf)
quit
.endc
.end
'''
model=json.loads((OUT/'circuito_rev4_8.json').read_text());parts={a['ref']:a for a in model['components']}
alias={'GND':'0','VCOM':'vcom','JACK_IN':'guitar','HI_Z':'hiz','IN_BUF':'inbuf','ADC_P_IN':'adcp','ADC_N_IN':'adcn','FB_P':'fbp','FB_N':'fbn','DRV_P':'drvp','DRV_N':'drvn','AINA_P':'ainp','AINA_N':'ainn','AOUTA_P':'dp','AOUTA_N':'dn','DAC_AC_P':'dacacp','DAC_AC_N':'dacacn','DAC_P':'dacp','DAC_N':'dacn','DAC_BUF':'dacbuf','LP1':'lp1','LP2':'lp2','JACK_OUT':'jackout'}
def node(n):return alias[n]
def val(s):return s.replace(' bipolar','').replace('Mohm','Meg').replace('ohm','').replace('F','').replace(' ','')
lines=['Vcom vcom 0 2.4','Vguitar guitar 0 DC 0 AC 1','Vdacp dp 0 DC 2.5 AC .5','Vdacn dn 0 DC 2.5 AC .5 180']
selected=[a for a in model['components'] if (a['sheet'] in (2,6) and a['kind'] in ('R','C','CP','CB')) or a['ref'] in ('C1','R3')]
for a in selected:lines.append(a['ref']+' '+node(a['pins']['1'])+' '+node(a['pins']['2'])+' '+val(a['value']))
for ref,unit,p,n,o in [('U1','A','3','2','1'),('U1','B','5','6','7'),('U3','A','3','2','1'),('U3','B','5','6','7')]:
 a=parts[ref];lines.append('X'+ref+unit+' '+' '.join(node(a['pins'][pin]) for pin in (p,n,o))+' OP_LIN')
lines += ['R_ADC_DIFF ainp ainn 37k','R_LOAD jackout 0 100k']
net=net.replace('{CIRCUIT}','\n'.join(lines))
(SIM/'analogico.cir').write_text(net)
p=subprocess.run([os.environ.get('NGSPICE_BIN') or shutil.which('ngspice') or '/tmp/pedaleira-local/usr/bin/ngspice','-b','analogico.cir'],cwd=SIM,text=True,capture_output=True)
(SIM/'ngspice.log').write_text(p.stdout+'\n'+p.stderr)
assert p.returncode==0,p.stderr
v=np.loadtxt(SIM/'ac.txt',skiprows=1);freq=v[:,0];adc=v[:,1]+1j*v[:,2];out=v[:,3]+1j*v[:,4];buf=v[:,5]+1j*v[:,6]
def db(a):return 20*np.log10(np.abs(a))
def at(a,f):return float(np.interp(np.log10(f),np.log10(freq),db(a)))
res={'tool':'ngspice-47','model':'linear finite Aol=200000, GBW=3MHz, Rout=50ohm; no slew/clipping/nonlinearities','load_ohm':100000,'adc_20Hz_dB':at(adc,20),'adc_1kHz_dB':at(adc,1000),'adc_20kHz_dB':at(adc,20000),'adc_6_144MHz_dB':at(adc,6144000),'output_20Hz_dB':at(out,20),'output_1kHz_dB':at(out,1000),'output_20kHz_dB':at(out,20000),'output_filter_6_144MHz_dB':at(out,6144000),'adc_peak_gain_dB':float(max(db(adc))),'output_peak_gain_dB':float(max(db(out)))}
# Frequency at -3dB relative to the passband; preserve loaded network, not the old unloaded estimate.
ix=(freq>1000)&(db(out)<at(out,1000)-3);res['output_f3_loaded_Hz']=float(freq[ix][0])
res['i2c_rise_time_200pF_ns']=.8473*4700*200e-12*1e9
res['negative_filter_drop_at_10mA_V']=22*.01
res['negative_filter_fc_Hz']=1/(2*np.pi*22*47e-6)
res['codec_VA_max_mA']=53;res['codec_VD_VL_max_mA']=28
res['adc_input_operating_target_Vpeak']=1.0
res['regulator_dissipation_at_8_3V_53mA_W']=(8.3-5)*(.053+5/910)+8.3*.008
(SIM/'resultados.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(9,5));ax.semilogx(freq,db(adc),label='Entrada guitarra -> ADC diferencial');ax.semilogx(freq,db(out),label='DAC diferencial -> P10 (carga 100 kohm)');ax.set(xlim=(1,1e7),ylim=(-100,5),xlabel='Frequência (Hz)',ylabel='Ganho (dB)');ax.grid(True,which='both',alpha=.3);ax.legend();fig.tight_layout();fig.savefig(SIM/'resposta_analogica.png',dpi=160)
