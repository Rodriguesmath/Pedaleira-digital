from pathlib import Path
import json,gzip
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parents[3]/'output/auditoria_rev49/SIMULACOES';r=pd.read_csv(D/'matriz_transientes.csv')
fig,ax=plt.subplots(1,2,figsize=(12,4))
for amp,g in r[(r.path=='adc')&(r.raw_V==11.3)].groupby('stimulus_peak_V'):
 ax[0].semilogx(g.hz,g.gain,'o-',label=f'{amp:g} Vpk');ax[1].loglog(g.hz,g.THD_2to7_percent,'o-',label=f'{amp:g} Vpk')
ax[0].set(xlabel='Frequency / Hz',ylabel='ADC differential / guitar, gain');ax[1].set(xlabel='Frequency / Hz',ylabel='Model harmonic ratio H2..H7 / %')
for a in ax:a.grid();a.legend(fontsize=8)
fig.suptitle('TI macro + generic diodes + resistive ADC: exploratory, not measured THD');fig.tight_layout();fig.savefig(D/'ganho_distorcao_modelo.png',dpi=150);plt.close(fig)
names=['ADC_BIAS','VREF_OP','IN_BUF','DRV_P','DRV_N','AINA_P','AINA_N','VCOM','DAC_BUF','JACK_OUT'];x=np.loadtxt(gzip.open(D/'startup_max_bounded.txt.gz','rt'),skiprows=1)
fig,ax=plt.subplots(2,1,figsize=(10,6))
for n in ['ADC_BIAS','VREF_OP','AINA_P','VCOM']:ax[0].plot(x[:,0],x[:,names.index(n)+1],label=n)
ax[1].plot(x[:,0],x[:,names.index('JACK_OUT')+1],label='Output jack')
for a in ax:a.grid();a.legend();a.set(xlabel='Time / s',ylabel='V')
fig.suptitle('12.6 V RAW envelope; bounded surrogate, NOT TI startup prediction');fig.tight_layout();fig.savefig(D/'partida_limites_modelo.png',dpi=150)
