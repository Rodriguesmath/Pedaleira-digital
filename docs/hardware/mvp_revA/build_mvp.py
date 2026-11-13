#!/usr/bin/env python3
"""Gera esquematicas PDF (multi-folha A4 e prancha unica A1), BOM e layouts JSON do MVP Rev. A."""
from collections import defaultdict
import csv
import json
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = Path(__file__).resolve().parent
OUT = ROOT / 'output/MVP_REVA'
OUT.mkdir(parents=True, exist_ok=True)

from layout_mvp import BLACK, MAROON, NAVY, SchematicDrawer  # noqa: E402

model = json.loads((SRC_DIR / 'circuito_mvp_revA.json').read_text())
components = model['components']
byref = {c['ref']: c for c in components}

PAGES = {
    1: 'Fonte bancada 12 V, CW7805 e referências VREF_OP / ADC_BIAS',
    2: 'Entrada P10, buffer U1A, clamps 1N4007, drivers U3 e C35/C36 RF',
    3: 'Codec CS4272, FILT+, VCOM cerâmico e canal B polarizado',
    4: 'Receptor DAC U1B, filtro RC e saída direta P10 (sem K1)',
    5: 'STM32H723, ESP32 DevKit, UART direta 2×1 kΩ e pull-ups',
    6: 'Chaves SW1..SW4 e LEDs indicadores',
    7: 'Desacoplamento local do CS4272 e dos dois TL072',
}

NOTES = {
    1: ['Fonte bancada 12,0 V (I_limit 250-300 mA) via D1 1N4007. Manter J5 aberto até validar +5V_CW = 5,0 V e pinagem de U5.',
        'Ligar 12 V antes da USB do STM32; nunca unir +5V_CW ao +5V/VIN das USBs.'],
    2: ['D6/D7/D13/D14 = 1N4007. Sem Q11..Q14 no MVP: controlar amplitude da entrada. C35/C36 (100 pF) MANTIDOS p/ RF do ADC.',
        'C2 e C16 eletrolíticos 10 µF: terminal + para o lado U3/R18/R20 (~5,5 V) e terminal - para AINA_P/N (~2,4 V).'],
    3: ['C14 em VCOM (pino 15): usar CERÂMICO 1 µF >=25 V (não eletrolítico) devido à impedância ~25 kΩ de VCOM.',
        'C12 (47 µF) eletrolítico com + no pino 22 (FILT+). VD/VL alimentados por +3V3_STM.'],
    4: ['C10 e C11 eletrolíticos 10 µF: terminal + para R1/R7 (lado TL072 ~5,5 V) e terminal - para pinos 25/24 do CS4272 (~2,4 V).',
        'Saída direta C5 (+ em LP2) e R6 = 47 kΩ direto para J3 TIP; sem relé K1 (ligar amplificador por último).'],
    5: ['UART direta 115200 bps via R_UTX/R_URX (1 kΩ): conectar USBs no mesmo PC/hub; GND comum; 3V3/VIN do ESP32 desconectados.',
        'PD10 conectado direto a CODEC_RST com pull-down R13 = 10 kΩ. Confirmar variant WROOM (GPIO16/17 livres).'],
    6: ['Chaves fecham para GND (pull-up interno). Firmware deve fechar SYSCFG PC2_C/PC3_C ou remapear SW3/SW4 antes de uso.',
        'D2..D5 opcionais para o primeiro teste de áudio.'],
    7: ['Soldar C23..C28 a poucos mm dos pinos de alimentação do CS4272; C30/C32 eletrolíticos com + em +RAW.'],
}

FONTS = Path('/home/rodrigues/.local/share/fonts/msttcorefonts')
for name, filename in [('T', 'Times.TTF'), ('TB', 'Timesbd.TTF')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / filename)))
pdfmetrics.registerFont(TTFont('HB', '/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf'))


