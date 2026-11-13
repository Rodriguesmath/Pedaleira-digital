# Projeto de Mute Físico Fail-Safe (Revisão 4.10B)
**Documento Técnico de Engenharia & Qualificação SPICE (Blocker 4)**  
*Autor: Rodrigues M. Lima | Data: 2026-11-12 | Revisão de Projeto: 4.10B*  
*Paridade Estrita com CAD: `docs/hardware/rev4_10/circuito_rev4_10.json`*

---

## 1. Resumo Executivo & Histórico do Bloqueio

Na Revisão 4.9, a saída de áudio do conector Jack (`JACK_OUT`) não possuía nenhum mecanismo eletromecânico ou físico de corte de sinal. O circuito dependia exclusivamente de rotinas de inicialização por software no firmware do microcontrolador STM32 e de shunts analógicos que ficavam inoperantes com a alimentação desenergizada.

Esse arranjo apresentava vulnerabilidades graves:
1. **Transientes Violentos de Energização (*Power-On Pop / Thump*)**:
   Durante os primeiros segundos após a energização da fonte, os amplificadores operacionais (`TL072`) e os conversores (`CS4272`) estabelecem suas referências DC quiescentes. O capacitor de acoplamento de referência `C38` ($470\mu\text{F}$) da malha $V_{\text{REF\_OP}}$ leva centenas de milissegundos para carregar, gerando um degrau de tensão transitório de até $\pm 6\text{ V}$ na saída analógica se o circuito não estiver rigidamente aterrado.
2. **Pops de Desconexão Abrupta (*Power-Off Pop / Plug-Pull*)**:
   Ao desconectar a fonte de alimentação ($12\text{ V}$) ou em caso de perda repentina de energia da rede elétrica, os barramentos de alimentação colapsam antes que o microcontrolador consiga registrar a interrupção e comandar um mute por software.
3. **Vulnerabilidade em Estado Desenergizado**:
   Com o pedal desligado da tomada, ruídos externos ou cargas eletrostáticas acumuladas podiam ser transferidos diretamente para a cadeia de amplificação de potência.

Para a Revisão 4.10B, foi projetado e homologado em SPICE um sistema autônomo de **Mute Físico Eletromecânico Fail-Safe** centrado no relé miniatura **Omron G5V-1-DC12** (`K1`), resistor de terminação de saída $R_6 = 47\text{ k}\Omega$, supervisor analógico de subtensão `U8 TL431ACZ`, lógica discreta de 3 entradas (`Q17..Q19`), circuito de corte instantâneo e descarga rápida (*fast-dump* com `Q16` e `Q22`), e temporizador anti-pop com gatilho Schmitt (`D17 BZX55C4V7`, `Q20`, `Q21`).

---

## 2. Análise Comparativa de Tecnologias de Mute

Antes de definir a arquitetura eletromecânica, foram avaliadas três tecnologias concorrentes de silenciamento de áudio:

