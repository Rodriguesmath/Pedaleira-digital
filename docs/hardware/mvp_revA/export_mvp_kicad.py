#!/usr/bin/env python3
"""Exporta o modelo MVP Rev. A para KiCad 10:
1. Projeto multi-folha A4 (output/MVP_REVA/kicad/pedaleira_mvp_revA.kicad_sch)
2. Prancha unica A1 unificada (output/MVP_REVA/kicad_unificada/esquematica_mvp_unificada.kicad_sch)
"""
from collections import defaultdict
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'output/MVP_REVA'
S = 0.254


def make_uid_gen(seed_prefix):
    seq = iter(range(1000000))
    return lambda: str(uuid.uuid5(uuid.NAMESPACE_URL, f'{seed_prefix}/{next(seq)}'))


def fmt(n):
    return f'{n:.5f}'.rstrip('0').rstrip('.') if n else '0'


def q(s):
    return json.dumps(str(s), ensure_ascii=False)


def eff(size=1.27, hide=False, align=None):
    just = f' (justify {align})' if align and align != 'center' else ''
    return f'(effects (font (size {fmt(size)} {fmt(size)})){just}{" hide" if hide else ""})'


def prop(k, v, x, y):
    return f'(property {q(k)} {q(v)} (at {fmt(x)} {fmt(y)} 0) {eff(1.27, True)})'


def point(x, y):
    return f'(xy {fmt(x)} {fmt(y)})'


def pin_type(byref, r, p):
    a = byref[r]
    k = a['kind']
    if k == 'OP':
        return 'output' if p in ('1', '7') else 'power_in' if p in ('4', '8') else 'input'
    return a.get('types', {}).get(p, 'passive')


def build_symbol_libs(byref, instances):
    refs = defaultdict(list)
    for a in instances:
        pts = list(a['pins'].values())
        a['center'] = [round((min(p[j] for p in pts) + max(p[j] for p in pts)) / 10) * 5 for j in (0, 1)]
        refs[a['ref']].append(a)

    def local(x, y, c):
        return (x - c[0]) * S, -(y - c[1]) * S

    def graphic_local(a, c):
        k = a['kind']
        if k == 'polygon':
            pts = [local(*v, c) for v in a['points']]
            pts.append(pts[0])
            return '(polyline (pts ' + ' '.join(point(*v) for v in pts) + ') (stroke (width 0.1) (type default)) (fill (type outline)))'
        if k == 'line':
            pts = [local(*v, c) for v in a['points']]
            return '(polyline (pts ' + ' '.join(point(*v) for v in pts) + f') (stroke (width {fmt(a.get("width", 0.6) * S)}) (type default)) (fill (type none)))'
        if k == 'circle':
            x, y = local(*a['at'], c)
            return f'(circle (center {fmt(x)} {fmt(y)}) (radius {fmt(a["radius"] * S)}) (stroke (width 0.15) (type default)) (fill (type none)))'
        if k in ('rect', 'block'):
            x, y, w, h = a['rect']
            x1, y1 = local(x, y, c)
            x2, y2 = local(x + w, y + h, c)
            return f'(rectangle (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)}) (stroke (width 0.15) (type default)) (fill (type background)))'
        if k == 'text':
            x, y = local(*a['at'], c)
            sz = a['size'] * S * 0.75
            align = a.get('align', 'left')
            txt = a['text'].replace('uF', 'µF').replace('kohm', 'kΩ').replace('Mohm', 'MΩ').replace('ohm', 'Ω')
            return f'(text {q(txt)} (at {fmt(x)} {fmt(y + sz * 0.3)} 0) {eff(sz, False, align)})'
        return ''

    libs = {}
    for ref, units in refs.items():
        in_bom = 'yes' if byref[ref].get('in_bom', True) else 'no'
        sym = (f'(symbol {q("mvpA:" + ref)} (pin_names (offset 0) hide) (pin_numbers hide) '
               f'(in_bom {in_bom}) (on_board {in_bom}) '
               + prop('Reference', ref, 0, 0) + prop('Value', byref[ref]['value'], 0, 0))
        for a in units:
            unit = a['unit']
            c = a['center']
            sym += f'(symbol {q(ref + "_" + str(unit) + "_1")} '
            sym += ''.join(graphic_local(g, c) for g in a['art'])
            for p, pt in a['pins'].items():
                x, y = local(*pt, c)
                name = byref[ref].get('names', {}).get(p, p)
                sym += f'(pin {pin_type(byref, ref, p)} line (at {fmt(x)} {fmt(y)} 0) (length 0) (name {q(name)} {eff(1.0)}) (number {q(p)} {eff(1.0)}))'
            sym += ')'
        sym += ')'
        libs[ref] = sym

    for i in range(1, 4):
        ref = f'#FLG0{i}'
        libs[ref] = (
            f'(symbol {q("mvpA:" + ref)} (pin_names (offset 0) hide) (pin_numbers hide) '
            f'(in_bom no) (on_board no) ' + prop('Reference', ref, 0, 0) + prop('Value', 'PWR_FLAG', 0, 0)
            + f'(symbol {q(ref + "_1_1")} (pin power_out line (at 0 0 90) (length 0) (name "pwr" {eff(1, True)}) (number "1" {eff(1, True)}))))'
        )
    return libs, refs


