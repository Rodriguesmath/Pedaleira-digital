# Testes de bancada — revisão 4.9

Autoria: Rodrigues M. Lima. **Nenhuma etapa foi executada fisicamente. Estado: NÃO APROVADO — REQUER CORREÇÕES.** Este roteiro permite qualificar subconjuntos; não autoriza energizar o codec sem passar pelos testes de alimentação. Registrar instrumento, data, temperatura, tensão/corrente, captura e resultado em cada etapa.

Material: multímetro, fonte isolada regulada de 12 V com limitação de corrente, carga eletrônica ou resistores de potência, osciloscópio com ponta ×10 e mola de GND, gerador de sinais e analisador lógico. Áudio externo desconectado/mutado durante partida e desligamento. Confirmar aterramento de proteção e referência do instrumento; não prender a garra de GND a VREF_OP, ADC_BIAS ou saída de regulador.

## 1. Inspeção visual, sem energia

Conferir orientação e encapsulamento de U2 TSSOP-28 e TL072 DIP-8. Confirmar pino 1 pela marca do CI e orientação do adaptador, não pelo desenho genérico de um módulo. Comparar todas as ilhas ao CSV de conexões. Conferir D1, D8, clamps e polaridade de C5/C33/C37/C38/C40 e reservas. C2/C16/C10/C11 são bipolares. Conferir inscrição real do CW7805, fabricante e pinagem antes de soldar. Se não for possível identificar a peça, parar na qualificação isolada do regulador.

Aprovar somente sem pontes, soldas frias, filamentos, inversões ou fios sem isolamento junto de outros terminais. Não instalar TL072 nem conectar as placas/codec nesta fase. Manter o adaptador CS4272 removível.

## 2. Curtos e continuidade

Com capacitores descarregados, verificar GND em todos os retornos, inclusive U2/8 e /21 e TL072/4. Verificar que VREF_OP, ADC_BIAS e VCOM NÃO têm continuidade direta entre si nem com +5V/+RAW. Continuidade entre fontes só através dos componentes previstos. Conferir que +5V dos dois módulos são ramais da mesma fonte, sem outro USB energizado.

Não usar um número fixo de resistência para condenar um circuito com capacitores: aguardar a carga do ohmímetro e comparar às redes resistivas. Curto persistente próximo de zero entre qualquer rail e GND é reprovação. Todos os 11 TP devem ser rastreados até o nó indicado no esquema.

## 3. Fonte e proteção sem CIs sensíveis

Testar primeiro a fonte externa desconectada: 11,4..12,6 V DC, centro positivo e isolamento apropriado. Montar J1/F1/D1/C33 com carga fictícia; começar com limite de 50 mA. TP1 deve acompanhar a entrada menos a queda de D1. Envelope de projeto de +RAW: 10,5..12,3 V sob as hipóteses de corrente/diodo do relatório. Medir queda real e dissipação de D1 em correntes maiores depois.

Testar inversão de polaridade apenas nesse subconjunto, com fonte limitada a 20 mA e sem regulador/placas/codec: não deve haver tensão negativa relevante a jusante de D1. Reprovar aquecimento, corrente inesperada, fusível que abre sem motivo ou tensão fora da faixa. Proteção contra inversão não protege contra fonte de tensão excessiva.

## 4. CW7805 isolado, identificação e térmica

Confirmar orientação e pinagem por documentação do fabricante real; a pinagem usual 7805 no desenho é condicional. Conferir TAB antes do chassi. Instalar dissipador ≤2 °C/W com interface térmica. C21/C22 devem estar próximos de IN/OUT e GND, C37 conforme esquema e D8 com ânodo na saída.

Sem placas/codec, começar pelo bleeder R21: TP2 deve ficar preferencialmente 4,85..5,15 V e obrigatoriamente 4,75..5,25 V. Ensaiar 50 mA, 200 mA e 600 mA, aguardando temperatura estabilizar. Usar carga/potência adequadas: 10 Ω a 5 V dissipa 2,5 W; usar resistor ≥10 W. Picos próximos de 0,92 A devem ser feitos com carga eletrônica ou banco apropriado, não com fio em curto.

Medir ripple com ponta curta, limites operacionais de entrada e degraus de carga. Critérios: sem oscilação sustentada; +5V não deve sair de 4,75..5,25 V; estimativa conservadora de Tj<100 °C no pior ambiente de projeto. Medir case e estimar Tj com parâmetros reais; se θJC não estiver identificado, o teste não encerra a pendência de especificação. Não aceitar “não está quente ao toque” como medição. Se não sustentar a carga, interromper e revisar a fonte digital — não ligar as placas mesmo assim.

