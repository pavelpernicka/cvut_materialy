#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

# Load the sample
raw = np.fromfile("tools/samples/latest_500ksps.cu8", dtype=np.uint8)
iq = ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

print(f"Sample size: {iq.size} complex samples ({raw.size} bytes)")

# Calculate power
power = np.abs(iq)**2

# Find burst regions by power threshold
threshold = np.percentile(power, 98)
burst_mask = power > threshold
burst_indices = np.where(burst_mask)[0]

if len(burst_indices) > 0:
    # Find burst start/end boundaries
    diff = np.diff(burst_indices)
    gaps = np.where(diff > 1000)[0]  # gaps larger than 1000 samples

    burst_starts = [burst_indices[0]]
    burst_ends = []

    for gap_idx in gaps:
        burst_ends.append(burst_indices[gap_idx])
        if gap_idx + 1 < len(burst_indices):
            burst_starts.append(burst_indices[gap_idx + 1])

    burst_ends.append(burst_indices[-1])

    print(f"\nFound {len(burst_starts)} bursts:")
    for i, (start, end) in enumerate(zip(burst_starts, burst_ends)):
        print(f"  Burst {i+1}: samples {start}..{end} (length {end-start})")

        # Analyze frequency content of first burst
        if i == 0:
            burst_data = iq[start:end]

            # FFT analysis
            fft = np.fft.fft(burst_data)
            freqs = np.fft.fftfreq(len(burst_data), 1/500000)  # 500kHz sample rate
            fft_mag = np.abs(fft)

            # Find peak frequency
            peak_idx = np.argmax(fft_mag)
            peak_freq = freqs[peak_idx]

            print(f"    Peak frequency offset: {peak_freq/1000:.1f} kHz")

            # Check around +31kHz as mentioned in README
            target_freq = 31000  # Hz
            target_idx = np.argmin(np.abs(freqs - target_freq))
            target_power = fft_mag[target_idx]
            peak_power = fft_mag[peak_idx]

            print(f"    Power at +31kHz: {target_power:.1e}")
            print(f"    Peak power: {peak_power:.1e}")
            print(f"    Power ratio (31kHz/peak): {target_power/peak_power:.3f}")
else:
    print("No bursts found!")