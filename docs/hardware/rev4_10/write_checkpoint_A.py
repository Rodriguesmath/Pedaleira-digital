#!/usr/bin/env python3
"""Publish actual 4.10A candidate results; do not manufacture B/C artifacts."""
from pathlib import Path
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
O=ROOT/'output/REV410_ENTREGA'
model=json.loads((O/'circuito_rev4_10.json').read_text())
calc=json.loads((O/'VALIDACAO_A/calculos.json').read_text())
states=json.loads((O/'VALIDACAO_A/estados.json').read_text())
parts={a['ref']:a for a in model['components']}

with (O/'CONEXOES_COMPLETAS_REV410.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Referência','Pino','Nome','Rede','Folha','Tipo','Observação'])
    for a in model['components']:
        for p,n in a['pins'].items():
            w.writerow([a['ref'],p,a['names'].get(p,p),n or 'NC',a['sheet'],a['types'].get(p,'passive'),
                        'PINAGEM CW NÃO QUALIFICADA' if a['ref']=='U5' else ''])

matrix='''# Matriz de alimentação - candidato 4.10A

2026-11-12. S = USB STM; E = USB ESP; A = 12 V. Análise estrutural/combinatória, não simulação de rampas ou medição. `estados.json` conserva a análise do conjunto com J5 fechado para identificar riscos; essa configuração NÃO está liberada. Perfil inicial: J5 aberto, codec removido fisicamente, guitarra e amplificador desconectados, sem outros adaptadores acionando GPIO. J5 sozinho não isola o codec dos drivers RAW ou dos sinais digitais.

|S E A|Trilhos comandados|UART RX STM / RX ESP|Reset/mute e restrições|
|---|---|---|---|
'''
for s in states:
    rails=', '.join(k for k,v in s['rails'].items() if v) or 'Nenhum; capacitores podem reter carga'
    matrix+=f"|{s['id']}|{rails}|{s['uart_rx_stm']} / {s['uart_rx_esp']}|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|\n"
matrix+='''
`VA_CW_5V` na tabela é a saída nominal do estágio CW. Com J5 aberto não há alimentação intencional de +5VA pelo CW. Não se presume ausência de carga residual no lado VA. VD/VL pertencem ao mesmo 3V3 do STM. /RST tem pull-down R13; não há intertravamento automático contra perda de VA quando PD10 estiver HIGH. Firmware entregue mantém transporte de áudio bloqueado; essa condição não substitui a proteção elétrica.

Foram enumeradas as 24 transições dirigidas de mudança de uma fonte e as seis ordens de chegada a111 em `VALIDACAO_A/transicoes.json` e `calculos.json`. Desligamentos são os caminhos inversos dessas ordens. Nenhuma transição do conjunto está declarada fisicamente segura. Cortes/retornos de VA podem manter carga em C2/C16/C40; reset não desconecta AIN. O mute de saída continua pendente na fase B.

UART U6: sinais e alimentação de cada lado pertencem à própria placa. O cruzamento de dados ocorre por barreira capacitiva, sem ligação DC de sinal entre USBs. Durante brownout a lógica é indeterminada; o default HIGH só vale nas condições PU/PD do fabricante. RX desligado é indeterminado, não Hi-Z garantido. Nenhum positivo USB se liga ao CW ou ao positivo da outra USB.

GND é comum. Usar retornos digitais separados do retorno analógico até o ponto de referência; nunca VREF_OP como retorno. Duas USBs não dão isolamento galvânico ao sistema. A compatibilidade dos terras de hosts/fontes e instrumentos precisa ser verificada antes do futuro ensaio; não levantar terra de proteção.
'''
(O/'MATRIZ_ALIMENTACAO.md').write_text(matrix)

