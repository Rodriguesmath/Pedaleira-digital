# Candidato 4.10A

Estado: **BLOCKED para o conjunto**. A separação das fontes e a correção UART foram implementadas e verificadas; a revisão 4.10 ainda não está aprovada. A fase B não foi iniciada, conforme o gate exigido pela missão.

Executar na raiz do repositório:

```sh
sh docs/hardware/rev4_10/run_A.sh
```

O comando recompõe modelo, PDF de oito folhas, BOM, layout, KiCad e XML; executa 11 testes de alimentação, 12 de UART e 12 de CAD independente, além do ERC completo. Os logs permanecem em `output/REV410_ENTREGA/VALIDACAO_A`. Êxito desses testes significa consistência das evidências específicas, não aprovação elétrica do conjunto.

Dependências: Python com ReportLab e fontes Times/Liberation Sans nos caminhos definidos em `build_rev4_10.py`; KiCad 10.0.8. Python e KiCad podem ser selecionados por `PEDALEIRA_PYTHON`, `PEDALEIRA_KICAD` e `PEDALEIRA_TOOL_LIB`. O verificador independente usa por padrão o cache local registrado em seu código. Poppler é usado apenas para inspeção visual.

Ferramentas extraídas sem instalação global em `/home/rodrigues/.cache/pedaleira-tools/root`. RPMs Fedora 44, download registrado em `VALIDACAO_A/download_ferramentas.log` e `download_wx.log`. ngspice 47 está disponível nesse diretório, mas nenhuma nova simulação SPICE da correção ADC/mute foi executada. O aviso sobre schema API ausente no prefixo global do KiCad permanece nos logs; leitura, exportação e ERC efetivos terminaram com sucesso. Nenhum warning elétrico foi excluído.

Fontes locais da auditoria 4.9 são dependências preservadas do repositório. O pacote desta etapa inclui scripts e projeto editável, mas sua reprodução completa deve ser feita neste checkout, com as fontes originais 4.9 e a errata. O footprint SOIC-8 de U6 é da biblioteca oficial KiCad e está incluído com tabela local e proveniência. Os demais footprints aguardam a fase C, sem confundir notas de encapsulamento com footprints verificados.

O CW7805 permanece genérico por decisão do usuário; nenhuma especificação ST foi atribuída a ele. J5 aberto não isola as entradas analógicas ou a alimentação digital do codec. O perfil inicial de ensaio também exige **codec fisicamente ausente**, sinais externos desconectados e apenas os subconjuntos autorizados pelo roteiro. Não se realizou esse ensaio físico nesta missão.

O ganho DAC 0,499, U1A/U3A seguidores, U3B inversor, referências, filtros e todos os valores originais foram preservados. Firmware e originais 4.9 não são modificados pelo comando. Ler o relatório, a matriz de riscos e o parecer independente antes de qualquer montagem ou retomada.
