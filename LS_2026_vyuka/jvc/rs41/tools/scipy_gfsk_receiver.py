#!/usr/bin/env python3
"""
SciPy-based GFSK receiver using the proven demodulation pipeline
Based on the provided working code snippet - no GNU Radio complexity!
"""

import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import subprocess
import threading
import queue
import time
import struct
import argparse
import sys
from collections import deque


class LivePlotter:
    def __init__(self, max_points=2000):
        """Live plotter for signal debugging"""
        self.max_points = max_points

        # Data buffers
        self.time_data = deque(maxlen=max_points)
        self.raw_magnitude = deque(maxlen=max_points)
        self.baseband_magnitude = deque(maxlen=max_points)
        self.demodulated_signal = deque(maxlen=max_points)
        self.symbol_samples = deque(maxlen=max_points//4)
        self.bit_stream = deque(maxlen=max_points//8)

        # Setup matplotlib for real-time plotting
        plt.ion()
        self.fig, self.axes = plt.subplots(3, 2, figsize=(12, 8))
        self.fig.suptitle('GFSK Receiver Debug - Live Signal Processing')

        # Initialize plot lines
        self.lines = {}

        # Raw RF signal magnitude
        self.axes[0,0].set_title('Raw RF Signal Magnitude')
        self.axes[0,0].set_ylabel('Magnitude')
        self.axes[0,0].grid(True, alpha=0.3)
        self.lines['raw_mag'] = self.axes[0,0].plot([], [], 'b-', alpha=0.7)[0]

        # Baseband signal magnitude
        self.axes[0,1].set_title('Decimated Baseband Magnitude')
        self.axes[0,1].set_ylabel('Magnitude')
        self.axes[0,1].grid(True, alpha=0.3)
        self.lines['bb_mag'] = self.axes[0,1].plot([], [], 'g-', alpha=0.7)[0]

        # Demodulated FM signal
        self.axes[1,0].set_title('FM Demodulated Signal')
        self.axes[1,0].set_ylabel('Frequency')
        self.axes[1,0].grid(True, alpha=0.3)
        self.lines['demod'] = self.axes[1,0].plot([], [], 'r-', alpha=0.7)[0]

        # Symbol sampling points
        self.axes[1,1].set_title('Symbol Sampling Points')
        self.axes[1,1].set_ylabel('Symbol Value')
        self.axes[1,1].grid(True, alpha=0.3)
        self.lines['symbols'] = self.axes[1,1].plot([], [], 'ro', markersize=3)[0]

        # Bit stream
        self.axes[2,0].set_title('Decoded Bit Stream')
        self.axes[2,0].set_ylabel('Bit Value')
        self.axes[2,0].set_ylim(-0.5, 1.5)
        self.axes[2,0].grid(True, alpha=0.3)
        self.lines['bits'] = self.axes[2,0].plot([], [], 'ko-', markersize=2)[0]

        # Spectrum (FFT)
        self.axes[2,1].set_title('Signal Spectrum')
        self.axes[2,1].set_ylabel('Power (dB)')
        self.axes[2,1].grid(True, alpha=0.3)
        self.lines['spectrum'] = self.axes[2,1].plot([], [], 'purple', alpha=0.7)[0]

        # Set common x-axis labels
        self.axes[2,0].set_xlabel('Time')
        self.axes[2,1].set_xlabel('Frequency (Hz)')

        plt.tight_layout()
        plt.show(block=False)

        self.last_update = 0
        self.update_interval = 0.1  # 100ms updates

    def update_data(self, raw_iq=None, baseband=None, demodulated=None,
                   symbol_data=None, bits=None, sample_rate=250000):
        """Update data buffers for plotting"""
        current_time = time.time()

        if raw_iq is not None:
            # Add raw signal magnitude
            mag = np.abs(raw_iq)
            if len(mag) > 0:
                time_points = np.linspace(current_time - len(mag)/sample_rate,
                                        current_time, len(mag))
                for t, m in zip(time_points[-100:], mag[-100:]):  # Limit updates
                    self.time_data.append(t)
                    self.raw_magnitude.append(m)

        if baseband is not None:
            # Add baseband signal magnitude
            bb_mag = np.abs(baseband)
            if len(bb_mag) > 0:
                # Match time scale for decimated data
                decimated_rate = sample_rate // 4  # Assuming decimation factor of 4
                time_points = np.linspace(current_time - len(bb_mag)/decimated_rate,
                                        current_time, len(bb_mag))
                for t, m in zip(time_points[-50:], bb_mag[-50:]):  # Limit updates
                    self.baseband_magnitude.append(m)

        if demodulated is not None:
            # Add demodulated signal
            for sample in demodulated[-100:]:  # Limit updates
                self.demodulated_signal.append(sample)

        if symbol_data is not None:
            # Add symbol samples
            for symbol in symbol_data[-25:]:  # Limit updates
                self.symbol_samples.append(symbol)

        if bits is not None:
            # Add bits
            for bit in bits[-50:]:  # Limit updates
                self.bit_stream.append(int(bit))

    def update_plots(self):
        """Update the live plots"""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return

        self.last_update = current_time

        try:
            # Update raw magnitude plot
            if len(self.time_data) > 0 and len(self.raw_magnitude) > 0:
                # Show last 2 seconds of data
                recent_time = current_time - 2.0
                recent_indices = [i for i, t in enumerate(self.time_data) if t > recent_time]

                if recent_indices:
                    x_data = [self.time_data[i] - current_time for i in recent_indices]
                    y_data = [self.raw_magnitude[i] for i in recent_indices]

                    self.lines['raw_mag'].set_data(x_data, y_data)
                    if y_data:
                        self.axes[0,0].set_xlim(min(x_data), max(x_data))
                        self.axes[0,0].set_ylim(0, max(y_data) * 1.1)

            # Update baseband magnitude plot
            if len(self.baseband_magnitude) > 0:
                x_data = list(range(-len(self.baseband_magnitude), 0))
                y_data = list(self.baseband_magnitude)

                self.lines['bb_mag'].set_data(x_data, y_data)
                if y_data:
                    self.axes[0,1].set_xlim(min(x_data), max(x_data))
                    self.axes[0,1].set_ylim(0, max(y_data) * 1.1)

            # Update demodulated signal plot
            if len(self.demodulated_signal) > 0:
                x_data = list(range(-len(self.demodulated_signal), 0))
                y_data = list(self.demodulated_signal)

                self.lines['demod'].set_data(x_data, y_data)
                if y_data:
                    self.axes[1,0].set_xlim(min(x_data), max(x_data))
                    y_range = max(abs(min(y_data)), abs(max(y_data)))
                    self.axes[1,0].set_ylim(-y_range * 1.1, y_range * 1.1)

            # Update symbol samples plot
            if len(self.symbol_samples) > 0:
                x_data = list(range(-len(self.symbol_samples), 0))
                y_data = list(self.symbol_samples)

                self.lines['symbols'].set_data(x_data, y_data)
                if y_data:
                    self.axes[1,1].set_xlim(min(x_data), max(x_data))
                    y_range = max(abs(min(y_data)), abs(max(y_data)))
                    self.axes[1,1].set_ylim(-y_range * 1.1, y_range * 1.1)

            # Update bit stream plot
            if len(self.bit_stream) > 0:
                x_data = list(range(-len(self.bit_stream), 0))
                y_data = list(self.bit_stream)

                self.lines['bits'].set_data(x_data, y_data)
                self.axes[2,0].set_xlim(min(x_data), max(x_data))

            # Update spectrum plot (use raw signal)
            if len(self.raw_magnitude) > 256:
                signal_data = np.array(list(self.raw_magnitude)[-1024:])
                fft_data = np.fft.fft(signal_data)
                freqs = np.fft.fftfreq(len(signal_data), 1/250000)  # Assume 250kHz
                power = 20 * np.log10(np.abs(fft_data) + 1e-10)

                # Show positive frequencies only
                pos_freqs = freqs[:len(freqs)//2]
                pos_power = power[:len(power)//2]

                self.lines['spectrum'].set_data(pos_freqs, pos_power)
                self.axes[2,1].set_xlim(0, max(pos_freqs))
                self.axes[2,1].set_ylim(min(pos_power), max(pos_power))

            # Refresh the plot
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()

        except Exception as e:
            print(f"Plot update error: {e}")

    def add_packet_marker(self, packet_info):
        """Add a marker when packet is detected"""
        current_time = time.time()

        # Add vertical line on bit stream to mark packet detection
        self.axes[2,0].axvline(x=-10, color='red', linestyle='--', alpha=0.8)
        self.axes[2,0].text(-5, 0.5, f"PKT#{packet_info.get('count', '?')}",
                           rotation=90, ha='center', va='center',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.7))

    def close(self):
        """Close the plot"""
        plt.close(self.fig)


class RTLSDRCapture:
    def __init__(self, freq=433.92e6, sample_rate=250000, gain=35, ppm=0):
        self.freq = freq
        self.sample_rate = sample_rate
        self.gain = gain
        self.ppm = ppm
        self.running = False
        self.data_queue = queue.Queue(maxsize=20)
        self.process = None

    def start(self):
        """Start RTL-SDR capture"""
        cmd = [
            "rtl_sdr",
            "-f", str(int(self.freq)),
            "-s", str(self.sample_rate),
            "-g", str(self.gain),
            "-"
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
        self.thread = threading.Thread(target=self._capture_worker)
        self.thread.start()

    def _capture_worker(self):
        """Capture worker thread"""
        chunk_size = 32768  # 32K samples

        while self.running and self.process.poll() is None:
            try:
                data = self.process.stdout.read(chunk_size)
                if not data:
                    break

                # Convert to complex IQ
                raw_data = np.frombuffer(data, dtype=np.uint8)
                if len(raw_data) >= 2 and len(raw_data) % 2 == 0:
                    # Scale factor for int8 to float
                    sf = 127.5
                    # Convert to complex: I + jQ
                    iq_data = (raw_data[0::2].astype(np.float32) - sf) + \
                             1j * (raw_data[1::2].astype(np.float32) - sf)
                    iq_data /= sf  # Normalize to [-1, 1]

                    # Put in queue, drop old data if full
                    try:
                        self.data_queue.put(iq_data, block=False)
                    except queue.Full:
                        try:
                            self.data_queue.get(block=False)  # Drop oldest
                            self.data_queue.put(iq_data, block=False)
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
        if hasattr(self, 'thread'):
            self.thread.join()


class SciPyGFSKDemodulator:
    def __init__(self, sample_rate=250000, symbol_rate=1200, decimation=4, plotter=None):
        self.sample_rate = sample_rate
        self.symbol_rate = symbol_rate
        self.decimation = decimation
        self.bb_fs = sample_rate // decimation
        self.plotter = plotter

        # Buffer for continuous processing
        self.buffer = np.array([], dtype=np.complex64)
        self.max_buffer_samples = sample_rate * 5  # 5 seconds

        # Decimation filter
        self.dec_filter = sig.butter(3, 1 / (decimation * 2))

        # Sync pattern (0x2dd4 in binary)
        self.sync_pattern = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0]

        # Debug data storage
        self.debug_data = {
            'last_baseband': None,
            'last_demodulated': None,
            'last_symbols': None,
            'last_bits': None
        }

        print(f"GFSK Demodulator: {symbol_rate} bps, decimated to {self.bb_fs} Hz")

    def process_chunk(self, iq_data):
        """Process new IQ data chunk using the proven scipy method"""
        # Add to buffer
        self.buffer = np.concatenate([self.buffer, iq_data])

        # Update live plots with raw data
        if self.plotter:
            self.plotter.update_data(raw_iq=iq_data, sample_rate=self.sample_rate)

        # Keep buffer manageable
        if len(self.buffer) > self.max_buffer_samples:
            self.buffer = self.buffer[-self.max_buffer_samples:]

        # Need minimum data for processing
        min_samples = self.bb_fs  # At least 1 second of decimated data
        if len(self.buffer) < min_samples * self.decimation:
            return []

        return self._demodulate_and_decode()

    def _demodulate_and_decode(self):
        """Demodulate GFSK using the proven pipeline from the snippet"""
        # Step 1: Decimate (following the working example)
        bb = sig.filtfilt(*self.dec_filter, self.buffer)
        bb = bb[::self.decimation]

        if len(bb) < 1000:  # Need reasonable amount of data
            return []

        # Store debug data and update plots
        self.debug_data['last_baseband'] = bb
        if self.plotter:
            self.plotter.update_data(baseband=bb[-500:])  # Show recent data

        # Step 2: Detect signal activity using magnitude - MUCH MORE AGGRESSIVE
        bb_mag = np.abs(bb)

        # Try multiple threshold levels
        mean_mag = np.mean(bb_mag)
        std_mag = np.std(bb_mag)

        # Use a much lower threshold
        threshold = mean_mag + 0.5 * std_mag  # Much more sensitive

        # Find active regions
        active_indices = np.nonzero(bb_mag > threshold)[0]

        # Debug output
        if len(active_indices) > 0:
            print(f"DEBUG: Found {len(active_indices)} active samples (threshold={threshold:.4f}, mean={mean_mag:.4f}, std={std_mag:.4f})")

        # Much more lenient requirement
        if len(active_indices) < 10:  # Only need 10 active samples
            # Try even more aggressive detection
            threshold_aggressive = mean_mag + 0.1 * std_mag
            active_indices = np.nonzero(bb_mag > threshold_aggressive)[0]

            if len(active_indices) > 0:
                print(f"DEBUG: Using aggressive threshold: {len(active_indices)} active samples (threshold={threshold_aggressive:.4f})")
            else:
                print(f"DEBUG: No activity detected even with aggressive threshold (mag range: {np.min(bb_mag):.4f} to {np.max(bb_mag):.4f})")
                return []

        # Process each burst
        packets = []
        burst_start = None
        burst_end = None

        # Find burst boundaries
        for i in range(len(active_indices) - 1):
            if burst_start is None:
                burst_start = active_indices[i]

            # Check for gap (end of burst) - Much more lenient
            if active_indices[i+1] - active_indices[i] > self.bb_fs * 0.05:  # 50ms gap (was 100ms)
                burst_end = active_indices[i]

                # Process this burst - Much shorter minimum duration
                burst_duration_samples = burst_end - burst_start
                burst_duration_ms = burst_duration_samples * 1000.0 / self.bb_fs

                if burst_duration_samples > self.bb_fs * 0.05:  # At least 50ms (was 200ms)
                    print(f"DEBUG: Processing burst: {burst_duration_ms:.1f}ms ({burst_duration_samples} samples)")
                    packet = self._process_burst(bb[burst_start:burst_end])
                    if packet:
                        packets.append(packet)
                    else:
                        print(f"DEBUG: Burst processing failed for {burst_duration_ms:.1f}ms burst")

                burst_start = None

        # Process final burst if exists
        if burst_start is not None:
            burst_end = active_indices[-1]
            burst_duration_samples = burst_end - burst_start
            burst_duration_ms = burst_duration_samples * 1000.0 / self.bb_fs

            if burst_duration_samples > self.bb_fs * 0.05:  # At least 50ms
                print(f"DEBUG: Processing final burst: {burst_duration_ms:.1f}ms ({burst_duration_samples} samples)")
                packet = self._process_burst(bb[burst_start:burst_end])
                if packet:
                    packets.append(packet)
                else:
                    print(f"DEBUG: Final burst processing failed for {burst_duration_ms:.1f}ms burst")

        return packets

    def _process_burst(self, bb_segment):
        """Process a single burst using FM demodulation and symbol sync"""
        if len(bb_segment) < 10:  # Much more lenient
            print(f"DEBUG: Burst too short: {len(bb_segment)} samples")
            return None

        print(f"DEBUG: Processing burst with {len(bb_segment)} samples")

        # Step 3: FM Demodulation (from the working example)
        # Frequency discrimination using angle difference
        bb_angle_diff = np.angle(bb_segment[:-1] * np.conj(bb_segment[1:]))
        # Remove DC offset
        dem = bb_angle_diff - np.mean(bb_angle_diff)

        # Store debug data and update plots
        self.debug_data['last_demodulated'] = dem
        if self.plotter:
            self.plotter.update_data(demodulated=dem[-200:])  # Show recent demodulated data

        # Step 4: Symbol synchronization using Early-Late method (from snippet)
        bits, symbols = self._early_late_symbol_sync(dem)

        print(f"DEBUG: Got {len(bits)} bits from {len(dem)} demodulated samples")

        if len(bits) < 50:  # Much more lenient (was 300)
            print(f"DEBUG: Too few bits: {len(bits)}")
            return None

        # Store debug data and update plots
        self.debug_data['last_symbols'] = symbols
        self.debug_data['last_bits'] = bits
        if self.plotter:
            self.plotter.update_data(symbol_data=symbols[-50:], bits=bits[-100:])

        # Step 5: Find sync pattern and decode packet
        return self._find_packet(bits)

    def _early_late_symbol_sync(self, dem):
        """Early-Late symbol synchronization from the working snippet"""
        # Initial bit rate estimate
        nco_step_initial = self.symbol_rate * 3 / self.bb_fs
        nco_step = nco_step_initial
        nco_phase_acc = 0
        el_sample_queue = []
        el_samples = []

        for i in range(len(dem)):
            el_error = 0

            # Time to sample?
            if nco_phase_acc >= 1:
                nco_phase_acc -= 1

                # Linear interpolation
                alpha = nco_phase_acc / nco_step
                if i > 0:
                    sample_value = (alpha * dem[i-1] + (1 - alpha) * dem[i])
                    el_sample_queue.append(sample_value)

                # Got all three samples for early-late?
                if len(el_sample_queue) == 3:
                    if el_sample_queue[1] != 0:  # Avoid division by zero
                        el_error = (el_sample_queue[2] - el_sample_queue[0]) / -el_sample_queue[1]
                    el_error = np.clip(el_error, -10, 10)
                    el_sample_queue = []
                elif len(el_sample_queue) == 2:
                    el_samples.append(sample_value)

            # Update NCO
            nco_step += el_error * 0.01
            nco_step = np.clip(nco_step, nco_step_initial * 0.7, nco_step_initial * 1.3)
            nco_phase_acc += nco_step + el_error * 0.3

        # Convert to bits
        bits = [1 if sample >= 0 else 0 for sample in el_samples]
        return bits, el_samples  # Return both bits and raw symbol values

    def _find_packet(self, bits):
        """Find sync pattern and decode packet"""
        if len(bits) < len(self.sync_pattern) + 256:
            return None

        # Look for sync pattern
        for i in range(len(bits) - len(self.sync_pattern) - 256):
            # Check both polarities
            for invert in [False, True]:
                search_bits = bits[i:i+len(self.sync_pattern)]
                if invert:
                    search_bits = [1-b for b in search_bits]

                # Count matches
                matches = sum(1 for j in range(len(self.sync_pattern))
                             if search_bits[j] == self.sync_pattern[j])

                if matches >= len(self.sync_pattern) - 2:  # Allow 2 bit errors
                    # Extract packet
                    packet_start = i + len(self.sync_pattern)
                    packet_bits = bits[packet_start:packet_start + 256]  # 32 bytes

                    if len(packet_bits) >= 256:
                        if invert:
                            packet_bits = [1-b for b in packet_bits]

                        packet_bytes = self._bits_to_bytes(packet_bits)
                        decoded = self._decode_packet(packet_bytes)

                        if decoded:
                            return {
                                'sync_errors': len(self.sync_pattern) - matches,
                                'invert': invert,
                                'raw_data': packet_bytes.hex(),
                                'decoded': decoded
                            }

        return None

    def _bits_to_bytes(self, bits):
        """Convert bit list to bytes"""
        if len(bits) % 8 != 0:
            bits = bits + [0] * (8 - len(bits) % 8)

        bytes_data = bytearray()
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            byte_val = sum(bit << (7-j) for j, bit in enumerate(byte_bits))
            bytes_data.append(byte_val)

        return bytes(bytes_data)

    def _decode_packet(self, packet_bytes):
        """Decode RS41 packet"""
        if len(packet_bytes) != 32 or packet_bytes[:2] != b"RS":
            return None

        try:
            # CRC check
            crc_received = struct.unpack("<H", packet_bytes[-2:])[0]
            crc_calculated = self._crc16_ccitt_false(packet_bytes[:-2])

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

    def _crc16_ccitt_false(self, data):
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


def format_packet(packet):
    """Format packet for display"""
    decoded = packet['decoded']
    gps_valid = 1 if decoded["flags"] & 0x01 else 0

    result = (
        f"seq={decoded['sequence']} gps={gps_valid} sats={decoded['satellites']} "
        f"lat={decoded['latitude_e7'] / 1e7:.7f} lon={decoded['longitude_e7'] / 1e7:.7f} "
        f"alt={decoded['altitude_cm'] / 100.0:.2f}m speed={decoded['speed_cms'] / 100.0:.2f}m/s "
        f"batt={decoded['battery_mv']}mV temp={decoded['mcu_temp_centi'] / 100.0:.2f}C"
    )

    if packet['sync_errors'] > 0:
        result += f" (sync_errs={packet['sync_errors']})"
    if packet['invert']:
        result += " (inverted)"

    return result


def main():
    parser = argparse.ArgumentParser(description="SciPy-based GFSK receiver")
    parser.add_argument("--freq", type=float, default=433.92e6, help="Frequency in Hz")
    parser.add_argument("--sample-rate", type=int, default=250000, help="Sample rate")
    parser.add_argument("--symbol-rate", type=int, default=1200, help="Symbol rate")
    parser.add_argument("--decimation", type=int, default=4, help="Decimation factor")
    parser.add_argument("--gain", type=float, default=35.0, help="RF gain")
    parser.add_argument("--ppm", type=int, default=0, help="PPM correction")
    parser.add_argument("--debug", action="store_true", help="Debug output")
    parser.add_argument("--plot", action="store_true", help="Show live debug plots")

    args = parser.parse_args()

    print("SciPy-based GFSK Receiver")
    print(f"Frequency: {args.freq/1e6:.3f} MHz")
    print(f"Sample rate: {args.sample_rate} Hz")
    print(f"Symbol rate: {args.symbol_rate} bps")
    print(f"Decimation: {args.decimation}x")
    if args.plot:
        print("Live debug plots: ENABLED")

    # Check RTL-SDR availability
    try:
        subprocess.run(["rtl_sdr"], capture_output=True, timeout=1)
    except FileNotFoundError:
        print("ERROR: rtl_sdr not found!")
        return 1
    except subprocess.TimeoutExpired:
        pass

    # Initialize plotter if requested
    plotter = None
    if args.plot:
        try:
            plotter = LivePlotter()
            print("Live plotter initialized")
        except Exception as e:
            print(f"Could not initialize plotter: {e}")
            print("Continuing without plots...")

    # Initialize
    capture = RTLSDRCapture(args.freq, args.sample_rate, args.gain, args.ppm)
    demodulator = SciPyGFSKDemodulator(args.sample_rate, args.symbol_rate, args.decimation, plotter)

    try:
        capture.start()
        print("Listening for GFSK packets...")

        packet_count = 0

        while True:
            iq_data = capture.get_data()
            if iq_data is not None:
                if args.debug:
                    print(f"Processing {len(iq_data)} samples...")

                packets = demodulator.process_chunk(iq_data)

                for packet in packets:
                    packet_count += 1
                    print(f"[{packet_count}] {format_packet(packet)}")

                    if args.debug:
                        print(f"    Raw: {packet['raw_data']}")

                    # Add packet marker to plot
                    if plotter:
                        plotter.add_packet_marker({'count': packet_count})

            # Update plots
            if plotter:
                plotter.update_plots()

    except KeyboardInterrupt:
        print(f"\nReceived {packet_count} packets")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        capture.stop()
        if plotter:
            plotter.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())