def render_sheet_body(byref, layout, libs, sh, ox, oy, flg_pts, uid, project, path_prefix, unified=False):
    def xy(x, y):
        return x * S + ox, y * S + oy

    def decor_graphic(a):
        k = a['kind']
        if k == 'line':
            pts = [xy(*v) for v in a['points']]
            return '(polyline (pts ' + ' '.join(point(*v) for v in pts) + f') (stroke (width {fmt(a.get("width", 0.6) * S)}) (type default)) (fill (type none)) (uuid {q(uid())}))'
        if k == 'text':
            x, y = xy(*a['at'])
            sz = a['size'] * S * 0.75
            align = a.get('align', 'left')
            txt = a['text'].replace('uF', 'µF').replace('kohm', 'kΩ').replace('Mohm', 'MΩ').replace('ohm', 'Ω')
            return f'(text {q(txt)} (at {fmt(x)} {fmt(y - sz * 0.3)} 0) {eff(sz, False, align)} (uuid {q(uid())}))'
        return ''

    instances = layout['instances']
    units = [a for a in instances if a['sheet'] == sh]
    rnames = {a['ref'] for a in units}
    if sh == 1:
        rnames |= {'#FLG01', '#FLG02', '#FLG03'}

    body = '(lib_symbols ' + ''.join(libs[r] for r in sorted(rnames)) + ')'
    for a in layout['decorations']:
        if a['sheet'] == sh and a['kind'] != 'junction':
            body += decor_graphic(a)

    for a in units:
        r = a['ref']
        unit = a['unit']
        x, y = xy(*a['center'])
        in_bom = 'yes' if byref[r].get('in_bom', True) else 'no'
        body += (
            f'(symbol (lib_id {q("mvpA:" + r)}) (at {fmt(x)} {fmt(y)} 0) (unit {unit}) '
            f'(exclude_from_sim no) (in_bom {in_bom}) (on_board {in_bom}) (dnp no) (uuid {q(uid())}) '
            + prop('Reference', r, x, y) + prop('Value', byref[r]['value'], x, y)
            + prop('Footprint', byref[r].get('footprint', ''), x, y)
            + prop('Package_note', byref[r]['package'], x, y)
            + ''.join(f'(pin {q(p)} (uuid {q(uid())}))' for p in a['pins'])
            + f'(instances (project {q(project)} (path {q(path_prefix)} (reference {q(r)}) (unit {unit})))))'
        )
        for p, pt in a['pins'].items():
            if byref[r]['pins'][p] is None:
                xx, yy = xy(*pt)
                body += f'(no_connect (at {fmt(xx)} {fmt(yy)}) (uuid {q(uid())}))'

    # Segmentos de fios e juncoes
    segments = []
    contacts = set(tuple(v) for a in units for v in a['pins'].values())
    for p in layout['ports']:
        if p['sheet'] == sh:
            contacts.add(tuple(p['at']))
    if sh == 1:
        contacts.update(flg_pts)
    for r in layout['routes']:
        if r['sheet'] != sh:
            continue
        for a, b in zip(r['points'], r['points'][1:]):
            a, b = tuple(a), tuple(b)
            if a != b:
                segments.append((r['net'], a, b))
                contacts.update([a, b])

    def on(p, a, b):
        return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
                and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])
                and (a[0] == b[0] == p[0] or a[1] == b[1] == p[1]))

    for n, a, b in segments:
        for N, c, d in segments:
            if a[0] == b[0] and c[1] == d[1]:
                pt = (a[0], c[1])
                if on(pt, a, b) and on(pt, c, d):
                    assert n == N, ('crossed nets', sh, n, N, pt)
                    contacts.add(pt)

    edges = set()
    for n, a, b in segments:
        pts = sorted(p for p in contacts if on(p, a, b))
        for c, d in zip(pts, pts[1:]):
            edges.add((n, c, d))

    degree = defaultdict(int)
    for _, a, b in sorted(edges):
        degree[a] += 1
        degree[b] += 1
        body += '(wire (pts ' + point(*xy(*a)) + ' ' + point(*xy(*b)) + f') (stroke (width 0) (type default)) (uuid {q(uid())}))'
    for pt, d in degree.items():
        if d >= 3:
            x, y = xy(*pt)
            body += f'(junction (at {fmt(x)} {fmt(y)}) (diameter 0) (color 0 0 0 0) (uuid {q(uid())}))'

    portnets = set()
    seen = set()
    for p in layout['ports']:
        if p['sheet'] != sh or p['net'] is None:
            continue
        net = p['net']
        pt = tuple(p['at'])
        if (net, pt) in seen:
            continue
        seen.add((net, pt))
        portnets.add(net)
        xx, yy = xy(*pt)
        if unified:
            body += f'(label {q(net)} (at {fmt(xx)} {fmt(yy)} 0) {eff(0.85)} (uuid {q(uid())}))'
        else:
            pages = {a['sheet'] for a in instances for pin in a['pins'] if byref[a['ref']]['pins'][pin] == net}
            if len(pages) > 1:
                body += f'(global_label {q(net)} (shape passive) (at {fmt(xx)} {fmt(yy)} 0) {eff(0.85)} (uuid {q(uid())}) ' + prop('Intersheetrefs', '${INTERSHEET_REFS}', xx, yy) + ')'
            else:
                body += f'(label {q(net)} (at {fmt(xx)} {fmt(yy)} 0) {eff(0.85)} (uuid {q(uid())}))'

    internal = {byref[a['ref']]['pins'][p] for a in units for p in a['pins'] if byref[a['ref']]['pins'][p] is not None} - portnets
    for net in sorted(internal):
        pt = next(tuple(pt) for a in units for p, pt in a['pins'].items() if byref[a['ref']]['pins'][p] == net)
        xx, yy = xy(*pt)
        body += f'(label {q(net)} (at {fmt(xx)} {fmt(yy)} 0) {eff(0.85)} (uuid {q(uid())}))'

    if sh == 1:
        for i, pt in enumerate(flg_pts, 1):
            r = f'#FLG0{i}'
            x, y = xy(*pt)
            body += (
                f'(symbol (lib_id {q("mvpA:" + r)}) (at {fmt(x)} {fmt(y)} 0) (unit 1) '
                f'(in_bom no) (on_board no) (dnp no) (uuid {q(uid())}) '
                + prop('Reference', r, x, y) + prop('Value', 'PWR_FLAG', x, y)
                + f'(instances (project {q(project)} (path {q(path_prefix)} (reference {q(r)}) (unit 1)))))'
            )
    return body