def draw_frame_a4(drawer, sheet, title, page_w=842, page_h=595):
    """Moldura e carimbo padrao A4 para caderno multi-folha."""
    sx, sy = page_w / 420.0, page_h / 297.0

    def rline(x, y, X, Y, w=0.25):
        drawer.cv.setStrokeColor(BLACK)
        drawer.cv.setLineWidth(w * sx)
        drawer.cv.line(x * sx, page_h - y * sy, X * sx, page_h - Y * sy)

    def rbox(x, y, w, h, lw=0.24):
        drawer.cv.setStrokeColor(BLACK)
        drawer.cv.setLineWidth(lw * sx)
        drawer.cv.rect(x * sx, page_h - (y + h) * sy, w * sx, h * sy, stroke=1, fill=0)

    def rtxt(x, y, val, size=2.8, col=BLACK, font='T', align='left'):
        drawer.cv.setFillColor(col)
        drawer.cv.setFont(font, size * 1.18 * sx)
        fn = {'left': 'drawString', 'right': 'drawRightString', 'center': 'drawCentredString'}[align]
        getattr(drawer.cv, fn)(x * sx, page_h - y * sy, str(val))

    rbox(3, 12, 414, 273)
    rbox(10, 19, 400, 259)
    rbox(230, 250, 180, 28, 0.35)
    for y in (259, 268):
        rline(230, y, 410, y)
    for x in (300, 319, 352, 374):
        rline(x, 259, x, 268)
    for x in (310, 365):
        rline(x, 268, x, 278)
    rtxt(233, 253.4, 'TÍTULO DA FOLHA', 2.5, '#404040')
    rtxt(233, 257.8, title, 3.0, NAVY)
    for x, cap, val in [(233, 'DOCUMENTO', 'PD-MVP-A'), (303, 'REV', 'MVP-A'), (322, 'DATA', '2026-11-12'),
                        (355, 'FOLHA', f'{sheet} / {len(PAGES)}'), (377, 'FORMATO', 'A4 / 91 itens')]:
        rtxt(x, 262.3, cap, 2.5, '#404040')
        rtxt(x, 266.8, val, 2.8, font='TB')
    rtxt(233, 271.8, 'AUTORIA / PROJETO', 2.5, '#404040')
    rtxt(233, 276.2, 'Rodrigues M. Lima')
    rtxt(313, 271.8, 'STATUS', 2.5, '#404040')
    rtxt(313, 276.2, 'MVP Bancada (91 itens)')
    rtxt(368, 271.8, 'ESCALA', 2.5, '#404040')
    rtxt(368, 276.2, 'Sem escala')


def draw_frame_a1(drawer, page_w, page_h, scale):
    """Moldura e carimbo A1 para a prancha unificada."""
    max_x = page_w / scale
    max_y = page_h / scale
    drawer.cv.setStrokeColor(BLACK)
    drawer.cv.setLineWidth(1.2)
    drawer.cv.rect(18, 18, page_w - 36, page_h - 36, stroke=1, fill=0)
    # Carimbo inferior direito
    bx, by, bw, bh = max_x - 860, max_y - 250, 825, 210
    drawer.cv.setStrokeColor(BLACK)
    drawer.cv.setLineWidth(1.0)
    drawer.cv.rect(bx * scale, page_h - (by + bh) * scale, bw * scale, bh * scale, stroke=1, fill=0)
    drawer.txt(bx + 18, by + 35, 'PEDALEIRA DIGITAL — ESQUEMÁTICA UNIFICADA COMPLETA (MVP REV. A)', 13, NAVY, 'HB', raw=True)
    drawer.txt(bx + 18, by + 65, 'Todas as 7 etapas integradas | 91 componentes reais (36 C, 32 R, 23 semicondutores/Eletromec.)', 9.5, BLACK, 'T', raw=True)
    drawer.txt(bx + 18, by + 95, 'Fonte Bancada 12 V (I_limit 250-300 mA) | Apenas 1N4007 | Apenas Ceramicos e Eletroliticos | UART Direta 2x 1k | C35/C36 Mantidos', 9.0, MAROON, 'T', raw=True)
    drawer.txt(bx + 18, by + 135, 'DOCUMENTO: PD-MVP-A-UNI   |   REVISAO: MVP Rev. A   |   FORMATO: A1 (841 x 594 mm)   |   DATA: 2026-11-12', 9.0, BLACK, 'TB', raw=True)
    drawer.txt(bx + 18, by + 168, 'AUTORIA: Rodrigues M. Lima   |   USO: Montagem academica controlada em perfboard (nao energizar sem checar J5)', 8.5, '#404040', 'T', raw=True)


