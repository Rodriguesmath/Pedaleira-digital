# Matriz de alimentação - Fase 4.10A (Gate A Projeto PASS)

2026-11-12. S = USB STM; E = USB ESP; A = 12 V. Combina os 8 estados estruturais (`estados.json`), 24 transições dirigidas (`transicoes.json`) e 16 cenários ngspice da Fase A (`SIMULACOES_A/resumo_A.json`). O perfil inicial físico em bancada segue exigindo `J5` aberto e `U2` ausente até qualificação presencial da amostra `CW7805`, inspeção `WeAct/ESP32` e conclusão das Fases B/C.

|S E A|Trilhos comandados|UART RX STM / RX ESP|Reset/conteção AIN F9 e pendências B|
|---|---|---|---|
|000|Nenhum; capacitores podem reter carga|indeterminado, receptor OFF / indeterminado, receptor OFF|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|001|RAW, VA_CW_5V|indeterminado, receptor OFF / indeterminado, receptor OFF|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|010|USB_ESP_5V, ESP_3V3|indeterminado, receptor OFF / HIGH após limiar PD e tDO|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|011|USB_ESP_5V, RAW, VA_CW_5V, ESP_3V3|indeterminado, receptor OFF / HIGH após limiar PD e tDO|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|100|USB_STM_5V, STM_3V3, VD_VL_STM|HIGH após limiar PD e tDO / indeterminado, receptor OFF|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|101|USB_STM_5V, RAW, VA_CW_5V, STM_3V3, VD_VL_STM|HIGH após limiar PD e tDO / indeterminado, receptor OFF|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|110|USB_STM_5V, USB_ESP_5V, STM_3V3, ESP_3V3, VD_VL_STM|dados / dados|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|
|111|USB_STM_5V, USB_ESP_5V, RAW, VA_CW_5V, STM_3V3, ESP_3V3, VD_VL_STM|dados / dados|Intertravamento /RST e contenção AIN sem-VA implementados na F9; mute físico e clamps ativos na Fase B|

`VA_CW_5V` na tabela é a saída nominal do estágio CW. Com `J5` aberto não há alimentação intencional de `+5VA` pelo CW. `VD/VL` pertencem a `+3V3_STM`. Na Folha 9, o supervisor `U7/Q3` + intertravamento `Q1/Q2/R39..R41` força `CODEC_RST <= 0,1 V` sempre que `+5VA < 4,52 V`, mesmo com `PD10` HIGH ou durante queda de `+5VA`, sem backpower para `+3V3_STM` quando STM estiver desligado. Adicionalmente, `D15/R43/C44/R44..R47/Q4..Q8` acionam os shunts NMOS off-state mantendo `AINA_P`, `AINA_N`, `ADC_BIAS` e `AINB_CM` contidos próximos de `GND` (`<= 2 mV` em SPICE Fase A) sempre que `+5VA < 4,52 V` e houver tensão em `+RAW` ou carga retida em `C44` (`10 uF`). A substituição ativa de `D9..D12` (`BAT85`) sob `+5VA` ativo em sobrecarga/surto e o mute físico de saída pertencem à Fase B.

UART `U6`: sinais e alimentação de cada lado pertencem à própria placa (`ISO7721DR`, SOIC-8). Durante brownout a lógica é indeterminada; o default HIGH só vale nas condições PU/PD do fabricante. Nenhum positivo USB se liga ao CW ou ao positivo da outra USB.

GND é comum. Usar retornos digitais separados do retorno analógico até o ponto de referência; nunca `VREF_OP` como retorno. A compatibilidade dos terras de hosts/fontes e instrumentos precisa ser conferida fisicamente antes de ensaio em bancada.
