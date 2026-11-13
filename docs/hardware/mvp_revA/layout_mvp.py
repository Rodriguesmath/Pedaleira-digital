"""Motor de desenho unificado para o MVP Rev. A.

Usa o mesmo modelo fisico (circuito_mvp_revA.json) para renderizar:
1. Modo multi-folha (7 pranchas A4 separadas para zoom de bancada);
2. Modo prancha unica unificada A1 (todas as 7 etapas juntas + guia de montagem).
"""
from collections import defaultdict
import re

BLUE = '#0000FF'
NAVY = '#000080'
MAROON = '#800000'
BLACK = '#000000'

UNIFIED_SLOTS = {
    1: (25, 25),
    2: (1085, 25),
    3: (2145, 25),
    4: (25, 650),
    5: (1085, 650),
    6: (2145, 650),
    7: (25, 1275),
}


class SchematicDrawer:
    """Mantem estado de desenho e gravacao de instancias/rotas para PDF e KiCad."""

    def __init__(self, cv, page_h, components, scale=1.0):
        self.cv = cv
        self.page_h = page_h
        self.scale = scale
        self.components = components
        self.byref = {c['ref']: c for c in components}
        self.pinpos = {}
        self.instances = []
        self.routes = []
        self.ports = []
        self.decor = []
        self.rendered = set()
        self.terminal_rendered = set()
        self.active = None
        self.current_sheet = 0
        self.in_draw = False
        self.ox = 0
        self.oy = 0
        self.unified = False
        self.target_sheet = 1

    def _px(self, x):
        return x * self.scale

    def _py(self, y):
        return self.page_h - y * self.scale

    def _ox(self, x):
        return x + self.ox

    def _oy(self, y):
        return y + self.oy

    def _rec_sheet(self):
        return 1 if self.unified else self.current_sheet

    def ln(self, x, y, X, Y, color=NAVY, w=0.6, raw=False):
        if not raw:
            x, y, X, Y = self._ox(x), self._oy(y), self._ox(X), self._oy(Y)
        self.cv.setStrokeColor(color)
        self.cv.setLineWidth(w * self.scale)
        self.cv.line(self._px(x), self._py(y), self._px(X), self._py(Y))
        seg = {'kind': 'line', 'points': [[x, y], [X, Y]], 'width': w}
        if self.active is not None:
            self.active['art'].append(seg)
        elif self.in_draw:
            self.decor.append({'sheet': self._rec_sheet(), **seg})

    def txt(self, x, y, s, size=7, color=BLACK, font='T', align='left', raw=False):
        if not raw:
            x, y = self._ox(x), self._oy(y)
        text = str(s).replace('uF', 'µF').replace('kohm', 'kΩ').replace('Mohm', 'MΩ').replace('ohm', 'Ω')
        self.cv.setFillColor(color)
        self.cv.setFont(font, size * self.scale)
        fn = {'left': 'drawString', 'right': 'drawRightString', 'center': 'drawCentredString'}[align]
        getattr(self.cv, fn)(self._px(x), self._py(y), text)
        item = {'kind': 'text', 'at': [x, y], 'text': str(s), 'size': size, 'align': align}
        if self.active is not None:
            self.active['art'].append(item)
        elif self.in_draw:
            self.decor.append({'sheet': self._rec_sheet(), **item})

    def poly(self, pts, color=BLUE, w=0.65):
        for a, b in zip(pts, pts[1:]):
            self.ln(*a, *b, color=color, w=w)

    def circle(self, x, y, r=0.95):
        ax, ay = self._ox(x), self._oy(y)
        self.cv.setStrokeColor(BLUE)
        self.cv.setFillColor('#FFFFFF')
        self.cv.setLineWidth(0.6 * self.scale)
        self.cv.circle(self._px(ax), self._py(ay), r * self.scale, stroke=1, fill=1)
        item = {'kind': 'circle', 'at': [ax, ay], 'radius': r}
        if self.active is not None:
            self.active['art'].append(item)

    def start(self, ref, unit=1):
        assert self.active is None
        self.active = {'ref': ref, 'unit': unit, 'sheet': self._rec_sheet(), 'pins': {}, 'art': []}
        self.rendered.add(ref)

    def finish(self):
        self.instances.append(self.active)
        self.active = None

    def pin(self, ref, p, x, y):
        p = str(p)
        ax, ay = self._ox(x), self._oy(y)
        key = (ref, p)
        assert key not in self.pinpos, key
        assert ax % 5 == 0 and ay % 5 == 0, (key, ax, ay)
        self.pinpos[key] = (ax, ay)
        self.terminal_rendered.add(key)
        self.active['pins'][p] = [ax, ay]

    def ppos(self, ref, p):
        return self.pinpos[(ref, str(p))]

    def pnet(self, ref, p):
        return self.byref[ref]['pins'][str(p)]

    def _raw_ln(self, x, y, X, Y, color=NAVY, w=0.6):
        self.cv.setStrokeColor(color)
        self.cv.setLineWidth(w * self.scale)
        self.cv.line(self._px(x), self._py(y), self._px(X), self._py(Y))

    def route(self, net, pts, raw=False):
        assert net is not None
        apts = [tuple(p) if raw else (self._ox(p[0]), self._oy(p[1])) for p in pts]
        for a, b in zip(apts, apts[1:]):
            assert a[0] == b[0] or a[1] == b[1], apts
            self._raw_ln(*a, *b)
        self.routes.append({'sheet': self._rec_sheet(), 'net': net, 'points': [list(v) for v in apts]})

    def link(self, a, b, *bends):
        assert self.pnet(*a) == self.pnet(*b), (a, b, self.pnet(*a), self.pnet(*b))
        apts = [self.ppos(*a), *[(self._ox(bx), self._oy(by)) for bx, by in bends], self.ppos(*b)]
        self.route(self.pnet(*a), apts, raw=True)

    def frompin(self, ref, p, *pts):
        apts = [self.ppos(ref, p), *[(self._ox(bx), self._oy(by)) for bx, by in pts]]
        self.route(self.pnet(ref, p), apts, raw=True)

    def dotat_raw(self, ax, ay):
        self.cv.setFillColor(NAVY)
        self.cv.circle(self._px(ax), self._py(ay), 1.35 * self.scale, stroke=0, fill=1)
        self.decor.append({'sheet': self._rec_sheet(), 'kind': 'junction', 'at': [ax, ay]})

    def dotpin(self, ref, p):
        self.dotat_raw(*self.ppos(ref, p))

    def gndat_raw(self, ax, ay):
        self.ln(ax, ay, ax, ay + 4, MAROON, raw=True)
        for d, w in [(4, 4), (6, 2.8), (8, 1.4)]:
            self.ln(ax - w, ay + d, ax + w, ay + d, MAROON, raw=True)
        self.txt(ax, ay + 18, 'GND', 6.5, MAROON, align='center', raw=True)
        self.ports.append({'sheet': self._rec_sheet(), 'net': 'GND', 'at': [ax, ay], 'kind': 'ground'})

    def ground(self, ref, p, at=None):
        assert self.pnet(ref, p) == 'GND', (ref, p)
        ax, ay = self.ppos(ref, p)
        if at:
            bx, by = self._ox(at[0]), self._oy(at[1])
            self.route('GND', [(ax, ay), (bx, by)], raw=True)
            ax, ay = bx, by
        self.gndat_raw(ax, ay)

    def net_pages(self, net):
        pages = set()
        for a in self.components:
            for p, n in a['pins'].items():
                if n != net:
                    continue
                sh = a['sheet']
                if a['ref'] == 'U1':
                    sh = 7 if p in ('4', '8') else 2 if p in ('1', '2', '3') else 4
                if a['ref'] == 'U3' and p in ('4', '8'):
                    sh = 7
                pages.add(sh)
        return pages

    def netport(self, ref, p, at=None, side='left', display=None, power=False, power_down=False):
        net = self.pnet(ref, p)
        ax, ay = self.ppos(ref, p)
        if at:
            bx, by = self._ox(at[0]), self._oy(at[1])
            self.route(net, [(ax, ay), (bx, by)], raw=True)
            ax, ay = bx, by
        label = re.sub(r' \(F[1-9]\)', '', display or net)
        if not power and not self.unified:
            others = sorted(self.net_pages(net) - {self.current_sheet})
            if others:
                label += '  [F' + ', F'.join(map(str, others)) + ']'
        if power:
            d = 1 if power_down else -1
            self.ln(ax, ay, ax, ay + 5 * d, MAROON, raw=True)
            self.ln(ax - 4, ay + 5 * d, ax + 4, ay + 5 * d, MAROON, raw=True)
            self.txt(ax, ay + 16 if power_down else ay - 10, label, 7, MAROON, align='center', raw=True)
        else:
            align = 'right' if side == 'left' else 'left'
            tx = ax - 3 if side == 'left' else ax + 3
            self.txt(tx, ay - 5, label, 7, MAROON, align=align, raw=True)
            self.ln(tx - len(label) * 3.8 if side == 'left' else tx, ay - 3,
                    tx if side == 'left' else tx + len(label) * 3.8, ay - 3, MAROON, 0.35, raw=True)
        self.ports.append({'sheet': self._rec_sheet(), 'net': net, 'at': [ax, ay], 'kind': 'power' if power else 'net'})

    def nc(self, ref, p):
        assert self.pnet(ref, p) is None, (ref, p, self.pnet(ref, p))
        ax, ay = self.ppos(ref, p)
        self.ln(ax - 2, ay - 2, ax + 2, ay + 2, BLUE, raw=True)
        self.ln(ax - 2, ay + 2, ax + 2, ay - 2, BLUE, raw=True)
        self.ports.append({'sheet': self._rec_sheet(), 'net': None, 'ref': ref, 'pin': str(p), 'at': [ax, ay], 'kind': 'nc'})

    def block(self, x, y, w, h, title, subtitle=None):
        if self.unified:
            ax, ay = self._ox(x), self._oy(y)
            self.cv.setStrokeColor('#CBD5E1')
            self.cv.setLineWidth(0.7 * self.scale)
            self.cv.rect(self._px(ax - 6), self._py(ay + h + 8), (w + 12) * self.scale, (h + 12) * self.scale, stroke=1, fill=0)
        self.txt(x + 12, y + 18, title, 9, NAVY, 'HB')
        if subtitle:
            self.txt(x + 12, y + 31, subtitle, 6.6, '#404040')

    def element(self, ref, a, b, labels=True):
        c = self.byref[ref]
        k = c['kind']
        assert len(c['pins']) == 2, ref
        assert a[0] == b[0] or a[1] == b[1]
        self.start(ref)
        self.pin(ref, '1', *a)
        self.pin(ref, '2', *b)
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        length = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / length, dy / length
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2

        def pt(s, t=0):
            return (cx + ux * s - uy * t, cy + uy * s + ux * t)

        def seg(s, t, S, T):
            self.ln(*pt(s, t), *pt(S, T), BLUE)

        self.ln(*a, *pt(-5), BLUE)
        self.ln(*pt(5), *b, BLUE)
        if k == 'R':
            self.poly([pt(s, t) for s, t in [(-5, 0), (-4, -2), (-2.4, 2), (-0.8, -2), (0.8, 2), (2.4, -2), (4, 2), (5, 0)]])
        elif k in ('C', 'CP', 'CB'):
            seg(-2, -5, -2, 5)
            seg(-5, 0, -2, 0)
            if k == 'CP':
                pts = [pt(3, -5), pt(1.7, -3), pt(1, -1.5), pt(0.8, 0), pt(1, 1.5), pt(1.7, 3), pt(3, 5)]
                self.poly(pts)
                seg(0.8, 0, 5, 0)
                if uy == 0:
                    px_plus = (cx + ux * (-14), cy - 7)
                    px_minus = (cx + ux * 14, cy - 7)
                    self.txt(*px_plus, '+', 7.5, BLUE, align='center')
                    self.txt(*px_minus, '-', 7.5, BLUE, align='center')
                else:
                    self.txt(*pt(-8, -8), '+', 7.5, BLUE, align='center')
                    self.txt(*pt(8, -8), '-', 7.5, BLUE, align='center')
            else:
                seg(2, -5, 2, 5)
                seg(2, 0, 5, 0)
        elif k in ('D', 'LED'):
            verts = [pt(-3, -3), pt(-3, 3), pt(3, 0)]
            averts = [(self._ox(vx), self._oy(vy)) for vx, vy in verts]
            shape = self.cv.beginPath()
            shape.moveTo(self._px(averts[0][0]), self._py(averts[0][1]))
            for vx, vy in averts[1:]:
                shape.lineTo(self._px(vx), self._py(vy))
            shape.close()
            self.cv.setFillColor(BLUE)
            self.cv.drawPath(shape, fill=1, stroke=0)
            self.active['art'].append({'kind': 'polygon', 'points': [list(v) for v in averts]})
            self.poly([pt(-3, -3), pt(-3, 3), pt(3, 0), pt(-3, -3)])
            seg(3, -4, 3, 4)
            seg(-5, 0, -3, 0)
            seg(3, 0, 5, 0)
            if k == 'LED':
                for s, t in [(0, -6), (5, -4)]:
                    self.poly([pt(s, t), pt(s + 4, t - 4)])
                    self.poly([pt(s + 2, t - 4), pt(s + 4, t - 4), pt(s + 4, t - 2)])
        if labels:
            if uy == 0:
                self.txt(cx, cy - (16 if k == 'CP' else 13), ref, 8, NAVY, align='center')
                self.txt(cx, cy + 17, c['value'] if k != 'LED' else 'LED', 7, NAVY, align='center')
            else:
                self.txt(cx + 11, cy - 3, ref, 8, NAVY)
                self.txt(cx + 11, cy + 10, c['value'], 7, NAVY)
        self.finish()

    def opunit(self, ref, unit, x, y):
        u = 1 if unit == 'A' else 2
        self.start(ref, u)
        pn, pp, po = ('2', '3', '1') if u == 1 else ('6', '5', '7')
        self.pin(ref, pn, x - 40, y - 10)
        self.pin(ref, pp, x - 40, y + 10)
        self.pin(ref, po, x + 40, y)
        ax, ay = self._ox(x), self._oy(y)
        self.cv.setFillColor('#FFFFB0')
        self.cv.setStrokeColor(BLUE)
        pp_ = self.cv.beginPath()
        pp_.moveTo(self._px(ax - 15), self._py(ay - 22))
        pp_.lineTo(self._px(ax - 15), self._py(ay + 22))
        pp_.lineTo(self._px(ax + 20), self._py(ay))
        pp_.close()
        self.cv.drawPath(pp_, fill=1, stroke=0)
        self.poly([(x - 15, y - 22), (x - 15, y + 22), (x + 20, y), (x - 15, y - 22)])
        self.ln(x - 40, y - 10, x - 15, y - 10, BLACK)
        self.ln(x - 40, y + 10, x - 15, y + 10, BLACK)
        self.ln(x + 20, y, x + 40, y, BLACK)
        self.txt(x - 11, y - 7, '-', 8)
        self.txt(x - 11, y + 13, '+', 8)
        for p, xx, yy in [(pn, x - 30, y - 14), (pp, x - 30, y + 6), (po, x + 27, y - 4)]:
            self.txt(xx, yy, p, 6, align='center')
        self.txt(x - 85 if ref == 'U3' else x, y - 10 if ref == 'U3' else y - 30, ref + unit, 8, NAVY, align='center')
        self.txt(x, y + 34, 'TL072', 7, BLACK, align='center')
        self.finish()

    def powerunit(self, ref, x, y):
        self.start(ref, 3)
        ax, ay = self._ox(x), self._oy(y)
        self.cv.setFillColor('#FFFFB0')
        self.cv.setStrokeColor(MAROON)
        self.cv.setLineWidth(0.6 * self.scale)
        self.cv.rect(self._px(ax - 20), self._py(ay + 38), 75 * self.scale, 28 * self.scale, fill=1, stroke=1)
        self.active['art'].append({'kind': 'rect', 'rect': [ax - 20, ay + 10, 75, 28]})
        for p, yy, end in [('8', y, y + 10), ('4', y + 50, y + 38)]:
            self.pin(ref, p, x, yy)
            self.ln(x, yy, x, end, BLACK)
            self.txt(x + 5, (yy + end) / 2 + 2, p, 6)
        self.txt(x + 17, y + 22, ref + ' · alimentação', 7, NAVY, align='center')
        self.txt(x + 17, y + 33, 'TL072', 6.5, BLACK, align='center')
        self.finish()
        self.netport(ref, '8', power=True)
        self.netport(ref, '4', power=True, power_down=True)

    def device(self, ref, rect_, rows):
        x, y, w, h = rect_
        self.start(ref)
        ax, ay = self._ox(x), self._oy(y)
        self.cv.setFillColor('#FFFFB0')
        self.cv.setStrokeColor(MAROON)
        self.cv.setLineWidth(0.6 * self.scale)
        self.cv.rect(self._px(ax), self._py(ay + h), w * self.scale, h * self.scale, fill=1, stroke=1)
        self.active['art'].append({'kind': 'rect', 'rect': [ax, ay, w, h]})
        if ref.startswith('J') or ref == 'PSU_12V':
            self.txt(x + w / 2, y + 13, ref, 8, NAVY, align='center')
        else:
            self.txt(x + w / 2, y - 15, ref, 8, NAVY, align='center')
            self.txt(x + w / 2, y - 5, self.byref[ref]['value'], 7, BLACK, align='center')
        for p, side, px, py, name in rows:
            self.pin(ref, p, px, py)
            xx = x if side == 'L' else x + w
            self.ln(px, py, xx, py, BLACK)
            self.txt((px + xx) / 2, py - 4, p, 5.8, align='center')
            self.txt(xx + 4 if side == 'L' else xx - 4, py + 2, name, 6.7, BLACK, align='left' if side == 'L' else 'right')
        self.finish()

    def jack(self, ref, x, y, name):
        self.device(ref, (x - 55, y - 20, 40, 65), [('1', 'R', x, y, 'TIP'), ('2', 'R', x, y + 35, 'GND')])
        self.txt(x - 35, y + 56, name, 7, BLACK, align='center')

    def switch(self, ref, x, y):
        self.start(ref)
        for p, xx, yy in [('C', x - 30, y), ('1', x + 30, y), ('2', x + 30, y - 15)]:
            self.pin(ref, p, xx, yy)
        self.ln(x - 30, y, x - 5, y)
        self.ln(x + 5, y, x + 30, y)
        self.ln(x + 5, y - 15, x + 30, y - 15)
        for xx, yy in [(x - 5, y), (x + 5, y), (x + 5, y - 15)]:
            self.circle(xx, yy, 1.15)
        self.ln(x - 4, y - 1, x + 4, y - 10, BLUE)
        self.txt(x, y - 29, ref, 8, NAVY, align='center')
        self.txt(x, y + 27, 'MTS-102', 7, BLACK, align='center')
        for p, xx, yy in [('C', x - 21, y + 9), ('1', x + 21, y + 9), ('2', x + 21, y - 19)]:
            self.txt(xx, yy, p, 5.8)
        self.finish()
        self.nc(ref, '2')

    def open_link(self, ref, a, b):
        self.start(ref)
        self.pin(ref, '1', *a)
        self.pin(ref, '2', *b)
        x, y = a
        X, _ = b
        self.ln(x, y, x + 25, y)
        self.ln(X - 25, y, X, y)
        self.circle(x + 25, y, 1.5)
        self.circle(X - 25, y, 1.5)
        self.txt((x + X) / 2, y - 18, ref, 8, NAVY, align='center')
        self.txt((x + X) / 2, y + 21, 'SEM SHUNT (ABERTO NO TESTE 1)', 6.5, BLACK, align='center')
        self.finish()

    def page1(self):
        self.block(40, 65, 760, 190, '1A  Fonte Bancada 12 V → CW7805 → +5VA', 'I_limit = 250-300 mA na bancada · D1 1N4007 · J5 aberto até confirmar 5,0 V')
        self.device('PSU_12V', (45, 115, 85, 65), [('1', 'R', 155, 135, '+12V'), ('2', 'R', 155, 165, 'GND')])
        self.element('D1', (195, 135), (245, 135))
        self.link(('PSU_12V', '1'), ('D1', '1'))
        self.ground('PSU_12V', '2', (155, 185))
        self.element('C33', (285, 135), (285, 205))
        self.link(('D1', '2'), ('C33', '1'))
        self.ground('C33', '2', (285, 225))
        self.device('U5', (450, 110, 100, 70), [('1', 'L', 420, 135, 'IN'), ('3', 'R', 580, 135, 'OUT'), ('2', 'L', 420, 170, 'GND / TAB')])
        self.element('C21', (380, 135), (380, 205))
        self.link(('C33', '1'), ('C21', '1'))
        self.link(('C21', '1'), ('U5', '1'))
        self.ground('C21', '2')
        self.ground('U5', '2', (420, 205))
        self.element('C22', (620, 135), (620, 205))
        self.element('R21', (690, 135), (690, 205))
        self.element('C37', (755, 135), (755, 205))
        self.link(('U5', '3'), ('C22', '1'))
        self.link(('C22', '1'), ('R21', '1'))
        self.link(('R21', '1'), ('C37', '1'))
        self.netport('C37', '1', (785, 135), power=True)
        for r in ('C22', 'R21', 'C37'):
            self.ground(r, '2')
        self.element('D8', (580, 260), (420, 260))
        self.frompin('D8', '1', (600, 260), (600, 135))
        self.frompin('D8', '2', (355, 260), (355, 135))
        self.open_link('J5', (650, 260), (730, 260))
        self.link(('D8', '1'), ('J5', '1'), (600, 260))
        self.netport('J5', '2', (775, 260), power=True)
        self.netport('C33', '1', (325, 135), power=True)
        self.block(40, 295, 340, 170, '1B  Referência dos Op-Amps (VREF_OP)', 'VREF_OP ≈ +RAW / 2 · C38 eletrolítico + C39 cerâmico')
        self.element('R22', (125, 350), (125, 390))
        self.element('R23', (125, 390), (125, 450))
        self.netport('R22', '1', power=True)
        self.link(('R22', '2'), ('R23', '1'))
        self.ground('R23', '2')
        self.element('C38', (220, 390), (220, 450))
        self.element('C39', (300, 390), (300, 450))
        self.link(('R23', '1'), ('C38', '1'))
        self.link(('C38', '1'), ('C39', '1'))
        self.ground('C38', '2')
        self.ground('C39', '2')
        self.netport('C39', '1', (350, 390), side='right')
        self.block(430, 295, 370, 170, '1C  Referência do ADC (ADC_BIAS)', '0,48 × +5VA · independente de VCOM')
        self.element('R27', (500, 350), (500, 390))
        self.element('R28', (500, 390), (500, 450))
        self.netport('R27', '1', power=True)
        self.link(('R27', '2'), ('R28', '1'))
        self.ground('R28', '2')
        self.element('C40', (600, 390), (600, 450))
        self.element('C41', (700, 390), (700, 450))
        self.link(('R28', '1'), ('C40', '1'))
        self.link(('C40', '1'), ('C41', '1'))
        self.ground('C40', '2')
        self.ground('C41', '2')
        self.netport('C41', '1', (770, 390))

    def page2(self):
        self.block(40, 65, 260, 235, '2A  Guitarra, Buffer U1A e Clamps 1N4007', 'C1 cerâmico · D6/D7/D13/D14 = 1N4007')
        self.jack('J2', 100, 175, 'IN P10')
        self.element('C1', (110, 175), (140, 175))
        self.element('R26', (145, 175), (175, 175))
        self.link(('J2', '1'), ('C1', '1'))
        self.link(('C1', '2'), ('R26', '1'))
        self.ground('J2', '2', (110, 210))
        self.opunit('U1', 'A', 220, 165)
        self.link(('R26', '2'), ('U1', '3'))
        self.link(('U1', '1'), ('U1', '2'), (285, 165), (285, 125), (175, 125), (175, 155))
        self.element('R3', (125, 205), (125, 270))
        self.element('D6', (190, 205), (190, 235))
        self.element('D13', (190, 235), (190, 270))
        self.element('D7', (255, 270), (255, 235))
        self.element('D14', (255, 235), (255, 205))
        self.link(('D6', '2'), ('D13', '1'))
        self.link(('D7', '2'), ('D14', '1'))
        self.frompin('R26', '2', (175, 205), (125, 205))
        self.link(('R3', '1'), ('D6', '1'))
        self.link(('D6', '1'), ('D14', '2'))
        self.link(('R3', '2'), ('D13', '2'))
        self.link(('D13', '2'), ('D7', '1'))
        self.netport('R3', '2', (125, 290), power=True, power_down=True)
        self.txt(52, 330, 'MVP: sem Q11..Q14 (sem clamp ativo em AIN).', 7)
        self.txt(52, 344, 'C2/C16 eletrolíticos: + no lado TL072,', 7)
        self.txt(52, 358, '- no lado CS4272 (ADC_BIAS ~2,4 V).', 7)
        self.txt(52, 376, 'C35/C36 100 pF MANTIDOS p/ RF do ADC.', 7, MAROON)
        self.block(310, 65, 485, 410, '2B  Drivers U3A/U3B + Acoplamento + RF C35/C36', 'U3A = +1 · U3B = -1 · C2/C16 eletrolíticos 10 µF (+ para esquerda)')
        self.opunit('U3', 'A', 470, 165)
        self.opunit('U3', 'B', 470, 350)
        self.link(('U1', '1'), ('U3', '3'), (340, 165), (340, 175))
        self.element('R24', (300, 340), (360, 340))
        self.frompin('U1', '1', (300, 165), (300, 340))
        self.link(('R24', '2'), ('U3', '6'))
        self.netport('U3', '5', (395, 360), power=True)
        for rf, cc, rs, pn, po, fb_y, cf_y, out_y in [
            ('R17', 'C18', 'R18', '2', '1', 120, 145, 165),
            ('R19', 'C19', 'R20', '6', '7', 305, 330, 350),
        ]:
            self.element(rf, (430, fb_y), (490, fb_y))
            self.element(cc, (470, cf_y), (530, cf_y), labels=False)
            self.txt(500, cf_y - 13, cc, 8, NAVY, align='center')
            self.txt(560, cf_y - 3, self.byref[cc]['value'], 6.5, NAVY)
            self.element(rs, (550, out_y), (610, out_y))
            self.link(('U3', pn), (rf, '1'))
            self.link((rf, '1'), (cc, '1'), (430, cf_y))
            self.link(('U3', po), (rs, '1'))
            self.link((cc, '2'), (rs, '1'), (530, out_y))
            self.link((rf, '2'), (rs, '1'), (550, fb_y))
        self.element('C2', (635, 165), (685, 165))
        self.element('C16', (635, 350), (685, 350))
        self.link(('R18', '2'), ('C2', '1'))
        self.link(('R20', '2'), ('C16', '1'))
        self.element('R15', (715, 165), (715, 225))
        self.element('R16', (715, 350), (715, 410))
        self.link(('C2', '2'), ('R15', '1'))
        self.link(('C16', '2'), ('R16', '1'))
        self.netport('R15', '2', side='right')
        self.netport('R16', '2', side='right')
        self.element('C35', (685, 220), (685, 260), labels=False)
        self.frompin('R15', '1', (685, 165), (685, 220))
        self.ground('C35', '2', (685, 275))
        self.txt(668, 238, 'C35', 7.5, NAVY, align='right')
        self.txt(668, 250, '100 pF', 6.5, NAVY, align='right')
        self.element('C36', (685, 395), (685, 435), labels=False)
        self.frompin('R16', '1', (685, 350), (685, 395))
        self.ground('C36', '2', (685, 450))
        self.txt(668, 413, 'C36', 7.5, NAVY, align='right')
        self.txt(668, 425, '100 pF', 6.5, NAVY, align='right')
        self.element('C20', (745, 165), (745, 350))
        self.link(('R15', '1'), ('C20', '1'))
        self.link(('R16', '1'), ('C20', '2'))
        self.netport('C20', '1', (765, 165), side='right')
        self.netport('C20', '2', (765, 350), side='right')

    def page3(self):
        self.block(40, 65, 305, 410, '3A  Codec CS4272 (TSSOP-28 + adaptador)')
        L = [('3', 135, 'MCLK'), ('4', 155, 'LRCK'), ('5', 175, 'SCLK'), ('7', 195, 'SDIN'),
             ('6', 215, 'SDOUT'), ('11', 250, 'SCL'), ('12', 270, 'SDA'), ('14', 290, '/RST'),
             ('13', 320, 'AD0'), ('2', 340, 'XTI'), ('1', 365, 'XTO'), ('8', 425, 'DGND'), ('21', 445, 'AGND')]
        R = [('20', 130, 'VA'), ('9', 150, 'VD'), ('10', 170, 'VL'), ('15', 200, 'VCOM'),
             ('22', 230, 'FILT+'), ('17', 270, 'AINA+'), ('16', 290, 'AINA-'), ('18', 320, 'AINB+'),
             ('19', 340, 'AINB-'), ('25', 370, 'AOUTA+'), ('24', 390, 'AOUTA-'), ('26', 410, 'AOUTB+'),
             ('27', 425, 'AOUTB-'), ('23', 440, 'AMUTEC'), ('28', 455, 'BMUTEC')]
        self.device('U2', (140, 110, 145, 355), [(p, 'L', 110, y, n) for p, y, n in L] + [(p, 'R', 315, y, n) for p, y, n in R])
        for p in ['3', '4', '5', '7', '6', '11', '12', '14']:
            self.netport('U2', p)
        self.link(('U2', '13'), ('U2', '2'), (80, 320), (80, 340))
        self.ground('U2', '2', (80, 340))
        self.nc('U2', '1')
        self.link(('U2', '8'), ('U2', '21'), (85, 425), (85, 445))
        self.ground('U2', '21', (85, 445))
        self.netport('U2', '20', (355, 130), power=True)
        self.link(('U2', '9'), ('U2', '10'), (365, 150), (365, 170))
        self.netport('U2', '9', (400, 150), power=True)
        self.dotat_raw(self._ox(365), self._oy(150))
        for p in ['17', '16', '25', '24']:
            self.netport('U2', p, side='right')
        for p in ['26', '27', '23', '28']:
            self.nc('U2', p)
        self.block(375, 65, 425, 230, '3B  FILT+ e VCOM', 'C14 = 1 µF CERÂMICO (não eletrolítico) · C12 + no pino 22')
        self.element('C12', (435, 230), (435, 275))
        self.element('C13', (505, 230), (505, 275))
        self.link(('U2', '22'), ('C12', '1'))
        self.link(('C12', '1'), ('C13', '1'))
        self.dotpin('C12', '1')
        self.link(('C12', '2'), ('C13', '2'))
        self.ground('C13', '2')
        self.txt(470, 224, 'FILT+', 7, MAROON, align='center')
        self.element('C14', (635, 200), (635, 275))
        self.element('C15', (715, 200), (715, 275))
        self.link(('U2', '15'), ('C14', '1'))
        self.link(('C14', '1'), ('C15', '1'))
        self.dotpin('C14', '1')
        self.link(('C14', '2'), ('C15', '2'))
        self.ground('C15', '2')
        self.txt(575, 194, 'VCOM', 7, MAROON, align='center')
        self.block(375, 305, 425, 170, '3C  Canal ADC B Não Usado')
        self.link(('U2', '18'), ('U2', '19'), (365, 320), (365, 340))
        self.dotat_raw(self._ox(365), self._oy(340))
        self.element('R10', (505, 385), (445, 385))
        self.frompin('U2', '19', (365, 340), (365, 355), (420, 355), (420, 385), (445, 385))
        self.netport('R10', '1', (545, 385), side='right', display='ADC_BIAS')
        self.element('C34', (650, 420), (650, 455))
        self.frompin('R10', '2', (420, 385), (420, 420), (650, 420))
        self.ground('C34', '2')
        self.dotat_raw(self._ox(420), self._oy(385))

    def page4(self):
        self.block(40, 65, 760, 255, '4A  Receptor DAC U1B (ganho 0,499)', 'C10/C11 eletrolíticos 10 µF: + para R1/R7 (~5,5 V), - para CS4272 (~2,4 V)')
        # C11 e C10 desenhados da direita (pin 1 = + em R7/R1) para esquerda (pin 2 = - em AOUTA)
        self.element('C11', (165, 145), (100, 145))
        self.netport('C11', '2', (85, 145), display='AOUTA_N')
        self.element('R7', (195, 145), (255, 145))
        self.link(('C11', '1'), ('R7', '1'))
        self.element('C10', (165, 245), (100, 245))
        self.netport('C10', '2', (85, 245), display='AOUTA_P')
        self.element('R1', (195, 245), (255, 245))
        self.link(('C10', '1'), ('R1', '1'))
        self.opunit('U1', 'B', 390, 200)
        self.link(('R7', '2'), ('U1', '6'), (310, 145), (310, 190))
        self.link(('R1', '2'), ('U1', '5'), (280, 245), (280, 210))
        self.dotat_raw(self._ox(280), self._oy(245))
        self.element('R2', (280, 245), (280, 290))
        self.netport('R2', '2', power=True, power_down=True)
        self.element('R8', (320, 115), (380, 115))
        self.link(('R8', '1'), ('U1', '6'), (310, 115), (310, 190))
        self.dotat_raw(self._ox(310), self._oy(190))
        self.dotat_raw(self._ox(310), self._oy(145))
        self.link(('R8', '2'), ('U1', '7'), (465, 115), (465, 200))
        self.dotat_raw(self._ox(465), self._oy(200))
        self.netport('U1', '7', (540, 200), side='right', display='DAC_BUF')
        self.txt(580, 155, 'R1/R7 = 100 kΩ · R2/R8 = 49,9 kΩ (0,1%).', 7.5)
        self.txt(580, 175, 'C10/C11: + em DAC_AC_P/N, - em AOUTA.', 7, MAROON)
        self.block(40, 345, 760, 130, '4B  Filtro RC e Saída Direta P10 (sem K1)', 'C5 eletrolítico (+ em LP2) · R6 47 kΩ descarga · atenção p/ pop na partida')
        self.element('R4', (95, 400), (155, 400))
        self.netport('R4', '1', (85, 400), display='DAC_BUF')
        self.element('C4', (200, 400), (200, 445))
        self.link(('R4', '2'), ('C4', '1'))
        self.ground('C4', '2')
        self.dotpin('C4', '1')
        self.element('R5', (265, 400), (325, 400))
        self.link(('C4', '1'), ('R5', '1'))
        self.element('C6', (370, 400), (370, 445))
        self.link(('R5', '2'), ('C6', '1'))
        self.ground('C6', '2')
        self.dotpin('C6', '1')
        self.element('C5', (450, 400), (510, 400))
        self.link(('C6', '1'), ('C5', '1'))
        self.element('R6', (550, 400), (550, 445))
        self.link(('C5', '2'), ('R6', '1'))
        self.ground('R6', '2')
        self.device('J3', (700, 395, 60, 60), [('1', 'L', 670, 410, 'TIP'), ('2', 'L', 670, 440, 'GND')])
        self.link(('R6', '1'), ('J3', '1'), (550, 410))
        self.ground('J3', '2', (670, 455))
        self.txt(730, 467, 'OUT P10', 7, BLACK, align='center')

    def page5(self):
        self.block(40, 65, 440, 410, '5A  STM32H723 WeAct V1.2', 'USB própria · PD10 direto p/ /RST · PC2_C/PC3_C')
        left = [('P1.4', 130), ('P2.5', 155), ('P2.6', 180), ('P2.7', 205), ('P2.17', 230),
                ('P1.6', 270), ('P1.5', 295), ('P1.38', 330), ('P1.2', 390), ('P2.2', 415), ('P1.1', 445)]
        right = [('P1.40', 130), ('P1.39', 155), ('P2.11', 205), ('P2.12', 230), ('P2.13', 255),
                 ('P2.14', 280), ('P2.30', 315), ('P2.31', 340), ('P2.32', 365), ('P2.38', 390)]
        a = self.byref['H_STM32']
        self.device('H_STM32', (245, 110, 150, 345),
                    [(p, 'L', 215, y, a['names'][p]) for p, y in left] + [(p, 'R', 425, y, a['names'][p]) for p, y in right])
        for p, y in left[:8]:
            self.netport('H_STM32', p, (140, y), display=self.pnet('H_STM32', p))
        for p, y in right[2:]:
            self.netport('H_STM32', p, side='right')
        self.nc('H_STM32', 'P1.2')
        self.netport('H_STM32', 'P2.2', (170, 415), power=True)
        self.ground('H_STM32', 'P1.1', (170, 445))
        self.block(500, 65, 300, 235, '5B  UART Direta + ESP32 DevKit V1', 'R_UTX/R_URX = 1 kΩ · apenas GND comum (USB separadas)')
        self.device('H_ESP32', (665, 145, 110, 145), [
            ('RX2', 'L', 635, 165, 'GPIO16 RX2'), ('TX2', 'L', 635, 190, 'GPIO17 TX2'),
            ('VIN', 'L', 635, 220, 'VIN / NC'), ('3V3', 'L', 635, 245, '3V3 / NC'), ('GND', 'L', 635, 270, 'GND')])
        self.nc('H_ESP32', 'VIN')
        self.nc('H_ESP32', '3V3')
        self.ground('H_ESP32', 'GND', (610, 270))
        self.element('R_UTX', (515, 130), (565, 130))
        self.element('R_URX', (565, 190), (515, 190))
        self.link(('H_STM32', 'P1.40'), ('R_UTX', '1'))
        self.link(('R_UTX', '2'), ('H_ESP32', 'RX2'), (600, 130), (600, 165))
        self.link(('H_ESP32', 'TX2'), ('R_URX', '1'))
        self.link(('R_URX', '2'), ('H_STM32', 'P1.39'), (485, 190), (485, 155))
        self.block(500, 305, 300, 170, '5C  Pull-ups I2C e Pull-downs /RST / Boot')
        self.element('R11', (555, 345), (555, 390))
        self.element('R12', (670, 345), (670, 390))
        self.link(('R11', '1'), ('R12', '1'))
        self.netport('R11', '1', (610, 345), power=True)
        self.netport('R11', '2', side='right', display='I2C_SCL')
        self.netport('R12', '2', side='right', display='I2C_SDA')
        self.element('R13', (555, 415), (555, 450))
        self.element('R14', (670, 415), (670, 450))
        self.netport('R13', '1', display='CODEC_RST')
        self.netport('R14', '1', display='ADC_DATA')
        self.ground('R13', '2')
        self.ground('R14', '2')

    def page6(self):
        self.block(40, 65, 350, 410, '6A  Chaves SW1..SW4', 'Fechado = LOW · PC2_C/PC3_C exigem SYSCFG ou remap')
        self.block(420, 65, 380, 410, '6B  LEDs Indicadores', 'PE7/8/9/15 → 330 Ω → LED → GND')
        for i, (sw, d, net, gpio) in enumerate([
            ('SW1', 'D2', 'LED_OD', 'PE7'), ('SW2', 'D3', 'LED_EQ', 'PE8'),
            ('SW3', 'D4', 'LED_DLY', 'PE9'), ('SW4', 'D5', 'LED_STAT', 'PE15'),
        ]):
            y = 145 + i * 85
            self.switch(sw, 220, y)
            self.netport(sw, 'C', (95, y), display=self.pnet(sw, 'C'))
            self.ground(sw, '1', (325, y))
            self.txt(65, y + 25, ['PC0', 'PC1', 'PC2_C', 'PC3_C'][i], 7, BLACK)
            self.txt(52, y - 27, self.byref[d]['function'], 8, BLACK)
            self.element('R_' + d, (495, y), (555, y))
            self.netport('R_' + d, '1', (470, y), display=net)
            self.element(d, (625, y), (685, y))
            self.link(('R_' + d, '2'), (d, '1'))
            self.ground(d, '2', (750, y))
            self.txt(465, y + 25, gpio, 7, BLACK)

    def page7(self):
        self.block(40, 65, 760, 200, '7A  Desacoplamento Local CS4272', 'Soldar a poucos mm dos pinos VA (20), VD (9), VL (10)')
        for r1, r2, x, caption in [('C23', 'C24', 125, 'VA · U2 pino 20'), ('C25', 'C26', 355, 'VD · U2 pino 9'), ('C27', 'C28', 585, 'VL · U2 pino 10')]:
            self.element(r1, (x, 145), (x, 220))
            self.element(r2, (x + 65, 145), (x + 65, 220))
            self.link((r1, '1'), (r2, '1'))
            self.netport(r1, '1', (x + 30, 145), power=True)
            self.link((r1, '2'), (r2, '2'))
            self.ground(r2, '2', (x + 30, 220))
            self.txt(x + 30, 260, caption, 7, BLACK, align='center')
        self.block(40, 290, 460, 180, '7B  Desacoplamento TL072 (U1/U3)', 'C30/C32 eletrolíticos (+ em +RAW, - em GND)')
        for ra, rb, x, caption in [('C29', 'C30', 100, 'U1: pinos 8/4'), ('C31', 'C32', 320, 'U3: pinos 8/4')]:
            self.element(ra, (x, 365), (x, 430))
            self.element(rb, (x + 70, 365), (x + 70, 430))
            self.link((ra, '1'), (rb, '1'))
            self.netport(ra, '1', (x + 35, 365), power=True)
            self.link((ra, '2'), (rb, '2'))
            self.ground(rb, '2', (x + 35, 430))
            self.txt(x + 35, 472, caption, 7, BLACK, align='center')
        self.block(520, 290, 275, 180, '7C  Alimentação TL072')
        self.powerunit('U1', 640, 335)
        self.powerunit('U3', 755, 335)

    def mark_junctions_for_sheet(self, sh):
        seg = []
        points = set()
        pins = set()
        for a in self.instances:
            if a['sheet'] == sh:
                pins.update(tuple(v) for v in a['pins'].values())
        points.update(pins)
        for r in self.routes:
            if r['sheet'] != sh:
                continue
            for a, b in zip(r['points'], r['points'][1:]):
                a, b = tuple(a), tuple(b)
                if a != b:
                    seg.append((a, b))
                    points.update([a, b])
        adj = defaultdict(set)
        for a, b in seg:
            pts = sorted(p for p in points if min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
                         and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
                         and (a[0] == b[0] == p[0] or a[1] == b[1] == p[1]))
            for c, d in zip(pts, pts[1:]):
                adj[c].add(d)
                adj[d].add(c)
        for pt, neighbors in adj.items():
            if len(neighbors) + (pt in pins) >= 3:
                self.dotat_raw(*pt)

    def draw_single_sheet(self, n):
        self.unified = False
        self.current_sheet = n
        self.ox, self.oy = 0, 0
        self.in_draw = True
        getattr(self, f'page{n}')()
        self.mark_junctions_for_sheet(n)
        self.in_draw = False

    def draw_unified_a1(self):
        self.unified = True
        self.in_draw = True
        for sh, (ox, oy) in UNIFIED_SLOTS.items():
            self.current_sheet = sh
            self.ox, self.oy = ox, oy
            getattr(self, f'page{sh}')()
        # Painel 8 (Slot inferior direito: etapas, fluxo de sinal, polaridades e protocolo de bancada)
        self.ox, self.oy = 0, 0
        bx, by, bw, bh = 1125, 1340, 1860, 410
        self.cv.setStrokeColor('#CBD5E1')
        self.cv.setLineWidth(0.9 * self.scale)
        self.cv.rect(self._px(bx), self._py(by + bh), bw * self.scale, bh * self.scale, stroke=1, fill=0)
        self.txt(bx + 18, by + 24, '8  GUIA DE IMPLEMENTAÇÃO E REGRAS CRÍTICAS DO MVP REV. A (91 COMPONENTES)', 11, NAVY, 'HB', raw=True)
        lines = [
            ('FLUXO END-TO-END (NOMES IGUAIS CONECTAM NA PRANCHA):', True, NAVY),
            ('  [1] Bancada 12V (I_limit 250-300 mA) -> D1 (1N4007) -> +RAW -> U5 (CW7805) -> J5 -> +5VA | R22/23 -> VREF_OP (~5,5V) | R27/28 -> ADC_BIAS (~2,4V)', False, BLACK),
            ('  [2->3->4] J2 (P10 IN) -> C1 -> U1A (Buffer) -> U3A/U3B -> C2/C16 -> AINA_P/N -> U2 (CS4272) -> AOUTA_P/N -> C10/C11 -> U1B -> R4/C4/R5/C6 -> C5/R6 -> J3 (P10 OUT)', False, BLACK),
            ('  [5<->3/6] H_STM32 (USB propria) <-> U2 (SAI4/I2C/PD10 direto c/ R13=10k) | UART direta 115200: PD8-[R_UTX 1k]->GPIO16 e GPIO17-[R_URX 1k]->PD9 | SW1..4/D2..5', False, BLACK),
            ('CORTES / SUBSTITUICOES DO MVP:', True, NAVY),
            ('  - Removidos: Folha 9 (25), Folha 10 (42), Q11..Q14 (4), K1/D16 (2), U6+passivos (7), J1/F1/J4/TP* (14). Adicionados: R_UTX/R_URX (2x 1k). MANTIDOS: C35/C36 (100 pF RF)!', False, BLACK),
            ('  - Diodos: todos 6x 1N4007 (D1, D8, D6, D7, D13, D14). Capacitores: APENAS ceramicos (<=1 uF) e eletroliticos (>=10 uF).', False, BLACK),
            ('POLARIDADE OBRIGATORIA DOS 12 ELETROLITICOS (+ / -):', True, MAROON),
            ('  - C2, C16 (10 uF): (+) lado R18/R20 (~5,5V), (-) lado AINA_P/N (~2,4V) | C10, C11 (10 uF): (+) lado R1/R7 (~5,5V), (-) lado CS4272 AOUTA (~2,4V)', False, BLACK),
            ('  - C5 (10 uF): (+) em LP2, (-) em OUT_PRE | C12 (47 uF): (+) pino 22 FILT+ | C33/C30/C32 (+ em +RAW) | C37 (+ em +5V_CW) | C38 (+ em VREF_OP) | C40 (+ em ADC_BIAS)', False, BLACK),
            ('  - ATENCAO C14 (1 uF em VCOM pino 15): usar CERAMICO (nao eletrolitico) para nao vazar corrente em VCOM (~25 kohm).', False, MAROON),
            ('PROTOCOLO DE BANCADA & FIRMWARE PENDENTE:', True, NAVY),
            ('  1) Ligar sempre na ordem: J5 ABERTO testar 5,0V em CW -> fechar J5 -> ligar 12V ANTES da USB STM32 (evita PD10=3V3 com VA=0V) -> ligar amp por ultimo.', False, BLACK),
            ('  2) Firmware STM32 atual tem HAL_SAI_MODULE_ENABLED comentado e dMAIN_AUDIO_TRANSPORT_READY=0U: implementar SAI4+DMA e fechar PC2_C/PC3_C (SYSCFG) antes do audio.', False, BLACK),
        ]
        yy = by + 50
        for text, bold, col in lines:
            self.txt(bx + 18, yy, text, 8.2 if bold else 7.6, col, 'HB' if bold else 'T', raw=True)
            yy += 24 if bold else 22
        self.mark_junctions_for_sheet(1)
        self.in_draw = False
