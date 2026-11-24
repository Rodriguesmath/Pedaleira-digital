# Modelo 3D Conceitual — Pedaleira Digital (IFPB Rev 4.10)

Conjunto mecânico paramétrico gerado conforme a **BOM Rev 4.10** para documentação e impressão 3D do gabinete do protótipo **Pedaleira Digital**.

## Arquivos Gerados

| Arquivo | Descrição |
| :--- | :--- |
| [`pedaleira_gabinete_3d.stl`](pedaleira_gabinete_3d.stl) | Malha STL binária (`4384` triângulos) contendo **Base + Tampa** (com furação completa para `SW1..SW4`, `D2..D5`, `J1..J3` e USBs) dispostas lado a lado no plano `Z = 0` para fatiamento sem suportes. |
| [`render1_isometrica_externa.png`](render1_isometrica_externa.png) | Vista isométrica montada com cotas externas (`180 × 120 × 55 mm`), 4 chaves `MTS-102` (`SW1..SW4`), 4 LEDs (`D2..D5`) e Jack `J2` (`IN P10`). |
| [`render2_vista_explodida_interna.png`](render2_vista_explodida_interna.png) | Vista explodida em 4 camadas mostrando placa perfurada (`145 × 95 mm`), `WeAct STM32H723`, `ESP32 DevKit`, `Adaptador CS4272` e `Relé G5V-1`. |
| [`render3_painel_superior.png`](render3_painel_superior.png) | Vista superior ortográfica com furação e legenda completa (`SW1..SW4`, `D2..D5`, `J2`/`J3`, passo `38.0 mm`, `PEDALEIRA DIGITAL - IFPB (REV 4.10)`). |
| [`render4_conectores_laterais.png`](render4_conectores_laterais.png) | Folha ortográfica com laterais (`J2 IN P10`, `J3 OUT P10`) e traseira (`J1 12V DC`, `USB-C STM32`, `USB ESP32`). |

## Mapeamento do Painel e Conectores (BOM Rev 4.10)

| Referência | Componente | Função | Posição `(X, Y, Z)` (mm) | Furo / Recorte |
| :--- | :--- | :--- | :--- | :--- |
| `SW1` + `D2` | MTS-102 + LED Vermelho | **OVERDRIVE** | `X = -57.0`, `Y = -20.0 / +6.0` | `Ø 6.5 mm` / `Ø 5.2 mm` |
| `SW2` + `D3` | MTS-102 + LED Verde | **EQUALIZADOR** | `X = -19.0`, `Y = -20.0 / +6.0` | `Ø 6.5 mm` / `Ø 5.2 mm` |
| `SW3` + `D4` | MTS-102 + LED Azul | **DELAY** | `X = +19.0`, `Y = -20.0 / +6.0` | `Ø 6.5 mm` / `Ø 5.2 mm` |
| `SW4` + `D5` | MTS-102 + LED Âmbar | **MODO CONFIG (ESP32)** | `X = +57.0`, `Y = -20.0 / +6.0` | `Ø 6.5 mm` / `Ø 5.2 mm` |
| `J1` | Jack P4 / Barrel | **Entrada 12 V DC** | `X = -45.0, Y = +60.0, Z = 24.0` | `Ø 11.0 mm` |
| `J2` | Jack P10 Mono | **IN P10** (Entrada) | `X = +90.0, Y = 0.0, Z = 26.0` | `Ø 10.5 mm` |
| `J3` | Jack P10 Mono | **OUT P10** (Saída) | `X = -90.0, Y = 0.0, Z = 26.0` | `Ø 10.5 mm` |
| `USB1` / `USB2` | Recortes USB | STM32H723 / ESP32 | `X = 0.0 / +45.0, Y = +60.0, Z = 24.0` | `13.0 × 8.0 mm` |

## Dimensões Principais (mm)

- **Gabinete externo montado:** `180.0 × 120.0 × 55.0 mm` (espessura de parede `3.0 mm`, chanfros externos de `5.0 mm`).
- **Base (`pedaleira_gabinete_3d.stl`):** `180.0 × 120.0 × 52.0 mm` com 4 torres internas `M3` nos cantos (`(±80, ±50)`) e 4 *standoffs* de `8.0 mm` para a placa perfurada (`(±64, ±38)`).
- **Tampa (`pedaleira_gabinete_3d.stl`):** `180.0 × 120.0 × 3.0 mm` + aba de encaixe de `2.5 mm`, invertida no leito de impressão em `Y = +142 mm`.

## Recomendações de Impressão 3D (FDM)

- **Material:** PETG ou ABS (maior resistência mecânica e térmica que PLA para uso em bancada).
- **Altura de camada:** `0.20 mm`, **Preenchimento:** `25%–30%` (giroide), **Perímetros:** `3` a `4`.
- **Suportes:** Não necessários — a tampa encontra-se invertida com a face superior apoiada na mesa (`Z = 0`).
- **Pós-processamento:** Insertos metálicos ou parafusos `M3 × 10 mm` nos 4 cantos; 4 pés de borracha adesivos (`Ø 16 × 5 mm`) na base.
