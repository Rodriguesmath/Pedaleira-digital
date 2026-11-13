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

def cw_budget(v5, rbleed, rtop, rbottom, r34_min=11000*0.99, r36_min=1800*0.99, r37_min=22000*0.99, r38_min=470000*0.99):
    # IA max 53 mA: Cirrus DS593F2 p17, especificado com clocks nas condições da tabela.
    # Soma supervisor F9 (U7 TL431 + Q3 + R33..R38): divisor R34<=2.52V/R34 + R36=(v5-0.5-1.5)/R36 + Q3 load.
    i_div = 2.52 / r34_min + 2.52 / r38_min
    i_tl_q3 = max(0.0, (v5 - 2.0) / r36_min) + v5 / r37_min
    # Phase 4.10B Blocker 3: clamp bias active windows ~1.40 mA on +5VA (R48..R53 + Q9/Q10)
    i_clamp_bias = 0.00140
    return .053 + v5 / rbleed + v5 / (rtop + rbottom) + i_div + i_tl_q3 + i_clamp_bias


def stm32_3v3_budget():
    # WeAct STM32H723 V1.2 schematic U2 worst-case buck variant: SY8088AAC = 1.0 A (alt XT3410 1.5 A, TLV62569 2.0 A).
    # STM32H723VG DS13313 Table 22 Run IDD max (550 MHz VOS0, peripherals ON, Ta=105C): 250 mA (220 mA @ 85C).
    loads_A = {
        'stm32_ds13313_105C_max': 0.250,
        'weact_onboard_flash_leds_reserve': 0.025,
        'codec_cs4272_VD_VL_max': 0.028,
        'iso7721_side1_115200bps': 0.004,
        'board_leds_4x470R_at_3V6': 4 * (3.6 - 1.7) / (470 * 0.99),
        'pullups_i2c_uart_reset_interlock': 2 * (3.6 / (4700 * 0.99)) + 3.6 / (47000 * 0.99) + 3.6 / (4700 * 0.99) + 3.6 / (1000 * 0.99),
    }
    total = sum(loads_A.values())
    weact_min_buck = 1.000
    return {
        'weact_buck_variants_A': {'SY8088AAC_default': 1.0, 'XT3410AFMR_G': 1.5, 'TLV62569DBVR': 2.0},
        'worst_case_buck_limit_A': weact_min_buck,
        'loads_A': loads_A,
        'total_worst_case_load_A': total,
        'gross_headroom_A': weact_min_buck - total,
        'arithmetic_budget_pass': total < weact_min_buck,
        'physical_sample_verification_required': True,
    }


