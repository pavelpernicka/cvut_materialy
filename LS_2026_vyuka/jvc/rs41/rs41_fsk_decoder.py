#!/usr/bin/env python3

import argparse
import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES, dewhiten_packet, crc16_ccitt_false, MAGIC, PROTOCOL_VERSION, PACKET_LEN

# Global verbosity setting
VERBOSE = False

def vprint(*args, **kwargs):
    """Print only if verbose mode is enabled"""
    if VERBOSE:
        print(*args, **kwargs)

def print_frame_details(packet_bytes, parsed_packet):
    """Print detailed frame breakdown for successfully parsed packets"""
    print(f"  Header: {packet_bytes[:12].hex()} (magic={packet_bytes[:2].hex()} ver={packet_bytes[2]} flags=0x{packet_bytes[3]:02x})")
    print(f"  Sequence: {parsed_packet.sequence} | Uptime: {parsed_packet.uptime_ms}ms ({parsed_packet.uptime_ms/3600000:.2f}h)")

    if parsed_packet.battery_mv is not None:
        print(f"  Battery: {parsed_packet.battery_mv}mV | Temp: {parsed_packet.mcu_temp_c:.1f}°C")

    if parsed_packet.satellites is not None:
        print(f"  GPS: {parsed_packet.satellites} satellites")

    # Show CRC
    crc_pos = len(packet_bytes) - 2
    if crc_pos >= 0:
        crc = int.from_bytes(packet_bytes[crc_pos:crc_pos+2], 'little')
        print(f"  CRC: 0x{crc:04x}")

def validate_packet_step_by_step(packet_bytes):
    """Detailed step-by-step packet validation with failure reporting"""
    print(f"  📋 Packet validation:")

    # Step 1: Length check
    if len(packet_bytes) != PACKET_LEN:
        print(f"    ❌ Length: {len(packet_bytes)} bytes (expected {PACKET_LEN})")
        return "length_error"
    else:
        print(f"    ✓ Length: {len(packet_bytes)} bytes")

    # Step 2: Magic check
    magic = packet_bytes[:2]
    if magic != MAGIC:
        print(f"    ❌ Magic: {magic.hex()} (expected {MAGIC.hex()})")
        return "magic_error"
    else:
        print(f"    ✓ Magic: {magic.hex()}")

    # Step 3: Dewhiten and check version
    dewhitened = dewhiten_packet(packet_bytes)
    version = dewhitened[2]
    if version != PROTOCOL_VERSION:
        print(f"    ❌ Version: {version} (expected {PROTOCOL_VERSION})")
        return "version_error"
    else:
        print(f"    ✓ Version: {version}")

    # Step 4: CRC check
    crc_rx = int.from_bytes(dewhitened[-2:], 'little')
    crc_calc = crc16_ccitt_false(dewhitened[:-2])
    if crc_rx != crc_calc:
        print(f"    ❌ CRC: rx=0x{crc_rx:04x} calc=0x{crc_calc:04x}")
        return "crc_error"
    else:
        print(f"    ✓ CRC: 0x{crc_rx:04x}")

    # Step 5: Payload length check
    payload_len = dewhitened[10]
    max_payload = PACKET_LEN - 14  # Header + CRC
    if payload_len > max_payload:
        print(f"    ❌ Payload length: {payload_len} (max {max_payload})")
        return "payload_length_error"
    else:
        print(f"    ✓ Payload length: {payload_len} bytes")

    # Step 6: TLV parsing check
    payload = dewhitened[12:12 + payload_len]
    pos = 0
    tlv_count = 0
    while pos + 2 <= len(payload):
        tlv_type = payload[pos]
        tlv_len = payload[pos + 1]
        pos += 2
        if pos + tlv_len > len(payload):
            print(f"    ❌ TLV {tlv_count}: type=0x{tlv_type:02x} len={tlv_len} extends beyond payload")
            return "tlv_error"
        print(f"    ✓ TLV {tlv_count}: type=0x{tlv_type:02x} len={tlv_len}")
        pos += tlv_len
        tlv_count += 1

    print(f"    ✅ All checks passed!")
    return "valid"

