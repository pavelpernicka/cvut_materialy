#!/usr/bin/env python3

from tools.telemetry_packet import parse_packet, format_packet, dewhiten_packet

# Our extracted packet that starts with "5229"
our_payload = "5229ff707726bd5e"  # First 8 bytes we see
print(f"Our packet starts with: {our_payload}")

# Extend to 48 bytes for testing
our_full = bytes.fromhex(our_payload + "00" * (48*2 - len(our_payload)))
print(f"Full packet length: {len(our_full)} bytes")

# Test if it's a whitening issue
print(f"Raw packet: {our_full[:8].hex()}")

# Try de-whitening
dewhitened = dewhiten_packet(our_full)
print(f"De-whitened: {dewhitened[:8].hex()}")

# Test parsing
parsed = parse_packet(our_full)
if parsed:
    print("✓ Packet parsed successfully!")
    print(format_packet(parsed))
else:
    print("✗ Failed to parse packet")

# Test if it passes magic check
magic = our_full[:2]
expected_magic = b"RS"  # 0x5253
print(f"Magic check: {magic.hex()} vs 5253 -> {'✓' if magic == expected_magic else '✗'}")

# The issue might be that "5229" != "5253"
# Let's see what "5253" would be in our bit pattern
target_magic = bytes.fromhex("5253")
print(f"Target magic: {target_magic.hex()}")
print(f"Our magic:    {magic.hex()}")
print(f"Difference:   {(target_magic[0] ^ magic[0]):02x}{(target_magic[1] ^ magic[1]):02x}")