RESET_INTERLOCK_OK = (
    parts.get('H_STM32', {}).get('pins', {}).get('P1.38') == 'CODEC_RST_CMD'
    and parts.get('R39', {}).get('pins') == {'1': 'CODEC_RST_CMD', '2': 'CODEC_RST'}
    and parts.get('U7', {}).get('value') == 'TL431ACZ'
    and parts.get('Q1', {}).get('pins') == {'1': 'GND', '2': 'RST_CLAMP_B', '3': 'CODEC_RST'}
    and parts.get('Q2', {}).get('pins') == {'1': 'GND', '2': 'Q2_B', '3': 'RST_CLAMP_B'}
)
AIN_OFFSTATE_SHUNT_OK = (
    parts.get('D15', {}).get('pins') == {'1': '+RAW', '2': 'RAW_D'}
    and parts.get('C44', {}).get('pins') == {'1': 'V_HOLD', '2': 'GND'}
    and parts.get('Q4', {}).get('pins') == {'1': 'GND', '2': 'Q4_B', '3': 'SHUNT_EN'}
    and parts.get('Q5', {}).get('pins') == {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINA_P'}
    and parts.get('Q6', {}).get('pins') == {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINA_N'}
    and parts.get('Q7', {}).get('pins') == {'1': 'GND', '2': 'SHUNT_EN', '3': 'ADC_B_SW'}
    and parts.get('Q8', {}).get('pins') == {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINB_CM'}
)

CLAMP_ACTIVE_OK = (
    'D9' not in parts and 'D10' not in parts and 'D11' not in parts and 'D12' not in parts
    and parts.get('Q11', {}).get('pins') == {'1': 'AINA_P', '2': 'V_BIAS_HI', '3': 'GND'}
    and parts.get('Q12', {}).get('pins') == {'1': 'AINA_P', '2': 'V_BIAS_LO', '3': '+5VA'}
    and parts.get('Q13', {}).get('pins') == {'1': 'AINA_N', '2': 'V_BIAS_HI', '3': 'GND'}
    and parts.get('Q14', {}).get('pins') == {'1': 'AINA_N', '2': 'V_BIAS_LO', '3': '+5VA'}
    and parts.get('Q9', {}).get('pins') == {'1': 'V_BIAS_HI', '2': 'V_REF_HI', '3': '+5VA'}
    and parts.get('Q10', {}).get('pins') == {'1': 'V_BIAS_LO', '2': 'V_REF_LO', '3': 'GND'}
)

MUTE_RELAY_OK = (
    parts.get('C5', {}).get('pins', {}).get('2') == 'OUT_PRE'
    and parts.get('R6', {}).get('value') == '47 kohm'
    and parts.get('R6', {}).get('pins') == {'1': 'OUT_PRE', '2': 'GND'}
    and parts.get('K1', {}).get('value') == 'G5V-1-DC12'
    and parts.get('K1', {}).get('pins') == {'1': 'GND', '2': 'K1_COILP', '5': 'JACK_OUT', '6': 'JACK_OUT', '9': 'GND', '10': 'OUT_PRE'}
    and parts.get('D16', {}).get('pins') == {'1': 'GND', '2': 'K1_COILP'}
    and parts.get('U8', {}).get('value') == 'TL431ACZ'
    and parts.get('Q15', {}).get('pins') == {'1': '+RAW', '2': 'Q15_B', '3': 'RAW_OK'}
    and parts.get('Q21', {}).get('pins') == {'1': '+RAW', '2': 'Q21_B', '3': 'K1_COILP'}
)


def power_state(stm,esp,analog):
    rails={'USB_STM_5V':bool(stm),'USB_ESP_5V':bool(esp),
           'RAW':bool(analog),'VA_CW_5V':bool(analog),
           'STM_3V3':bool(stm),'ESP_3V3':bool(esp),
           'VD_VL_STM':bool(stm)}
    risks=[]
    if not UART_ISOLATED and stm and not esp: risks.append('UART STM -> ESP sem contenção verificada')
    if not UART_ISOLATED and esp and not stm: risks.append('UART ESP -> STM sem contenção verificada')
    if not RESET_INTERLOCK_OK and stm and not analog: risks.append('VD/VL ativos e VA ausente sem intertravamento fisico de reset')
    if analog and not stm: risks.append('VA ativo e VD/VL ausentes: R13+Q1 mantem /RST LOW; sequenciamento interno codec ainda requer controle na fase B')
    if not analog: risks.append('Saída analógica sem VA: contenção off-state SHUNT_EN ativa nos AIN quando +RAW presente/C44 carregado; mute fisico DAC pendente na fase B')
    if not stm: risks.append('Codec /RST mantido em <= 0.1 V por R13+Q1; sem retorno para +3V3_STM')
    return {'id':f'{int(stm)}{int(esp)}{int(analog)}',
            'usb_stm':bool(stm),'usb_esp':bool(esp),'12V':bool(analog),
            'rails':rails,'risks':risks,
            'direct_SAI_I2C_supply_mismatch_candidate':False,
            'reset_interlock_active_in_design':RESET_INTERLOCK_OK,
            'offstate_ain_containment_in_design':AIN_OFFSTATE_SHUNT_OK,
            'safe_complete_system':False, 'analysis_profile':'candidato 4.10A com F9 (fases B/C e bancada fisica ainda pendentes)',
            'uart_remote_DC_signal_path_isolated':UART_ISOLATED,
            'uart_rx_stm':('dados' if esp else 'HIGH após limiar PD e tDO') if stm else 'indeterminado, receptor OFF',
            'uart_rx_esp':('dados' if stm else 'HIGH após limiar PD e tDO') if esp else 'indeterminado, receptor OFF',
            'default_test_profile':{'J5':'ABERTO ate CW caracterizado','codec':'REMOVIDO ate Fases B/C','VA':False,'VD_VL_at_empty_adapter':bool(stm),'complete_system_authorized':False}}

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
b3v3=stm32_3v3_budget()
results={
 'scope':'Phase 4.10B design checks (UART + Reset Interlock + Off-state AIN + Active Clamp Blocker 3 + Mute Relay Blocker 4); bench physical prerequisites explicit',
 'architecture':'USB STM and USB ESP independent; CW supplies codec VA only; common GND; F9 supervisor + RST interlock + AIN shunts; F10 clamp bias + RAW UVLO + mute timer',
 'VD_VL_implemented':'STM WeAct3V3; arithmetic budget PASS against 1A SY8088 worst-case buck; physical sample buck/ESP marking inspection required before energization',
 'CW_current_typical_with_typical_IA_A':.045+5/910+5/25000+2.5/20100+(5.0-2.5)/1800+5.0/22000+.00140,
 'CW_current_max_budget_A':imax,'CW_Iq_proxy_A':.008,
 'CW_clamp_bias_added_A':.00140,
 'RAW_mute_and_sheet10_budget_A':.0176,
 'RAW_mute_and_sheet10_headroom_A':1.500-.0176,
 'CW_power_corner_proxy_max_W':pmax,'CW_power_conservative_proxy_W':conservative,
 'CW_Tj_proxy_thetaJA50_ambient40_C':40+conservative*50,
 'CW_Tj_proxy_thetaJA50_ambient60_C':60+conservative*50,
 'CW_max_thetaJA_for100C_at60C_proxy_C_W':40/conservative,
 'CW_identity_qualified':False,
 'CW_user_decision':'Keep generic CW; qualification remains pending (2026-11-12)',
 'UART_implemented_ISO7721DR':UART_ISOLATED,
 'RESET_interlock_implemented':RESET_INTERLOCK_OK,
 'AIN_offstate_containment_implemented':AIN_OFFSTATE_SHUNT_OK,
 'active_clamp_implemented':CLAMP_ACTIVE_OK,
 'mute_relay_implemented':MUTE_RELAY_OK,
 'STM32_3V3_budget':b3v3,
 'UART_added_budget_per_3V3_A':.004,
 'UART_RX_load_design_pF':15,
 'model_sha256':hashlib.sha256(MODEL.read_bytes()).hexdigest(),
 'WeAct_total_max_claim_A':1.0,'WeAct_free_current_proven_A':b3v3['gross_headroom_A'],
 'codec_digital_current_max_3V3_A':.028,
 'codec_digital_current_max_5V_A':.049,
 'VD_limits_V':[3.1,5.25],'VL_limits_V':[2.37,5.25],
 'GPIO_injection_numeric_bound_A':None,
 'GPIO_reason_no_numeric_bound':'UART uses structural capacitive barrier and local-domain IO; no universal MCU clamp current invented. Reset interlock clamps CODEC_RST<=0.1V whenever VA<4.48V.',
 'source_states':8,'single_source_directed_transitions':24,
 'multi_source_orders_to_all_on':list(itertools.permutations(['USB_STM','USB_ESP','12V'])),
 'design_blockers_A':[*([] if UART_ISOLATED else ['UART implementation missing or invalid']),
                      *([] if RESET_INTERLOCK_OK else ['Reset interlock F9 missing or invalid']),
                      *([] if AIN_OFFSTATE_SHUNT_OK else ['Off-state AIN shunt F9 missing or invalid']),
                      *([] if b3v3['arithmetic_budget_pass'] else ['3V3 arithmetic budget exceeds 1A'])],
 'design_blockers_B':[*([] if CLAMP_ACTIVE_OK else ['Active clamp Blocker 3 missing or invalid']),
                      *([] if MUTE_RELAY_OK else ['Mute relay Blocker 4 missing or invalid'])],
 'bench_prerequisites_A':['A410-01: generic CW7805 physical sample pinout/stability qualification on bench (J5 open, codec absent)',
                          'A410-05_hw: physical inspection of WeAct V1.2 U2 buck IC (SY8088/XT3410/TLV62569) and 3V3 droop test under load',
                          'A410-07_hw: physical inspection of ESP32 module (WROOM vs WROVER) confirming GPIO16/17 free'],
 'phase_BC_pending_blockers':['A410-08 (Phase C): complete footprint validation across all BOM components'],
 'gate_A_design':'PASS',
 'gate_B_design':'PASS',
 'assumptions':{'RAW_min10_5V':'12V-5% minus assumed 0.9V D1, not guaranteed all-temperature specification',
  'RAW_max12_6V':'12V+5%, no guaranteed diode minimum drop',
  'CW_V5_4_75_5_25':'family comparator envelope, not identified CW specification',
  'CW_Iq8mA_thetaJA50':'family comparator only; no actual CW qualification',
  'codec_IA53mA':'datasheet current at stated clock/temperature conditions; not inrush bound'}}

results['gate_A_design']='BLOCKED' if results['design_blockers_A'] else 'PASS'
results['gate_B_design']='BLOCKED' if (results['design_blockers_A'] or results['design_blockers_B']) else 'PASS'
results['gate_A_bench']='CONDITIONED_ON_PHYSICAL_SAMPLE'
results['gate_B_bench']='CONDITIONED_ON_PHYSICAL_SAMPLE'

class Checks(unittest.TestCase):
    def test_current_reduction(self):self.assertLess(imax,.065)
    def test_thermal_conditional_reduction(self):self.assertLess(conservative,.60)
    def test_3v3_arithmetic_budget_margin(self):
        self.assertTrue(b3v3['arithmetic_budget_pass'])
        self.assertLess(b3v3['total_worst_case_load_A'], .400)
    def test_all_states(self):self.assertEqual(len(states),8)
    def test_transitions(self):self.assertEqual(len(transitions),24)
    def test_uart_asymmetric_states(self):
        self.assertTrue(UART_ISOLATED)
        for state in states:
            self.assertTrue(state['uart_remote_DC_signal_path_isolated'])
    def test_phase_a_reset_and_ain_shunt_design(self):
        self.assertTrue(RESET_INTERLOCK_OK)
        self.assertTrue(AIN_OFFSTATE_SHUNT_OK)
    def test_phase_b_clamp_and_mute_relay_design(self):
        self.assertTrue(CLAMP_ACTIVE_OK)
        self.assertTrue(MUTE_RELAY_OK)
        self.assertEqual(results['design_blockers_B'], [])
        self.assertEqual(results['gate_B_design'], 'PASS')
    def test_usb_headers_not_cw(self):
        self.assertIsNone(parts['H_STM32']['pins']['P1.2'])
        self.assertIsNone(parts['H_ESP32']['pins']['VIN'])
    def test_codec_digital_domain(self):
        self.assertEqual(parts['U2']['pins']['9'],'+3V3_STM')
        self.assertEqual(parts['U2']['pins']['10'],'+3V3_STM')
    def test_cw_disconnect_link(self):
        self.assertEqual(parts['J5']['pins'],{'1':'+5V_CW','2':'+5VA'})
        self.assertNotEqual(parts['U5']['pins']['3'],parts['U2']['pins']['20'])
    def test_honest_gate_boundaries(self):
        self.assertEqual(results['design_blockers_A'], [])
        self.assertEqual(results['gate_A_design'], 'PASS')
        self.assertEqual(results['gate_A_bench'], 'CONDITIONED_ON_PHYSICAL_SAMPLE')
        self.assertEqual(results['gate_B_design'], 'PASS')
        self.assertEqual(results['gate_B_bench'], 'CONDITIONED_ON_PHYSICAL_SAMPLE')
        self.assertTrue(results['bench_prerequisites_A'])
        self.assertTrue(results['phase_BC_pending_blockers'])
    def test_regulator_identity_not_assumed(self):self.assertFalse(results['CW_identity_qualified'])
    def test_3v3_physical_sample_still_required(self):self.assertTrue(b3v3['physical_sample_verification_required'])

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
