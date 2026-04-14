#!/usr/bin/env python3

import numpy as np
from tools.telemetry_packet import parse_packet, format_packet, SYNC_BYTES, dewhiten_packet

def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size < 2 or (raw.size % 2) != 0:
        raise ValueError("input file does not contain valid rtl_sdr cu8 IQ data")
    return ((raw[0::2].astype(np.float32) - 127.5) +
            1j * (raw[1::2].astype(np.float32) - 127.5)).astype(np.complex64)

def find_sync_in_raw(data_bytes, sync_pattern=SYNC_BYTES):
    """Find sync pattern in raw bytes"""
    packets = []
    i = 0
    while i <= len(data_bytes) - len(sync_pattern) - 48:
        if data_bytes[i:i+len(sync_pattern)] == sync_pattern:
            print(f"Found potential sync at byte {i}")
            packet_start = i + len(sync_pattern)
            if packet_start + 48 <= len(data_bytes):
                packet_bytes = data_bytes[packet_start:packet_start + 48]
                print(f"  Extracted packet: {packet_bytes[:8].hex()}...")

                # Try to parse
                parsed = parse_packet(packet_bytes)
                if parsed:
                    print(f"  ✓ Valid packet: {format_packet(parsed)}")
                    packets.append(packet_bytes)
                else:
                    print(f"  ❌ Invalid packet")
                    print(f"    Magic: {packet_bytes[:2].hex()}")
                    dewhitened = dewhiten_packet(packet_bytes)
                    print(f"    Dewhitened magic: {dewhitened[:2].hex()}")

                i = packet_start + 48
            else:
                i += 1
        else:
            i += 1

    return packets

# Test known URH data
print("=== Testing URH reference data ===")
urh_hex = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2dd45253fee176984af06d24e17ad33d469789f6577e2dd86d0dba8f6759c7a2bf34ca18305393df92eca7158adcf486143c"
urh_data = bytes.fromhex(urh_hex)
urh_packets = find_sync_in_raw(urh_data)

print(f"\n=== Testing IQ file conversion ===")
# Load IQ file
rf = load_rtl_u8_file("tools/samples/latest_500ksps.cu8")
print(f"Loaded {len(rf)} IQ samples")

# Convert IQ to raw bytes (naive approach)
# This is just to see if the data contains our reference packet
rf_magnitude = np.abs(rf)
threshold = np.percentile(rf_magnitude, 95)
high_power_samples = rf[rf_magnitude > threshold]

print(f"High power samples: {len(high_power_samples)}")

# Try to find the actual sync pattern in different representations
print("\n=== Looking for sync pattern in IQ data ===")

# Convert complex values to bytes in different ways
for scale_factor in [1, 127.5, 255]:
    for offset in [0, 127.5]:
        test_data = np.clip(np.real(rf[:100000]) * scale_factor + offset, 0, 255).astype(np.uint8)
        sync_positions = []

        for i in range(len(test_data) - 2):
            if test_data[i] == 0x2d and test_data[i+1] == 0xd4:
                sync_positions.append(i)

        if sync_positions:
            print(f"  Scale {scale_factor}, offset {offset}: found {len(sync_positions)} sync patterns")
            for pos in sync_positions[:3]:  # Show first 3
                print(f"    Position {pos}: {test_data[pos:pos+10].hex()}")

print("\nDone.")