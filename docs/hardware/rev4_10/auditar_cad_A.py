#!/usr/bin/env python3
"""Auditoria D read-only do CAD; reexporta somente evidências em REVISOES/CAD_D_TEMP.

Sem --export usa a evidência previamente exportada. Com --export executa KiCad
real, sem exclusões. PASS dos testes significa consistência do CAD, nunca gate A.
"""
import argparse
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'output/REV410_ENTREGA'
EVIDENCE = OUT / 'REVISOES/CAD_D_TEMP'
KICAD_ROOT = Path('/home/rodrigues/.cache/pedaleira-tools/root')


def export():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    cli = KICAD_ROOT / 'usr/bin/kicad-cli'
    env = dict(os.environ, LD_LIBRARY_PATH=str(KICAD_ROOT / 'usr/lib64'))
    sch = OUT / 'kicad/pedaleira_digital_rev4_10.kicad_sch'
    for log, args in [('export.log', ['sch', 'export', 'netlist', '--format', 'kicadxml', '--output', str(EVIDENCE / 'netlist_fresh.xml'), str(sch)]),
                      ('ERC.log', ['sch', 'erc', '--format', 'json', '--severity-all', '--output', str(EVIDENCE / 'ERC_fresh.json'), str(sch)])]:
        r = subprocess.run([str(cli), *args], env=env, text=True, capture_output=True)
        (EVIDENCE / log).write_text(r.stdout + r.stderr)
        if r.returncode:
            raise RuntimeError(f'{log}: KiCad exit {r.returncode}; see complete log')


def load():
    model = json.loads((OUT / 'circuito_rev4_10.json').read_text())
    parts = {c['ref']: c for c in model['components']}
    xml = ET.parse(EVIDENCE / 'netlist_fresh.xml').getroot()
    actual = {}
    endpoint = {}
    for n in xml.findall('nets/net'):
        nodes = {(x.attrib['ref'], x.attrib['pin']) for x in n.findall('node') if x.attrib['ref'] in parts}
        for pin in nodes:
            endpoint[pin] = n.attrib['name']
        if nodes and not n.attrib['name'].startswith('unconnected-'):
            actual[n.attrib['name']] = nodes
    expected = collections.defaultdict(set)
    for c in parts.values():
        for pin, net in c['pins'].items():
            if net is not None:
                expected[net].add((c['ref'], pin))
    return model, parts, xml, expected, actual, endpoint


def summarize():
    model, parts, xml, expected, actual, endpoint = load()
    erc = json.loads((EVIDENCE / 'ERC_fresh.json').read_text())
    violations = [dict(sheet=s['path'], **v) for s in erc['sheets'] for v in s['violations']]
    return {'scope': 'CAD consistency only; Phase 4.10A electrical design fixes applied, bench prerequisites & Phases B/C pending',
            'components': len(parts), 'partitions': len(expected),
            'connected_terminals': sum(len(n) for n in expected.values()),
            'sheet_count': len({c['sheet'] for c in parts.values()}),
            'erc_violations': violations, 'erc_ignored_checks': erc['ignored_checks'],
            'empty_footprints': [c.attrib['ref'] for c in xml.findall('components/comp') if not c.findtext('footprint')],
            'cw_qualification': 'PENDING, generic component preserved by user decision',
            'containment': 'J5 open AND U2 physically absent until bench prerequisites + Phases B/C complete; no CW qualification implied',
            'remaining_prerequisites_and_phases': [
                'A410-01: generic CW7805 physical sample pinout/stability qualification on bench',
                'A410-05/A410-07: physical inspection of WeAct 3V3 buck IC & ESP32 module (GPIO16/17 free)',
                'A410-04 (Phase B): BAT85 replacement with non-distorting active ADC clamp within [GND-0.3, VA+0.3]',
                'A410-06 (Phase B): fail-safe physical mute at DAC/line output stage',
                'A410-08 (Phase C): complete footprint validation across all BOM items'],
            'sha256': {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [OUT / 'circuito_rev4_10.json', OUT / 'diagram_layout.json',
                                 OUT / 'BOM_rev4_10.csv', *sorted((OUT / 'kicad').glob('*.kicad_sch'))]}}


