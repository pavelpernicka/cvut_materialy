#!/usr/bin/env python3
"""
Receiver backend that reuses URH's signal loading and burst segmentation.

The actual symbol slicing is still custom, but it now runs on the same
quadrature-demodulated stream (`Signal.qad`) that URH uses in the GUI.
"""

from __future__ import annotations

import argparse
import queue
import signal
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from telemetry_packet import PACKET_LEN, SYNC_BYTES, format_packet as format_telemetry_packet, parse_packet
from urh.ainterpretation import AutoInterpretation
from urh.signalprocessing.IQArray import IQArray
from urh.signalprocessing.Signal import Signal


SYNC_BITS = np.unpackbits(np.frombuffer(SYNC_BYTES, dtype=np.uint8), bitorder="big")
PREAMBLE_BITS = np.unpackbits(np.full(32, 0xAA, dtype=np.uint8), bitorder="big")
PREFIX_BITS = np.concatenate((PREAMBLE_BITS, SYNC_BITS))
PACKET_BITS_LEN = PACKET_LEN * 8


@dataclass(frozen=True)
class DecodedFrame:
    packet: object
    segment_start: int
    segment_end: int
    samples_per_symbol: int
    phase: int
    center: float
    polarity: str
    sync_errors: int
    bit_position: int


@dataclass(frozen=True)
class CandidateScore:
    matched_sync_bits: int
    matched_preamble_bits: int
    segment_start: int
    segment_end: int
    samples_per_symbol: int
    phase: int
    center: float
    polarity: str
    bit_position: int


class RTLSDRCapture:
    def __init__(self, freq: float, sample_rate: int, gain: float, ppm: int = 0):
        self.freq = freq
        self.sample_rate = sample_rate
        self.gain = gain
        self.ppm = ppm
        self.process: subprocess.Popen[bytes] | None = None
        self.data_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=16)
        self.running = False

    def start(self) -> None:
        cmd = [
            "rtl_sdr",
            "-f", str(int(self.freq)),
            "-s", str(self.sample_rate),
            "-g", str(self.gain),
        ]
        if self.ppm:
            cmd.extend(["-p", str(self.ppm)])
        cmd.append("-")

        print(f"Starting RTL-SDR: {' '.join(cmd)}")
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.capture_thread.start()

    def _capture_worker(self) -> None:
        assert self.process is not None
        assert self.process.stdout is not None

        chunk_size = 131072

        while self.running and self.process.poll() is None:
            data = self.process.stdout.read(chunk_size)
            if not data:
                break

            iq_u8 = np.frombuffer(data, dtype=np.uint8)
            if iq_u8.size < 2 or (iq_u8.size % 2) != 0:
                continue

            iq = iq_u8_to_complex(iq_u8)

            try:
                self.data_queue.put(iq, block=False)
            except queue.Full:
                try:
                    self.data_queue.get(block=False)
                except queue.Empty:
                    pass
                try:
                    self.data_queue.put(iq, block=False)
                except queue.Full:
                    pass

    def get_data(self, timeout: float = 0.25) -> np.ndarray | None:
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        self.running = False
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        if hasattr(self, "capture_thread"):
            self.capture_thread.join(timeout=1)


def iq_u8_to_complex(raw: np.ndarray) -> np.ndarray:
    return ((raw[0::2].astype(np.float32) - 128.0) +
            1j * (raw[1::2].astype(np.float32) - 128.0)).astype(np.complex64)


def load_rtl_u8_file(path: str) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size < 2 or (raw.size % 2) != 0:
        raise ValueError("input file does not contain valid rtl_sdr cu8 IQ data")
    return iq_u8_to_complex(raw)


def build_signal_from_iq(iq: np.ndarray, sample_rate: int, noise_threshold: float) -> Signal:
    signal_obj = Signal("", modulation="FSK", sample_rate=float(sample_rate))
    signal_obj.block_protocol_update = True
    signal_obj.iq_array = IQArray(iq)
    signal_obj.noise_threshold = float(noise_threshold)
    signal_obj.sample_rate = float(sample_rate)
    signal_obj.modulation_type = "FSK"
    signal_obj.bits_per_symbol = 1
    return signal_obj


def burst_segments(signal_obj: Signal, margin: int) -> list[tuple[int, int]]:
    auto_noise = AutoInterpretation.detect_noise_level(signal_obj.iq_array.magnitudes)
    segments = AutoInterpretation.segment_messages_from_magnitudes(
        signal_obj.iq_array.magnitudes, auto_noise
    )

    if not segments:
        return [(0, signal_obj.num_samples)]

    result = []
    for start, end in segments:
        lo = max(0, int(start) - margin)
        hi = min(signal_obj.num_samples, int(end) + margin)
        result.extend(refine_segment(signal_obj, lo, hi, margin))
    return result


