# Revisão da proposta de alimentação — fase 4.10A

Data: 2026-11-12. Papel A, análise independente. **Nenhuma medição física executada; nenhum CAD ou firmware alterado por este parecer.** Foram relidos integralmente a missão, AUDITORIA_REV49.md, RESULTADO_AUDITORIA.json, errata e ANALISE_CW7805.md atual. O objetivo deste parecer é oferecer correções e contenções implementáveis, distinguindo o gate documental para preparar ensaios da liberação para instalar e energizar todos os componentes.

## 1. Correções objetivas que permitem avançar

1. Criar redes distintas `USB_STM_5V`, `USB_ESP_5V` e `+5VA_CODEC`. Nenhuma conexão entre os três positivos, nem por conector legado J4, fio de programação, diodo D8 ou porta de teste. D8 permanece entre a saída CW e RAW exclusivamente no domínio analógico.
2. VD9 e VL10 do codec devem vir juntos de `+3V3_STM`, buck da WeAct alimentado por sua própria USB. Pull-ups I2C e sinal de reset pertencem ao mesmo domínio. Isso evita criar, sem necessidade, uma quarta fonte e mantém o nível lógico do codec rastreando o STM32. Não alimentar VD/VL pela saída 3V3 do ESP.
3. Substituir UART direta entre placas por interface com proteção de desligamento parcial demonstrada ou, no ensaio inicial, remover fisicamente ambos os jumpers de TX/RX. Resistores série sozinhos não impedem alimentação reversa. Há opções exatas abaixo; o agente embarcado está aprofundando a opção open-drain.
4. Inserir seccionamento físico `SJ_VA`, **normalmente aberto e sem jumper na entrega de ensaio**, entre a saída CW e a rede de carga do codec. C21/C22/C37 e D8 ficam no lado do regulador, antes do seccionamento. Terminal de teste/carga artificial desse lado; VA, ADC_BIAS e clamps superiores no lado codec, conforme revisão de conectividade. Se ADC_BIAS ficar no lado de teste, também deve ser fisicamente desligado de qualquer pino codec durante esse ensaio. Não deixar caminho alternativo pelo divisor/clamp que contorne SJ_VA.
5. Para ensaio do CW desconhecido: CS4272 fisicamente removido, harness de sinais analógicos/digitais externos removido e amplificador externo desconectado. O seccionamento sozinho, com VD/VL ativos e codec instalado, NÃO transforma alimentação parcial em validação do regulador. A retirada física do codec elimina essa interpretação.
6. Gate A deve testar automaticamente a separação das três redes positivas, a origem única de VD/VL, a ausência de UART direta, a posição e o estado padrão aberto de SJ_VA, e a impossibilidade de contornar o seccionamento em modo de teste. Um PWR_FLAG não é evidência de fonte segura.

## 2. CS4272: sequenciamento que o documento realmente exige

Cirrus DS593F2, outubro/2021, página 9: VA normal 4,75–5,25 V; VD 3,1–5,25 V; VL 2,37–5,25 V. Cada alimentação possui absoluto próprio −0,3..6,0 V. A tabela não define um limite de diferença VA−VD/VL nem uma ordem relativa obrigatória entre esses trilhos. Portanto **não se deve classificar VA ligada/VD desligada, por si só, como violação demonstrada**.

Página 27, §5.2.1: manter /RST baixo até alimentações, MCLK e LRCK estabilizarem, depois configurar CPEN/PDN dentro da janela de 10 ms. Isso é a sequência de operação documentada. Não prova áudio válido em alimentação parcial, nem libera transientes nos pinos. Página 9 exige entradas digitais ≤VL+0,3 V e analógicas ≤VA+0,3 V, mesmo quando o respectivo trilho cai.

Com VD e VL derivados do STM, MCLK/LRCK/SCLK/SDIN/SCL/SDA/RST e o receptor SDOUT pertencem ao mesmo domínio lógico. Desligar a USB STM retira simultaneamente a fonte desses sinais e a alimentação VL, eliminando a fonte externa constante de 3V3 que existiria se VD/VL viessem de outra origem. Isso é correção de arquitetura; diferenças de tempo de descarga, capacitâncias e comportamento dos buffers ainda precisam de ensaio.