def export_project(model_path, layout_path, out_dir, project, paper, ox, oy, flg_pts, unified=False):
    out_dir.mkdir(parents=True, exist_ok=True)
    model = json.loads(model_path.read_text())
    byref = {a['ref']: a for a in model['components']}
    layout = json.loads(layout_path.read_text())
    uid = make_uid_gen(f'pedaleira/{project}')
    libs, _ = build_symbol_libs(byref, layout['instances'])

    def header(title, doc_uid):
        return (f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {q(doc_uid)}) (paper {q(paper)}) '
                f'(title_block (title {q(title)}) (rev "MVP-A") (company "Rodrigues M. Lima"))')

    if unified:
        root_uid = uid()
        doc = header('Pedaleira Digital MVP Rev. A — Esquemática Unificada', root_uid)
        doc += render_sheet_body(byref, layout, libs, 1, ox, oy, flg_pts, uid, project, '/', unified=True)
        doc += f'(sheet_instances (path "/" (page "1")))'
        (out_dir / f'{project}.kicad_sch').write_text(doc + ')')
    else:
        root_uid = uid()
        sheetids = {int(k): uid() for k in layout['pages']}
        rootdoc = header('Pedaleira Digital MVP Rev. A', root_uid) + '(lib_symbols)(sheet_instances (path "/" (page "0")))'
        for sh in sorted(sheetids):
            su = sheetids[sh]
            title = layout['pages'][str(sh)]
            sx = 30 + ((sh - 1) % 3) * 80
            sy = 35 + ((sh - 1) // 3) * 45
            rootdoc += (
                f'(sheet (at {sx} {sy}) (size 65 25) (stroke (width 0.1524) (type solid)) '
                f'(fill (color 0 0 0 0)) (uuid {q(su)}) '
                + prop('Sheetname', title, sx, sy - 2) + prop('Sheetfile', f'folha_{sh}.kicad_sch', sx, sy + 28)
                + f'(instances (project {q(project)} (path {q("/" + root_uid)} (page {q(sh)})))))'
            )
            doc = header(title, uid())
            doc += render_sheet_body(byref, layout, libs, sh, ox, oy, flg_pts, uid, project, f'/{root_uid}/{su}', unified=False)
            (out_dir / f'folha_{sh}.kicad_sch').write_text(doc + ')')
        (out_dir / f'{project}.kicad_sch').write_text(rootdoc + ')')

    (out_dir / f'{project}.kicad_pro').write_text(json.dumps({
        'meta': {'filename': project + '.kicad_pro', 'version': 1},
        'erc': {'erc_exclusions': [], 'rule_severities': {k: 'warning' for k in ['single_global_label', 'four_way_junction', 'simulation_model_issue', 'footprint_filter']}},
    }, indent=2))
    (out_dir / 'mvp_revA.kicad_sym').write_text(
        '(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor")'
        + ''.join(v.replace(q('mvpA:' + r), q(r), 1) for r, v in libs.items()) + ')'
    )
    (out_dir / 'sym-lib-table').write_text(
        '(sym_lib_table\n  (lib (name "mvpA") (type "KiCad") (uri "${KIPRJMOD}/mvp_revA.kicad_sym") (options "") (descr "MVP Rev. A"))\n)\n'
    )


if __name__ == '__main__':
    model_path = OUT / 'circuito_mvp_revA.json'
    export_project(
        model_path, OUT / 'diagram_layout_folhas.json',
        OUT / 'kicad', 'pedaleira_mvp_revA', 'A4',
        19.05, 12.7, [(325, 135), (155, 185), (775, 260)], unified=False,
    )
    export_project(
        model_path, OUT / 'diagram_layout_unificada.json',
        OUT / 'kicad_unificada', 'esquematica_mvp_unificada', 'A1',
        25.4, 19.05, [(350, 160), (180, 210), (800, 285)], unified=True,
    )
    print('KiCad export OK: multi-sheet A4 + unified single-sheet A1')