| Critério de Engenharia | Relé Eletromecânico (Omron G5V-1-DC12) | Shunt MOSFET Discreto (ex: 2N7000 / BSS138) | Chave Analógica CMOS Bilateral (ex: CD4066 / TS5A) | Shunt JFET (ex: 2N5457 / J201) |
| :--- | :---: | :---: | :---: | :---: |
| **Estado Totalmente Desenergizado ($V_{\text{in}} = 0\text{ V}$)** | **MUDO GARANTIDO (Contato NC aterrado fisicamente por mola mecânica)** | **FALHA (Canal aberto $V_{gs}=0$, transiente vaza integralmente)** | **FALHA (Substrato flutuante, diodos ESD conduzem transiente)** | Mudo parcial (requer tensão de pinch-off negativa ausente) |
| **Comportamento no Desligamento Abrupto** | **Corte eletrônico em $< 1\mu\text{s}$; Contato NC fecha em $< 10\text{ ms}$** | Lento; $V_{gs}$ drena lentamente, liberando pop na queda | Indeterminado quando $V_{dd}$ cruza $2\text{ V}$ | Condução linear reversa distorce o transiente |
| **Distorção Harmônica Total (THD) no Sinal** | **$0,000000\%$ (Contato metálico puro Au-clad Ag)** | $0,05\%$ a $0,2\%$ (não-linearidade de $R_{ds(on)}$ com tensão) | $0,01\%$ a $0,08\%$ (modulação de $R_{on}$ por $V_{\text{sig}}$) | $0,03\%$ a $0,1\%$ (modulação de canal JFET) |
| **Isolação em Mute ($1\text{ kHz}$)** | **$> 180\text{ dB}$ (Aterramento galvânico direto)** | $\sim 40\text{ dB}$ a $55\text{ dB}$ ($R_{on} \sim 2\text{ a }5\,\Omega$) | $\sim 50\text{ dB}$ a $65\text{ dB}$ | $\sim 45\text{ dB}$ |
| **Resistência em Série ao Sinal Ativo** | **$0,05\,\Omega$ (Imperceptível)** | N/A (como shunt) ou $5\text{ a }10\,\Omega$ | $10\text{ a }50\,\Omega$ (adiciona ruído térmico) | N/A |
| **Consumo de Corrente em Regime Ativo** | $10,6\text{ mA} \dots 12,5\text{ mA}$ ($120\text{ a }150\text{ mW}$) | $< 1\mu\text{A}$ | $< 50\mu\text{A}$ | $< 100\mu\text{A}$ |

### 2.1 Por que os Semicondutores Falham no Mute Fail-Safe:
- **MOSFET de intensificação (Canal N)**: Para conduzir e aterrar a saída em mute, o MOSFET necessita de $V_{gs} > V_{th}$ ($1,5\text{ V}$ a $3,0\text{ V}$). Quando a alimentação principal é desconectada, $V_{gs}$ cai para $0\text{ V}$, desligando o canal e deixando o conector de saída completamente aberto no exato momento em que os capacitores de acoplamento dos op-amps estão descarregando.
- **JFET de depleção**: Embora conduza com $V_{gs} = 0\text{ V}$, a sua resistência de canal ($R_{ds} \sim 100\,\Omega$) não fornece aterramento ideal contra cargas de $100\text{ k}\Omega$ (atenuação limitada a $\sim 40\text{ dB}$). Ademais, para desmutar e liberar o áudio, exige uma tensão de gate estritamente **negativa** ($-3\text{ V}$ a $-5\text{ V}$), ausente na arquitetura de alimentação simples da pedaleira.
- **Relé Eletromecânico Form C (SPDT)**: A mola mecânica interna mantém o polo conectado fisicamente ao contato Normalmente Fechado (**NC**, conectado diretamente ao terra `GND`) em qualquer condição desenergizada. O contato Normalmente Aberto (**NO**, que conecta a linha de áudio `OUT_PRE`) possui isolação dielétrica por entreferro de ar, com capacitância residual inferior a $0,5\text{ pF}$.

---

## 3. Topologia e Paridade com o CAD (`circuito_rev4_10.json`)

O circuito de mute físico foi integrado nas Folhas 4 (bloco 4B: `C5`, `R6`, `K1`, `D16`), 9 (supervisor `VA_OK`) e 10 (blocos 10B e 10C: UVLO de `+RAW`, porta AND, temporizador `C49` e driver de `K1`) do esquemático Rev 4.10B com os seguintes componentes:

```
  +RAW ──► [R54=27k] ──┬──► [U8 TL431] ──► [Q15 2N3906] ──► RAW_OK (Folha 10)
                       │
                     [R55=10k]
                       │
                      GND

  +5VA ──► [R33=9.1k] ──┬──► [U7 TL431] ──► [Q3 2N3906]  ──► VA_OK  (Folha 9)
                        │
                      [R34=11k]
                        │
                       GND

  STM32 Firmware ──────────────────────────────────────────► CODEC_RST (3.3V)

                                 +RAW
                                   │
                             [R62 = 47 kohm]
                                   │
  FAULT_GATE ──────────────────────┴───────────────────────────────────────┐
      ▲                                                                    │
      │                                                                    ▼
     ┌┴┐                                                              [Q16 2N3904]
     │ │ Q19 (Base: RAW_OK via R67=22k / R75=2.2k)                     (Descarga C49
     └┬┘                                                                via R73=47R)
      ├── Q19_E                                                            │
     ┌┴┐                                                                   ▼
     │ │ Q18 (Base: CODEC_RST via R66=100k)                           [Q22 2N3904]
     └┬┘                                                               (Corta Q20_B
      ├── Q18_E                                                         em < 1 us!)
     ┌┴┐
     │ │ Q17 (Base: VA_OK via R65=47k)
     └┬┘
      │
     GND (3-Input Series AND Gate)

                                  RAW_OK
                                     │
                              [R60 = 33 kohm]
                                     │
  MUTE_ARM ──────────────────────────┴──┬──────────────────────────────────┐
      │                                 │                                  │
  [C49 = 47 uF]                  [D17 = BZX55C4V7]                   [R73 = 47 ohm]
      │                                 │                                  │
     GND                              Q20_Z                             [Q16 Dump]
                                        │
                                 [R68 = 10 kohm]
                                        │
                                        ├─── Q20_B (Histerese R71=1.5M de K1_COILP)
                                        │          (Pull-down R69=33k para GND)
                                       ┌┴┐         (Inibição por Q22 para GND)
                                       │ │ Q20 (2N3904)
                                       └┬┘
                                        │ (Q20_C com R70=10k para +RAW)
                                        │
                                 [R72 = 4.7 kohm]
                                        │
                                       ┌┴┐
                               +RAW ───┤ │ Q21 (2N3906 Driver PNP)
                                       └┬┘
                                        │ (K1_COILP)
                                        ├───► [Bobina K1 Omron G5V-1] (960 ohm)
                                        │     [D16 1N4148 Flyback para GND]
                                        └───► [R71 = 1.5 Mohm Feedback Histerese]
```

### 3.1 Lista Verificada de Componentes no CAD

