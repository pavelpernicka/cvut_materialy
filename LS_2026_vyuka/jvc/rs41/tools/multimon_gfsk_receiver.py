#!/usr/bin/env python3
"""
Multimon-ng based GFSK receiver using rtl_fm pipeline
This is a proven approach used by many radio amateurs
"""

import subprocess
import threading
import queue
import sys
import argparse
import time
import re
import struct
import signal


class MultimonGFSKReceiver:
    def __init__(self, freq=433.92e6, deviation=2400, sample_rate=22050, gain=35, ppm=0):
        self.freq = freq
        self.deviation = deviation
        self.sample_rate = sample_rate
        self.gain = gain
        self.ppm = ppm

        self.running = False
        self.packet_count = 0

    def start_receiver(self, verbose=False):
        """Start the rtl_fm -> multimon-ng pipeline"""

        # RTL_FM command for FM demodulation
        rtl_fm_cmd = [
            "rtl_fm",
            "-f", str(int(self.freq)),
            "-M", "fm",                    # FM demodulation (for FSK)
            "-s", str(self.sample_rate),   # Sample rate for multimon-ng (22050 is standard)
            "-g", str(self.gain),
            "-p", str(self.ppm),
            "-E", "dc",                    # DC blocking
            "-"                            # Output to stdout
        ]

        # Multimon-ng command for FSK demodulation
        multimon_cmd = [
            "multimon-ng",
            "-a", "FMSFSK",               # FSK demodulator
            "-t", "raw",                  # Raw input format
            "-v", "3" if verbose else "1", # Verbosity
            "--timestamp",                # Add timestamps
            "-"                           # Read from stdin
        ]

        if verbose:
            print(f"RTL_FM command: {' '.join(rtl_fm_cmd)}")
            print(f"Multimon-ng command: {' '.join(multimon_cmd)}")
            print(f"Pipeline: rtl_fm -> multimon-ng")

        try:
            # Start RTL_FM
            self.rtl_process = subprocess.Popen(
                rtl_fm_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if not verbose else None
            )

            # Start multimon-ng with RTL_FM output as input
            self.multimon_process = subprocess.Popen(
                multimon_cmd,
                stdin=self.rtl_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if not verbose else None,
                universal_newlines=True
            )

            # Allow rtl_fm to receive SIGPIPE when multimon-ng exits
            self.rtl_process.stdout.close()

            self.running = True

            print(f"Listening for FSK signals at {self.freq/1e6:.3f} MHz...")
            print("Press Ctrl+C to stop\n")

            # Read multimon-ng output
            while self.running:
                line = self.multimon_process.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if line:
                    self.process_multimon_output(line, verbose)

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop()

    def process_multimon_output(self, line, verbose):
        """Process output from multimon-ng"""

        if verbose:
            print(f"MULTIMON: {line}")

        # Look for FSK data lines
        # Multimon-ng FSK output typically looks like:
        # FMSFSK: <hex_data>
        if "FMSFSK:" in line:
            # Extract hex data
            match = re.search(r'FMSFSK:\s*([0-9A-Fa-f\s]+)', line)
            if match:
                hex_data = match.group(1).replace(' ', '')

                if len(hex_data) >= 8:  # At least 4 bytes
                    self.process_fsk_data(hex_data, line)

    def process_fsk_data(self, hex_data, raw_line):
        """Process FSK hex data to look for our packets"""

        try:
            # Convert hex to bytes
            data_bytes = bytes.fromhex(hex_data)

            # Look for sync pattern and RS magic
            sync_pattern = b"\x2d\xd4"  # Your sync pattern
            rs_magic = b"RS"

            # Search for patterns in the data
            for i in range(len(data_bytes) - 32):  # 32 byte packets
                # Look for sync pattern
                if data_bytes[i:i+2] == sync_pattern:
                    # Check if RS magic follows (might be offset)
                    for offset in range(0, 8):  # Check a few positions
                        if i + offset + 2 + 32 <= len(data_bytes):
                            packet_candidate = data_bytes[i + offset + 2:i + offset + 2 + 32]

                            if len(packet_candidate) >= 32 and packet_candidate[:2] == rs_magic:
                                packet = self.decode_packet(packet_candidate)
                                if packet:
                                    self.packet_count += 1
                                    print(f"[{self.packet_count}] {self.format_packet(packet)}")
                                    return

                # Also try direct RS magic search
                if data_bytes[i:i+2] == rs_magic and i + 32 <= len(data_bytes):
                    packet_candidate = data_bytes[i:i+32]
                    packet = self.decode_packet(packet_candidate)
                    if packet:
                        self.packet_count += 1
                        print(f"[{self.packet_count}] {self.format_packet(packet)}")
                        return

            # If no packet found, print raw data for debugging
            if len(hex_data) >= 32:  # Only show substantial data
                print(f"FSK_DATA: {hex_data[:64]}{'...' if len(hex_data) > 64 else ''}")

        except ValueError as e:
            print(f"Hex decode error: {e}")

    def decode_packet(self, packet_bytes):
        """Decode packet using RS41 format"""
        if len(packet_bytes) != 32:
            return None

        try:
            if packet_bytes[:2] != b"RS":
                return None

            # CRC check
            crc_received = struct.unpack("<H", packet_bytes[-2:])[0]
            crc_calculated = self.crc16_ccitt_false(packet_bytes[:-2])

            if crc_received != crc_calculated:
                return None

            # Unpack packet
            unpacked = struct.unpack("<2sBBHIiiiHHhBBH", packet_bytes)

            return {
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
                "crc_ok": True
            }

        except Exception:
            return None

    def crc16_ccitt_false(self, data):
        """Calculate CRC16 CCITT False"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc

    def format_packet(self, packet):
        """Format packet for display"""
        gps_valid = 1 if packet["flags"] & 0x01 else 0
        return (
            f"seq={packet['sequence']} gps={gps_valid} sats={packet['satellites']} "
            f"lat={packet['latitude_e7'] / 1e7:.7f} lon={packet['longitude_e7'] / 1e7:.7f} "
            f"alt={packet['altitude_cm'] / 100.0:.2f}m speed={packet['speed_cms'] / 100.0:.2f}m/s "
            f"batt={packet['battery_mv']}mV temp={packet['mcu_temp_centi'] / 100.0:.2f}C"
        )

    def stop(self):
        """Stop the receiver"""
        self.running = False

        if hasattr(self, 'multimon_process'):
            self.multimon_process.terminate()
            self.multimon_process.wait()

        if hasattr(self, 'rtl_process'):
            self.rtl_process.terminate()
            self.rtl_process.wait()


def main():
    parser = argparse.ArgumentParser(description="Multimon-ng based GFSK receiver")
    parser.add_argument("--freq", type=float, default=433.92e6, help="Frequency in Hz")
    parser.add_argument("--deviation", type=int, default=2400, help="FM deviation in Hz")
    parser.add_argument("--sample-rate", type=int, default=22050, help="Audio sample rate")
    parser.add_argument("--gain", type=float, default=35.0, help="RF gain")
    parser.add_argument("--ppm", type=int, default=0, help="PPM correction")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("Multimon-ng GFSK Receiver")
    print(f"Frequency: {args.freq/1e6:.3f} MHz")
    print(f"Deviation: {args.deviation} Hz")
    print(f"Sample rate: {args.sample_rate} Hz")
    print(f"RF gain: {args.gain} dB")

    # Check dependencies
    for cmd in ["rtl_fm", "multimon-ng"]:
        try:
            subprocess.run([cmd], capture_output=True, timeout=1)
        except FileNotFoundError:
            print(f"ERROR: {cmd} not found. Please install rtl-sdr and multimon-ng packages.")
            return 1
        except subprocess.TimeoutExpired:
            pass  # Normal

    receiver = MultimonGFSKReceiver(
        freq=args.freq,
        deviation=args.deviation,
        sample_rate=args.sample_rate,
        gain=args.gain,
        ppm=args.ppm
    )

    def signal_handler(signum, frame):
        print("\nStopping receiver...")
        receiver.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        receiver.start_receiver(args.verbose)
    except KeyboardInterrupt:
        print(f"\nReceived {receiver.packet_count} packets")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())