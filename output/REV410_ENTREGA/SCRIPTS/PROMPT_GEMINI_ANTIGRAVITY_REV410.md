# Retomada da pedaleira digital - Gemini Antigravity Flash 3.8 High

Você está recebendo um trabalho de engenharia já parcialmente implementado. Continue dos arquivos existentes; não reinicie o projeto nem declare aprovação para encerrar a tarefa.

## Objetivo

Corrigir os bloqueios restantes da revisão 4.10 e obter, quando as evidências permitirem, **APROVADO DOCUMENTALMENTE PARA ENSAIOS CONTROLADOS**. Não existe autorização para declarar funcionamento completo. Montagem, medições, flash, integração completa SAI/DMA e validação física de áudio estão fora desta missão.

O usuário encerrou a etapa atual do Codex e pediu este prompt para você concluir o trabalho. A fase A foi encerrada como checkpoint de trabalho **BLOCKED**, sem PASS. Isso não significa que seus requisitos elétricos tenham sido atendidos. As fases B e C não foram iniciadas.

## Ambiente e fontes da verdade

- Repositório: `/home/rodrigues/Pedaleira-digital`.
- Branch de trabalho: `codex/rev410-auditoria`. Inspecione `git status` e o último commit antes de editar.
- Base preservada anterior a esta etapa: commit `1c73c02`.
- Missão completa original: `/home/rodrigues/.codex/attachments/d2259877-0c5a-4aef-9a4f-365af81cdb67/Texto colado.txt`. Leia integralmente.
- Fontes e auditoria anteriores: `output/auditoria_rev49/`, incluindo `AUDITORIA_REV49.md`, `RESULTADO_AUDITORIA.json`, `FONTES/` e `VALIDACAO/circuito_rev49_errata_documental.json`.
- Originais 4.9: `docs/hardware/rev4_9/` e `output/rev4_9/`. Não sobrescreva. Os hashes estão em `output/REV410_ENTREGA/BASE_REV49_SHA256.txt`.
- Trabalho atual: `docs/hardware/rev4_10/` e `output/REV410_ENTREGA/`.
- Leia `CLAUDE.md`, os requisitos aplicáveis do repositório e eventuais `AGENTS.md`. Não regenere firmware nem tome exemplos antigos como pinagem atual.

Leia primeiro os relatórios atuais `RELATORIO_REV410.md`, `CHECKPOINTS.md`, `MATRIZ_RISCOS.csv`, `MATRIZ_ALIMENTACAO.md`, `ANALISE_CW7805.md` e os pareceres `REVISOES/CAD_A_INDEPENDENTE.md` e `REVISOES/INTERFACES_A.md`. Pareceres preliminares em `REVISOES/` são históricos: a escolha final de UART é ISO7721DR, não SN74LVC1G07 nem 1G125.

## Decisões do usuário que continuam válidas

1. STM WeAct H723 V1.2 alimentada pela própria USB; ESP32 alimentado pela própria USB.
2. Fonte externa 12 V ±5%; TL072 em alimentação simples, positivo RAW após proteção e negativo GND real.
3. CW7805 fornece somente os 5 V analógicos do codec. Nunca unir os positivos USB ao CW nem entre si.
4. VD/VL do codec no mesmo +3V3_STM dos sinais digitais do STM; capacidade livre deve ser fundamentada.
5. Manter VREF_OP e ADC_BIAS independentes; não carregar VCOM.
6. Usuário informou que o CW é genérico de três pinos, retirado de placa de aparelho alimentado em AC. Escolheu expressamente **manter o CW e registrar a qualificação pendente**. Depois pediu para não concentrar a revisão em seus limites, pois a saída nominal é 5 V. Não repita perguntas de substituição nem substitua silenciosamente. Trate 5 V como premissa de interface; não invente fabricante, pinagem garantida, estabilidade, SOA, térmica ou proteção interna a partir da procedência. Qualificação pendente não é medição realizada.
7. Preserve os componentes e valores originais que não tenham motivo elétrico demonstrado para mudança. Novos componentes de proteção podem ser propostos com necessidade, limites, alternativas e disponibilidade explicitados; não simule estoque ou compra.
8. Estilo visual aprovado: fontes Times, símbolos compactos azuis, fios azul-escuro, labels vinho, corpos claros, seções abertas sem cartões ambíguos, moldura técnica e legenda inferior direita. Sem header superior. Autoria **Rodrigues M. Lima**. Preservar a disposição existente sempre que possível.

## O que já está implementado e verificado

