#!/bin/sh
# Rebuild and verify the candidate. Successful checks do not mean gate A PASS.
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
cd "$task_root"
task_python=${PEDALEIRA_PYTHON:-/home/rodrigues/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}
task_kicad=${PEDALEIRA_KICAD:-/home/rodrigues/.cache/pedaleira-tools/root/usr/bin/kicad-cli}
task_lib=${PEDALEIRA_TOOL_LIB:-/home/rodrigues/.cache/pedaleira-tools/root/usr/lib64}
export LD_LIBRARY_PATH="$task_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
task_src=docs/hardware/rev4_10
task_out=output/REV410_ENTREGA
mkdir -p "$task_out/VALIDACAO_A" "$task_out/SIMULACOES_A"
"$task_python" "$task_src/prepare_model.py"
"$task_python" "$task_src/build_rev4_10.py"
"$task_python" "$task_src/validate_layout.py"
"$task_python" "$task_src/export_connected_kicad.py"
"$task_python" "$task_src/validar_alimentacao.py" > "$task_out/VALIDACAO_A/resumo_execucao.log"
"$task_python" "$task_src/test_interfaces_indep.py" > "$task_out/VALIDACAO_A/UART_execucao.log" 2>&1
"$task_python" "$task_src/simular_A.py" > "$task_out/SIMULACOES_A/simular_A_execucao.log" 2>&1
"$task_kicad" sch erc --format json --severity-all --exit-code-violations -o "$task_out/kicad/ERC_rev4_10.json" "$task_out/kicad/pedaleira_digital_rev4_10.kicad_sch" > "$task_out/VALIDACAO_A/ERC_execucao.log" 2>&1
"$task_kicad" sch export netlist --format kicadxml -o "$task_out/kicad/netlist.xml" "$task_out/kicad/pedaleira_digital_rev4_10.kicad_sch" > "$task_out/VALIDACAO_A/netlist_execucao.log" 2>&1
"$task_python" "$task_src/auditar_cad_A.py" --export > "$task_out/VALIDACAO_A/CAD_independente_execucao.log" 2>&1
"$task_python" "$task_src/write_checkpoint_A.py"
"$task_python" - <<'PY'
import json
from pathlib import Path
p=Path('output/REV410_ENTREGA')
j=json.loads((p/'kicad/ERC_rev4_10.json').read_text())
s=json.loads((p/'SIMULACOES_A/resumo_A.json').read_text())
c=json.loads((p/'VALIDACAO_A/calculos.json').read_text())
assert not j['ignored_checks']
assert not [v for sh in j['sheets'] for v in sh['violations']]
assert s['global_verdict']['verdict']=='PASS', s
assert c['gate_A_design']=='PASS', c
print(f"Executed: {c['test_count']} power tests + 12 UART tests + {s['global_verdict']['scenarios_passed']}/{s['global_verdict']['total_scenarios']} SPICE A + 11 independent CAD tests; ERC 0 violations.")
print("Gate A (Design & SPICE): PASS -> Phase B authorized. Physical bench prerequisites (CW/WeAct/ESP32) remain conditioned before energization.")
PY