A falta de 12 V deixa TL072/VA sem operação normal; /RST deve permanecer baixo, sem tentativa de áudio. R13=10 kΩ para GND fornece estado passivo baixo quando o STM está ausente/alta impedância, mas não impede um STM vivo de subir reset com VA ausente. Para controle de ensaio, manter o gate de áudio existente bloqueado e não liberar reset manualmente. Para aprovação de operação autônoma sem alimentação analógica, seria necessário qualificar uma interdição independente de VA ou um supervisor escolhido; não foi inventada uma proteção já disponível.

O CI não especifica comportamento de todas as suas saídas em qualquer alimentação parcial. Se existir sinal indevido medido em SDOUT ou backpower, deve ser corrigido. Ausência de uma curva não é prova de que o CI destrói a placa; tampouco é aprovação de hot-plug. Ensaios iniciais usam codec removido. ADC/clamps e os tempos das referências ficam no gate B, após o gate A documental correspondente.

## 3. Orçamento de 3V3: o que se sabe e o que falta

O README oficial WeAct H723 informa DC-DC com **1 A máximo total**. O esquema V1.2 p2 documenta XT3410 e variantes de montagem; não é 1 A livre no header. Codec VD/VL a 3,3 V consome até 28 mA, conforme Cirrus p17. O incremento solicitado é pequeno, mas a carga total precisa ser conferida.

ST DS13313 Rev5, maio/2025, tabela21 p99, consumo Run com código/processamento em Flash, cache ligado e VOS0/550 MHz: a variante consultada apresenta até 430 mA a Tj105 °C com todos os periféricos habilitados, sob suas condições de teste; máximo a Tj25 °C 250 mA e típico 220 mA. Esse não é consumo máximo universal de uma placa inteira. Duas memórias, LCD/backlight, câmera, SD, LEDs, GPIO e regulação devem ser somados; acessórios opcionais devem ficar desligados/desconectados na qualificação inicial. **O orçamento antigo de 350 mA não constitui um máximo garantido de placa.**

A diferença aritmética 1 A−430 mA−28 mA=542 mA é apenas margem antes dos demais consumidores; não chamá-la de corrente livre garantida. Proposta de critério de ensaio: carga total 3V3 ≤0,8 A, tensão no codec 3,2–3,4 V e VD sempre ≥3,1 V, sem ripple/oscilações excessivos. O teto 0,8 A é reserva de projeto de 20%, não dado do fabricante. Essa medição é uma condição futura de instalação, não teste alegadamente executado.

Fonte/cabo USB devem suportar o consumo real da placa com margem e queda aceitável. “USB” sozinho não significa corrente ilimitada: uma porta host depende da configuração/negociação e proteção correspondente. Não conectar a saída do CW no header 5V para compensar USB fraca. ESP também fica com sua própria fonte USB compatível e retorno de corrente separado.

## 4. CW7805 desconhecido: delimitação que não inventa datasheet

Retirar STM/ESP reduz a carga CW calculada para cerca de **59,04 mA**, incluindo VA máximo 53 mA, bleeder e divisor de ADC_BIAS. No envelope conservador RAW máximo12,6 V e saída mínima4,75 V, com Iq proxy8 mA, a perda calculada é **0,564 W**. Não há mais fundamento para impor automaticamente dissipador≤2 °C/W. θJA proxy50 °C/W daria Tj≈68,2 °C a40 °C; nada disso identifica o CW.

É possível aprovar **documentalmente a preparação de um ensaio isolado** sem identificar previamente toda a peça: carga artificial, fonte limitada, nenhuma carga sensível e pontos de acesso claros. Isso não aprova pinagem presumida nem autoriza energização do exemplar sem inspeção/localização dos terminais. Uma marcação/logo completa pode permitir vincular fabricante/datasheet; até lá, a pinagem usual 7805 permanece hipótese explícita.

Procedimento delimitado: verificar exemplar isolado e sem cargas sensíveis; limitar inicialmente a fonte a20 mA; confirmar orientação/pinagem antes da primeira alimentação; primeiro avaliar com carga pequena apropriada, depois ensaio com cerca de60 mA e extremos de entrada. Capturar tensão, ripple, partida e descarga de C37. Interromper em oscilação, corrente incompatível, tensão fora de4,75–5,25 V ou aquecimento anormal. Sem datasheet real não declarar proteção térmica/SOA/θJC garantida, nem usar a peça como proteção de falha do codec.

**SJ_VA fica aberto e o codec removido até essa qualificação.** A restrição deve aparecer no PDF, BOM, conexões e plano, e ser verificada por testes. Um simples texto sem seccionamento implementado não contém o risco. O teste físico futuro pode reprovar a peça; não alegar que uma medição pontual cria especificações garantidas de fabricação.

