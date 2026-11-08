#!/usr/bin/env python3
"""Independent corner arithmetic + static binding to actual BSP/HAL configuration."""
from pathlib import Path
import itertools
import json
import re
root = Path(__file__).resolve().parents[2]
header = (root/'firmware/stm32/Core/Inc/Cs4272I2cTiming.hpp').read_text()
fields = {name:int(re.search(r'constexpr uint32_t '+name+r' = (\d+)U', header)[1])
          for name in ['Presc','SclDel','SdaDel','SclHigh','SclLow']}
register = (fields['Presc']<<28)|(fields['SclDel']<<20)|(fields['SdaDel']<<16)|(fields['SclHigh']<<8)|fields['SclLow']
assert register == 0x70C4272F
bsp = (root/'firmware/stm32/Core/Src/Bsp.cpp').read_text()
function = bsp.split('void Bsp::I2c1Config(void)')[1]
for required in ['hsiConfig.OscillatorType = RCC_OSCILLATORTYPE_HSI',
                 'hsiConfig.HSIState = RCC_HSI_DIV1',
                 'hsiConfig.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT',
                 'HAL_RCC_OscConfig(&hsiConfig)', 'DelayUs(10U)',
                 'clockConfig.PeriphClockSelection = RCC_PERIPHCLK_I2C1',
                 'clockConfig.I2c123ClockSelection = RCC_I2C123CLKSOURCE_HSI',
                 'HAL_RCCEx_PeriphCLKConfig(&clockConfig)',
                 'hi2c1.Init.Timing = dI2C1_TIMING_VALUE',
                 'HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE)',
                 'HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0U)']:
    assert required in function, required
assert '#define dI2C1_TIMING_VALUE                  Cs4272I2cTiming::Register' in bsp
assert re.search(r'#define dMAIN_AUDIO_TRANSPORT_READY\s+0U',
                 (root/'firmware/stm32/Core/Src/main.cpp').read_text())
rows=[]
for frequency, af_ns, rise_ns, fall_ns, sync_cycles in itertools.product(
        [60.8e6,64e6,67.2e6],[50,260],[100,1000],[0,300],[2,3]):
    tick=1e9/frequency
    presc=(fields['Presc']+1)*tick
    low_count=(fields['SclLow']+1)*presc
    high_count=(fields['SclHigh']+1)*presc
    low=low_count+fall_ns+af_ns+sync_cycles*tick
    high=high_count+rise_ns+af_ns+sync_cycles*tick
    setup=(fields['SclDel']+1)*presc-rise_ns
    hold=fields['SdaDel']*presc+af_ns+3*tick-fall_ns
    # AN4235 upper data-valid bound: SDADEL*tPRESC+tF+tAF+4*tI2CCLK.
    valid_delay=fields['SdaDel']*presc+fall_ns+af_ns+4*tick
    assert low>=4700 and high>=4000
    assert high_count>=4700 # extra conservative STOP/repeated-START budget
    assert low_count>=4700 # extra conservative bus-free budget
    assert setup>=250 and hold>=0 and valid_delay<=3450
    assert 1e9/(low_count+high_count)<=100000 # no filter/edge credit needed
    rows.append(dict(kernel_hz=frequency,analog_filter_ns=af_ns,rise_ns=rise_ns,
        fall_ns=fall_ns,synchronizer_cycles=sync_cycles,tLOW_ns=low,tHIGH_ns=high,
        setup_ns=setup,hold_effective_ns=hold,data_valid_delay_ns=valid_delay,
        bare_high_count_ns=high_count,bare_low_count_ns=low_count,
        fSCL_model_hz=1e9/(low+high),fSCL_ignoring_all_extra_delays_hz=1e9/(low_count+high_count)))
summary={key:dict(min=min(r[key] for r in rows),max=max(r[key] for r in rows))
         for key in rows[0] if key not in ['kernel_hz','analog_filter_ns','rise_ns','fall_ns','synchronizer_cycles']}
result=dict(result='PASS',analysis='arithmetic, not simulation or physical measurement',
    timing_register=hex(register),fields=fields,clock='HSI64 DIV1 explicitly enabled and selected',
    HSI_tolerance_assumption_percent=5,analog_filter_delay_stress_budget_ns=[50,260],
    filter_note='260 ns is widened AN4235 calculation budget, not H723 datasheet filter maximum',
    DNF=0,requirements=dict(fSCL_max_hz=100000,tLOW_min_ns=4700,tHIGH_min_ns=4000,
        setup_min_ns=250,hold_min_ns=0,stop_setup_min_ns=4700,repeated_start_setup_min_ns=4700,
        bus_free_min_ns=4700),
    prior=dict(register='0x10909CEC',assumed_kernel_hz=137500000,
        bare_tLOW_ns=237*2/137500000*1e9,bare_tHIGH_ns=157*2/137500000*1e9,
        frequency_without_extra_delays_hz=137500000/(2*(237+157))),
    summary=summary,corners=rows,
    references=[dict(document='CS4272 DS593F2 October2021',page=21,
        section='SWITCHING CHARACTERISTICS I2C MODE CONTROL PORT',
        url='https://statics.cirrus.com/pubs/proDatasheet/CS4272_F2.pdf'),
        dict(document='ST AN4235 Rev2 August2013',pages='6-9',
        section='I2C timing field and synchronization equations; F0/F3 note used only as same-IP calculation model',
        url='https://www.st.com/resource/en/application_note/an4235-i2c-timing-configuration-tool-for-stm32f3xxxx-and-stm32f0xxxx-microcontrollers-stmicroelectronics.pdf'),
        dict(document='ST DS13313 Rev5 May2025',pages='116,196',tables='36,105,106',
        section='HSI, I2C clock requirements and filter characteristics; widened corner assumptions explicitly identified',
        url='https://www.st.com/resource/en/datasheet/stm32h723ve.pdf'),
        dict(document='Local official STM32H7 HAL/CMSIS headers',
        section='RCC_HSI_DIV1, RCC_I2C123CLKSOURCE_HSI, TIMINGR fields and filter APIs')],
    limitations=['Clock arithmetic and BSP static binding do not measure SCL/SDA waveforms.',
        'Board pullups/capacitance must keep rise<=1us and fall<=300ns.',
        '.ioc remains stale; current configuration is in BSP, not regenerated CubeMX.',
        'Validate tBUF/tSU:STA/tSU:STO and ACK sequence with scope or logic analyzer.'])
out=root/'output/auditoria_rev49/VALIDACAO/embedded/i2c_timing_corners.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print('PASS:',len(rows),'I2C timing corners;',hex(register),'; conservative clock maximum',summary['fSCL_ignoring_all_extra_delays_hz']['max'],'Hz')
print(json.dumps(summary,indent=2))