class AuditCAD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.parts, cls.xml, cls.expected, cls.actual, cls.endpoint = load()

    def test_exact_net_partitions_not_just_labels(self):
        # Compare sets of complete pin groups; local KiCad sheet prefixes and
        # labels do not hide shorts or disconnected aliases.
        self.assertEqual({frozenset(v) for v in self.expected.values()},
                         {frozenset(v) for v in self.actual.values()})
        self.assertEqual(len(self.expected), len(self.actual))

    def test_all_component_references_and_bom_values(self):
        comps = {c.attrib['ref']: c for c in self.xml.findall('components/comp')}
        self.assertEqual(len(self.parts), 139)
        self.assertEqual(set(comps), set(self.parts))
        with (OUT / 'BOM_rev4_10.csv').open(encoding='utf-8-sig') as f:
            bom = {r['Referência']: r for r in csv.DictReader(f)}
        self.assertEqual(set(bom), set(self.parts))
        for ref, p in self.parts.items():
            self.assertEqual(comps[ref].findtext('value'), p['value'], ref)
            self.assertEqual(bom[ref]['Valor'], p['value'], ref)

    def test_no_external_connection_to_usb_5v_headers(self):
        for key in [('H_STM32', 'P1.2'), ('H_ESP32', 'VIN')]:
            self.assertIsNone(self.parts[key[0]]['pins'][key[1]])
            self.assertTrue(self.endpoint[key].startswith('unconnected-'))

    def test_cw_analog_split_and_test_connector(self):
        p = self.parts
        self.assertEqual(p['J5']['pins'], {'1': '+5V_CW', '2': '+5VA'})
        self.assertIn('aberto', p['J5']['value'])
        self.assertIn('SEM shunt', p['J5']['min_spec'])
        self.assertEqual(p['J4']['pins'], {'1': '+5V_CW', '2': 'GND'})
        self.assertEqual(p['D8']['pins'], {'1': '+5V_CW', '2': '+RAW'})
        self.assertNotEqual(self.endpoint['U5', '3'], self.endpoint['U2', '20'])
        for ref in ('C22', 'R21', 'C37'):
            self.assertEqual(p[ref]['pins']['1'], '+5V_CW')

    def test_cw_is_hypothesis_not_identified_regulator(self):
        p = self.parts['U5']
        self.assertEqual(p['value'], 'CW7805')
        self.assertIn('NÃO QUALIFICADA', p['note'])
        self.assertIn('não são limites comprovados', p['min_spec'])
        self.assertIn('BLOCKED', self.model['release_status'])

    def test_codec_all_supply_pins_and_local_digital_pullups(self):
        p = self.parts
        for pin in ('9', '10'):
            self.assertEqual(p['U2']['pins'][pin], '+3V3_STM')
        self.assertEqual(p['U2']['pins']['20'], '+5VA')
        for pin in ('8', '21'):
            self.assertEqual(p['U2']['pins'][pin], 'GND')
        for ref in ('R11', 'R12'):
            self.assertEqual(p[ref]['pins']['1'], '+3V3_STM')

    def test_iso_exact_d8_pin_mapping_and_no_parallel_uart(self):
        p = self.parts
        self.assertEqual(p['U6']['value'], 'ISO7721DR')
        self.assertEqual(p['U6']['pins'], {'1': '+3V3_STM', '2': 'STM_UART_RX',
            '3': 'STM_UART_TX', '4': 'GND', '5': 'GND', '6': 'ESP_UART_RX',
            '7': 'ESP_UART_TX', '8': '+3V3_ESP'})
        self.assertEqual(self.expected['STM_UART_RX'], {('U6', '2'), ('H_STM32', 'P1.39')})
        self.assertEqual(self.expected['ESP_UART_RX'], {('U6', '6'), ('H_ESP32', 'RX2')})
        self.assertEqual(self.expected['STM_UART_TX'], {('U6', '3'), ('H_STM32', 'P1.40'), ('R31', '2')})
        self.assertEqual(self.expected['ESP_UART_TX'], {('U6', '7'), ('H_ESP32', 'TX2'), ('R32', '2')})

    def test_iso_bypass_bleeders_and_idle_pullups(self):
        for cap, bleed, pull, rail, tx in [('C42', 'R29', 'R31', '+3V3_STM', 'STM_UART_TX'),
                                          ('C43', 'R30', 'R32', '+3V3_ESP', 'ESP_UART_TX')]:
            self.assertEqual(self.parts[cap]['pins'], {'1': rail, '2': 'GND'})
            self.assertEqual(self.parts[cap]['value'], '100 nF')
            self.assertEqual(self.parts[bleed]['pins'], {'1': rail, '2': 'GND'})
            self.assertEqual(self.parts[bleed]['value'], '10 kohm')
            self.assertEqual(self.parts[pull]['pins'], {'1': rail, '2': tx})
            self.assertEqual(self.parts[pull]['value'], '47 kohm')

    def test_all_sheets_every_model_terminal_rendered(self):
        d = json.loads((OUT / 'diagram_layout.json').read_text())
        self.assertEqual(len(d['pages']), 9)
        self.assertEqual({int(s) for s in d['pages']}, set(range(1, len(d['pages']) + 1)))
        seen = {(i['ref'], pin) for i in d['instances'] for pin in i['pins']}
        expected = {(p['ref'], pin) for p in self.parts.values() for pin in p['pins']}
        self.assertEqual(seen, expected)
        self.assertEqual(len(list((OUT / 'kicad').glob('folha_*.kicad_sch'))), len(d['pages']))

    def test_official_footprints_and_zero_erc_violations(self):
        comps = {c.attrib['ref']: c for c in self.xml.findall('components/comp')}
        self.assertEqual(comps['U6'].findtext('footprint'), 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
        for ref in ('U7', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8'):
            self.assertEqual(comps[ref].findtext('footprint'), 'Package_TO_SOT_THT:TO-92_Inline', ref)
        j = json.loads((EVIDENCE / 'ERC_fresh.json').read_text())
        self.assertEqual(j['ignored_checks'], [])
        violations = [dict(sheet=s['path'], **v) for s in j['sheets'] for v in s['violations']]
        self.assertEqual(violations, [])

    def test_phase_a_reset_interlock_and_offstate_containment(self):
        p = self.parts
        self.assertEqual(p['H_STM32']['pins']['P1.38'], 'CODEC_RST_CMD')
        self.assertEqual(p['R39']['pins'], {'1': 'CODEC_RST_CMD', '2': 'CODEC_RST'})
        self.assertEqual(p['U2']['pins']['14'], 'CODEC_RST')
        self.assertEqual(p['R13']['pins'], {'1': 'CODEC_RST', '2': 'GND'})
        self.assertEqual(p['U7']['value'], 'TL431ACZ')
        self.assertEqual(p['U7']['pins'], {'1': 'VA_REF', '2': 'GND', '3': 'VA_K'})
        self.assertEqual(p['Q1']['pins'], {'1': 'GND', '2': 'RST_CLAMP_B', '3': 'CODEC_RST'})
        self.assertEqual(p['Q2']['pins'], {'1': 'GND', '2': 'Q2_B', '3': 'RST_CLAMP_B'})
        self.assertEqual(p['D15']['pins'], {'1': '+RAW', '2': 'RAW_D'})
        self.assertEqual(p['C44']['pins'], {'1': 'V_HOLD', '2': 'GND'})
        self.assertEqual(p['Q4']['pins'], {'1': 'GND', '2': 'Q4_B', '3': 'SHUNT_EN'})
        self.assertEqual(p['Q5']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINA_P'})
        self.assertEqual(p['Q6']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINA_N'})
        self.assertEqual(p['Q7']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'ADC_B_SW'})
        self.assertEqual(p['Q8']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINB_CM'})
        self.assertEqual(p['R47']['pins'], {'1': 'ADC_BIAS', '2': 'ADC_B_SW'})
        # Phase B risks remain honestly open and unmasked in Phase A.
        self.assertEqual(p['D9']['value'], 'BAT85')
        self.assertEqual(p['D11']['value'], 'BAT85')
        self.assertIn('J3', p)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.export:
        export()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'resultado_cad_D.json').write_text(json.dumps(summarize(), ensure_ascii=False, indent=2) + '\n')
    unittest.main(argv=[__file__, *unittest_args], verbosity=2)
