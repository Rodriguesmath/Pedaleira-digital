#include "DspEngine.hpp"
#include "DspDelay.hpp"
#include <cmath>
#include <cstdio>
#include <cstdlib>
static DspEngine engine;
static DspDelay delayLine;
static void require(bool ok, const char* what)
{
    if(!ok)
    {
        std::fprintf(stderr, "FAIL: %s\n", what);
        std::exit(1);
    }
}
int main()
{
    engine.Init(48000.0f);
    engine.SetMasterVolume(1.0f);
    engine.SetMasterMute(false);
    engine.SetMasterBypass(false);
    engine.SetOverdriveEnable(false);
    engine.SetEqualizerEnable(false);
    engine.SetDelayEnable(false);
    for(int i = 0; i < 48000; ++i)
    {
        float x = 0.1f * std::sin(6.283185307f * 1000.0f * i / 48000.0f);
        require(std::fabs(engine.ProcessSample(x) - x) < 0.00001f, "disabled effects transparent");
    }
    engine.SetMasterMute(true);
    require(engine.ProcessSample(0.5f) == 0.0f, "master mute");
    engine.SetMasterMute(false);
    engine.SetOverdriveEnable(true);
    engine.SetOverdriveDrive(1.0f);
    engine.SetOverdriveLevel(1.0f);
    engine.SetEqualizerEnable(true);
    engine.SetEqualizerLow(12.0f);
    engine.SetEqualizerMid(12.0f);
    engine.SetEqualizerTreble(12.0f);
    engine.SetDelayEnable(true);
    engine.SetDelayFeedback(0.95f);
    engine.SetDelayMix(0.7f);
    engine.SetDelayTimeMs(20.0f);
    for(int i = 0; i < 480000; ++i)
    {
        float y = engine.ProcessSample(0.95f * std::sin(0.173f * i));
        require(std::isfinite(y) && std::fabs(y) <= 1.000001f, "stress finite and bounded");
    }
    delayLine.Init(48000.0f);
    delayLine.SetEnabled(true);
    delayLine.SetDelayTimeMs(20.0f);
    delayLine.SetMix(1.0f);
    delayLine.SetFeedback(0.0f);
    for(int i = 0; i < 240000; ++i)
    {
        delayLine.Process(0.0f);
    }
    delayLine.Reset();
    float peak = 0.0f;
    int peakIndex = -1;
    for(int i = 0; i < 2000; ++i)
    {
        float y = delayLine.Process(i == 0 ? 1.0f : 0.0f);
        if(std::fabs(y) > peak)
        {
            peak = std::fabs(y);
            peakIndex = i;
        }
    }
    require(peakIndex >= 958 && peakIndex <= 962 && peak > 0.5f, "20 ms delay after settling");
    std::printf("PASS: bypass, mute, 480000 stress samples, delay impulse at %d samples (peak %.6f).\n", peakIndex, peak);
}