def refine_segment(signal_obj: Signal, start: int, end: int, margin: int) -> list[tuple[int, int]]:
    if (end - start) <= 150000:
        return [(start, end)]

    magnitudes = np.asarray(signal_obj.iq_array.magnitudes[start:end], dtype=np.float32)
    if magnitudes.size == 0:
        return [(start, end)]

    peak_threshold = 0.85 * float(np.max(magnitudes))
    peak_mask = magnitudes >= peak_threshold
    peak_indices = np.flatnonzero(peak_mask)

    if peak_indices.size == 0:
        return [(start, end)]

    refined: list[tuple[int, int]] = []
    run_start = int(peak_indices[0])
    previous = int(peak_indices[0])

    for index in peak_indices[1:]:
        current = int(index)
        if (current - previous) > 5000:
            if (previous + 1 - run_start) >= 1000:
                refined.append(_expand_segment(start, run_start, previous + 1, magnitudes.size, margin))
            run_start = current
        previous = current

    if (previous + 1 - run_start) >= 1000:
        refined.append(_expand_segment(start, run_start, previous + 1, magnitudes.size, margin))
    return refined or [(start, end)]


def _expand_segment(base_start: int, local_start: int, local_end: int, max_len: int, margin: int) -> tuple[int, int]:
    effective_margin = max(margin, 32000)
    lo = max(0, local_start - effective_margin)
    hi = min(max_len, local_end + effective_margin)
    return (base_start + lo, base_start + hi)


