# Plano de Implementação — Pedaleira Digital MVP Rev. A (`91` Componentes)

## 1. Escopo Consolidado (Cortes e Substituições vs Rev. 4.10)
- **Preservado:** caminho completo de áudio (`TL072` `U1/U3` + `CS4272` `U2`), referências separadas (`VREF_OP` e `ADC_BIAS`), `C35/C36` (`100 pF` RF modo comum ADC), `H_STM32` (`WeAct STM32H723 V1.2`), `H_ESP32` (`ESP32 DevKit V1 WROOM`), `SW1..SW4`, `D2..D5` e desacoplamentos locais (`C23..C32`).
- **Removido (`94` itens do CAD 4.10):** Folha 9 (`25`), Folha 10 (`42`), `Q11..Q14` (`4`), `K1/D16` (`2`), Folha 8 `U6 ISO7721DR + C42/C43 + R29..R32` (`7`), `J1/F1/J4/TP1..TP11` (`14`).
- **Adicionado / Substituído:**
  - Entrada direta `PSU_12V` por fios da fonte de bancada (`12,0 V`, `I_limit = 250–300 mA`).
  - `6× 1N4007` nos lugares de `D1` (`1N5822`), `D8` (`1N4007`) e `D6, D7, D13, D14` (`1N4148`).
  - `2× 1 kohm` (`R_UTX`, `R_URX`) em série na UART direta (`PD8 ↔ GPIO16`, `GPIO17 ↔ PD9`).
  - Capacitores **exclusivamente cerâmicos (`<= 1 uF`) e eletrolíticos (`>= 10 uF`)**.
  - Ligações diretas substituindo cortes: `OUT_PRE (C5/R6) -> J3.1` e `PD10 (H_STM32 P1.38) -> CODEC_RST (U2.14 / R13)`.

---

## 2. Arquitetura das Esquemáticas Geradas
- **Prancha Unificada Única (todas as 7 etapas juntas):**
  - PDF A1: `output/MVP_REVA/pedaleira_mvp_revA_unificada.pdf` (`pedaleira_mvp_revA_unificada-1.png`)
  - KiCad A1: `output/MVP_REVA/kicad_unificada/esquematica_mvp_unificada.kicad_sch`
- **Caderno Multi-Folha A4 (zoom de bancada):**
  - PDF A4 (7 folhas): `output/MVP_REVA/pedaleira_mvp_revA_folhas.pdf`
  - KiCad A4: `output/MVP_REVA/kicad/pedaleira_mvp_revA.kicad_sch`
- **Modelo único e BOM:**
  - `docs/hardware/mvp_revA/circuito_mvp_revA.json` e `output/MVP_REVA/BOM_mvp_revA.csv`
- **Regeneração + ERC + Netlist:**
  - Executar `sh docs/hardware/mvp_revA/run_mvp.sh`

---

## 3. Fases de Implementação e Montagem em Bancada

### Etapa 1 — Fonte de Bancada, `CW7805` e Referências (Bloco 1)
1. Ajustar fonte de bancada em **`12,0 V`** com **`I_limit = 250–300 mA`** (desligada).
2. Montar na perfboard `D1 (1N4007)`, `C33 (220 uF)`, `C21 (330 nF)`, `U5 (CW7805)`, `D8 (1N4007)`, `C22 (100 nF)`, `R21 (910 ohm)`, `C37 (1000 uF)` e **`J5` ABERTO (sem shunt)**.
3. Confirmar fisicamente a pinagem `IN / GND / OUT` do `CW7805` antes de ligar.
4. Energizar apenas a Etapa 1: validar `+RAW ≈ 11,1–11,3 V` e `+5V_CW = 4,90–5,10 V`.
5. Montar `1B` (`R22/R23`, `C38/C39`) e `1C` (`R27/R28`, `C40/C41`) com `J5` ainda aberto.

