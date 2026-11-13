#!/usr/bin/env python3
"""Gera o modelo unico do MVP Rev. A a partir de docs/hardware/rev4_10/circuito_rev4_10.json.

Nao altera rev4_9 nem rev4_10. Aplica exatamente os cortes e substituicoes acordados:
- Remove Folha 9 (25), Folha 10 (42), Q11..Q14 (4), K1/D16 (2)
- Remove U6 ISO7721DR + C42/C43/R29..R32 (7) -> substitui por UART direta com 2x 1 kohm
- Remove J1, F1, J4, TP1..TP11 (14) -> entrada direta por fonte de bancada (I_limit 250-300 mA)
- Mantem C35 e C36 (100 pF RF modo comum ADC)
- Converte D1, D6, D7, D13, D14 para 1N4007
- Converte todos os capacitores para apenas ceramicos ou eletroliticos polarizados (com pin 1 = '+', pin 2 = '-')
Total final: 91 componentes reais (36 C + 32 R + 23 demais) + porta virtual nao-BOM PSU_12V.
"""
from collections import defaultdict
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'docs/hardware/rev4_10/circuito_rev4_10.json'
DST_DIR = Path(__file__).resolve().parent
DST_MODEL = DST_DIR / 'circuito_mvp_revA.json'

raw = json.loads(SRC.read_text())

REMOVE_REFS = (
    {c['ref'] for c in raw['components'] if c['sheet'] in (9, 10)}
    | {'Q11', 'Q12', 'Q13', 'Q14', 'K1', 'D16'}
    | {'U6', 'C42', 'C43', 'R29', 'R30', 'R31', 'R32'}
    | {'J1', 'F1', 'J4'}
    | {f'TP{i}' for i in range(1, 12)}
)

components = [copy.deepcopy(c) for c in raw['components'] if c['ref'] not in REMOVE_REFS]
byref = {c['ref']: c for c in components}

# 1. Entrada de fonte de bancada (substitui J1/F1 sem entrar na BOM de compra)
byref['D1']['pins']['1'] = '12V_IN'
byref['D1'].update(
    value='1N4007',
    package='DO-41',
    min_spec='1N4007 (1 A, 1000 V); usar I_limit=250-300 mA na fonte de bancada',
    note='Substitui 1N5822 no MVP; queda ~0,7-0,8 V em +RAW. Exige fonte 12 V regulada com I_limit <= 300 mA.',
)

psu = {
    'ref': 'PSU_12V',
    'kind': 'PSU',
    'value': 'Bancada 12V',
    'pins': {'1': '12V_IN', '2': 'GND'},
    'sheet': 1,
    'function': 'Entrada por fios da fonte de bancada 12 V (I_limit = 250-300 mA)',
    'status': 'equipamento de bancada (não entra na BOM de compra)',
    'package': 'Bornes / fios perfboard',
    'note': 'Ligar 12 V primeiro antes da USB do STM32; nunca unir 5V_CW ao 5V das placas.',
    'basis': 'MVP Rev. A (substitui J1 e F1)',
    'nc': [],
    'names': {'1': '+12V', '2': 'GND'},
    'types': {'1': 'power_out', '2': 'power_in'},
    'min_spec': '12,0 V DC regulados, I_limit 250-300 mA',
    'in_bom': False,
}
components.insert(0, psu)
byref['PSU_12V'] = psu

# 2. Diodos de clamp HI_Z -> 1N4007
for ref in ('D6', 'D7', 'D13', 'D14'):
    byref[ref].update(
        value='1N4007',
        package='DO-41',
        min_spec='1N4007 (substitui 1N4148 no MVP academico)',
        note='Clamp simetrico +/-2*Vf em torno de VREF_OP; capacitancia maior irrelevante em audio de guitarra.',
    )

# 3. Capacitores: apenas ceramicos ou eletroliticos polarizados (pin 1 = '+', pin 2 = '-')
# C2 e C16: lado op-amp/TL072 (+5,5 V) eh sempre positivo frente a ADC_BIAS (+2,4 V)
for ref in ('C2', 'C16'):
    byref[ref].update(
        kind='CP',
        value='10 uF',
        package='Eletrolítico radial >=25 V',
        names={'1': '+', '2': '-'},
        min_spec='10 uF >=25 V eletrolítico; + no lado R18/R20 (VREF_OP ~5,5 V), - no lado AINA (2,4 V)',
        note='MVP apenas ceramicos/eletroliticos: polaridade DC fixa +3,1 V para lado TL072.',
    )

# C10 e C11: lado R1/R7 (VREF_OP ~5,5 V) eh positivo frente a AOUTA_P/N (~2,4 V); inverte pinos 1/2 p/ + em pin 1
byref['C10']['pins'] = {'1': 'DAC_AC_P', '2': 'AOUTA_P'}
byref['C11']['pins'] = {'1': 'DAC_AC_N', '2': 'AOUTA_N'}
for ref in ('C10', 'C11'):
    byref[ref].update(
        kind='CP',
        value='10 uF',
        package='Eletrolítico radial >=25 V',
        names={'1': '+', '2': '-'},
        min_spec='10 uF >=25 V eletrolítico; + no lado R1/R7 (VREF_OP ~5,5 V), - no lado CS4272 AOUTA (2,4 V)',
        note='Pinos reordenados (1=+, 2=-) para refletir polaridade DC correta no MVP com eletrolitico.',
    )

