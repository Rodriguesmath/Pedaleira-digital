#!/usr/bin/env python3
"""Verificação D: aritmética independente UART Rev4.10A, não ensaio físico.

python docs/hardware/rev4_10/test_interfaces_indep.py
Produz REVISOES/FONTES_UART/calculos_interfaces.json e executa unittest.
Os limites de 3V3 são requisitos de projeto, não medições das DevKits.
"""
import hashlib
import itertools
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/REV410_ENTREGA/REVISOES/FONTES_UART"
BAUD = 115200
BIT = 1 / BAUD
VOLTAGES = (3.1, 3.3, 3.4, 3.6)
PARAMETERS = {
    "iso": {"manufacturer": "Texas Instruments", "document": "SLLSEP3G",
            "revision": "G, May 2024", "url": "https://www.ti.com/lit/ds/symlink/iso7721.pdf",
            "pins_page": 6, "operating_page": 8, "dc_page": 15,
            "timing_page": 17, "load_page": 22, "functional_modes_page": 25,
            "decoupling_page": 31, "v_min": 2.25, "v_max": 5.5,
            "uvlo_pd_max": 1.7, "uvlo_pu_min": 2.25,
            "voh_drop_max": .3, "vol_max": .3, "output_test_A": .002,
            "vih_factor": .7, "vil_factor": .3,
            "tpd_max_s": 18.5e-9, "pwd_max_s": 5.9e-9,
            "default_delay_max_s": .3e-6, "cl_test_F": 15e-12,
            "cl_test_tolerance": .2, "icc_dc_low_max_A": .0034,
            "icc_dc_high_max_A": .0021, "icc_1Mbps_max_A": .0028,
            "input_current_max_A": 10e-6},
    "stm": {"manufacturer": "STMicroelectronics", "document": "DS13313",
            "revision": "5, May 2025", "url": "https://www.st.com/resource/en/datasheet/stm32h723vg.pdf",
            "pin_table_page": 64, "dc_table_51_page": 126,
            "output_table_52_page": 129, "rx_pin": "PD9 FT_h",
            "vih_factor": .7, "vil_factor": .3,
            "voh_drop_max": .4, "vol_max": .4,
            "rx_leak_A": 250e-9,
            "local_pdf_download": "FAILED: st.com and st.com.cn timed out; official PDF verified via web tool"},
    "esp": {"manufacturer": "Espressif Systems", "document": "ESP32 Series Datasheet",
            "revision": "5.3", "url": "https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf",
            "dc_table_5_3_page": 52, "condition": "DC characteristics (3.3 V, 25 C); range extension is design calculation, not full PVT qualification",
            "vih_factor": .75, "vil_factor": .25,
            "voh_factor": .8, "vol_factor": .1, "rx_leak_A": 50e-9},
    "lvc": {"manufacturer": "Texas Instruments", "document": "SCES296AG",
            "revision": "AG, October 2025", "url": "https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf",
            "pins_page": 3, "recommended_page": 5, "electrical_page": 6,
            "ii_A": 5e-6, "ii_condition": "VI=5.5 V or GND; VCC=0..5.5 V",
            "ioff_A": 10e-6, "ioff_condition": "VI or VO=5.5 V; VCC=0 V",
            "powered_high_output_leak_max_A": None,
            "output_leak_qualification_budget_A": 10e-6,
            "powered_high_output_leak_note": "10uA qualification budget only; NOT Ioff extrapolated to powered IOZ"},
}


def parallel(a, b):
    return a * b / (a + b)


def lvc_corners():
    """KCL of divider at resistor tolerance corners and receiver leakage."""
    result = []
    for v, tu, td, leak_rx in itertools.product(VOLTAGES, (.99, 1.01), (.99, 1.01), (50e-9, 250e-9)):
        ru, rd = 4700 * tu, 22000 * td
        req = parallel(ru, rd)
        # Explicit assumed qualification limit because TI does not specify powered IOZ.
        sink = PARAMETERS["lvc"]["output_leak_qualification_budget_A"] + leak_rx
        high = (v / ru - sink) / (1 / ru + 1 / rd)
        esp_thresh = .75 * v
        t_thresh = -req * 100e-12 * math.log(1 - esp_thresh / high)
        result.append({"vcc_V": v, "ru_Ohm": ru, "rd_Ohm": rd,
                       "sink_assumption_A": sink, "high_V": high,
                       "esp_high_margin_V": high - esp_thresh,
                       "stm_high_margin_V": high - .7 * v,
                       "t_esp_threshold_s_CL100pF": t_thresh,
                       "rise_10_90_s_CL100pF": math.log(9) * req * 100e-12,
                       "pullup_short_current_A": v / ru})
    return result


