#!/usr/bin/env python3
import argparse
import math
import signal
import subprocess
import sys
import time
import wave
from dataclasses import dataclass

import numpy as np
from gnuradio import blocks, digital, filter, gr

from ax25_aprs import PACKET_LEN, Packet, crc16_x25, format_packet, looks_like_ax25_ui_frame, parse_packet

SYNC_BYTES = b"\x2d\xd4"
PREAMBLE_LEN = 16
DEFAULT_SAMPLE_RATE = 240000
DEFAULT_SYMBOL_RATE = 1200

@dataclass
class FrameCandidate:
    burst_index: int
    burst_start_sample: int
    burst_end_sample: int
    target_sps: int
    freq_offset_hz: float
    polarity: str
    bit_offset: int
    byte_pos: int
    sync_bit_errors: int
    preamble_errors: int
    has_magic: bool
    crc_ok: bool
    payload_prefix_hex: str
    crc_rx: int | None
    crc_calc: int | None


@dataclass
class Burst:
    index: int
    start_sample: int
    end_sample: int
    peak_env: float


@dataclass
class FrameWindow:
    burst_index: int
    start_sample: int
    end_sample: int
    plateau_level: float
    threshold_on: float
    threshold_off: float

def detect_input_format(path: str, forced: str) -> str:
    if forced != "auto":
        return forced
    if path.lower().endswith(".wav"):
        return "wav_iq"
    return "rtl_u8"


def load_wav_iq_file(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        nframes = wav_file.getnframes()
        if channels != 2:
            raise ValueError("WAV IQ file must be stereo")
        raw = wav_file.readframes(nframes)

    if sample_width == 1:
        iq = np.frombuffer(raw, dtype=np.uint8).astype(np.float32).reshape(-1, 2)
        samples = (iq[:, 0] - 127.5) + 1j * (iq[:, 1] - 127.5)
    elif sample_width == 2:
        iq = np.frombuffer(raw, dtype=np.int16).astype(np.float32).reshape(-1, 2)
        samples = iq[:, 0] + 1j * iq[:, 1]
    elif sample_width == 4:
        iq = np.frombuffer(raw, dtype=np.int32).astype(np.float32).reshape(-1, 2)
        samples = iq[:, 0] + 1j * iq[:, 1]
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width}")

    return samples.astype(np.complex64), frame_rate


def load_iq_file(path: str, input_format: str) -> tuple[np.ndarray, int | None]:
    if input_format == "rtl_u8":
        raw = np.fromfile(path, dtype=np.uint8)
        if raw.size < 2 or raw.size % 2 != 0:
            raise ValueError("Invalid rtl_u8 IQ file")
        iq = raw.astype(np.float32).reshape(-1, 2)
        samples = (iq[:, 0] - 127.5) + 1j * (iq[:, 1] - 127.5)
        return samples.astype(np.complex64), None

    if input_format == "wav_iq":
        return load_wav_iq_file(path)

    raise ValueError(f"Unsupported input format: {input_format}")


def detect_gfsk_packets(samples: np.ndarray, sample_rate: int, symbol_rate: int) -> list[tuple[int, float, float]]:
    """
    Detect GFSK packet start positions by looking for sync patterns in demodulated data
    Returns list of (start_sample, confidence_score, freq_offset) tuples
    """
    if samples.size < sample_rate // 10:  # Need at least 100ms of data
        return []

    detected_packets = []
    target_sps = 10

    # Try multiple frequency offsets to find packets
    for freq_offset in [-10000, -5000, 0, 5000, 10000]:
        # Apply frequency offset correction
        offset_samples = apply_frequency_offset(samples, sample_rate, freq_offset)

        # Demodulate to bits
        try:
            bits = gnuradio_gfsk_demod(offset_samples, sample_rate, symbol_rate, target_sps)

            # Look for sync pattern in both polarities
            sync_pattern = np.array([int(x) for x in format(0x2dd4, '016b')])  # 16-bit sync

            for polarity in [0, 1]:  # normal and inverted
                search_bits = bits ^ polarity

                # Correlate with sync pattern
                if len(search_bits) < len(sync_pattern):
                    continue

                correlation = np.correlate(search_bits.astype(float), sync_pattern.astype(float), mode='valid')

                # Find peaks above threshold
                threshold = len(sync_pattern) * 0.8  # Allow some bit errors
                peaks = np.where(correlation > threshold)[0]

                for peak_pos in peaks:
                    # Convert bit position back to sample position
                    samples_per_bit = sample_rate / symbol_rate
                    start_sample = int(peak_pos * samples_per_bit / target_sps)
                    confidence = float(correlation[peak_pos]) / len(sync_pattern)

                    detected_packets.append((start_sample, confidence, freq_offset))

        except Exception:
            continue

    # Sort by confidence and remove duplicates
    detected_packets.sort(key=lambda x: x[1], reverse=True)

    # Remove nearby duplicates (within 1000 samples)
    filtered_packets = []
    for packet in detected_packets:
        is_duplicate = False
        for existing in filtered_packets:
            if abs(packet[0] - existing[0]) < 1000:
                is_duplicate = True
                break
        if not is_duplicate:
            filtered_packets.append(packet)

    return filtered_packets[:5]  # Return top 5 candidates


