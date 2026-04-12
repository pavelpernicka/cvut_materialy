#!/usr/bin/env python3
"""
Signal analyzer to debug why rtl_433 isn't seeing the GFSK signal
Captures raw IQ data and analyzes signal characteristics
"""

import subprocess
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys
import time
import tempfile
import os


def capture_iq_data(freq, sample_rate, duration, gain, ppm=0):
    """Capture IQ data using rtl_sdr"""

    # Create temporary file for IQ data
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.iq')
    temp_file.close()

    cmd = [
        "rtl_sdr",
        "-f", str(int(freq)),
        "-s", str(sample_rate),
        "-g", str(gain),
        "-n", str(int(sample_rate * duration)),  # Number of samples
        temp_file.name
    ]

    if ppm != 0:
        cmd.extend(["-p", str(ppm)])

    print(f"Capturing {duration}s of IQ data...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)

        if result.returncode != 0:
            print(f"rtl_sdr error: {result.stderr}")
            return None, None

        # Read IQ data
        iq_data = np.fromfile(temp_file.name, dtype=np.uint8)

        if len(iq_data) < 2:
            print("No data captured!")
            return None, None

        # Convert to complex
        iq_data = iq_data.astype(np.float32)
        iq_complex = (iq_data[0::2] - 127.5) + 1j * (iq_data[1::2] - 127.5)

        print(f"Captured {len(iq_complex)} IQ samples")
        return iq_complex, temp_file.name

    except subprocess.TimeoutExpired:
        print("Capture timeout!")
        return None, None
    except Exception as e:
        print(f"Capture error: {e}")
        return None, None
    finally:
        try:
            os.unlink(temp_file.name)
        except:
            pass


def analyze_signal(iq_data, sample_rate, show_plots=True):
    """Analyze the captured IQ data for GFSK characteristics"""

    print("\n=== SIGNAL ANALYSIS ===")

    # Basic statistics
    magnitude = np.abs(iq_data)
    print(f"Signal power: {np.mean(magnitude**2):.2f}")
    print(f"Peak amplitude: {np.max(magnitude):.2f}")
    print(f"RMS amplitude: {np.sqrt(np.mean(magnitude**2)):.2f}")
    print(f"DC offset: I={np.mean(iq_data.real):.2f}, Q={np.mean(iq_data.imag):.2f}")

    # Frequency domain analysis
    fft = np.fft.fftshift(np.fft.fft(iq_data))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(iq_data), 1/sample_rate))
    power_spectrum = 20 * np.log10(np.abs(fft) + 1e-10)

    # Find peak frequency
    peak_idx = np.argmax(power_spectrum)
    peak_freq = freqs[peak_idx]
    peak_power = power_spectrum[peak_idx]

    print(f"Peak frequency offset: {peak_freq:.0f} Hz")
    print(f"Peak power: {peak_power:.1f} dB")

    # Detect bursts based on power
    window_size = int(sample_rate * 0.01)  # 10ms window
    power_envelope = []

    for i in range(0, len(magnitude) - window_size, window_size//4):
        window_power = np.mean(magnitude[i:i+window_size]**2)
        power_envelope.append(window_power)

    power_envelope = np.array(power_envelope)
    median_power = np.median(power_envelope)
    threshold = median_power * 3  # 3x above median

    # Find burst segments
    above_threshold = power_envelope > threshold
    bursts = []

    if np.any(above_threshold):
        # Find burst start/end indices
        diff = np.diff(above_threshold.astype(int))
        starts = np.where(diff == 1)[0] + 1
        ends = np.where(diff == -1)[0] + 1

        # Handle edge cases
        if above_threshold[0]:
            starts = np.concatenate(([0], starts))
        if above_threshold[-1]:
            ends = np.concatenate((ends, [len(above_threshold)]))

        for start, end in zip(starts, ends):
            start_time = start * window_size / 4 / sample_rate
            end_time = end * window_size / 4 / sample_rate
            duration = end_time - start_time
            bursts.append((start_time, end_time, duration))

    print(f"\nDetected {len(bursts)} potential bursts:")
    for i, (start, end, duration) in enumerate(bursts):
        print(f"  Burst {i+1}: {start:.3f}s - {end:.3f}s (duration: {duration*1000:.1f}ms)")

    # Frequency deviation analysis (for GFSK)
    if len(iq_data) > 1:
        # Compute instantaneous frequency
        phase = np.angle(iq_data)
        # Unwrap phase to avoid discontinuities
        phase_unwrapped = np.unwrap(phase)
        # Compute instantaneous frequency
        inst_freq = np.diff(phase_unwrapped) * sample_rate / (2 * np.pi)

        # Remove DC component
        inst_freq = inst_freq - np.mean(inst_freq)

        print(f"\nFrequency deviation analysis:")
        print(f"Max deviation: ±{np.max(np.abs(inst_freq)):.0f} Hz")
        print(f"RMS deviation: ±{np.sqrt(np.mean(inst_freq**2)):.0f} Hz")

        # Look for FSK-like patterns
        if len(inst_freq) > sample_rate // 10:  # At least 100ms of data
            # Quantize to two levels (FSK)
            threshold_freq = np.median(np.abs(inst_freq))
            fsk_bits = inst_freq > threshold_freq

            # Look for bit transitions
            transitions = np.diff(fsk_bits.astype(int))
            transition_rate = np.sum(np.abs(transitions)) / (len(inst_freq) / sample_rate)

            print(f"Estimated symbol rate: {transition_rate:.0f} symbols/sec")

    if show_plots:
        # Create plots
        fig, axes = plt.subplots(3, 2, figsize=(12, 10))
        fig.suptitle('GFSK Signal Analysis')

        # Time domain
        t = np.arange(len(iq_data)) / sample_rate
        axes[0,0].plot(t[:min(len(t), sample_rate//10)], magnitude[:min(len(magnitude), sample_rate//10)])
        axes[0,0].set_title('Signal Magnitude (first 100ms)')
        axes[0,0].set_xlabel('Time (s)')
        axes[0,0].set_ylabel('Magnitude')

        # Power envelope
        t_env = np.arange(len(power_envelope)) * window_size / 4 / sample_rate
        axes[0,1].plot(t_env, power_envelope)
        axes[0,1].axhline(threshold, color='r', linestyle='--', label='Threshold')
        axes[0,1].set_title('Power Envelope')
        axes[0,1].set_xlabel('Time (s)')
        axes[0,1].set_ylabel('Power')
        axes[0,1].legend()

        # Spectrum
        axes[1,0].plot(freqs/1000, power_spectrum)
        axes[1,0].set_title('Power Spectrum')
        axes[1,0].set_xlabel('Frequency (kHz)')
        axes[1,0].set_ylabel('Power (dB)')
        axes[1,0].grid(True)

        # Constellation
        sample_step = max(1, len(iq_data) // 10000)  # Limit to 10k points
        axes[1,1].scatter(iq_data.real[::sample_step], iq_data.imag[::sample_step], alpha=0.1, s=0.5)
        axes[1,1].set_title('Constellation Diagram')
        axes[1,1].set_xlabel('I')
        axes[1,1].set_ylabel('Q')
        axes[1,1].grid(True)

        # Instantaneous frequency
        if len(iq_data) > 1:
            t_freq = np.arange(len(inst_freq)) / sample_rate
            axes[2,0].plot(t_freq[:min(len(t_freq), sample_rate//10)], inst_freq[:min(len(inst_freq), sample_rate//10)])
            axes[2,0].set_title('Instantaneous Frequency (first 100ms)')
            axes[2,0].set_xlabel('Time (s)')
            axes[2,0].set_ylabel('Frequency (Hz)')

        # Histogram of frequency deviation
        if len(inst_freq) > 0:
            axes[2,1].hist(inst_freq, bins=50, alpha=0.7)
            axes[2,1].set_title('Frequency Deviation Distribution')
            axes[2,1].set_xlabel('Frequency (Hz)')
            axes[2,1].set_ylabel('Count')

        plt.tight_layout()
        plt.show()

    return bursts, peak_freq


def main():
    parser = argparse.ArgumentParser(description="Analyze GFSK signal characteristics")
    parser.add_argument("--freq", type=float, default=433.920e6, help="Frequency in Hz")
    parser.add_argument("--sample-rate", type=int, default=250000, help="Sample rate")
    parser.add_argument("--duration", type=float, default=10.0, help="Capture duration in seconds")
    parser.add_argument("--gain", type=float, default=35.0, help="RF gain")
    parser.add_argument("--ppm", type=int, default=0, help="PPM correction")
    parser.add_argument("--no-plots", action="store_true", help="Don't show plots")

    args = parser.parse_args()

    print("GFSK Signal Analyzer")
    print(f"Frequency: {args.freq/1e6:.3f} MHz")
    print(f"Sample rate: {args.sample_rate} Hz")
    print(f"Duration: {args.duration} s")
    print(f"Gain: {args.gain} dB")

    # Check if rtl_sdr is available
    try:
        subprocess.run(["rtl_sdr"], capture_output=True, timeout=1)
    except FileNotFoundError:
        print("ERROR: rtl_sdr not found. Please install rtl-sdr package.")
        return 1
    except subprocess.TimeoutExpired:
        pass  # Normal - rtl_sdr waiting for arguments

    # Capture data
    iq_data, temp_file = capture_iq_data(
        args.freq, args.sample_rate, args.duration, args.gain, args.ppm
    )

    if iq_data is None:
        print("Failed to capture data!")
        return 1

    # Analyze
    bursts, peak_freq = analyze_signal(iq_data, args.sample_rate, not args.no_plots)

    print("\n=== RECOMMENDATIONS ===")
    print(f"For rtl_433, try:")
    print(f"  Frequency offset: {peak_freq:+.0f} Hz")
    print(f"  Detection level: -10.0 to -15.0 dB")
    if bursts:
        avg_duration = np.mean([b[2] for b in bursts]) * 1000
        print(f"  Burst duration: ~{avg_duration:.0f}ms")

    return 0


if __name__ == "__main__":
    sys.exit(main())