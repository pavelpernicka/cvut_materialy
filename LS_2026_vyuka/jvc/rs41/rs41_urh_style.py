#!/usr/bin/env python3
"""
RS41 decoder inspired by URH (Universal Radio Hacker) methodology
Uses similar signal processing approach as URH but simplified for RS41
"""

import argparse
import numpy as np
import scipy.signal as signal
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES

class URHStyleDecoder:
    def __init__(self, sample_rate=500000):
        self.sample_rate = sample_rate
        self.samples_per_symbol = 200  # Start with URH default
        self.center = 0.0465  # URH center value from screenshot

    def load_iq_file(self, filename):
        """Load IQ data from rtl_sdr cu8 format"""
        raw = np.fromfile(filename, dtype=np.uint8)
        if len(raw) % 2 != 0:
            raw = raw[:-1]

        # Convert to complex float [-1, 1] range
        i_data = (raw[0::2].astype(np.float32) - 127.5) / 127.5
        q_data = (raw[1::2].astype(np.float32) - 127.5) / 127.5
        return i_data + 1j * q_data

    def frequency_shift_to_baseband(self, iq_data, offset_freq):
        """Mix signal to baseband - like URH frequency correction"""
        t = np.arange(len(iq_data)) / self.sample_rate
        lo = np.exp(-1j * 2 * np.pi * offset_freq * t)
        return iq_data * lo

    def quadrature_demod(self, iq_data):
        """URH-style frequency discriminator demodulation"""
        # Exactly as in URH: tmp = conj(prev_sample) * current_sample, then atan2
        result = np.zeros(len(iq_data), dtype=np.float32)

        # URH sets first sample to noise value
        result[0] = -4.0  # NOISE_FSK_PSK from URH

        for i in range(1, len(iq_data)):
            # URH formula: tmp = conj(samples[i-1]) * samples[i]
            prev_conj = np.conj(iq_data[i-1])
            current = iq_data[i]
            tmp = prev_conj * current

            # Extract frequency using atan2
            result[i] = np.arctan2(np.imag(tmp), np.real(tmp))

        return result

    def symbol_extraction(self, demod_data):
        """Extract symbols using URH-like sampling"""
        symbols = []

        # URH uses fixed sampling at symbol centers
        for i in range(0, len(demod_data), self.samples_per_symbol):
            # Get symbol center
            center_idx = i + self.samples_per_symbol // 2

            if center_idx < len(demod_data):
                # Average around center (noise reduction)
                start = max(0, center_idx - self.samples_per_symbol // 16)
                end = min(len(demod_data), center_idx + self.samples_per_symbol // 16)
                symbol_value = np.mean(demod_data[start:end])
                symbols.append(symbol_value)

        return np.array(symbols)

    def symbols_to_bits(self, symbols):
        """Convert symbols to bits using URH center method"""
        # URH uses a fixed center threshold - we use the value from screenshot
        return (symbols > self.center).astype(int)

    def find_sync_and_extract_packets(self, bits):
        """Find sync patterns and extract packets"""
        sync_pattern = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8))
        packets = []

        # Search for sync pattern
        for i in range(len(bits) - len(sync_pattern) - 384):
            # Compare sync pattern
            sync_section = bits[i:i+len(sync_pattern)]
            errors = np.sum(sync_section != sync_pattern)

            if errors <= 2:  # Allow some errors
                # Extract packet after sync
                packet_start = i + len(sync_pattern)
                packet_bits = bits[packet_start:packet_start + 384]  # 48 bytes

                if len(packet_bits) == 384:
                    # Convert to bytes
                    packet_bytes = np.packbits(packet_bits).tobytes()

                    # Check magic bytes
                    if packet_bytes[:2] == b'\x52\x53':
                        # Try to parse
                        parsed = parse_packet(packet_bytes)
                        packets.append({
                            'raw': packet_bytes,
                            'parsed': parsed,
                            'sync_pos': i,
                            'sync_errors': errors
                        })

        return packets

    def auto_detect_frequency_offset(self, iq_data):
        """Auto-detect frequency offset like URH"""
        # Use power spectral density to find peak
        # Take middle portion for analysis
        start = len(iq_data) // 4
        end = start + 65536  # Use power of 2 for efficient FFT

        if end > len(iq_data):
            start = 0
            end = min(65536, len(iq_data))

        fft_data = np.fft.fft(iq_data[start:end])
        freqs = np.fft.fftfreq(len(fft_data), 1/self.sample_rate)

        # Find peak (exclude DC)
        fft_mag = np.abs(fft_data)
        fft_mag[0] = 0  # Remove DC

        peak_idx = np.argmax(fft_mag)
        peak_freq = freqs[peak_idx]

        return peak_freq

    def process_with_multiple_parameters(self, iq_data, verbose=False):
        """Try multiple parameter combinations like URH workflow"""

        all_packets = []

        # Try multiple frequency offsets (including auto-detected)
        auto_offset = self.auto_detect_frequency_offset(iq_data)
        freq_offsets = [auto_offset, 0, 31000, -31000, 62000, -62000]

        if verbose:
            print(f"Auto-detected frequency offset: {auto_offset:.0f} Hz")

        for freq_offset in freq_offsets:
            if verbose:
                print(f"Trying frequency offset: {freq_offset:.0f} Hz")

            # Mix to baseband
            bb_data = self.frequency_shift_to_baseband(iq_data, freq_offset)

            # Demodulate with URH algorithm
            demod_data = self.quadrature_demod(bb_data)

            # Try different samples per symbol (like URH adjustment)
            for sps in [200, 150, 250, 100, 300]:
                self.samples_per_symbol = sps

                if verbose and freq_offset == auto_offset:
                    print(f"  Trying samples per symbol: {sps}")

                symbols = self.symbol_extraction(demod_data)

                # Try both polarities
                for polarity_name, polarity_mult in [("normal", 1), ("inverted", -1)]:
                    test_symbols = polarity_mult * symbols

                    # Try different center values
                    for center in [0.0465, 0.0, -0.0465, 0.1, -0.1]:
                        self.center = center
                        bits = self.symbols_to_bits(test_symbols)

                        packets = self.find_sync_and_extract_packets(bits)

                        for pkt in packets:
                            pkt['sps'] = sps
                            pkt['polarity'] = polarity_name
                            pkt['center'] = center
                            pkt['freq_offset'] = freq_offset
                            all_packets.append(pkt)

                        if verbose and packets:
                            print(f"    {polarity_name}, center={center:.4f}: Found {len(packets)} packets")

        return all_packets

