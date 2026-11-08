"""Evidence integrity tests, not electrical acceptance or hardware measurements."""
from pathlib import Path
import json,hashlib,csv,itertools,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'output/auditoria_rev49';V=D/'VALIDACAO';S=D/'SIMULACOES'
def j(p):return json.loads(p.read_text())
def test_originals_unchanged():
 for name,digest in j(V/'originais_sha256.json').items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
def test_native_pin_partitions():
 r=j(V/'confronto_pdf_cad.json');assert r['connected_pin_differences']==[];assert r['net_partitions_match'];assert r['connected_pins']==256;assert len(r['nc_pins'])==9
 assert len(r['pages'])==7 and all(not p['missing_refs'] for p in r['pages'])
def test_erc_really_executed():
 r=j(V/'ERC_rev49.json');assert r['kicad_version']=='10.0.7';assert not r['ignored_checks'];assert len(r['sheets'])==8;assert not any(s['violations'] for s in r['sheets'])
def test_matrix_coverage_and_finite():
 rows=list(csv.DictReader((S/'matriz_transientes.csv').open()));keys={(r['path'],float(r['raw_V']),int(r['hz']),float(r['stimulus_peak_V'])) for r in rows}
 expected=set(itertools.product(['adc','dac'],[10.5,11.3,12.6],[100,1000,5000,10000,20000],[.05,.1,.25,.5,1]))
 assert expected<=keys;assert len(rows)==165
 for r in rows:
  assert r['status']=='OK';assert math.isfinite(float(r['gain']));assert float(r['THD_2to7_percent'])>=0
 assert j(S/'resumo.json')['physical_tests'] is False
 assert all(r['nominal_permitted']=='False' for r in rows if r['path']=='adc' and float(r['stimulus_peak_V'])==1)
def test_spice_vs_independent_nodal():
 c=j(V/'analogico_calculos.json')['DAC_nominal'];a={r['case']:r for r in j(S/'complementares.json')}
 assert abs(a['DAC_plus']['gain_real']-c['G_plus'])<.0001
 assert abs(a['DAC_minus']['gain_real']-c['G_minus'])<.0001
 assert abs(a['DAC_common']['magnitude'])<.0001
 assert c['G_diff']==.499 or np.isclose(c['G_diff'],.499)
def test_supply_worstcase_not_optimistic():
 p=j(V/'alimentacao_resultados.json');c=p['comparison'][-1];assert c['RAW_max_conservative_V']>=12.6;assert 7.23<c['CW_loss_proxy_continuous_W']<7.25;assert p['comparison'][0]['input_CM_margin_against_TI_4V_V']<0
 assert p['VREF_OP_over_all_12V_assumed_V'][1]>6.36
 # Commercial cap bounds settle slowly; a 5ms rail ramp is not reference settling.
 assert j(V/'capacitores_resultados.json')['ADC_BIAS_tau_max_s']>.74
def test_bounded_startup_not_hidden_vendor_success():
 a=j(S/'partida_resultados.json');assert len(a)==8
 assert all(not r['complete'] for r in a if r['model']=='TI');assert all(r['complete'] and not r['qualified'] for r in a if r['model']=='bounded')
 assert min(r['nodes']['JACK_OUT']['min'] for r in a if r['model']=='bounded')< -6
 for r in a:assert (S/(r['case']+'.log')).exists()
def test_tolerances_deterministic_before_monte_carlo():
 r=j(V/'analogico_calculos.json');assert r['MC_seed']==490410
 for q in r['DAC_tolerances']:assert q['corners']==16;assert q['MC_samples'] if 'MC_samples' in q else q['mc_samples']==100000
 assert r['DAC_tolerances'][0]['CMRR_worst_dB']>50;assert r['DAC_tolerances'][2]['CMRR_worst_dB']<18
 assert len(list(csv.DictReader((V/'capacitores_cantos.csv').open())))==48
def test_errata_does_not_change_topology_or_passive_values():
 a=j(ROOT/'docs/hardware/rev4_9/circuito_rev4_9.json');b=j(V/'circuito_rev49_errata_documental.json')
 for x,y in zip(a['components'],b['components']):
  assert x['pins']==y['pins'];assert x['ref']==y['ref']
  if x['kind'] in ['R','C','CP','CB','D']:assert x['value']==y['value']
def test_release_blocked_until_evidence_exists():
 s=(ROOT/'firmware/stm32/Core/Src/main.cpp').read_text();assert '#define dMAIN_AUDIO_TRANSPORT_READY          0U' in s
 assert j(D/'RESULTADO_AUDITORIA.json')['verdict']=='NÃO APROVADO'