def check_integrity(drawer, mode_name):
    assert drawer.rendered == set(byref), (mode_name, drawer.rendered ^ set(byref))
    assert drawer.terminal_rendered == {(a['ref'], p) for a in components for p in a['pins']}, mode_name
    # Verifica zero cruzamentos entre segmentos de nets diferentes na mesma folha
    by_sheet = defaultdict(list)
    for r in drawer.routes:
        for a, b in zip(r['points'], r['points'][1:]):
            if tuple(a) != tuple(b):
                by_sheet[r['sheet']].append((r['net'], tuple(a), tuple(b)))
    for sh, segs in by_sheet.items():
        for net_v, a, b in segs:
            if a[0] != b[0]:
                continue
            x0, y_min, y_max = a[0], min(a[1], b[1]), max(a[1], b[1])
            for net_h, c, d in segs:
                if c[1] != d[1] or net_v == net_h:
                    continue
                y0, x_min, x_max = c[1], min(c[0], d[0]), max(c[0], d[0])
                assert not (x_min < x0 < x_max and y_min < y0 < y_max), (mode_name, sh, net_v, net_h, (x0, y0))


def write_bom_and_json():
    (OUT / 'circuito_mvp_revA.json').write_text(json.dumps(model, ensure_ascii=False, indent=2) + '\n')
    bom_parts = [c for c in components if c.get('in_bom', True)]
    with (OUT / 'BOM_mvp_revA.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Referência', 'Tipo', 'Valor', 'Qtd', 'Encapsulamento', 'Função', 'Situação', 'Especificações mínimas', 'Observações'])
        for a in bom_parts:
            w.writerow([a['ref'], a['kind'], a['value'], 1, a['package'], a['function'], a['status'], a['min_spec'], a['note']])
    return len(bom_parts)


def build_multipage():
    cv = canvas.Canvas(str(OUT / 'pedaleira_mvp_revA_folhas.pdf'), pagesize=(842, 595), invariant=1)
    cv.setTitle('Pedaleira Digital MVP Rev. A - Folhas A4')
    cv.setAuthor('Rodrigues M. Lima')
    drawer = SchematicDrawer(cv, 595, components, scale=1.0)
    for sh, title in PAGES.items():
        cv.setFillColor('#FFFCF8')
        cv.rect(0, 0, 842, 595, fill=1, stroke=0)
        draw_frame_a4(drawer, sh, title)
        drawer.draw_single_sheet(sh)
        yy = 492
        for line in NOTES[sh]:
            drawer.cv.setFillColor(BLACK)
            drawer.cv.setFont('T', 6.5)
            drawer.cv.drawString(40, 595 - yy, line)
            yy += 9
        cv.showPage()
    cv.save()
    check_integrity(drawer, 'folhas')
    (OUT / 'diagram_layout_folhas.json').write_text(json.dumps({
        'version': 1, 'mode': 'multipage', 'pages': PAGES,
        'instances': drawer.instances, 'routes': drawer.routes,
        'ports': drawer.ports, 'decorations': drawer.decor,
    }, ensure_ascii=False, indent=2))


def build_unified_a1():
    page_w, page_h = 2383.94, 1683.78  # ISO A1 landscape (841 x 594 mm)
    scale = page_w / 3080.0
    cv = canvas.Canvas(str(OUT / 'pedaleira_mvp_revA_unificada.pdf'), pagesize=(page_w, page_h), invariant=1)
    cv.setTitle('Pedaleira Digital MVP Rev. A - Esquemática Unificada Completa')
    cv.setAuthor('Rodrigues M. Lima')
    cv.setFillColor('#FFFCF8')
    cv.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    drawer = SchematicDrawer(cv, page_h, components, scale=scale)
    draw_frame_a1(drawer, page_w, page_h, scale)
    drawer.draw_unified_a1()
    cv.showPage()
    cv.save()
    check_integrity(drawer, 'unificada')
    (OUT / 'diagram_layout_unificada.json').write_text(json.dumps({
        'version': 1, 'mode': 'unified', 'pages': {'1': 'Esquemática Unificada MVP Rev. A (Todas as etapas)'},
        'instances': drawer.instances, 'routes': drawer.routes,
        'ports': drawer.ports, 'decorations': drawer.decor,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    n_bom = write_bom_and_json()
    build_multipage()
    build_unified_a1()
    print(f'Build OK: {n_bom} BOM items, multi-sheet A4 + unified A1 PDFs and layouts generated in {OUT}')