cw=f'''# CW7805 mantido - análise 4.10A

2026-11-12. Decisão do usuário: manter o genérico de três pinos retirado de outra placa; qualificação pendente. A origem em aparelho alimentado em AC não fornece fabricante, pinagem/TAB, tensão máxima, corrente, estabilidade ou limites térmicos. Saída nominal de 5 V é premissa funcional, não garantia de todos esses parâmetros. Nenhum dado do ST L7805 foi atribuído ao exemplar.

Implementado: placas retiradas da saída CW; U5 fornece +5V_CW, com C22/C37/R21 e D8 preservados. J4 dá acesso somente à carga artificial. J5 fica SEM shunt e separa +5V_CW de +5VA. R27/R28 e VA20 ficam depois de J5. STM e ESP usam USB próprias; VD/VL vêm de +3V3_STM. D8 descarrega saída CW para RAW e não arbitra fontes.

A pinagem numérica 1=IN,2=GND/TAB,3=OUT herdada do desenho é HIPÓTESE NÃO QUALIFICADA, identificada na BOM e conexões. Não é instrução liberada de montagem do exemplar desconhecido. Antes de energizar, os terminais precisam ser determinados por evidência técnica. J5 aberto não torna segura uma ligação errada do próprio CW.

## Cálculos reproduzíveis

Executar `python3 docs/hardware/rev4_10/validar_alimentacao.py`.

- VA: IA típico45mA/máximo53mA sob condições Cirrus DS593F2 p17.
- R21 máximo: 5,25/(910x0,99)=5,8275mA; divisor ADC máximo0,21021mA.
- Orçamento CW do conjunto: **{calc['CW_current_max_budget_A']*1000:.4f}mA**; típico aproximado50,6945mA. Não inclui corrente de partida ou injeção dos clamps como se fossem conhecidas.
- RAW assumido10,5..12,6V: 12V±5%, queda D1 máxima adotada0,9V; não se impõe queda mínima garantida.
- Iq8mA é PROXY comparativo de família, não especificação CW. Dissipação conservadora calculada **{calc['CW_power_conservative_proxy_W']:.6f}W**; máximo de cantos consistentes **{calc['CW_power_corner_proxy_max_W']:.6f}W**.
- Com thetaJA hipotético50°C/W e ambiente40°C, Tj proxy{calc['CW_Tj_proxy_thetaJA50_ambient40_C']:.2f}°C. Não é temperatura medida/garantida nem qualificação sem dissipador.
- A revisão4.9 orçava aproximadamente0,909A e7,236W. Essa redução elimina a justificativa automática do antigo dissipador<=2°C/W; a seleção térmica real permanece pendente.
- C37=1000uF armazena13,8mJ a5,25V; compatibilidade de capacitância/ESR, inrush e estabilidade não foram simuladas nem medidas. C21=330nF e C22=100nF preservados.

Com J5 aberto, ADC_BIAS/VA não são carga intencional do CW. Para futuro ensaio isolado, carga externa100ohm±1%/1W em J4 representa até53,03mA a5,25V, além do bleederR21; é equipamento de ensaio a providenciar, não novo componente do circuito. Codec retirado e sinais externos desconectados. Não executar ensaio supondo pinagem desconhecida ou curto IN-OUT.

## Fundamentação e pendências

[Cirrus DS593F2](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf), p9/p17/p27: VA4,75..5,25V e correntes nas condições publicadas. [TI TL072 SLOS080W](https://www.ti.com/lit/ds/symlink/tl072.pdf), p11/p15: modo comum e caracterização em±15V; não usar TL072H como se fosse o clássico. [Vishay 1N5822](https://www.vishay.com/docs/88526/1n5820.pdf): Vf condicionado, não mínimo0,3V. PDFs preservados na auditoria4.9. [WeAct oficial](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723): 1A máximo total do buck, não 1A livre.

Pinagem/fabricante/estabilidade/SOA/térmica CW continuam não demonstrados. Variações da placa ESP e capacidade livre3V3 também não foram medidas. Esses itens não serão convertidos em resultados por decisão editorial. A qualificação pendente é uma escolha registrada do usuário; não foi substituído o regulador.
'''
(O/'ANALISE_CW7805.md').write_text(cw)