| Ref | Valor Nominal | Encapsulamento | Função de Projeto Conforme `circuito_rev4_10.json` |
| :---: | :---: | :---: | :--- |
| **K1** | `G5V-1-DC12` | DIP-6 / THT | Relé eletromecânico miniatura Form C SPDT de mute fail-safe na saída |
| **D16** | `1N4148` | DO-35 | Diodo flyback supressor de sobretensão reversa na bobina do relé |
| **D17** | `BZX55C4V7` | DO-35 | Diodo zener de $4,7\text{ V}$ para deslocamento de limiar do temporizador |
| **U8** | `TL431ACZ` | TO-92 | Comparador shunt de precisão ($2,495\text{ V}$, $0,5\%$) para UVLO de `+RAW` |
| **C49** | `47 uF` | Radial $\phi 5\text{ mm}$ | Capacitor eletrolítico de temporização anti-pop na energização |
| **C5** | `10 uF` | Radial $\phi 5\text{ mm}$ | Acoplamento AC de saída de áudio (positivo em `LP2`) |
| **R6** | `47 kohm` | Axial DIN0207 | Resistor de descarga e terminação do conector Jack de saída (`OUT_PRE`) |
| **R54** | `27 kohm` | Axial DIN0207 | Divisor superior do supervisor UVLO de `+RAW` |
| **R55** | `10 kohm` | Axial DIN0207 | Divisor inferior do supervisor UVLO de `+RAW` |
| **R56** | `1.0 kohm` | Axial DIN0207 | Resistor pull-up base-emissor anti-fuga de $Q_{15}$ |
| **R57** | `2.7 kohm` | Axial DIN0207 | Limitador de corrente de base de $Q_{15}$ e catodo de $U_8$ |
| **R58** | `2.2 kohm` | Axial DIN0207 | Resistor pull-down de carga na linha `RAW_OK` |
| **R59** | `1.0 Mohm` | Axial DIN0207 | Histerese positiva do comparador UVLO de `+RAW` ($\sim 280\text{ mV}$) |
| **R60** | `33 kohm` | Axial DIN0207 | Resistor de carga do temporizador anti-pop ($\tau \approx 1,55\text{ s}$) |
| **R62** | `47 kohm` | Axial DIN0207 | Resistor pull-up de `FAULT_GATE` para `+RAW` |
| **R65** | `47 kohm` | Axial DIN0207 | Limitador de corrente de base de $Q_{17}$ a partir de `VA_OK` |
| **R66** | `100 kohm` | Axial DIN0207 | Limitador de corrente de base de $Q_{18}$ a partir de `CODEC_RST` |
| **R67** | `22 kohm` | Axial DIN0207 | Divisor superior de polarização de base de $Q_{19}$ |
| **R75** | `2.2 kohm` | Axial DIN0207 | Divisor inferior de polarização de base de $Q_{19}$ |
| **R68** | `10 kohm` | Axial DIN0207 | Limitador de corrente de base do estágio Schmitt $Q_{20}$ |
| **R69** | `33 kohm` | Axial DIN0207 | Resistor pull-down de base de $Q_{20}$ |
| **R70** | `10 kohm` | Axial DIN0207 | Carga de coletor de $Q_{20}$ |
| **R71** | `1.5 Mohm` | Axial DIN0207 | Resistor de histerese positiva do Schmitt trigger do relé |
| **R72** | `4.7 kohm` | Axial DIN0207 | Limitador de corrente de base do driver de bobina $Q_{21}$ |
| **R73** | `47 ohm` | Axial DIN0207 | Limitador de corrente de descarga rápida de $C_{49}$ por $Q_{16}$ |
| **R74** | `10 kohm` | Axial DIN0207 | Limitador de corrente de base da chave de corte rápido $Q_{22}$ |
| **Q15, Q21** | `2N3906` | TO-92 | Transistores PNP: $Q_{15}$ chave de `RAW_OK`; $Q_{21}$ driver de alta corrente da bobina |
| **Q16..Q20, Q22** | `2N3904` | TO-92 | Transistores NPN: $Q_{16}$ dump de $C_{49}$; $Q_{17..19}$ AND 3-entradas; $Q_{20}$ Schmitt; $Q_{22}$ cut |

---

## 4. Detalhamento e Dimensionamento dos Subcircuitos

### 4.1 Resistor de Terminação de Saída $R_6 = 47\text{ k}\Omega$
Na Revisão 4.9, o resistor de referência de terra de saída era de $1\text{ M}\Omega$. Um valor tão alto exigia mais de 10 segundos para descarregar o capacitor de acoplamento `C5` ($10\mu\text{F}$) e aumentava a suscetibilidade a ruído eletrostático.

Na Revisão 4.10B, adotou-se $R_6 = 47\text{ k}\Omega$:
- **Constante de Tempo ($\tau$)**:
  $$\tau = R_6 \times C_5 = 47\text{ k}\Omega \times 10\mu\text{F} = 0,470\text{ s}$$
- **Frequência de Corte de Passa-Altas ($f_c$) com Carga de Linha ($R_{\text{load}} = 100\text{ k}\Omega$)**:
  $$R_{\text{eq}} = R_6 \parallel R_{\text{load}} = \frac{47\text{ k} \times 100\text{ k}}{47\text{ k} + 100\text{ k}} \approx 31,97\text{ k}\Omega$$
  $$f_c = \frac{1}{2\pi \times R_{\text{eq}} \times C_5} = \frac{1}{2\pi \times 31970 \times 10 \times 10^{-6}} \approx 0,498\text{ Hz} \approx 0,50\text{ Hz}$$
