---
name: stm32-baremetal-qa
description: Procedimentos de Quality Gate (QA), compilacao nativa C++17 no Linux (g++ sem toolchain cruzada), medicao de timing com DWT Cycle Counter no Cortex-M7 e roteiro experimental de bancada para pedais DSP.
---

# STM32 Bare-Metal QA & Benchmarking (ASSERT Standard)

Este guia estabelece os procedimentos rigorosos de Quality Gate, compilacao estatica sem toolchain cruzada no Linux host, perfilamento de timing com registradores DWT no Cortex-M7 e procedimentos de bancada experimental para o firmware da **Pedaleira Digital**.

---

## 1. Verificacao Local e Compilacao Nativa no Linux Host

Para assegurar ciclos de feedback ultra-rapidos (< 1s) sem dependencia de instalacao do `arm-none-eabi-gcc` na maquina de CI/CD ou estacao de desenvolvimento, todo o codigo C++ do STM32 pode ser sintaticamente e semanticamente validado usando `g++` nativo do Linux com os headers CMSIS/HAL presentes no repositorio.

### 1.1. Comando de Compilacao C++17 com Checagem Estrita
```bash
g++ -std=c++17 -fsyntax-only \
  -Wall -Wextra -Werror -Wno-unused-parameter \
  -DSTM32H723xx -DUSE_HAL_DRIVER \
  -Ifirmware/stm32/Core/Inc \
  -Ifirmware/stm32/Drivers/STM32H7xx_HAL_Driver/Inc \
  -Ifirmware/stm32/Drivers/STM32H7xx_HAL_Driver/Inc/Legacy \
  -Ifirmware/stm32/Drivers/CMSIS/Device/ST/STM32H7xx/Include \
  -Ifirmware/stm32/Drivers/CMSIS/Include \
  firmware/stm32/Core/Src/*.cpp
```