def print_frame_details_raw(packet_bytes):
    """Print detailed frame breakdown for raw packets"""
    try:
        # Decode header manually
        magic = packet_bytes[:2].hex()
        version = packet_bytes[2]
        flags = packet_bytes[3]
        sequence = int.from_bytes(packet_bytes[4:6], 'little')
        uptime_ms = int.from_bytes(packet_bytes[6:10], 'little')
        payload_len = packet_bytes[10] if len(packet_bytes) > 10 else 0

        print(f"  Header: {packet_bytes[:12].hex()} (magic={magic} ver={version} flags=0x{flags:02x})")
        print(f"  Sequence: {sequence} | Uptime: {uptime_ms}ms ({uptime_ms/3600000:.2f}h) | Payload: {payload_len} bytes")

        # Try to decode TLV data after dewhitening
        dewhitened = dewhiten_packet(packet_bytes)
        if len(dewhitened) > 12:
            print(f"  TLV area: {dewhitened[12:min(12+10, len(dewhitened))].hex()}...")

            # Try to decode basic TLVs
            pos = 12
            if pos + 6 < len(dewhitened):
                tlv_type = dewhitened[pos]
                tlv_len = dewhitened[pos + 1]
                if tlv_type == 0x01 and tlv_len == 4 and pos + 6 <= len(dewhitened):
                    battery = int.from_bytes(dewhitened[pos+2:pos+4], 'little')
                    temp = int.from_bytes(dewhitened[pos+4:pos+6], 'little', signed=True)
                    print(f"  Battery: {battery}mV | Temp: {temp/100:.1f}°C")

        # Show CRC with validation
        crc_pos = len(packet_bytes) - 2
        if crc_pos >= 0:
            crc_rx = int.from_bytes(packet_bytes[crc_pos:crc_pos+2], 'little')
            crc_calc = crc16_ccitt_false(dewhitened[:-2])
            crc_valid = "✓" if crc_rx == crc_calc else "❌"
            print(f"  CRC: rx=0x{crc_rx:04x} calc=0x{crc_calc:04x} {crc_valid}")

    except Exception as e:
        print(f"  Error decoding frame details: {e}")

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size < 2 or (raw.size % 2) != 0:
        raise ValueError("input file does not contain valid rtl_sdr cu8 IQ data")
    return ((raw[0::2].astype(np.float32) - 127.5) +
            1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def search_packets(bits, polarity_name, sync_bits, packet_len):
    found_packets = 0
    sync_candidates = 0

    vprint(f"\n=== {polarity_name.upper()} POLARITY ===")
    vprint(f"First 64 bits: {''.join(map(str, bits[:64]))}")

    for i in range(len(bits) - len(sync_bits) - packet_len):
        # Check for sync pattern with some error tolerance
        errors = np.sum(bits[i:i+len(sync_bits)] != sync_bits)
        if errors <= 8:  # Allow up to 8 bit errors initially
            sync_candidates += 1
            if sync_candidates <= 10:  # Show first 10 candidates
                vprint(f"Sync candidate at bit {i} with {errors} errors")

            if errors <= 5:  # More lenient check for actual packet extraction
                vprint(f"Found sync at bit {i} with {errors} errors")

                # Extract packet
                packet_start = i + len(sync_bits)
                packet_bits = bits[packet_start:packet_start + packet_len]
                if len(packet_bits) == packet_len:
                    packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()

                    # Try to parse as RS41 packet
                    parsed = parse_packet(packet_bytes)
                    if parsed:
                        print(f"✓ RS41: {format_packet(parsed)}")
                        print(f"  Frame: {packet_bytes.hex()}")
                        print_frame_details(packet_bytes, parsed)
                        found_packets += 1
                    else:
                        magic = packet_bytes[:2].hex() if len(packet_bytes) >= 2 else "??"
                        vprint(f"  Sync found but packet parsing failed: magic={magic}")

                        # Show detailed parsing failure analysis
                        failure_reason = validate_packet_step_by_step(packet_bytes)

                        if magic == "5253":  # Perfect magic - try manual decode
                            try:
                                # Basic header decode
                                sequence = int.from_bytes(packet_bytes[4:6], 'little')
                                uptime_ms = int.from_bytes(packet_bytes[6:10], 'little')
                                flags = packet_bytes[3]

                                # Format basic telemetry
                                flag_names = []
                                if flags & 0x01: flag_names.append("GPS_POS")
                                if flags & 0x02: flag_names.append("GPS_ALT")
                                if flags & 0x04: flag_names.append("GPS_SPEED")

                                # Check if this looks like valid telemetry despite CRC error
                                if failure_reason == "crc_error" and sequence < 100000 and uptime_ms < 5000000000:  # Reasonable bounds
                                    print(f"✓ RS41: seq={sequence} uptime={uptime_ms/3600000:.1f}h flags={' '.join(flag_names) if flag_names else 'none'} (CRC error)")
                                else:
                                    print(f"⚠ RS41: seq={sequence} uptime={uptime_ms/3600000:.1f}h flags={' '.join(flag_names) if flag_names else 'none'} (failed: {failure_reason})")
                                print(f"  Frame: {packet_bytes.hex()}")
                                print_frame_details_raw(packet_bytes)
                                found_packets += 1

                            except Exception as e:
                                vprint(f"Manual decode error: {e}")
                                found_packets += 1

    return found_packets, sync_candidates

def process_burst(rf_burst, fs):
    """Process a single RF burst to find packets"""

    # FSK demodulation using phase difference
    bb_angle_diff = np.angle(rf_burst[:-1] * np.conj(rf_burst[1:]))
    # Remove DC offset
    dem = bb_angle_diff - np.mean(bb_angle_diff)

    # RS41 bitrate - discovered to be 600 bps in this sample
    bit_rate = 600

    # Calculate samples per symbol correctly for RS41
    samples_per_symbol = fs / bit_rate
    vprint(f"Samples per symbol: {samples_per_symbol:.1f}")

    # Improved symbol sampling - try multiple phases
    el_samples = []

    # Try different sampling phases
    for phase_offset in range(0, int(samples_per_symbol), max(1, int(samples_per_symbol // 8))):
        phase_samples = []
        for i in range(phase_offset, len(dem), int(samples_per_symbol)):
            if i < len(dem):
                window_size = max(1, int(samples_per_symbol // 4))
                symbol_start = i
                symbol_end = min(i + window_size, len(dem))
                symbol_value = np.mean(dem[symbol_start:symbol_end])
                phase_samples.append((i, symbol_value))

        # Use the phase that gives us the most bits
        if len(phase_samples) > len(el_samples):
            el_samples = phase_samples
            vprint(f"Best phase offset: {phase_offset}, extracted {len(el_samples)} symbols")

    # Extract bits using zero threshold
    sample_values = np.array([x[1] for x in el_samples])
    bits_normal = (sample_values >= 0).astype(np.uint8)
    bits_inverted = 1 - bits_normal

    vprint(f"Extracted {len(bits_normal)} bits")

    # Search for RS41 sync pattern with both polarities
    sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")
    packet_len = 48 * 8  # 48 bytes = 384 bits

    # Test both polarities
    normal_packets, normal_candidates = search_packets(bits_normal, "normal", sync_bits, packet_len)
    inverted_packets, inverted_candidates = search_packets(bits_inverted, "inverted", sync_bits, packet_len)

    total_packets = normal_packets + inverted_packets
    vprint(f"Found {total_packets} total packets")

    return total_packets

def parse_urh_hex_data(hex_string):
    """Parse URH hex data string and extract RS41 packets"""
    print(f"🔍 Parsing URH data: {hex_string[:64]}...")

    # Remove any whitespace
    hex_clean = ''.join(hex_string.split())

    # Convert to bytes
    try:
        data_bytes = bytes.fromhex(hex_clean)
        print(f"  Total length: {len(data_bytes)} bytes ({len(hex_clean)} hex chars)")
    except ValueError as e:
        print(f"  ❌ Invalid hex data: {e}")
        return []

    # Look for sync pattern
    sync_pattern = SYNC_BYTES
    packets = []

    i = 0
    while i < len(data_bytes) - len(sync_pattern):
        if data_bytes[i:i+len(sync_pattern)] == sync_pattern:
            print(f"  📡 Found sync at byte {i} (0x{i:04x})")

            # Extract packet (48 bytes after sync)
            packet_start = i + len(sync_pattern)
            if packet_start + PACKET_LEN <= len(data_bytes):
                packet_bytes = data_bytes[packet_start:packet_start + PACKET_LEN]

                # Try to parse
                parsed = parse_packet(packet_bytes)
                if parsed:
                    print(f"  ✓ Valid RS41 packet found!")
                    print(f"    {format_packet(parsed)}")
                    packets.append((packet_bytes, parsed))
                else:
                    print(f"  ⚠ Invalid packet at sync position")
                    failure_reason = validate_packet_step_by_step(packet_bytes)
                    magic = packet_bytes[:2].hex()
                    print(f"    Magic: {magic}, Failure: {failure_reason}")

                i = packet_start + PACKET_LEN
            else:
                print(f"  ❌ Not enough data for full packet")
                break
        else:
            i += 1

    return packets

def main():
    global VERBOSE

    parser = argparse.ArgumentParser(description="RS41 FSK decoder")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--input", default="tools/samples/latest_500ksps.cu8",
                       help="Input IQ file path")
    parser.add_argument("--urh-data", type=str, help="Parse URH hex data string directly")
    args = parser.parse_args()

    VERBOSE = args.verbose

    # Handle URH data input
    if args.urh_data:
        packets = parse_urh_hex_data(args.urh_data)
        if packets:
            print(f"\n📊 Found {len(packets)} valid packets:")
            for i, (packet_bytes, parsed) in enumerate(packets, 1):
                print(f"\n[{i}] ✓ RS41: {format_packet(parsed)}")
                print(f"  Frame: {packet_bytes.hex()}")
                print_frame_details(packet_bytes, parsed)
        else:
            print("❌ No valid RS41 packets found in URH data")
        return

    # Load IQ data
    rf = load_rtl_u8_file(args.input)
    fs = 500000  # 500 kS/s sample rate
    rf = rf / 127.5  # Scale to (-1, 1) range

    vprint(f"Loaded {len(rf)} samples at {fs} Hz")

    # Try automatic frequency detection
    vprint("Detecting frequency offset using FFT...")
    fft = np.fft.fft(rf[:100000])  # Use first 100k samples
    freqs = np.fft.fftfreq(len(fft), 1/fs)
    peak_idx = np.argmax(np.abs(fft))
    detected_offset = freqs[peak_idx]

    vprint(f"Detected frequency offset: {detected_offset:.0f} Hz")

    # Use detected offset, fallback to 31kHz
    offset_frequency = detected_offset if abs(detected_offset) > 1000 else 31000
    vprint(f"Using frequency offset: {offset_frequency:.0f} Hz")

    bb_lo = np.exp(1j * (2 * np.pi * (-offset_frequency / fs) * np.arange(0, len(rf))))
    bb = rf * bb_lo

    # Decimate
    bb_dec_factor = 2
    bb_fs = fs // bb_dec_factor
    dec_lp_filter = sig.butter(3, 1 / (bb_dec_factor * 2))
    bb = sig.filtfilt(*dec_lp_filter, bb)
    bb = bb[::bb_dec_factor]

    vprint(f"Baseband sample rate: {bb_fs} Hz")

    # Find bursts
    bb_mag = np.abs(bb)
    bb_mag_thrs = np.percentile(bb_mag, 98)
    burst_mask = bb_mag > bb_mag_thrs
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

        vprint(f"Found {len(burst_starts)} bursts")
        total_packets = 0

        # Process all substantial bursts
        for i, (start, end) in enumerate(zip(burst_starts, burst_ends)):
            if end - start > 10000:  # at least 10k samples
                vprint(f"Processing burst {i+1}: samples {start}-{end}")
                burst_bb = bb[start:end]
                burst_packets = process_burst(burst_bb, bb_fs)
                total_packets += burst_packets

        if total_packets == 0:
            print("No RS41 packets found")
        else:
            vprint(f"Total: {total_packets} RS41 packets decoded")

    else:
        print("No signal bursts found")

if __name__ == "__main__":
    main()