- **Atenuação em $20\text{ Hz}$**:
  $$|H(j\omega)| = \frac{1}{\sqrt{1 + (0,498 / 20)^2}} \approx 0,99969 \implies \text{Ganho}(20\text{ Hz}) = -0,0027\text{ dB}$$
  A perda de apenas **$-0,0027\text{ dB}$** é completamente inaudível e atende amplamente o limite de projeto ($> -0,05\text{ dB}$).

### 4.2 Supervisor de Subtensão Antecipado UVLO de `+RAW` (Folha 10)
- Monitora a tensão bruta não-regulada `+RAW` antes que o regulador linear $5\text{ V}$ (`CW7805`) perca regulação.
- Divisor `R54 = 27k` e `R55 = 10k` com histerese $R_{59} = 1,0\text{ M}\Omega$:
  $$V_{\text{raw\_trip\_rise}} = 2,495\text{ V} \times \left(1 + \frac{27\text{ k}}{10\text{ k}}\right) \approx 9,23\text{ V}$$
  $$V_{\text{raw\_trip\_fall}} \approx 8,95\text{ V}$$
- Quando a fonte é desligada da tomada (*plug-pull*), a linha `RAW_OK` desliga enquanto `RAW` ainda está em $\approx 9,00\text{ V}$, momento em que a alimentação analógica `+5VA` ainda está **plenamente estável em $5,00\text{ V}$**.

### 4.3 Porta AND de 3 Entradas & Mecanismo Fast-Dump com $Q_{16}$ e $Q_{22}$
- A porta lógica AND é formada por $Q_{17}$, $Q_{18}$ e $Q_{19}$ em série (*stack*).
- Condição de liberação: `RAW_OK` ativo ($> 8,95\text{ V}$), `VA_OK` ativo ($> 4,52\text{ V}$) e `CODEC_RST` ativo ($3,3\text{ V}$ liberado pelo firmware após $5,02\text{ s}$).
- **Comportamento em Falha**: Se qualquer das três condições falhar por apenas $1\mu\text{s}$, a pilha de transistores corta. O resistor de pull-up $R_{62} = 47\text{ k}\Omega$ puxa o nó `FAULT_GATE` para `+RAW`, ativando instantaneamente:
  1. $Q_{22}$ via $R_{74} = 10\text{ k}\Omega$: aterra a base $Q_{20\_B}$, **cortando a corrente da bobina do relé em menos de $1\mu\text{s}$**!
  2. $Q_{16}$ via limitador $R_{73} = 47\,\Omega$: drena integralmente a carga acumulada em $C_{49}$ ($47\mu\text{F}$) para $< 0,05\text{ V}$ em menos de $3\text{ ms}$, forçando o temporizador a reiniciar um ciclo completo de espera anti-pop na recuperação.

### 4.4 Temporizador Anti-Pop & Schmitt Trigger Não-Inversor
- Após a liberação da porta AND, o resistor $R_{60} = 33\text{ k}\Omega$ carrega $C_{49} = 47\mu\text{F}$ a partir de `RAW_OK` ($\approx 12\text{ V}$).
- O diodo zener $D_{17}$ (`BZX55C4V7`) desloca o limiar de condução da base de $Q_{20}$ em $4,7\text{ V}$.
- Somente quando $V(C_{49})$ atinge $\approx 6,3\text{ V}$, o transistor $Q_{20}$ comuta, acionando o driver PNP $Q_{21}$ e energizando a bobina do relé $K_1$.
- Isso gera um atraso reproduzível de **$5,899\text{ segundos}$** na partida fria, permitindo que a referência $V_{\text{REF\_OP}}$ ($C_{38} = 470\mu\text{F}$), o conversor CS4272 e os filtros digitais atinjam regime estacionário perfeito antes do relé fechar.

---

## 5. Resultados Numéricos das Simulações Físicas SPICE

As simulações físicas foram validadas no motor `ngspice-47` através da suíte automatizada `docs/hardware/rev4_10/simular_B.py`, com dados consolidados em `output/REV410_ENTREGA/SIMULACOES_B/resumo_B.json`:

