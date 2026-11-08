#!/usr/bin/env python3
"""Auditoria analítica reproduzível, sem simulação de dispositivos/hardware.
Executar da raiz: python3 docs/hardware/auditoria_rev49/analise_alimentacao.py
Todos os parâmetros térmicos do CW são hipóteses, nunca especificações do CW.
"""
from pathlib import Path
import argparse, json

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, default=ROOT/'output/auditoria_rev49/VALIDACAO')
a = parser.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
p = {
 'method': 'Analítico; não é SPICE nem medição',
 'source_nominal_V': [9, 10.5, 11, 12], 'source_tolerance': .05,
 'D1_forward_nominal_assumed_V': .7, 'D1_forward_max_assumed_V': .9, 'D1_forward_min_guaranteed_V': 0,
 'V5_min_assumed_V':4.75, 'V5_nom_V':5, 'V5_max_assumed_V':5.25,
 'stm32_board_and_codec_digital_budget_A':.350, 'ESP_board_peak_budget_A':.500,
 'codec_VA_datasheet_max_A':.053, 'bleeder_ohm':910,
 'ADC_top_ohm':13000, 'ADC_bottom_ohm':12000, 'ADC_res_tolerance':.001,
 'ADC_cap_nom_F':100e-6, 'OP_top_ohm':2200, 'OP_bottom_ohm':2200,
 'OP_res_tolerance':.01, 'OP_cap_nom_F':470e-6, 'cap_tolerance':.20,
 'CW_Iq_proxy_A':.008, 'theta_JC_proxy_K_W':5, 'theta_CS_assumed_K_W':1,
 'theta_SA_spec_K_W':2, 'ambient_test_C':[25,40,50,60], 'Tj_target_C':100,
 'TL072_input_lower_headroom_TI_reference_V':4,
 'TL072_output_headroom_heuristic_V':3, 'guitar_peak_V':.5,
 'DAC_receiver_expected_peak_corrected_topology_V':1.324,
 'CW_parameters_identified':False,
}
def ratio(top,bottom,tol):
 return bottom*(1-tol)/(top*(1+tol)+bottom*(1-tol)), bottom*(1+tol)/(top*(1-tol)+bottom*(1+tol))
oplo,ophi=ratio(p['OP_top_ohm'],p['OP_bottom_ohm'],p['OP_res_tolerance'])
adlo,adhi=ratio(p['ADC_top_ohm'],p['ADC_bottom_ohm'],p['ADC_res_tolerance'])
load=p['stm32_board_and_codec_digital_budget_A']+p['ESP_board_peak_budget_A']+p['codec_VA_datasheet_max_A']+p['V5_max_assumed_V']/p['bleeder_ohm']+p['V5_max_assumed_V']/(p['ADC_top_ohm']+p['ADC_bottom_ohm'])
comp=[]
for v in p['source_nominal_V']:
 rawlo=v*(1-p['source_tolerance'])-p['D1_forward_max_assumed_V']; rawhi=v*(1+p['source_tolerance'])
 vreflo=rawlo*oplo; vrefhi_at_minraw=rawlo*ophi
 power=(rawhi-p['V5_min_assumed_V'])*load+rawhi*p['CW_Iq_proxy_A']
 comp.append({'source_nominal_V':v,'RAW_min_assumed_V':rawlo,'RAW_max_conservative_V':rawhi,
 'VREF_OP_min_at_RAW_min_V':vreflo,'input_min_at_0_5pk_V':vreflo-p['guitar_peak_V'],
 'input_CM_margin_against_TI_4V_V':vreflo-p['guitar_peak_V']-4,
 'output_margin_against_3V_heuristic_verified_receiver_V':min(vreflo-1.324,rawlo-vrefhi_at_minraw-1.324)-3,
 'CW_loss_proxy_continuous_W':power,
 'junction_proxy_C':{str(t):t+power*8 for t in p['ambient_test_C']},
 'theta_SA_max_target_100C_at40C_proxy_K_W':60/power-6})
zop=p['OP_top_ohm']*p['OP_bottom_ohm']/(p['OP_top_ohm']+p['OP_bottom_ohm'])
zadc=p['ADC_top_ohm']*p['ADC_bottom_ohm']/(p['ADC_top_ohm']+p['ADC_bottom_ohm'])
r={'classification':'Cálculos analíticos condicionais; não aprovam CW/TL072 desconhecidos',
 'current_5V_budget_A':load,'comparison':comp,
 'nominal_12V':{'RAW_V':11.3,'VREF_OP_V':5.65,'ADC_BIAS_V':2.4,'CW_loss_at_budget_proxy_W':(11.3-5)*load+11.3*.008},
 'OP_ratio_minmax':[oplo,ophi], 'ADC_ratio_minmax':[adlo,adhi],
 'VREF_OP_over_all_12V_assumed_V':[10.5*oplo,12.6*ophi],
 'ADC_BIAS_over_assumed_V5_V':[4.75*adlo,5.25*adhi],
 'ADC_divider_ratio_error_at5_25V_max_V':max(abs(adlo-.48),abs(adhi-.48))*5.25,
 'OP_Zdc_nom_ohm':zop,'ADC_Zdc_nom_ohm':zadc,
 'OP_tau_nom_s':zop*p['OP_cap_nom_F'],'ADC_tau_nom_s':zadc*p['ADC_cap_nom_F'],
 'OP_tau_worst_assumed_s':zop*1.01*p['OP_cap_nom_F']*1.2,
 'ADC_tau_worst_assumed_s':zadc*1.001*p['ADC_cap_nom_F']*1.2,
 'ADC_net_leakage_for_50mV_A':.05/zadc,
 'caution':'VCOM típico0,48VA sem min/max.50mV é critério de projeto; não garantiado datasheet. Swing1,324V deriva do receptor4.9 verificado independentemente porKCL; swing doTL072 real ainda não garantido.'}
for name,data in [('alimentacao_parametros.json',p),('alimentacao_resultados.json',r)]:
 (a.out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
assert comp[0]['input_CM_margin_against_TI_4V_V']<0
assert comp[-1]['input_CM_margin_against_TI_4V_V']>0
assert abs(comp[-1]['RAW_max_conservative_V']-12.6)<1e-9
assert 7.2 < comp[-1]['CW_loss_proxy_continuous_W'] < 7.3
print(json.dumps({'out':str(a.out),'checks_passed':4,'current_A':load,'CW_12V_W':comp[-1]['CW_loss_proxy_continuous_W']},ensure_ascii=False))