def iso_corners():
    """All four signal interfaces use their OWN local VDD, never remote VDD."""
    rows = []
    for stm_v, esp_v in itertools.product(VOLTAGES, repeat=2):
        rows.append({"stm_V": stm_v, "esp_V": esp_v,
                     "stm_tx_to_iso_high_margin_V": stm_v - .4 - .7 * stm_v,
                     "stm_tx_to_iso_low_margin_V": .3 * stm_v - .4,
                     "esp_tx_to_iso_high_margin_V": .8 * esp_v - .7 * esp_v,
                     "esp_tx_to_iso_low_margin_V": .3 * esp_v - .1 * esp_v,
                     "iso_to_stm_high_margin_V": stm_v - .3 - .7 * stm_v,
                     "iso_to_stm_low_margin_V": .3 * stm_v - .3,
                     "iso_to_esp_high_margin_V": esp_v - .3 - .75 * esp_v,
                     "iso_to_esp_low_margin_V": .25 * esp_v - .3})
    return rows


def receiver_state(transmitter_on, receiver_on):
    if not receiver_on:
        return "UNDETERMINED_LOCAL_OUTPUT; no remote DC signal path"
    return "DATA" if transmitter_on else "DEFAULT_HIGH_AFTER_tDO"


def iso_states():
    return [{"stm_usb": s, "esp_usb": e, "analog_12V": a,
             "rx_stm": receiver_state(e, s), "rx_esp": receiver_state(s, e),
             "remote_DC_signal_path": False}
            for s, e, a in itertools.product((False, True), repeat=3)]


def iso_voltage_state(vcc):
    if vcc <= 1.7:
        return "PD"
    if vcc >= 2.25:
        return "PU"
    return "UNDETERMINED"


