#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
cd "$ROOT"
PY=${PEDALEIRA_PYTHON:-/home/rodrigues/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}
KICAD=${PEDALEIRA_KICAD:-/home/rodrigues/.cache/pedaleira-tools/root/usr/bin/kicad-cli}
LIB=${PEDALEIRA_TOOL_LIB:-/home/rodrigues/.cache/pedaleira-tools/root/usr/lib64}
export LD_LIBRARY_PATH="$LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

SRC=docs/hardware/mvp_revA
OUT=output/MVP_REVA
mkdir -p "$OUT/VALIDACAO"

"$PY" "$SRC/prepare_mvp_model.py"
"$PY" "$SRC/build_mvp.py"
"$PY" "$SRC/export_mvp_kicad.py"

"$KICAD" sch erc --format json --severity-all --exit-code-violations \
  -o "$OUT/VALIDACAO/ERC_folhas.json" "$OUT/kicad/pedaleira_mvp_revA.kicad_sch" \
  > "$OUT/VALIDACAO/ERC_folhas.log" 2>&1

"$KICAD" sch erc --format json --severity-all --exit-code-violations \
  -o "$OUT/VALIDACAO/ERC_unificada.json" "$OUT/kicad_unificada/esquematica_mvp_unificada.kicad_sch" \
  > "$OUT/VALIDACAO/ERC_unificada.log" 2>&1

"$KICAD" sch export netlist --format kicadxml \
  -o "$OUT/kicad/netlist_folhas.xml" "$OUT/kicad/pedaleira_mvp_revA.kicad_sch" \
  > "$OUT/VALIDACAO/netlist_folhas.log" 2>&1

"$KICAD" sch export netlist --format kicadxml \
  -o "$OUT/kicad_unificada/netlist_unificada.xml" "$OUT/kicad_unificada/esquematica_mvp_unificada.kicad_sch" \
  > "$OUT/VALIDACAO/netlist_unificada.log" 2>&1

pdftoppm -png -r 130 "$OUT/pedaleira_mvp_revA_unificada.pdf" "$OUT/pedaleira_mvp_revA_unificada"
pdftoppm -png -r 130 "$OUT/pedaleira_mvp_revA_folhas.pdf" "$OUT/folha_page"

"$PY" - <<'PY'
import csv, json, xml.etree.ElementTree as ET
from pathlib import Path

out = Path('output/MVP_REVA')
for name in ('VALIDACAO/ERC_folhas.json', 'VALIDACAO/ERC_unificada.json'):
    j = json.loads((out / name).read_text())
    viols = [v for s in j['sheets'] for v in s['violations']]
    assert not j['ignored_checks'], name
    assert not viols, (name, viols)

model = json.loads((out / 'circuito_mvp_revA.json').read_text())
expected_sch = {c['ref'] for c in model['components']}
bom_rows = list(csv.DictReader((out / 'BOM_mvp_revA.csv').open(encoding='utf-8-sig')))
assert len(bom_rows) == 91, len(bom_rows)
for xml_name in ('kicad/netlist_folhas.xml', 'kicad_unificada/netlist_unificada.xml'):
    root = ET.parse(out / xml_name).getroot()
    xml_comps = {el.attrib['ref'] for el in root.findall('.//comp')}
    assert xml_comps == expected_sch, (xml_name, xml_comps ^ expected_sch)
    # Partition check: net pin-sets match JSON model
    xml_nets = {}
    xml_ncs = set()
    for net in root.findall('.//net'):
        pins = frozenset((n.attrib['ref'], n.attrib['pin']) for n in net.findall('node'))
        if not pins:
            continue
        if net.attrib['name'].startswith('unconnected-'):
            assert len(pins) == 1
            xml_ncs |= pins
        else:
            xml_nets[net.attrib['name']] = pins
    model_nets = {}
    model_ncs = set()
    for c in model['components']:
        for p, n in c['pins'].items():
            if n is not None:
                model_nets.setdefault(n, set()).add((c['ref'], p))
            else:
                model_ncs.add((c['ref'], p))
    assert set(frozenset(v) for v in model_nets.values()) == set(xml_nets.values()), xml_name
    assert xml_ncs == model_ncs, (xml_name, xml_ncs ^ model_ncs)

print('MVP_REVA VALIDATION PASS: 91 BOM parts, 0 ERC violations (folhas + unificada), 100% netlist pin-partition match!')
PY
