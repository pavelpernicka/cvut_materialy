#!/usr/bin/env python3

import numpy as np
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    return ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def test_bit_shifts():
    """Test different bit shift offsets to find correct packet"""

    # Target packet from URH
    target_seq = 39030  # From URH: seq=619 -> wait, let me check URH again

    # Let's decode the URH reference to see what we should get
    urh_hex = "5253fee176984af06d24e17ad33d469789f6577e2dd86d0dba8f6759c7a2bf34ca18305393df92eca7158adcf486143c"
    urh_bytes = bytes.fromhex(urh_hex)
    target_seq = int.from_bytes(urh_bytes[4:6], 'little')
    target_uptime = int.from_bytes(urh_bytes[6:10], 'little')

    print(f"Target from URH: seq={target_seq} uptime={target_uptime}ms ({target_uptime/3600000:.2f}h)")

    rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")

    # Preprocessing (same as our decoder)
    import scipy.signal as sig

    offset_frequency = 31000
    bb_lo = np.exp(1j * (2 * np.pi * (-offset_frequency / 500000) * np.arange(len(rf))))
    bb = rf * bb_lo

    bb_dec_factor = 2
    bb_fs = 500000 // bb_dec_factor
    dec_lp_filter = sig.butter(3, 1 / (bb_dec_factor * 2))
    bb = sig.filtfilt(*dec_lp_filter, bb)
    bb = bb[::bb_dec_factor]

    # Find burst
    bb_mag = np.abs(bb)
    bb_mag_thrs = np.percentile(bb_mag, 98)
    burst_mask = bb_mag > bb_mag_thrs
    burst_indices = np.where(burst_mask)[0]

    if len(burst_indices) > 0:
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

                # FSK demodulation
                bb_angle_diff = np.angle(burst_bb[:-1] * np.conj(burst_bb[1:]))
                dem = bb_angle_diff - np.mean(bb_angle_diff)

                # Test different bit rates and timing offsets
                for bit_rate in [600, 1200]:
                    samples_per_symbol = bb_fs / bit_rate
                    print(f"\n--- Testing bit rate {bit_rate} (sps={samples_per_symbol:.1f}) ---")

                    # Test multiple bit timing offsets
                    for bit_offset in range(0, min(16, int(samples_per_symbol))):
                        bits = []

                        for i in range(bit_offset, len(dem), int(samples_per_symbol)):
                            if i + int(samples_per_symbol//4) < len(dem):
                                symbol_start = i
                                symbol_end = min(i + int(samples_per_symbol//4), len(dem))
                                symbol_value = np.mean(dem[symbol_start:symbol_end])
                                bits.append(1 if symbol_value < 0 else 0)  # Inverted

                        if len(bits) > 450:  # Need enough bits for packet
                            # Look for sync pattern
                            sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")

                            for sync_pos in range(max(0, 130-5), min(len(bits)-400, 135+5)):
                                if sync_pos + len(sync_bits) + 384 <= len(bits):
                                    packet_sync = bits[sync_pos:sync_pos + len(sync_bits)]
                                    errors = sum(1 for a, b in zip(sync_bits, packet_sync) if a != b)

                                    if errors <= 3:  # Very strict sync check
                                        packet_start = sync_pos + len(sync_bits)
                                        packet_bits = bits[packet_start:packet_start + 384]

                                        if len(packet_bits) == 384:
                                            packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
                                            magic = packet_bytes[:2].hex()

                                            if magic == "5253":
                                                seq = int.from_bytes(packet_bytes[4:6], 'little')
                                                uptime = int.from_bytes(packet_bytes[6:10], 'little')

                                                print(f"Bit offset {bit_offset:2d}, sync {sync_pos:3d}: seq={seq:5d} uptime={uptime:10d}ms ({uptime/3600000:.2f}h)")

                                                if abs(seq - target_seq) < 10:  # Close match
                                                    print(f"    *** CLOSE MATCH! Target seq was {target_seq} ***")

                                                    parsed = parse_packet(packet_bytes)
                                                    if parsed:
                                                        print(f"    ✓ VALID: {format_packet(parsed)}")
                                                        return True
                                                    else:
                                                        print(f"    ❌ CRC error")
                break

    return False

# Run the test
found = test_bit_shifts()
if not found:
    print("\nNo exact match found, but we're getting close!")