### 5.1 Teste 5: Partida Nominal e Desconexão Abrupta (*Plug-Pull*)

| Parâmetro Físico Avaliado | Valor Medido em SPICE | Limite de Projeto | Veredito |
| :--- | :---: | :---: | :---: |
| **Instante de Desmute na Partida ($t_{\text{unmute}}$)** | **$5,899\text{ s}$** | $5,60\text{ s} \le t \le 6,20\text{ s}$ ($\sim 5,9\text{ s}$) | **PASS** |
| **Tensão Residual no Jack durante Mute ($t < 5,8\text{ s}$)** | **$0,0000\text{ mV}$** | $< 0,01\text{ mV}$ (Zero absoluto) | **PASS** |
| **Pico de Pop no Instante do Desmute** | **$1,2321\text{ mV}$** | $< 5,0\text{ mV}$ | **PASS** |
| **Tensão $RAW$ no Corte da Bobina pós Plug-Pull ($6,5\text{ s}$)** | **$9,00\text{ V}$** | $\ge 8,50\text{ V}$ | **PASS** |
| **Tensão $VA$ no Momento do Corte (Regulador Intacto)** | **$5,00\text{ V}$** | $\ge 4,90\text{ V}$ | **PASS** |
| **Tempo de Fechamento do Contato NC de Mute** | **$8,26\text{ ms}$** | $< 10,0\text{ ms}$ | **PASS** |
| **Tensão no Jack após Fechamento NC** | **$0,0000\text{ mV}$** | $< 2,0\text{ mV}$ | **PASS** |
| **Pico de Sobretensão de Flyback na Bobina** | **$12,30\text{ V}$** | $< 15,0\text{ V}$ (Limitado por $D_{16}$) | **PASS** |

### 5.2 Teste 6: Subtensão ($10,5\text{ V}$) e Brownout Dip ($8,2\text{ V}$, $300\text{ ms}$)

| Parâmetro Físico Avaliado | Valor Medido em SPICE | Limite de Projeto | Veredito |
| :--- | :---: | :---: | :---: |
| **Corrente na Bobina sob Tensão Mínima ($10,5\text{ V}$)** | **$10,64\text{ mA}$** | $\ge 10,0\text{ mA}$ (Retenção mecânica garantida) | **PASS** |
| **Tensão de Contato durante Brownout Dip ($8,2\text{ V}$)** | **$0,0000\text{ V}$** | $< 0,1\text{ V}$ (Relé silenciado) | **PASS** |
| **Descarga de $C_{49}$ durante o Dip** | **$4,0\text{ mV}$** | $< 100\text{ mV}$ (Drenagem completa por $Q_{16}$) | **PASS** |
| **Tempo de Re-espera Anti-Pop pós Recuperação** | **$1,152\text{ s}$** | $0,70\text{ s} \le t \le 1,30\text{ s}$ ($\sim 1,0\text{ s}$) | **PASS** |

### 5.3 Teste 7: Mute Imediato por Quedas de Reset e Tensão Analógica

| Parâmetro Físico Avaliado | Valor Medido em SPICE | Limite de Projeto | Veredito |
| :--- | :---: | :---: | :---: |
| **Tempo de Mute por Queda de `CODEC_RST`** | **$2,49\text{ ms}$** | $< 5,0\text{ ms}$ | **PASS** |
| **Drenagem de $C_{49}$ pós Queda de Reset** | **$27,2\text{ mV}$** | $< 100\text{ mV}$ | **PASS** |
| **Tempo de Mute por Glitch em `VA_OK`** | **$2,20\text{ ms}$** | $< 5,0\text{ ms}$ | **PASS** |
| **Drenagem de $C_{49}$ pós Glitch em `VA_OK`** | **$27,2\text{ mV}$** | $< 100\text{ mV}$ | **PASS** |

