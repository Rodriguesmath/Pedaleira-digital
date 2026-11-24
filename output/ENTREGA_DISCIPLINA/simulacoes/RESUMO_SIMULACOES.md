# Resumo Consolidado das Simulações Elétricas (SPICE Rev 4.10) e Funcionais (DSP C++17)

Este documento consolida as evidências de simulação da revisão final aprovada do hardware (**Rev 4.10**, Gate A `16/16 PASS` e Gate B `17/17 PASS` em `ngspice`) e da simulação funcional em ponto flutuante dos algoritmos DSP embarcados no STM32H723 (`Fs = 48 kHz`).

---

## 1. Índice dos Gráficos Gerados

| # | Arquivo | Domínio | Objetivo e Escopo |
| :--- | :--- | :--- | :--- |
| 1 | [`sim1_sequenciamento_partida.png`](sim1_sequenciamento_partida.png) | SPICE Rev 4.10A | Sequenciamento de partida (`0–95 ms`), supervisor `+5VA` (`U7`), intertravamento `/RST` (`Q1/Q2`) e contenção `AINA+/AINA-` pós-colapso (`Q4..Q8`). |
| 2 | [`sim2_clamp_ativo_adc.png`](sim2_clamp_ativo_adc.png) | SPICE Rev 4.10B | Comparação **BAT85 vs. Clamp Ativo** (`Q9..Q14`), 4 corners PVT (`0–70 °C`), falta off-state (`±12 V`) e THD na faixa útil. |
| 3 | [`sim3_mute_antipop_plugpull.png`](sim3_mute_antipop_plugpull.png) | SPICE Rev 4.10B | Mute fail-safe a relé `K1` (Omron G5V-1): partida anti-pop (`0–7 s`), zoom de comutação e corte rápido por plug-pull (`U8` UVLO). |
| 4 | [`sim4_bode_cadeia_analogica.png`](sim4_bode_cadeia_analogica.png) | SPICE Rev 4.10B | Diagrama de Bode (magnitude e fase `100 Hz – 10 kHz`) dos estágios `U1A/U3A/U3B/U1B` e margens de headroom (`10.5 V` e `12.6 V`). |
| 5 | [`sim5_dsp_overdrive_eq.png`](sim5_dsp_overdrive_eq.png) | DSP C++17 (`Fs=48 kHz`) | Curva `SoftLimit`, espectro FFT de harmônicos do `DspOverdrive`, formas de onda e curvas do equalizador SVF de 3 bandas (`DspEqualizer`). |
| 6 | [`sim6_dsp_crossfade_antipop.png`](sim6_dsp_crossfade_antipop.png) | DSP C++17 (`Fs=48 kHz`) | Crossfade de potência constante (`cos/sin`) no Master Bypass (`DspCrossfade`) vs. chaveamento abrupto e supressão de clique (`|Δy|`). |

---

## 2. Resultados Elétricos — SPICE Fase A (Rev 4.10A: `16/16 PASS`)

Fonte: [`transient_seq.txt`](../../REV410_ENTREGA/SIMULACOES_A/transient_seq.txt) e [`resumo_A.json`](../../REV410_ENTREGA/SIMULACOES_A/resumo_A.json).

- **Supervisor `+5VA` (`U7` TL431 + `Q3`)**:
  - Limiar de subida (`VA_OK` ON): **`4.6017 V`** | Limiar de queda (`VA_OK` OFF): **`4.5164 V`** | Histerese: **`85.26 mV`**.
  - Tensão `VA_OK` ativa: **`4.9931 V`** (carga adicional em `+5VA`: `1.8188 mA`).
- **Intertravamento `/RST` do Codec (`Q1/Q2`)**:
  - `t = 14 ms` (`+5VA = 0 V`, `PD10 = 3.3 V` prematuro): `/RST = 0.024 V` (**travado em LOW**).
  - `t = 25 ms` (`+5VA = 5.0 V`): `/RST = 3.0 V` | Pulso em `32 ms`: `0.0 V` | Retorno `40 ms`: `3.0 V`.
  - Pós-colapso (`68 ms`, `+5VA = 0 V`): `/RST = 0.024 V`, `SHUNT_EN = 7.3595 V`, `AINA+ = -0.10 mV`, corrente máxima de backpower nos diodos = **`0.011785 µA`**.
  - Reserva `C44` (`V_HOLD`) após queda de `RAW` (`t = 85 ms`): `V_HOLD = 10.754 V`, mantendo `SHUNT_EN = 7.3157 V`.
- **Degrau Rápido (`10 µs`) e Linearidade**:
  - Pico de inrush em `C44`: `250.51 mA` (`AINA+ max = 0.50 mV`).
  - THD diferencial (Fase A): **`0.000514%`** (limite `0.02%`).

---

## 3. Resultados Elétricos — SPICE Fase B (Rev 4.10B: `17/17 PASS`)

Fonte: [`resumo_B.json`](../../REV410_ENTREGA/SIMULACOES_B/resumo_B.json), [`mute_nominal.txt`](../../REV410_ENTREGA/SIMULACOES_B/mute_nominal.txt) e [`analog_chain_gains.txt`](../../REV410_ENTREGA/SIMULACOES_B/analog_chain_gains.txt).

