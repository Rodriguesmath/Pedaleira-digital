#!/usr/bin/env python3
"""Auditoria independente de rev4.9; não importa nem executa geradores CAD.

Saídas são cálculos com opamp ideal, não simulação SPICE ou medição.
Monte Carlo uniforme e independente não substitui cantos determinísticos.
"""
import csv
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'output/auditoria_rev49/VALIDACAO'
OUT.mkdir(parents=True, exist_ok=True)
model = json.loads((ROOT/'docs/hardware/rev4_9/circuito_rev4_9.json').read_text())
cs = {c['ref']: c for c in model['components']}
xml = ET.parse(ROOT/'output/rev4_9/kicad/netlist.xml')
nets = {}
for net in xml.findall('.//nets/net'):
    for node in net.findall('node'):
        nets[(node.attrib['ref'], node.attrib['pin'])] = net.attrib['name'].split('/')[-1]
diff = [(c['ref'], p, n, nets.get((c['ref'], p)))
        for c in cs.values() for p, n in c['pins'].items()
        if n is not None and nets.get((c['ref'], p)) != n]
assert not diff, diff

# Pinagem verificada antes de assumir a posição dos quatro resistores.
for ref, expected in {
    'R1': {'DAC_AC_P','DAC_P'}, 'R2': {'DAC_P','VREF_OP'},
    'R7': {'DAC_AC_N','DAC_N'}, 'R8': {'DAC_N','DAC_BUF'},
}.items():
    assert set(cs[ref]['pins'].values()) == expected

def resistance(ref):
    value = cs[ref]['value'].split()
    return float(value[0]) * {'ohm':1, 'kohm':1e3, 'Mohm':1e6}[value[1]]

nominal = np.array([resistance(r) for r in ('R1','R2','R7','R8')])

def nodal(r, plus, minus, bias):
    """KCL in+ / KCL in- / v+=v-; unknowns v+,v-,vout."""
    gp, gr, gn, gf = 1/np.asarray(r)
    matrix = np.array([[gp+gr,0,0], [0,gn+gf,-gf], [1,-1,0]])
    return float(np.linalg.solve(matrix, [gp*plus+gr*bias,gn*minus,0])[2])

def coefficients(r):
    p=nodal(r,1,0,0); n=nodal(r,0,1,0)
    return {'G_plus':p, 'G_minus':n, 'G_diff':(p-n)/2,
            'G_cm':p+n, 'G_bias':nodal(r,0,0,1)}

assert np.isclose(coefficients(nominal)['G_diff'], .499)
assert abs(coefficients(nominal)['G_cm']) < 1e-12
corners=[]; summary=[]
rng=np.random.default_rng(490410)
for tol in (.001,.01,.05):
    rows=[]
    for signs in itertools.product((-1,1), repeat=4):
        rr=nominal*(1+tol*np.array(signs)); cc=coefficients(rr)
        row={'tolerance':tol,'corner':''.join('+' if x==1 else '-' for x in signs),**cc}
        rows.append(row); corners.append(row)
    rr=nominal*(1+rng.uniform(-tol,tol,(100000,4)))
    a=rr[:,1]/rr[:,0]; b=rr[:,3]/rr[:,2]
    gplus=(1+b)*a/(1+a); gdiff=(gplus+b)/2; gcm=gplus-b
    analytic_check=coefficients(rr[0])
    assert np.isclose(gcm[0],analytic_check['G_cm'])
    cmrr=20*np.log10(np.abs(gdiff/gcm))
    worst=max(rows,key=lambda x:abs(x['G_cm']))
    summary.append({'tolerance':tol,'corners':16,'mc_samples':100000,
       'max_abs_G_cm':abs(worst['G_cm']),
       'CMRR_worst_dB':min(20*np.log10(abs(r['G_diff']/r['G_cm'])) if abs(r['G_cm'])>1e-14 else 400 for r in rows),
       'Gdiff_min':min(r['G_diff'] for r in rows),'Gdiff_max':max(r['G_diff'] for r in rows),
       'MC_CMRR_p01_p50_p99_dB':np.percentile(cmrr,[1,50,99]).tolist(),
       'MC_Gdiff_min_max':[float(gdiff.min()),float(gdiff.max())]})

loads=[]
for external in (1e6,1e5,1e4,1e3):
    reff=1/(1/external+1/1e6)
    loads.append({'external_ohm':external,'R_parallel_R6':reff,
      'low_band_resistive_gain':reff/(reff+440),
      'C5_highpass_Hz':1/(2*np.pi*10e-6*(reff+440))})

result={'analysis_type':'Analytical/numerical ideal-opamp KCL, not SPICE or hardware measurement',
 'MC_seed':490410,'MC_distribution':'independent uniform resistor error',
 'model_vs_XML_differences':diff,'connected_pins_checked':sum(n is not None for c in cs.values() for n in c['pins'].values()),
 'DAC_nominal':coefficients(nominal),'DAC_tolerances':summary,'output_loads':loads,
 'input_highpass_Hz':1/(2*np.pi*100e-9*1.001e6),
 'U3B_feedback_pole_Hz':1/(2*np.pi*1e4*22e-12),
 'ADC_differential_resistive_load_ohm':1/(1/37000+1/200000),
 'ADC_low_band_diff_gain':2/(1+3000*(1/37000+1/200000)),
 'ADC_BIAS_ratio_worstcase':[12000*.999/(13000*1.001+12000*.999),12000*1.001/(13000*.999+12000*1.001)],
 'Zout_20Hz_ohm':{'real':440,'imag':-1/(2*np.pi*20*10e-6)},
 'limitations':['37k differential ADC load is a bound, not a switched-capacitor ADC model',
 'VCOM has typical value only; no guaranteed worst-case matching follows',
 'No qualified CW7805 or real TL072 suffix identified',
 'Gain/headroom equations do not establish THD, stability or safe startup']}
(OUT/'analogico_calculos.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
with (OUT/'analogico_cantos.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(corners[0]));w.writeheader();w.writerows(corners)
with (OUT/'analogico_cargas.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(loads[0]));w.writeheader();w.writerows(loads)
print(json.dumps(result,indent=2,ensure_ascii=False))
