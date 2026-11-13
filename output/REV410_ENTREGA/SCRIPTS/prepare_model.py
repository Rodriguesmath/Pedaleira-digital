#!/usr/bin/env python3
"""Build the controlled 4.10A candidate from the immutable 4.9 audit errata.

This is a candidate, not an approval. Firmware and analog signal gains stay intact.
The CW pin numbering remains the inherited hypothesis pending physical identity.
"""
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'output/auditoria_rev49/VALIDACAO/circuito_rev49_errata_documental.json'
model = copy.deepcopy(json.loads(SOURCE.read_text()))
model.update(revision='4.10A-candidate', release_status='BLOCKED - alimentação em revisão')
parts = {a['ref']: a for a in model['components']}
for a in parts.values():
    for p, n in a['pins'].items():
        a['pins'][p] = {'+5V': '+5VA', '+3V3': '+3V3_STM'}.get(n, n)

stm, esp, cw = (parts[r] for r in ('H_STM32', 'H_ESP32', 'U5'))
stm['pins']['P1.2'] = None
stm['nc'] = ['P1.2']
stm['names']['P1.2'] = '5V header / NC externo'
stm['note'] = 'Alimentação exclusiva pela USB própria; não alimentar header 5V pelo CW. VD/VL saem de P2.2; orçamento da placa ainda condicionado.'
esp['pins'].update(VIN=None, RX2='ESP_UART_RX', TX2='ESP_UART_TX', **{'3V3': '+3V3_ESP'})
esp['nc'] = ['VIN']
esp['names']['3V3'] = '3V3 saída local'
esp['types']['3V3'] = 'power_out'
esp['note'] = 'Alimentação exclusiva pela USB própria. VIN sem conexão externa. Confirmar variante WROOM e identificação do header 3V3; sem pressupor estoque de outro modelo.'
stm['pins'].update({'P1.40': 'STM_UART_TX', 'P1.39': 'STM_UART_RX'})

# The bleeder and reserve stay on the CW side of the normally open test link.
for r, p in [('U5', '3'), ('C22', '1'), ('R21', '1'), ('C37', '1'),
             ('D8', '1'), ('TP2', '1'), ('J4', '1')]:
    parts[r]['pins'][p] = '+5V_CW'
cw.update(function='Saída nominal 5 V apenas para VA; USBs independentes',
          min_spec='Identificar IN/GND/OUT e fabricante antes de montar; saída de projeto 4,75..5,25 V a >=60 mA; não são limites comprovados do CW',
          note='Mantido por decisão do usuário. Pinagem 1/2/3 herdada é hipótese NÃO QUALIFICADA. Nenhum parâmetro térmico/ST atribuído ao exemplar. J5 aberto por padrão; não instalar codec antes de qualificar fonte.')
parts['J4'].update(value='Teste CW 5 V', function='Conector de carga artificial no lado CW, antes de J5; nunca USB',
                   package='Borne THT 2 vias 5,08 mm', note='Somente saída para carga de teste. Não ligar a STM/ESP/USB.')
parts['C37']['function'] = 'Reserva da saída CW antes do seccionamento J5'
parts['R15']['package'] = parts['R16']['package'] = 'Axial DIN0207, 1/4 W, 0,1%'
for r in ('R15', 'R16'):
    parts[r]['function'] = 'Polarização da entrada ADC em ADC_BIAS independente de VCOM'
parts['C5']['function'] = 'Acoplamento de saída; positivo em LP2'
for r in ('C30', 'C32'):
    parts[r]['function'] = 'Reserva local entre RAW e GND nos pinos 8/4 do TL072'

def add(ref, kind, value, pins, sheet, function, package, min_spec, names=None, types=None, note=''):
    assert ref not in parts
    a = dict(ref=ref, kind=kind, value=value, pins=pins, sheet=sheet,
             function=function, package=package, min_spec=min_spec,
             status='necessário adquirir / conferir estoque', names=names or {},
             types=types or {}, nc=[p for p,n in pins.items() if n is None],
             note=note, basis='Revisão 4.10A; ver REVISOES/ e fontes oficiais')
    model['components'].append(a)
    parts[ref] = a

add('J5', 'LINK', 'VA / aberto', {'1': '+5V_CW', '2': '+5VA'}, 1,
    'Seccionamento físico CW -> VA; aberto por padrão', 'Header 1x02 2,54 mm + shunt removível',
    'Manter SEM shunt até qualificação da fonte; codec removido nos ensaios iniciais',
    note='Não há continuidade interna com shunt removido. Não é fusível nem proteção automática contra falha do CW.')

# ISO7721D pin map is intentionally separate from the 16-pin DW variant.
add('U6', 'ISOLATOR', 'ISO7721DR',
    {'1': '+3V3_STM', '2': 'STM_UART_RX', '3': 'STM_UART_TX', '4': 'GND',
     '5': 'GND', '6': 'ESP_UART_RX', '7': 'ESP_UART_TX', '8': '+3V3_ESP'}, 8,
    'UART bidirecional entre alimentações independentes; cada I/O pertence ao seu domínio',
    'SOIC-8 D, 3,9x4,9 mm, pitch 1,27 mm; adaptador SOIC8-DIP8 para perfboard',
    'Texas Instruments ISO7721DR, default HIGH; NÃO ISO7721F nem DW16',
    names={'1':'VCC1','2':'OUTA','3':'INB','4':'GND1','5':'GND2','6':'OUTB','7':'INA','8':'VCC2'},
    types={'1':'power_in','2':'output','3':'input','4':'power_in','5':'power_in','6':'output','7':'input','8':'power_in'},
    note='Aquisição necessária, estoque não confirmado. GND1/GND2 unidos ao GND do sistema: não há alegação de isolamento galvânico entre placas.')
for r, rail in [('C42', '+3V3_STM'), ('C43', '+3V3_ESP')]:
    add(r, 'C', '100 nF', {'1':rail,'2':'GND'}, 8, 'Bypass local de U6', 'Cerâmico THT', '100 nF X7R >=16 V, próximo dos pinos VCC/GND')
for r, rail in [('R29', '+3V3_STM'), ('R30', '+3V3_ESP')]:
    add(r, 'R', '10 kohm', {'1':rail,'2':'GND'}, 8, 'Descarga local e estado sem alimentação', 'Axial DIN0207 1/4 W 1%', '10 kohm 1%, 0,25 W')
for r, rail, tx in [('R31', '+3V3_STM', 'STM_UART_TX'), ('R32', '+3V3_ESP', 'ESP_UART_TX')]:
    add(r, 'R', '47 kohm', {'1':rail,'2':tx}, 8, 'UART idle HIGH quando TX está em alta impedância', 'Axial DIN0207 1/4 W 1%', '47 kohm 1%, 0,25 W')

parts['U6']['footprint'] = 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
parts['U6']['note'] += ' Orçamento 4 mA por domínio; saída RX com carga de projeto <=15 pF. Estado lógico durante brownout indeterminado.'

model['architecture'] = 'STM USB própria; ESP USB própria; CW somente VA através de J5 aberto por padrão; VD/VL 3V3_STM; UART U6 dual-supply; GND comum'
Path(__file__).with_name('circuito_rev4_10.json').write_text(json.dumps(model, ensure_ascii=False, indent=2)+'\n')
print(f'4.10A candidate: {len(parts)} components; no approval implied')