risks=[
('A410-01','ALTO','CW7805 genérico sem identidade/pinagem qualificada','Aberto por decisão do usuário','J5 aberto e codec removido nos ensaios iniciais; confirmar terminais antes de energizar'),
('A410-02','ALTO','UART direta entre USBs independentes','CORRIGIDO DOCUMENTALMENTE','U6 ISO7721DR, IO de cada lado no próprio domínio; aquisição/ensaio pendentes'),
('A410-03','ALTO','Perda VA com PD10 HIGH não força reset físico','ABERTO','Codec removido; intertravamento automático não implementado'),
('A410-04','ALTO','AIN pode exceder VA durante partida/queda; BAT85 sem prova de limite0,3V','ABERTO / fase B não iniciada','Codec removido; preservar achadoA02 sem fingir correção'),
('A410-05','MEDIO','Capacidade livre do3V3 WeAct não garantida pela indicação1 A total','ABERTO','Reservar28mA codec+4mA UART; orçamento completo e ensaio posteriores'),
('A410-06','ALTO','Saída sem mute físico durante partida/queda','ABERTO / fase B não iniciada','Jack externo desconectado; achadoA03 preservado'),
('A410-07','MEDIO','Variante ESP e GPIO16/17 não confirmados','ABERTO','Conferir móduloWROOM/headers e ausênciaPSRAM nessespinos'),
('A410-08','MEDIO','Footprints herdados ainda não verificados para todos os componentes','ABERTO / fase C não iniciada','Somente U6 foi associado a footprint oficial; não liberar PCB/montagem integral'),
]
with (O/'MATRIZ_RISCOS.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['ID','Severidade','Evidência/impacto','Estado','Correção/contenção']);w.writerows(risks)

(O/'CHANGELOG_REV49_REV410.md').write_text('''# Alterações efetivas 4.9 -> candidato 4.10A

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
''')

(O/'PENDENCIAS_BANCADA.md').write_text('''# Condições de futuros ensaios - não executados

GateA integralBLOCKED. Este roteiro prepara subconjuntos, não autoriza montar/energizar a pedaleira completa.

1. Conferir variante das placas, headers e compatibilidade de GND/fontes USB/instrumentos. Não usarVREF_OP como terra.
2. Manter J5 SEM shunt, codec REMOVIDO, guitarra/jack de saída e outros adaptadores de sinal desconectados. Confirmar continuidade e ausência de pontes de5V.
3. Identificar IN/GND/OUT/TAB do CW antes de qualquer alimentação; a ordem numérica no candidato é hipótese. Caracterizar a fonte isolada com carga artificial e limitação de corrente; não atribuir especificaçõesST nem executar curtoIN-OUT.
4. Somar consumo de toda a WeAct (sem acessórios opcionais),28 mA do codec e reserva de 4 mA do lado UART. Critério de projeto:3,2..3,4V no codec,VD>=3,1V e margem de corrente total a definir/medir.1 A total não é corrente livre.
5. Adquirir ISO7721DR genuíno (sem sufixo F), adaptador SOIC-8 / DIP-8 e passivos locais. Testar UART em oito estados e 24 transições, incluindo rampas lentas/cortes, sinalRX/capacitância/overshoot. Timing de datasheet usaCL = 15 pF; capacitância real/sonda deve ser incluída.
6. Não instalar codec nem fechar J5 para áudio enquanto alimentação, reset/partida, proteçãoADC e mute não tiverem gate correspondente. Proteção BAT85 e pop continuam achados críticos conhecidos.
7. Repetir futuramente os ensaios analógicos da auditoria4.9 com carga artificial >=100 kΩ, sinais limitados, mediçõesAIN/VA/VCOM/ADC_BIAS e mute físico definido. Não conectar amplificador/fones para observar transientes exploratórios.

Não há resultados físicos anexos. ngspice foi restaurado, mas não foi executada simulaçãoSPICE de uma correçãoB nesta fase. Nenhum resultado antigo foi reapresentado como teste da4.10.
''')

(O/'RELATORIO_REV410.md').write_text(f'''# Revisão 4.10 - checkpoint de trabalho A

2026-11-12. **Veredito: REPROVADO para o conjunto; CHECKPOINT A BLOCKED.** Candidato editável salvo; B e C não iniciadas. Não é aprovação para funcionamento completo nem aprovação documental integral para ensaios do conjunto.

## Alterações e evidências

Placas saíram da carga CW e usamUSB independentes; VD/VL pertencem a +3V3_STM. UART foi corrigida documentalmente com ISO7721DR; positivos permanecem separados. J5 aberto por padrão seccionaCW->VA, sem fingir que isola sinaisADC. Mantidos todos os valores originais e topologias de ganho.114 componentes, 288 terminais e 61 redes; oito folhas A4 paisagem e autoria Rodrigues M. Lima.

Foram executados11 testes de alimentação/candidato,12 cálculos independentesUART e validação gráfica de conectividade. Logs e resultados ficam emVALIDACAO_A eREVISOES. ERC/XML atuais e revisão independente devem ser consultados emkicad eREVISOES/CAD_A_INDEPENDENTE.md; não usar um log anterior como se cobrisse uma nova exportação. Passar ERC não resolve os bloqueios elétricos.

Orçamento CW calculado{calc['CW_current_max_budget_A']*1000:.4f}mA e dissipação proxy conservadora{calc['CW_power_conservative_proxy_W']:.6f}W, contra aproximadamente 0,909 A / 7,236 W na4.9. Nenhum parâmetro térmico de fabricante foi atribuído aoCW genérico. Não houve montagem, compra, medição ou simulação física doCW.

## Bloqueios e decisão de escopo

Usuário manteveCW genérico e qualificação pendente. Ainda faltam pinagem/limites rastreáveis ou qualificação externa; a proveniência de placaAC não demonstra esses dados. Também permanecem reset automático na perdaVA, proteçãoADC durante queda, mute físico e capacidade livre3V3. Condições de isolamento autorizam preparar ensaios de subconjuntos; não fecham o gate do conjunto.

A missão exige PASS A antes de B e PASS B antes de C. Não foram criados ANALISE_ADC.md/PROJETO_MUTE_FISICO.md com projetos fictícios, nem simulações para uma correção não realizada. Os achadosADC/mute da 4.9 continuam explícitos na matriz de riscos. O usuário pode retomar deste checkpoint após resolver o bloqueio de alimentação ou redefinir formalmente o escopo dos gates; não se marcou FAIL comoPASS.

## Componentes adicionais e custo

U6 ISO7721DR, adaptador SOIC-8 / DIP-8, dois capacitores de 100 nF, dois resistores de 10 kΩ, dois resistores de 47 kΩ e header/shunt J5. Aquisição/estoque/custo não confirmados; aumento de uma pequena submontagem de interface. Não foram inventados preços. CW, TL072 e codec e valores originais mantidos.

## Retomada

Ler CHECKPOINTS.md, MATRIZ_RISCOS.csv, REVISOES/CAD_A_INDEPENDENTE.md e scripts emdocs/hardware/rev4_10. Preservar firmware e originais4.9. A pasta contém trabalho parcial rastreável e candidato PDF claramente marcado Em revisão - fase A. Não tratar este checkpoint como entrega final 4.10 aprovada.
''')

foot=Path(__file__).with_name('Package_SO.pretty')/'SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod'
(O/'FONTES_FOOTPRINT.md').write_text('''# Footprint U6

Origem: https://raw.githubusercontent.com/KiCad/kicad-footprints/master/Package_SO.pretty/SOIC-8_3.9x4.9mm_P1.27mm.kicad_mod
Biblioteca oficial KiCad; licença CC-BY-SA 4.0 com exceção de bibliotecasKiCad, conforme https://www.kicad.org/libraries/license/ . Download2026-11-12. Arquivo preservado sem alterar pads; modelo 3D referenciado é opcional e não incluído. Não representa um adaptador DIP físico adquirido.

SHA256: '''+hashlib.sha256(foot.read_bytes()).hexdigest()+'\n')
print('Checkpoint A reports/connections written; BLOCKED remains explicit')
