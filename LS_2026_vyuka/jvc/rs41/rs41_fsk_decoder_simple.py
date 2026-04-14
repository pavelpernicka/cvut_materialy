#!/usr/bin/env python3
"""
Simple, robust RS41 FSK decoder using proven signal processing techniques
Based on GNU Radio and established DSP practices
"""

import argparse
import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES, dewhiten_packet, crc16_ccitt_false

def load_iq_file(filename):
    """Load IQ data from rtl_sdr cu8 format"""
    try:
        raw = np.fromfile(filename, dtype=np.uint8)
        if len(raw) % 2 != 0:
            raw = raw[:-1]  # Remove last byte if odd length

        # Convert to complex float
        i_data = raw[0::2].astype(np.float32) - 127.5
        q_data = raw[1::2].astype(np.float32) - 127.5

        # Normalize to [-1, 1]
        iq_data = (i_data + 1j * q_data) / 127.5

        return iq_data
    except Exception as e:
        print(f"Error loading IQ file: {e}")
        return None

def find_signal_frequency(iq_data, sample_rate, fft_size=8192):
    """Find the strongest signal frequency using FFT"""
    # Find high-power region first
    power = np.abs(iq_data)**2
    threshold = np.percentile(power, 95)
    high_power_indices = np.where(power > threshold)[0]

    if len(high_power_indices) == 0:
        return 31000  # Default fallback

    # Use middle of high-power region
    start_idx = high_power_indices[len(high_power_indices)//2]
    end_idx = min(start_idx + fft_size, len(iq_data))

    if end_idx - start_idx < fft_size//2:
        start_idx = max(0, end_idx - fft_size)

    fft_data = np.fft.fft(iq_data[start_idx:end_idx])
    fft_mag = np.abs(fft_data)

    # Find peak frequency (exclude DC)
    fft_mag[0] = 0  # Remove DC component
    peak_bin = np.argmax(fft_mag)
    freq_resolution = sample_rate / len(fft_data)

    if peak_bin > len(fft_data) // 2:
        peak_freq = (peak_bin - len(fft_data)) * freq_resolution
    else:
        peak_freq = peak_bin * freq_resolution

    # If detected frequency is too close to zero, try 31kHz offset
    if abs(peak_freq) < 5000:
        peak_freq = 31000

    return peak_freq

def frequency_shift(iq_data, shift_freq, sample_rate):
    """Shift signal frequency (mix to baseband)"""
    t = np.arange(len(iq_data)) / sample_rate
    lo = np.exp(-1j * 2 * np.pi * shift_freq * t)
    return iq_data * lo

def lowpass_filter(data, cutoff_freq, sample_rate, order=5):
    """Apply lowpass filter"""
    nyquist = sample_rate / 2
    normal_cutoff = cutoff_freq / nyquist
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
    return signal.filtfilt(b, a, data)

def fsk_demodulate(iq_data):
    """FSK demodulation using frequency discriminator"""
    # Frequency discriminator: diff(angle(signal))
    angles = np.angle(iq_data[1:] * np.conj(iq_data[:-1]))

    # Remove DC component
    demod_signal = angles - np.mean(angles)

    return demod_signal

def clock_recovery(demod_signal, sample_rate, symbol_rate, phase_offset=0):
    """Clock recovery with phase offset support"""
    samples_per_symbol = sample_rate / symbol_rate

    # Start sampling from phase_offset
    start_sample = phase_offset
    symbol_centers = np.arange(start_sample + samples_per_symbol/2, len(demod_signal), samples_per_symbol)

    # Extract symbols
    symbols = []
    for center in symbol_centers:
        center = int(center)
        if center < len(demod_signal):
            # Average around symbol center for noise reduction
            window = max(1, int(samples_per_symbol/8))
            start = max(0, center - window)
            end = min(len(demod_signal), center + window)
            symbol_value = np.mean(demod_signal[start:end])
            symbols.append(symbol_value)

    return np.array(symbols)

def symbols_to_bits(symbols, adaptive_threshold=True):
    """Convert symbols to bits using threshold"""
    if adaptive_threshold:
        # Use median as threshold for better noise immunity
        threshold = np.median(symbols)
    else:
        threshold = 0.0

    return (symbols > threshold).astype(int)

def find_sync_pattern(bits, sync_pattern, max_errors=3):
    """Find sync pattern in bit stream with error tolerance"""
    sync_positions = []

    for i in range(len(bits) - len(sync_pattern) + 1):
        errors = np.sum(bits[i:i+len(sync_pattern)] != sync_pattern)
        if errors <= max_errors:
            sync_positions.append((i, errors))

    return sync_positions

def extract_packet(bits, sync_pos, packet_bits=384):
    """Extract packet after sync pattern"""
    packet_start = sync_pos + 16  # 16-bit sync pattern
    packet_end = packet_start + packet_bits

    if packet_end <= len(bits):
        packet_bits_data = bits[packet_start:packet_end]
        # Convert bits to bytes
        packet_bytes = np.packbits(packet_bits_data).tobytes()
        return packet_bytes

    return None

def process_iq_data(iq_data, sample_rate=500000, verbose=False):
    """Process IQ data to extract RS41 packets"""
    if verbose:
        print(f"Processing {len(iq_data)} samples at {sample_rate} Hz")

    # 1. Find signal frequency
    signal_freq = find_signal_frequency(iq_data, sample_rate)
    if verbose:
        print(f"Detected signal frequency: {signal_freq:.0f} Hz")

    # 2. Mix to baseband
    baseband = frequency_shift(iq_data, signal_freq, sample_rate)

    # 3. Decimate and filter
    decimation = 4
    new_sample_rate = sample_rate // decimation

    # Lowpass filter before decimation
    cutoff = new_sample_rate / 4
    filtered = lowpass_filter(baseband, cutoff, sample_rate)

    # Decimate
    decimated = filtered[::decimation]

    if verbose:
        print(f"After decimation: {len(decimated)} samples at {new_sample_rate} Hz")

    # 4. FSK demodulation
    demod = fsk_demodulate(decimated)

    # 5. Symbol extraction (try multiple symbol rates)
    symbol_rates = [1200, 600, 2400]  # Try different rates
    sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8))

    packets_found = []

    for symbol_rate in symbol_rates:
        if verbose:
            print(f"Trying symbol rate: {symbol_rate} bps")

        samples_per_symbol = new_sample_rate / symbol_rate

        # Try multiple phase offsets
        for phase_offset in range(0, int(samples_per_symbol), max(1, int(samples_per_symbol/16))):
            symbols = clock_recovery(demod, new_sample_rate, symbol_rate, phase_offset)

            # Try both polarities
            for polarity, polarity_name in [(1, "normal"), (-1, "inverted")]:
                bits = symbols_to_bits(polarity * symbols)

                # Find sync pattern
                sync_positions = find_sync_pattern(bits, sync_bits)

                if verbose and sync_positions and phase_offset == 0:
                    print(f"  {polarity_name}: Found {len(sync_positions)} sync candidates")

                for sync_pos, errors in sync_positions:
                packet_bytes = extract_packet(bits, sync_pos)

                if packet_bytes and len(packet_bytes) == 48:
                    # Check if it's a valid RS41 packet
                    if packet_bytes[:2] == b'\x52\x53':  # Magic bytes
                        parsed = parse_packet(packet_bytes)

                        if parsed:
                            packets_found.append({
                                'packet': parsed,
                                'raw': packet_bytes,
                                'symbol_rate': symbol_rate,
                                'polarity': polarity_name,
                                'sync_pos': sync_pos,
                                'sync_errors': errors
                            })
                            if verbose:
                                print(f"    ✓ Valid packet: {format_packet(parsed)}")
                        else:
                            # Manual decode for debugging
                            try:
                                seq = int.from_bytes(packet_bytes[4:6], 'little')
                                uptime = int.from_bytes(packet_bytes[6:10], 'little')

                                # Check CRC manually for debugging
                                dewhitened = dewhiten_packet(packet_bytes)
                                crc_rx = int.from_bytes(dewhitened[-2:], 'little')
                                crc_calc = crc16_ccitt_false(dewhitened[:-2])

                                # Only report if sequence looks reasonable
                                if 0 < seq < 100000 and 0 < uptime < 5000000000:
                                    if verbose:
                                        print(f"    ⚠ CRC error: seq={seq} uptime={uptime/3600000:.1f}h")
                                        print(f"      Frame: {packet_bytes[:16].hex()}...")
                                        print(f"      CRC: rx=0x{crc_rx:04x} calc=0x{crc_calc:04x}")

                                    # Still add to results as potential packet
                                    packets_found.append({
                                        'packet': None,
                                        'raw': packet_bytes,
                                        'symbol_rate': symbol_rate,
                                        'polarity': polarity_name,
                                        'sync_pos': sync_pos,
                                        'sync_errors': errors,
                                        'seq': seq,
                                        'uptime': uptime,
                                        'crc_error': True
                                    })
                            except:
                                pass

    return packets_found

