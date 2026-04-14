#!/usr/bin/env python3
"""
Fast RS41 decoder with fixed parameters
Based on URH settings but optimized for speed
"""

import argparse
import numpy as np
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES

def load_iq_file(filename):
    """Load IQ data quickly"""
    raw = np.fromfile(filename, dtype=np.uint8)
    if len(raw) % 2 != 0:
        raw = raw[:-1]

    # Convert to complex, normalized to [-1, 1]
    iq = ((raw[0::2] - 127.5) + 1j * (raw[1::2] - 127.5)) / 127.5
    return iq.astype(np.complex64)

def find_signal_region(iq_data):
    """Find the main signal region quickly with expanded window"""
    power = np.abs(iq_data)**2
    threshold = np.percentile(power, 95)  # Lower threshold for more signal

    # Find start and end of high power region
    high_indices = np.where(power > threshold)[0]
    if len(high_indices) == 0:
        return 0, len(iq_data)

    # Expand the region a bit for more context
    start = max(0, high_indices[0] - 50000)  # Add 50k samples before
    end = min(len(iq_data), high_indices[-1] + 50000)  # Add 50k samples after

    return start, end

def frequency_shift(iq_data, offset_hz, sample_rate):
    """Simple frequency shift"""
    t = np.arange(len(iq_data), dtype=np.float32) / sample_rate
    return iq_data * np.exp(-1j * 2 * np.pi * offset_hz * t)

def fsk_discriminator(iq_data):
    """URH-style frequency discriminator"""
    # Exactly URH algorithm: conj(prev) * current, then atan2
    result = np.zeros(len(iq_data), dtype=np.float32)
    result[0] = -4.0  # URH noise value

    # Vectorized for speed
    prev_conj = np.conj(iq_data[:-1])
    current = iq_data[1:]
    tmp = prev_conj * current
    result[1:] = np.arctan2(np.imag(tmp), np.real(tmp))

    return result

def extract_bits(demod, samples_per_symbol, center=0.0222):
    """Extract bits with fixed sampling"""
    sps = int(samples_per_symbol)

    # Sample at symbol centers
    symbol_indices = np.arange(sps//2, len(demod), sps)
    if len(symbol_indices) == 0:
        return np.array([], dtype=np.uint8)

    symbol_indices = symbol_indices[symbol_indices < len(demod)]
    symbols = demod[symbol_indices]

    if len(symbols) == 0:
        return np.array([], dtype=np.uint8)

    # If center is 0, use adaptive threshold
    if center == 0.0:
        center = np.median(symbols)

    # Convert to bits using center threshold
    bits = (symbols > center).astype(np.uint8)
    return bits

def find_packets(bits):
    """Find RS41 packets in bit stream"""
    sync_pattern = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8))
    packets = []

    # Quick sync search
    sync_len = len(sync_pattern)
    packet_len = 384  # 48 bytes

    for i in range(len(bits) - sync_len - packet_len):
        # Check sync with max 5 errors (URH setting)
        errors = np.sum(bits[i:i+sync_len] != sync_pattern)
        if errors <= 5:
            # Extract packet
            packet_start = i + sync_len
            packet_bits = bits[packet_start:packet_start + packet_len]

            if len(packet_bits) == packet_len:
                packet_bytes = np.packbits(packet_bits).tobytes()

                # Try to parse even without perfect magic
                parsed = parse_packet(packet_bytes)

                # Always add packet info for debugging
                packets.append({
                    'raw': packet_bytes,
                    'parsed': parsed,
                    'sync_pos': i,
                    'sync_errors': errors,
                    'magic': packet_bytes[:2].hex() if len(packet_bytes) >= 2 else "??"
                })

    return packets

