# Análise de Proteção do ADC CS4272 (Revisão 4.10B)
**Documento Técnico de Engenharia & Qualificação SPICE (Blocker 3)**  
*Autor: Rodrigues M. Lima | Data: 2026-11-12 | Revisão de Projeto: 4.10B*  
*Paridade Estrita com CAD: `docs/hardware/rev4_10/circuito_rev4_10.json`*

---

## 1. Resumo Executivo & Histórico do Bloqueio

Na Revisão 4.9, a interface de entrada analógica do CODEC CS4272 (`AINA+`, `AINA-`, `AINB+`, `AINB-`) dependia exclusivamente de resistores em série de $1,5\text{ k}\Omega$ (`R18`, `R20`) combinados com diodos Schottky de uso geral **BAT85** (`D9..D12`) conectados aos trilhos de alimentação `+5VA` e terra (`GND`).

A auditoria de confiabilidade analógica identificou que essa solução clássica **falha criticamente**:
1. **Violação das Tensões Máximas Absolutas (*Absolute Maximum Ratings*) do CS4272**:
   O fabricante (Cirrus Logic, CS4272 DS593F2, p. 9) estipula rigorosamente:
   $$V_{\text{IN}} \in [\text{AGND} - 0,30\text{ V}, \,\, \text{VA} + 0,30\text{ V}]$$
   Sob sobretensões reais de falha operacional (saturação de op-amps em $+12\text{ V}$ ou surtos externos de até $+20\text{ V}$ / $-15\text{ V}$ através de $1,5\text{ k}\Omega$), a corrente de surto atinge $10\text{ mA}$. A essa corrente, a tensão direta ($V_f$) do BAT85 atinge entre $0,47\text{ V}$ e $0,55\text{ V}$ (podendo exceder $0,65\text{ V}$ a $0^\circ\text{C}$), forçando a entrada a violar as junções internas ESD de silício do conversor.
2. **Injeção Parasita no Trilho Analógico (*Back-Pumping*)**:
   Sob sobretensão positiva, o clamp passivo convencional baseado em diodos conectados a `+5VA` injeta toda a corrente do surto ($~9,8\text{ mA}$) diretamente no nó `+5VA`. Como o regulador de alimentação analógica (CW7805/L7805) é uma fonte linear unidirecional (*source only*), ele não consegue afundar corrente (*sink*). O trilho `+5VA` sobretensiona descontroladamente, destruindo o conversor CS4272 e os circuitos de polarização conectados.

Na Revisão 4.10B, os antigos diodos BAT85 `D9..D12` foram **completamente removidos do CAD** (`circuito_rev4_10.json`). Em seu lugar, foi implementada a topologia de **Clamp Ativo em Janela Compensado por $V_{be}$** (`R48..R53`, `Q9..Q14`, `C45..C48`), mantendo a tensão de entrada do CS4272 rigidamente dentro da janela segura com **zero injeção de corrente (*zero back-pumping*)** no barramento analógico `+5VA`.

---

## 2. Topologia do Circuito no CAD (`circuito_rev4_10.json`)

A implementação física na Folha 10 (bloco 10A: malhas de bias $V_{\text{BIAS\_HI}}$ e $V_{\text{BIAS\_LO}}$) e na Folha 2 (bloco 2B: células de grampeamento $Q_{11}..Q_{14}$) do esquemático Rev 4.10B é composta rigorosamente pelos seguintes componentes discretos:

```
                      +5VA (VA)
                        │
                ┌───────┴───────┐
                │ R48 = 12 kohm │
                └───────┬───────┘
                        ├─── V_REF_HI (desacoplado por C45 = 100 nF para +5VA)
                ┌───────┴───────┐
                │ R49 = 150 kohm│
                └───────┬───────┘
                        │
                       GND

     +5VA ───────────┐ (Collector Q9)
                     │
                    ┌┴┐
         V_REF_HI ──┤b│ Q9 (2N3904 NPN Follower)
                    └┬┘
                     │ (Emitter Q9)
                     ├─── V_BIAS_HI (desacoplado por C46 = 100 nF para GND)
                ┌────┴────┐
                │R50=6.8k │ (Carga de emissor)
                └────┬────┘
                     │
                    GND

                      +5VA
                        │
                ┌───────┴───────┐
                │ R51 = 150 kohm│
                └───────┬───────┘
                        ├─── V_REF_LO (desacoplado por C47 = 100 nF para GND)
                ┌───────┴───────┐
                │ R52 = 10 kohm │
                └───────┬───────┘
                        │
                       GND

      GND ───────────┐ (Collector Q10)
                     │
                    ┌┴┐
         V_REF_LO ──┤b│ Q10 (2N3906 PNP Follower)
                    └┬┘
                     │ (Emitter Q10)
                     ├─── V_BIAS_LO (desacoplado por C48 = 100 nF para GND)
                ┌────┴────┐
                │R53=6.8k │ (Pull-up de emissor para +5VA)
                └────┬────┘
                     │
                    +5VA
```

