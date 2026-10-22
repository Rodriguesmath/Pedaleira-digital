# Documentação de Hardware

![Status](https://img.shields.io/badge/Status-em%20desenvolvimento-yellow?style=flat-square)
![Hardware](https://img.shields.io/badge/Hardware-STM32H723VG%20%7C%20ESP32%20%7C%20CS4272-blue?style=flat-square)

## Sobre

Esta seção reúne as especificações de hardware, esquemáticos de condicionamento analógico, mapeamento de pinagem (*pinout*), diagramas de interconexão e lista de materiais (*Bill of Materials* - BOM) para o protótipo de bancada da **Pedaleira Digital**.

---

## Documentos Técnicos Disponíveis

- [**Guia Prático para Criação do Esquemático no EasyEDA Web**](./guia_esquematico_easyeda.md):
  - Passo a passo para montar o esquemático no EasyEDA Web sem instalar nada.
  - Tabela completa de códigos de componentes **LCSC** (footprints Through-Hole para protoboard).
  - Tabela de NetLabels para interconexão pino a pino limpa sem emaranhado de fios.
  - Link interativo do **Simulador Falstad** com o circuito analógico operando.
- [**Mapeamento de Pinout, Conexões e Lista de Materiais (BOM de Bancada)**](./pinout_e_bom.md):
  - Diagrama em blocos da interconexão entre placas e circuitos.
  - Tabela completa de pinagem do **STM32H723VGT6 (LQFP100)**: barramentos SAI/I2S, I2C de controle, UART serial e GPIOs de chaves e LEDs.
  - Tabela de pinagem do **Codec Cirrus Logic CS4272** e do **ESP32 DevKit V1**.
  - Circuito de condicionamento analógico: buffer de entrada Hi-Z ($Z_{in} \approx 1\text{ M}\Omega$) com amp-op TL072 e filtro ativo/passivo de reconstrução de saída com conectores Jack P10.
  - Levantamento orçamentário detalhado com estimativa de custos em Reais (BRL) e fornecedores locais.
  - Justificativas técnicas de seleção de cada componente conforme as diretrizes do IFPB.

---

## Arquitetura de Hardware Resumida

| Subsistema | Componente Principal | Interface com DSP | Papel no Sistema |
| :--- | :--- | :--- | :--- |
| **Núcleo DSP** | STM32H723VGT6 (ARM Cortex-M7 @ 550MHz) | Core central | Processamento de áudio em tempo real, DMA circular e controle de efeitos |
| **Codec de Áudio** | Cirrus Logic CS4272 | SAI1 (I2S) + I2C1 | Conversão analógico-digital (ADC) e digital-analógica (DAC) de 24 bits / 48 kHz |
| **Condicionamento** | TL072 / NE5532 | Analógica (1 Vrms) | Buffer de alta impedância na entrada e filtro passa-baixas anti-aliasing na saída |
| **Conectividade IoT** | ESP32 DevKit V1 | UART3 (115200 baud) | Ponte Wi-Fi / MQTT e recepção de comandos do aplicativo |
| **Controle Físico** | Chaves de alavanca com retenção | GPIOs (Pull-Up) | Acionamento físico comutado dos efeitos (Overdrive, EQ, Delay, Mute) |
| **Sinalização** | LEDs difusos com resistor limitador | GPIOs Push-Pull | Indicação luminosa de efeito ativo e status operacional |

---

## Próximas Entregas de Hardware

- [ ] Montagem do buffer Hi-Z e filtro de reconstrução em protoboard ([Issue #10](https://github.com/Rodriguesmath/Pedaleira-digital/issues/10)).
- [ ] Validação experimental com osciloscópio, gerador de funções e medição de ruído de bancada ([Issue #11](https://github.com/Rodriguesmath/Pedaleira-digital/issues/11)).
- [ ] Teste de leitura das chaves mecânicas com debounce e acionamento de LEDs ([Issue #15](https://github.com/Rodriguesmath/Pedaleira-digital/issues/15)).
- [ ] Montagem definitiva em placa perfurada/ilhada e acomodação em gabinete protótipo ([Issue #18](https://github.com/Rodriguesmath/Pedaleira-digital/issues/18) e [Issue #19](https://github.com/Rodriguesmath/Pedaleira-digital/issues/19)).
