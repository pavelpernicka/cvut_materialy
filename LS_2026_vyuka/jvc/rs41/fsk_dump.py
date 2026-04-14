#!/usr/bin/env python3
import sys
import math

SAMPLE_RATE = 500_000
DECIM = 10
SAMPLES_PER_SYMBOL = 900
EFF_SPS = SAMPLES_PER_SYMBOL // DECIM

SYNC_HEX = "2dd45253"
WINDOW_IQ = 500_000
STEP_IQ = 100_000

def hex_to_bits(hex_string):
    out = []
    for b in bytes.fromhex(hex_string):
        for i in range(7, -1, -1):
            out.append((b >> i) & 1)
    return out

def bits_to_hex(bits):
    n = len(bits) // 8
    out = bytearray()
    for i in range(n):
        b = 0
        for j in range(8):
            b = (b << 1) | bits[i * 8 + j]
        out.append(b)
    return out.hex()

def iq_bytes_to_complex(data):
    out = []
    n = len(data) // 2
    for i in range(n):
        iv = (data[2 * i] - 127.5) / 128.0
        qv = (data[2 * i + 1] - 127.5) / 128.0
        out.append(complex(iv, qv))
    return out

def fm_demod(iq):
    out = []
    for i in range(1, len(iq)):
        a = iq[i - 1]
        b = iq[i]
        cross = a.real * b.imag - a.imag * b.real
        dot = a.real * b.real + a.imag * b.imag
        out.append(math.atan2(cross, dot))
    return out

def moving_average_decimate(x, decim):
    out = []
    i = 0
    while i + decim <= len(x):
        s = 0.0
        for j in range(decim):
            s += x[i + j]
        out.append(s / decim)
        i += decim
    return out

def slice_bits(x, sps, offset):
    bits = []
    i = offset
    while i + sps <= len(x):
        s = 0.0
        for j in range(sps):
            s += x[i + j]
        avg = s / sps
        bits.append(1 if avg >= 0 else 0)
        i += sps
    return bits

def find_pattern(bits, pat):
    limit = len(bits) - len(pat) + 1
    for i in range(limit):
        ok = True
        for j in range(len(pat)):
            if bits[i + j] != pat[j]:
                ok = False
                break
        if ok:
            return i
    return -1

def try_decode(iq):
    dem = fm_demod(iq)
    if len(dem) < 1000:
        return []

    ds = moving_average_decimate(dem, DECIM)
    sync_bits = hex_to_bits(SYNC_HEX)
    found = []

    for offset in range(EFF_SPS):
        bits = slice_bits(ds, EFF_SPS, offset)

        p = find_pattern(bits, sync_bits)
        if p >= 0:
            pkt = bits[p:p + 8 * 64]
            found.append(("normal", offset, p, bits_to_hex(pkt)))

        inv = [1 - b for b in bits]
        p = find_pattern(inv, sync_bits)
        if p >= 0:
            pkt = inv[p:p + 8 * 64]
            found.append(("inverted", offset, p, bits_to_hex(pkt)))

    return found

def main():
    buf = bytearray()
    last_print = None

    while True:
        chunk = sys.stdin.buffer.read(262144)
        if not chunk:
            break

        buf.extend(chunk)

        while len(buf) >= 2 * WINDOW_IQ:
            window = bytes(buf[:2 * WINDOW_IQ])
            iq = iq_bytes_to_complex(window)
            found = try_decode(iq)

            if found:
                for mode, offset, pos, hx in found:
                    if hx != last_print:
                        print(f"{mode} offset={offset} pos={pos} hex={hx}", flush=True)
                        last_print = hx
            else:
                print("debug: no sync in current window", flush=True)

            del buf[:2 * STEP_IQ]

if __name__ == "__main__":
    main()