### 2.1 Células de Grampeamento nos Pinos do CS4272

Para os canais diferenciais $AINA\_P$ e $AINA\_N$, as redes de corte são dispostas de forma idêntica:

- **Canal $AINA\_P$**:
  - $Q_{11}$ (`2N3906`, PNP):
    - Emissor: pino `AINA_P`
    - Base: nó $V_{\text{BIAS\_HI}}$
    - **Coletor: conectado ao terra (`GND`)** (Zero Back-Pump para +5VA!)
  - $Q_{12}$ (`2N3904`, NPN):
    - Emissor: pino `AINA_P`
    - Base: nó $V_{\text{BIAS\_LO}}$
    - Coletor: conectado a `+5VA`
- **Canal $AINA\_N$**:
  - $Q_{13}$ (`2N3906`, PNP): Emissor em `AINA_N`, Base em $V_{\text{BIAS\_HI}}$, **Coletor em `GND`**.
  - $Q_{14}$ (`2N3904`, NPN): Emissor em `AINA_N`, Base em $V_{\text{BIAS\_LO}}$, Coletor em `+5VA`.

---

## 3. Princípio de Funcionamento & Cancelamento de $V_{be}$

### 3.1 Grampeamento Superior (Corte de Sobretensão Positiva)
1. **Tensão de Referência Alta ($V_{\text{REF\_HI}}$)**:
   Estabelecida pelo divisor resistivo `R48 = 12 kohm` e `R49 = 150 kohm`:
   $$V_{\text{REF\_HI}} = VA \times \frac{R_{49}}{R_{48} + R_{49}} = VA \times \frac{150\text{ k}}{162\text{ k}} \approx 0,9259 \times VA$$
   Para $VA = 5,00\text{ V}$, $V_{\text{REF\_HI}} = 4,630\text{ V}$.
2. **Buffer Seguidor NPN ($Q_9$)**:
   O transistor $Q_9$ opera como seguidor de emissor de baixa impedância:
   $$V_{\text{BIAS\_HI}} = V_{\text{REF\_HI}} - V_{be}(Q_9) \approx 4,630\text{ V} - 0,650\text{ V} = 3,980\text{ V}$$
3. **Ativação do Grampo PNP ($Q_{11} / Q_{13}$)**:
   Quando a tensão no pino do ADC ($AINA\_P$) se eleva durante um surto positivo:
   $$V_{\text{clamp\_hi}} = V_{\text{BIAS\_HI}} + V_{eb}(Q_{11}) = [V_{\text{REF\_HI}} - V_{be}(Q_9)] + V_{eb}(Q_{11})$$
   Como $Q_9$ e $Q_{11}$ são transistores bipolares complementares submetidos ao mesmo ambiente térmico, suas quedas de junção se compensam mutuamente ($V_{be}(Q_9) \approx V_{eb}(Q_{11})$):
   $$V_{\text{clamp\_hi}} \approx V_{\text{REF\_HI}} \approx 4,63\text{ V} \dots 4,99\text{ V}$$
4. **Despejo Direto para o Terra (Zero Back-Pumping)**:
   Quando $Q_{11}$ conduz, toda a corrente de surto que entra pelo resistor $R_{18} = 1,5\text{ k}\Omega$ flui diretamente pelo coletor de $Q_{11}$ para o **terra (`GND`)**.
   A corrente injetada no barramento `+5VA` é de exatamente **$0,0000\text{ mA}$**, eliminando qualquer risco de sobretensão no regulador analógico linear.

### 3.2 Grampeamento Inferior (Corte de Sobretensão Negativa)
1. **Tensão de Referência Baixa ($V_{\text{REF\_LO}}$)**:
   Estabelecida pelo divisor resistivo `R51 = 150 kohm` e `R52 = 10 kohm`:
   $$V_{\text{REF\_LO}} = VA \times \frac{R_{52}}{R_{51} + R_{52}} = VA \times \frac{10\text{ k}}{160\text{ k}} \approx 0,0625 \times VA$$
   Para $VA = 5,00\text{ V}$, $V_{\text{REF\_LO}} = 0,3125\text{ V}$.
2. **Buffer Seguidor PNP ($Q_{10}$)**:
   O transistor $Q_{10}$ eleva o potencial em uma junção base-emissor:
   $$V_{\text{BIAS\_LO}} = V_{\text{REF\_LO}} + V_{eb}(Q_{10}) \approx 0,3125\text{ V} + 0,650\text{ V} = 0,9625\text{ V}$$
