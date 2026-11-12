# Alterações efetivas 4.9 -> candidato 4.10A

- Originais4.9 preservados; hashes em BASE_REV49_SHA256.txt. Base na errata documental da auditoria.
- Headers STM5V e ESPVIN agora NC externos; cada placa alimentada pela própria USB.
- Renomeadas +5V para redes explícitas +5V_CW/+5VA e +3V3 para +3V3_STM; adicionado +3V3_ESP independente.
- VD/VL exclusivamente3V3_STM. Nenhum regulador extra ou XL6019 adicionado.
- J4 convertido em acesso de carga artificial CW; não alimenta placas.
- J5 normalmente aberto entre CW e VA; não protege automaticamente falhas nem entradas analógicas.
- UART direta substituída por U6 ISO7721DR dual-supply, C42/C43 de100nF, R29/R30 de10k e R31/R32 de47k locais. Oito componentes adicionais incluindo J5; disponibilidade não presumida.
- Ganhos, filtros e estágios analógicos preservados; nenhum valor original foi alterado. MetadadosR15/R16,C5,C30/C32 corrigidos.
- Folha8 para UART e bypass, mantendo fontes, cores, moldura e legenda anteriores. AutoriaRodrigues M. Lima, data2026-11-12, statusEm revisão-faseA.
- Projeto editável e footprint oficialSOIC8 de U6 incluídos, sem exclusões ERC. Não é entrega de PCB completa.
- Firmware preservado. ProteçãoADC e mute físico aguardam PASS A; nenhuma correção B foi simulada ou declarada pronta.
