#!/usr/bin/env python3
"""
GNU Radio based GFSK receiver - more reliable than rtl_433
Uses proven GNU Radio blocks for RTL-SDR + GFSK demodulation
"""

import numpy as np
from gnuradio import gr, blocks, analog, filter, digital
from gnuradio.filter import firdes
import osmosdr
import threading
import queue
import time
import struct
import sys
import argparse


class GFSKReceiver(gr.top_block):
    def __init__(self, freq=433.92e6, samp_rate=2.4e6, rf_gain=35, if_gain=20, bb_gain=20):
        gr.top_block.__init__(self, "GFSK Receiver")

        ##################################################
        # Variables
        ##################################################
        # Ensure frequency is in valid RTL-SDR range (24-1766 MHz)
        self.freq = max(24e6, min(1766e6, freq))
        # Use RTL-SDR friendly sample rates
        valid_rates = [250000, 1000000, 1024000, 1536000, 1792000, 1920000, 2048000, 2160000, 2560000, 2880000, 3200000]
        self.samp_rate = min(valid_rates, key=lambda x: abs(x - samp_rate))

        self.rf_gain = rf_gain
        self.if_gain = if_gain
        self.bb_gain = bb_gain

        # GFSK Parameters
        self.symbol_rate = 1200
        self.deviation = 2400
        self.audio_rate = 48000
        self.channel_width = 25000

        print(f"Using sample rate: {self.samp_rate/1e6:.1f} Msps")
        print(f"Using frequency: {self.freq/1e6:.3f} MHz")

        # Output queues
        self.bit_queue = queue.Queue()
        self.raw_queue = queue.Queue()

        ##################################################
        # Blocks
        ##################################################

        # RTL-SDR Source with better error handling
        try:
            self.rtlsdr_source = osmosdr.source(args="numchan=1 rtl=0")
            self.rtlsdr_source.set_sample_rate(self.samp_rate)
            # Set frequency with retry on PLL lock failure
            freq_set = False
            for attempt in range(3):
                self.rtlsdr_source.set_center_freq(self.freq, 0)
                time.sleep(0.1)  # Give PLL time to lock
                actual_freq = self.rtlsdr_source.get_center_freq(0)
                if abs(actual_freq - self.freq) < 1000:  # Within 1kHz
                    freq_set = True
                    break
                print(f"PLL lock attempt {attempt+1}/3...")

            if not freq_set:
                raise RuntimeError(f"Failed to set frequency {self.freq/1e6:.3f} MHz. PLL not locked!")

            self.rtlsdr_source.set_freq_corr(0, 0)
            self.rtlsdr_source.set_dc_offset_mode(0, 0)
            self.rtlsdr_source.set_iq_balance_mode(0, 0)
            self.rtlsdr_source.set_gain_mode(False, 0)
            self.rtlsdr_source.set_gain(rf_gain, 0)

            # Skip IF/BB gains for RTL-SDR - not supported by all devices
            try:
                self.rtlsdr_source.set_if_gain(if_gain, 0)
                self.rtlsdr_source.set_bb_gain(bb_gain, 0)
            except:
                pass  # These gains might not be supported

            self.rtlsdr_source.set_antenna('', 0)
            self.rtlsdr_source.set_bandwidth(0, 0)

            print(f"RTL-SDR configured successfully at {actual_freq/1e6:.3f} MHz")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize RTL-SDR: {e}")

        # Low-pass filter to select our channel
        # Use compatible window parameter for newer GNU Radio versions
        try:
            # Try newer GNU Radio API
            from gnuradio.fft import window
            window_type = window.WIN_HAMMING
        except (ImportError, AttributeError):
            try:
                # Try older GNU Radio API
                window_type = firdes.WIN_HAMMING
            except AttributeError:
                # Fallback to no window specification
                window_type = None

        if window_type is not None:
            filter_taps = firdes.low_pass(1, self.samp_rate, self.channel_width/2, self.channel_width/4,
                                        window=window_type, beta=6.76)
        else:
            # Simplified filter for compatibility
            filter_taps = firdes.low_pass(1, self.samp_rate, self.channel_width/2, self.channel_width/4)

        self.lpf = filter.fir_filter_ccf(int(self.samp_rate/self.audio_rate), filter_taps)

        # FM demodulator for FSK
        self.fm_demod = analog.fm_demod_cf(
            channel_rate=self.audio_rate,
            audio_decim=1,
            deviation=self.deviation,
            audio_pass=self.symbol_rate*2,
            audio_stop=self.symbol_rate*4,
            gain=1.0,
            tau=75e-6
        )

        # Clock recovery for bit synchronization
        self.clock_recovery = digital.symbol_sync_ff(
            digital.TED_GARDNER,
            self.audio_rate/self.symbol_rate,  # samples per symbol
            0.045,  # loop bandwidth
            1.0,    # damping factor
            1.0,    # Ted gain
            1.5,    # maximum deviation
            1,      # detector samples per symbol
            digital.constellation_bpsk().base(),
            digital.IR_MMSE_8TAP,
            128,
            []
        )

        # Binary slicer
        self.binary_slicer = digital.binary_slicer_fb()

        # Bit sink to collect data
        self.bit_sink = blocks.vector_sink_b()

        # Raw FM sink for debugging
        self.raw_sink = blocks.vector_sink_f()

        ##################################################
        # Connections
        ##################################################
        self.connect((self.rtlsdr_source, 0), (self.lpf, 0))
        self.connect((self.lpf, 0), (self.fm_demod, 0))
        self.connect((self.fm_demod, 0), (self.raw_sink, 0))
        self.connect((self.fm_demod, 0), (self.clock_recovery, 0))
        self.connect((self.clock_recovery, 0), (self.binary_slicer, 0))
        self.connect((self.binary_slicer, 0), (self.bit_sink, 0))

    def get_bits(self):
        """Get decoded bits"""
        data = self.bit_sink.data()
        self.bit_sink.reset()
        return np.array(data, dtype=np.uint8)

    def get_raw_fm(self):
        """Get raw FM data for debugging"""
        data = self.raw_sink.data()
        self.raw_sink.reset()
        return np.array(data, dtype=np.float32)


