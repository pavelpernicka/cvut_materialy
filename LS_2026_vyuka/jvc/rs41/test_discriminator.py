#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

# Load a burst from the sample
raw = np.fromfile("tools/samples/latest_500ksps.cu8", dtype=np.uint8)
iq = ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

# Extract first burst
burst_start, burst_end = 343087, 449330
burst_iq = iq[burst_start:burst_end]

print(f"Burst length: {len(burst_iq)} samples")

# Apply frequency correction
fft = np.fft.fft(burst_iq)
freqs = np.fft.fftfreq(len(burst_iq), 1/500000)
peak_idx = np.argmax(np.abs(fft))
peak_freq = freqs[peak_idx]

print(f"Peak frequency: {peak_freq/1000:.1f} kHz")

t = np.arange(len(burst_iq)) / 500000
correction = np.exp(-1j * 2 * np.pi * peak_freq * t).astype(np.complex64)
corrected_iq = burst_iq * correction

# Test different discriminator approaches
discrim1 = np.angle(corrected_iq[1:] * np.conj(corrected_iq[:-1])).astype(np.float32)
discrim2 = np.diff(np.unwrap(np.angle(corrected_iq))).astype(np.float32)

print(f"Discriminator 1 range: [{discrim1.min():.4f}, {discrim1.max():.4f}]")
print(f"Discriminator 2 range: [{discrim2.min():.4f}, {discrim2.max():.4f}]")

# Try with different center values
for center in [0.0, 0.01, 0.05, 0.0563, 0.1]:
    bits = (discrim1 > center).astype(np.uint8)
    ones_percent = np.mean(bits) * 100
    print(f"Center {center:6.4f}: {ones_percent:5.1f}% ones")

# Use the same adaptive center calculation as the decoder
p25 = np.percentile(discrim1, 25)
p75 = np.percentile(discrim1, 75)
center = (p25 + p75) / 2.0
print(f"Adaptive center: {center:.6f} (from p25={p25:.6f}, p75={p75:.6f})")
sps = 200  # samples per symbol
phase = 100  # arbitrary phase offset

# Manual bit slicing (using cumulative sum approach like the decoder)
csum = np.concatenate((np.array([0.0], dtype=np.float64), np.cumsum(discrim1, dtype=np.float64)))
starts = np.arange(phase, len(discrim1) - sps + 1, sps, dtype=np.int32)
if len(starts) > 0:
    ends = starts + sps
    sums = csum[ends] - csum[starts]
    means = sums / sps
    bits = (means > center).astype(np.uint8)

    print(f"Got {len(bits)} bits")
    print(f"First 32 bits: {''.join(map(str, bits[:32]))}")
    print(f"Mean values (first 10): {means[:10]}")
    print(f"Min/max mean: {means.min():.6f} / {means.max():.6f}")

    # Try different phases
    for test_phase in [0, 50, 100, 150]:
        starts = np.arange(test_phase, len(discrim1) - sps + 1, sps, dtype=np.int32)[:10]
        if len(starts) > 0:
            ends = starts + sps
            sums = csum[ends] - csum[starts]
            means_test = sums / sps
            bits_test = (means_test > center).astype(np.uint8)
            print(f"Phase {test_phase:3d}: bits={''.join(map(str, bits_test))} means=[{means_test[0]:.4f}, {means_test[1]:.4f}, ...]")

    # Search for sync pattern in the main bit stream
    sync_bits = np.unpackbits(np.array([0x2D, 0xD4], dtype=np.uint8), bitorder="big")
    print(f"Sync pattern: {''.join(map(str, sync_bits))}")

    # Search for sync in extracted bits
    for i in range(min(200, len(bits) - len(sync_bits))):
        errors = np.sum(bits[i:i+len(sync_bits)] != sync_bits)
        if errors <= 2:  # allow some errors
            print(f"Found sync at bit {i} with {errors} errors")
            print(f"  Context: {''.join(map(str, bits[max(0,i-8):i+len(sync_bits)+8]))}")
            packet_start = i + len(sync_bits)
            if packet_start + 48*8 <= len(bits):
                packet_bits = bits[packet_start:packet_start + 48*8]
                packet_bytes = np.packbits(packet_bits, bitorder="big")
                print(f"  Packet: {packet_bytes[:8].tobytes().hex()}")

                # Test if this packet parses
                from tools.telemetry_packet import parse_packet, format_packet
                parsed = parse_packet(packet_bytes.tobytes())
                if parsed:
                    print(f"  ✓ Valid packet: {format_packet(parsed)}")
                    break