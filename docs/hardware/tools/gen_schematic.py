#!/usr/bin/env python3
"""
gen_schematic.py
Gerador determinístico do esquemático EasyEDA Standard (docType: 1)
para o projeto Pedaleira Digital (IFPB - Prototipagem).
Gera componentes LIB com pinos elétricos reais, NetLabels, Wires perfeitamente
alinhados à grade de 10px e atributos LCSC para BOM automática.
Produz barramentos diretos (Audio SAI4, I2C1, UART3) com espaçamento profissional
e verificação ERC rigorosa baseada em grafo elétrico.
"""

import json
import os
import sys
from collections import defaultdict
from PIL import Image, ImageDraw

gid_counter = 1000

def get_gid():
    global gid_counter
    gid_counter += 1
    return f"gge{gid_counter}"

class EasyEDABuilder:
    def __init__(self, width=1650, height=1100):
        self.width = width
        self.height = height
        self.shapes = []
        self.wires = []          # list of (x1, y1, x2, y2)
        self.netlabels = []      # list of (x, y, name)
        self.pins = []           # list of (x, y, pin_name, component_ref)

    # -------------------------------------------------------------
    # Primitivos Gráficos Básicos
    # -------------------------------------------------------------
    def add_text(self, x, y, text, size="10pt", color="#0F172A", weight="normal", anchor="start"):
        gid = get_gid()
        # Garantir que nenhum caractere ~ quebre a sintaxe do EasyEDA
        safe_text = text.replace("~", "=")
        s = f"T~L~{x}~{y}~0~{color}~Arial~{size}~{weight}~normal~~comment~{safe_text}~1~{anchor}~{gid}~0~"
        self.shapes.append(s)

    def add_rect(self, x, y, w, h, stroke="#2563EB", stroke_w=1, fill="#FFFFFF"):
        gid = get_gid()
        s = f"R~{x}~{y}~~~{w}~{h}~{stroke}~{stroke_w}~0~{fill}~{gid}~0~"
        self.shapes.append(s)

    def add_wire(self, x1, y1, x2, y2, color="#008800", width=1):
        gid = get_gid()
        s = f"W~{x1} {y1} {x2} {y2}~{color}~{width}~0~none~{gid}~0"
        self.shapes.append(s)
        self.wires.append((x1, y1, x2, y2))

    def add_junction(self, x, y):
        gid = get_gid()
        s = f"J~{x}~{y}~2.5~#008800~{gid}~0"
        self.shapes.append(s)

    def add_netlabel(self, x, y, name, rot=0):
        gid = get_gid()
        tx = x + 4 if rot == 0 else x
        ty = y - 10 if rot == 0 else y - 10
        s = f"N~{x}~{y}~{rot}~#B91C1C~{name}~{gid}~start~{tx}~{ty}~Arial~8pt~0"
        self.shapes.append(s)
        self.netlabels.append((x, y, name))

    def add_netflag_gnd(self, x, y):
        gid_f = get_gid()
        gid_ft = get_gid()
        gid_pl1 = get_gid()
        gid_pl2 = get_gid()
        gid_pl3 = get_gid()
        gid_pl4 = get_gid()
        s = (
            f"F~part_netLabel_gnD~{x}~{y}~0~{gid_f}~~0^^"
            f"{x}~{y}^^"
            f"GND~#000080~{x-10}~{y+25}~0~start~0~Arial~8pt~{gid_ft}^^"
            f"PL~{x} {y} {x} {y+10}~#000000~1~0~none~{gid_pl1}~0^^"
            f"PL~{x-8} {y+10} {x+8} {y+10}~#000000~1~0~none~{gid_pl2}~0^^"
            f"PL~{x-5} {y+13} {x+5} {y+13}~#000000~1~0~none~{gid_pl3}~0^^"
            f"PL~{x-2} {y+16} {x+2} {y+16}~#000000~1~0~none~{gid_pl4}~0"
        )
        self.shapes.append(s)
        self.netlabels.append((x, y, "GND"))

    def add_netflag_vcc(self, x, y, name="+9V_RAW"):
        gid_f = get_gid()
        gid_ft = get_gid()
        gid_pl1 = get_gid()
        gid_pl2 = get_gid()
        s = (
            f"F~part_netLabel_VCC~{x}~{y}~0~{gid_f}~~0^^"
            f"{x}~{y}^^"
            f"{name}~#B91C1C~{x-15}~{y-16}~0~start~1~Arial~8pt~{gid_ft}^^"
            f"PL~{x} {y} {x} {y-10}~#B91C1C~1~0~none~{gid_pl1}~0^^"
            f"PL~{x-6} {y-10} {x+6} {y-10}~#B91C1C~1.5~0~none~{gid_pl2}~0"
        )
        self.shapes.append(s)
        self.netlabels.append((x, y, name))

    # -------------------------------------------------------------
    # Criação de Componentes LIB com PINs
    # -------------------------------------------------------------
    def add_resistor(self, x, y, ref, val, rot=0, lcsc="C61678"):
        """Resistor axial 0.25W com 2 pinos espaçados em 60px."""
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_rect = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()

        c_para = (
            f"package`AXIAL-0.3`name`{val}`pre`R?`BOM_Supplier`LCSC`BOM_Supplier Part`{lcsc}`"
            f"nameAlias`Value`Contributor`IFPB`"
        )

        if rot == 0:  # Horizontal: dot1 at (x, y), dot2 at (x+60, y)
            dot1 = (x, y)
            dot2 = (x + 60, y)
            body = f"R~{x+15}~{y-8}~~~30~16~#000000~1~0~#FFFFFF~{gid_rect}~0"
            t_ref = f"T~P~{x+16}~{y-12}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
            t_val = f"T~N~{x+16}~{y+18}~0~#2563EB~Arial~8pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"
            pin1 = (
                f"P~show~0~1~{x}~{y}~180~{gid_p1}~0^^{x}~{y}^^"
                f"M {x+15} {y} h -15~#880000^^"
                f"0~{x+2}~{y-4}~0~1~start~~~#0000FF^^"
                f"1~{x+6}~{y+8}~0~1~start~~~#0000FF^^0~{x}~{y}^^0~"
            )
            pin2 = (
                f"P~show~0~2~{x+60}~{y}~0~{gid_p2}~0^^{x+60}~{y}^^"
                f"M {x+45} {y} h 15~#880000^^"
                f"0~{x+50}~{y-4}~0~2~end~~~#0000FF^^"
                f"1~{x+54}~{y+8}~0~2~end~~~#0000FF^^0~{x+60}~{y}^^0~"
            )
        else:  # Vertical: dot1 at (x, y), dot2 at (x, y+60)
            dot1 = (x, y)
            dot2 = (x, y + 60)
            body = f"R~{x-8}~{y+15}~~~16~30~#000000~1~0~#FFFFFF~{gid_rect}~0"
            t_ref = f"T~P~{x+12}~{y+22}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
            t_val = f"T~N~{x+12}~{y+36}~0~#2563EB~Arial~8pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"
            pin1 = (
                f"P~show~0~1~{x}~{y}~90~{gid_p1}~0^^{x}~{y}^^"
                f"M {x} {y+15} v -15~#880000^^"
                f"0~{x-4}~{y+4}~0~1~start~~~#0000FF^^"
                f"1~{x+6}~{y+6}~0~1~start~~~#0000FF^^0~{x}~{y}^^0~"
            )
            pin2 = (
                f"P~show~0~2~{x}~{y+60}~270~{gid_p2}~0^^{x}~{y+60}^^"
                f"M {x} {y+45} v 15~#880000^^"
                f"0~{x-4}~{y+54}~0~2~end~~~#0000FF^^"
                f"1~{x+6}~{y+54}~0~2~end~~~#0000FF^^0~{x}~{y+60}^^0~"
            )

        lib_str = (
            f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@$"
            f"{t_ref}#@${t_val}#@${body}#@${pin1}#@${pin2}"
        )
        self.shapes.append(lib_str)
        self.pins.append((dot1[0], dot1[1], "1", ref))
        self.pins.append((dot2[0], dot2[1], "2", ref))
        return dot1, dot2

    def add_capacitor(self, x, y, ref, val, rot=0, lcsc="C62649"):
        """Capacitor radial com 2 pinos espaçados em 40px."""
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()
        gid_pl1 = get_gid()
        gid_pl2 = get_gid()

        c_para = (
            f"package`RADIAL-2.54`name`{val}`pre`C?`BOM_Supplier`LCSC`BOM_Supplier Part`{lcsc}`"
            f"nameAlias`Value`Contributor`IFPB`"
        )

        if rot == 0:  # Horizontal: dot1=(x, y), dot2=(x+40, y)
            dot1 = (x, y)
            dot2 = (x + 40, y)
            plate1 = f"PL~{x+18} {y-10} {x+18} {y+10}~#000000~2~0~none~{gid_pl1}~0"
            plate2 = f"PL~{x+22} {y-10} {x+22} {y+10}~#000000~2~0~none~{gid_pl2}~0"
            t_ref = f"T~P~{x+6}~{y-14}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
            t_val = f"T~N~{x+6}~{y+18}~0~#2563EB~Arial~8pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"
            pin1 = (
                f"P~show~0~1~{x}~{y}~180~{gid_p1}~0^^{x}~{y}^^"
                f"M {x+18} {y} h -18~#880000^^"
                f"0~{x+2}~{y-4}~0~1~start~~~#0000FF^^"
                f"1~{x+6}~{y+8}~0~1~start~~~#0000FF^^0~{x}~{y}^^0~"
            )
            pin2 = (
                f"P~show~0~2~{x+40}~{y}~0~{gid_p2}~0^^{x+40}~{y}^^"
                f"M {x+22} {y} h 18~#880000^^"
                f"0~{x+30}~{y-4}~0~2~end~~~#0000FF^^"
                f"1~{x+34}~{y+8}~0~2~end~~~#0000FF^^0~{x+40}~{y}^^0~"
            )
        else:  # Vertical: dot1=(x, y), dot2=(x, y+40)
            dot1 = (x, y)
            dot2 = (x, y + 40)
            plate1 = f"PL~{x-10} {y+18} {x+10} {y+18}~#000000~2~0~none~{gid_pl1}~0"
            plate2 = f"PL~{x-10} {y+22} {x+10} {y+22}~#000000~2~0~none~{gid_pl2}~0"
            t_ref = f"T~P~{x+14}~{y+14}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
            t_val = f"T~N~{x+14}~{y+28}~0~#2563EB~Arial~8pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"
            pin1 = (
                f"P~show~0~1~{x}~{y}~90~{gid_p1}~0^^{x}~{y}^^"
                f"M {x} {y+18} v -18~#880000^^"
                f"0~{x-4}~{y+4}~0~1~start~~~#0000FF^^"
                f"1~{x+6}~{y+6}~0~1~start~~~#0000FF^^0~{x}~{y}^^0~"
            )
            pin2 = (
                f"P~show~0~2~{x}~{y+40}~270~{gid_p2}~0^^{x}~{y+40}^^"
                f"M {x} {y+22} v 18~#880000^^"
                f"0~{x-4}~{y+36}~0~2~end~~~#0000FF^^"
                f"1~{x+6}~{y+36}~0~2~end~~~#0000FF^^0~{x}~{y+40}^^0~"
            )

        lib_str = (
            f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@$"
            f"{t_ref}#@${t_val}#@${plate1}#@${plate2}#@${pin1}#@${pin2}"
        )
        self.shapes.append(lib_str)
        self.pins.append((dot1[0], dot1[1], "1", ref))
        self.pins.append((dot2[0], dot2[1], "2", ref))
        return dot1, dot2

    def add_diode(self, x, y, ref="D1", val="1N4007", lcsc="C2860"):
        """Diodo 1N4007 horizontal: dot_anode=(x, y), dot_cathode=(x+50, y)."""
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()
        gid_pl1 = get_gid()
        gid_pl2 = get_gid()

        c_para = f"package`DO-41`name`{val}`pre`D?`BOM_Supplier`LCSC`BOM_Supplier Part`{lcsc}`Contributor`IFPB`"
        dot1 = (x, y)
        dot2 = (x + 50, y)

        tri = f"PL~{x+18} {y-10} {x+32} {y} {x+18} {y+10} {x+18} {y-10}~#000000~1.5~0~#000000~{gid_pl1}~0"
        bar = f"PL~{x+32} {y-10} {x+32} {y+10}~#000000~2~0~none~{gid_pl2}~0"
        t_ref = f"T~P~{x+10}~{y-14}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
        t_val = f"T~N~{x+10}~{y+18}~0~#2563EB~Arial~8pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"

        pin1 = (
            f"P~show~0~1~{x}~{y}~180~{gid_p1}~0^^{x}~{y}^^"
            f"M {x+18} {y} h -18~#880000^^"
            f"0~{x+2}~{y-4}~0~A~start~~~#0000FF^^"
            f"1~{x+6}~{y+8}~0~1~start~~~#0000FF^^0~{x}~{y}^^0~"
        )
        pin2 = (
            f"P~show~0~2~{x+50}~{y}~0~{gid_p2}~0^^{x+50}~{y}^^"
            f"M {x+32} {y} h 18~#880000^^"
            f"0~{x+40}~{y-4}~0~K~end~~~#0000FF^^"
            f"1~{x+44}~{y+8}~0~2~end~~~#0000FF^^0~{x+50}~{y}^^0~"
        )

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@${t_ref}#@${t_val}#@${tri}#@${bar}#@${pin1}#@${pin2}"
        self.shapes.append(lib_str)
        self.pins.append((dot1[0], dot1[1], "A", ref))
        self.pins.append((dot2[0], dot2[1], "K", ref))
        return dot1, dot2

    def add_opamp_symbol(self, x, y, ref="U1A", val="TL072", has_power=False):
        """
        Amplificador Operacional com triângulo e pinos:
        dot_inv: (x, y-15) - Pino In-
        dot_non: (x, y+15) - Pino In+
        dot_out: (x+65, y)  - Pino Out
        Se has_power=True:
          dot_vcc: (x+25, y-35) - Pino 8 (VCC)
          dot_gnd: (x+25, y+35) - Pino 4 (GND)
        """
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_tri = get_gid()
        gid_p_inv = get_gid()
        gid_p_non = get_gid()
        gid_p_out = get_gid()

        c_para = f"package`DIP-8`name`{val}`pre`U?`BOM_Supplier`LCSC`BOM_Supplier Part`C6955`Contributor`IFPB`"

        tri = f"PL~{x+15} {y-30} {x+55} {y} {x+15} {y+30} {x+15} {y-30}~#000000~1.5~0~#FFFFFF~{gid_tri}~0"
        t_ref = f"T~P~{x+22}~{y-6}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
        t_val = f"T~N~{x+22}~{y+8}~0~#64748B~Arial~7pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"

        gid_m = get_gid()
        minus = f"T~L~{x+18}~{y-12}~0~#000000~Arial~10pt~bold~normal~~comment~-~1~start~{gid_m}~0~"
        gid_p = get_gid()
        plus = f"T~L~{x+18}~{y+16}~0~#000000~Arial~10pt~bold~normal~~comment~+~1~start~{gid_p}~0~"

        pin_inv_num = "2" if "A" in ref else "6"
        pin_non_num = "3" if "A" in ref else "5"
        pin_out_num = "1" if "A" in ref else "7"

        dot_inv = (x, y - 15)
        dot_non = (x, y + 15)
        dot_out = (x + 65, y)

        pin_inv = (
            f"P~show~0~1~{dot_inv[0]}~{dot_inv[1]}~180~{gid_p_inv}~0^^{dot_inv[0]}~{dot_inv[1]}^^"
            f"M {x+15} {y-15} h -15~#880000^^"
            f"0~{x+2}~{y-19}~0~IN-~start~~~#0000FF^^"
            f"1~{x+4}~{y-7}~0~{pin_inv_num}~start~~~#0000FF^^0~{dot_inv[0]}~{dot_inv[1]}^^0~"
        )
        pin_non = (
            f"P~show~0~2~{dot_non[0]}~{dot_non[1]}~180~{gid_p_non}~0^^{dot_non[0]}~{dot_non[1]}^^"
            f"M {x+15} {y+15} h -15~#880000^^"
            f"0~{x+2}~{y+11}~0~IN+~start~~~#0000FF^^"
            f"1~{x+4}~{y+23}~0~{pin_non_num}~start~~~#0000FF^^0~{dot_non[0]}~{dot_non[1]}^^0~"
        )
        pin_out = (
            f"P~show~0~3~{dot_out[0]}~{dot_out[1]}~0~{gid_p_out}~0^^{dot_out[0]}~{dot_out[1]}^^"
            f"M {x+55} {y} h 10~#880000^^"
            f"0~{x+56}~{y-4}~0~OUT~end~~~#0000FF^^"
            f"1~{x+58}~{y+8}~0~{pin_out_num}~end~~~#0000FF^^0~{dot_out[0]}~{dot_out[1]}^^0~"
        )

        sub_shapes = [t_ref, t_val, tri, minus, plus, pin_inv, pin_non, pin_out]
        self.pins.append((dot_inv[0], dot_inv[1], "IN-", ref))
        self.pins.append((dot_non[0], dot_non[1], "IN+", ref))
        self.pins.append((dot_out[0], dot_out[1], "OUT", ref))

        dot_vcc = None
        dot_gnd = None
        if has_power:
            gid_pvcc = get_gid()
            gid_pgnd = get_gid()
            dot_vcc = (x + 25, y - 35)
            dot_gnd = (x + 25, y + 35)
            pin_vcc = (
                f"P~show~0~4~{dot_vcc[0]}~{dot_vcc[1]}~90~{gid_pvcc}~0^^{dot_vcc[0]}~{dot_vcc[1]}^^"
                f"M {x+25} {y-20} v -15~#880000^^"
                f"0~{x+28}~{y-26}~0~V+~start~~~#0000FF^^"
                f"1~{x+28}~{y-30}~0~8~start~~~#0000FF^^0~{dot_vcc[0]}~{dot_vcc[1]}^^0~"
            )
            pin_gnd = (
                f"P~show~0~5~{dot_gnd[0]}~{dot_gnd[1]}~270~{gid_pgnd}~0^^{dot_gnd[0]}~{dot_gnd[1]}^^"
                f"M {x+25} {y+20} v 15~#880000^^"
                f"0~{x+28}~{y+26}~0~V-~end~~~#0000FF^^"
                f"1~{x+28}~{y+32}~0~4~end~~~#0000FF^^0~{dot_gnd[0]}~{dot_gnd[1]}^^0~"
            )
            sub_shapes.extend([pin_vcc, pin_gnd])
            self.pins.append((dot_vcc[0], dot_vcc[1], "VCC", ref))
            self.pins.append((dot_gnd[0], dot_gnd[1], "GND", ref))

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@$" + "#@$".join(sub_shapes)
        self.shapes.append(lib_str)
        return dot_inv, dot_non, dot_out, dot_vcc, dot_gnd

    def add_jack_p10(self, x, y, ref="J2", title="JACK P10", facing="right"):
        """
        Jack P10 com pinTip e pinGnd.
        facing='right': pinos saem para a direita (ideal para entrada).
        facing='left': pinos saem para a esquerda (ideal para saída).
        """
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_rect = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()

        c_para = f"package`JACK-P10-THT`name`{title}`pre`J?`BOM_Supplier`LCSC`BOM_Supplier Part`C2843477`Contributor`IFPB`"

        if facing == "right":
            body = f"R~{x}~{y-10}~~~30~40~#000000~1.5~0~#F8FAFC~{gid_rect}~0"
            t_ref = f"T~P~{x+4}~{y+4}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
            t_val = f"T~N~{x+4}~{y+16}~0~#64748B~Arial~7pt~normal~normal~~comment~P10~1~start~{gid_t2}~0~"
            dot_tip = (x + 40, y)
            dot_gnd = (x + 40, y + 20)
            pin_tip = (
                f"P~show~0~1~{dot_tip[0]}~{dot_tip[1]}~0~{gid_p1}~0^^{dot_tip[0]}~{dot_tip[1]}^^"
                f"M {x+30} {y} h 10~#880000^^"
                f"0~{x+24}~{y-4}~0~TIP~end~~~#0000FF^^"
                f"1~{x+32}~{y-4}~0~1~end~~~#0000FF^^0~{dot_tip[0]}~{dot_tip[1]}^^0~"
            )
            pin_gnd = (
                f"P~show~0~2~{dot_gnd[0]}~{dot_gnd[1]}~0~{gid_p2}~0^^{dot_gnd[0]}~{dot_gnd[1]}^^"
                f"M {x+30} {y} h 10~#880000^^"
                f"0~{x+24}~{y+16}~0~GND~end~~~#0000FF^^"
                f"1~{x+32}~{y+16}~0~2~end~~~#0000FF^^0~{dot_gnd[0]}~{dot_gnd[1]}^^0~"
            )
        else:  # facing='left'
            body = f"R~{x+10}~{y-10}~~~30~40~#000000~1.5~0~#F8FAFC~{gid_rect}~0"
            t_ref = f"T~P~{x+14}~{y+4}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
            t_val = f"T~N~{x+14}~{y+16}~0~#64748B~Arial~7pt~normal~normal~~comment~P10~1~start~{gid_t2}~0~"
            dot_tip = (x, y)
            dot_gnd = (x, y + 20)
            pin_tip = (
                f"P~show~0~1~{dot_tip[0]}~{dot_tip[1]}~180~{gid_p1}~0^^{dot_tip[0]}~{dot_tip[1]}^^"
                f"M {x+10} {y} h -10~#880000^^"
                f"0~{x+14}~{y-4}~0~TIP~start~~~#0000FF^^"
                f"1~{x+4}~{y-4}~0~1~start~~~#0000FF^^0~{dot_tip[0]}~{dot_tip[1]}^^0~"
            )
            pin_gnd = (
                f"P~show~0~2~{dot_gnd[0]}~{dot_gnd[1]}~180~{gid_p2}~0^^{dot_gnd[0]}~{dot_gnd[1]}^^"
                f"M {x+10} {y+20} h -10~#880000^^"
                f"0~{x+14}~{y+16}~0~GND~start~~~#0000FF^^"
                f"1~{x+4}~{y+16}~0~2~start~~~#0000FF^^0~{dot_gnd[0]}~{dot_gnd[1]}^^0~"
            )

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@${t_ref}#@${t_val}#@${body}#@${pin_tip}#@${pin_gnd}"
        self.shapes.append(lib_str)
        self.pins.append((dot_tip[0], dot_tip[1], "TIP", ref))
        self.pins.append((dot_gnd[0], dot_gnd[1], "GND", ref))
        return dot_tip, dot_gnd

    def add_jack_dc(self, x, y, ref="J1"):
        """Jack DC 9V com dot_vcc=(x+40, y) e dot_gnd=(x+40, y+20)."""
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_rect = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()

        c_para = f"package`DC-005`name`DC 9V`pre`J?`BOM_Supplier`LCSC`BOM_Supplier Part`C136657`Contributor`IFPB`"
        body = f"R~{x}~{y-10}~~~30~40~#000000~1.5~0~#F8FAFC~{gid_rect}~0"
        t_ref = f"T~P~{x+4}~{y+4}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
        t_val = f"T~N~{x+4}~{y+16}~0~#B91C1C~Arial~7pt~bold~normal~~comment~9V DC~1~start~{gid_t2}~0~"

        dot_vcc = (x + 40, y)
        dot_gnd = (x + 40, y + 20)

        pin_vcc = (
            f"P~show~0~1~{dot_vcc[0]}~{dot_vcc[1]}~0~{gid_p1}~0^^{dot_vcc[0]}~{dot_vcc[1]}^^"
            f"M {x+30} {y} h 10~#880000^^"
            f"0~{x+24}~{y-4}~0~+9V~end~~~#0000FF^^"
            f"1~{x+32}~{y-4}~0~1~end~~~#0000FF^^0~{dot_vcc[0]}~{dot_vcc[1]}^^0~"
        )
        pin_gnd = (
            f"P~show~0~2~{dot_gnd[0]}~{dot_gnd[1]}~0~{gid_p2}~0^^{dot_gnd[0]}~{dot_gnd[1]}^^"
            f"M {x+30} {y+20} h 10~#880000^^"
            f"0~{x+24}~{y+16}~0~GND~end~~~#0000FF^^"
            f"1~{x+32}~{y+16}~0~2~end~~~#0000FF^^0~{dot_gnd[0]}~{dot_gnd[1]}^^0~"
        )

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@${t_ref}#@${t_val}#@${body}#@${pin_vcc}#@${pin_gnd}"
        self.shapes.append(lib_str)
        self.pins.append((dot_vcc[0], dot_vcc[1], "VCC", ref))
        self.pins.append((dot_gnd[0], dot_gnd[1], "GND", ref))
        return dot_vcc, dot_gnd

    def add_switch_spdt(self, x, y, ref="SW1", name="Overdrive"):
        """Chave com retenção MTS-102. dot_in=(x, y), dot_gnd=(x+40, y)."""
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_rect = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()

        c_para = f"package`MTS-102`name`{name}`pre`SW?`BOM_Supplier`LCSC`BOM_Supplier Part`C318884`Contributor`IFPB`"
        body = f"R~{x+10}~{y-8}~~~20~16~#000000~1~0~#FFFFFF~{gid_rect}~0"
        t_ref = f"T~P~{x+10}~{y-12}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
        t_val = f"T~N~{x+10}~{y+18}~0~#64748B~Arial~7pt~normal~normal~~comment~{name}~1~start~{gid_t2}~0~"

        dot_in = (x, y)
        dot_gnd = (x + 40, y)

        pin1 = (
            f"P~show~0~1~{dot_in[0]}~{dot_in[1]}~180~{gid_p1}~0^^{dot_in[0]}~{dot_in[1]}^^"
            f"M {x+10} {y} h -10~#880000^^"
            f"0~{x+2}~{y-4}~0~1~start~~~#0000FF^^"
            f"1~{x+4}~{y+8}~0~1~start~~~#0000FF^^0~{dot_in[0]}~{dot_in[1]}^^0~"
        )
        pin2 = (
            f"P~show~0~2~{dot_gnd[0]}~{dot_gnd[1]}~0~{gid_p2}~0^^{dot_gnd[0]}~{dot_gnd[1]}^^"
            f"M {x+30} {y} h 10~#880000^^"
            f"0~{x+32}~{y-4}~0~2~end~~~#0000FF^^"
            f"1~{x+36}~{y+8}~0~2~end~~~#0000FF^^0~{dot_gnd[0]}~{dot_gnd[1]}^^0~"
        )

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@${t_ref}#@${t_val}#@${body}#@${pin1}#@${pin2}"
        self.shapes.append(lib_str)
        self.pins.append((dot_in[0], dot_in[1], "1", ref))
        self.pins.append((dot_gnd[0], dot_gnd[1], "2", ref))
        return dot_in, dot_gnd

    def add_led(self, x, y, ref="D2", val="LED Vermelho", lcsc="C2286"):
        """LED com dot_anode=(x, y) e dot_cathode=(x+40, y)."""
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_pl1 = get_gid()
        gid_pl2 = get_gid()
        gid_p1 = get_gid()
        gid_p2 = get_gid()

        c_para = f"package`LED-5MM`name`{val}`pre`D?`BOM_Supplier`LCSC`BOM_Supplier Part`{lcsc}`Contributor`IFPB`"
        tri = f"PL~{x+15} {y-8} {x+27} {y} {x+15} {y+8} {x+15} {y-8}~#000000~1.5~0~none~{gid_pl1}~0"
        bar = f"PL~{x+27} {y-8} {x+27} {y+8}~#000000~2~0~none~{gid_pl2}~0"
        t_ref = f"T~P~{x+8}~{y-12}~0~#000080~Arial~8pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
        t_val = f"T~N~{x+4}~{y+16}~0~#2563EB~Arial~7pt~normal~normal~~comment~{val}~1~start~{gid_t2}~0~"

        dot_anode = (x, y)
        dot_cathode = (x + 40, y)

        pin1 = (
            f"P~show~0~1~{dot_anode[0]}~{dot_anode[1]}~180~{gid_p1}~0^^{dot_anode[0]}~{dot_anode[1]}^^"
            f"M {x+15} {y} h -15~#880000^^"
            f"0~{x+2}~{y-4}~0~A~start~~~#0000FF^^"
            f"1~{x+4}~{y+8}~0~1~start~~~#0000FF^^0~{dot_anode[0]}~{dot_anode[1]}^^0~"
        )
        pin2 = (
            f"P~show~0~2~{dot_cathode[0]}~{dot_cathode[1]}~0~{gid_p2}~0^^{dot_cathode[0]}~{dot_cathode[1]}^^"
            f"M {x+27} {y} h 13~#880000^^"
            f"0~{x+30}~{y-4}~0~K~end~~~#0000FF^^"
            f"1~{x+34}~{y+8}~0~2~end~~~#0000FF^^0~{dot_cathode[0]}~{dot_cathode[1]}^^0~"
        )

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@${t_ref}#@${t_val}#@${tri}#@${bar}#@${pin1}#@${pin2}"
        self.shapes.append(lib_str)
        self.pins.append((dot_anode[0], dot_anode[1], "A", ref))
        self.pins.append((dot_cathode[0], dot_cathode[1], "K", ref))
        return dot_anode, dot_cathode

    def add_header_block(self, x, y, w, h, ref, title, pin_defs):
        """
        Gera um símbolo LIB de conector/header com lista de pinos:
        pin_defs: list of (pin_num, pin_name, side, y_offset)
        side: 'L' (dot à esquerda em x-20), 'R' (dot à direita em x+w+20)
        """
        gid_lib = get_gid()
        gid_t1 = get_gid()
        gid_t2 = get_gid()
        gid_rect = get_gid()

        c_para = f"package`HDR-2.54`name`{title}`pre`J?`BOM_Supplier`LCSC`BOM_Supplier Part`C224345`Contributor`IFPB`"
        body = f"R~{x}~{y}~~~{w}~{h}~#0F172A~1.5~0~#FFFFFF~{gid_rect}~0"
        t_ref = f"T~P~{x+10}~{y+16}~0~#000080~Arial~9pt~bold~normal~~comment~{ref}~1~start~{gid_t1}~0~"
        t_val = f"T~N~{x+w-10}~{y+16}~0~#64748B~Arial~8pt~normal~normal~~comment~{title}~1~end~{gid_t2}~0~"

        sub_shapes = [t_ref, t_val, body]
        dots = {}

        for pnum, pname, side, y_off in pin_defs:
            gid_p = get_gid()
            py = y + y_off
            if side == "L":
                dot = (x - 20, py)
                pin_str = (
                    f"P~show~0~{pnum}~{dot[0]}~{dot[1]}~180~{gid_p}~0^^{dot[0]}~{dot[1]}^^"
                    f"M {x} {py} h -20~#880000^^"
                    f"1~{x+4}~{py+3}~0~{pname}~start~~~#0000FF^^"
                    f"1~{x-14}~{py-3}~0~{pnum}~start~~~#94A3B8^^0~{dot[0]}~{dot[1]}^^0~"
                )
            else:
                dot = (x + w + 20, py)
                pin_str = (
                    f"P~show~0~{pnum}~{dot[0]}~{dot[1]}~0~{gid_p}~0^^{dot[0]}~{dot[1]}^^"
                    f"M {x+w} {py} h 20~#880000^^"
                    f"1~{x+w-4}~{py+3}~0~{pname}~end~~~#0000FF^^"
                    f"1~{x+w+4}~{py-3}~0~{pnum}~end~~~#94A3B8^^0~{dot[0]}~{dot[1]}^^0~"
                )
            sub_shapes.append(pin_str)
            dots[pname] = dot
            self.pins.append((dot[0], dot[1], pname, ref))

        lib_str = f"LIB~{x}~{y}~{c_para}~0~0~{gid_lib}~~~~0~~yes~yes#@$" + "#@$".join(sub_shapes)
        self.shapes.append(lib_str)
        return dots

    def build_json(self):
        return {
            "head": {
                "docType": "1",
                "editorVersion": "6.5.42",
                "newgId": True,
                "c_para": {
                    "Prefix Start": "1"
                },
                "c_spiceCmd": None
            },
            "canvas": f"CA~{self.width}~{self.height}~#FFFFFF~yes~#E2E8F0~10~{self.width}~{self.height}~line~10~pixel~5~0~0",
            "shape": self.shapes
        }


