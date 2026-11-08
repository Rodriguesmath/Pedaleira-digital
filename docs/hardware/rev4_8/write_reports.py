from pathlib import Path
import os,shutil
import json,collections
ROOT=Path(__file__).resolve().parents[3];OUT=Path(os.environ.get('PEDALEIRA_REV48_OUT',str(ROOT/'output/rev4_8'))).resolve()
m=json.loads((OUT/'circuito_rev4_8.json').read_text());cs=m['components'];sim=json.loads((OUT/'simulacao/resultados.json').read_text())
new=[a for a in cs if a['status']=='novo'];replaced=[a for a in cs if a['status'].startswith('substituído')]
sources='''## Fontes técnicas consultadas

- **S1**: [Cirrus CS4272, DS593F2, outubro/2021](https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf). Pinagem pp.5-6; condições p.9; DAC p.10; ADC p.14; DC p.17; temporização pp.18-21; fig.8 p.23; controle pp.27-30; entradas/saídas pp.32-33; alimentação p.34; I2C p.36; registradores pp.38-44.
- **S2**: [TI TL07xx, SLOS080W, julho/2025](https://www.ti.com/lit/ds/symlink/tl072.pdf). Pinagem TL072 DIP-8; seção 5.3, condições operacionais; seção 5.8, dispositivos TL07x clássicos. **Não foram aplicadas ao TL072CP as especificações superiores do TL072H.**
- **S3**: [ST STM32H723, DS13313 Rev.5, maio/2025](https://www.st.com/resource/en/datasheet/stm32h723vg.pdf). Tabelas 7/8, pp.57-85: números físicos, pads _C e funções alternativas.
- **S4**: [ST RM0468 Rev.3](https://www.st.com/resource/en/reference_manual/dm00603761.pdf). Capítulo 56, SAI: blocos síncronos A/B, slots, alinhamento e clocks; SYSCFG_PMCR para switches dos pads _C. O acesso web retornou o documento de referência; cópia local integral não foi obtida por timeout do servidor ST.
- **S5**: [WeAct MiniSTM32H723, hardware oficial](https://github.com/WeActStudio/WeActStudio.MiniSTM32H723/tree/master/Hardware). Foi consultado o PDF V1.2 fornecido pelo usuário e copiado para `fontes/WeAct_STM32H7xx_V12.pdf`: headers P1/P2 e circuito de alimentação. A revisão da placa física ainda precisa ser conferida; não presumir correspondência de clones.
- **S6**: [Microchip TC1044S, DS20001348B, 2025](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/TC1044S-Charge-Pump-DC-to-DC-Voltage-Converter-DS20001348.pdf). Pinagem, figuras de inversão, faixa até 12 V, BOOST e impedância de saída. Foi baixada cópia local.
- **S7**: [ST L78, DS0422 Rev.38](https://www.st.com/resource/en/datasheet/l78.pdf). Tabela 10, p.13, L7805C: carga mínima de 5 mA; saída 4,75-5,25 V; circuito com 330 nF/100 nF. Consulta oficial via web; download direto local indisponível por timeout.
- **S8**: [Espressif ESP32-DevKitC, alimentação e identificação dos módulos](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html). Referência de interface; **não comprova a pinagem ordinal de qualquer DevKit V1 genérico**. Usar nomes serigrafados e confirmar WROOM sem PSRAM nos GPIO16/17.

Números/valores provenientes de tabelas são separados de escolhas de projeto e resultados de simulação. “Novo” na BOM significa acrescentado à esquemática 4.7, não uma afirmação sobre o estoque físico; conferir disponibilidade antes de comprar. Valores novos calculados são identificados como “Projeto” na BOM. Nenhum teste de bancada foi declarado como executado.
'''
issues=[
('01','Codec tratado como breakout completo','F3 H_CODEC','CI U2 TSSOP-28, 28 pinos e todos os auxiliares explícitos','Funcionamento','S1 pp.5-6','Implementado; netlist'),
('02','VL não explicitado','F3 codec','Pino 10 em +3V3, separado de VA; VD também +3V3','Funcionamento','S1 pp.9/23/34','Implementado; ERC'),
('03','Desacoplamento/reserva ausentes','F3 codec','C23..C28: 100 nF + 1 uF em VA/VD/VL','Funcionamento','S1 fig.8','Implementado; ERC'),
('04','VCOM/FILT+ sem componentes','F3 e pendência P4','C12/C13 FILT+, C14/C15 VCOM; bias de alta impedância','Funcionamento','S1 fig.8, p.17','Implementado; medir VCOM'),
('05','XTI/XTO não definidos','F3 codec','XTI p.2 em GND, XTO p.1 em NC','Funcionamento','S1 sec.5.2.3.1','Implementado; pinagem'),
('06','AD0/endereço sem ligação física','F3 codec','AD0 p.13 em GND; 0x10 em 7 bits, 0x20 no byte de escrita','Funcionamento','S1 sec.6.2','Implementado; pinagem'),
('07','AINA- flutuante/omitido','F3 e P1','Driver U3B e rede negativa; entrada AC nula','Funcionamento','S1 fig.12','Implementado; OP/AC'),
('08','C2 sem retorno de bias no lado ADC','F1 e P1','R15/R16 de 10 kohm para VCOM; C2 positivo para ADC','Funcionamento','S1 fig.12','Implementado; OP=2,400 V'),
('09','Sem interface para modulador comutado','F1/F3','U3A/B, 634 ohm, 91 ohm, C20; compensação 4,7 nF','Qualidade de áudio','S1 fig.12 + cálculo/simulação','Implementado; estabilidade física pendente'),
('10','Saída DAC tratada como single-ended genérica','F2/F3','AOUTA+ p.25 e AOUTA- p.24, AC e receptor diferencial U1B','Funcionamento','S1 pp.10/33','Implementado; OP/AC'),
('11','Margem TL072 inadequada em 8,3 V simples','F1/F2 e P2','U4 gera alimentação negativa; pino 4 de U1/U3 sai do GND','Funcionamento','S2 sec.5.3/5.8; S6','Implementado; carga da bomba requer bancada'),
('12','Ausência de bypass local nos amplificadores','F1 alimentação U1','C29..C32 junto aos pinos 8 e 4 de cada DIP-8','Qualidade de áudio','S2 aplicação/alimentação','Implementado; layout físico pendente'),
('13','Canal B e saídas não usadas omitidos','F3/P4','AINB+/AINB- juntos em bias filtrado; DAC B e MUTEC em NC','Funcionamento','S1 pinagem/analógico + escolha de projeto','Implementado; conferir bias do B'),
('14','Pull-ups I2C supostos onboard','F3 e pinout antigo','R11/R12 externos 4,7 kohm; I2C inicial 100 kHz','Funcionamento','S5 esquema V1.2; cálculo tr','Implementado; tr calculado 796 ns/200 pF'),
('15','AF10 incorreta em PE4/PE5/PE6','Docs/F3 e Bsp.cpp:508','Documentado AF8 nesses três pinos; PE0/PA0 AF10','Funcionamento','S3 tabela 8 p.80','PENDENTE: firmware não alterado'),
('16','Espera de 10 ms após /RST','Cs4272.cpp:42/170','Exigir 07h=03h antes de 10 ms; aguardar antes de liberar reset','Funcionamento','S1 sec.5.2.1','PENDENTE: firmware não alterado'),
('17','ATAPI=0000 silencia ambos DACs','Cs4272.cpp:46','Exigir 03h=38h para A=L/B=mute com soft+zero-cross','Funcionamento','S1 tabela 15 p.42','PENDENTE: firmware não alterado'),
('18','ADC configurado left-justified','Cs4272.cpp:47','Exigir 06h=14h: ADC I2S, B mutado, HPF habilitado','Funcionamento','S1 sec.8.6/tabela17','PENDENTE: firmware não alterado'),
('19','C5 polarizado sem DC definido após correção','F2 C5','Substituir por 10 uF bipolar; mesma capacitância','Segurança elétrica','Cálculo dos níveis DC do novo receptor','Implementado; BOM e OP'),
('20','VA dependia do USB sem margem garantida','F3/P3','L7805CV dedicado; R21 mantém carga mínima; VA separado de USB','Segurança elétrica','S1 p.9; S7 tabela10','Implementado; medir sob carga'),
('21','Clocks/DMA/SAI não demonstrados no firmware','Bsp.cpp e caminho de áudio','Requisitos completos A master TX/B sync RX e arranque antes do codec','Funcionamento','S4 cap.56; S1 tabela9','PENDENTE: clocks/DMA devem ser implementados ou comprovados'),
('22','BOM/fonte/PDF sem um contrato físico completo','BOM e fontes rev4.7','Modelo físico único; BOM, PDF, CAD e simulação gerados e comparados','Funcionamento','Conferência cruzada de arquivos','Implementado; ver VALIDACAO_rev4_8.json')]
text='''# Auditoria elétrica - Pedaleira Digital - Rev.4.8

Autoria: Rodrigues M. Lima. Revisão de projeto em 06/11/2026. **Veredito: CONDICIONADO; não liberado para montagem definitiva/fabricação.** O hardware foi corrigido documentalmente e passou por ERC, mas o firmware existente contém impedimentos conhecidos à passagem de áudio e a montagem não foi medida.

## Escopo e rastreabilidade

O hardware real contém um CS4272 TSSOP-28 em adaptador **passivo**, sem reguladores, desacoplamento ou condicionamento. Foram mantidos STM32H723, ESP32, chaves, LEDs, jacks e alimentação externa de 9 V/USB. A autorização posterior permite **dois TL072**: U1 existente e U3 novo. Não foi utilizado MCP6022, nem um terceiro amplificador.

Os originais foram preservados em `backup_rev4_7/`, com SHA-256, antes de modificações. O gerador antigo e o EasyEDA rev4.7 permanecem como legado, não como fonte desta revisão. A fonte elétrica é `circuito_rev4_8.json`; há projeto KiCad nativo com símbolos incorporados e biblioteca local. PDF e BOM vêm do mesmo modelo físico; a netlist exportada pelo KiCad é comparada pino a pino. Redes iguais são conexões, mesmo sem fio longo entre folhas. Não existe PCB projetada.

## Resultado da revisão

'''
text+=f'Foram registrados **22 problemas**, com **17 correções implementadas** no hardware/documentação e **5 itens pendentes no firmware/ativação do áudio**. A BOM contém **{len(cs)} itens físicos**, sendo **{len(new)} novos**, 32 existentes preservados e **1 substituição de tipo**, C5. U2 substitui apenas o nome H_CODEC; não representa compra de outro codec. C33 é o antigo C_IN. U1A/U1B e U3A/U3B são metades de dois CIs, não quatro CIs.\n\n'
text+='| ID | Problema identificado | Localização na rev.4.7/projeto | Correção aplicada/exigida | Classe | Fundamentação | Verificação/status |\n|---|---|---|---|---|---|---|\n'
for row in issues:text+='| '+' | '.join(row)+' |\n'
text+='''
## Alimentação e limites

| Domínio | Ligação física | Operação exigida | Absoluto / observação |
|---|---|---|---|
| VA U2 | pino 20, +5VA de U5 | 4,75-5,25 V | -0,3 a +6 V; absoluto não é tensão normal |
| VD U2 | pino 9, +3V3 WeAct | 3,1-5,25 V; projeto 3,3 V | -0,3 a +6 V |
| VL U2 | pino 10, mesmo +3V3 | 2,37-5,25 V; projeto 3,3 V | -0,3 a +6 V; entradas digitais <=VL+0,3 V |
| AGND/DGND | pinos 21/8, GND | Terra comum contínuo | Evitar retorno Wi-Fi/bomba pelo caminho ADC |
| U1/U3 | pinos 8 +RAW / 4 -VA_OP | +RAW >=7,8 V; -VA_OP <=-6 V como critério de bancada | Conferir fabricante/sufixo real do TL072 |
| USB das placas | J4, +5V_USB | Fonte única 5 V >=1 A; preferir 2 A para margem | 5V das placas não é saída regulada de 9 V |

VA não está unido a VL nem a +5V_USB. VD e VL podem compartilhar os 3,3 V conforme S1. Cada um recebe seu par de 100 nF/1 uF junto ao pino. Consumo do codec: VA até 53 mA e VD/VL combinados até 28 mA nas condições da tabela S1; isso não inclui STM32/ESP32. Confirmar orçamento e transientes da WeAct real. Nunca alimentar ESP32 pelo GPIO ou assumir corrente USB ilimitada.

U5 L7805CV recebe aproximadamente 8,3 V de D1. Com VA a 5 V, codec 53 mA, carga R21 ~5,5 mA e corrente própria estimada em 8 mA, dissipa aproximadamente 0,26 W. R21=910 ohm garante >5 mA mesmo em 4,75 V com tolerância de 1%; sua dissipação é ~30 mW. Valores 330 nF/100 nF seguem S7. A faixa garantida 4,75-5,25 V do L7805C coincide com a do codec e requer medição sob carga; não há margem adicional de tolerância para ignorar cabeamento.

U4 TC1044S recebe +RAW; pino 1 BOOST ligado a V+, LV/OSC abertos. C7/C8 seguem o circuito de inversão. C8 e C3 têm **positivo em GND**. R9=22 ohm/C3=47 uF filtram a alimentação negativa: fc~154 Hz, queda de 0,22 V a 10 mA. A frequência de comutação com BOOST é tipicamente 22,5 kHz, não garantidamente fora de toda a faixa audível. A resistência da bomba e a tensão negativa foram apenas estimadas; não foi simulada a conversão chaveada. Confirmar -VA_OP em carga, ripple e partida. Não alimentar outras cargas pela bomba.

Ferrites não foram acrescentados sem necessidade medida. São opcionais após avaliação de EMI; uma divisão ruim de terras ou ferrite sem análise pode piorar o retorno. A montagem precisa de conexões curtas, retornos segregados e conexão contínua de AGND/DGND. O adaptador não substitui uma região local de desacoplamento.

VCOM nominal ~0,48 VA, cerca de 2,4 V: C14=1 uF selecionado <=1 uF e C15=100 nF, conforme fig.8. C17=10 nF pertence ao bias da fig.12. A limitação de 1 uF refere-se ao capacitor indicado na figura, que também mostra 100 nF em paralelo. FILT+ usa 47 uF/100 nF. Nenhuma dessas redes é fonte para ESP32, LEDs ou outras cargas. VCOM admite somente 1 uA DC; bias dos dois TL072 e nó B devem ser conferidos por medição. Não foi inventado um limite garantido para a corrente DC do ADC B, que não é tabelada separadamente; R10/C34 e o bias B precisam ser verificados na bancada.

## Entrada e TL072

U1A mantém ganho unitário. C1=100 nF e R3=1 Mohm estabelecem fc~1,59 Hz e impedância em torno de 1 Mohm; R3 agora retorna ao GND porque há alimentação bipolar. U1A pinos 1/2 unidos; pino 3 é HI_Z. A entrada especificada para o protótipo é **até 1 V de pico**, sem fonte DC externa no jack.

C2=10 uF acopla IN_BUF ao driver positivo. Seu positivo fica no lado ADC (~2,4 V). C16 faz a referência AC nula do ramo negativo, também com positivo no lado de bias. R15/R16=10 kohm polarizam as entradas + de U3 em VCOM. U3A/B utilizam feedback a partir dos próprios pinos AINA+/AINA-, **após** 91 ohm, via 634 ohm; isso é diferente de colocar 634 ohm em série ou aterrar AINA-.

A rede parte da fig.12 de S1. O valor de compensação 470 pF indicado pelo fabricante foi avaliado com um modelo linear de TL072 de 3 MHz e produziu pico de ~4,59 dB. C18/C19 foram ajustados para 4,7 nF C0G/NP0, reduzindo o pico nominal para ~0,73 dB. Esse valor é uma **escolha de projeto sustentada pela simulação**, não um valor atribuído ao datasheet. Ainda exige verificação de margem de fase/estabilidade com o componente real, parasitas, tolerâncias e carga comutada. C20=2,7 nF diferencial foi preservado da figura.

O ADC recebe áudio mono por uma perna, com a outra no modo comum; não se exige sinal complementar para haver conversão. Isso utiliza menos da faixa diferencial: com 1 V de pico, 2 Vpp representam cerca de -9 dBFS frente a 5,65 Vpp típicos. Não se promete SNR de 114 dB no instrumento nem ganho para captadores fracos. Amplificar a guitarra para aproveitar toda a faixa é uma melhoria opcional futura, com nova análise de clipping.

Com +RAW>=7,8 V e -VA_OP<=-6 V, as entradas de U1A em +/-1 V e de U3 em ~2,4 V estão afastadas do rail negativo. As saídas ADC previstas ficam ~1,4-3,4 V, dentro da figura de operação de S1. O receptor U1B deve produzir até cerca de +/-2,65 V na maior escala DAC e VA. A alimentação simples anterior colocava entradas na região problemática do TL072 clássico. A nova alimentação remove esse impedimento nominal, mas **os limites min/max de excursão e modo comum da tabela TI caracterizados em +/-15 V não foram extrapolados como garantias para +/-8 V**. Clipping real e cargas capacitivas continuam sendo critérios de aprovação física.

Os resistores de 91 ohm são isoladores de carga, não proteção contra qualquer sobrecarga. Não foram adicionados grampos de diodo em VCOM, pois o sobrecarregariam e contaminariam a referência. Não há proteção ESD/sobretensão certificada: não ligar saída de potência, phantom power ou níveis além do envelope especificado à entrada. Uma especificação de proteção contra abuso é pendência de produto, além deste protótipo condicionado.

## Saída e filtro

O CS4272 fornece AOUTA+ e AOUTA- (pinos 25/24), diferencial, em cerca de VA/2. Não existe pino físico “AOUTL” single-ended. C10/C11 bipolares removem esse nível DC; R1/R2 existentes e R7/R8 novos, todos 100 kohm, formam o receptor diferencial U1B de ganho 1. Preferir casamento 0,1% se a rejeição de modo comum for importante; 1% é suficiente apenas para prototipagem. O ruído dos 100 kohm e do TL072 impede atribuir à pedaleira automaticamente o desempenho máximo do codec.

R4/R5=1 kohm, C4=4,7 nF, C6=1,5 nF e R6=100 kohm foram conservados. A cascata RC passa a ficar **depois** do receptor U1B; o op-amp deixa de ser um seguidor colocado depois de um DAC abstrato. C5 continua 10 uF, agora bipolar por ausência de DC garantido. O filtro digital do codec permanece responsável pela reconstrução principal; a rede externa atenua imagens/RF.

Sem carga, a rede RC ideal é:

`H(s)=1/[R4*R5*C4*C6*s² + (R4*C4+R4*C6+R5*C6)*s + 1]`.

Com carga, R6 fica em paralelo com a entrada do amplificador e há C5 em série: foi simulada a rede completa, não somente a expressão ideal. Para carga externa de 100 kohm: ganho em 1 kHz ~-0,35 dB, em 20 kHz ~-2,60 dB, corte relativo de -3 dB ~24,5 kHz. Isso caracteriza uma saída de linha com pequeno arredondamento de agudos, **não uma saída para fones**. Em 10 kohm a perda aumenta; medir antes de prometer nível de instrumento/linha. Muting externo para eliminar pops é melhoria recomendada não implementada; AMUTEC/BMUTEC permanecem corretamente em NC.

## Pinagem física e interface digital

A tabela usa número do **CI LQFP100**, contato do **header WeAct V1.2**, nome lógico e terminal físico do codec. Não misturar estes sistemas de numeração.

| Sinal | STM32 / pino físico | Header WeAct | AF | CS4272 / pino | Sentido |
|---|---|---|---|---|---|
| MCLK | PE0 / 97 | P1.4 | AF10 SAI4_MCLK_A | MCLK / 3 | STM -> codec |
| LRCK | PE4 / 3 | P2.5 | **AF8** SAI4_FS_A | LRCK / 4 | STM -> codec |
| BCLK | PE5 / 4 | P2.6 | **AF8** SAI4_SCK_A | SCLK / 5 | STM -> codec |
| DAC_DATA | PE6 / 5 | P2.7 | **AF8** SAI4_SD_A | SDIN / 7 | STM -> DAC |
| ADC_DATA | PA0 / 22 | P2.17 | AF10 SAI4_SD_B | SDOUT / 6 | ADC -> STM |
| I2C_SCL | PB8 / 95 | P1.6 | AF4 I2C1_SCL | SCL / 11 | STM -> codec |
| I2C_SDA | PB9 / 96 | P1.5 | AF4 I2C1_SDA | SDA / 12 | Bidirecional |
| CODEC_RST | PD10 / 57 | P1.38 | GPIO | /RST / 14 | STM -> codec |
| UART_TX | PD8 / 55 | P1.40 | AF7 USART3_TX | ESP GPIO16 RX2 | STM -> ESP |
| UART_RX | PD9 / 56 | P1.39 | AF7 USART3_RX | ESP GPIO17 TX2 | ESP -> STM |

PC0/PC1, pinos 15/16, P2.11/P2.12, e PC2_C/PC3_C, pinos 17/18, P2.13/P2.14, leem as chaves. Nos pads _C do H723, o caminho ao GPIO PC2/PC3 depende do switch analógico interno **fechado**; conferir SYSCFG_PMCR PC2SO/PC3SO e testar pull-up. A serigrafia WeAct abrevia esses nomes. Alternativa caso o firmware/plataforma não suporte esse uso: remapear essas duas chaves para GPIOs livres e atualizar a documentação antes de montar; não foi feita uma troca silenciosa de fios. PE7/8/9/15 são pinos 37/38/39/45 e P2.30/31/32/38; LEDs de aproximadamente 2 V consomem ~4 mA com 330 ohm, enquanto LEDs de Vf alto podem ficar mais fracos. Não usar câmera nos mesmos pinos. Confirmar módulo ESP32: GPIO16/17 não ficam livres em todas as variantes com PSRAM.

O mapeamento SAI4 existente é fisicamente viável; não precisa usar PE2/PE3, que conflitam com recursos onboard. A correção necessária é **AF8**, não a troca para outra instância ou a alegação de que PE4/PE5/PE6 usam AF10. Alimentar VL em 3,3 V mantém os níveis do codec compatíveis com STM32/ESP32. Não ligar MUTEC, que pode chegar a VA, diretamente a GPIO de 3,3 V.

R11/R12 externos iniciam I2C em 100 kHz. `tr≈0,8473*4,7k*200pF≈796 ns`, adequado ao limite de subida de 1 us do modo padrão. Não afirmar 400 kHz com esses mesmos 200 pF; seria necessário reduzir capacitância/resistência e recalcular corrente de sink.

## Requisitos de firmware (documentados; não implementados nesta tarefa)

1. Inicializar rails, GPIO de reset em LOW e clocks SAI antes de liberar /RST. GPIOs não devem injetar sinal em dispositivo sem seus rails operacionais; energizar 9 V/USB com controle, sem conectar instrumento durante partida de testes.
2. SAI4 A master TX assíncrono gera MCLK/LRCK/BCLK; SAI4 B slave RX síncrono internamente ao A. Configurar PE0/PA0 AF10, PE4/5/6 AF8. I2C AF4 open-drain. UART3 AF7, 115200 8N1.
3. Fs=48 kHz, 2 slots x 32 bits, 24 bits válidos, frame 64 bits, ativo 32 bits, I2S com deslocamento de um BCLK, LRCK baixo para canal A/esquerdo, dados amostrados na subida. Clock MCLK=256 Fs e BCLK=64 Fs, ambos derivados da mesma fonte SAI. HSE WeAct=25 MHz, portanto não assumir divisão inteira que gere exatamente 12,288 MHz; PLL de áudio/fração e tolerância devem ser calculadas e medidas. Não foi afirmada uma configuração PLL testada que não existe.
4. Manter /RST baixo até clocks/rails estáveis; liberar e escrever **07h=03h antes de 10 ms**. O atraso pós-reset atual de 10 ms em Cs4272.cpp torna isso não garantido. Aguardar a estabilização antes de liberar o reset, e não depois.
5. Sob PDN: 01h=01h (single-speed, slave, I2S DAC, ratio 256), 02h=00h (sem de-emphasis), **03h=38h** (soft+zero-cross, DAC A recebe L e B mutado), 04h=00h, 05h=80h, **06h=14h** (ADC I2S, B mute, HPF ligado). Por fim 07h=02h libera PDN. Confirmar leitura quando aplicável; o início interno leva ~85 us após PDN conforme S1, sem confundir com a estabilização analógica externa.
6. Firmware atual escreve 03h=30h, cujo ATAPI=0000 silencia **ambos** os DACs; escreve 06h=00h (ADC left-justified), incompatível com o I2S planejado. São bloqueadores conhecidos de áudio mesmo que o hardware esteja perfeito. O GPIO AF10 geral da configuração SAI4 também está errado em três pinos. A busca no código não demonstrou configuração operacional de SAI/clocks/DMA: não foi declarada inexistência absoluta em toda dependência externa, nem execução de pass-through.
7. Inicializar buffers TX com zero, habilitar SAI/DMA na sequência válida, habilitar ADC/DAC, encaminhar slot esquerdo do ADC ao slot esquerdo do DAC e manter o direito em zero. Confirmar acesso/cache/DMA do H7 e formato/sinal de 24 bits; o ERC não avalia firmware.

## Verificações executadas e seus limites

- KiCad 10.0.7: projeto hierárquico carregado, netlist XML exportada e ERC **0 erros/0 avisos**, sem exclusões adicionadas. Flags +RAW, GND e -VA_OP documentam fontes após diodo/filtro; não escondem ausência de circuito.
- Netlist do KiCad comparada por tuplas `(referência,pino)` com o modelo, ignorando somente as redes artificiais de NC e os três flags sem BOM. Igualdade exigida para todas as 56 redes reais; conjunto de NC também conferido.
- BOM física e valores comparados com modelo e CAD. U1/U3 contam uma vez cada. Todos os terminais do modelo aparecem no PDF. Capacitores eletrolíticos e bipolares diferenciados.
- ngspice 47 executado em `.op` e AC de 1 Hz a 100 MHz. Passivos e conexões analógicas são extraídos do mesmo JSON usado para o PDF, evitando uma simulação de outro circuito.
- Amplificador linear aproximado: Aol=200000, GBW=3 MHz, Rout=50 ohm, dominante de um polo. **Não é macromodelo do fabricante.** Carga ADC diferencial de 37 kohm é a resistência mínima tabelada; não reproduz o chaveamento real. Rails e fontes de DAC/VCOM são ideais. Não modela slew, saturação, ruído, THD, tolerâncias, EMI ou partida da bomba.
- Resultado OP: U1A e DAC_BUF ~0 V, entradas ADC ~2,400 V, P10 ~0 V. AC: ADC 20 Hz -0,055 dB, 1 kHz ~0 dB, 20 kHz +0,170 dB; pico 0,73 dB; atenuação em 6,144 MHz ~42,4 dB. A resposta fora da banda é indicativa do modelo linear, não medição de aliasing/SNR.
- Os sete layouts PDF foram rasterizados e inspecionados. Não foi executada montagem, medição, simulação transitória de partida nem ERC de uma PCB.

## Pendências para liberação

As cinco pendências funcionais de firmware da tabela impedem declarar passagem de áudio. Exigem correção posterior autorizada e teste real. A montagem fica também condicionada a: conferir revisão/modelo das placas e adaptador; medir rails e ripple sob carga; confirmar bias em AINA e AINB sem consumir VCOM; validar estabilidade e clipping dos dois TL072; testar sequência com uma fonte presente e a outra ausente, sem injeção indevida; medir clocks e fluxo de áudio por analisador lógico; avaliar ruído de Wi-Fi/bomba e pops.

A revisão permite iniciar preparação e conferência de montagem de bancada seguindo o checklist. Não é liberação para fabricação, conexão indiscriminada de fontes/sinais ou montagem definitiva. A ausência de erros de ERC não encerra essas pendências.

'''+sources
(OUT/'AUDITORIA_ELETRICA.md').write_text(text)
change=f'''# Changelog - rev.4.8

Autoria: Rodrigues M. Lima. A revisão 4.7 foi preservada em backup antes das alterações.

- 22 problemas registrados: 17 corrigidos no circuito/documentação; 5 pendências funcionais de firmware documentadas.
- CS4272 agora é U2, CI físico TSSOP-28 em adaptador passivo, com os 28 pinos, NC, alimentações e referências.
- Acrescentado U3 TL072 para ADC, conforme autorização: total de dois TL072 DIP-8.
- Acrescentados U4 TC1044S e U5 L7805CV com componentes externos. U1/U3 pino 4 em -VA_OP, sem curto ao GND.
- R1/R2 de 100 kohm reutilizados no receptor diferencial; C3 de 47 uF reutilizado no filtro negativo. C_IN renomeado C33.
- C5 substituído por bipolar de 10 uF; demais valores antigos mantidos. C10/C11 bipolares novos.
- Rede de ADC baseada na fig.12 DS593F2; C18/C19 ajustados a 4,7 nF por simulação linear com TL072 de 3 MHz.
- R4/R5/C4/C6 preservados e reposicionados após U1B. Nova função e carga do filtro documentadas.
- Pull-ups I2C explícitos, reset com pull-down, SDOUT com 47 kohm; AF8/AF10 corrigidas na documentação.
- Circuito, PDF, BOM, KiCad e simulação têm um modelo físico comum; ERC sem violações e comparação integral de netlist.
- Nenhum firmware foi alterado. ADC_DIF, ATAPI, atraso pós-reset, AF e SAI/clocks/DMA permanecem bloqueadores documentados.

## Quantidades

BOM: {len(cs)} itens físicos. Novos: {len(new)}. Existentes reaproveitados: 32. Substituição de tipo: 1 (C5).

Novos: {', '.join(a['ref'] for a in new)}.

Não houve troca do STM32, ESP32, CS4272 ou TL072 existente. O adaptador TSSOP não foi contado como breakout eletrônico. Os três PWR_FLAG do CAD são declarações elétricas, não peças de compra.

## Classificação

Obrigatórias para funcionamento: alimentação negativa/TL072, circuitos externos do codec, ADC, conversão diferencial DAC, I2C, reset e mapeamento digital. Obrigatórias para segurança elétrica: separação VA/USB, polaridades, C5 bipolar, limitação às faixas operacionais e checklist. Recomendadas para qualidade: desacoplamento local, casamento do receptor e compensação do ADC. Opcionais, não montadas: ferrites após ensaio EMI, ganho adicional para captadores fracos e mute externo anti-pop.

Ver fundamentação e status de cada item na AUDITORIA_ELETRICA.md. Veredito: condicionado, sem aprovação para montagem definitiva.
'''
(OUT/'CHANGELOG_rev4_8.md').write_text(change)
check='''# Checklist de montagem e ensaio - rev.4.8

Autoria: Rodrigues M. Lima. Usar exclusivamente a esquemática/BOM 4.8. Os arquivos 4.7 são legado. Marcar resultados e valores medidos; nenhum item abaixo foi executado fisicamente nesta revisão.

## Sem alimentação

- [ ] Conferir CS4272 TSSOP-28, fabricante/sufixo/grade e marca do pino 1 no adaptador. Identificar continuidade CI->pinos; não assumir a ordem do header do adaptador.
- [ ] Conferir dois TL072 DIP-8: U1 e U3, fabricante/sufixo do existente e datasheet aplicável. O pino 4 de ambos vai a -VA_OP, **não GND**; pino 8 em +RAW.
- [ ] Conferir U4 TC1044SCPA, não um 7660 genérico: 1 BOOST/8 V+, 2 CAP+, 4 CAP-, 3 GND, 5 VOUT, 6/7 NC.
- [ ] Conferir U5 ST L7805CV: frente do TO-220 e numeração 1 IN/2 GND/3 OUT; aba em GND.
- [ ] Conferir BOM, componentes novos e capacitores. C33 é C_IN antigo. C3/C8 positivos no GND; C7 positivo CAP+; C2 positivo ADC_P_IN; C16 positivo ADC_N_IN; C12 positivo FILT+; C33 positivo +RAW.
- [ ] C5/C10/C11 de 10 uF são **bipolares**. C18/C19=4,7 nF e C20=2,7 nF C0G/NP0. C14 de 1 uF selecionado <=1 uF, próximo de VCOM.
- [ ] R21=910 ohm, 1%, carga mínima VA; R17/R19=634 ohm; R18/R20=91 ohm. Feedback 634 ohm após 91 ohm.
- [ ] 100 nF junto a cada alimentação; circuitos de VCOM/FILT e pares ADC curtos. Bomba/ESP e seus retornos afastados do ADC.
- [ ] AGND e DGND em GND contínuo. Medir ausência de curto entre +5VA, +5V_USB, +3V3, +RAW, -VA_OP e GND.
- [ ] AINB+ e AINB- unidos em AINB_CM. XTI aterrado, XTO e saídas B/MUTEC NC. Não aterrar nenhum AOUT.
- [ ] Identificar COM das MTS-102 por continuidade; terceiro contato isolado. Conferir ânodo/cátodo dos LEDs e orientação de D1.
- [ ] Conferir WeAct **V1.2** e modelo do ESP32. Seguir nomes dos GPIOs e headers do relatório; nenhuma numeração de outro DevKit deve ser presumida.
- [ ] PC2_C/PC3_C exigem switch interno fechado para GPIO; confirmar SYSCFG_PMCR e leitura com pull-up antes de usar as chaves.

## Alimentação por etapas, sem instrumento nem amplificador

- [ ] J4 é borne de duas vias (1=VBUS, 2=GND), não pinagem ordinal de USB-A. No cabo USB-A usar 1=VBUS e 4=GND; identificar por continuidade.
- [ ] Fonte 9 V regulada, centro positivo, inicialmente limitada em corrente. Verificar 8,8-9,2 V na entrada antes de inserir CIs.
- [ ] Verificar +RAW sob carga (alvo ~8,3 V, mínimo de ensaio 7,8 V); +5VA **4,75-5,25 V** em reset e operação. Se fora, parar e corrigir.
- [ ] Verificar -PUMP e -VA_OP, com carga representativa dos dois TL072. Exigir -VA_OP <=-6,0 V para o envelope proposto; observar ripple e aquecimento. Se o critério falhar, não presumir operação correta.
- [ ] Verificar positivo de C3/C8 no zero e negativo no rail negativo; verificar frequência/ripple da bomba no osciloscópio.
- [ ] Usar fonte USB única, >=1 A (preferir 2 A), distribuída para VIN/5V das placas. Não conectar simultaneamente outro USB com VBUS ativo, nem alimentar pelo 3V3. Debug sem VBUS adicional.
- [ ] Medir +3V3 em VD/VL do codec sob carga e com Wi-Fi ativo: 3,1-3,6 V no projeto. Medir VA durante transientes do ESP32.
- [ ] Medir corrente nos dois barramentos, queda em cabos e temperatura U5. Confirmar ausência de realimentação entre fontes e sequência segura de desligamento.
- [ ] Não aplicar sinais de GPIO/áudio a dispositivos sem seus rails operacionais. Testar energização parcial de forma controlada e sem injetar clocks no codec desligado.
- [ ] VCOM próximo de 0,48*VA e FILT+ próximo de VA; investigar se carregados. AINB_CM deve acompanhar VCOM. Medir os dois ramos AINA sem sinal (~VCOM).
- [ ] U1A IN_BUF e U1B DAC_BUF próximos de 0 V. P10 saída próximo de 0 V. Registrar offsets; não interpretar estimativas como tolerâncias garantidas.

## Firmware e sinais digitais - bloqueadores atuais

- [ ] Corrigir PE4/PE5/PE6 para **AF8**; manter PE0/PA0 AF10. Conferir GPIOs, open-drain I2C e pull-ups externos 4,7 kohm.
- [ ] Corrigir espera pós-/RST: 07h=03h antes de 10 ms da liberação. Clocks e rails já estáveis antes dela.
- [ ] Corrigir 03h para **38h**, e 06h para **14h**. 01h=01h, 04h=00h, 05h=80h e 07h=02h ao liberar PDN. Ler chip ID/registradores e confirmar ACK em 0x10 de 7 bits.
- [ ] Configurar e comprovar SAI4 A master TX, B RX síncrono, clocks/PLL e DMA/cache do H7; essa configuração não foi validada nesta tarefa.
- [ ] Medir MCLK 12,288 MHz, BCLK 3,072 MHz e LRCK 48 kHz, sincronizados; I2S MSB após um bit, 2 slots de 32 bits/24 úteis.
- [ ] Confirmar transições dos GPIOs e três estados de partida sem sobrescrever sinal SDOUT; confirmar UART cruzada de 3,3 V e GND comum.

## Passagem de áudio de bancada

- [ ] Só após itens anteriores: gerador de funções 1 kHz/100 mVpp, sem DC, na entrada; carga resistiva 100 kohm na saída, sem amplificador de potência inicialmente.
- [ ] Conferir U1A ganho 1 e bias zero. U3A/B devem manter modo comum, sem oscilação ou clipping; observar também em alta largura de banda.
- [ ] Aumentar gradualmente até o limite de ensaio de 1 V de pico; conferir cada pino ADC dentro da faixa analógica permitida. Não testar abuso/sobretensão nesta montagem.
- [ ] Testar pass-through real, slot esquerdo para esquerdo, direito zero. Confirmar saída, polaridade, ruído e THD por medição; o projeto não declara valores medidos.
- [ ] Varrer 20 Hz-20 kHz, repetir com Wi-Fi e bomba ativos. Comparar com simulação e verificar estabilidade com carga/cabo reais. Avaliar pops ao ligar/desligar e mutar.
- [ ] Só então conectar a entrada de alta impedância do amplificador de guitarra com volume baixo. Não conectar fones nem saída de potência no jack da pedaleira.

## Liberação

- [ ] Cinco bloqueadores de firmware encerrados e resultados registrados.
- [ ] Rails, bias, estabilidade, clipping e passagem de áudio aprovados por medidas reais.
- [ ] Atualizar auditoria com valores, equipamentos, data e responsável.

Até o encerramento, o veredito continua **CONDICIONADO**, sem aprovação para fabricação/montagem definitiva.
'''
(OUT/'CHECKLIST_MONTAGEM.md').write_text(check)
(OUT/'fontes/REFERENCIAS.md').write_text(sources)