def parse_urh_data(hex_string):
    """Parse URH hex data directly"""
    try:
        # Remove whitespace
        hex_clean = ''.join(hex_string.split())
        data_bytes = bytes.fromhex(hex_clean)

        # Find sync pattern
        sync_bytes = SYNC_BYTES
        packets = []

        i = 0
        while i < len(data_bytes) - len(sync_bytes):
            if data_bytes[i:i+len(sync_bytes)] == sync_bytes:
                packet_start = i + len(sync_bytes)
                if packet_start + 48 <= len(data_bytes):
                    packet_bytes = data_bytes[packet_start:packet_start + 48]

                    parsed = parse_packet(packet_bytes)
                    if parsed:
                        packets.append({
                            'packet': parsed,
                            'raw': packet_bytes,
                            'source': 'URH'
                        })

                i = packet_start + 48
            else:
                i += 1

        return packets
    except Exception as e:
        print(f"Error parsing URH data: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description='Simple RS41 FSK Decoder')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--input', default='tools/samples/latest_500ksps.cu8', help='Input IQ file')
    parser.add_argument('--urh-data', help='URH hex data string')
    parser.add_argument('--sample-rate', type=int, default=500000, help='Sample rate (Hz)')

    args = parser.parse_args()

    # Handle URH data
    if args.urh_data:
        print("🔍 Processing URH data...")
        packets = parse_urh_data(args.urh_data)

        for i, pkt_info in enumerate(packets, 1):
            print(f"[{i}] ✓ {format_packet(pkt_info['packet'])}")
            if args.verbose:
                print(f"    Frame: {pkt_info['raw'].hex()}")

        print(f"Found {len(packets)} packets")
        return

    # Process IQ file
    print(f"📡 Loading IQ file: {args.input}")
    iq_data = load_iq_file(args.input)

    if iq_data is None:
        print("❌ Failed to load IQ file")
        return

    packets = process_iq_data(iq_data, args.sample_rate, args.verbose)

    # Display results
    if packets:
        valid_packets = [p for p in packets if p.get('packet')]
        crc_error_packets = [p for p in packets if p.get('crc_error')]

        if valid_packets:
            print(f"\n📊 Found {len(valid_packets)} valid RS41 packets:")
            for i, pkt_info in enumerate(valid_packets, 1):
                print(f"[{i}] ✓ {format_packet(pkt_info['packet'])}")
                if args.verbose:
                    print(f"    Rate: {pkt_info['symbol_rate']} bps, {pkt_info['polarity']}")
                    print(f"    Frame: {pkt_info['raw'].hex()}")

        if crc_error_packets:
            print(f"\n⚠️  Found {len(crc_error_packets)} packets with CRC errors:")
            for i, pkt_info in enumerate(crc_error_packets, 1):
                seq = pkt_info.get('seq', 0)
                uptime = pkt_info.get('uptime', 0)
                print(f"[{i}] ❌ seq={seq} uptime={uptime/3600000:.1f}h (CRC error)")
                if args.verbose:
                    print(f"    Rate: {pkt_info['symbol_rate']} bps, {pkt_info['polarity']}")
                    print(f"    Frame: {pkt_info['raw'][:16].hex()}...")

        if not valid_packets and not crc_error_packets:
            print("❌ No RS41 packets found")
    else:
        print("❌ No RS41 packets found")

if __name__ == "__main__":
    main()