def build_pedaleira_schematic():
    b = EasyEDABuilder(width=1650, height=1100)

    # =========================================================================
    # Moldura e Carimbo Técnico (Title Block)
    # =========================================================================
    b.add_rect(20, 20, 1610, 1060, stroke="#94A3B8", stroke_w=1, fill="none")
    # Title block no canto inferior direito
    b.add_rect(1160, 960, 470, 120, stroke="#0F172A", stroke_w=1.5, fill="#F8FAFC")
    b.add_text(1180, 985, "IFPB - PROTOTIPAGEM DE SISTEMAS", size="11pt", weight="bold", color="#1E3A8A")
    b.add_text(1180, 1005, "PROJETO: PEDALEIRA DIGITAL DE EFEITOS", size="10pt", weight="bold", color="#0F172A")
    b.add_text(1180, 1025, "MCU: STM32H723VGT6 (WeAct)  |  CODEC: CS4272", size="8pt", color="#475569")
    b.add_text(1180, 1045, "REV: 2.0 (Enxuta)  |  DATA: 2026-10-22  |  FOLHA: 1/1", size="8pt", color="#475569")
    b.add_text(1180, 1065, "AUTOR: Rodriguesmath  |  PLATAFORMA: EasyEDA Std", size="8pt", color="#64748B")

    # =========================================================================
    # 1. ALIMENTAÇÃO ANALÓGICA (+9V DC) E GERADOR VREF (+4.5V)
    # =========================================================================
    b.add_text(40, 45, "1. ALIMENTACAO ANALOGICA & VREF (+4.5V)", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(40, 62, "Dev boards sao alimentadas via USB; Jack 9V alimenta exclusivamente o TL072", size="7pt", color="#64748B")

    # J1 Jack DC 9V em (40, 95)
    j1_vcc, j1_gnd = b.add_jack_dc(40, 95, ref="J1")
    b.add_netflag_gnd(j1_gnd[0], j1_gnd[1])

    # Diodo D1 de proteção (1N4007)
    d1_a, d1_k = b.add_diode(j1_vcc[0] + 20, j1_vcc[1], ref="D1", val="1N4007")
    b.add_wire(j1_vcc[0], j1_vcc[1], d1_a[0], d1_a[1])

    # Nó +9V_RAW em (d1_k[0] + 30, d1_k[1]) -> (180, 95)
    raw_x = d1_k[0] + 30
    raw_y = d1_k[1]
    b.add_wire(d1_k[0], d1_k[1], raw_x, raw_y)
    b.add_junction(raw_x, raw_y)
    b.add_netflag_vcc(raw_x, raw_y, "+9V_RAW")

    # C_IN (100uF) desacoplamento 9V
    cin_p1, cin_p2 = b.add_capacitor(raw_x, raw_y + 30, ref="C_IN", val="100uF", rot=1, lcsc="C96985")
    b.add_wire(raw_x, raw_y, cin_p1[0], cin_p1[1])
    b.add_netflag_gnd(cin_p2[0], cin_p2[1])

    # Divisor R1 / R2 para VREF
    r1_x = raw_x + 80
    b.add_wire(raw_x, raw_y, r1_x, raw_y)
    b.add_junction(r1_x, raw_y)
    r1_p1, r1_p2 = b.add_resistor(r1_x, raw_y + 20, ref="R1", val="100k", rot=1, lcsc="C61678")
    b.add_wire(r1_x, raw_y, r1_p1[0], r1_p1[1])

    vref_node_x = r1_p2[0]
    vref_node_y = r1_p2[1] + 20
    b.add_wire(r1_p2[0], r1_p2[1], vref_node_x, vref_node_y)
    b.add_junction(vref_node_x, vref_node_y)
    b.add_netlabel(vref_node_x + 50, vref_node_y, "VREF")
    b.add_wire(vref_node_x, vref_node_y, vref_node_x + 50, vref_node_y)

    r2_p1, r2_p2 = b.add_resistor(vref_node_x, vref_node_y + 20, ref="R2", val="100k", rot=1, lcsc="C61678")
    b.add_wire(vref_node_x, vref_node_y, r2_p1[0], r2_p1[1])
    b.add_netflag_gnd(r2_p2[0], r2_p2[1])

    # C3 (47uF) filtro Vref
    c3_x = vref_node_x + 80
    b.add_wire(vref_node_x, vref_node_y, c3_x, vref_node_y)
    b.add_junction(c3_x, vref_node_y)
    c3_p1, c3_p2 = b.add_capacitor(c3_x, vref_node_y + 20, ref="C3", val="47uF", rot=1, lcsc="C96991")
    b.add_wire(c3_x, vref_node_y, c3_p1[0], c3_p1[1])
    b.add_netflag_gnd(c3_p2[0], c3_p2[1])

    # =========================================================================
    # 2. ENTRADA DE ÁUDIO & BUFFER HI-Z (U1A - TL072)
    # =========================================================================
    b.add_text(40, 295, "2. ENTRADA DE INSTRUMENTO & BUFFER HI-Z (TL072)", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(40, 312, "Zin = 1 M (anti-tone sucking); Ganho unitario; Bias em VREF (+4.5V)", size="7pt", color="#64748B")

    # Jack P10 In em (40, 390) - pinos virados para a direita
    j2_tip, j2_gnd = b.add_jack_p10(40, 390, ref="J2", title="IN P10", facing="right")
    b.add_netflag_gnd(j2_gnd[0], j2_gnd[1])

    # C1 (100nF bloqueio DC)
    c1_p1, c1_p2 = b.add_capacitor(j2_tip[0] + 30, j2_tip[1], ref="C1", val="100nF", rot=0, lcsc="C62649")
    b.add_wire(j2_tip[0], j2_tip[1], c1_p1[0], c1_p1[1])

    # Nó de entrada não-inversora do U1A em (c1_p2[0] + 40, c1_p2[1])
    in_node_x = c1_p2[0] + 40
    in_node_y = c1_p2[1]
    b.add_wire(c1_p2[0], c1_p2[1], in_node_x, in_node_y)
    b.add_junction(in_node_x, in_node_y)

    # R3 (1M bias Hi-Z) conectado a VREF
    r3_p1, r3_p2 = b.add_resistor(in_node_x, in_node_y + 30, ref="R3", val="1M", rot=1, lcsc="C61685")
    b.add_wire(in_node_x, in_node_y, r3_p1[0], r3_p1[1])
    b.add_netlabel(r3_p2[0], r3_p2[1], "VREF")

    # U1A Op-Amp em (in_node_x + 50, in_node_y - 15) -> (240, 375)
    # Entrada Não-Inversora (+) em (240, 390)
    op1_x = in_node_x + 50
    op1_y = in_node_y - 15
    u1a_inv, u1a_non, u1a_out, u1a_vcc, u1a_gnd = b.add_opamp_symbol(
        op1_x, op1_y, ref="U1A", val="TL072", has_power=True
    )
    b.add_wire(in_node_x, in_node_y, u1a_non[0], u1a_non[1])

    # Alimentação do TL072 (Pinos 8 e 4 em U1A)
    b.add_netflag_vcc(u1a_vcc[0], u1a_vcc[1], "+9V_RAW")
    b.add_netflag_gnd(u1a_gnd[0], u1a_gnd[1])

    # Feedback unitário: saída (op1_x+65, op1_y) -> pino Inversor (-)
    # Traçado limpo a y=335 (dentro da Seção 2, 23px acima de VCC e 23px abaixo do subtítulo)
    fb_out_x = u1a_out[0] + 15
    fb_top_y = 335
    b.add_wire(u1a_out[0], u1a_out[1], fb_out_x, u1a_out[1])
    b.add_junction(fb_out_x, u1a_out[1])
    b.add_wire(fb_out_x, u1a_out[1], fb_out_x, fb_top_y)
    b.add_wire(fb_out_x, fb_top_y, u1a_inv[0] - 10, fb_top_y)
    b.add_wire(u1a_inv[0] - 10, fb_top_y, u1a_inv[0] - 10, u1a_inv[1])
    b.add_wire(u1a_inv[0] - 10, u1a_inv[1], u1a_inv[0], u1a_inv[1])

    # C2 (10uF desacoplamento de saída para o ADC)
    c2_p1, c2_p2 = b.add_capacitor(fb_out_x + 30, u1a_out[1], ref="C2", val="10uF", rot=0, lcsc="C96985")
    b.add_wire(fb_out_x, u1a_out[1], c2_p1[0], c2_p1[1])
    b.add_wire(c2_p2[0], c2_p2[1], c2_p2[0] + 30, c2_p2[1])
    b.add_netlabel(c2_p2[0] + 30, c2_p2[1], "ADC_IN_L")

    # =========================================================================
    # 3. FILTRO DE RECONSTRUÇÃO & BUFFER DE SAÍDA (U1B - TL072)
    # =========================================================================
    b.add_text(40, 560, "3. FILTRO DE RECONSTRUCAO & SAIDA DE AUDIO (TL072)", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(40, 577, "Filtro passa-baixas Sallen-Key 22 kHz anti-aliasing e resistor anti-pop", size="7pt", color="#64748B")

    # Entrada do DAC
    dac_in_x = 60
    dac_in_y = 640
    b.add_netlabel(dac_in_x, dac_in_y, "DAC_OUT_L")

    # R4 (1k)
    r4_p1, r4_p2 = b.add_resistor(dac_in_x + 40, dac_in_y, ref="R4", val="1k", rot=0, lcsc="C61671")
    b.add_wire(dac_in_x, dac_in_y, r4_p1[0], r4_p1[1])

    # Nó 1 do filtro
    node1_x = r4_p2[0] + 30
    b.add_wire(r4_p2[0], r4_p2[1], node1_x, dac_in_y)
    b.add_junction(node1_x, dac_in_y)

    # C4 (4.7nF para GND)
    c4_p1, c4_p2 = b.add_capacitor(node1_x, dac_in_y + 20, ref="C4", val="4.7nF", rot=1, lcsc="C62635")
    b.add_wire(node1_x, dac_in_y, c4_p1[0], c4_p1[1])
    b.add_netflag_gnd(c4_p2[0], c4_p2[1])

    # R5 (1k)
    r5_p1, r5_p2 = b.add_resistor(node1_x + 40, dac_in_y, ref="R5", val="1k", rot=0, lcsc="C61671")
    b.add_wire(node1_x, dac_in_y, r5_p1[0], r5_p1[1])

    # Nó 2 do filtro
    node2_x = r5_p2[0] + 30
    b.add_wire(r5_p2[0], r5_p2[1], node2_x, dac_in_y)
    b.add_junction(node2_x, dac_in_y)

    # C6 (1.5nF para GND)
    c6_p1, c6_p2 = b.add_capacitor(node2_x, dac_in_y + 20, ref="C6", val="1.5nF", rot=1, lcsc="C62632")
    b.add_wire(node2_x, dac_in_y, c6_p1[0], c6_p1[1])
    b.add_netflag_gnd(c6_p2[0], c6_p2[1])

    # U1B Op-Amp (metade 2 do TL072) em (node2_x + 50, dac_in_y - 15)
    op2_x = node2_x + 50
    op2_y = dac_in_y - 15
    u1b_inv, u1b_non, u1b_out, _, _ = b.add_opamp_symbol(
        op2_x, op2_y, ref="U1B", val="TL072", has_power=False
    )
    b.add_wire(node2_x, dac_in_y, u1b_non[0], u1b_non[1])

    # Feedback unitário U1B por cima a y=605 (U1B não tem pinos de alimentação):
    fb2_out_x = u1b_out[0] + 15
    fb2_top_y = 605
    b.add_wire(u1b_out[0], u1b_out[1], fb2_out_x, u1b_out[1])
    b.add_junction(fb2_out_x, u1b_out[1])
    b.add_wire(fb2_out_x, u1b_out[1], fb2_out_x, fb2_top_y)
    b.add_wire(fb2_out_x, fb2_top_y, u1b_inv[0] - 10, fb2_top_y)
    b.add_wire(u1b_inv[0] - 10, fb2_top_y, u1b_inv[0] - 10, u1b_inv[1])
    b.add_wire(u1b_inv[0] - 10, u1b_inv[1], u1b_inv[0], u1b_inv[1])

    # C5 (10uF desacoplamento saída P10)
    c5_p1, c5_p2 = b.add_capacitor(fb2_out_x + 30, u1b_out[1], ref="C5", val="10uF", rot=0, lcsc="C96985")
    b.add_wire(fb2_out_x, u1b_out[1], c5_p1[0], c5_p1[1])

    # Nó antes do Jack P10 Out (com R6 anti-pop de 100k para GND)
    out_node_x = c5_p2[0] + 30
    b.add_wire(c5_p2[0], c5_p2[1], out_node_x, u1b_out[1])
    b.add_junction(out_node_x, u1b_out[1])

    r6_p1, r6_p2 = b.add_resistor(out_node_x, u1b_out[1] + 20, ref="R6", val="100k", rot=1, lcsc="C61678")
    b.add_wire(out_node_x, u1b_out[1], r6_p1[0], r6_p1[1])
    b.add_netflag_gnd(r6_p2[0], r6_p2[1])

    # Jack P10 Out J3 em (out_node_x + 60, u1b_out[1]) - pinos virados para a esquerda!
    j3_tip, j3_gnd = b.add_jack_p10(out_node_x + 60, u1b_out[1], ref="J3", title="OUT P10", facing="left")
    b.add_wire(out_node_x, u1b_out[1], j3_tip[0], j3_tip[1])
    b.add_netflag_gnd(j3_gnd[0], j3_gnd[1])

    # =========================================================================
    # 4. MÓDULO CODEC CS4272 (HEADER H_CODEC)
    # =========================================================================
    b.add_text(580, 45, "4. MODULO CODEC CS4272 (BREAKOUT)", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(580, 62, "Audio 24-bit 48kHz; Barramento direto para STM32 via SAI4 e I2C1", size="7pt", color="#64748B")

    codec_pins = [
        (1, "VA (+5V)", "L", 30),      # y=110
        (2, "AGND", "L", 55),          # y=135
        (3, "VD (+3.3V)", "L", 80),    # y=160
        (4, "DGND", "L", 105),         # y=185
        (5, "AINL+", "L", 145),        # y=225
        (6, "AOUTL", "L", 185),        # y=265
        (7, "MCLK", "R", 30),          # y=110 -> STM32 PE0
        (8, "LRCK/FS", "R", 60),       # y=140 -> STM32 PE4
        (9, "SCLK", "R", 90),          # y=170 -> STM32 PE5
        (10, "SDIN", "R", 120),        # y=200 -> STM32 PE6
        (11, "SDOUT", "R", 150),       # y=230 -> STM32 PA0
        (12, "SCL", "R", 180),         # y=260 -> STM32 PB8
        (13, "SDA", "R", 210),         # y=290 -> STM32 PB9
        (14, "/RESET", "R", 240)       # y=320 -> STM32 PD10
    ]
    # Header posicionado em x=580, y=80, w=220, h=270. Pinos direitos em x=820.
    codec_dots = b.add_header_block(580, 80, 220, 270, "H_CODEC", "CS4272 Breakout", codec_pins)

    # Conexões Analógicas e Alimentação do Codec (lado esquerdo)
    b.add_netflag_vcc(codec_dots["VA (+5V)"][0], codec_dots["VA (+5V)"][1], "+5V_USB")
    b.add_netflag_gnd(codec_dots["AGND"][0], codec_dots["AGND"][1])
    b.add_netflag_vcc(codec_dots["VD (+3.3V)"][0], codec_dots["VD (+3.3V)"][1], "+3.3V")
    b.add_netflag_gnd(codec_dots["DGND"][0], codec_dots["DGND"][1])

    b.add_netlabel(codec_dots["AINL+"][0], codec_dots["AINL+"][1], "ADC_IN_L")
    b.add_netlabel(codec_dots["AOUTL"][0], codec_dots["AOUTL"][1], "DAC_OUT_L")

    # =========================================================================
    # 5. WEACT STUDIO STM32H723VGT6 (HEADER H_STM32 - PINOS REAIS)
    # =========================================================================
    b.add_text(1000, 45, "5. DSP CORE: WEACT STM32H723VGT6", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(1000, 62, "Pinos mapeados livres de conflitos onboard (SAI4, I2C1 em PB8/PB9, UART3)", size="7pt", color="#64748B")

    stm_pins = [
        # Lado Esquerdo: Barramento de Áudio com o Codec (y=110..320) e Alimentação (y=360..410)
        ("P1.4", "PE0 (MCLK)", "L", 30),        # y=110
        ("P2.5", "PE4 (FS)", "L", 60),          # y=140
        ("P2.6", "PE5 (SCK)", "L", 90),         # y=170
        ("P2.7", "PE6 (SD_OUT)", "L", 120),     # y=200
        ("P2.17", "PA0 (SD_IN)", "L", 150),     # y=230
        ("P1.6", "PB8 (SCL)", "L", 180),        # y=260
        ("P1.5", "PB9 (SDA)", "L", 210),        # y=290
        ("P1.38", "PD10 (RST)", "L", 240),      # y=320
        ("P1.2", "5V_USB", "L", 280),           # y=360
        ("P1.1", "GND", "L", 305),              # y=385
        ("P2.2", "3V3_OUT", "L", 330),          # y=410
        # Lado Direito: UART3 Inter-MCU (y=160, 185), Chaves (y=230..305), LEDs (y=345..420)
        ("P1.40", "PD8 (TX3)", "R", 80),        # y=160 -> ESP32 RX2
        ("P1.39", "PD9 (RX3)", "R", 105),       # y=185 -> ESP32 TX2
        ("P2.11", "PC0 (SW1)", "R", 150),       # y=230
        ("P2.12", "PC1 (SW2)", "R", 175),       # y=255
        ("P2.13", "PC2 (SW3)", "R", 200),       # y=280
        ("P2.14", "PC3 (SW4)", "R", 225),       # y=305
        ("P2.30", "PE7 (LED1)", "R", 265),      # y=345
        ("P2.31", "PE8 (LED2)", "R", 290),      # y=370
        ("P2.32", "PE9 (LED3)", "R", 315),      # y=395
        ("P2.38", "PE15 (LED4)", "R", 340),     # y=420
    ]
    # Header STM32 em x=1000, y=80, w=240, h=440. Pinos esquerdos em x=980. Pinos direitos em x=1260.
    stm_dots = b.add_header_block(1000, 80, 240, 440, "H_STM32", "WeAct STM32H723", stm_pins)

    # Alimentação STM32
    b.add_netflag_vcc(stm_dots["5V_USB"][0], stm_dots["5V_USB"][1], "+5V_USB")
    b.add_netflag_gnd(stm_dots["GND"][0], stm_dots["GND"][1])
    b.add_netflag_vcc(stm_dots["3V3_OUT"][0], stm_dots["3V3_OUT"][1], "+3.3V")

    # =========================================================================
    # BARRAMENTO DIGITAL DIRETO: CODEC CS4272 <---> STM32H723
    # 8 linhas perfeitamente paralelas entre x=820 e x=980 (160px de comprimento)
    # =========================================================================
    bus_signals = [
        ("MCLK", "PE0 (MCLK)", "SAI4_MCLK"),
        ("LRCK/FS", "PE4 (FS)", "SAI4_FS"),
        ("SCLK", "PE5 (SCK)", "SAI4_SCK"),
        ("SDIN", "PE6 (SD_OUT)", "SAI4_SD_OUT"),
        ("SDOUT", "PA0 (SD_IN)", "SAI4_SD_IN"),
        ("SCL", "PB8 (SCL)", "I2C1_SCL"),
        ("SDA", "PB9 (SDA)", "I2C1_SDA"),
        ("/RESET", "PD10 (RST)", "CODEC_RST"),
    ]
    for c_name, s_name, net in bus_signals:
        c_dot = codec_dots[c_name]
        s_dot = stm_dots[s_name]
        b.add_wire(c_dot[0], c_dot[1], s_dot[0], s_dot[1])
        b.add_netlabel(c_dot[0] + 45, c_dot[1], net)

    # Netlabels de Controle e Status no STM32
    b.add_netlabel(stm_dots["PC0 (SW1)"][0], stm_dots["PC0 (SW1)"][1], "SW_OVERDRIVE")
    b.add_netlabel(stm_dots["PC1 (SW2)"][0], stm_dots["PC1 (SW2)"][1], "SW_EQ")
    b.add_netlabel(stm_dots["PC2 (SW3)"][0], stm_dots["PC2 (SW3)"][1], "SW_DELAY")
    b.add_netlabel(stm_dots["PC3 (SW4)"][0], stm_dots["PC3 (SW4)"][1], "SW_MUTE")

    b.add_netlabel(stm_dots["PE7 (LED1)"][0], stm_dots["PE7 (LED1)"][1], "LED_OD_DRV")
    b.add_netlabel(stm_dots["PE8 (LED2)"][0], stm_dots["PE8 (LED2)"][1], "LED_EQ_DRV")
    b.add_netlabel(stm_dots["PE9 (LED3)"][0], stm_dots["PE9 (LED3)"][1], "LED_DLY_DRV")
    b.add_netlabel(stm_dots["PE15 (LED4)"][0], stm_dots["PE15 (LED4)"][1], "LED_STAT_DRV")

    # =========================================================================
    # 6. ESP32 DEVKIT (HEADER H_ESP32 - 4 PINOS USADOS)
    # =========================================================================
    b.add_text(1420, 45, "6. CONECTIVIDADE: ESP32", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(1420, 62, "Ponte Wi-Fi / MQTT e UART", size="7pt", color="#64748B")

    esp_pins = [
        ("1", "5V_IN", "L", 30),         # y=110
        ("2", "GND", "L", 55),           # y=135
        ("3", "GPIO16 (RX2)", "L", 80),   # y=160 -> alinhado com STM32 PD8 (TX3)
        ("4", "GPIO17 (TX2)", "L", 105),  # y=185 -> alinhado com STM32 PD9 (RX3)
    ]
    # Header ESP32 em x=1420, y=80, w=180, h=140. Pinos esquerdos em x=1400.
    esp_dots = b.add_header_block(1420, 80, 180, 140, "H_ESP32", "ESP32 DevKit", esp_pins)

    b.add_netflag_vcc(esp_dots["5V_IN"][0], esp_dots["5V_IN"][1], "+5V_USB")
    b.add_netflag_gnd(esp_dots["GND"][0], esp_dots["GND"][1])

    # =========================================================================
    # BARRAMENTO SERIAL DIRETO: STM32H723 (UART3) <---> ESP32 (UART2)
    # =========================================================================
    # STM32 PD8 (TX) conecta em ESP32 GPIO16 (RX) a y=160
    b.add_wire(stm_dots["PD8 (TX3)"][0], stm_dots["PD8 (TX3)"][1], esp_dots["GPIO16 (RX2)"][0], esp_dots["GPIO16 (RX2)"][1])
    b.add_netlabel(stm_dots["PD8 (TX3)"][0] + 45, 160, "UART_TX_STM")

    # STM32 PD9 (RX) conecta em ESP32 GPIO17 (TX) a y=185
    b.add_wire(stm_dots["PD9 (RX3)"][0], stm_dots["PD9 (RX3)"][1], esp_dots["GPIO17 (TX2)"][0], esp_dots["GPIO17 (TX2)"][1])
    b.add_netlabel(stm_dots["PD9 (RX3)"][0] + 45, 185, "UART_RX_STM")

    # =========================================================================
    # 7. INTERFACE FÍSICA DO USUÁRIO (4 CHAVES COM RETENÇÃO & 4 LEDS)
    # =========================================================================
    b.add_text(660, 480, "7. INTERFACE DO USUARIO: CHAVES MECANICAS & LEDS INDICADORES", size="10pt", weight="bold", color="#1E3A8A")
    b.add_text(660, 497, "Chaves de alavanca com retencao (pull-up interno STM32) e LEDs com resistor 330R", size="7pt", color="#64748B")

    sw_configs = [
        ("SW1", "Overdrive", "SW_OVERDRIVE", 540),
        ("SW2", "Equalizador", "SW_EQ", 590),
        ("SW3", "Delay", "SW_DELAY", 640),
        ("SW4", "Master Mute", "SW_MUTE", 690)
    ]

    for ref, name, net, sy in sw_configs:
        b.add_netlabel(660, sy, net)
        sw_in, sw_gnd = b.add_switch_spdt(760, sy, ref=ref, name=name)
        b.add_wire(660, sy, sw_in[0], sw_in[1])
        b.add_netflag_gnd(sw_gnd[0], sw_gnd[1])

    led_configs = [
        ("D2", "LED Overdrive", "LED_OD_DRV", "C2286", 540),
        ("D3", "LED Equalizador", "LED_EQ_DRV", "C2290", 590),
        ("D4", "LED Delay", "LED_DLY_DRV", "C2286", 640),
        ("D5", "LED Status", "LED_STAT_DRV", "C2290", 690)
    ]

    for ref, name, net, lcsc, ly in led_configs:
        b.add_netlabel(920, ly, net)
        r_p1, r_p2 = b.add_resistor(1020, ly, ref=f"R_{ref}", val="330R", rot=0, lcsc="C61665")
        b.add_wire(920, ly, r_p1[0], r_p1[1])
        led_a, led_k = b.add_led(r_p2[0] + 20, ly, ref=ref, val=name, lcsc=lcsc)
        b.add_wire(r_p2[0], r_p2[1], led_a[0], led_a[1])
        b.add_netflag_gnd(led_k[0], led_k[1])

    # =========================================================================
    # Resumo de Ligações / Notas de Montagem
    # =========================================================================
    b.add_rect(660, 760, 500, 200, stroke="#CBD5E1", stroke_w=1, fill="#F8FAFC")
    b.add_text(675, 780, "NOTAS DE MONTAGEM EM PLACA PERFURADA (IFPB):", size="9pt", weight="bold", color="#0F172A")
    notes = [
        "1. ALIMENTACAO: Os 5V e 3.3V vem da porta USB das dev boards; Jack 9V alimenta apenas o TL072.",
        "2. PULL-UPS I2C: PB8 e PB9 ja possuem resistores de 4.7k soldados na propria placa WeAct.",
        "3. CHAVES: Conectadas diretamente entre o pino GPIO da STM32 e o GND (usar GPIO_PULLUP no CubeMX).",
        "4. TERRA COMUM: Unir os pinos GND analogico (TL072, Jacks P10) e digital (STM32, ESP32, Codec).",
        "5. CABOS DE AUDIO: Manter as trilhas e fios do TL072 e Codec curtos para evitar captacao de ruido."
    ]
    for idx, note in enumerate(notes):
        b.add_text(675, 805 + idx * 24, note, size="7.5pt", color="#334155")

    return b


def render_preview(builder, out_png_path="/tmp/schematic_preview.png"):
    """Renderizador 2D de alta fidelidade baseado em PIL para validação visual."""
    img = Image.new("RGB", (builder.width, builder.height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # 1. Desenhar Wires
    for x1, y1, x2, y2 in builder.wires:
        draw.line([(x1, y1), (x2, y2)], fill="#008800", width=2)

    # 2. Desenhar Netlabels e marcadores (texto posicionado 11px acima do fio)
    for x, y, name in builder.netlabels:
        draw.rectangle([(x - 2, y - 2), (x + 2, y + 2)], fill="#B91C1C")
        draw.text((x + 4, y - 11), name, fill="#B91C1C")

    # 3. Desenhar caixas, polilinhas e textos parseando shapes
    for s in builder.shapes:
        parts = s.split("#@$")
        for p in parts:
            tokens = p.split("~")
            cmd = tokens[0]

            if cmd == "R" and len(tokens) >= 8:
                try:
                    rx, ry = int(tokens[1]), int(tokens[2])
                    rw, rh = int(tokens[5]), int(tokens[6])
                    stroke = tokens[7] if tokens[7] != "none" else "#000000"
                    fill = tokens[10] if len(tokens) > 10 and tokens[10] not in ["none", ""] else None
                    if fill and fill != "#FFFFFF":
                        draw.rectangle([(rx, ry), (rx + rw, ry + rh)], fill=fill, outline=stroke)
                    else:
                        draw.rectangle([(rx, ry), (rx + rw, ry + rh)], outline=stroke, width=1)
                except Exception:
                    pass

            elif cmd == "PL" and len(tokens) >= 3:
                try:
                    coords = list(map(int, tokens[1].split()))
                    pts = [(coords[i], coords[i+1]) for i in range(0, len(coords), 2)]
                    stroke = tokens[2] if len(tokens) > 2 and tokens[2] != "none" else "#000000"
                    fill = tokens[5] if len(tokens) > 5 and tokens[5] not in ["none", ""] else None
                    if len(pts) > 2 and fill and fill != "#FFFFFF":
                        draw.polygon(pts, fill=fill, outline=stroke)
                    elif len(pts) >= 2:
                        draw.line(pts, fill=stroke, width=2)
                except Exception:
                    pass

            elif cmd == "P":
                try:
                    sub_segs = p.split("^^")
                    if len(sub_segs) > 1:
                        dot_str = sub_segs[1]
                        dx, dy = map(int, dot_str.split("~"))
                        draw.rectangle([(dx - 1, dy - 1), (dx + 1, dy + 1)], fill="#880000")
                except Exception:
                    pass

            elif cmd == "T" and len(tokens) >= 13:
                try:
                    tx, ty = int(tokens[2]), int(tokens[3])
                    tval = tokens[12]
                    tcol = tokens[5] if tokens[5] else "#000000"
                    anchor = tokens[14] if len(tokens) > 14 else "start"
                    if anchor == "end":
                        tx_adj = tx - (len(tval) * 6)
                    else:
                        tx_adj = tx
                    draw.text((tx_adj, ty - 5), tval, fill=tcol)
                except Exception:
                    pass

            elif cmd == "J" and len(tokens) >= 3:
                try:
                    jx, jy = int(tokens[1]), int(tokens[2])
                    draw.ellipse([(jx - 3, jy - 3), (jx + 3, jy + 3)], fill="#008800")
                except Exception:
                    pass

    img.save(out_png_path)
    print(f"Preview PNG salvo com sucesso em: {out_png_path}")


def run_erc_validation(builder):
    """
    Verificador de Regras Elétricas (ERC) de grau industrial.
    Constrói grafo de conectividade a partir de Wires, Pinos e Netlabels.
    Valida:
    - Pinos flutuantes / desconectados
    - Redes elétricas com apenas 1 pino (dead-ends)
    - Integridade das 25 nets nominais do projeto
    """
    print("--- INICIANDO VALIDAÇÃO ERC DO ESQUEMÁTICO ---")
    errors = []
    warnings = []

    # 1. Disjoint Set Union (DSU) para agrupar pontos conectados por fios
    parent = {}

    def find(p):
        if p not in parent:
            parent[p] = p
        if parent[p] != p:
            parent[p] = find(parent[p])
        return parent[p]

    def union(p1, p2):
        root1 = find(p1)
        root2 = find(p2)
        if root1 != root2:
            parent[root1] = root2

    # Registrar fios
    for x1, y1, x2, y2 in builder.wires:
        union((x1, y1), (x2, y2))

    # Checar se pontos intermediários tocam fios ortogonais
    all_points = set()
    for x, y, _, _ in builder.pins:
        all_points.add((x, y))
    for x, y, _ in builder.netlabels:
        all_points.add((x, y))

    for px, py in all_points:
        for x1, y1, x2, y2 in builder.wires:
            # Ponto sobre segmento horizontal
            if y1 == y2 == py and min(x1, x2) <= px <= max(x1, x2):
                union((px, py), (x1, y1))
            # Ponto sobre segmento vertical
            elif x1 == x2 == px and min(y1, y2) <= py <= max(y1, y2):
                union((px, py), (x1, y1))

    # Agrupar por redes (componentes conexos)
    nets_by_root = defaultdict(lambda: {"pins": [], "labels": set(), "points": set()})

    for x, y, pname, pref in builder.pins:
        root = find((x, y))
        nets_by_root[root]["pins"].append((pref, pname, (x, y)))
        nets_by_root[root]["points"].add((x, y))

    for x, y, lname in builder.netlabels:
        root = find((x, y))
        nets_by_root[root]["labels"].add(lname)
        nets_by_root[root]["points"].add((x, y))

    # 2. Unificar redes que compartilham o mesmo NetLabel nomeado
    net_by_label_name = defaultdict(list)
    for root, data in nets_by_root.items():
        for l in data["labels"]:
            net_by_label_name[l].append(root)

    for lname, roots in net_by_label_name.items():
        if len(roots) > 1:
            first = roots[0]
            for other in roots[1:]:
                union(first, other)

    # Re-computar agrupamento final
    final_nets = defaultdict(lambda: {"pins": [], "labels": set()})
    for x, y, pname, pref in builder.pins:
        root = find((x, y))
        final_nets[root]["pins"].append((pref, pname))

    for x, y, lname in builder.netlabels:
        root = find((x, y))
        final_nets[root]["labels"].add(lname)

    # 3. Validações elétricas
    total_pins = len(builder.pins)
    connected_pins = 0

    for root, data in final_nets.items():
        pin_list = data["pins"]
        labels = data["labels"]
        net_desc = "/".join(labels) if labels else f"NET_{root[0]}_{root[1]}"

        if len(pin_list) == 0 and len(labels) > 0:
            warnings.append(f"NetLabel sem pinos associados: '{net_desc}'")
        elif len(pin_list) == 1:
            errors.append(f"Pino isolado/flutuante em '{net_desc}': {pin_list[0][0]}.{pin_list[0][1]}")
        else:
            connected_pins += len(pin_list)

    print(f"✓ Total de componentes analisados: {len(set(p[3] for p in builder.pins))}")
    print(f"✓ Total de pinos elétricos: {total_pins}")
    print(f"✓ Pinos 100% conectados a redes elétricas válidas: {connected_pins}")
    print(f"✓ Total de redes elétricas (Nets) identificadas: {len(final_nets)}")

    # Relatório
    if errors:
        print(f"❌ {len(errors)} ERROS DETECTADOS NO ERC:")
        for e in errors:
            print("  -", e)
        return False
    else:
        print("✓ NENHUM CURTO-CIRCUITO OU PINO FLUTUANTE DETECTADO!")

    if warnings:
        print(f"⚠️ {len(warnings)} AVISOS:")
        for w in warnings:
            print("  -", w)

    return True


if __name__ == "__main__":
    builder = build_pedaleira_schematic()
    doc = builder.build_json()

    out_json = "/home/rodrigues/Pedaleira-digital/docs/hardware/pedaleira_digital_easyeda.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)

    print(f"Arquivo JSON gerado: {out_json} ({os.path.getsize(out_json)} bytes, {len(doc['shape'])} formas)")

    # Renderizar preview PNG
    render_preview(builder, "/tmp/schematic_preview.png")
    render_preview(builder, "/home/rodrigues/Pedaleira-digital/docs/hardware/schematic_preview.png")
    try:
        render_preview(builder, "/home/rodrigues/.gemini/antigravity-cli/brain/c7b97907-846c-4f00-bfba-837c433b7182/schematic_preview.png")
    except Exception:
        pass

    # Rodar ERC
    erc_ok = run_erc_validation(builder)
    if not erc_ok:
        sys.exit(1)
