#!/usr/bin/env python3

import numpy as np
import scipy.signal as sig
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    return ((raw[0::2].astype(np.float32) - 127.5) + 1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def search_entire_file():
    """Search entire IQ file with different frequency offsets"""

    # Target from URH
    target_seq = 39030  # seq=619 from URH parse

    print(f"🎯 Searching entire file for URH packet: seq={target_seq}")

    rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")
    print(f"📁 File size: {len(rf)} samples")

    # Test MANY different frequency offsets
    for freq_offset in [0, 31000, -31000, 15000, -15000, 62000, -62000,
                        1000, -1000, 5000, -5000, 10000, -10000]:
        print(f"\n🔄 Testing frequency offset: {freq_offset} Hz")

        # Mix to baseband
        bb_lo = np.exp(1j * (2 * np.pi * (-freq_offset / 500000) * np.arange(len(rf))))
        bb = rf * bb_lo

        # Decimate
        bb_dec_factor = 2
        bb_fs = 500000 // bb_dec_factor
        dec_lp_filter = sig.butter(3, 1 / (bb_dec_factor * 2))
        bb = sig.filtfilt(*dec_lp_filter, bb)
        bb = bb[::bb_dec_factor]

        # Split file into manageable chunks for processing
        chunk_size = 100000  # Process 100k samples at a time
        for chunk_start in range(0, len(bb), chunk_size // 4):  # Overlap chunks
            chunk_end = min(chunk_start + chunk_size, len(bb))

            if chunk_end - chunk_start < 50000:  # Skip small chunks
                continue

            chunk_bb = bb[chunk_start:chunk_end]

            # Check if this chunk has any signal
            power = np.mean(np.abs(chunk_bb)**2)
            if power < 0.01:  # Skip low power chunks
                continue

            print(f"  📍 Chunk {chunk_start//1000}k-{chunk_end//1000}k (power={power:.3f})")

            # FSK demodulation
            bb_angle_diff = np.angle(chunk_bb[:-1] * np.conj(chunk_bb[1:]))
            dem = bb_angle_diff - np.mean(bb_angle_diff)

            # Test different bit rates
            for bit_rate in [600, 1200]:
                samples_per_symbol = bb_fs / bit_rate

                # Test a few key timing offsets
                for bit_offset in range(0, min(16, int(samples_per_symbol)), max(1, int(samples_per_symbol//16))):
                    bits = []

                    for i in range(bit_offset, len(dem), int(samples_per_symbol)):
                        if i + max(1, int(samples_per_symbol//8)) < len(dem):
                            symbol_start = i
                            symbol_end = min(i + max(1, int(samples_per_symbol//8)), len(dem))
                            symbol_value = np.mean(dem[symbol_start:symbol_end])
                            bits.append(1 if symbol_value < 0 else 0)  # Inverted

                    if len(bits) < 450:
                        continue

                    # Look for sync pattern
                    sync_bits = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")

                    for sync_pos in range(0, len(bits)-400, 8):  # Check every 8th position
                        if sync_pos + len(sync_bits) + 384 <= len(bits):
                            packet_sync = bits[sync_pos:sync_pos + len(sync_bits)]
                            errors = sum(1 for a, b in zip(sync_bits, packet_sync) if a != b)

                            if errors <= 3:
                                packet_start = sync_pos + len(sync_bits)
                                packet_bits = bits[packet_start:packet_start + 384]

                                if len(packet_bits) == 384:
                                    packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
                                    magic = packet_bytes[:2].hex()

                                    if magic == "5253":
                                        seq = int.from_bytes(packet_bytes[4:6], 'little')
                                        uptime = int.from_bytes(packet_bytes[6:10], 'little')

                                        print(f"    🔍 Found packet: seq={seq} rate={bit_rate} offset={bit_offset} sync={sync_pos}")

                                        if seq == target_seq:  # EXACT match!
                                            print(f"    🎯 EXACT MATCH FOUND!")
                                            print(f"       Frequency offset: {freq_offset} Hz")
                                            print(f"       Chunk: {chunk_start}-{chunk_end}")
                                            print(f"       Bit rate: {bit_rate}")
                                            print(f"       Bit offset: {bit_offset}")
                                            print(f"       Sync position: {sync_pos}")
                                            print(f"       Frame: {packet_bytes.hex()}")

                                            parsed = parse_packet(packet_bytes)
                                            if parsed:
                                                print(f"    ✅ VALID: {format_packet(parsed)}")
                                                return True
                                            else:
                                                print(f"    ❌ CRC error but EXACT sequence match!")

                                        elif abs(seq - target_seq) < 50:
                                            print(f"    📍 Close: diff={abs(seq - target_seq)}")

    print("\n❌ Target packet still not found")
    return False

# Run the full file search
found = search_entire_file()