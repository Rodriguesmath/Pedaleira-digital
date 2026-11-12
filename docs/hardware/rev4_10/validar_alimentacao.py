#!/usr/bin/env python3
"""Verificação independente 4.10A: hipóteses e bloqueios permanecem explícitos.

Lê o candidato CAD, não projeta proteção ADC/mute, não altera firmware.
Os estados são análise de conectividade/energização, não modelo de semicondutor.
"""
import csv
import hashlib
import itertools
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/REV410_ENTREGA/VALIDACAO_A'
OUT.mkdir(parents=True,exist_ok=True)
MODEL=ROOT/'docs/hardware/rev4_10/circuito_rev4_10.json'
model=json.loads(MODEL.read_text())
parts={a['ref']:a for a in model['components']}
ISO_PINS={'1':'+3V3_STM','2':'STM_UART_RX','3':'STM_UART_TX','4':'GND','5':'GND','6':'ESP_UART_RX','7':'ESP_UART_TX','8':'+3V3_ESP'}
UART_ISOLATED=parts.get('U6',{}).get('value')=='ISO7721DR' and parts.get('U6',{}).get('pins')==ISO_PINS

def cw_budget(v5, rbleed, rtop, rbottom):
    # IA max53mA: Cirrus DS593F2p17, especificado com clocks nas condições da tabela.
    return .053+v5/rbleed+v5/(rtop+rbottom)

def power_state(stm,esp,analog):
    rails={'USB_STM_5V':bool(stm),'USB_ESP_5V':bool(esp),
           'RAW':bool(analog),'VA_CW_5V':bool(analog),
           'STM_3V3':bool(stm),'ESP_3V3':bool(esp),
           'VD_VL_STM':bool(stm)}
    risks=[]
    if not UART_ISOLATED and stm and not esp: risks.append('UART STM -> ESP sem contenção verificada')
    if not UART_ISOLATED and esp and not stm: risks.append('UART ESP -> STM sem contenção verificada')
    if stm and not analog: risks.append('VD/VL ativos e VA ausente: estado interno codec/SDOUT não qualificado; reset LOW necessário')
    if analog and not stm: risks.append('VA ativo e VD/VL ausentes: sequenciamento interno não qualificado; reset LOW não constitui isolação')
    if not analog: risks.append('Saída analógica sem alimentação; nenhum estado de mute físico demonstrado nesta fase')
    if not stm: risks.append('Codec RST tem pull-down10k no circuito-base; não há liberação por MCU')
    return {'id':f'{int(stm)}{int(esp)}{int(analog)}',
            'usb_stm':bool(stm),'usb_esp':bool(esp),'12V':bool(analog),
            'rails':rails,'risks':risks,
            'direct_SAI_I2C_supply_mismatch_candidate':False,
            'safe_complete_system':False, 'analysis_profile':'conjunto com J5 fechado, NÃO liberado',
            'uart_remote_DC_signal_path_isolated':UART_ISOLATED,
            'uart_rx_stm':('dados' if esp else 'HIGH após limiar PD e tDO') if stm else 'indeterminado, receptor OFF',
            'uart_rx_esp':('dados' if stm else 'HIGH após limiar PD e tDO') if esp else 'indeterminado, receptor OFF',
            'default_test_profile':{'J5':'ABERTO','codec':'REMOVIDO','VA':False,'VD_VL_at_empty_adapter':bool(stm),'complete_system_authorized':False}}

states=[power_state(*s) for s in itertools.product((0,1), repeat=3)]
transitions=[]
for a in states:
    for b in states:
        delta=[i for i in range(3) if a['id'][i]!=b['id'][i]]
        if len(delta)!=1:continue
        i=delta[0]
        transitions.append({'from':a['id'],'to':b['id'],
          'source_changed':['USB_STM','USB_ESP','12V'][i],
          'direction':'ON' if b['id'][i]=='1' else 'OFF',
          'automatic_containment_demonstrated':False, 'UART_DC_isolation_structural':UART_ISOLATED,
          'risks_before':a['risks'],'risks_after':b['risks'],
          'transient_risks':(['Capacitores retêm carga; ordem de queda VD/VL/VA não especificada',
                              'Reset software não antecipa perda abrupta de alimentação'] if i!=1 else
                             ['UART por barreira de U6; lógica indeterminada no brownout, default HIGH apenas após condição PD especificada'])})

corners=[]
for v5,rb,rt,rl in itertools.product((4.75,5.25),(910*.99,910*1.01),(13000*.999,13000*1.001),(12000*.999,12000*1.001)):
    current=cw_budget(v5,rb,rt,rl)
    for raw in (10.5,12.6):
        corners.append({'V5':v5,'RAW':raw,'R21':rb,'R27':rt,'R28':rl,
         'current_A':current,'power_proxy_W':(raw-v5)*current+raw*.008})