Se se exige energização integral sem essa condição, a informação externa indispensável é identidade/pinagem/datasheet confiável do CW, ou seleção/aquisição explícita de regulador identificado compatível. A missão não confirma disponibilidade de outro regulador; nenhuma substituição foi efetuada.

## 5. UART: alternativas exatas e limitações

### Opção preferida para montagem acessível: open-drain com Ioff

A equipe embarcada avalia dois SN74LVC1G07, um por sentido, alimentados pelo **domínio transmissor**, com saída open-drain e pull-up no **domínio receptor**. O interesse dessa topologia é não fornecer nível alto para uma placa desligada; quando o transmissor perde alimentação, Ioff limita o caminho reverso para ele. Usar o componente exato, bypass local e bleed nos trilhos conforme cálculo independente. Não trocar por transistor bipolar genérico ou 74HC sem comprovar desligamento parcial. A escolha final depende do parecer do agente embarcado e datasheet exato; este parecer não altera sua BOM.

### Alternativa comprovadamente específica: SN74AXC2T245RSWR

TI SCES879A, fevereiro/2024: dois canais com direções independentes, alimentação dual0,65–3,6 V, Ioff e isolamento quando qualquer alimentação<100 mV; §8.3 p23 trata sequenciamento de fontes sem exigência de ordem/rampa. Esse recurso é mais completo que um buffer push-pull alimentado apenas de um lado. Um SN74AXC2T45 comum possui DIR compartilhado e não serve sozinho para dois sentidos simultâneos de UART.

Conexão candidata do AXC2T245: VCCA7=3V3_STM, VCCB6=3V3_ESP, GND3=GND; A1/8 recebe TX_STM, B1/5 entrega RX_ESP, DIR1/10=VCCA; B2/4 recebe TX_ESP, A2/9 entrega RX_STM, DIR2/1=GND. /OE2 tem pull-up aVCCA e habilitação local com estado definido; não deixar flutuante. Bypass100 nF em cada VCC. Pull-ups e bleeders locais devem ser dimensionados para a fuga máxima indicada no datasheet e para entrada inativa definida. Não unir as alimentações nos capacitores.

Limitação prática: encapsulamento UQFN10 de1,8×1,4 mm, exigindo adaptador/PCB apropriado; pouco adequado a perfboard direta. O produto oficial existe, mas não foi verificado estoque local, comprado nem declarado disponível. A opção1G07 em adaptador SOT23 é mais simples se confirmar todos os limites. O AXC é alternativa documentada caso a solução open-drain não satisfaça as transições.

### Alternativas rejeitadas sem evidência suficiente

- Somente resistor série: limita corrente, não garante tensão do trilho desligado nem ausência de backpower.
- Um único SN74LVC2G125 com uma alimentação para ambos os sentidos: um de seus outputs continuaria no domínio errado quando o receptor perde energia.
- Dois buffers1G125 alimentados pelos receptores: Ioff emVCC0 ajuda, mas brownout e habilitação /OE requerem controle explícito; é menos direto que open-drain com pull-up receptor.
- NPN simples em inversor: altera polaridade e pode permitir corrente por junções B–C quando o coletor/receptor está desligado; não declarar isolamento apenas porque o coletor tem resistor.

## 6. Matriz de oito estados: conclusão revisada

S=USB STM, E=USB ESP, A=12 V. A tabela abaixo se refere à arquitetura proposta; UART protegida significa solução Ioff efetivamente implementada/verificada. Modo inicial contém o risco CW removendo fisicamente o codec e abrindo SJ_VA.

|S E A|Trilhos comandados|Risco e contenção|
|---|---|---|
|000|Todos desligados|Aguardar descarga; excluir sinal externo alimentado. Não assumir zero instantâneo nos capacitores.|
|100|STM/3V3/VDVL|UART direta seria risco para ESPoff; interfaceIoff ou jumpers removidos. SemVA: resetbaixo, sem áudio.|
|010|ESP apenas|UART direta seria risco para STMoff; interfaceIoff ou jumpers removidos. Codec sem ambas fontes.|
|110|USBs/VDVL|UART pode operar após qualificar; semVA: resetbaixo, sem áudio, saída externa desconectada.|
|001|RAW/CW/VA seSJfechado|STM/ESPoff; VDVLoff. Sem operação codec; emensaio inicialSJaberto ecodec removido. VAon/VDoff não é violação absoluta demonstrada.|
|101|STM/RAW/VA/VDVL|ESPoff exigeinterfaceUART; clocks/reset devemseguirCirrus. Energização codec ainda dependeCW/clamps/gateB.|
|011|ESP/RAW/VA seSJfechado|STMoff eVDVLoff; conterUART e mantersemoperação codec. Emmodo inicialcodec removido.|
|111|Todas fontes|Não é aprovação automática: primeiroqualificarCW,3V3,clamps,reset e mute. Estadoestável não valida perda defonte.|