### 5.4 Teste 8: Qualidade de Áudio, Isolação e Transparência Acústica

| Parâmetro Físico Avaliado | Valor Medido em SPICE | Limite de Projeto | Veredito |
| :--- | :---: | :---: | :---: |
| **Ganho a $20\text{ Hz}$ com $R_6 = 47\text{ k}\Omega \parallel 100\text{ k}\Omega$** | **$-0,0027\text{ dB}$** | $> -0,050\text{ dB}$ | **PASS** |
| **Ganho a $20\text{ Hz}$ com $R_6 = 1\text{ M}\Omega \parallel 100\text{ k}\Omega$ (Referência 4.9)** | $-0,0003\text{ dB}$ | N/A | Informativo |
| **Atenuação no Jack em Mute ($1\text{ kHz}$)** | **$-185,61\text{ dB}$** | $< -80,0\text{ dB}$ | **PASS** |
| **THD em Condução ($1\text{ V}_p$ @ $1\text{ kHz}$)** | **$0,000066\%$** | $< 0,010\%$ | **PASS** |

---

## 6. Tolerâncias Conservadoras & Limites de Bancada

Para assegurar a reprodutibilidade na fabricação física da placa e validação experimental em bancada:
1. **Dinâmica Mecânica do Relé Omron G5V-1-DC12**:
   - Tempo de atuação nominal (*operate time*): máximo $5\text{ ms}$ (típico $2,5\text{ ms}$).
   - Tempo de liberação mecânica (*release time*): máximo $5\text{ ms}$ (típico $1\text{ ms}$).
   - Repique de contatos (*contact bounce*): típico $1,5\text{ ms}$. Durante os ensaios de bancada, a inspeção em osciloscópio na transição de mute deve confirmar ausência de picos induzidos superiores a $5\text{ mV}$.
2. **Dispersão do Diodo Zener $D_{17}$ (`BZX55C4V7`)**:
   - Faixa de tensão Zener admissível: $4,4\text{ V} \le V_z \le 5,0\text{ V}$ ($\pm 5\%$).
   - Essa variação altera o tempo de desmute inicial em no máximo $\pm 180\text{ ms}$, mantendo a liberação com folga segura dentro da janela especificada de $5,6\text{ s}$ a $6,2\text{ s}$.
3. **Tolerância do Capacitor Eletrolítico $C_{49}$ ($47\mu\text{F}$)**:
   - Capacitores eletrolíticos de alumínio comuns apresentam tolerância de $\pm 20\%$. Mesmo no pior caso de capacitância máxima ($56,4\mu\text{F}$), o desmute ocorre antes de $6,3\text{ s}$, garantindo perfeita integridade sonora.
4. **Resistores de Precisão**:
   - Os divisores $R_{54} / R_{55}$ (supervisor $RAW$) e $R_{33} / R_{34}$ (supervisor $VA$) devem utilizar resistores de filme metálico com tolerância estrita de $1\%$ para garantir que os limiares de UVLO não variem mais de $\pm 100\text{ mV}$.

---

## 7. Conclusão & Veredito de Engenharia

O Blocker 4 está **plenamente solucionado, aprovado e com paridade estrita com o CAD**:
- O relé eletromecânico Omron G5V-1-DC12 mantém o pico de transiente no desmute em `1,2321 mV` (`< 5 mV`), desconectando a carga em caso de corte de energia enquanto a alimentação do conversor ainda está intacta (`RAW = 9,00 V`, `VA = 5,00 V`).
- O tempo de atuação em falhas transitórias é inferior a $2,5\text{ ms}$, com drenagem completa do temporizador por $Q_{16}$.
- Todos os 38 componentes requeridos batem 100% com `docs/hardware/rev4_10/circuito_rev4_10.json`.
- A transparência sonora atinge nível audiófilo ($\text{THD} = 0,000066\%$, Ganho $20\text{ Hz} = -0,0027\text{ dB}$, Isolação em Mute $= -185,61\text{ dB}$).