def decode_rs41_fast(iq_data, sample_rate=500000, verbose=False):
    """Fast RS41 decoding with minimal parameter search"""

    # Find signal region
    start_idx, end_idx = find_signal_region(iq_data)
    signal_iq = iq_data[start_idx:end_idx]

    if verbose:
        print(f"Signal region: {start_idx}-{end_idx} ({len(signal_iq)} samples)")

    all_packets = []

    # Try only a few key frequency offsets
    for freq_offset in [31000, -31000, 0]:
        if verbose:
            print(f"Trying freq offset: {freq_offset} Hz")

        # Frequency shift
        bb_iq = frequency_shift(signal_iq, freq_offset, sample_rate)

        # FSK demodulation
        demod = fsk_discriminator(bb_iq)

        # Use exact URH parameters from screenshot
        for sps in [900, 850, 950]:  # URH shows 900 samples/symbol
            # Try both polarities quickly
            for polarity, polarity_name in [(1, "normal"), (-1, "inverted")]:
                test_demod = polarity * demod

                # Use exact URH center value
                for center in [0.0222, 0.0, -0.0222]:  # URH shows 0,0222
                    # Extract bits
                    bits = extract_bits(test_demod, sps, center)

                    # Find packets
                    packets = find_packets(bits)

                    # Add metadata
                    for pkt in packets:
                        pkt['freq_offset'] = freq_offset
                        pkt['sps'] = sps
                        pkt['polarity'] = polarity_name
                        pkt['center'] = center
                        all_packets.append(pkt)

                    if verbose and packets:
                        print(f"  sps={sps}, {polarity_name}, center={center}: {len(packets)} packets")

                    # Show sync candidates for debugging
                    if verbose and freq_offset == 31000 and sps == 900 and center == 0.0222:
                        sync_pattern = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8))
                        sync_candidates = 0
                        for i in range(len(bits) - len(sync_pattern)):
                            errors = np.sum(bits[i:i+len(sync_pattern)] != sync_pattern)
                            if errors <= 5:
                                sync_candidates += 1
                        print(f"    Debug: {sync_candidates} sync candidates (errors <= 5)")
                        print(f"    Total bits extracted: {len(bits)}")
                        print(f"    Bit pattern sample: {''.join(map(str, bits[:50]))}")

    return all_packets

def parse_urh_data(hex_string):
    """Quick URH data parsing"""
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
                    packets.append({'raw': packet_bytes, 'parsed': parsed})
            i = packet_start + 48
        else:
            i += 1

    return packets

def main():
    parser = argparse.ArgumentParser(description='Fast RS41 Decoder')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--input', default='tools/samples/latest_500ksps.cu8')
    parser.add_argument('--urh-data', help='URH hex data')

    args = parser.parse_args()

    if args.urh_data:
        packets = parse_urh_data(args.urh_data)
        for i, pkt in enumerate(packets, 1):
            print(f"[{i}] ✓ {format_packet(pkt['parsed'])}")
        return

    # Load IQ file
    print(f"Loading {args.input}...")
    iq_data = load_iq_file(args.input)

    # Decode
    packets = decode_rs41_fast(iq_data, verbose=args.verbose)

    # Show results
    valid_packets = [p for p in packets if p['parsed']]
    invalid_packets = [p for p in packets if not p['parsed']]

    if valid_packets:
        print(f"\n✅ Found {len(valid_packets)} valid packets:")
        for i, pkt in enumerate(valid_packets, 1):
            print(f"[{i}] {format_packet(pkt['parsed'])}")
            if args.verbose:
                print(f"    {pkt['freq_offset']} Hz, sps={pkt['sps']}, {pkt['polarity']}")

    if invalid_packets and args.verbose:
        print(f"\n⚠️ {len(invalid_packets)} packets with CRC errors")
        for i, pkt in enumerate(invalid_packets[:3], 1):  # Show only first 3
            magic = pkt['raw'][:2].hex()
            print(f"[{i}] Magic: {magic}")

    if not valid_packets and not invalid_packets:
        print("❌ No packets found")

if __name__ == "__main__":
    main()