#!/usr/bin/env python3
"""
simular_A.py - Suíte ngspice de verificação Phase 4.10A
Projeto: Pedaleira Digital - Revisão 4.10A
Autoria: Rodrigues M. Lima

Simula integralmente:
1. Supervisor de alimentação +5VA (U7=TL431 + Q3=2N3906 com histerese).
2. Intertravamento de reset do codec /RST (Q1/Q2/R39/R13/R40/R41).
3. Contenção OFF-state e sem VA nas entradas analógicas (D15/C44/Q4 e shunts Q5..Q8=2N7000).
4. 8 combinações estáticas de alimentação (RAW, J5, USB).
5. Transiente completo sequencial (partida, reset, colapso de VA e RAW).
6. Cantos de operação (nominal 27°C, frio 0°C, quente 70°C, step rápido 10us).
7. Impacto de THD na entrada analógica diferencial AINA_P - AINA_N.
"""

import sys
import os
import json
import re
import math
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "output" / "REV410_ENTREGA" / "SIMULACOES_A"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OP_LIB = ROOT_DIR / "output" / "auditoria_rev49" / "SIMULACOES" / "OP_STARTUP.lib"

if not OP_LIB.is_file():
    raise FileNotFoundError(f"OP_STARTUP.lib não encontrado em {OP_LIB}")

# Detecção do ngspice
NGSPICE_BIN = None
for candidate in [
    "/home/rodrigues/.cache/pedaleira-tools/root/usr/bin/ngspice",
    "/usr/bin/ngspice",
    "/usr/local/bin/ngspice"
]:
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        NGSPICE_BIN = candidate
        break

if not NGSPICE_BIN:
    import shutil
    NGSPICE_BIN = shutil.which("ngspice")

if not NGSPICE_BIN:
    raise RuntimeError("ngspice binário não encontrado no ambiente!")

ENV = os.environ.copy()
LIB_DIR = "/home/rodrigues/.cache/pedaleira-tools/root/usr/lib64"
if os.path.isdir(LIB_DIR):
    ENV["LD_LIBRARY_PATH"] = LIB_DIR + (":" + ENV["LD_LIBRARY_PATH"] if "LD_LIBRARY_PATH" in ENV else "")

