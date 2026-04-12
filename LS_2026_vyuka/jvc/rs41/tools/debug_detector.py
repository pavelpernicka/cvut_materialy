#!/usr/bin/env python3
"""
Debug detector to understand why frames aren't being detected
Shows detailed signal processing steps and thresholds
"""

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import time
import sys
import argparse


def capture_and_analyze(freq=433.92e6, duration=10, sample_rate=250000, gain=35):
    """Capture signal and analyze step by step"""

    print(f"Capturing {duration}s at {freq/1e6:.3f} MHz...")

    # Capture with rtl_sdr
    cmd = [
        "rtl_sdr",
        "-f", str(int(freq)),
        "-s", str(sample_rate),
        "-g", str(gain),
        "-n", str(int(sample_rate * duration)),
        "/tmp/debug_capture.iq"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
        if result.returncode != 0:
            print(f"RTL-SDR error: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print("Capture timeout!")
        return None

    # Load IQ data
    try:
        iq_data = np.fromfile("/tmp/debug_capture.iq", dtype=np.uint8)
        if len(iq_data) < 2:
            print("No data captured!")
            return None

        # Convert to complex
        iq_data = iq_data.astype(np.float32)
        iq_complex = (iq_data[0::2] - 127.5) + 1j * (iq_data[1::2] - 127.5)
        iq_complex /= 127.5  # Normalize

        print(f"Loaded {len(iq_complex)} IQ samples")

        import os
        os.remove("/tmp/debug_capture.iq")

        return iq_complex

    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def analyze_signal_step_by_step(iq_data, sample_rate=250000):
    """Analyze the signal processing chain step by step"""

    print("\n=== STEP-BY-STEP SIGNAL ANALYSIS ===")

    # Step 1: Raw signal analysis
    print(f"\nStep 1: Raw Signal Analysis")
    magnitude = np.abs(iq_data)
    print(f"  - Signal RMS: {np.sqrt(np.mean(magnitude**2)):.4f}")
    print(f"  - Signal peak: {np.max(magnitude):.4f}")
    print(f"  - Signal mean: {np.mean(magnitude):.4f}")

    # Look for activity bursts
    mag_threshold = np.mean(magnitude) + 2 * np.std(magnitude)
    active_samples = np.sum(magnitude > mag_threshold)
    print(f"  - Activity threshold: {mag_threshold:.4f}")
    print(f"  - Active samples: {active_samples} ({100*active_samples/len(magnitude):.1f}%)")

    # Step 2: Frequency analysis
    print(f"\nStep 2: Frequency Analysis")
    if len(iq_data) > 1:
        # Instantaneous frequency
        phase_diff = np.angle(iq_data[1:] * np.conj(iq_data[:-1]))
        inst_freq = phase_diff * sample_rate / (2 * np.pi)

        print(f"  - Freq deviation RMS: {np.sqrt(np.mean(inst_freq**2)):.0f} Hz")
        print(f"  - Freq deviation peak: ±{np.max(np.abs(inst_freq)):.0f} Hz")
        print(f"  - Freq deviation mean: {np.mean(inst_freq):.0f} Hz")

        # Check for FSK-like activity
        freq_threshold = np.mean(np.abs(inst_freq)) + 2 * np.std(np.abs(inst_freq))
        freq_active = np.sum(np.abs(inst_freq) > freq_threshold)
        print(f"  - Freq activity threshold: {freq_threshold:.0f} Hz")
        print(f"  - Freq active samples: {freq_active} ({100*freq_active/len(inst_freq):.1f}%)")

    # Step 3: Decimation test
    print(f"\nStep 3: Decimation Test")
    from scipy import signal as sig

    decimation = 4
    bb_fs = sample_rate // decimation
    print(f"  - Decimation factor: {decimation}x")
    print(f"  - Baseband rate: {bb_fs} Hz")

    try:
        # Simple decimation
        dec_filter = sig.butter(3, 1 / (decimation * 2))
        bb = sig.filtfilt(*dec_filter, iq_data)
        bb = bb[::decimation]

        bb_mag = np.abs(bb)
        print(f"  - Baseband samples: {len(bb)}")
        print(f"  - Baseband RMS: {np.sqrt(np.mean(bb_mag**2)):.4f}")
        print(f"  - Baseband peak: {np.max(bb_mag):.4f}")

        # Activity detection
        bb_threshold = np.mean(bb_mag) + 2 * np.std(bb_mag)
        bb_active = np.sum(bb_mag > bb_threshold)
        print(f"  - Baseband threshold: {bb_threshold:.4f}")
        print(f"  - Baseband active: {bb_active} ({100*bb_active/len(bb_mag):.1f}%)")

    except Exception as e:
        print(f"  - Decimation error: {e}")
        bb = iq_data[::decimation]  # Simple decimation fallback
        bb_mag = np.abs(bb)

    # Step 4: FM Demodulation test
    print(f"\nStep 4: FM Demodulation Test")
    if len(bb) > 1:
        # FM discrimination
        bb_angle_diff = np.angle(bb[:-1] * np.conj(bb[1:]))
        dem = bb_angle_diff - np.mean(bb_angle_diff)

        print(f"  - Demod samples: {len(dem)}")
        print(f"  - Demod RMS: {np.sqrt(np.mean(dem**2)):.4f}")
        print(f"  - Demod range: [{np.min(dem):.4f}, {np.max(dem):.4f}]")

        # Look for bit-like patterns
        estimated_symbol_rate = 1200
        samples_per_symbol = bb_fs / estimated_symbol_rate
        print(f"  - Expected samples/symbol: {samples_per_symbol:.1f}")

        # Simple bit estimation
        if len(dem) > samples_per_symbol:
            # Resample to symbol rate
            n_symbols = int(len(dem) / samples_per_symbol)
            if n_symbols > 10:
                symbols = []
                for i in range(n_symbols):
                    start_idx = int(i * samples_per_symbol)
                    end_idx = int((i + 1) * samples_per_symbol)
                    if end_idx <= len(dem):
                        symbol_avg = np.mean(dem[start_idx:end_idx])
                        symbols.append(symbol_avg)

                if symbols:
                    bits = [1 if s > 0 else 0 for s in symbols]
                    print(f"  - Estimated symbols: {len(symbols)}")
                    print(f"  - Bit transitions: {np.sum(np.diff(bits) != 0)}")
                    print(f"  - First 32 bits: {''.join(map(str, bits[:32]))}")

                    # Look for sync pattern (0x2dd4 = 0010110111010100)
                    sync_pattern = "0010110111010100"
                    bit_string = ''.join(map(str, bits))

                    sync_found = sync_pattern in bit_string
                    print(f"  - Sync pattern found: {sync_found}")
                    if sync_found:
                        sync_pos = bit_string.find(sync_pattern)
                        print(f"  - Sync position: {sync_pos}")

    return {
        'raw_samples': len(iq_data),
        'active_percent': 100*active_samples/len(magnitude),
        'freq_active_percent': 100*freq_active/len(inst_freq) if len(iq_data) > 1 else 0,
        'baseband_active_percent': 100*bb_active/len(bb_mag)
    }


def create_debug_plots(iq_data, sample_rate=250000):
    """Create detailed debug plots"""

    print(f"\nCreating debug plots...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Signal Detection Debug Analysis')

    # Raw signal magnitude
    magnitude = np.abs(iq_data)
    time_axis = np.arange(len(magnitude)) / sample_rate

    axes[0,0].plot(time_axis, magnitude, 'b-', alpha=0.7)
    axes[0,0].set_title('Raw Signal Magnitude')
    axes[0,0].set_ylabel('Magnitude')
    axes[0,0].grid(True, alpha=0.3)

    # Add activity threshold
    mag_threshold = np.mean(magnitude) + 2 * np.std(magnitude)
    axes[0,0].axhline(mag_threshold, color='r', linestyle='--', label=f'Threshold: {mag_threshold:.3f}')
    axes[0,0].legend()

    # Instantaneous frequency
    if len(iq_data) > 1:
        phase_diff = np.angle(iq_data[1:] * np.conj(iq_data[:-1]))
        inst_freq = phase_diff * sample_rate / (2 * np.pi)
        time_freq = np.arange(len(inst_freq)) / sample_rate

        axes[0,1].plot(time_freq, inst_freq, 'g-', alpha=0.7)
        axes[0,1].set_title('Instantaneous Frequency')
        axes[0,1].set_ylabel('Frequency (Hz)')
        axes[0,1].grid(True, alpha=0.3)

    # Frequency spectrum
    if len(iq_data) > 1024:
        fft_data = np.fft.fft(iq_data[:8192])  # Use first 8k samples
        freqs = np.fft.fftfreq(8192, 1/sample_rate)
        power = 20 * np.log10(np.abs(fft_data) + 1e-10)

        # Show positive frequencies only
        pos_mask = freqs >= 0
        axes[0,2].plot(freqs[pos_mask]/1000, power[pos_mask], 'purple', alpha=0.7)
        axes[0,2].set_title('Signal Spectrum')
        axes[0,2].set_xlabel('Frequency (kHz)')
        axes[0,2].set_ylabel('Power (dB)')
        axes[0,2].grid(True, alpha=0.3)

    # Decimated signal
    from scipy import signal as sig
    decimation = 4
    bb_fs = sample_rate // decimation

    try:
        dec_filter = sig.butter(3, 1 / (decimation * 2))
        bb = sig.filtfilt(*dec_filter, iq_data)
        bb = bb[::decimation]

        bb_mag = np.abs(bb)
        bb_time = np.arange(len(bb_mag)) / bb_fs

        axes[1,0].plot(bb_time, bb_mag, 'm-', alpha=0.7)
        axes[1,0].set_title('Decimated Baseband Magnitude')
        axes[1,0].set_ylabel('Magnitude')
        axes[1,0].set_xlabel('Time (s)')
        axes[1,0].grid(True, alpha=0.3)

        # Add threshold
        bb_threshold = np.mean(bb_mag) + 2 * np.std(bb_mag)
        axes[1,0].axhline(bb_threshold, color='r', linestyle='--', label=f'Threshold: {bb_threshold:.3f}')
        axes[1,0].legend()

        # FM demodulated signal
        if len(bb) > 1:
            bb_angle_diff = np.angle(bb[:-1] * np.conj(bb[1:]))
            dem = bb_angle_diff - np.mean(bb_angle_diff)
            dem_time = np.arange(len(dem)) / bb_fs

            axes[1,1].plot(dem_time, dem, 'r-', alpha=0.7)
            axes[1,1].set_title('FM Demodulated Signal')
            axes[1,1].set_ylabel('Frequency')
            axes[1,1].set_xlabel('Time (s)')
            axes[1,1].grid(True, alpha=0.3)

            # Estimated bit stream
            estimated_symbol_rate = 1200
            samples_per_symbol = bb_fs / estimated_symbol_rate

            if len(dem) > samples_per_symbol * 10:
                n_symbols = int(len(dem) / samples_per_symbol)
                symbols = []
                symbol_times = []

                for i in range(min(n_symbols, 200)):  # Limit to first 200 symbols
                    start_idx = int(i * samples_per_symbol)
                    end_idx = int((i + 1) * samples_per_symbol)
                    if end_idx <= len(dem):
                        symbol_avg = np.mean(dem[start_idx:end_idx])
                        symbols.append(1 if symbol_avg > 0 else 0)
                        symbol_times.append(start_idx / bb_fs)

                axes[1,2].plot(symbol_times, symbols, 'ko-', markersize=3)
                axes[1,2].set_title('Estimated Bit Stream')
                axes[1,2].set_ylabel('Bit Value')
                axes[1,2].set_xlabel('Time (s)')
                axes[1,2].set_ylim(-0.5, 1.5)
                axes[1,2].grid(True, alpha=0.3)

    except Exception as e:
        print(f"Plotting error: {e}")

    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Debug frame detection issues")
    parser.add_argument("--freq", type=float, default=433.92e6, help="Frequency in Hz")
    parser.add_argument("--duration", type=float, default=10, help="Capture duration in seconds")
    parser.add_argument("--sample-rate", type=int, default=250000, help="Sample rate")
    parser.add_argument("--gain", type=float, default=35, help="RF gain")

    args = parser.parse_args()

    print("Frame Detection Debugger")
    print(f"Frequency: {args.freq/1e6:.3f} MHz")
    print(f"Duration: {args.duration} seconds")
    print(f"Sample rate: {args.sample_rate} Hz")
    print(f"Gain: {args.gain} dB")
    print("\nMake sure your GFSK transmitter is active during capture!")

    # Check RTL-SDR
    try:
        subprocess.run(["rtl_sdr"], capture_output=True, timeout=1)
    except FileNotFoundError:
        print("ERROR: rtl_sdr not found!")
        return 1
    except subprocess.TimeoutExpired:
        pass

    # Capture data
    iq_data = capture_and_analyze(args.freq, args.duration, args.sample_rate, args.gain)

    if iq_data is None:
        print("Failed to capture data!")
        return 1

    # Analyze
    stats = analyze_signal_step_by_step(iq_data, args.sample_rate)

    # Show plots
    create_debug_plots(iq_data, args.sample_rate)

    print(f"\n=== SUMMARY ===")
    print(f"Raw signal activity: {stats['active_percent']:.1f}%")
    print(f"Frequency activity: {stats['freq_active_percent']:.1f}%")
    print(f"Baseband activity: {stats['baseband_active_percent']:.1f}%")

    if stats['active_percent'] < 5:
        print("\n⚠️  Very low signal activity - check transmitter and frequency!")
    elif stats['freq_active_percent'] < 10:
        print("\n⚠️  Low frequency activity - signal might not be FSK/GFSK!")
    elif stats['baseband_active_percent'] < 5:
        print("\n⚠️  Low baseband activity - decimation/filtering issue!")
    else:
        print("\n✅ Signal looks good - check sync pattern detection!")

    return 0


if __name__ == "__main__":
    sys.exit(main())