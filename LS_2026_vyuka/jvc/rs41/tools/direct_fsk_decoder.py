#!/usr/bin/env python3
"""
Direct FSK decoder that captures from RTL-SDR and decodes GFSK manually
Bypasses rtl_433 detection issues
"""

import numpy as np
import subprocess
import struct
import threading
import queue
import time
import sys
import argparse
from scipy import signal as sp_signal


class RTLSDRCapture:
    def __init__(self, freq, sample_rate, gain, ppm=0):
        self.freq = freq
        self.sample_rate = sample_rate
        self.gain = gain
        self.ppm = ppm
        self.process = None
        self.data_queue = queue.Queue(maxsize=10)
        self.running = False

    def start(self):
        """Start RTL-SDR capture process"""
        cmd = [
            "rtl_sdr",
            "-f", str(int(self.freq)),
            "-s", str(self.sample_rate),
            "-g", str(self.gain),
            "-"  # Output to stdout
        ]

        if self.ppm != 0:
            cmd.extend(["-p", str(self.ppm)])

        print(f"Starting RTL-SDR: {' '.join(cmd)}")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_worker)
        self.capture_thread.start()

    def _capture_worker(self):
        """Worker thread to read IQ data"""
        chunk_size = 16384  # 16KB chunks

        while self.running and self.process.poll() is None:
            try:
                data = self.process.stdout.read(chunk_size)
                if not data:
                    break

                # Convert to IQ samples
                iq_data = np.frombuffer(data, dtype=np.uint8)
                if len(iq_data) >= 2:
                    iq_complex = (iq_data[0::2].astype(np.float32) - 127.5) + \
                                1j * (iq_data[1::2].astype(np.float32) - 127.5)

                    # Put in queue (drop if full)
                    try:
                        self.data_queue.put(iq_complex, block=False)
                    except queue.Full:
                        # Drop oldest data
                        try:
                            self.data_queue.get(block=False)
                            self.data_queue.put(iq_complex, block=False)
                        except queue.Empty:
                            pass

            except Exception as e:
                print(f"Capture error: {e}")
                break

    def get_data(self, timeout=0.1):
        """Get next chunk of IQ data"""
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        """Stop capture"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join()


class GFSKDecoder:
    def __init__(self, sample_rate, symbol_rate, deviation=2400):
        self.sample_rate = sample_rate
        self.symbol_rate = symbol_rate
        self.deviation = deviation
        self.samples_per_symbol = sample_rate / symbol_rate

        # Buffer for continuous processing
        self.buffer = np.array([], dtype=np.complex64)
        self.bit_buffer = []

        # Sync pattern from your original code
        self.sync_pattern = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0]  # 0x2dd4

        print(f"GFSK Decoder: {symbol_rate} bps, {deviation} Hz deviation")
        print(f"Samples per symbol: {self.samples_per_symbol:.1f}")

    def process_chunk(self, iq_data):
        """Process a chunk of IQ data"""
        # Add to buffer
        self.buffer = np.concatenate([self.buffer, iq_data])

        # Keep buffer manageable size
        max_buffer = int(self.sample_rate * 2)  # 2 seconds
        if len(self.buffer) > max_buffer:
            self.buffer = self.buffer[-max_buffer:]

        # Look for signals
        return self._detect_and_decode()

    def _detect_and_decode(self):
        """Detect bursts and decode GFSK"""
        if len(self.buffer) < self.samples_per_symbol * 100:  # Need at least 100 symbols
            return []

        # Compute instantaneous frequency (FSK demodulation)
        phase = np.angle(self.buffer[1:] * np.conj(self.buffer[:-1]))
        inst_freq = phase * self.sample_rate / (2 * np.pi)

        # Remove DC component
        inst_freq = inst_freq - np.mean(inst_freq)

        # Detect signal activity using frequency deviation
        power = np.abs(inst_freq)
        threshold = np.mean(power) + 3 * np.std(power)

        # Find active regions
        active = power > threshold
        if not np.any(active):
            return []

        # Find burst boundaries
        active_padded = np.concatenate(([False], active, [False]))
        diff = np.diff(active_padded.astype(int))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]

        packets = []

        for start, end in zip(starts, ends):
            duration = (end - start) / self.sample_rate
            if duration < 0.1:  # Skip short bursts
                continue

            # Extract burst
            burst_freq = inst_freq[start:end]

            # Decode bits
            bits = self._freq_to_bits(burst_freq)

            if len(bits) < 200:  # Need reasonable packet length
                continue

            # Look for sync pattern
            packet = self._find_and_decode_packet(bits)
            if packet:
                packets.append(packet)

        return packets

    def _freq_to_bits(self, freq_data):
        """Convert frequency data to bits"""
        # Resample to symbol rate
        if len(freq_data) < self.samples_per_symbol:
            return []

        # Simple bit decision based on frequency sign
        symbols_per_chunk = int(len(freq_data) / self.samples_per_symbol)
        bits = []

        for i in range(symbols_per_chunk):
            start_idx = int(i * self.samples_per_symbol)
            end_idx = int((i + 1) * self.samples_per_symbol)

            if end_idx > len(freq_data):
                break

            symbol_avg = np.mean(freq_data[start_idx:end_idx])
            bit = 1 if symbol_avg > 0 else 0
            bits.append(bit)

        return bits

    def _find_and_decode_packet(self, bits):
        """Find sync pattern and decode packet"""
        if len(bits) < len(self.sync_pattern) + 256:  # sync + min packet
            return None

        # Look for sync pattern
        for i in range(len(bits) - len(self.sync_pattern) - 256):
            # Check sync match
            sync_match = sum(1 for j in range(len(self.sync_pattern))
                            if bits[i + j] == self.sync_pattern[j])

            if sync_match >= len(self.sync_pattern) - 2:  # Allow 2 bit errors
                # Found sync, extract packet
                packet_start = i + len(self.sync_pattern)
                packet_bits = bits[packet_start:packet_start + 256]  # 32 bytes

                if len(packet_bits) >= 256:
                    # Convert bits to bytes
                    packet_bytes = self._bits_to_bytes(packet_bits[:256])
                    return {
                        'sync_errors': len(self.sync_pattern) - sync_match,
                        'sync_position': i,
                        'raw_data': packet_bytes.hex(),
                        'decoded': self._decode_packet(packet_bytes)
                    }

        return None

    def _bits_to_bytes(self, bits):
        """Convert bit list to bytes"""
        if len(bits) % 8 != 0:
            # Pad to multiple of 8
            bits = bits + [0] * (8 - len(bits) % 8)

        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            byte_val = sum(bit << (7-j) for j, bit in enumerate(byte_bits))
            bytes_data.append(byte_val)

        return bytes(bytes_data)

    def _decode_packet(self, packet_bytes):
        """Decode packet using your original format"""
        if len(packet_bytes) < 32:
            return None

        try:
            if packet_bytes[:2] != b"RS":
                return None

            # Unpack using your original format
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
                "crc": unpacked[-1]
            }

        except Exception as e:
            print(f"Decode error: {e}")
            return None


def format_packet(packet):
    """Format packet for display"""
    if not packet:
        return "Invalid packet"

    decoded = packet.get('decoded')
    if not decoded:
        return f"Raw: {packet['raw_data']}"

    gps_valid = 1 if decoded["flags"] & 0x01 else 0
    return (
        f"seq={decoded['sequence']} gps={gps_valid} sats={decoded['satellites']} "
        f"lat={decoded['latitude_e7'] / 1e7:.7f} lon={decoded['longitude_e7'] / 1e7:.7f} "
        f"alt={decoded['altitude_cm'] / 100.0:.2f}m speed={decoded['speed_cms'] / 100.0:.2f}m/s "
        f"batt={decoded['battery_mv']}mV temp={decoded['mcu_temp_centi'] / 100.0:.2f}C"
    )


def main():
    parser = argparse.ArgumentParser(description="Direct GFSK decoder")
    parser.add_argument("--freq", type=float, default=433.920e6)
    parser.add_argument("--sample-rate", type=int, default=250000)
    parser.add_argument("--symbol-rate", type=int, default=1200)
    parser.add_argument("--deviation", type=int, default=2400)
    parser.add_argument("--gain", type=float, default=35.0)
    parser.add_argument("--ppm", type=int, default=0)

    args = parser.parse_args()

    print("Direct GFSK Decoder")
    print(f"Frequency: {args.freq/1e6:.3f} MHz")
    print(f"Sample rate: {args.sample_rate} Hz")
    print(f"Symbol rate: {args.symbol_rate} bps")
    print(f"Deviation: {args.deviation} Hz")

    # Initialize
    capture = RTLSDRCapture(args.freq, args.sample_rate, args.gain, args.ppm)
    decoder = GFSKDecoder(args.sample_rate, args.symbol_rate, args.deviation)

    try:
        capture.start()
        print("Listening for GFSK packets...")

        packet_count = 0

        while True:
            iq_data = capture.get_data()
            if iq_data is not None:
                packets = decoder.process_chunk(iq_data)

                for packet in packets:
                    packet_count += 1
                    print(f"[{packet_count}] {format_packet(packet)}")
                    if packet.get('sync_errors', 0) > 0:
                        print(f"    (Sync errors: {packet['sync_errors']})")

    except KeyboardInterrupt:
        print(f"\nReceived {packet_count} packets")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        capture.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())