imax=max(c['current_A'] for c in corners)
pmax=max(c['power_proxy_W'] for c in corners)
conservative=(12.6-4.75)*imax+12.6*.008
results={
 'scope':'A only; calculations/state analysis, not SPICE/hardware/CAD approval',
 'architecture':'USB STM and USB ESP independent; CW supplies codec VA only; common GND',
 'VD_VL_implemented':'STM WeAct3V3; free current/partial-power behavior remains pending',
 'CW_current_typical_with_typical_IA_A':.045+5/910+5/25000,
 'CW_current_max_budget_A':imax,'CW_Iq_proxy_A':.008,
 'CW_power_corner_proxy_max_W':pmax,'CW_power_conservative_proxy_W':conservative,
 'CW_Tj_proxy_thetaJA50_ambient40_C':40+conservative*50,
 'CW_Tj_proxy_thetaJA50_ambient60_C':60+conservative*50,
 'CW_max_thetaJA_for100C_at60C_proxy_C_W':40/conservative,
 'CW_identity_qualified':False,
 'CW_user_decision':'Keep generic CW; qualification remains pending (2026-11-12)',
 'UART_implemented_ISO7721DR':UART_ISOLATED,
 'UART_added_budget_per_3V3_A':.004,
 'UART_RX_load_design_pF':15,
 'model_sha256':hashlib.sha256(MODEL.read_bytes()).hexdigest(),
 'WeAct_total_max_claim_A':1.0,'WeAct_free_current_proven_A':None,
 'codec_digital_current_max_3V3_A':.028,
 'codec_digital_current_max_5V_A':.049,
 'VD_limits_V':[3.1,5.25],'VL_limits_V':[2.37,5.25],
 'GPIO_injection_numeric_bound_A':None,
 'GPIO_reason_no_numeric_bound':'UART uses structural capacitive barrier and local-domain IO; no universal MCU clamp current invented. Codec analog/reset partial-power remain unqualified',
 'source_states':8,'single_source_directed_transitions':24,
 'multi_source_orders_to_all_on':list(itertools.permutations(['USB_STM','USB_ESP','12V'])),
 'gate_A':'BLOCKED',
 'blockers':['CW7805 manufacturer/pinout/stability not identified',
             *(['UART implementation missing or invalid'] if not UART_ISOLATED else []),
             'WeAct3V3 free current not demonstrated',
             'Automatic codec reset on VA loss and analog input protection during rail decay not demonstrated'],
 'forbidden_progress':['B ADC redesign','B physical mute redesign','C final approval'],
 'assumptions':{'RAW_min10_5V':'12V−5% minus assumed0.9V D1, not guaranteed all-temperature specification',
  'RAW_max12_6V':'12V+5%, no guaranteed diode minimum drop',
  'CW_V5_4_75_5_25':'family comparator envelope, not identified CW specification',
  'CW_Iq8mA_thetaJA50':'family comparator only; no actual CW qualification',
  'codec_IA53mA':'datasheet current at stated clock/temperature conditions; not inrush bound'}}

results['gate_A']='BLOCKED' if results['blockers'] else 'PASS'

class Checks(unittest.TestCase):
    def test_current_reduction(self):self.assertLess(imax,.060)
    def test_thermal_conditional_reduction(self):self.assertLess(conservative,.57)
    def test_all_states(self):self.assertEqual(len(states),8)
    def test_transitions(self):self.assertEqual(len(transitions),24)
    def test_uart_asymmetric_states(self):
        self.assertTrue(UART_ISOLATED)
        for state in states:
            self.assertTrue(state['uart_remote_DC_signal_path_isolated'])
    def test_usb_headers_not_cw(self):
        self.assertIsNone(parts['H_STM32']['pins']['P1.2'])
        self.assertIsNone(parts['H_ESP32']['pins']['VIN'])
    def test_codec_digital_domain(self):
        self.assertEqual(parts['U2']['pins']['9'],'+3V3_STM')
        self.assertEqual(parts['U2']['pins']['10'],'+3V3_STM')
    def test_cw_disconnect_link(self):
        self.assertEqual(parts['J5']['pins'],{'1':'+5V_CW','2':'+5VA'})
        self.assertNotEqual(parts['U5']['pins']['3'],parts['U2']['pins']['20'])
    def test_no_false_gate(self):
        self.assertTrue(results['blockers'])
        self.assertEqual(results['gate_A'],'BLOCKED')
    def test_regulator_identity_not_assumed(self):self.assertFalse(results['CW_identity_qualified'])
    def test_3v3_capacity_not_invented(self):self.assertIsNone(results['WeAct_free_current_proven_A'])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    with (OUT/'testes_execucao.log').open('w') as log:
        run=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    results['test_count']=run.testsRun;results['tests_successful']=run.wasSuccessful()
    for name,data in [('calculos',results),('estados',states),('transicoes',transitions)]:
        (OUT/f'{name}.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    with (OUT/'cw_cantos.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(corners[0]));w.writeheader();w.writerows(corners)
    (OUT/'script_sha256.txt').write_text(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+'  docs/hardware/rev4_10/validar_alimentacao.py\n')
    print(json.dumps(results,indent=2,ensure_ascii=False))
    raise SystemExit(0 if run.wasSuccessful() else 1)
