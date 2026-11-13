# Firmware ESP32 — Inter-MCU UART & MQTT Connectivity Bridge

![ESP32](https://img.shields.io/badge/MCU-ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-660066?style=flat-square&logo=mqtt&logoColor=white)
![UART](https://img.shields.io/badge/UART-115200%208N1-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-Implemented%20%26%20Verified-brightgreen?style=flat-square)

## 1. Visão Geral

Firmware responsável pela conectividade sem fio (Wi-Fi / MQTT) e pela ponte de comunicação serial bidirecional com o microcontrolador DSP principal (**STM32H723VGT6**).

Atua como gateway IoT entre aplicativos externos (mobile/desktop/web via broker MQTT) e o mecanismo de áudio de ultra-baixa latência do STM32, mantendo um espelho sincronizado do estado do pedal e respeitando a governança do modelo **Hardware Master Gate**.

---

## 2. Pinagem e Conexão Física (UART2)

| Sinal | Pino ESP32 | Pino STM32H723 | Descrição |
| :--- | :--- | :--- | :--- |
| **RX2** | `GPIO16` | `PD8` (USART3 TX) | Recepção de telemetria, estados e eventos de chave |
| **TX2** | `GPIO17` | `PD9` (USART3 RX) | Envio de comandos de parâmetros, requisição de estado e heartbeat |
| **GND** | `GND` | `GND` | Referência comum de baixo retorno |

- **Baud Rate:** 115.200 bps
- **Configuração:** 8-N-1 (8 bits de dados, sem paridade, 1 stop bit)
- **Nível Lógico:** 3.3V LVCMOS nativo

---

## 3. Protocolo Binário Inter-MCU

Para eliminar sobrecarga de texto no DSP, toda a comunicação UART opera com quadros determinísticos com validação **CRC-8 CCITT**:

```
+------------+------------+---------+---------+------------------------+---------+
| SYNC_1     | SYNC_2     | CMD     | LEN     | PAYLOAD (0 a 64 bytes) | CRC8    |
| (0xAA)     | (0x55)     | (1 B)   | (1 B)   | (N <= 64 bytes)        | (1 B)   |
+------------+------------+---------+---------+------------------------+---------+
```

- **Polinômio CRC-8 CCITT:** $x^8 + x^2 + x + 1$ (`0x07`), valor inicial `0x00`.
- **Fatia de cálculo do CRC:** calculada estritamente sobre `[CMD, LEN, PAYLOAD...]`.
- **FSM de Recepção:** máquina de estados finita estática com timeout de 20 ms, recuperação automática de erros de CRC e contador de integridade.

### Tabela de Comandos

| CMD | Nome | Direção | Descrição |
| :---: | :--- | :---: | :--- |
| `0x01` | `CMD_SET_PARAM` | ESP32 -> STM32 | Altera parâmetro contínuo ou booleano de áudio |
| `0x02` | `CMD_GET_STATE` | ESP32 -> STM32 | Solicita sincronização completa de estado do DSP |
| `0x03` | `CMD_STATE_REPORT` | STM32 -> ESP32 | Relatório de estado contendo `[SW1, SW2, SW3, SW4, MasterVol%]` |
| `0x04` | `CMD_SWITCH_EVENT` | STM32 -> ESP32 | Notificação assíncrona de comutação física de chave `[SwitchID, State]` |
| `0x05` | `CMD_ACK` | Ambos | Confirmação de execução bem-sucedida |
| `0x06` | `CMD_NACK` | Ambos | Notificação de erro de comando ou CRC |
| `0x07` | `CMD_HEARTBEAT` | Ambos | Keep-alive periódico de enlace (1.000 ms) |

---

## 4. Arquitetura Hardware Master Gate

A pedaleira combina **chaves mecânicas físicas de alavanca com retenção** no painel com **controle remoto via MQTT/App**:

1. **A Chave Física é o Master Gate Soberano:**
   - Comutação física define se o módulo está em Bypass ou Ativo.
   - Chave em OFF força o bloco de efeito em bypass digital transparente (crossfade).
   - SW4 controla o mute físico mestre.
2. **O Aplicativo Governa os Parâmetros Contínuos:**
   - Ganho de Overdrive, Tonalidade, Bandas de EQ, Tempo de Delay e Mix podem ser ajustados a qualquer momento pelo aplicativo.
   - Mute remoto via app (`remote_mute`) e SW4 físico são arbitrados pela equação:
     $$\text{effective\_mute} = \text{remote\_mute} \lor \text{SW4} \lor \neg\text{transport\_ready}$$
3. **Notificação Assíncrona Zero-Polling:**
   - Ao comutar uma chave física, o STM32 despacha `CMD_SWITCH_EVENT`, o ESP32 atualiza seu espelho e publica imediatamente no tópico `pedaleira/state`.

---

## 5. Interface MQTT (JSON)

### Publicação de Estado (`pedaleira/state`)
Buffer estático zero-heap com atualização sob evento e periódica:
```json
{
  "switches": {"sw1": 1, "sw2": 0, "sw3": 1, "sw4": 0},
  "global": {"volume": 80, "bypass": 0, "remote_mute": 0, "effective_mute": 0},
  "overdrive": {"enabled": 1, "drive": 75, "tone": 50, "level": 70},
  "equalizer": {"enabled": 0, "low": 0, "mid": 0, "treble": 0},
  "delay": {"enabled": 1, "time_ms": 500, "feedback": 30, "mix": 30}
}
```

### Comandos de Entrada (`pedaleira/cmd`)
O parser zero-heap aceita formato estruturado ou chaves amigáveis:
- Formato estruturado: `{"module": 1, "param": 1, "value": 75}`
- Chaves amigáveis diretas:
  - `{"volume": 85}` (Master Volume 0..100)
  - `{"mute": 1}` (Mute remoto 0/1)
  - `{"drive": 80}` (Overdrive Drive 0..100)
  - `{"bass": 4}` (EQ Low -12..+12 dB)
  - `{"delay_time": 450}` (Delay Time 20..1000 ms — codificado em Little-Endian 16 bits)

---

## 6. Estrutura de Arquivos

```
firmware/esp32/
├── CMakeLists.txt              # Suporte a compilação ESP-IDF e standalone host
├── Makefile                    # Quality Gate e suíte de testes unitários C11 de host
├── README.md                   # Documentação arquitetural e de uso
├── platformio.ini              # Configuração do ambiente PlatformIO (esp32dev)
├── include/
│   ├── inter_mcu_proto.h       # Definições do protocolo serial binário e FSM
│   ├── pedal_bridge.h          # Espelho de estado, serializador/parser JSON e encoders
│   └── pedal_config.h          # Pinagem UART2, tópicos MQTT e configurações
├── main/
│   └── CMakeLists.txt          # Componente principal do projeto ESP-IDF
├── src/
│   ├── inter_mcu_proto.c       # Implementação da FSM e CRC-8 CCITT
│   ├── pedal_bridge.c          # Lógica da ponte, Hardware Master Gate e JSON
│   └── main.cpp                # Ponto de entrada dual-mode (Arduino / ESP-IDF)
└── tests/
    └── test_esp32_bridge.c     # Suíte de verificação local C11 executável no Linux
```

---

## 7. Compilação e Verificação

### Testes de Unidade Host (Linux C11 sem hardware)
Executa a suíte de testes determinísticos com `/usr/bin/gcc`:
```bash
make -C firmware/esp32 CC=/usr/bin/gcc test
```

### Compilação via PlatformIO
```bash
cd firmware/esp32
pio run
```

### Compilação via ESP-IDF nativo
```bash
cd firmware/esp32
idf.py set-target esp32
idf.py build
```
