#!/usr/bin/env python3

import numpy as np
import scipy.signal as sig
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size < 2 or (raw.size % 2) != 0:
        raise ValueError("input file does not contain valid rtl_sdr cu8 IQ data")
    return ((raw[0::2].astype(np.float32) - 127.5) +
            1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def test_fine_timing(rf_burst, fs, bit_rate=600):
    """Test fine timing adjustments around bit 133"""

    # FSK demodulation
    bb_angle_diff = np.angle(rf_burst[:-1] * np.conj(rf_burst[1:]))
    dem = bb_angle_diff - np.mean(bb_angle_diff)

    samples_per_symbol = fs / bit_rate
    print(f"Samples per symbol: {samples_per_symbol:.1f}")

    # Test different starting phases around the successful position
    for phase_offset in range(0, int(samples_per_symbol), max(1, int(samples_per_symbol // 32))):
        bits = []

        for i in range(phase_offset, len(dem), int(samples_per_symbol)):
            if i + int(samples_per_symbol//4) < len(dem):
                symbol_start = i
                symbol_end = min(i + int(samples_per_symbol//4), len(dem))
                symbol_value = np.mean(dem[symbol_start:symbol_end])
                bits.append(1 if symbol_value < 0 else 0)  # Inverted polarity

        if len(bits) > 150:
            # Look for sync around position 133
            sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")

            for start_pos in range(max(0, 133-10), min(len(bits)-400, 133+10)):
                if start_pos + len(sync_bits) + 384 <= len(bits):
                    # Check sync pattern
                    packet_sync = bits[start_pos:start_pos + len(sync_bits)]
                    errors = sum(1 for a, b in zip(sync_bits, packet_sync) if a != b)

                    if errors <= 6:
                        # Extract packet
                        packet_start = start_pos + len(sync_bits)
                        packet_bits = bits[packet_start:packet_start + 384]
                        if len(packet_bits) == 384:
                            packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()

                            # Check magic
                            magic = packet_bytes[:2].hex()
                            if magic == "5253":
                                print(f"\nPhase {phase_offset:3d}, pos {start_pos:3d}: MAGIC OK, {errors} sync errors")
                                print(f"  Packet: {packet_bytes[:16].hex()}...")

                                # Try to parse
                                parsed = parse_packet(packet_bytes)
                                if parsed:
                                    print(f"  ✓ VALID: {format_packet(parsed)}")
                                    return phase_offset, start_pos, packet_bytes
                                else:
                                    # Manual decode to show what we have
                                    try:
                                        seq = int.from_bytes(packet_bytes[4:6], 'little')
                                        uptime = int.from_bytes(packet_bytes[6:10], 'little')
                                        print(f"  ❌ CRC fail: seq={seq} uptime={uptime}ms ({uptime/3600000:.2f}h)")
                                    except:
                                        pass

    return None, None, None

# Load and test
rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")
fs = 500000

# Find burst (similar to our previous code)
offset_frequency = 31000
bb_lo = np.exp(1j * (2 * np.pi * (-offset_frequency / fs) * np.arange(len(rf))))
bb = rf * bb_lo

bb_dec_factor = 2
bb_fs = fs // bb_dec_factor
dec_lp_filter = sig.butter(3, 1 / (bb_dec_factor * 2))
bb = sig.filtfilt(*dec_lp_filter, bb)
bb = bb[::bb_dec_factor]

# Find bursts
bb_mag = np.abs(bb)
bb_mag_thrs = np.percentile(bb_mag, 98)
burst_mask = bb_mag > bb_mag_thrs
burst_indices = np.where(burst_mask)[0]

if len(burst_indices) > 0:
    # Find first substantial burst
    diff = np.diff(burst_indices)
    gaps = np.where(diff > 1000)[0]

    burst_starts = [burst_indices[0]]
    burst_ends = []

    for gap_idx in gaps:
        burst_ends.append(burst_indices[gap_idx])
        if gap_idx + 1 < len(burst_indices):
            burst_starts.append(burst_indices[gap_idx + 1])

    burst_ends.append(burst_indices[-1])

    for start, end in zip(burst_starts, burst_ends):
        if end - start > 10000:
            print(f"Testing burst {start}-{end}")
            burst_bb = bb[start:end]

            phase, pos, packet = test_fine_timing(burst_bb, bb_fs)
            if packet is not None:
                print(f"\n🎯 BEST RESULT: phase={phase}, pos={pos}")
                print(f"Full packet: {packet.hex()}")
            break
else:
    print("No bursts found")