### Etapa 2 — Estágio Digital Base e UART Direta (Blocos 5 e 6)
1. Montar headers para `H_STM32` e `H_ESP32` mantendo **`+3V3_STM`, `+3V3_ESP`, `5V/VIN` isolados entre si** (ligar **somente `GND` comum** e cada placa na própria USB).
2. Instalar `R_UTX` (`1 kohm`: `PD8/P1.40 -> RX2/GPIO16`), `R_URX` (`1 kohm`: `TX2/GPIO17 -> PD9/P1.39`), `R11/R12` (`4,7 kohm` pull-up para `+3V3_STM`), `R13` (`10 kohm` em `CODEC_RST`), `R14` (`47 kohm` em `ADC_DATA`).
3. Instalar `SW1..SW4` (`PC0, PC1, PC2_C, PC3_C -> GND`) e `R_D2..R_D5` (`330 ohm`) + `D2..D5` (`PE7/8/9/15`).
4. **Pendências obrigatórias de firmware antes de testar áudio/chaves:**
   - Habilitar `#define HAL_SAI_MODULE_ENABLED` em `firmware/stm32/Core/Inc/stm32h7xx_hal_conf.h`.
   - Implementar clocks/DMA de `SAI4` (`PE0 MCLK AF10`, `PE4/5/6 FS/SCK/SDA AF8`, `PA0 SDB AF10`) e liberar `dMAIN_AUDIO_TRANSPORT_READY` em `firmware/stm32/Core/Src/main.cpp`.
   - Fechar switches internos `SYSCFG_SWITCH_PC2_CLOSE` / `PC3_CLOSE` para `SW3/SW4` (ou remapear para outros GPIOs livres).
   - Desenvolver `firmware/esp32/` (UART2 a `115200 8N1` em `GPIO16/GPIO17`, confirmar módulo WROOM sem PSRAM nos mesmos pinos).

### Etapa 3 — Caminho Analógico `TL072` sem Codec (Blocos 2, 4 e 7B/7C)
1. Montar `U1`, `U3` (preferencialmente em soquetes DIP-8) com `C29/C30` e `C31/C32` colados nos pinos `8/4`.
2. Montar Bloco 2 (`J2`, `C1` cerâmico, `R26`, `R3`, `D6/D7/D13/D14` `1N4007`, `R17/C18/R18`, `R24/R19/C19/R20`, `C2/C16` eletrolíticos, `R15/R16`, `C35/C36` `100 pF` RF, `C20` `680 pF`).
3. Montar Bloco 4 (`C10/C11` eletrolíticos, `R1/R2/R7/R8`, `R4/C4/R5/C6` cerâmicos, `C5` eletrolítico, `R6`, `J3` ligado direto em `OUT_PRE`).
4. Checar polaridades críticas antes de fechar `J5`:
   - `C2, C16` (`10 uF`): **`+`** no lado `R18/R20` (`~5,5 V`), **`-`** em `AINA_P/N` (`~2,4 V`).
   - `C10, C11` (`10 uF`): **`+`** no lado `R1/R7` (`~5,5 V`), **`-`** nos pinos `25/24` do `U2` (`~2,4 V`).
   - `C5` (`10 uF`): **`+`** em `LP2`, **`-`** em `OUT_PRE` / `J3.1`.
5. Sem `U2` inserido e com `J5` fechado apenas para medir `ADC_BIAS`: validar `VREF_OP ≈ +5,5 V` nos op-amps, injetar senoide `0,5 Vpp` em `J2` e conferir ganho `+1` em `DRV_P` e `-1` em `DRV_N`.

### Etapa 4 — Codec `CS4272` e Validação Completa (Bloco 3 + Bloco 7A)
1. Com tudo desenergizado, montar o adaptador `U2 (CS4272)` com fios curtos de `MCLK/LRCK/SCLK/SDIN/SDOUT`, plano/malha de `GND` baixa impedância e `C23..C28` colados nos pinos `20 (VA)`, `9 (VD)` e `10 (VL)`.
2. Conferir **`C12` (`47 uF` eletrolítico, `+` no pino 22 `FILT+`)** e **`C14` (`1 uF` CERÂMICO, não eletrolítico, no pino 15 `VCOM`)**.
3. **Ordem rígida de energização em todos os ensaios (compensa ausência das Folhas 9/10 e `K1`):**
   1. Desligar amplificador/fone da saída `J3`.
   2. Ligar fonte de bancada `12 V` (`+RAW`, `+5VA` via `J5` fechado) **primeiro** (`R13 = 10 kohm` mantém `/RST` em `0 V`).
   3. Ligar `USB_STM` (e `USB_ESP` no mesmo PC/hub) — STM32 aguarda `5 s` em `Cs4272::Init()`, configura `0x10` via I2C e libera áudio.
   4. Conectar/ligar amplificador/fone por último.
   5. Ao desligar: desconectar/mutar saída primeiro → desligar USBs → desligar fonte `12 V`.