- 114 componentes, 288 terminais físicos, 277 conectados e 11 NC, em 61 redes e oito folhas A4 paisagem.
- Headers STM P1.2/5V e ESP VIN estão NC externos; as USBs são internas às placas e não foram inventadas como pinos externos.
- +5V_CW contém U5 saída, C22/C37/R21, D8 anodo, TP2 e J4 de carga artificial. J4 não alimenta as placas.
- J5 é seccionamento entre +5V_CW e +5VA, **sem shunt por padrão**. +5VA alimenta VA20, bypass VA, ADC_BIAS e clamps superiores. J5 não é proteção automática.
- UART direta foi substituída por **Texas Instruments ISO7721DR, sem sufixo F, encapsulamento D/SOIC-8**. Não usar pinagem DW16.
- U6: 1 VCC1=STM; 2 OUTA→RX STM; 3 INB←TX STM; 4 GND1; 5 GND2; 6 OUTB→RX ESP; 7 INA←TX ESP; 8 VCC2=ESP. Os dois GND estão no GND comum: não há isolamento galvânico do produto.
- C42/C43=100 nF locais; R29/R30=10 kΩ de descarga; R31/R32=47 kΩ de pull-up dos TX à própria alimentação. Cada I/O externo pertence ao seu domínio. Não existe UART paralela.
- USART3 é **PD8/TX, chip55, headerP1.40, AF7; PD9/RX, chip56, headerP1.39, AF7**. Ambos FT_h. Não são PA9/PA10.
- ISO: orçamento de projeto 4 mA por domínio; timing publicado usa CL=15 pF. Brownout é indeterminado. Com receptor alimentado e transmissor desligado, default HIGH só nas condições e atrasos do datasheet. Saída com próprio lado desligado é indeterminada, não Hi-Z garantido.
- Footprint oficial SOIC-8 de U6 incluído com tabela local. Os demais footprints herdados continuam sem qualificação completa; não são aprovados por conter uma nota de encapsulamento.
- ERC final: **zero violações, sem exclusões**, executado com todas as severidades. XML e BOM conferidos por partições completas de pinos, não somente nomes de labels.
- Executados e aprovados: 11 testes de alimentação, 12 cálculos independentes UART, 12 testes independentes CAD e conferência das rotas visíveis. Todas as oito folhas foram inspecionadas visualmente.
- Os ganhos analógicos e todos os valores originais foram preservados. DAC diferencial 0,499; U1A/U3A seguidores; U3B inversor. Metadados R15/R16, C5, C30/C32 foram corrigidos.
- Firmware não foi alterado nesta etapa. As correções anteriores e o bloqueio de transporte de áudio devem permanecer.

## Bloqueios que você precisa resolver

1. **Reset na perda de VA:** PD10 pode ficar HIGH enquanto VA cai. R13=10 kΩ não vence uma saída ativa. Reset por software não é intertravamento físico de alimentação. Projete uma solução elétrica e confira partida, queda, brownout, retorno e compatibilidade com o procedimento de reset/configuração do driver existente; não introduza um atraso que faça o driver escrever antes da liberação real.
2. **Entradas analógicas com VA ausente:** RAW alimenta TL072; C2/C16/C40 retêm ou transferem carga. Reset LOW não desconecta AIN. J5 aberto com codec instalado também não isola suas 28 conexões. A contenção inicial documentada exige U2 fisicamente ausente e guitarra/jack externo desconectados; isso só prepara ensaios separados.
3. **Proteção ADC:** BAT85 e 1,5 kΩ não demonstram AIN dentro de GND−0,3 a VA+0,3 V. Não equipare limitação de corrente a respeito do limite de tensão. Analise VA off, referências, sobrecarga e transientes, com limites de fabricante e condições explícitas. Se não há garantia de Vf, escolha arquitetura verificável em vez de esconder a lacuna em um modelo genérico.
4. **Mute físico:** ainda inexistente. Precisa atuar na partida e perda de alimentação, com STM desligado, sem depender exclusivamente de firmware. Compare relé, transistor e chave analógica; dimensione realmente a solução escolhida, incluindo tempo de atuação, retenção de carga, bounce/flyback e impacto de áudio conforme aplicável. Não acrescente relé somente por parecer simples.
5. **3V3 e variantes:** WeAct anuncia 1 A total, não livre. Somar consumo real documentado da placa, codec digital até28 mA e reserva UART4 mA. Não converter a reserva antiga350 mA em máximo garantido. Confirmar variante ESP, regulador/header e GPIO16/17 livres; não presumir WROVER compatível.
6. **CW pendente:** respeite a escolha de mantê-lo. O orçamento do conjunto caiu para59,0377 mA e a dissipação proxy conservadora para0,564246 W, contra aproximadamente0,909 A/7,236 W anteriores. Proxy Iq8 mA/thetaJA50 não são dados CW. Não reimponha automaticamente dissipador2°C/W. Explicite o contrato de alimentação/ensaios necessários sem fabricar uma qualificação.