# C5 e C12: confirmar polaridade explicita
byref['C5']['names'] = {'1': '+', '2': '-'}
byref['C5']['pins']['2'] = 'OUT_PRE'
byref['C5']['note'] = 'Eletrolítico: + em LP2 (~5,5 V), - em OUT_PRE (ligado direto a J3.1).'
byref['C12']['names'] = {'1': '+', '2': '-'}
for ref in ('C30', 'C32', 'C33', 'C37', 'C38', 'C40'):
    byref[ref]['kind'] = 'CP'
    byref[ref]['names'] = {'1': '+', '2': '-'}

# C1, C4, C6, C14, C18, C19, C20, C35, C36 -> ceramicos >=25 V
ceramic_notes = {
    'C1': 'Cerâmico >=25 V (substitui filme/C0G no MVP; corte passa-altas segue << 82 Hz)',
    'C14': 'Cerâmico 1 uF >=25 V (NAO usar eletrolitico em VCOM ~25 kohm para evitar fuga DC)',
    'C4': 'Cerâmico >=25 V (filtro RC pos-DAC)',
    'C6': 'Cerâmico >=25 V (filtro RC pos-DAC)',
    'C20': 'Cerâmico >=25 V (filtro diferencial ADC pinos 17/16)',
    'C35': 'Cerâmico 100 pF >=25 V (Filtro RF modo comum ADC AINA_P — MANTIDO da Rev 4.9/4.10)',
    'C36': 'Cerâmico 100 pF >=25 V (Filtro RF modo comum ADC AINA_N — MANTIDO da Rev 4.9/4.10)',
}
for ref, ntxt in ceramic_notes.items():
    byref[ref]['package'] = 'Cerâmico >=25 V'
    byref[ref]['note'] = ntxt

# 4. Saida direta (sem K1/D16) e Reset direto (sem Folha 9)
byref['J3']['pins']['1'] = 'OUT_PRE'
byref['H_STM32']['pins']['P1.38'] = 'CODEC_RST'
byref['R13']['note'] = 'Pull-down passivo 10k mantém /RST LOW com STM desligado; energizar 12 V antes da USB STM.'

# 5. ESP32 3V3 agora sem conexao externa (mantem GND comum e UART direta via 2x 1k)
byref['H_ESP32']['pins']['3V3'] = None
byref['H_ESP32']['nc'] = ['VIN', '3V3']
byref['H_ESP32']['names']['3V3'] = '3V3 / NC externo'

# Adiciona 2 resistores de protecao em serie na UART direta
uart_res = [
    {
        'ref': 'R_UTX',
        'kind': 'R',
        'value': '1 kohm',
        'pins': {'1': 'STM_UART_TX', '2': 'ESP_UART_RX'},
        'sheet': 5,
        'function': 'Limitador serie anti-backpower UART STM32 TX -> ESP32 RX2',
        'status': 'já disponível (estoque R/C)',
        'package': 'Axial DIN0207, 1/4 W, 1%',
        'note': 'Limita corrente ESD caso apenas uma placa esteja energizada via USB (115200 bps).',
        'basis': 'MVP Rev. A (substitui U6 ISO7721DR)',
        'nc': [],
        'names': {'1': '1', '2': '2'},
        'types': {'1': 'passive', '2': 'passive'},
        'min_spec': '1 kohm 1%..5%, 0,25 W',
    },
    {
        'ref': 'R_URX',
        'kind': 'R',
        'value': '1 kohm',
        'pins': {'1': 'ESP_UART_TX', '2': 'STM_UART_RX'},
        'sheet': 5,
        'function': 'Limitador serie anti-backpower UART ESP32 TX2 -> STM32 RX',
        'status': 'já disponível (estoque R/C)',
        'package': 'Axial DIN0207, 1/4 W, 1%',
        'note': 'Limita corrente ESD caso apenas uma placa esteja energizada via USB (115200 bps).',
        'basis': 'MVP Rev. A (substitui U6 ISO7721DR)',
        'nc': [],
        'names': {'1': '1', '2': '2'},
        'types': {'1': 'passive', '2': 'passive'},
        'min_spec': '1 kohm 1%..5%, 0,25 W',
    },
]
components.extend(uart_res)

# Validacao estrita de integridade de redes e contagem BOM
bom_parts = [c for c in components if c.get('in_bom', True)]
assert len(bom_parts) == 91, f'Esperado 91 componentes reais, obtido {len(bom_parts)}'
caps = [c for c in bom_parts if c['ref'].startswith('C')]
ress = [c for c in bom_parts if c['ref'].startswith('R')]
assert len(caps) == 36, len(caps)
assert len(ress) == 32, len(ress)

nets = defaultdict(list)
for c in components:
    for p, n in c['pins'].items():
        if n is not None:
            nets[n].append((c['ref'], p))
dangling = {n: v for n, v in nets.items() if len(v) < 2}
assert not dangling, f'Redes soltas encontradas: {dangling}'

out = {
    'revision': 'MVP-Rev.A',
    'author': raw.get('author', 'Rodrigues M. Lima'),
    'release_status': 'MVP-Rev.A (prototipo academico em perfboard, fonte de bancada, UART direta 2x1k, apenas C/E e 1N4007)',
    'architecture': 'Fonte bancada 12V (I_limit 250-300 mA) -> D1 1N4007 -> +RAW (TL072 + CW7805 -> +5VA via J5); STM32 e ESP32 USBs proprias; UART direta via 2x 1k; saida direta C5/R6 -> J3; C35/C36 mantidos; apenas ceramicos e eletroliticos.',
    'status': 'Pronto para montagem controlada em bancada apos conferir pinagem CW7805 e implementar SAI4/DMA + PC2_C/PC3_C no firmware.',
    'components': components,
}
DST_MODEL.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(f'MVP model written: {len(bom_parts)} real BOM components ({len(caps)} C, {len(ress)} R, {len(bom_parts)-len(caps)-len(ress)} other), {len(nets)} nets, 0 dangling.')