def run_simulation(cir_content: str, name: str):
    cir_file = OUTPUT_DIR / f"{name}.cir"
    log_file = OUTPUT_DIR / f"{name}.log"
    cir_file.write_text(cir_content, encoding="utf-8")
    
    cmd = [NGSPICE_BIN, "-b", str(cir_file)]
    res = subprocess.run(cmd, capture_output=True, text=True, env=ENV)
    log_file.write_text(f"--- STDOUT ---\n{res.stdout}\n--- STDERR ---\n{res.stderr}\n", encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Simulação '{name}' falhou (código {res.returncode}). Veja {log_file}")
    return res.stdout

def parse_wrdata(txt_path: Path):
    if not txt_path.is_file():
        raise FileNotFoundError(f"Arquivo wrdata {txt_path} não encontrado")
    with open(txt_path, "r", encoding="utf-8") as f:
        raw_lines = [l.strip().split() for l in f if l.strip()]
    if not raw_lines:
        return []
    return [[float(x) for x in l] for l in raw_lines]

# Modelos SPICE Comuns Padronizados
COMMON_MODELS = f"""* Modelos SPICE Padronizados Rev 4.10A
.include "{OP_LIB}"

.model 2N3904 NPN (Is=14.34f Bf=255.9 Vaf=74.03 Ikf=.2847 Xtb=1.5 Br=6.092 Cjc=7.306p Cje=22.01p Rb=10 Rc=1)
.model 2N3906 PNP (Is=1.41f Bf=180.7 Vaf=18.7 Ikf=80m Xtb=1.5 Br=4.977 Cjc=9.728p Cje=10.68p Rb=20 Rc=2.4)

.subckt 2N7000 D G S
M1 D G S S NMOS_INT
Cgs G S 30p
Cgd G D 10p
Cds D S 25p
D_body S D DBODY
.model DBODY D(Is=1e-14 Rs=0.5)
.model NMOS_INT NMOS (Level=1 Vto=2.1 Kp=0.25 Rd=1.2 Rs=1.2 Lambda=0.01)
.ends

.model D4148 D(Is=2.5n N=1.75 Rs=.6 Cjo=4p Tt=4n)
.model DBAT85 D(Is=200n N=1.05 Rs=2 Cjo=10p)
.model Dprot D(Is=1p N=1 Rs=1 Cjo=5p)
.model DZ1V8 D(Is=1e-14 Bv=1.8 Ibv=1m N=1)

.subckt TL431 K A REF
Rref REF A 10Meg
Cref REF A 2p
Vref vr A 2.488
Gerr A n_err REF vr 20m
Rerr n_err A 10k
Ccomp n_err A 100p
D_hi n_err v_lim D4148
V_lim v_lim A 4.0
D_lo A n_err D4148
R_b n_err q_b 100
Q_out k_sat q_b A 2N3904
Dz k_sat K DZ1V8
C_k K A 20p
.ends
"""

def generate_circuit_core(r33="9.1k", r34="11k", temp=None):
    temp_line = f".temp {temp}\n" if temp is not None else ""
    return f"""{temp_line}{COMMON_MODELS}
* --- Supervisor +5VA ---
R33 v5 ref_tl {r33}
R34 ref_tl 0 {r34}
R38 va_ok ref_tl 470k
XU7 u7_k 0 ref_tl TL431
Q3 va_ok q3_b v5 2N3906
R35 v5 q3_b 2.2k
R36 q3_b u7_k 1.8k
R37 va_ok 0 22k
C_ok va_ok 0 10p

* --- Intertravamento /RST ---
R39 pd10 codec_rst 1.0k
R13 codec_rst 0 10k
C_codec codec_rst 0 20p
Q1 codec_rst rst_clamp_b 0 2N3904
R40 v33 rst_clamp_b 4.7k
Q2 rst_clamp_b q2_b 0 2N3904
R41 va_ok q2_b 22k

* --- Contenção AIN sem VA ---
D15 n2 d15_k D4148
R43 d15_k v_hold 47
C44 v_hold 0 10u
R45 v_hold shunt_en 47k
R46 shunt_en 0 100k
Q4 shunt_en q4_b 0 2N3904
R44 va_ok q4_b 10k

* Shunts Q5..Q8
XQ5 n9 shunt_en 0 2N7000
XQ6 n8 shunt_en 0 2N7000
R47 n4 q7_d 47
XQ7 q7_d shunt_en 0 2N7000
XQ8 n10 shunt_en 0 2N7000

* --- Front-End Analógico e Polarização ---
R22 n2 n56 2.2k
R23 n56 0 2.2k
C38 n56 0 470u
C39 n56 0 100n

R27 v5 n4 13k
R28 n4 0 12k
C40 n4 0 100u
C41 n4 0 100n
R10 n4 n10 100k
C34 n10 0 100n

XU1A n34 n38 n2 0 n38 TL072
XU3A n38 n30 n2 0 n28 TL072
XU3B n56 n29 n2 0 n27 TL072

C1 n39 n37 100n
R26 n37 n34 1k
R3 n34 n56 1Meg
R17 n30 n28 10k
C18 n30 n28 22p
R18 n28 n7 1.5k
C2 n7 n9 10u
R19 n29 n27 10k
C19 n29 n27 22p
R20 n27 n6 1.5k
C16 n6 n8 10u
R24 n38 n29 10k

R15 n9 n4 100k
R16 n8 n4 100k
C20 n9 n8 680p
C35 n9 0 100p
C36 n8 0 100p
RADC n9 n8 37k

* Diodos de proteção e clamping com sensor de corrente
V_sense_d9 n9_k v5 0
V_sense_d11 n8_k v5 0
D9 n9 n9_k DBAT85
D10 0 n9 DBAT85
D11 n8 n8_k DBAT85
D12 0 n8 DBAT85
Dhi0 n9 v5 Dprot
Dlo0 0 n9 Dprot
Dhi1 n8 v5 Dprot
Dlo1 0 n8 Dprot
"""

# =========================================================================
# TESTE 1: Supervisor +5VA (Histerese, I_K, Carga Adicional)
# =========================================================================
def test_supervisor():
    print("[1/7] Testando Supervisor +5VA (Histerese, I_K, Carga Adicional)...")
    data_file = OUTPUT_DIR / "supervisor_hyst.txt"
    cir = f"""* Supervisor +5VA Hysteresis and Load Test
{COMMON_MODELS}

V_VA v5 0 PWL(0 0 10m 5.0 20m 5.0 30m 4.0 40m 5.0)

R33 v5 ref_tl 9.1k
R34 ref_tl 0 11k
R38 va_ok ref_tl 470k
XU7 u7_k 0 ref_tl TL431
Q3 va_ok q3_b v5 2N3906
R35 v5 q3_b 2.2k
R36 q3_b u7_k 1.8k
R37 va_ok 0 22k
C_ok va_ok 0 10p

.options reltol=1e-3 abstol=1e-9 trtol=1
.control
tran 20u 40m
wrdata {data_file} v(v5) v(va_ok) v(ref_tl) v(u7_k) v(q3_b) i(V_VA)
quit
.endc
.end
"""
    run_simulation(cir, "supervisor_hyst")
    data = parse_wrdata(data_file)
    
    t_rise, t_fall, v_rise, v_fall = None, None, None, None
    for row in data:
        t = row[0]
        v_va = row[1]
        v_ok = row[3]
        if t <= 15e-3 and v_ok > 2.5 and v_rise is None:
            v_rise, t_rise = v_va, t
        if 20e-3 < t <= 35e-3 and v_ok < 2.5 and v_fall is None:
            v_fall, t_fall = v_va, t
            
    # Checar carga e I_K em 5.0V (t = 15ms)
    row_5v = next(r for r in data if 14.5e-3 <= r[0] <= 15.5e-3)
    v5_val = row_5v[1]
    v_ok_val = row_5v[3]
    v_k_val = row_5v[7]
    v_q3b_val = row_5v[9]
    i_va_val = abs(row_5v[11]) * 1000.0 # mA
    i_k_ma = (v_q3b_val - v_k_val) / 1800.0 * 1000.0 # mA
    
    pass_rise = 4.50 <= v_rise <= 4.70
    pass_fall = 4.40 <= v_fall <= 4.55
    pass_ik = i_k_ma >= 1.00
    pass_load = i_va_val <= 3.00
    all_ok = pass_rise and pass_fall and pass_ik and pass_load

    res = {
        "rising_trip_v": round(v_rise, 4),
        "falling_trip_v": round(v_fall, 4),
        "hysteresis_mv": round((v_rise - v_fall) * 1000.0, 2),
        "va_ok_active_v": round(v_ok_val, 4),
        "ik_active_ma": round(i_k_ma, 4),
        "additional_load_5va_ma": round(i_va_val, 4),
        "status": "PASS" if all_ok else "FAIL"
    }
    print(f"  Supervisor: V_rise={v_rise:.3f}V, V_fall={v_fall:.3f}V, I_K={i_k_ma:.2f}mA, Carga={i_va_val:.2f}mA -> {res['status']}")
    if not all_ok:
        raise AssertionError(f"Supervisor violou contrato: {res}")
    return res

# =========================================================================
# TESTE 2: Intertravamento /RST (Clamping, Liberação, Backpower)
# =========================================================================
def test_interlock_rst():
    print("[2/7] Testando Intertravamento /RST (Clamping, Liberação, Backpower e Subida)...")
    data_pulse = OUTPUT_DIR / "rst_pulse.txt"
    cir = f"""* Reset Interlock Pulse and Rise Time
{COMMON_MODELS}

V33 v33 0 3.3
Vok va_ok 0 5.0
Vpd10 pd10 0 PWL(0 0 100u 0 100.01u 3.3 200u 3.3)

R39 pd10 codec_rst 1.0k
R13 codec_rst 0 10k
C_codec codec_rst 0 20p
Q1 codec_rst rst_clamp_b 0 2N3904
R40 v33 rst_clamp_b 4.7k
Q2 rst_clamp_b q2_b 0 2N3904
R41 va_ok q2_b 22k

.control
tran 0.2u 200u
wrdata {data_pulse} v(codec_rst) v(rst_clamp_b) v(pd10)
quit
.endc
.end
"""
    run_simulation(cir, "rst_pulse")
    data = parse_wrdata(data_pulse)
    
    row_200ns = next(r for r in data if r[0] >= 100.2e-6)
    v_rst_200ns = row_200ns[1]
    
    row_150us = next(r for r in data if r[0] >= 150e-6)
    v_rst_high = row_150us[1]
    
    data_dc = OUTPUT_DIR / "rst_dc.txt"
    cir_dc = f"""* Reset Interlock DC checks
{COMMON_MODELS}

V33_1 v33_1 0 3.3
Vpd10_1 pd10_1 0 3.3
Vok_1 va_ok_1 0 0.0
R39_1 pd10_1 rst_1 1.0k
R13_1 rst_1 0 10k
Q1_1 rst_1 clamp_b_1 0 2N3904
R40_1 v33_1 clamp_b_1 4.7k
Q2_1 clamp_b_1 q2b_1 0 2N3904
R41_1 va_ok_1 q2b_1 22k

V33_2 v33_2 0 0.0
Vpd10_2 pd10_2 0 0.0
Vok_2 va_ok_2 0 5.25
R39_2 pd10_2 rst_2 1.0k
R13_2 rst_2 0 10k
Q1_2 rst_2 clamp_b_2 0 2N3904
R40_2 v33_2 clamp_b_2 4.7k
Q2_2 clamp_b_2 q2b_2 0 2N3904
R41_2 va_ok_2 q2b_2 22k

.control
op
wrdata {data_dc} v(rst_1) v(rst_2)
quit
.endc
.end
"""
    run_simulation(cir_dc, "rst_dc")
    data_dc_rows = parse_wrdata(data_dc)
    v_rst_clamped = data_dc_rows[0][1]
    v_rst_backpower = data_dc_rows[0][3]

    pass_clamp = v_rst_clamped <= 0.15 and v_rst_clamped <= (0.30 * 3.3)
    pass_high = v_rst_high >= (0.70 * 3.3)
    pass_rise = v_rst_200ns >= (0.70 * 3.3)
    pass_bp = v_rst_backpower <= 0.30
    all_ok = pass_clamp and pass_high and pass_rise and pass_bp

    res = {
        "v_rst_clamped_va_low": round(v_rst_clamped, 4),
        "v_rst_normal_va_high": round(v_rst_high, 4),
        "v_rst_at_200ns_rise": round(v_rst_200ns, 4),
        "v_rst_backpower_3v3_off": round(v_rst_backpower, 6),
        "status": "PASS" if all_ok else "FAIL"
    }
    print(f"  Reset: Clamped={v_rst_clamped:.3f}V, High={v_rst_high:.3f}V, Rise@200ns={v_rst_200ns:.3f}V, BP={v_rst_backpower:.4f}V -> {res['status']}")
    if not all_ok:
        raise AssertionError(f"Intertravamento /RST violou contrato: {res}")
    return res

# =========================================================================
# TESTE 3: 8 Combinações Estáticas (RAW, J5, USB)
# =========================================================================
def test_static_combinations():
    print("[3/7] Testando 8 Combinações Estáticas (RAW on/off, J5 fechada/aberta, USB on/off)...")
    combos = [
        (1, 0.0, False, 0.0, "RAW=OFF, J5=OPEN, USB=OFF"),
        (2, 0.0, False, 3.3, "RAW=OFF, J5=OPEN, USB=ON"),
        (3, 0.0, True,  0.0, "RAW=OFF, J5=CLOSED, USB=OFF"),
        (4, 0.0, True,  3.3, "RAW=OFF, J5=CLOSED, USB=ON"),
        (5, 11.3, False, 0.0, "RAW=ON, J5=OPEN, USB=OFF (Contenção crítica)"),
        (6, 11.3, False, 3.3, "RAW=ON, J5=OPEN, USB=ON (Contenção + Intertravamento)"),
        (7, 11.3, True,  0.0, "RAW=ON, J5=CLOSED, USB=OFF (Backpower check)"),
        (8, 11.3, True,  3.3, "RAW=ON, J5=CLOSED, USB=ON (Operação Nominal)")
    ]

    results = []
    all_ok = True

    for cid, v_raw, j5, v_usb, desc in combos:
        data_file = OUTPUT_DIR / f"static_c{cid}.txt"
        v_5va = 5.0 if (v_raw > 6.0 and j5) else 0.0
        v_pd10 = v_usb

        cir = f"""* Combinação Estática {cid}: {desc}
{generate_circuit_core()}

Vraw n2 0 {v_raw}
V5 v5 0 {v_5va}
V33 v33 0 {v_usb}
Vpd10 pd10 0 {v_pd10}
Vguitar n39 0 SIN(0 0.5 1k)

.options reltol=1e-3 abstol=1e-9 trtol=1
.control
tran 20u 20m 10m
wrdata {data_file} v(n9) v(n8) v(n4) v(n10) v(codec_rst) v(va_ok) v(shunt_en) i(V_sense_d9) i(V_sense_d11) i(V5)
quit
.endc
.end
"""
        run_simulation(cir, f"static_c{cid}")
        data = parse_wrdata(data_file)
        
        p_vals = [r[1] for r in data]
        n_vals = [r[3] for r in data]
        bias_vals = [r[5] for r in data]
        cm_vals = [r[7] for r in data]
        rst_vals = [r[9] for r in data]
        va_ok_vals = [r[11] for r in data]
        shunt_vals = [r[13] for r in data]
        # Backpower current through D9/D11 into +5VA:
        # Current through V_sense_d9 is positive when flowing into v5 (+5VA)
        i_d9_vals = [r[15] * 1e6 for r in data] # uA
        i_d11_vals = [r[17] * 1e6 for r in data] # uA
        i_backpower_diodes = [max(0.0, id9 + id11) for id9, id11 in zip(i_d9_vals, i_d11_vals)]
        max_bp_diodes_ua = max(i_backpower_diodes) if i_backpower_diodes else 0.0
        
        min_p, max_p = min(p_vals), max(p_vals)
        min_n, max_n = min(n_vals), max(n_vals)
        min_bias, max_bias = min(bias_vals), max(bias_vals)
        min_cm, max_cm = min(cm_vals), max(cm_vals)
        max_rst = max(rst_vals)
        max_va_ok = max(va_ok_vals)
        max_shunt = max(shunt_vals)

        passed = True
        errs = []
        if not j5 or v_5va < 4.4:
            # VA ausente:
            if not (-0.25 <= min_p and max_p <= 0.25):
                passed = False; errs.append(f"AINA_P fora [-0.25, 0.25]: [{min_p:.3f}, {max_p:.3f}]")
            if not (-0.25 <= min_n and max_n <= 0.25):
                passed = False; errs.append(f"AINA_N fora [-0.25, 0.25]: [{min_n:.3f}, {max_n:.3f}]")
            if not (-0.25 <= min_bias and max_bias <= 0.25):
                passed = False; errs.append(f"ADC_BIAS fora [-0.25, 0.25]: [{min_bias:.3f}, {max_bias:.3f}]")
            if not (-0.25 <= min_cm and max_cm <= 0.25):
                passed = False; errs.append(f"AINB_CM fora [-0.25, 0.25]: [{min_cm:.3f}, {max_cm:.3f}]")
            if max_bp_diodes_ua > 1.0:
                passed = False; errs.append(f"Corrente reversa por D9/D11 > 1uA: {max_bp_diodes_ua:.4f}uA")
            if v_usb > 2.5:
                if max_rst > 0.15:
                    passed = False; errs.append(f"CODEC_RST não travou em LOW: {max_rst:.3f}V")
        else:
            # VA presente (5.0V):
            if max_va_ok < 4.5:
                passed = False; errs.append(f"VA_OK não subiu: {max_va_ok:.3f}V")
            if v_usb > 2.5 and max_rst < (0.70 * 3.3):
                passed = False; errs.append(f"CODEC_RST não liberou: {max_rst:.3f}V")
            if v_usb < 0.5 and max_rst > 0.30:
                passed = False; errs.append(f"Backpower em CODEC_RST com 3V3 OFF: {max_rst:.3f}V")

        if not passed:
            all_ok = False

        c_info = {
            "id": cid,
            "description": desc,
            "raw_v": v_raw,
            "j5_closed": j5,
            "usb_v": v_usb,
            "aina_p_range": [round(min_p, 4), round(max_p, 4)],
            "aina_n_range": [round(min_n, 4), round(max_n, 4)],
            "adc_bias_range": [round(min_bias, 4), round(max_bias, 4)],
            "ainb_cm_range": [round(min_cm, 4), round(max_cm, 4)],
            "codec_rst_max": round(max_rst, 4),
            "va_ok_max": round(max_va_ok, 4),
            "shunt_en_max": round(max_shunt, 4),
            "max_i_diodes_backpower_ua": round(max_bp_diodes_ua, 6),
            "status": "PASS" if passed else "FAIL",
            "errors": errs
        }
        results.append(c_info)
        print(f"  Combo {cid} ({desc}): Status={c_info['status']} (RST={max_rst:.3f}V, AIN_P=[{min_p*1000:.1f},{max_p*1000:.1f}]mV, I_bp_diodes={max_bp_diodes_ua:.4f}uA)")

    if not all_ok:
        raise AssertionError("Uma ou mais combinações estáticas falharam!")
    return results

# =========================================================================
# TESTE 4: Transiente Sequencial Completo (a)
# =========================================================================
def test_transient_full_sequence():
    print("[4/7] Testando Transiente Sequencial Completo (USB -> 12V -> J5 atrasada -> PD10 -> Colapso VA -> Colapso RAW)...")
    data_file = OUTPUT_DIR / "transient_seq.txt"

    cir = f"""* Transiente Sequencial Completo Rev 4.10A
{generate_circuit_core()}

V33 v33 0 3.3
Vraw n2 0 PWL(0 0 5m 0 6m 11.3 75m 11.3 80m 0 100m 0)
V5 v5 0 PWL(0 0 18m 0 20m 5.0 60m 5.0 61m 0 100m 0)
Vpd10 pd10 0 PWL(0 0 10m 0 10.01m 3.3 30m 3.3 30.01m 0 35m 0 35.01m 3.3 100m 3.3)
Vguitar n39 0 SIN(0 0.5 1k)

.options reltol=1e-3 abstol=1e-9 trtol=1
.control
tran 50u 95m
wrdata {data_file} v(n2) v(v5) v(va_ok) v(codec_rst) v(v_hold) v(shunt_en) v(n9) v(n8) v(n4) v(n10) i(V_sense_d9) i(V_sense_d11)
quit
.endc
.end
"""
    run_simulation(cir, "transient_seq")
    data = parse_wrdata(data_file)

    row_14m = next(r for r in data if 13.9e-3 <= r[0] <= 14.1e-3)
    rst_14m = row_14m[7]
    ain_p_14m = row_14m[13]
    ain_n_14m = row_14m[15]

    row_25m = next(r for r in data if 24.9e-3 <= r[0] <= 25.1e-3)
    rst_25m = row_25m[7]
    va_ok_25m = row_25m[5]

    row_32m = next(r for r in data if 31.9e-3 <= r[0] <= 32.1e-3)
    rst_32m = row_32m[7]

    row_40m = next(r for r in data if 39.9e-3 <= r[0] <= 40.1e-3)
    rst_40m = row_40m[7]

    row_68m = next(r for r in data if 67.9e-3 <= r[0] <= 68.1e-3)
    va_ok_68m = row_68m[5]
    rst_68m = row_68m[7]
    shunt_68m = row_68m[11]
    ain_p_68m = row_68m[13]
    ain_n_68m = row_68m[15]
    i_d9_68m = max(0.0, row_68m[21] * 1e6)
    i_d11_68m = max(0.0, row_68m[23] * 1e6)
    i_bp_68m = i_d9_68m + i_d11_68m

    row_85m = next(r for r in data if 84.9e-3 <= r[0] <= 85.1e-3)
    v_hold_85m = row_85m[9]
    shunt_85m = row_85m[11]
    bias_85m = row_85m[17]

    pass_1 = (rst_14m <= 0.15) and (-0.25 <= ain_p_14m <= 0.25)
    pass_2 = (rst_25m >= 2.31) and (va_ok_25m >= 4.5)
    pass_3 = (rst_32m <= 0.10)
    pass_4 = (rst_40m >= 2.31)
    pass_5 = (va_ok_68m <= 0.10) and (rst_68m <= 0.15) and (shunt_68m >= 5.0) and (-0.25 <= ain_p_68m <= 0.25) and (i_bp_68m < 1.0)
    pass_6 = (shunt_85m >= 4.0) and (-0.25 <= bias_85m <= 0.25)

    all_ok = pass_1 and pass_2 and pass_3 and pass_4 and pass_5 and pass_6

    res = {
        "rst_prematuro_14ms_v": round(rst_14m, 4),
        "rst_liberado_25ms_v": round(rst_25m, 4),
        "rst_pulso_low_32ms_v": round(rst_32m, 4),
        "rst_retorno_40ms_v": round(rst_40m, 4),
        "va_ok_colapso_68ms_v": round(va_ok_68m, 4),
        "rst_pos_colapso_68ms_v": round(rst_68m, 4),
        "shunt_en_pos_colapso_68ms_v": round(shunt_68m, 4),
        "ain_p_pos_colapso_68ms_v": round(ain_p_68m, 4),
        "max_i_diodes_pos_colapso_ua": round(i_bp_68m, 6),
        "v_hold_85ms_v": round(v_hold_85m, 4),
        "shunt_en_85ms_v": round(shunt_85m, 4),
        "adc_bias_85ms_v": round(bias_85m, 4),
        "status": "PASS" if all_ok else "FAIL"
    }
    print(f"  Transiente Sequencial: Status={res['status']} (RST_pre={rst_14m:.3f}V, RST_lib={rst_25m:.3f}V, RST_clamp={rst_68m:.3f}V, Shunt={shunt_68m:.2f}V)")
    if not all_ok:
        raise AssertionError(f"Transiente sequencial violou contrato: {res}")
    return res

# =========================================================================
# TESTE 5: Cantos de Operação (Nominal, Frio/Min, Quente/Max)
# =========================================================================
def test_corners():
    print("[5/7] Testando Cantos de Operação (Nominal, Frio/Min, Quente/Max)...")
    corners = [
        ("nominal", 27, 11.3, 5.0, 3.3, "9.1k", "11k"),
        ("frio_min", 0, 10.5, 4.75, 3.0, "8.918k", "11.22k"),
        ("quente_max", 70, 12.6, 5.25, 3.6, "9.282k", "10.78k")
    ]

    corner_results = {}
    for cname, temp, v_raw, v_va, v_3v3, r33, r34 in corners:
        data_on = OUTPUT_DIR / f"corner_{cname}_on.txt"
        cir_on = f"""* Corner {cname} ON
{generate_circuit_core(r33=r33, r34=r34, temp=temp)}

Vraw n2 0 {v_raw}
V5 v5 0 {v_va}
V33 v33 0 {v_3v3}
Vpd10 pd10 0 {v_3v3}
Vguitar n39 0 SIN(0 0.5 1k)

.options reltol=1e-3 abstol=1e-9 trtol=1
.control
tran 20u 20m 10m
wrdata {data_on} v(va_ok) v(codec_rst) v(shunt_en) i(V5)
quit
.endc
.end
"""
        run_simulation(cir_on, f"corner_{cname}_on")
        d_on = parse_wrdata(data_on)
        va_ok_on = max(r[1] for r in d_on)
        rst_on = max(r[3] for r in d_on)
        shunt_on = max(r[5] for r in d_on)
        i_5va_on = max(abs(r[7]) * 1000.0 for r in d_on) # mA

        data_off = OUTPUT_DIR / f"corner_{cname}_off.txt"
        cir_off = f"""* Corner {cname} OFF (VA=0V)
{generate_circuit_core(r33=r33, r34=r34, temp=temp)}

Vraw n2 0 {v_raw}
V5 v5 0 0.0
V33 v33 0 {v_3v3}
Vpd10 pd10 0 {v_3v3}
Vguitar n39 0 SIN(0 0.5 1k)

.options reltol=1e-3 abstol=1e-9 trtol=1
.control
tran 20u 20m 10m
wrdata {data_off} v(va_ok) v(codec_rst) v(shunt_en) v(n9) v(n8) v(n4) v(n10) i(V_sense_d9) i(V_sense_d11)
quit
.endc
.end
"""
        run_simulation(cir_off, f"corner_{cname}_off")
        d_off = parse_wrdata(data_off)
        rst_off = max(r[3] for r in d_off)
        shunt_off = min(r[5] for r in d_off)
        min_p_off = min(r[7] for r in d_off)
        max_p_off = max(r[7] for r in d_off)
        bp_diodes_ua = [max(0.0, (r[15] + r[17]) * 1e6) for r in d_off]
        max_bp_ua = max(bp_diodes_ua) if bp_diodes_ua else 0.0

        pass_on = (va_ok_on >= (v_va * 0.90)) and (rst_on >= (0.70 * v_3v3)) and (shunt_on <= 0.10) and (i_5va_on <= 3.0)
        pass_off = (rst_off <= 0.15) and (shunt_off >= 5.0) and (-0.25 <= min_p_off and max_p_off <= 0.25) and (max_bp_ua < 1.0)
        
        status = "PASS" if (pass_on and pass_off) else "FAIL"
        c_res = {
            "temp_c": temp,
            "raw_v": v_raw,
            "va_v": v_va,
            "v33_v": v_3v3,
            "on_va_ok_v": round(va_ok_on, 4),
            "on_codec_rst_v": round(rst_on, 4),
            "on_shunt_en_v": round(shunt_on, 4),
            "on_load_5va_ma": round(i_5va_on, 4),
            "off_codec_rst_v": round(rst_off, 4),
            "off_shunt_en_v": round(shunt_off, 4),
            "off_aina_p_range": [round(min_p_off, 4), round(max_p_off, 4)],
            "off_backpower_diodes_ua": round(max_bp_ua, 6),
            "status": status
        }
        corner_results[cname] = c_res
        print(f"  Corner {cname}: Status={status} (ON_RST={rst_on:.3f}V, OFF_RST={rst_off:.3f}V, OFF_P=[{min_p_off*1000:.1f},{max_p_off*1000:.1f}]mV)")
        if status != "PASS":
            raise AssertionError(f"Canto {cname} violou contrato: {c_res}")

    return corner_results

# =========================================================================
# TESTE 6: Step Rápido +RAW 10us (Inrush, Estabilidade, Fixação)
# =========================================================================
def test_fast_step():
    print("[6/7] Testando Step Rápido +RAW 10us (Inrush em C44 e Shunts)...")
    data_file = OUTPUT_DIR / "step_10us.txt"

    cir = f"""* Step Rápido RAW 10us
{generate_circuit_core()}

Vraw n2 0 PWL(0 0 10u 0 20u 12.6 10m 12.6)
V5 v5 0 0.0
V33 v33 0 3.3
Vpd10 pd10 0 3.3
Vguitar n39 0 0

.options reltol=1e-3 abstol=1e-9 trtol=1
.control
tran 1u 5m
wrdata {data_file} v(n2) v(v_hold) v(shunt_en) v(codec_rst) v(n9) v(n4) i(Vraw)
quit
.endc
.end
"""
    run_simulation(cir, "step_10us")
    data = parse_wrdata(data_file)

    # Inrush peak in 0..500us window
    inrush_window = [r for r in data if r[0] <= 500e-6]
    max_iraw_ma = max(abs(r[13]) * 1000.0 for r in inrush_window)

    # Settled values at t >= 4ms (after ~8.5 tau)
    settled_window = [r for r in data if r[0] >= 4.0e-3]
    v_hold_end = settled_window[-1][3]
    shunt_en_end = settled_window[-1][5]
    rst_max = max(r[7] for r in data)
    aina_p_max = max(abs(r[9]) for r in data)

    pass_iraw = max_iraw_ma < 450.0
    pass_shunt = shunt_en_end >= 6.0
    pass_rst = rst_max <= 0.15
    pass_aina = aina_p_max <= 0.25
    all_ok = pass_iraw and pass_shunt and pass_rst and pass_aina

    res = {
        "peak_inrush_c44_ma": round(max_iraw_ma, 2),
        "v_hold_settled_v": round(v_hold_end, 4),
        "shunt_en_settled_v": round(shunt_en_end, 4),
        "max_codec_rst_v": round(rst_max, 4),
        "max_aina_p_v": round(aina_p_max, 4),
        "status": "PASS" if all_ok else "FAIL"
    }
    print(f"  Step 10us: Status={res['status']} (Peak Inrush={max_iraw_ma:.1f}mA, Shunt={shunt_en_end:.2f}V, RST={rst_max:.3f}V)")
    if not all_ok:
        raise AssertionError(f"Step rápido violou contrato: {res}")
    return res

# =========================================================================
# TESTE 7: Verificação de THD e Impacto na Entrada Diferencial
# =========================================================================
def test_thd_impact():
    print("[7/7] Testando THD e Impacto dos Shunts em AINA_P - AINA_N (< 0.02%)...")
    cir = f"""* Verificação de THD Nominal (12V ON, VA=5.0V, Guitarra 0.5Vpk @ 1kHz)
{generate_circuit_core()}

Vraw n2 0 11.3
V5 v5 0 5.0
V33 v33 0 3.3
Vpd10 pd10 0 3.3
Vguitar n39 0 SIN(0 0.5 1k)

.options reltol=1e-4 abstol=1e-10
.control
tran 5u 30m 20m
fourier 1k v(n9,n8)
quit
.endc
.end
"""
    stdout = run_simulation(cir, "thd_nominal")
    match = re.search(r"THD:\s+([\d\.\+eE\-]+)\s*%", stdout)
    if not match:
        raise RuntimeError("Não foi possível extrair THD da saída do ngspice")
    
    thd_pct = float(match.group(1))
    pass_thd = thd_pct < 0.02

    res = {
        "thd_differential_pct": round(thd_pct, 6),
        "thd_limit_pct": 0.02,
        "status": "PASS" if pass_thd else "FAIL"
    }
    print(f"  THD: {thd_pct:.6f}% (Limite < 0.02%) -> {res['status']}")
    if not pass_thd:
        raise AssertionError(f"THD violou limite de 0.02%: {thd_pct}%")
    return res

# =========================================================================
# EXECUÇÃO PRINCIPAL E EMISSÃO DE EVIDÊNCIAS
# =========================================================================
def main():
    print("=" * 70)
    print("SUÍTE DE VERIFICAÇÃO NGSPICE - REVISÃO 4.10A (simular_A.py)")
    print("=" * 70)

    try:
        sup_res = test_supervisor()
        rst_res = test_interlock_rst()
        static_res = test_static_combinations()
        trans_res = test_transient_full_sequence()
        corner_res = test_corners()
        step_res = test_fast_step()
        thd_res = test_thd_impact()

        total_scenarios = 1 + 1 + len(static_res) + 1 + len(corner_res) + 1 + 1

        summary = {
            "meta": {
                "script": "docs/hardware/rev4_10/simular_A.py",
                "revision": "4.10A",
                "author": "Rodrigues M. Lima",
                "ngspice_bin": NGSPICE_BIN,
                "timestamp_utc": "2026-11-12T21:50:00Z"
            },
            "supervisor_va": sup_res,
            "interlock_rst": rst_res,
            "static_combinations": static_res,
            "transient_sequence": trans_res,
            "corners": corner_res,
            "fast_step_10us": step_res,
            "thd_analysis": thd_res,
            "global_verdict": {
                "total_scenarios": total_scenarios,
                "scenarios_passed": total_scenarios,
                "scenarios_failed": 0,
                "verdict": "PASS",
                "gate_phase": "4.10A"
            }
        }

        json_path = OUTPUT_DIR / "resumo_A.json"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print("=" * 70)
        print(f"VERIFICAÇÃO COMPLETA: {total_scenarios}/{total_scenarios} cenários PASSED com sucesso!")
        print(f"Resumo JSON gerado em: {json_path}")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\nERRO CRÍTICO NA SUÍTE: {e}", file=sys.stderr)
        err_summary = {
            "verdict": "FAIL",
            "error": str(e)
        }
        (OUTPUT_DIR / "resumo_A.json").write_text(json.dumps(err_summary, indent=2), encoding="utf-8")
        return 1

if __name__ == "__main__":
    sys.exit(main())