def gnuradio_gfsk_demod(samples: np.ndarray, sample_rate: int, symbol_rate: int, target_sps: int) -> np.ndarray:
    target_rate = symbol_rate * target_sps
    divisor = math.gcd(sample_rate, target_rate)
    interpolation = target_rate // divisor
    decimation = sample_rate // divisor

    tb = gr.top_block()
    src = blocks.vector_source_c(samples.astype(np.complex64), False)
    current = src

    if interpolation != 1 or decimation != 1:
        resampler = filter.rational_resampler_ccc(
            interpolation=interpolation,
            decimation=decimation,
        )
        tb.connect(current, resampler)
        current = resampler

    demod = digital.gfsk_demod(samples_per_symbol=target_sps, sensitivity=0.5)
    sink = blocks.vector_sink_b()
    tb.connect(current, demod, sink)
    tb.run()
    return np.array(sink.data(), dtype=np.uint8) & 1


def apply_frequency_offset(samples: np.ndarray, sample_rate: int, freq_offset_hz: float) -> np.ndarray:
    if abs(freq_offset_hz) < 1e-9:
        return samples
    n = np.arange(samples.size, dtype=np.float32)
    rot = np.exp(-1j * 2.0 * np.pi * float(freq_offset_hz) * n / float(sample_rate)).astype(np.complex64)
    return (samples * rot).astype(np.complex64)


def detect_bursts(
    samples: np.ndarray,
    sample_rate: int,
    *,
    window_ms: float,
    threshold_mad: float,
    merge_gap_ms: float,
    min_duration_ms: float,
    pad_ms: float,
) -> tuple[list[Burst], np.ndarray, float]:
    if samples.size == 0:
        return [], np.array([], dtype=np.float32), 0.0

    # For GFSK, detect activity using frequency discriminator instead of amplitude
    if samples.size < 2:
        return [], np.array([]), 0.0

    # Compute frequency discriminator
    discrim = np.angle(samples[1:] * np.conj(samples[:-1])).astype(np.float32)
    discrim_abs = np.abs(discrim)

    # Smooth the discriminator output
    window = max(16, int(sample_rate * window_ms / 1000.0))
    kernel = np.ones(window, dtype=np.float32) / float(window)
    env = np.convolve(discrim_abs, kernel, mode="same")

    # Pad to match original sample size
    env = np.concatenate([[env[0]], env])

    median = float(np.median(env))
    mad = float(np.median(np.abs(env - median)))
    if mad < 1e-6:
        mad = max(1e-6, median * 0.05)
    threshold = median + threshold_mad * mad

    active = env > threshold
    active_idx = np.flatnonzero(active)
    if active_idx.size == 0:
        return [], env, threshold

    merge_gap = max(1, int(sample_rate * merge_gap_ms / 1000.0))
    min_duration = max(1, int(sample_rate * min_duration_ms / 1000.0))
    pad = max(0, int(sample_rate * pad_ms / 1000.0))

    bursts: list[Burst] = []
    start = int(active_idx[0])
    prev = int(active_idx[0])
    burst_index = 0

    for idx in active_idx[1:]:
        idx = int(idx)
        if idx - prev <= merge_gap:
            prev = idx
            continue

        seg_start = max(0, start - pad)
        seg_end = min(samples.size, prev + 1 + pad)
        if seg_end - seg_start >= min_duration:
            bursts.append(Burst(
                index=burst_index,
                start_sample=seg_start,
                end_sample=seg_end,
                peak_env=float(np.max(env[seg_start:seg_end])),
            ))
            burst_index += 1
        start = prev = idx

    seg_start = max(0, start - pad)
    seg_end = min(samples.size, prev + 1 + pad)
    if seg_end - seg_start >= min_duration:
        bursts.append(Burst(
            index=burst_index,
            start_sample=seg_start,
            end_sample=seg_end,
            peak_env=float(np.max(env[seg_start:seg_end])),
        ))

    return bursts, env, threshold