## 5. Todas as alimentações com placas, ainda sem CS4272

Conectar os módulos um por vez, sem VBUS USB paralelo. WeAct 5 V em P1.2; ESP VIN/5V somente se confirmado no modelo real. Limite de corrente progressivo conforme consumo observado. ESP recebe ramal próprio do CW, não passa pelo header de potência da STM32.

Conferir TP2 nos conectores e nos pontos reservados a VA20 do codec: obrigatório 4,75..5,25 V, alvo 4,85..5,15 V. TP3 e pontos reservados a VD9/VL10: alvo 3,2..3,4 V; VD nunca abaixo de 3,1 V; VL deve permanecer compatível com lógica 3,3 V. Testar ESP em transmissão Wi-Fi e STM32 sob carga real quando disponíveis. Orçamento de ~0,91 A é hipótese; registrar consumo verdadeiro e reavaliar se ultrapassado.

**Não conectar/energizar CS4272 antes de confirmar tensões, polaridades e ausência de surtos nesses três pinos.** A existência do conversor onboard não prova reserva ou ruído suficiente.

## 6. Referências DC, sem áudio

Antes dos TL072, verificar TP4≈0,5×TP1 e TP11≈0,48×TP2. Aguardar ≥5 s; com capacitores de tolerância extrema, confirmar o assentamento no escopo. A razão OP sem carga excessiva deve estar entre 0,495 e 0,505; razão ADC entre aproximadamente 0,4795 e 0,4805, antes das cargas/leakage reais.

VCOM TP5 só pode ser testado após a etapa de instalação controlada do codec, quando VA/VD/VL já estiverem aprovadas. VCOM é típico 0,48×VA, sem limites min/max garantidos no datasheet. Verificar |TP11−TP5|≤50 mV e pinos AIN em ADC_BIAS±20 mV sem sinal; caso contrário, interromper e rever bias/leakage/peça. Nunca injetar VREF_OP no TP5 nem usar TP5 como saída de alimentação.

## 7. TL072 e proteção ADC, antes de ligar os pinos AIN reais

Instalar os TL072 identificados; conferir pinos 8=+RAW e 4=GND. Verificar DC nas quatro saídas: todas próximas de VREF_OP, sem saturação ou oscilação. Modelar primeiro o ADC com carga diferencial fictícia 37 kΩ e clamps conforme esquema, sem CS4272.

Aplicar 1 kHz inicialmente 50 mVpk e depois 0,5 Vpk. U1A≈+1, U3A≈+1 e U3B≈−1 em torno de VREF_OP. Em 0,5 Vpk, TP7/TP8 devem oscilar aproximadamente 2,4±0,46 V, em oposição. Escala exata depende da carga, bias, tolerâncias e gerador. Ganho diferencial esperado perto de 1,82 V/V; rejeitar cortes assimétricos, comportamento inversor inesperado ou recuperação lenta de saturação.

Verificar 20 Hz/1 kHz/20 kHz e ondas quadradas de pequena amplitude. Em quadrada/RF, usar banda suficiente para procurar oscilação e ringing; critério de projeto: sem oscilação sustentada, sem crescimento do ringing, sobre-elevação <20% após remover artefatos de medição. Não equiparar resposta ideal em ngspice à margem de fase real.

Medir partida/desligamento e religamento rápido, com a carga fictícia: AIN deve ficar entre −0,3 V e VA+0,3 V durante a sequência real; corrente de clamp deve ter margem em relação a 10 mA. Reprovar qualquer excursão acima desses limites, inclusive enquanto VA cai. Os BAT85 do fabricante comprado precisam ser testados; modelo aproximado não é certificado de proteção. Se falhar, rever proteção/sequenciamento antes de conectar o codec.

## 8. Clocks, com reset do codec mantido LOW

O firmware entregue mantém o transporte bloqueado: SAI4/PLL3/BDMA ainda têm de ser implementados. Não liberar /RST apenas mudando uma constante. Após implementar, verificar MCLK 12,288 MHz, LRCK 48 kHz e BCLK 3,072 MHz, coerentes e sem pulsos indevidos. Meta inicial de frequência: erro <100 ppm medido, registrando erro do instrumento/cristal.

