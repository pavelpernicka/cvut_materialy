#!/usr/bin/env python3
"""
RTL_433 based GFSK receiver for 433.920 MHz, 1200 bps signals
Uses proven rtl_433 FSK demodulation with flexible decoder
"""

import argparse
import json
import subprocess
import sys
import time
import signal
import struct
from dataclasses import dataclass
from typing import Optional


@dataclass
class DecodedPacket:
    """Decoded packet information"""
    timestamp: str
    frequency: float
    rssi: float
    snr: float
    raw_data: str
    decoded_data: Optional[dict] = None


def check_rtl433_device() -> bool:
    """Check if RTL-SDR device is available"""
    try:
        result = subprocess.run(
            ["rtl_433", "-d", "help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def build_rtl433_command(args) -> list[str]:
    """Build rtl_433 command for GFSK 1200 bps reception"""

    # Calculate timing parameters for 1200 bps FSK_PCM
    bit_period_us = int(1_000_000 / 1200)  # ~833 us per bit
    tolerance_us = int(bit_period_us * 0.2)  # 20% tolerance

    # Sync pattern: 0x2dd4 (from your original code)
    sync_hex = "2dd4"

    # Packet length: 32 bytes = 256 bits (from your original code)
    packet_bits = 32 * 8

    cmd = [
        "rtl_433",
        "-f", str(int(args.freq)),           # 433.920 MHz
        "-s", str(args.sample_rate),          # Sample rate
        "-g", str(args.gain),                 # Gain
        "-Y", "minmax",                       # Use minmax FSK detector for better sensitivity
        "-Y", f"level={args.detection_level}", # Detection level
        "-F", "json",                         # JSON output for easy parsing
        "-F", "log",                          # Also enable log output for debugging
        "-M", "time:local",                   # Add local timestamp
        "-M", "level",                        # Add signal level info
    ]

    # Add flexible decoder for GFSK 1200 bps with your sync pattern
    decoder_spec = (
        f"n=GFSK1200,"                        # Name
        f"m=FSK_PCM,"                         # FSK Pulse Code Modulation
        f"s={bit_period_us//2},"              # Short pulse (half bit period for FSK)
        f"l={bit_period_us},"                 # Long pulse (bit period)
        f"r={bit_period_us*10},"              # Reset gap (10 bit periods)
        f"g={bit_period_us*5},"               # Gap (5 bit periods)
        f"t={tolerance_us},"                  # Tolerance
        f"preamble={{16}}aaaa,"               # 16 bits of 0xAAAA preamble (common for GFSK)
        f"sync={{16}}{sync_hex},"             # Sync pattern
        f"bits>={packet_bits},"               # Minimum bits expected
        f"rows=1"                             # Expect single row packets
    )

    cmd.extend(["-X", decoder_spec])

    if args.ppm:
        cmd.extend(["-p", str(args.ppm)])

    # Read from RTL-SDR device (default) or file
    if args.input_file:
        cmd.extend(["-r", args.input_file])

    return cmd


def parse_packet(packet_data: str) -> Optional[dict]:
    """Parse the packet data if it matches expected format"""
    try:
        # Convert hex string to bytes
        if len(packet_data) < 64:  # 32 bytes = 64 hex chars
            return None

        raw_bytes = bytes.fromhex(packet_data[:64])  # Take first 32 bytes

        # Check for "RS" magic bytes (from your original packet format)
        if raw_bytes[:2] != b"RS":
            return None

        # Unpack according to your original format
        # PACKET_FORMAT = "<2sBBHIiiiHHhBBH"
        try:
            unpacked = struct.unpack("<2sBBHIiiiHHhBBH", raw_bytes)

            packet = {
                "magic": unpacked[0].decode('ascii'),
                "sequence": unpacked[3],
                "flags": unpacked[2],
                "uptime_ms": unpacked[4],
                "latitude_e7": unpacked[5],
                "longitude_e7": unpacked[6],
                "altitude_cm": unpacked[7],
                "speed_cms": unpacked[8],
                "battery_mv": unpacked[9],
                "mcu_temp_centi": unpacked[10],
                "satellites": unpacked[11],
                "crc": unpacked[-1]
            }

            return packet

        except struct.error:
            return None

    except ValueError:
        return None


def format_packet(packet: dict) -> str:
    """Format packet data for display"""
    gps_valid = 1 if packet["flags"] & 0x01 else 0
    return (
        f"seq={packet['sequence']} gps={gps_valid} sats={packet['satellites']} "
        f"lat={packet['latitude_e7'] / 1e7:.7f} lon={packet['longitude_e7'] / 1e7:.7f} "
        f"alt={packet['altitude_cm'] / 100.0:.2f}m speed={packet['speed_cms'] / 100.0:.2f}m/s "
        f"batt={packet['battery_mv']}mV temp={packet['mcu_temp_centi'] / 100.0:.2f}C "
        f"uptime={packet['uptime_ms']}ms"
    )


def main():
    parser = argparse.ArgumentParser(description="RTL_433 based GFSK receiver for 1200 bps signals")
    parser.add_argument("--freq", type=float, default=433.920e6, help="Frequency in Hz")
    parser.add_argument("--sample-rate", type=int, default=250000, help="Sample rate in Hz")
    parser.add_argument("--gain", type=float, default=35.0, help="RF gain")
    parser.add_argument("--ppm", type=int, default=0, help="PPM correction")
    parser.add_argument("--detection-level", type=float, default=-8.0, help="FSK detection level in dB")
    parser.add_argument("--input-file", help="Input file instead of live RTL-SDR")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Check if we have an input file or RTL-SDR device
    if not args.input_file:
        # Check if RTL-SDR device is available
        try:
            result = subprocess.run(
                ["rtl_433", "-f", str(int(args.freq))],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "No supported devices found" in result.stderr:
                print("ERROR: No RTL-SDR device found!", file=sys.stderr)
                print("Please connect an RTL-SDR device or use --input-file option", file=sys.stderr)
                return 1
        except subprocess.TimeoutExpired:
            # Timeout means rtl_433 is probably waiting for input, which is good
            pass
        except Exception as e:
            print(f"ERROR: Could not test rtl_433: {e}", file=sys.stderr)
            return 1

    cmd = build_rtl433_command(args)

    if args.verbose:
        print(f"Starting RTL_433 GFSK receiver:", file=sys.stderr)
        print(f"Command: {' '.join(cmd)}", file=sys.stderr)
        print(f"Frequency: {args.freq/1e6:.3f} MHz", file=sys.stderr)
        print(f"Sample rate: {args.sample_rate} Hz", file=sys.stderr)
        print(f"Detection level: {args.detection_level} dB", file=sys.stderr)

    try:
        # Start rtl_433 process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        def signal_handler(signum, frame):
            process.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        packet_count = 0

        print("Listening for GFSK packets...", file=sys.stderr)

        # Read JSON output from rtl_433
        for line in process.stdout:
            try:
                # Parse JSON output from rtl_433
                data = json.loads(line.strip())

                if data.get("model") == "GFSK1200" and "data" in data:
                    packet = DecodedPacket(
                        timestamp=data.get("time", ""),
                        frequency=data.get("freq", 0),
                        rssi=data.get("rssi", 0),
                        snr=data.get("snr", 0),
                        raw_data=data["data"]
                    )

                    # Try to decode the packet
                    decoded = parse_packet(packet.raw_data)

                    if decoded:
                        packet.decoded_data = decoded
                        packet_count += 1

                        print(f"[{packet.timestamp}] {format_packet(decoded)}")

                        if args.verbose:
                            print(f"  RSSI: {packet.rssi:.1f} dBm, SNR: {packet.snr:.1f} dB", file=sys.stderr)
                            print(f"  Raw: {packet.raw_data}", file=sys.stderr)
                    else:
                        if args.verbose:
                            print(f"[{packet.timestamp}] Unknown packet: {packet.raw_data}", file=sys.stderr)

            except json.JSONDecodeError:
                # Skip non-JSON lines (debug output from rtl_433)
                if args.verbose and line.strip():
                    print(f"RTL_433: {line.strip()}", file=sys.stderr)
                continue

    except KeyboardInterrupt:
        print(f"\nReceived {packet_count} valid packets", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()

    return 0


if __name__ == "__main__":
    sys.exit(main())