class URHBackedDecoder:
    def __init__(
        self,
        sample_rate: int,
        samples_per_symbol: int,
        symbol_span: int,
        center: float,
        sync_error_tolerance: int,
        preamble_error_tolerance: int,
        noise_threshold: float,
        burst_margin: int,
        verbose: bool,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.samples_per_symbol = int(samples_per_symbol)
        self.symbol_span = max(0, int(symbol_span))
        self.center = float(center)
        self.sync_error_tolerance = max(0, int(sync_error_tolerance))
        self.preamble_error_tolerance = max(0, int(preamble_error_tolerance))
        self.noise_threshold = float(noise_threshold)
        self.burst_margin = max(0, int(burst_margin))
        self.verbose = verbose
        self.seen_keys: set[tuple[int, int]] = set()

    def decode_iq(self, iq: np.ndarray) -> tuple[list[DecodedFrame], CandidateScore | None]:
        signal_obj = build_signal_from_iq(iq, self.sample_rate, self.noise_threshold)
        segments = burst_segments(signal_obj, self.burst_margin)

        if self.verbose:
            print(f"Detected {len(segments)} candidate burst(s): {segments}", flush=True)

        frames: list[DecodedFrame] = []
        best_candidate: CandidateScore | None = None

        for segment_start, segment_end in segments:
            qad = np.asarray(signal_obj.qad[segment_start:segment_end], dtype=np.float32)
            segment_frames, segment_best = self._decode_segment(qad, segment_start, segment_end)
            frames.extend(segment_frames)

            if best_candidate is None:
                best_candidate = segment_best
            elif segment_best is not None and segment_best.matched_sync_bits > best_candidate.matched_sync_bits:
                best_candidate = segment_best

        return frames, best_candidate

    def _decode_segment(
        self,
        qad: np.ndarray,
        segment_start: int,
        segment_end: int,
    ) -> tuple[list[DecodedFrame], CandidateScore | None]:
        min_sps = max(1, self.samples_per_symbol - self.symbol_span)
        max_sps = max(min_sps, self.samples_per_symbol + self.symbol_span)

        frames: list[DecodedFrame] = []
        best_candidate: CandidateScore | None = None

        for sps in range(min_sps, max_sps + 1):
            needed_symbols = len(SYNC_BITS) + PACKET_BITS_LEN
            if qad.size < needed_symbols * sps:
                continue

            for phase in range(sps):
                symbol_count = (qad.size - phase) // sps
                if symbol_count < needed_symbols:
                    continue

                trimmed = qad[phase:phase + symbol_count * sps]
                symbol_means = trimmed.reshape(symbol_count, sps).mean(axis=1)

                for center in self._candidate_centers(symbol_means):
                    bits = (symbol_means > center).astype(np.uint8)

                    for polarity_name, candidate_bits in (
                        ("normal", bits),
                        ("inverted", 1 - bits),
                    ):
                        frame = self._find_packet(
                            qad,
                            candidate_bits,
                            segment_start,
                            segment_end,
                            sps,
                            phase,
                            center,
                            polarity_name,
                        )
                        if frame is not None:
                            key = frame.packet.dedupe_key
                            if key not in self.seen_keys:
                                self.seen_keys.add(key)
                                frames.append(frame)

                        matched_sync_bits, matched_preamble_bits, bit_position = self._best_sync_match(candidate_bits)
                        candidate = CandidateScore(
                            matched_sync_bits=matched_sync_bits,
                            matched_preamble_bits=matched_preamble_bits,
                            segment_start=segment_start,
                            segment_end=segment_end,
                            samples_per_symbol=sps,
                            phase=phase,
                            center=center,
                            polarity=polarity_name,
                            bit_position=bit_position,
                        )
                        if (
                            best_candidate is None or
                            (candidate.matched_sync_bits, candidate.matched_preamble_bits) >
                            (best_candidate.matched_sync_bits, best_candidate.matched_preamble_bits)
                        ):
                            best_candidate = candidate

        return frames, best_candidate

    def _candidate_centers(self, symbol_means: np.ndarray) -> list[float]:
        if symbol_means.size == 0:
            return [self.center]

        percentiles = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95]
        centers = [self.center]
        centers.extend(float(np.percentile(symbol_means, p)) for p in percentiles)
        return sorted(set(centers))

    def _best_sync_match(self, bits: np.ndarray) -> tuple[int, int, int]:
        limit = bits.size - len(SYNC_BITS) - PACKET_BITS_LEN + 1
        if limit <= 0:
            return (0, 0, 0)

        windows = np.lib.stride_tricks.sliding_window_view(bits, len(SYNC_BITS))
        matches = np.sum(windows[:limit] == SYNC_BITS, axis=1)
        position = int(matches.argmax())
        preamble_matches = 0
        if position >= len(PREAMBLE_BITS):
            preamble = bits[position - len(PREAMBLE_BITS):position]
            preamble_matches = int(np.sum(preamble == PREAMBLE_BITS))
        return int(matches[position]), preamble_matches, position

    def _find_packet(
        self,
        qad: np.ndarray,
        bits: np.ndarray,
        segment_start: int,
        segment_end: int,
        samples_per_symbol: int,
        phase: int,
        center: float,
        polarity: str,
    ) -> DecodedFrame | None:
        limit = bits.size - len(SYNC_BITS) - PACKET_BITS_LEN + 1
        if limit <= 0:
            return None

        windows = np.lib.stride_tricks.sliding_window_view(bits, len(SYNC_BITS))
        matches = np.sum(windows[:limit] == SYNC_BITS, axis=1)
        positions = np.flatnonzero(matches >= (len(SYNC_BITS) - self.sync_error_tolerance))
        ordered_positions = sorted(positions.tolist(), key=lambda pos: int(matches[pos]), reverse=True)[:8]

        for bit_position in ordered_positions:
            if bit_position < len(PREAMBLE_BITS):
                continue

            preamble = bits[bit_position - len(PREAMBLE_BITS):bit_position]
            preamble_matches = int(np.sum(preamble == PREAMBLE_BITS))
            if preamble_matches < (len(PREAMBLE_BITS) - self.preamble_error_tolerance):
                parsed, refined_sps, refined_center = self._refine_packet_from_sync(
                    qad=qad,
                    approx_samples_per_symbol=float(samples_per_symbol),
                    approx_phase=phase,
                    approx_center=center,
                    bit_position=bit_position,
                    polarity=polarity,
                )
                if parsed is not None:
                    return DecodedFrame(
                        packet=parsed,
                        segment_start=segment_start,
                        segment_end=segment_end,
                        samples_per_symbol=refined_sps,
                        phase=phase,
                        center=refined_center,
                        polarity=polarity,
                        sync_errors=int(len(SYNC_BITS) - matches[bit_position]),
                        bit_position=bit_position,
                    )
                continue

            packet_start = bit_position + len(SYNC_BITS)
            packet_end = packet_start + PACKET_BITS_LEN
            packet_bits = bits[packet_start:packet_end]
            if packet_bits.size != PACKET_BITS_LEN:
                continue

            packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
            parsed = parse_packet(packet_bytes)
            if parsed is None:
                parsed, refined_sps, refined_center = self._refine_packet_from_sync(
                    qad=qad,
                    approx_samples_per_symbol=float(samples_per_symbol),
                    approx_phase=phase,
                    approx_center=center,
                    bit_position=bit_position,
                    polarity=polarity,
                )
                if parsed is None:
                    continue
            else:
                refined_sps = float(samples_per_symbol)
                refined_center = center

            return DecodedFrame(
                packet=parsed,
                segment_start=segment_start,
                segment_end=segment_end,
                samples_per_symbol=refined_sps,
                phase=phase,
                center=refined_center,
                polarity=polarity,
                sync_errors=int(len(SYNC_BITS) - matches[bit_position]),
                bit_position=bit_position,
            )

        return None

    def _refine_packet_from_sync(
        self,
        qad: np.ndarray,
        approx_samples_per_symbol: float,
        approx_phase: int,
        approx_center: float,
        bit_position: int,
        polarity: str,
    ) -> tuple[object | None, float, float]:
        if bit_position < len(PREAMBLE_BITS):
            return (None, approx_samples_per_symbol, approx_center)

        prefix_start_symbol = bit_position - len(PREAMBLE_BITS)
        approx_prefix_start = float(approx_phase) + float(prefix_start_symbol) * approx_samples_per_symbol
        total_symbols = len(PREFIX_BITS) + PACKET_BITS_LEN

        best_score: tuple[int, int] | None = None
        best_packet: object | None = None
        best_sps = approx_samples_per_symbol
        best_center = approx_center

        for sps in np.linspace(max(1.0, approx_samples_per_symbol - 2.0), approx_samples_per_symbol + 2.0, 17):
            start_offsets = np.linspace(approx_prefix_start - 1.5 * approx_samples_per_symbol,
                                        approx_prefix_start + 1.5 * approx_samples_per_symbol, 17)
            for prefix_start in start_offsets:
                symbol_means = self._fractional_symbol_means(qad, prefix_start, sps, total_symbols)
                if symbol_means is None:
                    continue

                centers = [approx_center]
                centers.extend(float(np.percentile(symbol_means[:len(PREFIX_BITS)], p)) for p in (25, 40, 50, 60, 75))

                for center in sorted(set(centers)):
                    bits = (symbol_means > center).astype(np.uint8)
                    for trial_polarity, candidate_bits in (
                        (polarity, bits if polarity == "normal" else 1 - bits),
                        ("inverted" if polarity == "normal" else "normal", 1 - bits if polarity == "normal" else bits),
                    ):
                        prefix_matches = int(np.sum(candidate_bits[:len(PREFIX_BITS)] == PREFIX_BITS))
                        sync_matches = int(np.sum(candidate_bits[len(PREAMBLE_BITS):len(PREFIX_BITS)] == SYNC_BITS))
                        score = (prefix_matches, sync_matches)

                        if best_score is None or score > best_score:
                            best_score = score
                            best_sps = float(sps)
                            best_center = float(center)

                        if sync_matches < (len(SYNC_BITS) - self.sync_error_tolerance):
                            continue

                        packet_bits = candidate_bits[len(PREFIX_BITS):len(PREFIX_BITS) + PACKET_BITS_LEN]
                        packet_bytes = np.packbits(packet_bits, bitorder="big").tobytes()
                        parsed = parse_packet(packet_bytes)
                        if parsed is not None:
                            return (parsed, float(sps), float(center))

        return (best_packet, best_sps, best_center)

    @staticmethod
    def _fractional_symbol_means(
        qad: np.ndarray,
        start: float,
        samples_per_symbol: float,
        symbol_count: int,
    ) -> np.ndarray | None:
        if samples_per_symbol <= 0.0:
            return None

        stop = start + samples_per_symbol * symbol_count
        if start < 0.0 or stop > float(qad.size):
            return None

        csum = np.concatenate((np.array([0.0], dtype=np.float64), np.cumsum(qad, dtype=np.float64)))
        bounds = start + samples_per_symbol * np.arange(symbol_count + 1, dtype=np.float64)
        indices = np.arange(csum.size, dtype=np.float64)
        samples = np.interp(bounds, indices, csum)
        return ((samples[1:] - samples[:-1]) / samples_per_symbol).astype(np.float32)