### 3.1 Blocker 3 — Clamp Ativo do ADC (`Q9..Q14`)
- **Comparação BAT85 vs. Clamp Ativo Rev 4.10B**:
  - *Baseline BAT85 (FAIL)*: excursão `[-0.3129 V, +5.2505 V]` — viola o limite inferior `-0.30 V` em `12.9 mV` e injeta **`9.832 mA`** em `+5VA`.
  - *Clamp Ativo Rev 4.10B (PASS)*: excursão contida em **`[+0.3159 V, +4.7416 V]`** (nominal) com **`0.000 mA`** de injeção em `+5VA`.
- **Corners PVT**:
  - `C1 (0 °C, VA=4.75 V, hFE=80)`: `[0.2979, 4.4966] V` (limite `[-0.30, +5.05] V`).
  - `C2 (27 °C, VA=5.00 V, hFE=200)`: `[0.3159, 4.7394] V` (limite `[-0.30, +5.30] V`).
  - `C3 (70 °C, VA=4.75 V, hFE=80)`: `[0.2992, 4.5232] V` (limite `[-0.30, +5.05] V`).
  - `C4 (70 °C, VA=5.25 V, hFE=250)`: `[0.3283, 4.9910] V` (limite `[-0.30, +5.55] V`).
- **Falta Off-State (`±12 V`)**: `+12 V → +30.145 mV` | `-12 V → -30.082 mV` (`I_VA = 0.0 nA`, limite `±50.0 mV`).
- **Linearidade THD**: **`0.000878%`** @ `1.40 Vp (0 dBFS)` e **`0.000096%`** @ `0.50 Vp` (limite `0.01%`).

### 3.2 Blocker 4 — Mute Fail-Safe a Relé `K1`
- **Partida Anti-Pop**: unmute em **`5.899 s`** (janela alvo `[5.6, 6.2] s`), saída durante mute = **`0.0 mV`**, pico de pop na comutação = **`1.2321 mV < 5.0 mV`**.
- **Plug-Pull e Quedas**: fechamento NC em **`8.26 ms`** (`RAW_cut = 9.0 V`, `VA_cut = 5.0 V`, flyback D16 = `12.3 V`, pós-corte = `0.0 mV`). Quedas `/RST` e `VA_OK`: `2.49 ms` e `2.20 ms`. Brownout re-wait: `1.152 s`; corrente bobina @ `10.5 V`: `10.64 mA >= 10.0 mA`.
- **Qualidade de Áudio e Isolação**: ganho @ `20 Hz` (`R6 = 47 kΩ`) = **`-0.0027 dB`** (limite `-0.05 dB`), isolação em mute @ `1 kHz` = **`-185.61 dB`** (limite `-80.0 dB`), THD @ `1 kHz / 1 Vp` = **`0.000066%`**.

### 3.3 Cadeia Analógica (`U1A`, `U3A`, `U3B`, `U1B`)
- **Ganhos nominais (`100 Hz – 10 kHz`)**: `U1A = 1.0000` (`-0.00028 dB`), `U3A = 0.9999` (`-0.00055 dB`), `U3B = -1.0000` (`-0.00036 dB`, fase `179.99°..179.49°`), `U1B = 0.4990` (`-6.0382 dB`).
- **Headroom**: pior caso em `RAW = 10.5 V` com sinal `0 dBFS (1.40 Vp)` apresenta excursão `[3.85 V, 6.65 V]` e margem mínima de **`3.85 V`** aos trilhos (limite `>= 1.50 V`).

---

## 4. Simulação Funcional DSP (`Fs = 48 kHz`, Firmware C++17)

- **Overdrive (`DspOverdrive`)**: saturação polinomial cúbica `SoftLimit` + filtro `DspSvf` Low-Pass (`800 Hz – 10 kHz`). Para entrada `440 Hz / 0.50 Vp` (`Drive = 0.7`), `Tone = 1.0` preserva harmônicos ímpares até `10 kHz` (THD = `39.5%`), enquanto `Tone = 0.25` (`fc = 3.1 kHz`) suaviza os agudos (THD = `34.9%`).
- **Equalizador 3 Bandas (`DspEqualizer`)**: 3 filtros SVF paralelos (`100 Hz` LP, `1 kHz` BP, `4 kHz` HP) com recomposição aditiva; excursão medida de `-14.40 dB` (mid-scoop `-12 dB`) até `+12.08 dB` / `+11.99 dB` (`+12 dB`).
- **Crossfade Anti-Pop (`DspCrossfade`)**: curva de potência constante (`cos/sin`, `gA² + gB² = 1.000`, sem queda de `-3.01 dB`) com rampa de `500` amostras (**`10.42 ms`** @ `48 kHz`), reduzindo o salto amostra-a-amostra `|Δy|` no Master Bypass de `0.3500` (Hard Switch) para `0.0016` (**atenuação de `47.0 dB`**).