def refine_burst_to_frame_window(
    samples: np.ndarray,
    sample_rate: int,
    symbol_rate: int,
    burst: Burst,
    discrim_baseline: float,
) -> FrameWindow:
    segment = samples[burst.start_sample:burst.end_sample]
    if segment.size < 8:
        return FrameWindow(
            burst_index=burst.index,
            start_sample=burst.start_sample,
            end_sample=burst.end_sample,
            plateau_level=0.0,
            threshold_on=0.0,
            threshold_off=0.0,
        )

    decim = max(1, sample_rate // (symbol_rate * 10))
    discrim = np.angle(segment[1:] * np.conj(segment[:-1])).astype(np.float32)
    discrim -= float(discrim_baseline)
    usable = (discrim.size // decim) * decim
    if usable < decim:
        return FrameWindow(
            burst_index=burst.index,
            start_sample=burst.start_sample,
            end_sample=burst.end_sample,
            plateau_level=0.0,
            threshold_on=0.0,
            threshold_off=0.0,
        )

    decimated = discrim[:usable].reshape(-1, decim).mean(axis=1).astype(np.float32)
    smooth_len = max(5, int((sample_rate / decim) * 0.002))
    if smooth_len % 2 == 0:
        smooth_len += 1
    kernel = np.ones(smooth_len, dtype=np.float32) / float(smooth_len)
    smooth = np.convolve(decimated, kernel, mode="same")

    plateau_level = float(np.percentile(smooth, 80))
    threshold_on = max(0.02, plateau_level * 0.60)
    threshold_off = max(0.015, plateau_level * 0.45)

    active = smooth > threshold_on
    idx = np.flatnonzero(active)
    if idx.size == 0:
        return FrameWindow(
            burst_index=burst.index,
            start_sample=burst.start_sample,
            end_sample=burst.end_sample,
            plateau_level=plateau_level,
            threshold_on=threshold_on,
            threshold_off=threshold_off,
        )

    merge_gap = max(1, int((sample_rate / decim) * 0.004))
    best_start = int(idx[0])
    best_end = int(idx[0])
    cur_start = int(idx[0])
    prev = int(idx[0])
    best_score = -1

    def score_region(a: int, b: int) -> float:
        region = smooth[a:b + 1]
        return float(np.mean(region) * (b - a + 1))

    for item in idx[1:]:
        item = int(item)
        if item - prev <= merge_gap:
            prev = item
            continue
        score = score_region(cur_start, prev)
        if score > best_score:
            best_score = score
            best_start, best_end = cur_start, prev
        cur_start = prev = item
    score = score_region(cur_start, prev)
    if score > best_score:
        best_start, best_end = cur_start, prev

    while best_start > 0 and smooth[best_start - 1] > threshold_off:
        best_start -= 1
    while best_end + 1 < smooth.size and smooth[best_end + 1] > threshold_off:
        best_end += 1

    pad_dec = max(2, int((sample_rate / decim) * 0.003))
    best_start = max(0, best_start - pad_dec)
    best_end = min(smooth.size - 1, best_end + pad_dec)

    start_sample = burst.start_sample + best_start * decim
    end_sample = min(burst.end_sample, burst.start_sample + (best_end + 1) * decim)

    return FrameWindow(
        burst_index=burst.index,
        start_sample=start_sample,
        end_sample=end_sample,
        plateau_level=plateau_level,
        threshold_on=threshold_on,
        threshold_off=threshold_off,
    )


def find_frame_candidates(
    bits: np.ndarray,
    debug_limit: int,
    *,
    sync_threshold: int,
    max_preamble_errors: int,
    freq_offset_hz: float,
    burst: Burst,
) -> tuple[list[FrameCandidate], list[Packet]]:
    candidates: list[FrameCandidate] = []
    packets: list[Packet] = []
    seen_packets: set[tuple[str, str]] = set()
    sync_hi = SYNC_BYTES[0]
    sync_lo = SYNC_BYTES[1]

    for polarity_name, stream in (("normal", bits), ("inverted", bits ^ 1)):
        for bit_offset in range(8):
            aligned = stream[bit_offset:]
            usable = (aligned.size // 8) * 8
            if usable < (PREAMBLE_LEN + len(SYNC_BYTES) + PACKET_LEN) * 8:
                continue

            packed = np.packbits(aligned[:usable], bitorder="big")
            for sync_pos in range(PREAMBLE_LEN, len(packed) - PACKET_LEN - 1):
                sync_bit_errors = int((int(packed[sync_pos]) ^ sync_hi).bit_count() + (int(packed[sync_pos + 1]) ^ sync_lo).bit_count())
                if sync_bit_errors > sync_threshold:
                    continue

                preamble = packed[sync_pos - PREAMBLE_LEN:sync_pos]
                preamble_errors = int(sum((byte ^ 0x55).bit_count() for byte in preamble))
                if preamble_errors > max_preamble_errors:
                    continue

                payload = packed[sync_pos + len(SYNC_BYTES):sync_pos + len(SYNC_BYTES) + PACKET_LEN].tobytes()
                if len(payload) < PACKET_LEN:
                    continue

                has_magic = looks_like_ax25_ui_frame(payload)
                crc_rx = int.from_bytes(payload[-2:], "little")
                crc_calc = crc16_x25(payload[:-2])
                crc_ok = has_magic and crc_rx == crc_calc

                candidate = FrameCandidate(
                    burst_index=burst.index,
                    burst_start_sample=burst.start_sample,
                    burst_end_sample=burst.end_sample,
                    target_sps=0,
                    freq_offset_hz=float(freq_offset_hz),
                    polarity=polarity_name,
                    bit_offset=bit_offset,
                    byte_pos=sync_pos,
                    sync_bit_errors=sync_bit_errors,
                    preamble_errors=preamble_errors,
                    has_magic=has_magic,
                    crc_ok=crc_ok,
                    payload_prefix_hex=payload[:12].hex(),
                    crc_rx=crc_rx if has_magic else None,
                    crc_calc=crc_calc if has_magic else None,
                )
                candidates.append(candidate)

                if crc_ok:
                    packet = parse_packet(payload)
                    if packet is not None:
                        packet_key = packet.dedupe_key
                        if packet_key not in seen_packets:
                            seen_packets.add(packet_key)
                            packets.append(packet)

    candidates.sort(
        key=lambda item: (
            item.preamble_errors,
            item.sync_bit_errors,
            0 if item.crc_ok else 1,
            0 if item.has_magic else 1,
            abs(item.freq_offset_hz),
        )
    )
    return candidates[:debug_limit], packets


def decode_burst_over_offsets(
    burst: Burst,
    burst_samples: np.ndarray,
    sample_rate: int,
    symbol_rate: int,
    target_sps_values: list[int],
    offsets_hz: list[float],
    debug_limit: int,
    sync_threshold: int,
    max_preamble_errors: int,
) -> tuple[list[FrameCandidate], list[Packet], dict[tuple[int, float], tuple[int, int]]]:
    all_candidates: list[FrameCandidate] = []
    all_packets: list[Packet] = []
    stats: dict[tuple[int, float], tuple[int, int]] = {}
    seen_packets: set[tuple[str, str]] = set()

    for target_sps in target_sps_values:
        for freq_offset_hz in offsets_hz:
            shifted = apply_frequency_offset(burst_samples, sample_rate, freq_offset_hz)
            bits = gnuradio_gfsk_demod(shifted, sample_rate, symbol_rate, target_sps)
            candidates, packets = find_frame_candidates(
                bits,
                debug_limit,
                sync_threshold=sync_threshold,
                max_preamble_errors=max_preamble_errors,
                freq_offset_hz=freq_offset_hz,
                burst=burst,
            )
            for candidate in candidates:
                candidate.target_sps = target_sps
            all_candidates.extend(candidates)
            stats[(int(target_sps), float(freq_offset_hz))] = (len(bits), len(candidates))
            for packet in packets:
                packet_key = packet.dedupe_key
                if packet_key not in seen_packets:
                    seen_packets.add(packet_key)
                    all_packets.append(packet)

    all_candidates.sort(
        key=lambda item: (
            item.preamble_errors,
            item.sync_bit_errors,
            0 if item.crc_ok else 1,
            0 if item.has_magic else 1,
            abs(item.freq_offset_hz),
        )
    )
    return all_candidates[:debug_limit], all_packets, stats


def decode_detected_bursts(
    samples: np.ndarray,
    sample_rate: int,
    symbol_rate: int,
    target_sps_values: list[int],
    offsets_hz: list[float],
    debug_limit: int,
    sync_threshold: int,
    max_preamble_errors: int,
    *,
    burst_window_ms: float,
    burst_threshold_mad: float,
    burst_merge_gap_ms: float,
    burst_min_duration_ms: float,
    burst_pad_ms: float,
) -> tuple[list[Burst], list[FrameCandidate], list[Packet], dict[int, dict[float, tuple[int, int]]], np.ndarray, float]:
    bursts, envelope, threshold = detect_bursts(
        samples,
        sample_rate,
        window_ms=burst_window_ms,
        threshold_mad=burst_threshold_mad,
        merge_gap_ms=burst_merge_gap_ms,
        min_duration_ms=burst_min_duration_ms,
        pad_ms=burst_pad_ms,
    )

    all_candidates: list[FrameCandidate] = []
    all_packets: list[Packet] = []
    seen_packets: set[tuple[str, str]] = set()
    all_stats: dict[int, dict[tuple[int, float], tuple[int, int]]] = {}
    frame_windows: list[FrameWindow] = []

    if not bursts:
        fallback = Burst(index=0, start_sample=0, end_sample=samples.size, peak_env=float(np.max(envelope)) if envelope.size else 0.0)
        bursts = [fallback]

    if samples.size >= 2:
        discrim_baseline = float(np.mean(np.angle(samples[1:] * np.conj(samples[:-1]))))
    else:
        discrim_baseline = 0.0

    for burst in bursts:
        frame_window = refine_burst_to_frame_window(samples, sample_rate, symbol_rate, burst, discrim_baseline)
        frame_windows.append(frame_window)
        burst_for_decode = Burst(
            index=burst.index,
            start_sample=frame_window.start_sample,
            end_sample=frame_window.end_sample,
            peak_env=burst.peak_env,
        )
        burst_samples = samples[burst_for_decode.start_sample:burst_for_decode.end_sample]
        candidates, packets, stats = decode_burst_over_offsets(
            burst_for_decode,
            burst_samples,
            sample_rate,
            symbol_rate,
            target_sps_values,
            offsets_hz,
            debug_limit,
            sync_threshold,
            max_preamble_errors,
        )
        all_candidates.extend(candidates)
        all_stats[burst.index] = stats
        for packet in packets:
            packet_key = packet.dedupe_key
            if packet_key not in seen_packets:
                seen_packets.add(packet_key)
                all_packets.append(packet)

    all_candidates.sort(
        key=lambda item: (
            item.preamble_errors,
            item.sync_bit_errors,
            0 if item.crc_ok else 1,
            0 if item.has_magic else 1,
            abs(item.freq_offset_hz),
        )
    )
    return bursts, frame_windows, all_candidates[:debug_limit], all_packets, all_stats, envelope, threshold


class Plotter:
    def __init__(self, window_sec: float):
        import matplotlib.pyplot as plt

        self.plt = plt
        self.window_sec = float(window_sec)
        plt.ion()
        self.fig, self.axes = plt.subplots(3, 1, figsize=(11, 8))
        self.fig.canvas.manager.set_window_title("RS41 Receiver")

        self.lines = [
            self.axes[0].plot([], [], lw=1.0)[0],
            self.axes[1].plot([], [], lw=1.0)[0],
            self.axes[2].plot([], [], lw=1.0)[0],
        ]
        self.span_artists = []

        self.axes[0].set_title("Received Signal Magnitude")
        self.axes[1].set_title("FM Discriminator")
        self.axes[2].set_title("Decimated Demodulated Signal")
        self.axes[0].set_ylabel("Mag")
        self.axes[1].set_ylabel("Disc")
        self.axes[2].set_ylabel("Decim")
        self.axes[2].set_xlabel("Time [s]")

        for ax in self.axes:
            ax.grid(True, alpha=0.3)

        self.last_draw = 0.0

    def update(self, sample_rate: int, rx_mag: np.ndarray, discrim: np.ndarray, decimated: np.ndarray, burst_ranges: list[tuple[float, float]]):
        now = time.monotonic()
        if now - self.last_draw < 0.05:
            return
        self.last_draw = now

        series = [
            rx_mag,
            discrim,
            decimated,
        ]
        rates = [
            max(1.0, rx_mag.size / self.window_sec),
            max(1.0, discrim.size / self.window_sec),
            max(1.0, decimated.size / self.window_sec),
        ]

        for ax, line, data, _rate in zip(self.axes, self.lines, series, rates):
            if data.size == 0:
                continue
            x = np.linspace(-self.window_sec, 0.0, data.size, endpoint=False)
            line.set_data(x, data)
            ymin = float(np.min(data))
            ymax = float(np.max(data))
            if ymin == ymax:
                ymin -= 1.0
                ymax += 1.0
            ax.set_xlim(-self.window_sec, 0.0)
            ax.set_ylim(ymin, ymax)

        for artist in self.span_artists:
            artist.remove()
        self.span_artists = []

        for start_sec, end_sec in burst_ranges:
            for ax in self.axes:
                self.span_artists.append(ax.axvspan(start_sec, end_sec, color="#46a546", alpha=0.18))
                self.span_artists.append(ax.axvline(start_sec, color="#2f7f2f", alpha=0.45, lw=0.8))
                self.span_artists.append(ax.axvline(end_sec, color="#2f7f2f", alpha=0.45, lw=0.8))

        self.fig.tight_layout()
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        self.plt.pause(0.001)

    def close(self):
        self.plt.ioff()
        self.plt.close(self.fig)


def bursts_to_plot_ranges(samples_len: int, sample_rate: int, window_sec: float, bursts: list[Burst | FrameWindow]) -> list[tuple[float, float]]:
    ranges = []
    for burst in bursts:
        start_sec = (burst.start_sample - samples_len) / float(sample_rate)
        end_sec = (burst.end_sample - samples_len) / float(sample_rate)
        if end_sec < -window_sec or start_sec > 0.0:
            continue
        ranges.append((max(-window_sec, start_sec), min(0.0, end_sec)))
    return ranges


def compute_plot_series(samples: np.ndarray, sample_rate: int, window_sec: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if samples.size < 2:
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32), np.array([], dtype=np.float32)

    max_iq = int(sample_rate * window_sec)
    tail = samples[-max(2, max_iq):]
    rx_mag = np.abs(tail).astype(np.float32)

    discrim = np.angle(tail[1:] * np.conj(tail[:-1])).astype(np.float32)
    discrim -= float(np.mean(discrim))

    decim = max(1, sample_rate // (DEFAULT_SYMBOL_RATE * 10))
    usable = (discrim.size // decim) * decim
    if usable == 0:
        return rx_mag, discrim, np.array([], dtype=np.float32)
    decimated = discrim[:usable].reshape(-1, decim).mean(axis=1).astype(np.float32)
    return rx_mag, discrim, decimated


def build_rtl_sdr_command(args) -> list[str]:
    cmd = [
        args.rtl_bin,
        "-f",
        str(int(args.freq)),
        "-s",
        str(args.sample_rate),
        "-g",
        str(args.gain),
    ]
    if args.ppm:
        cmd.extend(["-p", str(args.ppm)])
    cmd.append("-")
    return cmd


def print_candidate_debug(candidates: list[FrameCandidate]) -> None:
    if not candidates:
        print("DEBUG: no frame candidates found", file=sys.stderr, flush=True)
        return

    for candidate in candidates:
        status = []
        if candidate.has_magic:
            status.append("magic")
        if candidate.crc_ok:
            status.append("crc_ok")
        status_text = ",".join(status) if status else "sync_only"
        crc_text = ""
        if candidate.crc_rx is not None and candidate.crc_calc is not None:
            crc_text = f" crc_rx=0x{candidate.crc_rx:04x} crc_calc=0x{candidate.crc_calc:04x}"
        print(
            f"DEBUG: frame_candidate burst={candidate.burst_index} "
            f"burst_start={candidate.burst_start_sample} burst_end={candidate.burst_end_sample} "
            f"freq_offset_hz={candidate.freq_offset_hz:+.0f} polarity={candidate.polarity} "
            f"bit_offset={candidate.bit_offset} byte_pos={candidate.byte_pos} "
            f"sync_bit_errors={candidate.sync_bit_errors} preamble_errors={candidate.preamble_errors} "
            f"status={status_text} payload_prefix={candidate.payload_prefix_hex}{crc_text}",
            file=sys.stderr,
            flush=True,
        )


def print_burst_debug(bursts: list[Burst], sample_rate: int, threshold: float) -> None:
    if not bursts:
        print(f"DEBUG: no bursts detected threshold={threshold:.3f}", file=sys.stderr, flush=True)
        return
    for burst in bursts:
        print(
            f"DEBUG: burst idx={burst.index} start={burst.start_sample / sample_rate:.6f}s "
            f"end={burst.end_sample / sample_rate:.6f}s dur_ms={(burst.end_sample - burst.start_sample) * 1000.0 / sample_rate:.1f} "
            f"peak_env={burst.peak_env:.3f} threshold={threshold:.3f}",
            file=sys.stderr,
            flush=True,
        )


def print_frame_window_debug(frame_windows: list[FrameWindow], sample_rate: int) -> None:
    for window in frame_windows:
        print(
            f"DEBUG: frame_window burst={window.burst_index} start={window.start_sample / sample_rate:.6f}s "
            f"end={window.end_sample / sample_rate:.6f}s dur_ms={(window.end_sample - window.start_sample) * 1000.0 / sample_rate:.1f} "
            f"plateau={window.plateau_level:.3f} th_on={window.threshold_on:.3f} th_off={window.threshold_off:.3f}",
            file=sys.stderr,
            flush=True,
        )


def print_scan_stats(target_sps_values: list[int], freq_offsets: list[float], stats_by_burst: dict[int, dict[tuple[int, float], tuple[int, int]]]) -> None:
    for burst_index, stats in sorted(stats_by_burst.items()):
        for target_sps in target_sps_values:
            for freq_offset_hz in freq_offsets:
                demod_bits, cand_count = stats.get((int(target_sps), float(freq_offset_hz)), (0, 0))
                print(
                    f"DEBUG: scan_offset burst={burst_index} target_sps={target_sps} freq_offset_hz={float(freq_offset_hz):+.0f} "
                    f"demod_bits={demod_bits} frame_candidates={cand_count}",
                    file=sys.stderr,
                    flush=True,
                )


def process_demodulated(args, samples: np.ndarray, sample_rate: int) -> tuple[list[Burst], list[FrameWindow], list[FrameCandidate], list[Packet], dict[int, dict[tuple[int, float], tuple[int, int]]], np.ndarray, float]:
    bursts, frame_windows, candidates, packets, stats, envelope, threshold = decode_detected_bursts(
        samples,
        sample_rate,
        args.symbol_rate,
        args.target_sps_values,
        args.freq_offsets,
        args.debug_candidates,
        args.sync_threshold,
        args.max_preamble_errors,
        burst_window_ms=args.burst_window_ms,
        burst_threshold_mad=args.burst_threshold_mad,
        burst_merge_gap_ms=args.burst_merge_gap_ms,
        burst_min_duration_ms=args.burst_min_duration_ms,
        burst_pad_ms=args.burst_pad_ms,
    )
    return bursts, frame_windows, candidates, packets, stats, envelope, threshold


def process_file(args, plotter: Plotter | None) -> int:
    input_format = detect_input_format(args.input_file, args.input_format)
    samples, detected_sample_rate = load_iq_file(args.input_file, input_format)
    sample_rate = detected_sample_rate or args.sample_rate

    print(
        f"Reading IQ file: {args.input_file} format={input_format} sample_rate={sample_rate} "
        f"symbol_rate={args.symbol_rate} demod_backend=gnuradio_gfsk target_sps_values={','.join(str(x) for x in args.target_sps_values)} "
        f"freq_offsets={','.join(f'{x:+.0f}' for x in args.freq_offsets)}",
        file=sys.stderr,
        flush=True,
    )
    print(
        f"Loaded iq_samples={samples.size} duration={samples.size / sample_rate:.3f}s",
        file=sys.stderr,
        flush=True,
    )

    bursts, frame_windows, candidates, packets, stats, _envelope, threshold = process_demodulated(args, samples, sample_rate)
    print_burst_debug(bursts, sample_rate, threshold)
    print_frame_window_debug(frame_windows, sample_rate)
    print_candidate_debug(candidates)
    print_scan_stats(args.target_sps_values, args.freq_offsets, stats)

    for packet in packets:
        print(format_packet(packet), flush=True)

    if plotter is not None:
        rx_mag, discrim, decimated = compute_plot_series(samples, sample_rate, args.plot_window_sec)
        burst_ranges = bursts_to_plot_ranges(samples.size, sample_rate, args.plot_window_sec, frame_windows)
        plotter.update(sample_rate, rx_mag, discrim, decimated, burst_ranges)
        while plotter.plt.fignum_exists(plotter.fig.number):
            plotter.update(sample_rate, rx_mag, discrim, decimated, burst_ranges)

    print(
        f"Done. bursts={len(bursts)} frame_windows={len(frame_windows)} packets={len(packets)} frame_candidates={len(candidates)}",
        file=sys.stderr,
        flush=True,
    )
    return 0 if packets else 1


def enhanced_packet_detection(samples: np.ndarray, sample_rate: int, symbol_rate: int) -> tuple[list[Burst], list[Packet]]:
    """Enhanced packet detection specifically for GFSK burst transmissions"""
    packets_detected = detect_gfsk_packets(samples, sample_rate, symbol_rate)

    bursts = []
    packets = []

    for i, (start_sample, confidence, freq_offset) in enumerate(packets_detected):
        # Estimate packet duration (preamble + sync + payload at 1200 bps)
        estimated_bits = PREAMBLE_LEN * 8 + 16 + PACKET_LEN * 8
        estimated_duration_samples = int(estimated_bits * sample_rate / symbol_rate)

        end_sample = min(samples.size, start_sample + estimated_duration_samples)

        # Create burst for this packet
        burst = Burst(
            index=i,
            start_sample=max(0, start_sample - 1000),  # Add some padding
            end_sample=min(samples.size, end_sample + 1000),
            peak_env=confidence
        )
        bursts.append(burst)

        # Try to decode this specific packet region
        packet_samples = samples[burst.start_sample:burst.end_sample]
        if packet_samples.size > 0:
            try:
                # Apply frequency correction
                corrected_samples = apply_frequency_offset(packet_samples, sample_rate, freq_offset)

                # Demodulate
                bits = gnuradio_gfsk_demod(corrected_samples, sample_rate, symbol_rate, 10)

                # Look for complete packet
                candidates, found_packets = find_frame_candidates(
                    bits, 5,
                    sync_threshold=2,
                    max_preamble_errors=80,
                    freq_offset_hz=freq_offset,
                    burst=burst
                )

                packets.extend(found_packets)

            except Exception as e:
                print(f"DEBUG: Packet decode error at sample {start_sample}: {e}", file=sys.stderr, flush=True)

    return bursts, packets


def process_live(args, plotter: Plotter | None) -> int:
    cmd = build_rtl_sdr_command(args)
    print(
        f"Starting live receiver: freq={args.freq/1e6:.3f} MHz sample_rate={args.sample_rate} "
        f"symbol_rate={args.symbol_rate} gain={args.gain} ppm={args.ppm} "
        f"demod_backend=gnuradio_gfsk target_sps_values={','.join(str(x) for x in args.target_sps_values)} "
        f"freq_offsets={','.join(f'{x:+.0f}' for x in args.freq_offsets)}",
        file=sys.stderr,
        flush=True,
    )
    print("Command:", " ".join(cmd), file=sys.stderr, flush=True)

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=None)
    except FileNotFoundError:
        print(f"rtl_sdr binary not found: {args.rtl_bin}", file=sys.stderr, flush=True)
        return 1

    if proc.stdout is None:
        print("rtl_sdr stdout pipe was not created", file=sys.stderr, flush=True)
        return 1

    total_iq_bytes = 0
    packet_count = 0
    start = time.monotonic()
    last_status = start
    iq_buffer = np.array([], dtype=np.complex64)
    max_iq = int(args.sample_rate * args.scan_window_sec)
    printed_candidate_keys: set[tuple[str, int, int]] = set()
    printed_packet_keys: set[tuple[str, str]] = set()

    def stop_handler(_signum, _frame):
        proc.terminate()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    try:
        while True:
            block = proc.stdout.read(args.block_bytes)
            if not block:
                break

            total_iq_bytes += len(block)
            iq_u8 = np.frombuffer(block, dtype=np.uint8)
            if iq_u8.size < 2 or iq_u8.size % 2 != 0:
                continue
            iq = iq_u8.astype(np.float32).reshape(-1, 2)
            samples = ((iq[:, 0] - 127.5) + 1j * (iq[:, 1] - 127.5)).astype(np.complex64)
            iq_buffer = np.concatenate([iq_buffer, samples])
            if iq_buffer.size > max_iq:
                iq_buffer = iq_buffer[-max_iq:]

            now = time.monotonic()
            if args.status_interval > 0 and (now - last_status) >= args.status_interval and iq_buffer.size > 0:
                if args.enhanced_detection:
                    # Use enhanced packet detection for GFSK bursts
                    enhanced_bursts, enhanced_packets = enhanced_packet_detection(iq_buffer, args.sample_rate, args.symbol_rate)

                    # Fallback to original detection if enhanced detection finds nothing
                    if not enhanced_packets:
                        bursts, frame_windows, candidates, packets, stats, _envelope, threshold = process_demodulated(args, iq_buffer, args.sample_rate)
                    else:
                        # Use enhanced detection results
                        bursts = enhanced_bursts
                        packets = enhanced_packets
                        frame_windows = []
                        candidates = []
                        stats = {}
                        threshold = 0.0
                else:
                    # Use original detection method
                    bursts, frame_windows, candidates, packets, stats, _envelope, threshold = process_demodulated(args, iq_buffer, args.sample_rate)

                new_candidates = []
                for candidate in candidates:
                    key = (candidate.burst_index, candidate.freq_offset_hz, candidate.polarity, candidate.bit_offset, candidate.byte_pos)
                    if key not in printed_candidate_keys:
                        printed_candidate_keys.add(key)
                        new_candidates.append(candidate)
                print_burst_debug(bursts, args.sample_rate, threshold)
                print_frame_window_debug(frame_windows, args.sample_rate)
                if new_candidates:
                    print_candidate_debug(new_candidates)
                print_scan_stats(args.target_sps_values, args.freq_offsets, stats)

                for packet in packets:
                    packet_key = packet.dedupe_key
                    if packet_key in printed_packet_keys:
                        continue
                    printed_packet_keys.add(packet_key)
                    packet_count += 1
                    print(format_packet(packet), flush=True)

                if plotter is not None:
                    rx_mag, discrim, decimated = compute_plot_series(iq_buffer, args.sample_rate, args.plot_window_sec)
                    burst_ranges = bursts_to_plot_ranges(iq_buffer.size, args.sample_rate, args.plot_window_sec, frame_windows)
                    plotter.update(args.sample_rate, rx_mag, discrim, decimated, burst_ranges)

                best = candidates[0] if candidates else None
                best_text = (
                    f"best_burst={best.burst_index} best_target_sps={best.target_sps} best_frame_freq_offset={best.freq_offset_hz:+.0f} best_frame_err={best.preamble_errors} "
                    f"best_frame_sync_err={best.sync_bit_errors} best_frame_magic={int(best.has_magic)} "
                    f"best_frame_crc={int(best.crc_ok)} best_frame_offset={best.bit_offset} "
                    f"best_frame_pos={best.byte_pos} best_frame_polarity={best.polarity}"
                    if best
                    else "best_frame=none"
                )
                demod_bits_total = sum(offset_stats[0] for burst_stats in stats.values() for offset_stats in burst_stats.values())
                print(
                    f"Listening... packets={packet_count} iq_mb={total_iq_bytes / 1_000_000:.1f} "
                    f"bursts={len(bursts)} frame_windows={len(frame_windows)} demod_bits={demod_bits_total} frame_candidates={len(candidates)} {best_text} "
                    f"elapsed={now - start:.1f}s",
                    file=sys.stderr,
                    flush=True,
                )
                last_status = now

        returncode = proc.poll()
        if returncode not in (0, None):
            print(f"rtl_sdr exited with code {returncode}", file=sys.stderr, flush=True)
            return returncode

        print(
            f"Receiver stopped. packets={packet_count} iq_mb={total_iq_bytes / 1_000_000:.1f}",
            file=sys.stderr,
            flush=True,
        )
        return 0 if packet_count else 1
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def main() -> int:
    def parse_freq_offsets(value: str) -> list[float]:
        items = []
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            items.append(float(part))
        return items or [0.0]

    def parse_int_list(value: str) -> list[int]:
        items = []
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            items.append(int(part))
        return items or [10]

    parser = argparse.ArgumentParser(description="Receive SI4032 AX.25/APRS telemetry using GNU Radio burst demodulation")
    parser.add_argument("--freq", type=float, default=433.920e6)
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--symbol-rate", type=int, default=DEFAULT_SYMBOL_RATE)
    parser.add_argument("--gain", type=float, default=35.0)
    parser.add_argument("--ppm", type=int, default=0)
    parser.add_argument("--rtl-bin", default="rtl_sdr")
    parser.add_argument("--input-file")
    parser.add_argument("--input-format", choices=["auto", "rtl_u8", "wav_iq"], default="auto")
    parser.add_argument("--block-bytes", type=int, default=262144)
    parser.add_argument("--status-interval", type=float, default=2.0)
    parser.add_argument("--target-sps", type=int, default=10)
    parser.add_argument("--target-sps-list", type=parse_int_list)
    parser.add_argument("--scan-window-sec", type=float, default=2.5)
    parser.add_argument("--debug-candidates", type=int, default=12)
    parser.add_argument("--sync-threshold", type=int, default=2)
    parser.add_argument("--max-preamble-errors", type=int, default=80)
    parser.add_argument("--freq-offsets", type=parse_freq_offsets, default=[-15000.0, -10000.0, -5000.0, -2500.0, 0.0, 2500.0, 5000.0, 10000.0, 15000.0])
    parser.add_argument("--burst-window-ms", type=float, default=5.0)
    parser.add_argument("--burst-threshold-mad", type=float, default=3.0)
    parser.add_argument("--burst-merge-gap-ms", type=float, default=10.0)
    parser.add_argument("--burst-min-duration-ms", type=float, default=200.0)
    parser.add_argument("--burst-pad-ms", type=float, default=50.0)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--plot-window-sec", type=float, default=10.0)
    parser.add_argument("--enhanced-detection", action="store_true", help="Use enhanced GFSK packet detection (recommended for burst transmissions)")
    args = parser.parse_args()
    args.target_sps_values = args.target_sps_list if args.target_sps_list else [args.target_sps]

    plotter = Plotter(args.plot_window_sec) if args.plot else None
    try:
        if args.input_file:
            return process_file(args, plotter)
        return process_live(args, plotter)
    finally:
        if plotter is not None:
            plotter.close()


if __name__ == "__main__":
    sys.exit(main())
