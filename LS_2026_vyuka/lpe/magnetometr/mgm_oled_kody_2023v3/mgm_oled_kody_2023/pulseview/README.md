# MMC5883MA I2C Trace For PulseView

This directory contains a synthetic I2C waveform for the transactions used by
`main_example.cpp` through `MMC5883L.cpp`.

Generated files:

- `mmc5883_i2c_example.vcd`: digital waveform for PulseView import
- `mmc5883_i2c_example.csv`: same waveform sampled at 1 MHz
- `generate_mmc5883_i2c_trace.py`: generator script

The trace uses:

- `SCL`: I2C clock
- `SDA`: I2C data
- 100 kHz I2C clock
- 7-bit slave address `0x30`
- write address byte `0x60`
- read address byte `0x61`

Transactions included:

```text
init #1:
  write 0x60 0x08 0x08   Internal Control 0: SET pulse
  write 0x60 0x09 0x00   Internal Control 1: BW=00
  write 0x60 0x0A 0x00   Internal Control 2: continuous mode off

init #2:
  same three writes again, because main_example.cpp calls compass.init()
  after the constructor has already called init()

one measurement:
  write 0x60 0x08 0x01   Internal Control 0: TM_M, start magnetic measurement
  write/read status 0x07 -> 0x00
  write/read status 0x07 -> 0x01
  write/read data from 0x00 -> 6 bytes: Xlow, Xhigh, Ylow, Yhigh, Zlow, Zhigh
```

PulseView import:

1. Open PulseView.
2. Use `File -> Open`.
3. Select `mmc5883_i2c_example.vcd`.
4. Add protocol decoder `I2C`.
5. Assign `SCL` to `SCL` and `SDA` to `SDA`.

Regenerate with a different speed:

```sh
python3 pulseview/generate_mmc5883_i2c_trace.py --i2c-rate 400000
```

## SSD1306 SPI Blink Trace

The OLED display is connected through the software-SPI transport:

- `CLK`: `PA_5`
- `MOSI`: `PA_7`
- `DC`: `PA_6`
- `RST`: `PB_0`
- `CS`: `PA_4`

Generated files:

- `ssd1306_spi_blink.vcd`: digital waveform for PulseView import
- `ssd1306_spi_blink.csv`: same waveform sampled at 1 MHz
- `ssd1306_spi_blink_visible.vcd`: same commands, but slowed down and with a
  shorter idle gap so the pulses are easy to see immediately after opening
- `generate_ssd1306_spi_blink_trace.py`: generator script

This trace captures only the background blinking part:

```text
gOled1.invertDisplay(0);  command 0xA6, SSD1306_NORMALDISPLAY
thread_sleep_for(500);
gOled1.invertDisplay(1);  command 0xA7, SSD1306_INVERTDISPLAY
```

PulseView import:

1. Open PulseView.
2. Use `File -> Open`.
3. Select `ssd1306_spi_blink_visible.vcd` for easy viewing, or
   `ssd1306_spi_blink.vcd` for the original 500 ms blink gap.
4. Add protocol decoder `SPI`.
5. Assign `CLK` to `CLK`, `MOSI` to `MOSI`, and `CS` to `CS`.

The `DC` line is not part of the SPI byte itself. For SSD1306 it tells you
whether the byte is a command or display data. In this blink trace `DC=0`, so
both bytes are commands.

Regenerate with a shorter idle gap for easier viewing:

```sh
python3 pulseview/generate_ssd1306_spi_blink_trace.py --prefix ssd1306_spi_blink_visible --spi-rate 10000 --gap-ms 5
```
