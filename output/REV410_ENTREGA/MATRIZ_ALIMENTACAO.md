# Matriz de alimentação - candidato 4.10A

2026-11-12. S = USB STM; E = USB ESP; A = 12 V. Análise estrutural/combinatória, não simulação de rampas ou medição. `estados.json` conserva a análise do conjunto com J5 fechado para identificar riscos; essa configuração NÃO está liberada. Perfil inicial: J5 aberto, codec removido fisicamente, guitarra e amplificador desconectados, sem outros adaptadores acionando GPIO. J5 sozinho não isola o codec dos drivers RAW ou dos sinais digitais.

|S E A|Trilhos comandados|UART RX STM / RX ESP|Reset/mute e restrições|
|---|---|---|---|
|000|Nenhum; capacitores podem reter carga|indeterminado, receptor OFF / indeterminado, receptor OFF|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|001|RAW, VA_CW_5V|indeterminado, receptor OFF / indeterminado, receptor OFF|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|010|USB_ESP_5V, ESP_3V3|indeterminado, receptor OFF / HIGH após limiar PD e tDO|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|011|USB_ESP_5V, RAW, VA_CW_5V, ESP_3V3|indeterminado, receptor OFF / HIGH após limiar PD e tDO|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|100|USB_STM_5V, STM_3V3, VD_VL_STM|HIGH após limiar PD e tDO / indeterminado, receptor OFF|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|101|USB_STM_5V, RAW, VA_CW_5V, STM_3V3, VD_VL_STM|HIGH após limiar PD e tDO / indeterminado, receptor OFF|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|110|USB_STM_5V, USB_ESP_5V, STM_3V3, ESP_3V3, VD_VL_STM|dados / dados|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|
|111|USB_STM_5V, USB_ESP_5V, RAW, VA_CW_5V, STM_3V3, ESP_3V3, VD_VL_STM|dados / dados|Conjunto não liberado; sem mute físico implementado; codec ausente no perfil inicial|

`VA_CW_5V` na tabela é a saída nominal do estágio CW. Com J5 aberto não há alimentação intencional de +5VA pelo CW. Não se presume ausência de carga residual no lado VA. VD/VL pertencem ao mesmo 3V3 do STM. /RST tem pull-down R13; não há intertravamento automático contra perda de VA quando PD10 estiver HIGH. Firmware entregue mantém transporte de áudio bloqueado; essa condição não substitui a proteção elétrica.

Foram enumeradas as 24 transições dirigidas de mudança de uma fonte e as seis ordens de chegada a111 em `VALIDACAO_A/transicoes.json` e `calculos.json`. Desligamentos são os caminhos inversos dessas ordens. Nenhuma transição do conjunto está declarada fisicamente segura. Cortes/retornos de VA podem manter carga em C2/C16/C40; reset não desconecta AIN. O mute de saída continua pendente na fase B.

UART U6: sinais e alimentação de cada lado pertencem à própria placa. O cruzamento de dados ocorre por barreira capacitiva, sem ligação DC de sinal entre USBs. Durante brownout a lógica é indeterminada; o default HIGH só vale nas condições PU/PD do fabricante. RX desligado é indeterminado, não Hi-Z garantido. Nenhum positivo USB se liga ao CW ou ao positivo da outra USB.

GND é comum. Usar retornos digitais separados do retorno analógico até o ponto de referência; nunca VREF_OP como retorno. Duas USBs não dão isolamento galvânico ao sistema. A compatibilidade dos terras de hosts/fontes e instrumentos precisa ser verificada antes do futuro ensaio; não levantar terra de proteção.
