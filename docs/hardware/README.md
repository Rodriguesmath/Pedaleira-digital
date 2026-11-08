# Documentação de hardware - rev.4.8

Autoria: Rodrigues M. Lima. **Veredito condicionado: circuito revisado, sem liberação para fabricação/montagem definitiva.**

O CS4272 disponível é o CI TSSOP-28 em adaptador passivo, sem componentes auxiliares. A rev.4.8 representa todos os pinos e componentes externos, usa dois TL072 DIP-8 e acrescenta alimentação negativa/VA regulado. Não é um breakout completo.

- [Esquemática PDF rev.4.8](../../output/rev4_8/pedaleira_digital_rev4_8.pdf)
- [Projeto KiCad editável](../../output/rev4_8/kicad/pedaleira_digital_rev4_8.kicad_pro)
- [BOM rev.4.8](../../output/rev4_8/BOM_rev4_8.csv)
- [Auditoria e datasheets](../../output/rev4_8/AUDITORIA_ELETRICA.md)
- [Checklist de montagem](../../output/rev4_8/CHECKLIST_MONTAGEM.md)
- [Alterações](../../output/rev4_8/CHANGELOG_rev4_8.md)
- [Pinout atual](pinout_e_bom.md)
- [Fonte física JSON](rev4_8/circuito_rev4_8.json) e [gerador](rev4_8/build_rev4_8.py)

KiCad: 0 violações no ERC da entrega; conectividade comparada pino a pino com o modelo. A simulação ngspice é linear, não valida saturação/ruído/partida nem substitui ensaio. Permanecem cinco bloqueadores de firmware, documentados sem alterar seu código: AF, prazo de reset, ATAPI, formato ADC e SAI/clocks/DMA.

## Reprodução

Com Python e reportlab: `python docs/hardware/rev4_8/build_rev4_8.py`. Com KiCad 10: executar `export_kicad.py` e depois ERC/export de netlist, conforme README da entrega. A fonte elétrica canônica é o JSON, não os scripts anteriores. Não há projeto de PCB ou liberação de footprints para fabricação.

## Legado preservado

`tools/gen_schematic.py`, `pedaleira_digital_easyeda.json`, `schematic_preview.png`, `bom_auto.*`, o guia EasyEDA e `tools/export_schematic_pdf.py` correspondem à revisão anterior. **Não os usar para montar o CI em adaptador passivo**: omitem auxiliares e têm premissas antigas. Os originais anteriores às mudanças documentais estão em `output/rev4_8/backup_rev4_7`, com SHA-256. O PDF estável antigo em `output/pdf` continua sendo rev.4.7, para evitar sobrescrever o original.
