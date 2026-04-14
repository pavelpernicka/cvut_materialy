#!/usr/bin/env python3

import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size < 2 or (raw.size % 2) != 0:
        raise ValueError("input file does not contain valid rtl_sdr cu8 IQ data")
    return ((raw[0::2].astype(np.float32) - 127.5) +
            1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def analyze_spectrum(rf, fs=500000):
    """Analyze spectrum to find signal characteristics"""

    print(f"Analyzing {len(rf)} samples at {fs} Hz")

    # Find signal bursts
    power = np.abs(rf)**2
    threshold = np.percentile(power, 98)
    burst_mask = power > threshold
    burst_indices = np.where(burst_mask)[0]

    if len(burst_indices) > 0:
        # Find burst boundaries
        diff = np.diff(burst_indices)
        gaps = np.where(diff > 1000)[0]

        burst_starts = [burst_indices[0]]
        burst_ends = []

        for gap_idx in gaps:
            burst_ends.append(burst_indices[gap_idx])
            if gap_idx + 1 < len(burst_indices):
                burst_starts.append(burst_indices[gap_idx + 1])

        burst_ends.append(burst_indices[-1])

        print(f"Found {len(burst_starts)} bursts:")
        for i, (start, end) in enumerate(zip(burst_starts, burst_ends)):
            print(f"  Burst {i+1}: samples {start}-{end} (length {end-start})")

        # Analyze first substantial burst
        for start, end in zip(burst_starts, burst_ends):
            if end - start > 50000:  # At least 50k samples
                print(f"\nAnalyzing burst {start}-{end}:")

                burst_data = rf[start:end]

                # FFT analysis
                fft = np.fft.fft(burst_data[:65536])  # Use power of 2
                freqs = np.fft.fftfreq(len(fft), 1/fs)
                fft_mag = np.abs(fft)

                # Find peak frequency
                peak_idx = np.argmax(fft_mag)
                peak_freq = freqs[peak_idx]
                print(f"  Peak frequency: {peak_freq:.0f} Hz")

                # Test different frequency offsets around the peak
                for offset in [peak_freq, peak_freq + 1000, peak_freq - 1000, 31000, 0]:
                    print(f"\n  Testing offset: {offset:.0f} Hz")

                    # Mix to baseband
                    bb_lo = np.exp(1j * (2 * np.pi * (-offset / fs) * np.arange(len(burst_data))))
                    bb = burst_data * bb_lo

                    # Simple decimation
                    bb_dec = bb[::2]  # Decimate by 2
                    bb_fs = fs // 2

                    # FSK demodulation
                    bb_angle_diff = np.angle(bb_dec[:-1] * np.conj(bb_dec[1:]))
                    dem = bb_angle_diff - np.mean(bb_angle_diff)

                    # Different bit rates
                    for bit_rate in [1200, 2400, 600, 4800]:
                        samples_per_symbol = bb_fs / bit_rate
                        print(f"    Bit rate {bit_rate}: {samples_per_symbol:.1f} samples/symbol")

                        # Simple bit extraction
                        if samples_per_symbol > 1:
                            bits = []
                            for i in range(0, len(dem), int(samples_per_symbol)):
                                if i + int(samples_per_symbol) < len(dem):
                                    symbol = np.mean(dem[i:i+int(samples_per_symbol)])
                                    bits.append(1 if symbol > 0 else 0)

                            if len(bits) > 32:
                                # Check for sync pattern in bits
                                sync_pattern = "0010110111010100"  # 0x2DD4 in binary
                                bit_str = ''.join(map(str, bits))

                                sync_pos = bit_str.find(sync_pattern)
                                if sync_pos >= 0:
                                    print(f"      *** SYNC FOUND at bit {sync_pos}! ***")
                                    # Extract packet after sync
                                    packet_start = sync_pos + len(sync_pattern)
                                    if packet_start + 384 <= len(bits):  # 48 bytes = 384 bits
                                        packet_bits = bits[packet_start:packet_start + 384]
                                        packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
                                        print(f"      Packet: {packet_bytes[:8].hex()}...")
                                        if packet_bytes[:2].hex() == "5253":
                                            print(f"      *** CORRECT MAGIC! ***")

                                # Also check inverted bits
                                inv_bits = [1-b for b in bits]
                                inv_bit_str = ''.join(map(str, inv_bits))
                                sync_pos = inv_bit_str.find(sync_pattern)
                                if sync_pos >= 0:
                                    print(f"      *** INVERTED SYNC FOUND at bit {sync_pos}! ***")
                                    packet_start = sync_pos + len(sync_pattern)
                                    if packet_start + 384 <= len(inv_bits):
                                        packet_bits = inv_bits[packet_start:packet_start + 384]
                                        packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
                                        print(f"      Inverted packet: {packet_bytes[:8].hex()}...")
                                        if packet_bytes[:2].hex() == "5253":
                                            print(f"      *** INVERTED CORRECT MAGIC! ***")

                break  # Only analyze first good burst

    else:
        print("No signal bursts found")

# Run analysis
rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")
analyze_spectrum(rf)