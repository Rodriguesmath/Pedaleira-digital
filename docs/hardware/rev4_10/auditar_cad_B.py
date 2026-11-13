#!/usr/bin/env python3
"""Independent CAD audit for Phase 4.10B (Blockers 3 + 4 on top of Phase A invariants)."""
import argparse
import csv
import json
import unittest
import auditar_cad_A

auditar_cad_A.EVIDENCE = auditar_cad_A.OUT / 'REVISOES/CAD_B_TEMP'


class AuditCAD_B(auditar_cad_A.AuditCAD):
    def test_all_component_references_and_bom_values(self):
        comps = {c.attrib['ref']: c for c in self.xml.findall('components/comp')}
        self.assertEqual(len(self.parts), 183)
        self.assertEqual(set(comps), set(self.parts))
        with (auditar_cad_A.OUT / 'BOM_rev4_10.csv').open(encoding='utf-8-sig') as f:
            bom = {r['Referência']: r for r in csv.DictReader(f)}
        self.assertEqual(set(bom), set(self.parts))
        for ref, p in self.parts.items():
            self.assertEqual(comps[ref].findtext('value'), p['value'], ref)
            self.assertEqual(bom[ref]['Valor'], p['value'], ref)

    def test_cw_is_hypothesis_not_identified_regulator(self):
        p = self.parts['U5']
        self.assertEqual(p['value'], 'CW7805')
        self.assertIn('NÃO QUALIFICADA', p['note'])
        self.assertIn('não são limites comprovados', p['min_spec'])
        self.assertIn('4.10B', self.model['release_status'])

    def test_all_sheets_every_model_terminal_rendered(self):
        d = json.loads((auditar_cad_A.OUT / 'diagram_layout.json').read_text())
        self.assertEqual(len(d['pages']), 10)
        self.assertEqual({int(s) for s in d['pages']}, set(range(1, len(d['pages']) + 1)))
        seen = {(i['ref'], pin) for i in d['instances'] for pin in i['pins']}
        expected = {(p['ref'], pin) for p in self.parts.values() for pin in p['pins']}
        self.assertEqual(seen, expected)
        self.assertEqual(len(list((auditar_cad_A.OUT / 'kicad').glob('folha_*.kicad_sch'))), len(d['pages']))

    def test_official_footprints_and_zero_erc_violations(self):
        comps = {c.attrib['ref']: c for c in self.xml.findall('components/comp')}
        self.assertEqual(comps['U6'].findtext('footprint'), 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
        self.assertEqual(comps['K1'].findtext('footprint'), 'Relay_THT:Relay_SPDT_Omron_G5V-1')
        for ref in ('U7', 'U8', *(f'Q{i}' for i in range(1, 23))):
            self.assertEqual(comps[ref].findtext('footprint'), 'Package_TO_SOT_THT:TO-92_Inline', ref)
        j = json.loads((auditar_cad_A.EVIDENCE / 'ERC_fresh.json').read_text())
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
        self.assertEqual(p['Q5']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINA_P'})
        self.assertEqual(p['Q6']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINA_N'})
        self.assertEqual(p['Q7']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'ADC_B_SW'})
        self.assertEqual(p['Q8']['pins'], {'1': 'GND', '2': 'SHUNT_EN', '3': 'AINB_CM'})
        self.assertEqual(p['R47']['pins'], {'1': 'ADC_BIAS', '2': 'ADC_B_SW'})

    def test_phase_b_active_adc_clamp_blocker3(self):
        p = self.parts
        for old in ('D9', 'D10', 'D11', 'D12'):
            self.assertNotIn(old, p)
        self.assertEqual(p['Q9']['value'], '2N3904')
        self.assertEqual(p['Q9']['pins'], {'1': 'V_BIAS_HI', '2': 'V_REF_HI', '3': '+5VA'})
        self.assertEqual(p['Q10']['value'], '2N3906')
        self.assertEqual(p['Q10']['pins'], {'1': 'V_BIAS_LO', '2': 'V_REF_LO', '3': 'GND'})
        for ch_net, pnp, npn in [('AINA_P', 'Q11', 'Q12'), ('AINA_N', 'Q13', 'Q14')]:
            self.assertEqual(p[pnp]['value'], '2N3906')
            self.assertEqual(p[pnp]['pins'], {'1': ch_net, '2': 'V_BIAS_HI', '3': 'GND'})
            self.assertEqual(p[npn]['value'], '2N3904')
            self.assertEqual(p[npn]['pins'], {'1': ch_net, '2': 'V_BIAS_LO', '3': '+5VA'})
        for ref in ('R48', 'R49', 'R50', 'R51', 'R52', 'R53', 'C45', 'C46', 'C47', 'C48'):
            self.assertEqual(p[ref]['sheet'], 10)

    def test_phase_b_fail_safe_mute_relay_blocker4(self):
        p = self.parts
        self.assertEqual(p['C5']['pins'], {'1': 'LP2', '2': 'OUT_PRE'})
        self.assertEqual(p['R6']['value'], '47 kohm')
        self.assertEqual(p['R6']['pins'], {'1': 'OUT_PRE', '2': 'GND'})
        self.assertEqual(p['K1']['value'], 'G5V-1-DC12')
        self.assertEqual(p['K1']['pins'], {'1': 'GND', '2': 'K1_COILP', '5': 'JACK_OUT', '6': 'JACK_OUT', '9': 'GND', '10': 'OUT_PRE'})
        self.assertEqual(p['D16']['value'], '1N4148')
        self.assertEqual(p['D16']['pins'], {'1': 'GND', '2': 'K1_COILP'})
        self.assertEqual(p['U8']['value'], 'TL431ACZ')
        self.assertEqual(p['D17']['value'], 'BZX55C4V7')
        self.assertEqual(p['C49']['value'], '47 uF')
        self.assertEqual(p['Q21']['value'], '2N3906')
        self.assertEqual(p['Q21']['pins'], {'1': '+RAW', '2': 'Q21_B', '3': 'K1_COILP'})
        for ref in ('Q15', 'Q16', 'Q17', 'Q18', 'Q19', 'Q20', 'Q22'):
            self.assertEqual(p[ref]['sheet'], 10)
        for i in (54, 55, 56, 57, 58, 59, 60, 62, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75):
            self.assertEqual(p[f'R{i}']['sheet'], 10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', action='store_true')
    args, unittest_args = parser.parse_known_args()
    if args.export:
        auditar_cad_A.export()
    auditar_cad_A.EVIDENCE.mkdir(parents=True, exist_ok=True)
    summary = auditar_cad_A.summarize()
    summary['scope'] = 'Phase 4.10B CAD consistency; bench prerequisites & Phase C (full BOM footprints) pending'
    summary['remaining_prerequisites_and_phases'] = [
        'A410-01: generic CW7805 physical sample pinout/stability qualification on bench',
        'A410-05/A410-07: physical inspection of WeAct 3V3 buck IC & ESP32 module (GPIO16/17 free)',
        'A410-08 (Phase C): complete footprint validation across all BOM items',
    ]
    (auditar_cad_A.EVIDENCE / 'resultado_cad_B.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    unittest.main(argv=[__file__, *unittest_args], verbosity=2)