def calculate():
    states = iso_states()
    transitions = [(i, j) for i, x in enumerate(states) for j, y in enumerate(states)
                   if sum(x[k] != y[k] for k in ("stm_usb", "esp_usb", "analog_12V")) == 1]
    return {"kind": "CALCULATED; not SPICE, physical measurement, or global gate approval",
            "parameters": PARAMETERS, "baud": BAUD, "bit_s": BIT,
            "iso_corners": iso_corners(), "lvc_conditional_corners": lvc_corners(),
            "states": states, "directed_single_source_transitions": transitions,
            "iso_timing_CL15pF": {"tpd_fraction_bit": 18.5e-9 / BIT,
                                  "pwd_fraction_bit": 5.9e-9 / BIT,
                                  "default_delay_fraction_bit": .3e-6 / BIT},
            "lvc_off_conditional_bounds": {
                "Y_V_10uA22k_1pct": 10e-6 * 22000 * 1.01,
                "rail_V_10uA10k_1pct": 10e-6 * 10000 * 1.01,
                "A_V_5uA47k_1pct": 5e-6 * 47000 * 1.01,
                "note": "Illustrative bounds at named leakage conditions, not proof at all ramp voltages"},
            "iso_budget": {"reserve_each_rail_A": .004,
                           "dc_low_plus_bleeder_max_A": .0034 + 3.6 / 9900,
                           "pullup47k_load_max_A": 3.6 / (47000 * .99) + 10e-6,
                           "rail_total_power_reserve_W": 2 * 3.6 * .004},
            "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in OUT.glob("*.pdf")}}


class TestInterfacesIndependent(unittest.TestCase):
    def test_primary_source_files(self):
        iso = (OUT / "ISO7721_TI.txt").read_text()
        self.assertIn("SLLSEP3G", iso)
        self.assertIn("The outputs are in undetermined state", iso)
        self.assertIn("VCCO - 0.3", iso)
        self.assertIn("18.5", iso)
        lvc = (OUT / "SN74LVC1G07_TI_SCES296AG.txt").read_text()
        self.assertIn("SCES296AG", lvc)
        self.assertIn("VI = 5.5 V or GND", lvc)

    def test_iso_all_local_logic_margins(self):
        for row in iso_corners():
            for key, value in row.items():
                if key.endswith("margin_V"):
                    self.assertGreater(value, 0, (key, row))

    def test_iso_receiver_margins_worst(self):
        rows = iso_corners()
        self.assertAlmostEqual(min(x["iso_to_esp_high_margin_V"] for x in rows), .475)
        self.assertAlmostEqual(min(x["iso_to_esp_low_margin_V"] for x in rows), .475)
        self.assertAlmostEqual(min(x["iso_to_stm_high_margin_V"] for x in rows), .63)

    def test_iso_own_source_logic_no_cross_supply_comparison(self):
        # A common design mistake compares TX at VDDremote against local VIH.
        rows = iso_corners()
        self.assertEqual(rows[0]["esp_tx_to_iso_high_margin_V"], rows[12]["esp_tx_to_iso_high_margin_V"])

    def test_iso_budget_and_input_loading(self):
        b = calculate()["iso_budget"]
        self.assertLess(b["dc_low_plus_bleeder_max_A"], b["reserve_each_rail_A"])
        self.assertLess(b["pullup47k_load_max_A"], .002)
        self.assertAlmostEqual(b["rail_total_power_reserve_W"], .0288)

    def test_iso_timing_under_named_capacitive_test_load(self):
        self.assertLess(18.5e-9 / BIT, .003)
        self.assertLess(5.9e-9 / BIT, .001)
        self.assertLess(.3e-6 / BIT, .04)
        self.assertEqual(PARAMETERS["iso"]["cl_test_F"], 15e-12)

    def test_iso_eight_states_independent_of_analog(self):
        states = iso_states()
        self.assertEqual(len(states), 8)
        for state in states:
            self.assertFalse(state["remote_DC_signal_path"])
            if state["stm_usb"] and not state["esp_usb"]:
                self.assertTrue(state["rx_stm"].startswith("DEFAULT_HIGH"))
            if state["esp_usb"] and not state["stm_usb"]:
                self.assertTrue(state["rx_esp"].startswith("DEFAULT_HIGH"))
        for off_a, on_a in zip(states[::2], states[1::2]):
            self.assertEqual(off_a["rx_stm"], on_a["rx_stm"])
            self.assertEqual(off_a["rx_esp"], on_a["rx_esp"])

    def test_iso_transitions_coverage_only(self):
        transitions = calculate()["directed_single_source_transitions"]
        self.assertEqual(len(transitions), 24)
        self.assertTrue(all((j, i) in transitions for i, j in transitions))

    def test_brownout_not_false_logic_guarantee(self):
        for v in (1.700001, 1.8, 2.0, 2.249999):
            self.assertEqual(iso_voltage_state(v), "UNDETERMINED")
        self.assertEqual(iso_voltage_state(1.7), "PD")
        self.assertEqual(iso_voltage_state(2.25), "PU")

    def test_lvc_dc_conditional_corners(self):
        rows = lvc_corners()
        self.assertGreater(min(x["esp_high_margin_V"] for x in rows), .17)
        self.assertLess(max(x["pullup_short_current_A"] for x in rows), .001)
        self.assertIsNone(PARAMETERS["lvc"]["powered_high_output_leak_max_A"])

    def test_lvc_rc_against_bit_period_conditional(self):
        rows = lvc_corners()
        self.assertLess(max(x["rise_10_90_s_CL100pF"] for x in rows), BIT / 8)
        self.assertLess(max(x["t_esp_threshold_s_CL100pF"] for x in rows), BIT / 7)

    def test_lvc_off_leakage_only_at_named_conditions(self):
        off = calculate()["lvc_off_conditional_bounds"]
        self.assertLess(off["Y_V_10uA22k_1pct"], .3)
        self.assertLess(off["rail_V_10uA10k_1pct"], .11)
        self.assertLess(off["A_V_5uA47k_1pct"], .3)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "calculos_interfaces.json").write_text(json.dumps(calculate(), indent=2) + "\n")
    unittest.main(verbosity=2)
