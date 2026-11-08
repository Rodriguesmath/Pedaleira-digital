# Pedaleira Digital — revisão 4.9

Autoria: **Rodrigues M. Lima**, 2026-11-07.

**NÃO APROVADO — REQUER CORREÇÕES.** Entrega de engenharia para revisão e qualificação de subconjuntos, sem liberação da pedaleira completa. Não houve teste físico. Não instalar o CS4272 antes de aprovar as alimentações; não remover o gate de áudio sem implementar o transporte.

A proposta usa fonte única **12 V DC regulados ±5%, ≥1,5 A**, sem trilho negativo e sem CI novo. 9 V foi rejeitado por margem de entrada insuficiente no TL072 clássico. O CW7805 alimenta um barramento comum de +5V com ramais físicos separados; requer identificação e dissipador ≤2 °C/W. A WeAct mantém seu conversor/indutor onboard: não foi acrescentado indutor à perfboard, mas a proibição literal de todos os indutores não é satisfeita pela placa pronta.

## Arquivos

- `pedaleira_digital_rev4_9.pdf`: sete folhas vetoriais A4, autoria e estado técnico na legenda. F1 fontes/bias; F2 entrada e condicionamento completo; F3 codec; F4 DAC/saída; F5 digital; F6 controles; F7 desacoplamento.
- `kicad/pedaleira_digital_rev4_9.kicad_pro` e `.kicad_sch`: CAD nativo KiCad 10, biblioteca local e sete folhas conectadas. Abrir o projeto, não importar como imagem. Não há PCB nem footprints definidos para fabricação.
- `circuito_rev4_9.json`: modelo elétrico canônico, 106 itens físicos, incluindo módulos e 11 pontos de teste. Quatro CIs na perfboard: dois TL072, CS4272 e CW7805; dois módulos prontos.
- `BOM_rev4_9.csv`: itens elétricos e especificações mínimas. `BOM_COMPLEMENTAR_REV49.csv`: fonte, dissipador, soquetes e materiais de montagem. Só os ativos informados pelo usuário estão marcados como disponíveis; passivos têm estoque a conferir.
- `CONEXOES_REV49.md` e `CONEXOES_COMPLETAS_REV49.csv`: tabelas de módulos, alimentação, CIs, jacks e todos os 265 terminais.
- `AUDITORIA_REV49.md`, `CALCULOS_REV49.json`: análise, limites, fontes, hipóteses, riscos e motivos do veredito.
- `TESTES_BANCADA_REV49.md`, `MONTAGEM_PERFBOARD_REV49.md`: sequência segura de qualificação e organização manual da placa.
- `VALIDACAO_REV49.json`, `VALIDACAO_LAYOUT.json`, `kicad/ERC_rev4_9.json`, `kicad/netlist.xml`: verificações automatizadas. ERC sem erros/avisos e sem exclusões; não equivale a validação funcional.
- `simulacao/`: netlists, mapas de nós, modelos, logs, gráficos e resultados OP/AC/transientes. Modelo TI antigo exploratório a 12 V; partida/desligamento usa modelo distinto e explicitamente limitado. As fontes e diodos não são dispositivos completos qualificados.
- `firmware_qa.log`: 9 testes existentes. `dsp_host_qa.log`: teste de execução DSP no host; não é benchmark do STM32.
- `firmware_rev49.patch` e `firmware_corrigido/`: quatro arquivos alterados, com correções AF/registradores/mute/reset. O gate continua em zero porque não existe transporte SAI/BDMA nem firmware ESP32.
- `fontes/`: referências primárias e PDFs disponíveis. CW7805 real ainda sem fabricante confirmado.
- `fontes_editaveis/`: cópia dos geradores, modelo e teste DSP. Fontes de trabalho no repositório: `docs/hardware/rev4_9/`.
- `backup/`: revisão 4.8 e firmware anteriores em ZIP, com hashes recuperáveis.
- `MANIFEST_SHA256.json`: integridade dos arquivos entregues, exceto o próprio manifesto.

## Reprodução

Dependências: Python com reportlab, pypdf, numpy e matplotlib; Times New Roman e Liberation Sans nos caminhos configurados; ngspice; KiCad 10. O teste DSP usa compilador C++17 nativo (não o `g++` ARM do PATH). O ambiente foi suprido com ferramentas extraídas localmente, sem alterar bibliotecas do sistema.

A partir do repositório, usando o Python que tem as dependências:

```sh
python docs/hardware/rev4_9/build_rev4_9.py
python docs/hardware/rev4_9/export_connected_kicad.py
kicad-cli sch erc --format json --exit-code-violations -o output/rev4_9/kicad/ERC_rev4_9.json output/rev4_9/kicad/pedaleira_digital_rev4_9.kicad_sch
kicad-cli sch export netlist --format kicadxml -o output/rev4_9/kicad/netlist.xml output/rev4_9/kicad/pedaleira_digital_rev4_9.kicad_sch
python docs/hardware/rev4_9/validate_layout.py
python docs/hardware/rev4_9/simulate_rev4_9.py
python docs/hardware/rev4_9/write_reports.py
python3 -m unittest tests/test_stm32_cpp_dsp_quality.py -v
python docs/hardware/rev4_9/validate_rev4_9.py
```

O teste DSP em `test_dsp_host.cpp` liga DspEngine/DspCrossfade/DspDelay/DspOverdrive/DspEqualizer/DspSvf com `Core/Inc`, C++17, e executa no PC. Os logs de QA são parte da evidência e devem ser renovados ao reproduzir. `PEDALEIRA_REV49_OUT` permite apontar a saída dos scripts a outra pasta; fora do repositório, a validação de mudanças no firmware depende de restaurar a árvore correspondente. `prepare_model.py` é a transformação histórica a partir da 4.8, não é necessário para editar/regerar o modelo 4.9 já entregue.

## O que falta

Identificar/qualificar CW e TL072; comprovar carga/temperatura, interface ADC com 1,5 kΩ/clamps e sequenciamento; resolver pop de saída para uso sem mute externo; implementar SAI4/PLL3/BDMA/SRAM4/cache/erros; implementar ESP e alinhar payloads UART. Plano e critérios completos nos documentos. **Nenhuma aprovação experimental ou funcionamento de áudio foi alegado.**
