#!/usr/bin/env python3

import numpy as np
import scipy.signal as sig
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES, dewhiten_packet, crc16_ccitt_false

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    return ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def focused_burst_search():
    """Focus on high-power region where signal definitely exists"""

    # Target from URH - this MUST be in our IQ file
    target_hex = "5253fee176984af06d24e17ad33d469789f6577e2dd86d0dba8f6759c7a2bf34ca18305393df92eca7158adcf486143c"
    target_bytes = bytes.fromhex(target_hex)
    target_seq = int.from_bytes(target_bytes[4:6], 'little')  # Should be 39030
    target_uptime = int.from_bytes(target_bytes[6:10], 'little')

    print(f"🎯 Target: seq={target_seq} uptime={target_uptime}ms")
    print(f"   Target frame: {target_hex[:32]}...")

    rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")

    # Focus ONLY on the high power region we saw: ~1275k-1600k samples
    # That corresponds to samples 2550000-3200000 in original file (after decimation factor)
    focus_start = 2550000
    focus_end = 3200000
    focus_rf = rf[focus_start:focus_end]

    print(f"🔍 Focusing on samples {focus_start}-{focus_end} ({len(focus_rf)} samples)")

    # Test MANY frequency offsets very systematically
    for freq_offset in range(-50000, 51000, 2000):  # -50kHz to +50kHz, step 2kHz
        print(f"\n📡 Freq offset: {freq_offset:+6d} Hz", end="")

        # Mix to baseband
        bb_lo = np.exp(1j * (2 * np.pi * (-freq_offset / 500000) * np.arange(len(focus_rf))))
        bb = focus_rf * bb_lo

        # Simple decimation
        bb_dec = bb[::2]  # Decimate by 2
        bb_fs = 500000 // 2

        # FSK demodulation
        bb_angle_diff = np.angle(bb_dec[:-1] * np.conj(bb_dec[1:]))
        dem = bb_angle_diff - np.mean(bb_angle_diff)

        # Test precise bit rates around 600 and 1200
        for bit_rate in [600, 1200, 585, 615, 1185, 1215]:
            samples_per_symbol = bb_fs / bit_rate

            # Test many timing offsets within symbol period
            best_match = None
            for bit_offset in range(0, min(32, int(samples_per_symbol))):
                bits = []

                # Extract bits
                for i in range(bit_offset, len(dem), int(samples_per_symbol)):
                    if i + max(1, int(samples_per_symbol//8)) < len(dem):
                        symbol_start = i
                        symbol_end = min(i + max(1, int(samples_per_symbol//8)), len(dem))
                        symbol_value = np.mean(dem[symbol_start:symbol_end])
                        bits.append(1 if symbol_value < 0 else 0)  # Inverted polarity

                if len(bits) < 450:
                    continue

                # Look for sync pattern
                sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")

                # Test multiple sync positions around expected location
                for sync_pos in range(max(0, len(bits)//3-50), min(len(bits)-400, len(bits)//3+50)):
                    if sync_pos + len(sync_bits) + 384 <= len(bits):
                        packet_sync = bits[sync_pos:sync_pos + len(sync_bits)]
                        errors = sum(1 for a, b in zip(sync_bits, packet_sync) if a != b)

                        if errors <= 4:  # Allow some sync errors
                            packet_start = sync_pos + len(sync_bits)
                            packet_bits = bits[packet_start:packet_start + 384]

                            if len(packet_bits) == 384:
                                packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()

                                if packet_bytes[:2] == b'\x52\x53':  # Magic check
                                    seq = int.from_bytes(packet_bytes[4:6], 'little')

                                    # Check how close we are to target
                                    seq_diff = abs(seq - target_seq)

                                    if seq_diff < 1000:  # Within reasonable range
                                        if best_match is None or seq_diff < best_match[0]:
                                            best_match = (seq_diff, freq_offset, bit_rate, bit_offset, sync_pos, packet_bytes, errors)

            # Report best match for this frequency
            if best_match is not None:
                seq_diff, _, rate, offset, sync, packet, sync_err = best_match
                seq = int.from_bytes(packet[4:6], 'little')

                if seq_diff == 0:  # Perfect match!
                    print(f" 🎯 EXACT! rate={rate} offset={offset} sync={sync}")
                    print(f"    Frame: {packet.hex()}")

                    # Check if it parses correctly
                    parsed = parse_packet(packet)
                    if parsed:
                        print(f"    ✅ VALID: {format_packet(parsed)}")
                        return True
                    else:
                        print(f"    ❌ CRC fail but exact sequence!")

                elif seq_diff < 10:
                    print(f" 📍 Close: seq={seq} (diff={seq_diff})")

        if best_match and best_match[0] == 0:  # Stop if we found exact match
            break

    print("\n❌ Exact URH packet not found in focused search")
    return False

# Run focused search
found = focused_burst_search()