O datasheet Cirrus DS593F2 **não proíbe explicitamente uma ordem VA/VD/VL** e não dá um limite de diferença entre trilhos na tabela absoluta. Não invente essa proibição. Ele exige RST LOW até fontes/MCLK/LRCK estáveis; reset não revoga limites de pinos nem isola sinais.

## Como resolver a dependência entre fases

A missão original exige PASS A antes de B e PASS B antes de C. Não marque um subconjunto PASS e chame isso de aprovação do conjunto. Para fechar A, trate dentro da segurança de alimentação as correções necessárias aos estados desligados, interfaces e reset, mesmo que alterem conexões usadas depois pelo estágio analógico. Justifique cada mudança nesse escopo. Não declare que B foi concluída por antecipação.

Se uma mudança realmente exigir quebrar a ordem dos gates, proponha a redefinição explícita com o problema e a correção concreta; não a presuma nem rode a auditoria com critérios enfraquecidos. A pergunta anterior do Codex foi encerrada pelo usuário em favor deste handoff, não respondida com autorização para um falso PASS.

Implemente, calcule, simule e peça revisão independente das correções de A. Somente após seu fechamento real avance para desempenho/proteção/mute B e, depois, a validação final C. Se houver informação externa indispensável, descreva exatamente a lacuna e a contenção física possível; não repita investigações já concluídas.

## Ferramentas e reprodução

Na raiz, `sh docs/hardware/rev4_10/run_A.sh` recompõe o candidato e reexecuta os testes da etapa. Sucesso do comando não é PASS A; o log informa BLOCKED.

- Python: `/home/rodrigues/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
- KiCad: `/home/rodrigues/.cache/pedaleira-tools/root/usr/bin/kicad-cli`, versão10.0.8.
- `LD_LIBRARY_PATH=/home/rodrigues/.cache/pedaleira-tools/root/usr/lib64`.
- ngspice47 no mesmo `usr/bin`. Restaurado, mas não houve nova simulação ADC/mute nesta etapa.
- RPMs e bibliotecas extraídos ficam em `/home/rodrigues/.cache/pedaleira-tools/`; não baixar tudo novamente se já disponível.
- Poppler `pdftoppm` disponível para renderização. Fontes nos caminhos do gerador.
- Aviso de schema API no prefixo global do KiCad permanece registrado; não impediu ERC/XML. Não esconda erros reais com exclusões.

Fonte do modelo: `prepare_model.py` usa a errata4.9, preserva os valores e aplica somente as alterações A. PDF e KiCad compartilham `layout_connected.py`. Edite a fonte, não somente o PDF ou somente o CAD gerado. O exportador usa UUIDs determinísticos e o PDF tem geração invariável. Faça a BOM/conexões, scripts, simulações e relatórios acompanharem a mudança.

## Critérios de entrega

Preservar originais e firmware, registrar checkpoints Git por fase e revisar cada decisão com evidência. Usar agentes independentes, se disponíveis, ou papéis sequenciais com revisão adversarial explícita. Não permitir múltiplos autores editando o CAD ao mesmo tempo.

Entregar `output/REV410_ENTREGA/` com todos os relatórios exigidos na missão, esquemático/PDF limpo, projeto KiCad editável, BOM, conexões, netlist, ERC, scripts, logs, simulações e manifesto SHA256. Não criar arquivos vazios/fictícios para completar a lista. Não reutilizar teste4.9 como se fosse teste4.10. Falhas SPICE e incertezas devem permanecer registradas.

A auditoria deve tentar reprovar sua solução: todas as combinações de fontes, ordens, perdas abruptas, parasitas pelos GPIO/ADC, reset, mute, limites térmicos e discrepâncias entre documentação/CAD. Só publique a aprovação documental máxima quando não restar bloqueio crítico documental; ensaios físicos futuros continuam condicionantes, nunca resultados inventados.

O usuário pediu salvar todo o trabalho quando a cota restante chegar a10%. Monitore se houver ferramenta confiável e faça checkpoints frequentes; não use créditos de reset ou compras. Se o percentual não estiver disponível, declare isso e salve continuamente. Ao parar, deixe relatório de retomada, arquivos íntegros e veredito verdadeiro.
