# Condições de futuros ensaios - não executados

GateA integralBLOCKED. Este roteiro prepara subconjuntos, não autoriza montar/energizar a pedaleira completa.

1. Conferir variante das placas, headers e compatibilidade de GND/fontes USB/instrumentos. Não usarVREF_OP como terra.
2. Manter J5 SEM shunt, codec REMOVIDO, guitarra/jack de saída e outros adaptadores de sinal desconectados. Confirmar continuidade e ausência de pontes de5V.
3. Identificar IN/GND/OUT/TAB do CW antes de qualquer alimentação; a ordem numérica no candidato é hipótese. Caracterizar a fonte isolada com carga artificial e limitação de corrente; não atribuir especificaçõesST nem executar curtoIN-OUT.
4. Somar consumo de toda a WeAct (sem acessórios opcionais),28 mA do codec e reserva de 4 mA do lado UART. Critério de projeto:3,2..3,4V no codec,VD>=3,1V e margem de corrente total a definir/medir.1 A total não é corrente livre.
5. Adquirir ISO7721DR genuíno (sem sufixo F), adaptador SOIC-8 / DIP-8 e passivos locais. Testar UART em oito estados e 24 transições, incluindo rampas lentas/cortes, sinalRX/capacitância/overshoot. Timing de datasheet usaCL = 15 pF; capacitância real/sonda deve ser incluída.
6. Não instalar codec nem fechar J5 para áudio enquanto alimentação, reset/partida, proteçãoADC e mute não tiverem gate correspondente. Proteção BAT85 e pop continuam achados críticos conhecidos.
7. Repetir futuramente os ensaios analógicos da auditoria4.9 com carga artificial >=100 kΩ, sinais limitados, mediçõesAIN/VA/VCOM/ADC_BIAS e mute físico definido. Não conectar amplificador/fones para observar transientes exploratórios.

Não há resultados físicos anexos. ngspice foi restaurado, mas não foi executada simulaçãoSPICE de uma correçãoB nesta fase. Nenhum resultado antigo foi reapresentado como teste da4.10.
