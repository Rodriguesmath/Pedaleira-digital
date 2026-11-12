#!/bin/sh
# Rebuild and verify Phase 4.10B candidate (Blockers 3 + 4 on top of Phase A).
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
cd "$task_root"
task_python=${PEDALEIRA_PYTHON:-/home/rodrigues/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}
task_kicad=${PEDALEIRA_KICAD:-/home/rodrigues/.cache/pedaleira-tools/root/usr/bin/kicad-cli}
task_lib=${PEDALEIRA_TOOL_LIB:-/home/rodrigues/.cache/pedaleira-tools/root/usr/lib64}
export LD_LIBRARY_PATH="$task_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
task_src=docs/hardware/rev4_10
task_out=output/REV410_ENTREGA
mkdir -p "$task_out/VALIDACAO_B" "$task_out/SIMULACOES_B"

"$task_python" "$task_src/prepare_model.py"
"$task_python" "$task_src/build_rev4_10.py"
"$task_python" "$task_src/validate_layout.py"
"$task_python" "$task_src/export_connected_kicad.py"
"$task_python" "$task_src/validar_alimentacao.py" > "$task_out/VALIDACAO_B/alimentacao_execucao.log"
"$task_python" "$task_src/test_interfaces_indep.py" > "$task_out/VALIDACAO_B/UART_execucao.log" 2>&1
"$task_python" "$task_src/simular_A.py" > "$task_out/SIMULACOES_A/simular_A_execucao.log" 2>&1
"$task_python" "$task_src/simular_B.py" > "$task_out/SIMULACOES_B/simular_B_execucao.log" 2>&1
"$task_kicad" sch erc --format json --severity-all --exit-code-violations -o "$task_out/kicad/ERC_rev4_10.json" "$task_out/kicad/pedaleira_digital_rev4_10.kicad_sch" > "$task_out/VALIDACAO_B/ERC_execucao.log" 2>&1
"$task_kicad" sch export netlist --format kicadxml -o "$task_out/kicad/netlist.xml" "$task_out/kicad/pedaleira_digital_rev4_10.kicad_sch" > "$task_out/VALIDACAO_B/netlist_execucao.log" 2>&1
"$task_python" "$task_src/auditar_cad_B.py" --export > "$task_out/VALIDACAO_B/CAD_independente_execucao.log" 2>&1
sha256sum -c "$task_out/BASE_REV49_SHA256.txt" > "$task_out/VALIDACAO_B/base_rev49_check.log"

"$task_python" - <<'PY'
import json
from pathlib import Path
p = Path('output/REV410_ENTREGA')
j = json.loads((p / 'kicad/ERC_rev4_10.json').read_text())
sa = json.loads((p / 'SIMULACOES_A/resumo_A.json').read_text())
sb = json.loads((p / 'SIMULACOES_B/resumo_B.json').read_text())
c = json.loads((p / 'VALIDACAO_A/calculos.json').read_text())
v = json.loads((p / 'VALIDACAO_LAYOUT.json').read_text())
assert not j['ignored_checks']
assert not [viol for sh in j['sheets'] for viol in sh['violations']]
assert v['visible_routes_and_ports_equal_model'] and v['cross_net_intersections'] == 0
assert sa['global_verdict']['verdict'] == 'PASS', sa
assert sb['global_verdict']['verdict'] == 'PASS', sb
assert c['gate_A_design'] == 'PASS' and c['gate_B_design'] == 'PASS', c
print(
    f"Executed: {c['test_count']} power tests + 12 UART tests + "
    f"{sa['global_verdict']['scenarios_passed']}/{sa['global_verdict']['total_scenarios']} SPICE A + "
    f"{sb['global_verdict']['scenarios_passed']}/{sb['global_verdict']['total_scenarios']} SPICE B + "
    f"13 independent CAD tests; ERC 0 violations; layout {v['all_physical_pins']} pins / {v['visible_connected_nets']} nets."
)
print("Gate B (Design & SPICE): checks PASS (bench prerequisites + Phase C footprints remain pending before energization).")
PY