def print_frames(frames: list[DecodedFrame]) -> None:
    for index, frame in enumerate(frames, start=1):
        print(
            f"[{index}] {format_telemetry_packet(frame.packet)} "
            f"sync_err={frame.sync_errors} sps={frame.samples_per_symbol} "
            f"phase={frame.phase} center={frame.center:.5f} polarity={frame.polarity} "
            f"segment={frame.segment_start}:{frame.segment_end} bit_pos={frame.bit_position}",
            flush=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="URH-backed direct FSK decoder")
    parser.add_argument("--freq", type=float, default=433.920e6)
    parser.add_argument("--sample-rate", type=int, default=500000)
    parser.add_argument("--samples-per-symbol", type=int, default=208)
    parser.add_argument("--symbol-span", type=int, default=16)
    parser.add_argument("--center", type=float, default=0.0563)
    parser.add_argument("--sync-errors", type=int, default=10)
    parser.add_argument("--preamble-errors", type=int, default=24)
    parser.add_argument("--noise", type=float, default=0.0)
    parser.add_argument("--burst-margin", type=int, default=4000)
    parser.add_argument("--gain", type=float, default=20.0)
    parser.add_argument("--ppm", type=int, default=0)
    parser.add_argument("--input-file")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print(f"Frequency: {args.freq / 1e6:.3f} MHz")
    print(f"Sample rate: {args.sample_rate} Hz")
    print(f"Samples/symbol center: {args.samples_per_symbol}")
    print(f"Symbol span: +/-{args.symbol_span}")
    print(f"Center: {args.center:.5f}")
    print(f"Sync error tolerance: {args.sync_errors}")
    print(f"URH noise threshold: {args.noise:.5f}")

    decoder = URHBackedDecoder(
        sample_rate=args.sample_rate,
        samples_per_symbol=args.samples_per_symbol,
        symbol_span=args.symbol_span,
        center=args.center,
        sync_error_tolerance=args.sync_errors,
        preamble_error_tolerance=args.preamble_errors,
        noise_threshold=args.noise,
        burst_margin=args.burst_margin,
        verbose=args.verbose,
    )

    if args.input_file:
        iq = load_rtl_u8_file(args.input_file)
        print(f"Loaded IQ file: {Path(args.input_file)} samples={iq.size}")
        frames, best_candidate = decoder.decode_iq(iq)
        print_frames(frames)
        if not frames and best_candidate is not None:
            print(
                "Best candidate without valid CRC: "
                f"sync_bits={best_candidate.matched_sync_bits}/{len(SYNC_BITS)} "
                f"preamble_bits={best_candidate.matched_preamble_bits}/{len(PREAMBLE_BITS)} "
                f"sps={best_candidate.samples_per_symbol} phase={best_candidate.phase} "
                f"center={best_candidate.center:.5f} polarity={best_candidate.polarity} "
                f"segment={best_candidate.segment_start}:{best_candidate.segment_end} "
                f"bit_pos={best_candidate.bit_position}",
                flush=True,
            )
        print(f"Received {len(frames)} packets")
        return 0 if frames else 1

    capture = RTLSDRCapture(args.freq, args.sample_rate, args.gain, args.ppm)

    def stop_handler(_signum, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    packet_count = 0
    iq_buffer = np.array([], dtype=np.complex64)
    buffer_limit = args.sample_rate * 12

    try:
        capture.start()
        print("Listening for RS41 telemetry packets...")

        while True:
            iq_chunk = capture.get_data()
            if iq_chunk is None:
                continue

            iq_buffer = np.concatenate((iq_buffer, iq_chunk))
            if iq_buffer.size > buffer_limit:
                iq_buffer = iq_buffer[-buffer_limit:]

            frames, best_candidate = decoder.decode_iq(iq_buffer)
            if frames:
                new_frames = frames[packet_count:]
                packet_count = len(frames)
                print_frames(new_frames)
            elif args.verbose and best_candidate is not None:
                print(
                    "No valid packet yet. "
                    f"Best candidate: sync_bits={best_candidate.matched_sync_bits}/{len(SYNC_BITS)} "
                    f"preamble_bits={best_candidate.matched_preamble_bits}/{len(PREAMBLE_BITS)} "
                    f"sps={best_candidate.samples_per_symbol} phase={best_candidate.phase} "
                    f"center={best_candidate.center:.5f} polarity={best_candidate.polarity} "
                    f"segment={best_candidate.segment_start}:{best_candidate.segment_end} "
                    f"bit_pos={best_candidate.bit_position}",
                    flush=True,
                )

    except KeyboardInterrupt:
        print(f"\nReceived {packet_count} packets")
        return 0 if packet_count else 1
    finally:
        capture.stop()


if __name__ == "__main__":
    raise SystemExit(main())