### 1.2. Execucao do Quality Gate Automatizado em Python
O repositorio possui uma suite deterministica em [`tests/test_stm32_cpp_dsp_quality.py`](file:///home/rodrigues/Pedaleira-digital/tests/test_stm32_cpp_dsp_quality.py):

```bash
python3 -m unittest tests/test_stm32_cpp_dsp_quality.py -v
```

A suite executa automaticamente:
1. **Existencia de Arquivos do Escopo Delimitado**.
2. **ASCII 7-bit Puro**: Bloqueia caracteres acentuados ou especiais (norma Assert).
3. **Ausencia de TABs**: Espacos exclusivamente (4 espacos por indentacao).
4. **Formatacao Allman**: Chaves de abertura `{` isoladas em linha dedicada.
5. **Proibicao de Blocos Single-Line**: Reprova `if(...) do();` ou `else do();`.
6. **Banners de Secao**: Exige estrutura formal de cabecalho em `.hpp` e `.cpp`.
7. **Compilacao C++17 com `g++`**: Valida todos os arquivos `.cpp`.
8. **Vetores CRC-8 CCITT**: Testa coerencia do protocolo inter-MCU.
9. **Autoria em Ordem Alfabetica**: `@author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus`.

---

## 2. Validacao de Timing Budget e Perfilamento DWT no Cortex-M7

No STM32H723VGT6 operando a **550 MHz**, cada nanossegundo conta para evitar quebras de buffer de audio (underruns de DMA):

### 2.1. Calculo do Orcamento Temporal
- **Clock da CPU ($f_{cpu}$)**: $550\text{ MHz} \rightarrow 1\text{ ciclo} \approx 1{,}818\text{ ns}$.
- **Frequencia de Amostragem ($f_s$)**: $48\text{ kHz} \rightarrow T_s = 20{,}833\text{ µs}$.
- **Ciclos por Amostra**: $550.000.000 / 48.000 \approx \mathbf{11.458\text{ ciclos}}$.
- **Bloco de DMA Ping-Pong (ex.: 32 amostras estéreo)**:
  - Janela total de processamento: $32 \times 20{,}833\text{ µs} \approx \mathbf{666{,}6\text{ µs}}$.
  - Orcamento total de ciclos por bloco: $\mathbf{366.666\text{ ciclos}}$.
- **Limite de Carga (Headroom)**: A cadeia total de DSP nunca deve exceder **25% de uso de CPU** (< 2.864 ciclos/amostra ou < 91.666 ciclos por bloco de 32 amostras).

### 2.2. Perfilamento com o Registrador DWT (Data Watchpoint and Trace)
O Cortex-M7 possui um contador de ciclos de hardware embutido de 32 bits (`DWT->CYCCNT`) que roda na frequencia maxima do nucleo (550 MHz) sem qualquer overhead de software:

```cpp
#include "stm32h7xx_hal.h"

// Inicializacao do DWT (executada uma vez na inicializacao do sistema)
void Dsp_InitDwtCycleCounter(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->LAR = 0xC5ACCE55; // Desbloqueia registradores de depuracao se aplicavel
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk; // Habilita o contador CYCCNT
}

// Medicao precisa de um bloco de processamento DSP
void Audio_ProcessBlockBenchmark(float *pInLeft, float *pInRight, float *pOutLeft, float *pOutRight, uint32_t numSamples)
{
    uint32_t startCycles = DWT->CYCCNT;

    // Execucao da cadeia de audio
    DspEngine::GetInstance().ProcessBuffer(pInLeft, pInRight, pOutLeft, pOutRight, numSamples);

    uint32_t elapsedCycles = DWT->CYCCNT - startCycles;
    float cyclesPerSample = static_cast<float>(elapsedCycles) / static_cast<float>(numSamples);
    float cpuUsagePercent = (cyclesPerSample / 11458.33f) * 100.0f;

    // Se o uso de CPU ultrapassar 25%, registra alarme ou telemetria
    if(cpuUsagePercent > 25.0f)
    {
        // Alerta de headroom de CPU comprometido
    }
}
```

---

## 3. Roteiro Experimental de Ensaios em Bancada

Baseado no documento formal [`docs/code/plano_testes_bancada_efeitos.md`](file:///home/rodrigues/Pedaleira-digital/docs/code/plano_testes_bancada_efeitos.md), os testes de bancada seguem 6 etapas progressivas:

```
[Etapa 0] Pass-Through Puro & Alimentacao
   └──> [Etapa 1] Overdrive & FFT Harmonica
         └──> [Etapa 2] Equalizador Shelving / Peaking
               └──> [Etapa 3] Linha de Delay Circular
                     └──> [Etapa 4] Crossfade Anti-Pop
                           └──> [Etapa 5] Cadeia Completa & Stress Test
```

### Etapa 0: Verificacao Eletrica e Audio Pass-Through
- **Objetivo**: Validar integridade da alimentacao e codec CS4272 em modo Loopback (Bypass).
- **Procedimento**:
  1. Multimetro: confirmar $3{,}30\text{ V} \pm 0{,}05\text{ V}$ no barramento digital e $5{,}00\text{ V} \pm 0{,}10\text{ V}$ no barramento analogico VA do CS4272.
  2. Gerador de sinais: senoide $1{,}00\text{ kHz}$ a $500\text{ mVpp}$ no Jack de Entrada.
  3. Osciloscopio: CH1 na entrada (buffer TL072), CH2 na saida analogica do CS4272.
- **Criterio de Aprovacao**:
  - $V_{out} \approx V_{in}$ (ganho unitario $\pm 1\text{ dB}$).
  - Latencia fim-a-fim $< 2{,}0\text{ ms}$.

### Etapa 1: Validacao do Overdrive e FFT Harmonica
- **Objetivo**: Comprovar a curva de ceifamento suave e geracao de harmonicos sem clipping digital espurio.
- **Procedimento**:
  1. Ligar Chave SW1 (Overdrive) -> LED PE7 acende.
  2. Injetar senoide $440\text{ Hz}$ de $100\text{ mVpp}$ ate $1{,}0\text{ Vpp}$.
  3. Habilitar FFT no osciloscopio (Janela Hanning).
- **Criterio de Aprovacao**:
  - Curva senoidal arredonda no topo sem descontinuidades abruptas.
  - Surgimento de harmonicos impares (3a ordem em $1{,}32\text{ kHz}$, 5a ordem em $2{,}20\text{ kHz}$) com decaimento suave.

### Etapa 2: Validacao do Equalizador de 3 Bandas
- **Objetivo**: Comprovar atenuacao e amplificacao de $\pm 12\text{ dB}$ nos filtros Shelving e Peaking.
- **Procedimento**:
  1. Ligar Chave SW2 (Equalizador) -> LED PE8 acende.
  2. Injetar varredura senoidal de frequencia (Sweep $20\text{ Hz}$ a $20\text{ kHz}$).
  3. Testar Bass ($100\text{ Hz}$), Mid ($1\text{ kHz}$), Treble ($4\text{ kHz}$).
- **Criterio de Aprovacao**:
  - Ganho maximo $+12\text{ dB}$ (fator $\approx 4\times$ tensao); atenuacao $-12\text{ dB}$ (fator $\approx 0{,}25\times$).

### Etapa 3: Validacao do Delay e Buffer Circular
- **Objetivo**: Confirmar estabilidade do retardo sem ruido de zipper ou extrapolacao de buffer.
- **Procedimento**:
  1. Ligar Chave SW3 (Delay) -> LED PE9 acende.
  2. Injetar trem de pulsos senoidais isolados de $1\text{ kHz}$ com duracao de $10\text{ ms}$ a cada $1\text{ segundo}$.
  3. Ajustar `Time = 300 ms`, `Feedback = 50%`, `Mix = 50%`.
- **Criterio de Aprovacao**:
  - Primeira repeticao surge exatamente $300\text{ ms} \pm 2\text{ ms}$ apos o pulso de entrada.
  - Repeticoes decaem exponencialmente sem corte ou estouro de memoria.

### Etapa 4: Validacao do Crossfade Anti-Pop
- **Objetivo**: Medir ausencia de transiente de clique ao ligar/desligar efeitos.
- **Procedimento**:
  1. Injetar senoide continua de $1\text{ kHz}$ a $1\text{ Vpp}$.
  2. Comutar repetidamente as chaves fisicas SW1, SW2, SW3.
  3. Disparar o osciloscopio em modo Single Trigger na borda da chave.
- **Criterio de Aprovacao**:
  - Rampa suave de $10\text{ ms}$ sem picos espurios superiores a $-60\text{ dBFS}$.
  - Zero estalos perceptiveis no fone de monitoramento.

### Etapa 5: Cadeia Completa Integrada e Carga de CPU
- **Procedimento**:
  1. Ligar todos os efeitos simultaneamente: Overdrive (Drive 80%), EQ (Bass +6, Treble +6), Delay (500 ms, Feedback 60%).
  2. Conectar instrumento musical e tocar acordes cheios com alto ataque dinamico.
  3. Monitorar a saida serial/MQTT da telemetria de ciclos DWT.
- **Criterio de Aprovacao**:
  - Audio sem glitches, estalos ou travamentos por buffer underflow.
  - Carga de CPU reportada via DWT estritamente inferior a $25\%$.
