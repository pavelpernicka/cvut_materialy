#!/usr/bin/env python3

import numpy as np
import scipy.signal as sig
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES, dewhiten_packet, crc16_ccitt_false

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    return ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def exhaustive_packet_search():
    """Exhaustively search for the URH packet in our IQ sample"""

    # Target from URH
    urh_hex = "5253fee176984af06d24e17ad33d469789f6577e2dd86d0dba8f6759c7a2bf34ca18305393df92eca7158adcf486143c"
    urh_bytes = bytes.fromhex(urh_hex)
    target_seq = int.from_bytes(urh_bytes[4:6], 'little')  # 39030
    target_uptime = int.from_bytes(urh_bytes[6:10], 'little')

    print(f"🎯 Searching for URH packet: seq={target_seq} uptime={target_uptime}ms")

    rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")

    # Preprocessing (same as our decoder)
    offset_frequency = 31000
    bb_lo = np.exp(1j * (2 * np.pi * (-offset_frequency / 500000) * np.arange(len(rf))))
    bb = rf * bb_lo

    bb_dec_factor = 2
    bb_fs = 500000 // bb_dec_factor
    dec_lp_filter = sig.butter(3, 1 / (bb_dec_factor * 2))
    bb = sig.filtfilt(*dec_lp_filter, bb)
    bb = bb[::bb_dec_factor]

    # Find ALL bursts, not just substantial ones
    bb_mag = np.abs(bb)
    bb_mag_thrs = np.percentile(bb_mag, 95)  # Lower threshold
    burst_mask = bb_mag > bb_mag_thrs
    burst_indices = np.where(burst_mask)[0]

    if len(burst_indices) > 0:
        diff = np.diff(burst_indices)
        gaps = np.where(diff > 500)[0]  # Smaller gap threshold

        burst_starts = [burst_indices[0]]
        burst_ends = []

        for gap_idx in gaps:
            burst_ends.append(burst_indices[gap_idx])
            if gap_idx + 1 < len(burst_indices):
                burst_starts.append(burst_indices[gap_idx + 1])
        burst_ends.append(burst_indices[-1])

        print(f"Found {len(burst_starts)} signal bursts:")
        for i, (start, end) in enumerate(zip(burst_starts, burst_ends)):
            print(f"  Burst {i+1}: samples {start}-{end} (length {end-start})")

        # Search ALL bursts, even small ones
        for burst_idx, (start, end) in enumerate(zip(burst_starts, burst_ends)):
            if end - start > 5000:  # Much lower minimum
                print(f"\n🔍 Searching burst {burst_idx+1}: {start}-{end}")
                burst_bb = bb[start:end]

                # FSK demodulation
                bb_angle_diff = np.angle(burst_bb[:-1] * np.conj(burst_bb[1:]))
                dem = bb_angle_diff - np.mean(bb_angle_diff)

                # Test MANY different parameters
                for bit_rate in [600, 1200, 2400, 300]:
                    samples_per_symbol = bb_fs / bit_rate

                    if samples_per_symbol < 10:  # Skip if too low
                        continue

                    print(f"  📡 Bit rate {bit_rate} (sps={samples_per_symbol:.1f})")

                    # Test MANY timing offsets within one symbol period
                    for bit_offset in range(0, min(64, int(samples_per_symbol))):
                        # Extract bits with this timing
                        bits = []
                        for i in range(bit_offset, len(dem), int(samples_per_symbol)):
                            if i + max(1, int(samples_per_symbol//8)) < len(dem):
                                symbol_start = i
                                symbol_end = min(i + max(1, int(samples_per_symbol//8)), len(dem))
                                symbol_value = np.mean(dem[symbol_start:symbol_end])
                                bits.append(1 if symbol_value < 0 else 0)  # Inverted

                        if len(bits) < 450:  # Need enough bits
                            continue

                        # Test BOTH polarities
                        for polarity_name, test_bits in [("inverted", bits), ("normal", [1-b for b in bits])]:
                            # Look for sync in wider range
                            sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")

                            for sync_pos in range(0, len(test_bits)-400, 1):  # Every position!
                                if sync_pos + len(sync_bits) + 384 <= len(test_bits):
                                    packet_sync = test_bits[sync_pos:sync_pos + len(sync_bits)]
                                    errors = sum(1 for a, b in zip(sync_bits, packet_sync) if a != b)

                                    if errors <= 2:  # Very strict sync
                                        packet_start = sync_pos + len(sync_bits)
                                        packet_bits = test_bits[packet_start:packet_start + 384]

                                        if len(packet_bits) == 384:
                                            packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
                                            magic = packet_bytes[:2].hex()

                                            if magic == "5253":
                                                seq = int.from_bytes(packet_bytes[4:6], 'little')
                                                uptime = int.from_bytes(packet_bytes[6:10], 'little')

                                                # Check if this matches our target
                                                seq_diff = abs(seq - target_seq)
                                                uptime_diff = abs(uptime - target_uptime)

                                                if seq_diff == 0:  # EXACT sequence match!
                                                    print(f"    🎯 EXACT SEQ MATCH! offset={bit_offset} sync={sync_pos} {polarity_name}")
                                                    print(f"       seq={seq} uptime={uptime}ms")
                                                    print(f"       Frame: {packet_bytes.hex()}")

                                                    # Test CRC
                                                    parsed = parse_packet(packet_bytes)
                                                    if parsed:
                                                        print(f"    ✅ PERFECT MATCH: {format_packet(parsed)}")
                                                        return True
                                                    else:
                                                        # Check CRC manually
                                                        dewhitened = dewhiten_packet(packet_bytes)
                                                        crc_rx = int.from_bytes(dewhitened[-2:], 'little')
                                                        crc_calc = crc16_ccitt_false(dewhitened[:-2])
                                                        print(f"    ❌ CRC mismatch: rx=0x{crc_rx:04x} calc=0x{crc_calc:04x}")

                                                elif seq_diff < 100:  # Close match
                                                    print(f"    📍 Close match: seq={seq} (diff={seq_diff}) offset={bit_offset} sync={sync_pos} {polarity_name}")

    print("\n❌ URH packet not found with current parameters")
    return False

# Run the exhaustive search
found = exhaustive_packet_search()