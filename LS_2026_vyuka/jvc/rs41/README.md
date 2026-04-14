# RS41 RSM4x2 Telemetry Notes

This file is for the next agent or developer session. It describes the current RF format, firmware TX path, and receiver tooling.

## Current State

The project no longer uses APRS/Bell 202.

Current firmware now transmits a custom binary telemetry packet using the `Si4032` packet/FIFO path instead of the older direct async FSK bit-banging on `PB15`.

Current goals of this change:

- make the TX symbol timing stable enough for `rtl_433`
- keep a simple extensible binary payload
- preserve GPS + onboard sensor telemetry

Status after the current change:

- firmware build passes
- Python receiver tooling syntax passes
- packet parser supports both old `v1` whitened frames and new `v2` unwhitened frames
- live RF reception with the new firmware still needs on-air verification on hardware

## Hardware Target

- MCU: `STM32F100C8T6`
- Radio: `Si4032`
- `SPI2`: `PB13/PB14/PB15`
- Radio chip select `nSEL`: `PC13`
- GPS UART: `USART1` on `PA9/PA10`
- LEDs: `PB8` red, `PB7` green

Important wiring note:

- `PC13` is the `Si4032` chip select.
- `PB15` is the shared `SPI2 MOSI / Si4032 SDI` line.
- The current firmware does not use `PB15` as a manually toggled modulation pin anymore.

## Firmware TX Path

Main files:

- [include/board.h](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/include/board.h)
- [include/protocol.h](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/include/protocol.h)
- [src/protocol.c](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/src/protocol.c)
- [src/si4032.c](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/src/si4032.c)

Current on-air settings:

- frequency: `433.920 MHz`
- bitrate: `2400 bps`
- deviation register: `0x08`
- preamble: `32` bytes of `0xAA`
- sync word: `0x2D D4 4B 59`
- packet length: `48` bytes
- telemetry interval: `10 s`

Current TX sequence:

1. `si4032_init()`
2. configure `Si4032` packet handler / FIFO mode
3. clear TX FIFO
4. set fixed TX packet length to `48`
5. write payload into radio FIFO through SPI
6. start TX
7. wait for `packet sent`
8. return radio to ready state

Implementation detail:

- `src/si4032.c` now uses the `Si4032` packet engine, not software-timed GPIO bit output.
- This should be much friendlier to `rtl_433` than the previous direct-mode waveform.

## Packet Format

Packet builder: [src/protocol.c](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/src/protocol.c)

Total payload after sync: `48` bytes.

Layout:

- `0..1`: ASCII magic `RS`
- `2`: protocol version
- `3`: flags
- `4..5`: sequence number, `u16 LE`
- `6..9`: `uptime_ms`, `u32 LE`
- `10`: TLV payload length
- `11`: reserved, currently `0`
- `12..45`: TLV payload area
- `46..47`: `CRC16-CCITT-FALSE` over bytes `0..45`

Flags:

- bit `0`: GPS position valid
- bit `1`: GPS altitude valid
- bit `2`: GPS speed valid

Current TLVs:

- `0x01` board status
  - `battery_mv` as `u16 LE`
  - `mcu_temp_centi` as `s16 LE`
- `0x03` GPS motion
  - `speed_cms` as `u16 LE`
  - `satellites` as `u8`
- `0x02` GPS position
  - `latitude_e7` as `s32 LE`
  - `longitude_e7` as `s32 LE`
  - `altitude_cm` as `s32 LE`

Extensibility note:

- TLV layout was kept intentionally, so adding more board sensors later does not require changing the radio framing.

## Protocol Versions

- `v1`: old direct-FSK format, whitened payload, `2-byte` sync `0x2DD4`
- `v2`: current packet/FIFO format, unwhitened payload, `4-byte` sync `0x2DD44B59`

Current firmware transmits `v2`.

The parser in [tools/telemetry_packet.py](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/tools/telemetry_packet.py) accepts both versions so old captures remain useful.

## Receiver Path

Default receiver is now [tools/rx.py](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/tools/rx.py).

It does this:

1. runs `rtl_433` with a flex decoder for `FSK_PCM`
2. asks `rtl_433` for JSON output
3. reads `rows[0].data` as hex
4. finds sync `2dd44b59`
5. extracts the following `48` bytes
6. parses the payload with [tools/telemetry_packet.py](/home/pavel/skola/LS_2026_vyuka/jvc/rs41/tools/telemetry_packet.py)

Live receive command:

```sh
python3 tools/rx.py --freq 433.92e6 --gain 15 --ppm 20
```

Offline decode of a saved IQ file:

```sh
python3 tools/decode_sample.py --input-file tools/samples/latest_500ksps.cu8 --sample-rate 500000
```

Capture then decode:

```sh
python3 tools/capture_decode.py --freq 433.92e6 --sample-rate 500000 --gain 15 --ppm 20 --seconds 12
```

## Important Historical Context

The repo previously spent a lot of time debugging a manually demodulated direct-FSK path against URH.

That path is now legacy.

Legacy sample:

- `tools/samples/latest_500ksps.cu8`

Important caveat:

- that sample was captured from the older direct-mode firmware
- it is still useful for old parser sanity checks
- it is not proof that the new `v2` FIFO-based TX is working on-air

## What To Verify Next

The next hardware session should verify these in order:

1. flash the new `build/rs41.bin`
2. confirm SDR shows a stable burst every `10 s`
3. run `python3 tools/rx.py --freq 433.92e6 --gain 15 --ppm 20`
4. if no frames appear, run `rtl_433` directly with `-v` and inspect the JSON `rows[0].data`
5. confirm the extracted row contains sync `2dd44b59` followed by `48` payload bytes

If RX still fails after that, the likely remaining issues are:

- `rtl_433` timing parameters need adjustment for the new waveform
- `Si4032` packet-mode register values need minor correction
- actual over-the-air bitrate/deviation differs from the intended settings
