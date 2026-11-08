#include "InterMcuUart.hpp"
#include "Cs4272.hpp"
#include "Cs4272I2cTiming.hpp"
#include "Bsp.hpp"
#include "UartRxRing.hpp"
#include "MasterMuteGate.hpp"
#include <cassert>
#include <cstdio>
#include <vector>
#include <thread>
#include <atomic>
static UartRxRing input;
static std::vector<u8> output;
static u32 tick;
bool Bsp::Usart3ReadEvent(u16* event)
{
    return input.Pop(*event);
}
void Bsp::Usart3WriteByte(u8 byte)
{
    output.push_back(byte);
}
u32 Bsp::GetTick(void)
{
    return tick;
}
static I2C_HandleTypeDef i2c;
static HAL_StatusTypeDef i2cStatus = HAL_OK;
static GPIO_PinState resetState = GPIO_PIN_RESET;
static std::vector<std::pair<u8, u8>> registerWrites;
void Bsp::DelayMs(u32 ms)
{
    tick += ms;
}
I2C_HandleTypeDef* Bsp::GetI2c1Handle(void)
{
    return &i2c;
}
void HAL_GPIO_WritePin(void*, uint16_t pin, GPIO_PinState value)
{
    assert(pin == GPIO_PIN_10);
    resetState = value;
}
HAL_StatusTypeDef HAL_I2C_Mem_Write(I2C_HandleTypeDef*, uint16_t address,
    uint16_t reg, uint16_t, uint8_t* data, uint16_t size, uint32_t)
{
    assert(address == 0x20 && size == 1);
    registerWrites.emplace_back(reg, *data);
    return i2cStatus;
}
HAL_StatusTypeDef HAL_I2C_Mem_Read(I2C_HandleTypeDef*, uint16_t address,
    uint16_t, uint16_t, uint8_t* data, uint16_t size, uint32_t)
{
    assert(address == 0x20 && size == 1);
    *data = 0;
    return i2cStatus;
}
static std::vector<u8> Frame(u8 cmd, std::vector<u8> payload = {})
{
    std::vector<u8> body{cmd, static_cast<u8>(payload.size())};
    body.insert(body.end(), payload.begin(), payload.end());
    std::vector<u8> bytes{0xAA, 0x55};
    bytes.insert(bytes.end(), body.begin(), body.end());
    bytes.push_back(InterMcuUart::CalculateCrc8(body.data(), body.size()));
    return bytes;
}
static void Inject(const std::vector<u8>& bytes)
{
    for(u8 byte : bytes)
    {
        assert(input.PushByte(byte));
    }
}
static void Expect(InterMcuUart& uart, u8 command, std::vector<u8> expected = {})
{
    u8 cmd, length, payload[64];
    assert(uart.GetPacket(&cmd, payload, &length));
    assert(cmd == command && length == expected.size());
    assert(std::vector<u8>(payload, payload + length) == expected);
}
int main()
{
    static_assert(Cs4272I2cTiming::Register == 0x70C4272FU, "Derived timing register");
    InterMcuUart uart;
    uart.Init();
    const u8 heartbeat[]{7, 0};
    const u8 overdrive[]{1, 3, 1, 1, 75};
    const u8 switchEvent[]{4, 2, 1, 1};
    assert(InterMcuUart::CalculateCrc8(heartbeat, 2) == 0x6B);
    assert(InterMcuUart::CalculateCrc8(overdrive, 5) == 0xD0);
    assert(InterMcuUart::CalculateCrc8(switchEvent, 4) == 0x9C);
    Inject(Frame(1, {1, 1, 75}));
    Inject(Frame(7));
    uart.ProcessRx();
    Expect(uart, 1, {1, 1, 75});
    Expect(uart, 7);
    assert(!uart.HasNewPacket());
    std::vector<u8> maximum(64, 0xAA);
    Inject(Frame(3, maximum));
    uart.ProcessRx();
    Expect(uart, 3, maximum);
    auto corrupt = Frame(7);
    corrupt.back() ^= 1;
    Inject(corrupt);
    Inject({0xAA, 0x55, 1, 65});
    Inject(Frame(4, {1, 1}));
    uart.ProcessRx();
    assert(uart.GetCrcErrors() == 1);
    Expect(uart, 4, {1, 1});
    assert(!uart.HasNewPacket());
    // Full decoded queue applies backpressure to the byte ring, preserving order.
    for(u8 i = 0; i < 10; ++i)
    {
        Inject(Frame(1, {i}));
    }
    uart.ProcessRx();
    for(u8 i = 0; i < 8; ++i)
    {
        Expect(uart, 1, {i});
    }
    uart.ProcessRx();
    Expect(uart, 1, {8});
    Expect(uart, 1, {9});
    // Public foreground callback cannot silently overwrite a full packet queue.
    for(u8 i = 0; i < 9; ++i)
    {
        for(u8 byte : Frame(7))
        {
            uart.RxByteCallback(byte);
        }
    }
    assert(uart.GetPacketDrops() == 1);
    for(int i = 0; i < 8; ++i)
    {
        Expect(uart, 7);
    }
    // Framing/noise/overrun boundaries reset a partial frame in order.
    Inject({0xAA, 0x55, 1, 3, 1});
    input.MarkHardwareError();
    Inject(Frame(7));
    uart.ProcessRx();
    Expect(uart, 7);
    assert(!uart.HasNewPacket() && input.HardwareErrors() == 1);
    // Interrupted frame expires; tick subtraction also works across wraparound.
    tick = 0xFFFFFFF0U;
    Inject({0xAA, 0x55, 1, 64});
    uart.ProcessRx();
    tick += 21;
    Inject(Frame(7));
    uart.ProcessRx();
    Expect(uart, 7);
    // Overflow is explicit and the recovery marker precedes subsequent bytes.
    for(unsigned i = 0; i < UartRxRing::Capacity; ++i)
    {
        assert(input.PushByte(0));
    }
    assert(!input.PushByte(99));
    uart.ProcessRx();
    Inject(Frame(7));
    uart.ProcessRx();
    Expect(uart, 7);
    assert(input.DroppedBytes() == 1);
    uart.SendPacket(4, switchEvent + 2, 2);
    assert(output == Frame(4, {1, 1}));
    assert(!uart.SendPacket(1, nullptr, 1));
    // SPSC publication under concurrent producer and consumer.
    UartRxRing concurrent;
    std::atomic<bool> done{false};
    std::thread producer([&]()
    {
        for(unsigned i = 0; i < 200000; ++i)
        {
            concurrent.PushByte(static_cast<u8>(i));
        }
        done.store(true, std::memory_order_release);
    });
    unsigned received = 0;
    u16 event;
    while(!done.load(std::memory_order_acquire))
    {
        if(concurrent.Pop(event))
        {
            received += event < 256;
        }
    }
    producer.join();
    while(concurrent.Pop(event))
    {
        received += event < 256;
    }
    assert(received + concurrent.DroppedBytes() == 200000);
    MasterMuteGate mute;
    assert(mute.Effective(false, false));
    assert(!mute.Effective(false, true));
    mute.SetRemote(true);
    for(int i = 0; i < 100; ++i)
    {
        assert(mute.Effective(false, true));
    }
    mute.SetRemote(false);
    assert(mute.Effective(true, true));
    assert(mute.Effective(false, false));
    assert(!mute.Effective(false, true));
    Cs4272 codec;
    assert(codec.Init() == eCS4272_STATUS_OK);
    assert(codec.IsInitialized() && resetState == GPIO_PIN_SET);
    const std::vector<std::pair<u8, u8>> expectedRegisters = {
        {7, 3}, {1, 1}, {2, 0}, {3, 0x39}, {4, 0xFF}, {5, 0xFF}, {6, 0x14}, {7, 2}};
    assert(registerWrites == expectedRegisters);
    i2cStatus = HAL_TIMEOUT;
    assert(codec.SetMute(false) == eCS4272_STATUS_TIMEOUT);
    assert(!codec.IsInitialized() && resetState == GPIO_PIN_RESET);
    i2cStatus = HAL_ERROR;
    assert(codec.Init() == eCS4272_STATUS_ERROR);
    assert(!codec.IsInitialized() && resetState == GPIO_PIN_RESET);
    std::puts("PASS: real C++ CRC/parser/TX, consecutive packets, 64/65-byte bounds, queue backpressure, counted overflow, error marker, timeout/wrap, concurrent SPSC, persistent mute, safety gates, real codec register sequence and reset LOW on I2C timeout/NACK.");
}
