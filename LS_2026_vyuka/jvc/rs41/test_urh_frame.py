#!/usr/bin/env python3

from tools.telemetry_packet import parse_packet, format_packet

# URH-decoded frame from README (without preamble and sync)
decoder_payload = "5253fee191980d6d931270bd699ea34be7fbabbf16ec3686dd4791d671e8afcd32860c14e4f7e4bb29c562b73d20994b"  # Full packet from decoder
urh_payload = "5253fee11f9afad53324e17ad33d4697d6f7577e2dd86d0dba8f6759c7a2bf34ca18305393df92eca7158adcf4866508"

print("Comparing packets:")
decoder_bytes = bytes.fromhex(decoder_payload)
urh_bytes = bytes.fromhex(urh_payload)

print(f"Decoder: {decoder_payload}")
print(f"URH:     {urh_payload}")
print()

print("First 16 bytes comparison:")
for i in range(16):
    d = decoder_bytes[i] if i < len(decoder_bytes) else 0
    u = urh_bytes[i] if i < len(urh_bytes) else 0
    print(f"Byte {i:2d}: decoder=0x{d:02x} urh=0x{u:02x} {'✗' if d != u else '✓'}")

print("\nTesting decoder packet:")
parsed_decoder = parse_packet(decoder_bytes)
if parsed_decoder:
    print("✓ Decoder packet parsed!")
    print(format_packet(parsed_decoder))
else:
    print("✗ Decoder packet failed to parse")

print("\nTesting URH packet:")
parsed_urh = parse_packet(urh_bytes)
if parsed_urh:
    print("✓ URH packet parsed!")
    print(format_packet(parsed_urh))
else:
    print("✗ URH packet failed to parse")