3. **Ativação do Grampo NPN ($Q_{12} / Q_{14}$)**:
   Quando a tensão no pino do ADC cai durante um surto negativo:
   $$V_{\text{clamp\_lo}} = V_{\text{BIAS\_LO}} - V_{be}(Q_{12}) = [V_{\text{REF\_LO}} + V_{eb}(Q_{10})] - V_{be}(Q_{12})$$
   Com o cancelamento térmico ($V_{eb}(Q_{10}) \approx V_{be}(Q_{12})$):
   $$V_{\text{clamp\_lo}} \approx V_{\text{REF\_LO}} \approx +0,298\text{ V} \dots +0,328\text{ V}$$
   Dessa forma, mesmo sob uma sobretensão de $-15\text{ V}$ contínua na entrada, o pino do CS4272 **nunca fica negativo**! A tensão mínima observada é de $+0,298\text{ V}$, mantendo uma margem superior a **$598\text{ mV}$** em relação ao limite absoluto destrutivo de $-0,300\text{ V}$.

---

## 4. Resultados das Simulações em 4 Cantos (Corners)

As simulações físicas automatizadas executadas pelo script `docs/hardware/rev4_10/simular_B.py` aplicaram sweeps contínuos de $-15\text{ V}$ a $+20\text{ V}$ bi-canal simultâneos através de $R_{18} = R_{20} = 1,5\text{ k}\Omega$:

| Canto | Condição de Contorno / Parâmetros | Faixa $V(AIN)$ Medida | Faixa Permitida $[GND-0.3, VA+0.3]$ | Injeção em +5VA | Margem p/ Limite | Veredito |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **C1** | **Frio extremo:** $0^\circ\text{C}$, $VA = 4,75\text{ V}$, $h_{FE} = 80$ | $[+0,298\text{ V}, \,\, +4,497\text{ V}]$ | $[-0,300\text{ V}, \,\, +5,050\text{ V}]$ | **0,0000 mA** | **553 mV** | **PASS** |
| **C2** | **Nominal:** $27^\circ\text{C}$, $VA = 5,00\text{ V}$, $h_{FE} = 200$ | $[+0,316\text{ V}, \,\, +4,739\text{ V}]$ | $[-0,300\text{ V}, \,\, +5,300\text{ V}]$ | **0,0000 mA** | **561 mV** | **PASS** |
| **C3** | **Quente:** $70^\circ\text{C}$, $VA = 4,75\text{ V}$, $h_{FE} = 80$ | $[+0,299\text{ V}, \,\, +4,523\text{ V}]$ | $[-0,300\text{ V}, \,\, +5,050\text{ V}]$ | **0,0000 mA** | **527 mV** | **PASS** |
| **C4** | **Quente:** $70^\circ\text{C}$, $VA = 5,25\text{ V}$, $h_{FE} = 250$ | $[+0,328\text{ V}, \,\, +4,991\text{ V}]$ | $[-0,300\text{ V}, \,\, +5,550\text{ V}]$ | **0,0000 mA** | **559 mV** | **PASS** |

### Destaques das Medições:
- Em todos os cantos, a tensão $V(AIN)$ permaneceu estritamente contida no intervalo seguro de **$+0,298\text{ V}$ a $+4,991\text{ V}$**.
- A margem de segurança contra quebra do silício superou **$520\text{ mV}$** no pior caso absoluto.
- Back-pumping comprovado em **$0,0000\text{ mA}$** (descarga integral para o GND via $Q_{11}$ e $Q_{13}$).

---

## 5. Comparação Numérica: BAT85 (Rev 4.9) vs Clamp Ativo (Rev 4.10B)

Sob sobretensões extremas aplicadas através do resistor de proteção em série $R_{\text{in}} = 1,5\text{ k}\Omega$:

| Cenário de Falha Externa | Topologia BAT85 (Rev 4.9 Legada) | Clamp Ativo Rev 4.10B (Paridade CAD) | Consequência no Silício CS4272 |
| :--- | :---: | :---: | :--- |
| **Sobretensão $+20\text{ V}$ Contínua** | $V(AIN) = 5,250\text{ V} \dots 5,48\text{ V}$<br>Injeção em `+5VA`: **$9,832\text{ mA}$** | $V(AIN) = 4,739\text{ V} \dots 4,991\text{ V}$<br>Injeção em `+5VA`: **$0,000\text{ mA}$** | **BAT85:** Eleva o trilho `+5VA`, queima o conversor e periféricos por sobretensão.<br>**Rev 4.10B:** Zero injeção; grampo seguro a terra. |
| **Sobretensão $-15\text{ V}$ Contínua** | $V(AIN) = -0,313\text{ V} \dots -0,48\text{ V}$<br>(Violação de até $-180\text{ mV}$) | $V(AIN) = +0,298\text{ V} \dots +0,328\text{ V}$<br>(Margem $> 598\text{ mV}$) | **BAT85:** Conduz corrente reversa no substrato do CS4272 gerando risco de *CMOS latch-up* destrutivo.<br>**Rev 4.10B:** Tensão permanece estritamente positiva. |