class PacketProcessor:
    def __init__(self):
        self.sync_pattern = [0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0]  # 0x2dd4
        self.packet_bits = 256  # 32 bytes
        self.bit_buffer = []

    def process_bits(self, new_bits):
        """Process incoming bits and look for packets"""
        self.bit_buffer.extend(new_bits)

        # Keep buffer manageable
        max_buffer_bits = 10000
        if len(self.bit_buffer) > max_buffer_bits:
            self.bit_buffer = self.bit_buffer[-max_buffer_bits:]

        packets = []

        # Look for sync pattern
        for i in range(len(self.bit_buffer) - len(self.sync_pattern) - self.packet_bits):
            # Check both polarities
            for invert in [False, True]:
                search_bits = self.bit_buffer[i:i+len(self.sync_pattern)]
                if invert:
                    search_bits = [1-b for b in search_bits]

                # Count matching bits
                matches = sum(1 for j in range(len(self.sync_pattern))
                             if search_bits[j] == self.sync_pattern[j])

                if matches >= len(self.sync_pattern) - 2:  # Allow 2 bit errors
                    # Found sync, extract packet
                    packet_start = i + len(self.sync_pattern)
                    packet_bits = self.bit_buffer[packet_start:packet_start + self.packet_bits]

                    if len(packet_bits) >= self.packet_bits:
                        if invert:
                            packet_bits = [1-b for b in packet_bits]

                        packet_bytes = self._bits_to_bytes(packet_bits)
                        decoded = self._decode_packet(packet_bytes)

                        if decoded:
                            packets.append({
                                'sync_errors': len(self.sync_pattern) - matches,
                                'invert': invert,
                                'position': i,
                                'raw_data': packet_bytes.hex(),
                                'decoded': decoded
                            })

                            # Remove processed bits to avoid duplicates
                            self.bit_buffer = self.bit_buffer[i + len(self.sync_pattern) + self.packet_bits:]
                            break

            if packets:  # Found packet, stop searching
                break

        return packets

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
        """Decode packet using RS41 format"""
        if len(packet_bytes) < 32:
            return None

        try:
            if packet_bytes[:2] != b"RS":
                return None

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
                "crc_rx": crc_received,
                "crc_calc": crc_calculated
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
        f"batt={decoded['battery_mv']}mV temp={decoded['mcu_temp_centi'] / 100.0:.2f}C "
        f"uptime={decoded['uptime_ms']}ms"
    )

    if packet['sync_errors'] > 0:
        result += f" (sync_errs={packet['sync_errors']})"
    if packet['invert']:
        result += " (inverted)"

    return result


def main():
    parser = argparse.ArgumentParser(description="GNU Radio GFSK receiver")
    parser.add_argument("--freq", type=float, default=433.92e6, help="Frequency in Hz")
    parser.add_argument("--samp-rate", type=int, default=2000000, help="Sample rate")
    parser.add_argument("--rf-gain", type=float, default=35.0, help="RF gain")
    parser.add_argument("--if-gain", type=float, default=20.0, help="IF gain")
    parser.add_argument("--bb-gain", type=float, default=20.0, help="BB gain")
    parser.add_argument("--debug", action="store_true", help="Show debug info")

    args = parser.parse_args()

    print("GNU Radio GFSK Receiver")
    print(f"Frequency: {args.freq/1e6:.3f} MHz")
    print(f"Sample rate: {args.samp_rate/1e6:.1f} Msps")
    print(f"RF gain: {args.rf_gain} dB")

    # Create receiver
    receiver = GFSKReceiver(
        freq=args.freq,
        samp_rate=args.samp_rate,
        rf_gain=args.rf_gain,
        if_gain=args.if_gain,
        bb_gain=args.bb_gain
    )

    # Create packet processor
    processor = PacketProcessor()

    try:
        receiver.start()
        print("Listening for GFSK packets... (Ctrl+C to stop)")

        packet_count = 0
        last_process_time = time.time()

        while True:
            time.sleep(0.1)  # Process every 100ms

            # Get new bits
            new_bits = receiver.get_bits()

            if len(new_bits) > 0:
                if args.debug:
                    print(f"Got {len(new_bits)} bits")

                # Process bits for packets
                packets = processor.process_bits(new_bits.tolist())

                for packet in packets:
                    packet_count += 1
                    print(f"[{packet_count}] {format_packet(packet)}")

                    if args.debug:
                        print(f"    Raw: {packet['raw_data']}")
                        print(f"    Position: {packet['position']}, Errors: {packet['sync_errors']}")

            # Show periodic status
            current_time = time.time()
            if args.debug and current_time - last_process_time > 5.0:
                raw_fm = receiver.get_raw_fm()
                if len(raw_fm) > 0:
                    print(f"DEBUG: FM signal level: {np.max(np.abs(raw_fm)):.3f}")
                last_process_time = current_time

    except KeyboardInterrupt:
        print(f"\nReceived {packet_count} valid packets")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        receiver.stop()
        receiver.wait()

    return 0


if __name__ == "__main__":
    sys.exit(main())