I2S: dois slots de 32 bits com 24 válidos, MSB um BCLK após transição LRCK, LRCK baixo=canal A, dados amostrados na subida. RX SAI4B síncrono internamente ao TX A. Verificar AFs e ausência de conflitos onboard; usar BDMA requests 15/16 e SRAM4/D3, conforme projeto de firmware a implementar. Reprovar ringing que cruze limites de entrada do codec; se precisar de resistores série de clock, acrescentá-los formalmente à revisão.

## 9. Instalação e inicialização controlada do CS4272

Somente depois de 1–8 aprovados, desligar e descarregar, conectar o adaptador CS4272, reenergizar com limite de corrente compatível e monitorar VA/VD/VL/AIN. O teste sem efeitos não autoriza pular a validação do regulador.

Sequência a implementar/medir: manter /RST LOW; rails, bias e clocks estáveis; esperar ≥5 s para referências; liberar /RST; escrever 07h=03h dentro de 10 ms (alvo <5 ms); carregar 01h=01h, 02h=00h, 03h=39h, 04h/05h=FFh, 06h=14h; ler de volta os registradores; escrever 07h=02h; aguardar a sequência interna (~85 µs nominal) e estabilização observada. Identificação do chip em 08h deve ser registrada, não presumida. I2C 7 bits=0x10, HAL usa 0x20.

ADC B fica mutado; XTI em GND e XTO em NC; AOUTB/MUTEC em NC. Se não houver clocks ou qualquer tensão falhar, permanecer em reset/mute. Não ligar saídas DAC diretamente entre si ou ao GND.

## 10. Áudio sem efeitos

Implementar primeiro transporte de zeros e contadores de erro; testar UART sem afetar deadlines. Só então liberar DAC mute com rampa e sinal pequeno. Encaminhar ADC A ao DAC A com ganho digital documentado e B zerado. Rastrear ADC/P10 no escopo.

Ganho físico previsto: entrada→ADC ≈1,82 V/V; DAC diferencial→P10 ≈0,497. Isso não implica ganho fim-a-fim unitário, porque o ganho de conversão ADC/DAC depende das escalas full scale e do volume digital. Calibrar em 1 kHz, não aplicar o antigo critério genérico Vout=Vin sem conversão de escala. Registrar latência; meta <2 ms depende de filtros e buffers. Aprovar somente sem underrun/overrun, DC P10<10 mV estabilizado, ausência de oscilação e sinal sem cortes.

## 11. Efeitos e controles

Testar overdrive, EQ e delay isoladamente, depois juntos. Não há firmware ESP32 implementado: a prova local de UART/CRC não valida Wi-Fi/MQTT.

Overdrive: nível pequeno, harmônicos e controle de drive/tone/level sem wrap digital. EQ: sweep e ganhos 0/±12 dB; registrar curva real, sem presumir que os SVF atendem exatamente à curva ideal. Delay: tempo estável de 20/300/1000 ms, impulso, decaimento, sem estouro de buffer; o máximo efetivo pode ser ligeiramente menor que 1000 ms pela reserva do buffer. SW4 deve zerar o áudio e ter precedência sobre unmute remoto. Chaves dos efeitos precisam conservar o hardware master gate. Comutar e medir transientes, sem apenas escuta subjetiva.

Meta de DSP: <91.667 ciclos por bloco de 32 frames a 550 MHz, medidos por DWT; não confundir benchmark no PC com timing no Cortex-M7. Forçar underrun/overrun e confirmar mute/zeros, contador e recuperação controlada.

## 12. Ruído, THD, carga, partida e desligamento

Carga P10=100 kΩ. Medir FFT/THD+N com equipamento adequado e registrar piso do instrumento; não prometer 114 dB nem 24 bits efetivos. Comparar Wi-Fi ligado/desligado e clock ativo; investigar retorno compartilhado, captador e referência antes de acrescentar peças.

A fonte comum de 5 V pode acoplar corrente do ESP à VA: medir no pino do codec, não só no regulador. Critério de projeto inicial: ripple analógico <5 mVpp em banda de áudio com ponta adequada, sem picos que ultrapassem limites dos rails; valor não é limite de datasheet. Rever arquitetura se ruído/THD não atender ao objetivo medido.

Capturar energização, corte abrupto, religamento e desconexão do jack. A simulação prevê pop de volts em P10; manter amplificador externo em mute/desconectado. Se uso normal exigir silêncio automático, adicionar solução física de mute/desconexão em nova revisão e repetir os testes. **O sistema permanece não aprovado enquanto CW, interface ADC, sequenciamento e transporte não forem qualificados.**