As24transições dirigidas por troca de uma fonte, inversão de ordem e cortes abruptos devem manter: positivos separados; GND presente antes de sinais; /RSTbaixo até alimentações/clocksestáveis; saída externa desconectada enquanto muteB não estiver definido. DesligarA comS ativo deixaVA cair antesVDVL: não libera áudio e requercapturaAIN/clamps. DesligarS comAativo retiraVL e seus sinais, masUART precisaIoff contraE. DesligarE comSativo precisaIoff nooutrosentido. Não usar teste de curta duração como prova de isolamento em toda rampa.

Duas USBs podem ligar terras de fontes/hosts diferentes. Planejar GND comum em ponto de referência do sistema com retornos digitais separados do analógico; não levantar terra de proteção para eliminar ruído. Antes de conectar instrumentos/hosts, conferir compatibilidade e ausência de diferença perigosa; fontes isoladas adequadas ou mesmo host podem simplificar o ensaio. Não afirmar isolamento galvânico porque as fontes são distintas.

## 7. Veredito adversarial e evidências necessárias para PASS

**Situação dos arquivos que li: gate A ainda não pode receber PASS integral.** A separação e as contenções acima são propostas, não conexões CAD verificadas. Este parecer oferece um caminho corrigível, não repete simplesmente o bloqueio de identidade.

Um **PASS documental limitado a preparação/ensaios controlados**, permitindo desenvolver a documentação B sem energizar o conjunto, é defensável depois que um auditor independente verificar:

- CAD/BOM/conexões implementam três5V separados, VD/VL exclusivamente3V3STM e interfaceUART comdatasheetIoff;
- SJ_VA aberto porpadrão, testeCW antesdele e nenhuma ponte porADC_BIAS/clamps; requisito de codec removido é explícito no modo de ensaio;
- testes de conectividade/estados passam efetivamente e não fingem validar CW, os oito estados com codec instalado ou ensaios reais;
- documentação deixa **proibido instalar/energizar codec por CW ainda não qualificado**, e mantém bancadaforaescopo desta execução;
- capacidade3V3 é critério futuro condicionado, e nenhum parâmetro de fornecedor errado é atribuídoaoCW.

Esse PASS não pode ser chamado de gate de funcionamento completo nem autorizar fecharSJ_VA. Se o gateA for interpretado como aprovação para energizar todoo codec emquaisquerdos8estados, a decisão permanece **BLOCKED** até a informação/qualificação externa e os mecanismos desegurançacorrespondentes. Especificar os limites docheckpoint é parte da correção, não trocaro nomede umteste reprovado.

## 8. Fontes recuperadas e limitações

- TI SN74AXC2T245, SCES879A RevA, fevereiro/2024, pp1–2 (funções/pinos), p5 (características), pp18–20 (isolação), p23 (sequenciamento): `FONTES_ALIMENTACAO/SN74AXC2T245_TI.pdf`. [Fonte oficial](https://www.ti.com/lit/ds/symlink/sn74axc2t245.pdf).
- TI SN74LVC1G125, SCES223U RevU, agosto/2026, p1 e tabela elétrica: `FONTES_ALIMENTACAO/SN74LVC1G125_TI.pdf`. Alternativa comparativa, não componente escolhido. [Fonte oficial](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf).
- [ST STM32H723 datasheet oficial](https://www.st.com.cn/resource/en/datasheet/stm32h723vg.pdf), seção de consumo Run/tabelas com cacheFlash: consultaweb concluída; tentativa de baixarPDF local deu timeout e está registrada. Não alego PDF local existente. A consulta web identificou DS13313 Rev5, tabela21 p99 (o PDF local não foi obtido).
- Cirrus DS593F2 e WeActV12 foram lidos dos PDFs locais em `output/auditoria_rev49/FONTES/`. [Cirrus oficial](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf), [WeAct oficial](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723).

`FONTES_ALIMENTACAO/inventario.json` registra URLs, hashes dos arquivos obtidos e timeout. Nenhuma fonteCW específica foi fabricada, e nenhum modeloideal foi apresentado como reguladorreal.