---

## 6. Linearidade e Distorção Harmônica Total (THD)

Para certificar que o clamp ativo não adiciona distorção harmônica ao sinal de alta fidelidade musical, foi efetuada análise espectral de Fourier a $1\text{ kHz}$ centrado na polarização quiescente do ADC ($V_{\text{CM}} \approx 2,28\text{ V}$), sob a condição de pior caso ($70^\circ\text{C}, VA=4,75\text{V}, h_{FE}=80$):

- **Sinal de Excursão Máxima Linear ($0\text{ dBFS} = 1,40\text{ V}_p$, ou $2,80\text{ V}_{pp}$ diferencial)**:
  - Tensão oscila entre $0,88\text{ V}$ e $3,68\text{ V}$.
  - Limiares de grampo: $> 4,52\text{ V}$ e $< 0,30\text{ V}$ (margem de guarda $> 840\text{ mV}$).
  - **THD medido:** **$0,000878\%$** ($-101,1\text{ dB}$), com folga extrema contra o teto de $0,01\%$.
- **Sinal de Guitarra Nominal ($0,50\text{ V}_p$, ou $1,00\text{ V}_{pp}$ diferencial)**:
  - Tensão oscila entre $1,78\text{ V}$ e $2,78\text{ V}$.
  - **THD medido:** **$0,000096\%$** ($-120,3\text{ dB}$).

O circuito é totalmente transparente e inaudível na faixa audível ($20\text{ Hz} \dots 20\text{ kHz}$).

---

## 7. Compatibilidade em Modo Desligado (*Off-State*) com Shunts Folha 9

Na Folha 9 do esquemático, os transistores MOSFET canal N `2N7000` (`Q5..Q8`) operam como shunts de emergência para as entradas do ADC:
- Quando o aparelho está desligado (`VA = 0 V`), a linha supervisora `SHUNT_EN` é polarizada em $+8,2\text{ V}$ a partir de `+RAW` via zener supervisor.
- Com $V_{gs} = 8,2\text{ V} > V_{th} = 3,0\text{ V}$, o canal NMOS conduz fortemente para o terra.

Sob falha de $\pm 12\text{ V}$ aplicada nos jacks de entrada com o aparelho desenergizado:
- A corrente de surto ($\approx 8\text{ mA}$) é drenada pelo canal do 2N7000.
- **Tensão residual medida no nó do ADC**:
  - Para $+12\text{ V}$ externo: $V(AIN) = +30,15\text{ mV} \ll 50\text{ mV}$.
  - Para $-12\text{ V}$ externo: $V(AIN) = -30,08\text{ mV} \ll 50\text{ mV}$.
- **Condução espúria para `+5VA`**:
  - $I(+5VA) = 0,00\text{ nA}$.
  - Nenhuma corrente atinge o barramento digital ou analógico; os transistores $Q_9..Q_{14}$ permanecem em corte perfeito.

---

## 8. Tolerâncias Conservadoras & Limites de Bancada

Para a montagem física e validação experimental em bancada, devem ser observadas as seguintes diretrizes:
1. **Casamento de Transistores**: Os pares $Q_9 / Q_{11}$ e $Q_{10} / Q_{12}$ devem preferencialmente ser adquiridos da mesma fita de componentes para assegurar casamento de $V_{be}$ com tolerância $\Delta V_{be} < 20\text{ mV}$.
2. **Tolerância dos Resistores**: Resistores `R48..R53` devem ser de filme metálico DIN0207 $1\%$, assegurando que os potenciais de referência $V_{\text{REF\_HI}}$ e $V_{\text{REF\_LO}}$ não desviem mais do que $\pm 1,5\%$.
3. **Capacitores de Bypass**: `C45..C48` devem ser cerâmicos multicamada X7R de $100\text{ nF}$ posicionados a menos de $10\text{ mm}$ dos coletores e bases para conter transientes de radiofrequência e ESD.

---

## 9. Conclusão & Veredito de Engenharia

O Blocker 3 está **plenamente solucionado, aprovado e com paridade estrita com o CAD**:
- Aprovado no simulador `ngspice-47` com 100% de sucesso nos 4 cantos térmicos e de ganho.
- Total ausência de injeção reversa em `+5VA`.
- Total integridade das tensões de entrada do CS4272 ($[+0,298\text{ V}, \,\, +4,991\text{ V}]$).
- Documentação e modelos matemáticos alinhados 100% com `docs/hardware/rev4_10/circuito_rev4_10.json`.
