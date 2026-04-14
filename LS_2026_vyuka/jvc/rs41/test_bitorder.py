#!/usr/bin/env python3

import numpy as np

# Test different bit orders
test_data = [0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1]  # Example bits

print("Testing different bit orders:")
print(f"Input bits: {''.join(map(str, test_data))}")

# Little endian, LSB first
le_lsb = np.packbits(test_data, bitorder="little").tobytes()
print(f"Little endian: {le_lsb.hex()}")

# Big endian, MSB first
be_msb = np.packbits(test_data, bitorder="big").tobytes()
print(f"Big endian: {be_msb.hex()}")

# Test with actual magic pattern
magic_bits_5253 = [0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1]  # 0x5253 in binary
print(f"\nMagic 0x5253 bits: {''.join(map(str, magic_bits_5253))}")

magic_le = np.packbits(magic_bits_5253, bitorder="little").tobytes()
magic_be = np.packbits(magic_bits_5253, bitorder="big").tobytes()
print(f"Little endian: {magic_le.hex()}")
print(f"Big endian: {magic_be.hex()}")

# What we need to get 0x5253
target = bytes.fromhex("5253")
print(f"Target: {target.hex()}")

# Try different bit arrangements to get to 5253
import itertools

# Try all permutations of the magic bits to see what gives us 5253
possible_arrangements = []
for perm in itertools.permutations(range(16)):
    test_bits = [magic_bits_5253[i] for i in perm[:16]]
    result_be = np.packbits(test_bits, bitorder="big").tobytes()
    if result_be == target:
        possible_arrangements.append(perm[:16])

print(f"\nFound {len(possible_arrangements)} arrangements that give 0x5253")