def parse_urh_data(hex_string):
    """Parse URH hex data directly"""
    try:
        hex_clean = ''.join(hex_string.split())
        data_bytes = bytes.fromhex(hex_clean)

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
                            'raw': packet_bytes,
                            'parsed': parsed,
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
    parser = argparse.ArgumentParser(description='RS41 Decoder - URH Style')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--input', default='tools/samples/latest_500ksps.cu8', help='Input IQ file')
    parser.add_argument('--urh-data', help='URH hex data string')
    parser.add_argument('--sample-rate', type=int, default=500000, help='Sample rate (Hz)')

    args = parser.parse_args()

    # Handle URH data
    if args.urh_data:
        print("🔍 Processing URH data...")
        packets = parse_urh_data(args.urh_data)

        for i, pkt in enumerate(packets, 1):
            print(f"[{i}] ✓ {format_packet(pkt['parsed'])}")
            if args.verbose:
                print(f"    Frame: {pkt['raw'].hex()}")

        print(f"Found {len(packets)} packets")
        return

    # Process IQ file
    print(f"📡 Loading IQ file: {args.input}")
    decoder = URHStyleDecoder(args.sample_rate)
    iq_data = decoder.load_iq_file(args.input)

    if iq_data is None:
        print("❌ Failed to load IQ file")
        return

    if args.verbose:
        print(f"Loaded {len(iq_data)} samples")

    packets = decoder.process_with_multiple_parameters(iq_data, args.verbose)

    # Display results
    if packets:
        valid_packets = [p for p in packets if p['parsed']]
        invalid_packets = [p for p in packets if not p['parsed']]

        if valid_packets:
            print(f"\n📊 Found {len(valid_packets)} valid RS41 packets:")
            for i, pkt in enumerate(valid_packets, 1):
                print(f"[{i}] ✓ {format_packet(pkt['parsed'])}")
                if args.verbose:
                    print(f"    Parameters: sps={pkt['sps']}, {pkt['polarity']}, center={pkt['center']:.4f}")
                    print(f"    Frame: {pkt['raw'].hex()}")

        if invalid_packets and args.verbose:
            print(f"\n⚠️ Found {len(invalid_packets)} packets with issues:")
            for i, pkt in enumerate(invalid_packets, 1):
                magic = pkt['raw'][:2].hex() if len(pkt['raw']) >= 2 else "??"
                print(f"[{i}] ❌ Magic: {magic}, sps={pkt['sps']}, {pkt['polarity']}")

        if not valid_packets and not invalid_packets:
            print("❌ No RS41 packets found")
    else:
        print("❌ No RS41 packets found")

if __name__ == "__main__":
    main()