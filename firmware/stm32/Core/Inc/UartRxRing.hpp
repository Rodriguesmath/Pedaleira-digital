/******************************************************************************/
/**
 * @file UartRxRing.hpp
 * @brief Bounded single-producer ISR / single-consumer foreground RX queue.
 * @author Arthur Ramalho, Isabelle Lavinia, Joao Paulo, Rodrigues Matheus
 */
#ifndef UART_RX_RING_HPP
#define UART_RX_RING_HPP
#include <atomic>
#include <cstdint>

class UartRxRing
{
public:
    static constexpr uint32_t Capacity = 512U;
    static constexpr uint16_t Discontinuity = 0x100U;
    static_assert(std::atomic<uint32_t>::is_always_lock_free,
                  "ISR counters must be lock free");

    bool PushByte(uint8_t value)
    {
        if(pendingFault_)
        {
            if(!Push(Discontinuity))
            {
                droppedBytes_.fetch_add(1U, std::memory_order_relaxed);
                return false;
            }
            pendingFault_ = false;
        }
        if(!Push(value))
        {
            droppedBytes_.fetch_add(1U, std::memory_order_relaxed);
            pendingFault_ = true;
            return false;
        }
        return true;
    }

    void MarkHardwareError()
    {
        hardwareErrors_.fetch_add(1U, std::memory_order_relaxed);
        if(!pendingFault_)
        {
            pendingFault_ = !Push(Discontinuity);
        }
    }

    bool Pop(uint16_t& value)
    {
        const uint32_t tail = tail_.load(std::memory_order_relaxed);
        if(tail == head_.load(std::memory_order_acquire))
        {
            return false;
        }
        value = events_[tail % Capacity];
        tail_.store(tail + 1U, std::memory_order_release);
        return true;
    }

    uint32_t DroppedBytes() const
    {
        return droppedBytes_.load(std::memory_order_relaxed);
    }

    uint32_t HardwareErrors() const
    {
        return hardwareErrors_.load(std::memory_order_relaxed);
    }

private:
    bool Push(uint16_t value)
    {
        const uint32_t head = head_.load(std::memory_order_relaxed);
        if(head - tail_.load(std::memory_order_acquire) == Capacity)
        {
            return false;
        }
        events_[head % Capacity] = value;
        head_.store(head + 1U, std::memory_order_release);
        return true;
    }

    uint16_t events_[Capacity] = {};
    std::atomic<uint32_t> head_{0U};
    std::atomic<uint32_t> tail_{0U};
    std::atomic<uint32_t> droppedBytes_{0U};
    std::atomic<uint32_t> hardwareErrors_{0U};
    bool pendingFault_ = false; // Written only by the ISR producer.
};
#endif
