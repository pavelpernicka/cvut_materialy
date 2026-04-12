#!/usr/bin/env python3

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


BITRATE = 1200
PACKET_LEN = 32
PACKET_FORMAT = "<2sBBHIiiiHHhBBH"
PREAMBLE_BYTES = 16
PREAMBLE_BITS = np.array([1, 0] * (PREAMBLE_BYTES * 4), dtype=np.uint8)
PREAMBLE_BITS_INV = np.array([0, 1] * (PREAMBLE_BYTES * 4), dtype=np.uint8)
SYNC_BITS = np.unpackbits(np.frombuffer(b"\x2d\xd4", dtype=np.uint8), bitorder="big")
MAGIC_BITS = np.unpackbits(np.frombuffer(b"RS", dtype=np.uint8), bitorder="big")
PAYLOAD_BITS = PACKET_LEN * 8
FRAME_BITS = PREAMBLE_BITS.size + SYNC_BITS.size + PAYLOAD_BITS
ANALYSIS_MARGIN_MS = 30.0
MAX_PREAMBLE_START_SYMBOLS = 192
MAX_CANDIDATES_PER_OFFSET = 4
COARSE_PHASE_TRIALS = 4
MIN_CAPTURED_PREAMBLE_BITS = 8
SYNC_SYMBOLS = (SYNC_BITS.astype(np.float32) * 2.0) - 1.0
PREAMBLE_SYMBOLS = (PREAMBLE_BITS.astype(np.float32) * 2.0) - 1.0
MAGIC_SYMBOLS = (MAGIC_BITS.astype(np.float32) * 2.0) - 1.0
HEADER_SYMBOLS = np.concatenate((SYNC_SYMBOLS, MAGIC_SYMBOLS)).astype(np.float32)
COARSE_PREAMBLE_BYTES = (8, 12, 16)


@dataclass(frozen=True)
class Burst:
    index: int
    start_sample: int
    end_sample: int
    peak_env: float


@dataclass(frozen=True)
class Packet:
    sequence: int
    flags: int
    uptime_ms: int
    latitude_e7: int
    longitude_e7: int
    altitude_cm: int
    speed_cms: int
    battery_mv: int
    mcu_temp_centi: int
    satellites: int


@dataclass(frozen=True)
class DecodeCandidate:
    burst_index: int
    freq_offset_hz: float
    target_sps: int
    timing_sps: float
    timing_phase: float
    polarity: str
    sample_offset: int
    demod_start_sample: float
    demod_end_sample: float
    start_sample: int
    end_sample: int
    start_symbol: int
    end_symbol: int
    preamble_errors: int
    sync_errors: int
    preamble_strength: float
    first_byte_errors: int
    has_magic: bool
    score: int
    frame_hex: str
    frame_bin: str
    payload_hex: str
    payload_prefix_hex: str
    payload: bytes
    packet: Packet | None


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def parse_packet(raw: bytes) -> Packet | None:
    if len(raw) != PACKET_LEN or raw[:2] != b"RS":
        return None
    unpacked = struct.unpack(PACKET_FORMAT, raw)
    if unpacked[-1] != crc16_ccitt_false(raw[:-2]):
        return None
    return Packet(
        sequence=unpacked[3],
        flags=unpacked[2],
        uptime_ms=unpacked[4],
        latitude_e7=unpacked[5],
        longitude_e7=unpacked[6],
        altitude_cm=unpacked[7],
        speed_cms=unpacked[8],
        battery_mv=unpacked[9],
        mcu_temp_centi=unpacked[10],
        satellites=unpacked[11],
    )


def format_packet(packet: Packet) -> str:
    gps_valid = 1 if packet.flags & 0x01 else 0
    return (
        f"seq={packet.sequence} gps={gps_valid} sats={packet.satellites} "
        f"lat={packet.latitude_e7 / 1e7:.7f} lon={packet.longitude_e7 / 1e7:.7f} "
        f"alt={packet.altitude_cm / 100.0:.2f}m speed={packet.speed_cms / 100.0:.2f}m/s "
        f"batt={packet.battery_mv}mV temp={packet.mcu_temp_centi / 100.0:.2f}C "
        f"uptime={packet.uptime_ms}ms"
    )


def moving_average(data: np.ndarray, window: int) -> np.ndarray:
    window = max(1, int(window))
    if window == 1:
        return data.astype(np.float32, copy=False)
    padded = np.pad(data.astype(np.float32), (window // 2, window - 1 - window // 2), mode="edge")
    csum = np.cumsum(padded, dtype=np.float64)
    csum[window:] = csum[window:] - csum[:-window]
    return (csum[window - 1:] / float(window)).astype(np.float32)


def fir_lowpass(data: np.ndarray, sample_rate: int, cutoff_hz: float, taps: int = 129) -> np.ndarray:
    taps = max(17, int(taps) | 1)
    n = np.arange(taps, dtype=np.float64) - (taps - 1) / 2.0
    h = 2.0 * cutoff_hz / sample_rate * np.sinc(2.0 * cutoff_hz * n / sample_rate)
    h *= np.hamming(taps)
    h /= np.sum(h)
    return np.convolve(data, h.astype(np.float32), mode="same").astype(np.float32)


def resample_linear(data: np.ndarray, input_rate: int, output_rate: int) -> np.ndarray:
    if len(data) < 2 or input_rate == output_rate:
        return data.astype(np.float32, copy=False)
    duration = (len(data) - 1) / float(input_rate)
    count = max(2, int(duration * output_rate) + 1)
    src_x = np.arange(len(data), dtype=np.float64) / float(input_rate)
    dst_x = np.arange(count, dtype=np.float64) / float(output_rate)
    return np.interp(dst_x, src_x, data).astype(np.float32)


def load_cu8(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size < 2 or raw.size % 2 != 0:
        raise ValueError("input file does not contain valid rtl_sdr cu8 IQ data")
    iq = raw.astype(np.float32).reshape(-1, 2)
    return ((iq[:, 0] - 127.5) + 1j * (iq[:, 1] - 127.5)).astype(np.complex64)


def estimate_peak_offset(samples: np.ndarray, sample_rate: int) -> float:
    if samples.size < 64:
        return 0.0
    windowed = samples * np.hanning(samples.size).astype(np.float32)
    spectrum = np.fft.fftshift(np.fft.fft(windowed))
    freqs = np.fft.fftshift(np.fft.fftfreq(samples.size, d=1.0 / sample_rate))
    return float(freqs[int(np.argmax(np.abs(spectrum)))])


def detect_bursts(
    samples: np.ndarray,
    sample_rate: int,
    threshold_mad: float,
    min_duration_ms: float,
    env_window_ms: float,
    merge_gap_ms: float,
    pad_ms: float,
) -> tuple[list[Burst], np.ndarray, np.ndarray, float]:
    power = (np.abs(samples).astype(np.float32) ** 2)
    power_env = moving_average(power, int(sample_rate * env_window_ms / 1000.0))

    discrim = np.angle(samples[1:] * np.conj(samples[:-1])).astype(np.float32)
    discrim_abs = np.abs(discrim)
    discrim_env = moving_average(discrim_abs, int(sample_rate * env_window_ms / 1000.0))
    discrim_env = np.concatenate(([discrim_env[0]], discrim_env))

    median = float(np.median(power_env))
    mad = float(np.median(np.abs(power_env - median)))
    mad = max(mad, 1e-6)
    threshold = median + threshold_mad * mad

    active = power_env > threshold
    active_idx = np.flatnonzero(active)
    if active_idx.size == 0:
        return [], power_env, discrim_env, threshold

    min_duration = max(1, int(sample_rate * min_duration_ms / 1000.0))
    merge_gap = max(1, int(sample_rate * merge_gap_ms / 1000.0))
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
            bursts.append(Burst(burst_index, seg_start, seg_end, float(np.max(power_env[seg_start:seg_end]))))
            burst_index += 1
        start = prev = idx

    seg_start = max(0, start - pad)
    seg_end = min(samples.size, prev + 1 + pad)
    if seg_end - seg_start >= min_duration:
        bursts.append(Burst(burst_index, seg_start, seg_end, float(np.max(power_env[seg_start:seg_end]))))

    return bursts, power_env, discrim_env, threshold


def demodulate_burst(samples: np.ndarray, sample_rate: int, target_sps: int, offset_hz: float) -> np.ndarray:
    n = np.arange(samples.size, dtype=np.float32)
    shifted = samples * np.exp(-1j * 2.0 * np.pi * offset_hz * n / float(sample_rate)).astype(np.complex64)
    filtered_i = fir_lowpass(shifted.real.astype(np.float32), sample_rate, 12_000.0)
    filtered_q = fir_lowpass(shifted.imag.astype(np.float32), sample_rate, 12_000.0)
    filtered = filtered_i + 1j * filtered_q
    discrim = np.angle(filtered[1:] * np.conj(filtered[:-1])).astype(np.float32)
    discrim_hz = discrim * (sample_rate / (2.0 * np.pi))
    discrim_hz -= float(np.mean(discrim_hz))
    demod = fir_lowpass(discrim_hz, sample_rate, 2_500.0)
    target_rate = BITRATE * target_sps
    return resample_linear(demod, sample_rate, target_rate)


def symbol_values_from_start(demod_samples: np.ndarray, target_sps: int, start_sample: int, symbol_count: int) -> np.ndarray:
    if symbol_count <= 0:
        return np.empty(0, dtype=np.float32)

    last_needed = start_sample + symbol_count * target_sps
    if last_needed > demod_samples.size:
        symbol_count = max(0, (demod_samples.size - start_sample) // target_sps)
    if symbol_count <= 0:
        return np.empty(0, dtype=np.float32)

    left = max(0, target_sps // 4)
    right = max(left + 1, (3 * target_sps) // 4)
    values = np.empty(symbol_count, dtype=np.float32)

    for idx in range(symbol_count):
        start = start_sample + idx * target_sps + left
        end = min(demod_samples.size, start_sample + idx * target_sps + right)
        if end <= start:
            start = start_sample + idx * target_sps
            end = min(demod_samples.size, start + target_sps)
        values[idx] = float(np.mean(demod_samples[start:end]))

    return values


def bits_to_hex_and_bin(frame_bits: np.ndarray) -> tuple[str, str]:
    packed = np.packbits(frame_bits.astype(np.uint8), bitorder="big").tobytes()
    return packed.hex(), "".join("1" if bit else "0" for bit in frame_bits)


def bytes_to_bit_string(data: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in data)


def decode_payload_fields(payload: bytes) -> list[str]:
    if len(payload) != PACKET_LEN:
        return [f"payload bits 0..{len(payload) * 8 - 1}: invalid length={len(payload)}B"]

    version = payload[2]
    flags = payload[3]
    sequence = int.from_bytes(payload[4:6], "little")
    uptime_ms = int.from_bytes(payload[6:10], "little")
    latitude_e7 = int.from_bytes(payload[10:14], "little", signed=True)
    longitude_e7 = int.from_bytes(payload[14:18], "little", signed=True)
    altitude_cm = int.from_bytes(payload[18:22], "little", signed=True)
    speed_cms = int.from_bytes(payload[22:24], "little")
    battery_mv = int.from_bytes(payload[24:26], "little")
    mcu_temp_centi = int.from_bytes(payload[26:28], "little", signed=True)
    satellites = payload[28]
    reserved = payload[29]
    crc_rx = int.from_bytes(payload[30:32], "little")
    crc_calc = crc16_ccitt_false(payload[:-2])

    fields = [
        ("magic", 0, 15, payload[0:2].hex(), f"ascii={payload[0:2]!r}"),
        ("version", 16, 23, f"0x{version:02x}", str(version)),
        ("flags", 24, 31, f"0x{flags:02x}", f"gps_valid={int(bool(flags & 0x01))}"),
        ("sequence", 32, 47, f"0x{sequence:04x}", str(sequence)),
        ("uptime_ms", 48, 79, f"0x{uptime_ms:08x}", str(uptime_ms)),
        ("latitude_e7", 80, 111, f"0x{latitude_e7 & 0xffffffff:08x}", f"{latitude_e7} ({latitude_e7 / 1e7:.7f})"),
        ("longitude_e7", 112, 143, f"0x{longitude_e7 & 0xffffffff:08x}", f"{longitude_e7} ({longitude_e7 / 1e7:.7f})"),
        ("altitude_cm", 144, 175, f"0x{altitude_cm & 0xffffffff:08x}", f"{altitude_cm} ({altitude_cm / 100.0:.2f}m)"),
        ("speed_cms", 176, 191, f"0x{speed_cms:04x}", f"{speed_cms} ({speed_cms / 100.0:.2f}m/s)"),
        ("battery_mv", 192, 207, f"0x{battery_mv:04x}", f"{battery_mv}mV"),
        ("mcu_temp_centi", 208, 223, f"0x{mcu_temp_centi & 0xffff:04x}", f"{mcu_temp_centi} ({mcu_temp_centi / 100.0:.2f}C)"),
        ("satellites", 224, 231, f"0x{satellites:02x}", str(satellites)),
        ("reserved", 232, 239, f"0x{reserved:02x}", str(reserved)),
        ("crc16", 240, 255, f"0x{crc_rx:04x}", f"calc=0x{crc_calc:04x} match={int(crc_rx == crc_calc)}"),
    ]

    return [f"{name} bits {start:3d}..{end:3d}: {raw} -> {decoded}" for name, start, end, raw, decoded in fields]


def symbol_values_from_demod(demod_samples: np.ndarray, target_sps: int, offset: int) -> np.ndarray:
    symbol_count = (demod_samples.size - offset) // target_sps
    if symbol_count <= 0:
        return np.empty(0, dtype=np.float32)

    return symbol_values_from_start(demod_samples, target_sps, offset, symbol_count)


def matched_filter_demod(demod_samples: np.ndarray, sps: float) -> np.ndarray:
    taps = max(3, int(round(sps)))
    kernel = np.ones(taps, dtype=np.float32) / float(taps)
    return np.convolve(demod_samples.astype(np.float32), kernel, mode="same").astype(np.float32)


def build_header_bits(preamble_bytes: int) -> np.ndarray:
    return np.concatenate((np.tile(np.array([1, 0], dtype=np.uint8), preamble_bytes * 4), SYNC_BITS, MAGIC_BITS))


def build_header_template(sps: float, preamble_bytes: int) -> tuple[np.ndarray, int]:
    header_bits = build_header_bits(preamble_bytes)
    length = max(1, int(round(header_bits.size * sps)))
    positions = np.arange(length, dtype=np.float64) / float(sps)
    symbol_idx = np.clip(positions.astype(np.int32), 0, header_bits.size - 1)
    template = ((header_bits[symbol_idx].astype(np.float32) * 2.0) - 1.0).astype(np.float32)
    norm = float(np.linalg.norm(template))
    if norm > 0.0:
        template /= norm
    return template, preamble_bytes * 8


def coarse_header_seeds(
    demod_samples: np.ndarray,
    burst_index: int,
    freq_offset_hz: float,
    target_sps: int,
) -> list[DecodeCandidate]:
    coarse_candidates: list[DecodeCandidate] = []
    coarse_sps_trials = [float(target_sps) + delta for delta in (-0.5, 0.0, 0.5)]

    for trial_sps in coarse_sps_trials:
        if trial_sps < 2.0:
            continue
        matched = matched_filter_demod(demod_samples, trial_sps)

        for preamble_bytes in COARSE_PREAMBLE_BYTES:
            template, preamble_bits = build_header_template(trial_sps, preamble_bytes)
            if matched.size < template.size + PAYLOAD_BITS:
                continue
            corr = np.correlate(matched.astype(np.float32), template, mode="valid").astype(np.float32)
            if corr.size == 0:
                continue

            top_n = min(MAX_CANDIDATES_PER_OFFSET * 3, corr.size)
            top_idx = np.argpartition(np.abs(corr), -top_n)[-top_n:]
            top_idx = top_idx[np.argsort(np.abs(corr[top_idx]))[::-1]]

            for start_idx in top_idx.tolist():
                start_idx = int(start_idx)
                total_frame_samples = int(round((preamble_bytes * 8 + SYNC_BITS.size + PAYLOAD_BITS) * trial_sps))
                if start_idx + total_frame_samples > matched.size:
                    continue
                polarity_name = "normal" if corr[start_idx] >= 0.0 else "inverted"
                phase = float(start_idx % trial_sps)
                coarse_candidates.append(
                    DecodeCandidate(
                        burst_index=burst_index,
                        freq_offset_hz=float(freq_offset_hz),
                        target_sps=target_sps,
                        timing_sps=float(trial_sps),
                        timing_phase=phase,
                        polarity=polarity_name,
                        sample_offset=int(round(phase)),
                        demod_start_sample=float(start_idx),
                        demod_end_sample=float(start_idx + template.size),
                        start_sample=0,
                        end_sample=0,
                        start_symbol=0,
                        end_symbol=0,
                        preamble_errors=0,
                        sync_errors=0,
                        preamble_strength=float(abs(corr[start_idx])),
                        first_byte_errors=0,
                        has_magic=False,
                        score=-int(round(abs(corr[start_idx]) * 1000.0)) - preamble_bits + start_idx,
                        frame_hex="",
                        frame_bin="",
                        payload_hex="",
                        payload_prefix_hex="",
                        payload=b"",
                        packet=None,
                    )
                )

    coarse_candidates.sort(key=lambda item: (item.score, abs(item.freq_offset_hz), item.timing_sps, item.timing_phase))
    return coarse_candidates[:8]


def hard_slice(values: np.ndarray) -> np.ndarray:
    return (values > 0.0).astype(np.uint8)


def soft_correlate(stream: np.ndarray, pattern: np.ndarray) -> np.ndarray:
    if stream.size < pattern.size:
        return np.empty(0, dtype=np.float32)
    return np.correlate(stream.astype(np.float32), pattern.astype(np.float32), mode="valid").astype(np.float32)


def choose_preamble_start_soft(symbols: np.ndarray, sync_pos: int) -> tuple[int, int, int, float, int] | None:
    if sync_pos < 8:
        return None

    best: tuple[int, float, int, int, int, int] | None = None
    search_start = max(0, sync_pos - PREAMBLE_BITS.size)

    for start in range(search_start, sync_pos - 7, 8):
        captured_len = sync_pos - start
        if captured_len < MIN_CAPTURED_PREAMBLE_BITS:
            continue
        if captured_len % 8 != 0:
            continue

        segment = symbols[start:sync_pos]
        expected_symbols = PREAMBLE_SYMBOLS[:captured_len]
        first_byte_soft = float(np.dot(segment[:8], PREAMBLE_SYMBOLS[:8]))
        preamble_soft = float(np.dot(segment, expected_symbols)) / float(captured_len)
        hard_bits = hard_slice(segment)
        first_byte_errors = bit_errors(hard_bits[:8], PREAMBLE_BITS[:8])
        preamble_errors = bit_errors(hard_bits, PREAMBLE_BITS[:captured_len])
        key = (first_byte_errors, -first_byte_soft, -preamble_soft, preamble_errors, -captured_len, start)
        if best is None or key < best:
            best = key

    if best is None:
        return None

    first_byte_errors, neg_first_soft, neg_preamble_soft, preamble_errors, neg_captured_len, start = best
    return start, preamble_errors, -neg_captured_len, -neg_preamble_soft, first_byte_errors


def candidate_sort_key(item: DecodeCandidate) -> tuple[int, int, int, int, int, float]:
    return (
        0 if item.packet is not None else 1,
        item.first_byte_errors,
        0 if item.has_magic else 1,
        item.score,
        item.preamble_errors,
        abs(item.freq_offset_hz),
    )


def build_decoded_candidate(
    demod_samples: np.ndarray,
    burst_index: int,
    freq_offset_hz: float,
    target_sps: int,
    trial_sps: float,
    header_start_sample: float,
    preamble_bytes: int,
    polarity_name: str,
    max_sync_errors: int,
    max_preamble_errors: int,
) -> DecodeCandidate | None:
    preamble_bits_len = preamble_bytes * 8
    symbol_count = preamble_bits_len + SYNC_BITS.size + PAYLOAD_BITS
    frame_symbols = sample_symbols_float(demod_samples, header_start_sample, trial_sps, symbol_count)
    if frame_symbols.size != symbol_count:
        return None

    if polarity_name == "inverted":
        frame_symbols = -frame_symbols

    frame_bits = hard_slice(frame_symbols)
    preamble_bits = frame_bits[:preamble_bits_len]
    expected_preamble = PREAMBLE_BITS[:preamble_bits_len]
    preamble_errors = bit_errors(preamble_bits, expected_preamble)

    sync_offset = preamble_bits_len
    sync_bits = frame_bits[sync_offset:sync_offset + SYNC_BITS.size]
    sync_errors = bit_errors(sync_bits, SYNC_BITS)

    payload_bits = frame_bits[sync_offset + SYNC_BITS.size:]
    payload = np.packbits(payload_bits, bitorder="big").tobytes()
    magic_errors = bit_errors(payload_bits[:MAGIC_BITS.size], MAGIC_BITS)
    has_magic = payload[:2] == b"RS"
    packet = parse_packet(payload)
    frame_hex, frame_bin = bits_to_hex_and_bin(frame_bits)
    preamble_soft = float(np.dot(frame_symbols[:preamble_bits_len], PREAMBLE_SYMBOLS[:preamble_bits_len])) / float(max(1, preamble_bits_len))
    sync_soft = float(np.dot(frame_symbols[sync_offset:sync_offset + SYNC_BITS.size], SYNC_SYMBOLS)) / float(SYNC_BITS.size)
    magic_soft = float(np.dot(frame_symbols[sync_offset + SYNC_BITS.size:sync_offset + SYNC_BITS.size + MAGIC_BITS.size], MAGIC_SYMBOLS)) / float(MAGIC_BITS.size)
    first_byte_errors = bit_errors(frame_bits[:8], PREAMBLE_BITS[:8])

    score = (
        (0 if packet is not None else 50_000)
        + first_byte_errors * 20_000
        + sync_errors * 3_000
        + magic_errors * 1_000
        + preamble_errors * 200
        - int(round(preamble_soft * 150.0))
        - int(round(sync_soft * 450.0))
        - int(round(magic_soft * 700.0))
        - preamble_bits_len * 4
    )

    return DecodeCandidate(
        burst_index=burst_index,
        freq_offset_hz=float(freq_offset_hz),
        target_sps=target_sps,
        timing_sps=float(trial_sps),
        timing_phase=float(header_start_sample % max(1.0, trial_sps)),
        polarity=polarity_name,
        sample_offset=int(round(header_start_sample % max(1.0, trial_sps))),
        demod_start_sample=float(header_start_sample),
        demod_end_sample=float(header_start_sample + symbol_count * trial_sps),
        start_sample=0,
        end_sample=0,
        start_symbol=0,
        end_symbol=symbol_count,
        preamble_errors=preamble_errors,
        sync_errors=sync_errors,
        preamble_strength=preamble_soft,
        first_byte_errors=first_byte_errors,
        has_magic=has_magic,
        score=score,
        frame_hex=frame_hex,
        frame_bin=frame_bin,
        payload_hex=payload.hex(),
        payload_prefix_hex=payload[:12].hex(),
        payload=payload,
        packet=packet,
    )


def refine_seed_candidate(
    demod_samples: np.ndarray,
    seed: DecodeCandidate,
    burst_index: int,
    freq_offset_hz: float,
    target_sps: int,
    max_sync_errors: int,
    max_preamble_errors: int,
) -> list[DecodeCandidate]:
    candidates: list[DecodeCandidate] = []
    fine_sps_trials = np.arange(seed.timing_sps - 0.25, seed.timing_sps + 0.2501, 0.03125, dtype=np.float64)

    for trial_sps in fine_sps_trials.tolist():
        if trial_sps < 2.0:
            continue
        matched = matched_filter_demod(demod_samples, trial_sps)
        lo = max(0, int(round(seed.demod_start_sample - 2.0 * trial_sps)))
        hi = min(matched.size - 1, int(round(seed.demod_start_sample + 2.0 * trial_sps)) + 1)
        if hi <= lo:
            continue

        for preamble_bytes in COARSE_PREAMBLE_BYTES:
            for header_start_sample in range(lo, hi):
                for polarity_name in ("normal", "inverted"):
                    candidate = build_decoded_candidate(
                        matched,
                        burst_index,
                        freq_offset_hz,
                        target_sps,
                        trial_sps,
                        float(header_start_sample),
                        preamble_bytes,
                        polarity_name,
                        max_sync_errors,
                        max_preamble_errors,
                    )
                    if candidate is not None:
                        candidates.append(candidate)

    candidates.sort(key=candidate_sort_key)
    return candidates[:8]


def extract_candidates_from_soft_stream(
    soft_stream: np.ndarray,
    burst_index: int,
    freq_offset_hz: float,
    target_sps: int,
    trial_sps: float,
    phase: float,
    polarity_name: str,
    max_sync_errors: int,
    max_preamble_errors: int,
    top_n: int,
) -> list[DecodeCandidate]:
    if soft_stream.size < SYNC_BITS.size + MAGIC_BITS.size + PAYLOAD_BITS + 8:
        return []

    header_corr = soft_correlate(soft_stream, HEADER_SYMBOLS)
    if header_corr.size == 0:
        return []

    top_n = min(max(1, top_n), header_corr.size)
    top_idx = np.argpartition(header_corr, -top_n)[-top_n:]
    top_idx = top_idx[np.argsort(header_corr[top_idx])[::-1]]

    candidates: list[DecodeCandidate] = []
    for sync_start in top_idx.tolist():
        sync_start = int(sync_start)
        frame_end = sync_start + SYNC_BITS.size + PAYLOAD_BITS
        if frame_end > soft_stream.size:
            continue

        preamble_choice = choose_preamble_start_soft(soft_stream, sync_start)
        if preamble_choice is None:
            continue

        frame_start, preamble_errors, captured_preamble_bits, preamble_soft, first_byte_errors = preamble_choice
        if preamble_errors > max(max_preamble_errors, PREAMBLE_BITS.size):
            continue

        frame_symbols = soft_stream[frame_start:frame_end]
        frame_bits = hard_slice(frame_symbols)
        sync_offset = sync_start - frame_start
        sync_bits = frame_bits[sync_offset:sync_offset + SYNC_BITS.size]
        sync_errors = bit_errors(sync_bits, SYNC_BITS)
        if sync_errors > max_sync_errors:
            continue

        payload_bits = frame_bits[sync_offset + SYNC_BITS.size:]
        payload = np.packbits(payload_bits, bitorder="big").tobytes()
        magic_errors = bit_errors(payload_bits[:MAGIC_BITS.size], MAGIC_BITS)
        sync_soft = float(np.dot(soft_stream[sync_start:sync_start + SYNC_BITS.size], SYNC_SYMBOLS)) / float(SYNC_BITS.size)
        magic_soft = float(np.dot(soft_stream[sync_start + SYNC_BITS.size:sync_start + SYNC_BITS.size + MAGIC_BITS.size], MAGIC_SYMBOLS)) / float(MAGIC_BITS.size)
        header_soft = float(np.dot(soft_stream[sync_start:sync_start + HEADER_SYMBOLS.size], HEADER_SYMBOLS)) / float(HEADER_SYMBOLS.size)
        has_magic = payload[:2] == b"RS"
        packet = parse_packet(payload)
        frame_hex, frame_bin = bits_to_hex_and_bin(frame_bits)

        score = (
            (0 if packet is not None else 50_000)
            + first_byte_errors * 20_000
            + sync_errors * 3_000
            + magic_errors * 1_000
            + preamble_errors * 200
            - int(round(preamble_soft * 120.0))
            - int(round(sync_soft * 300.0))
            - int(round(magic_soft * 450.0))
            - int(round(header_soft * 700.0))
            - captured_preamble_bits * 4
        )

        candidates.append(
            DecodeCandidate(
                burst_index=burst_index,
                freq_offset_hz=float(freq_offset_hz),
                target_sps=target_sps,
                timing_sps=float(trial_sps),
                timing_phase=float(phase),
                polarity=polarity_name,
                sample_offset=int(round(phase)),
                demod_start_sample=float(phase + frame_start * trial_sps),
                demod_end_sample=float(phase + frame_end * trial_sps),
                start_sample=0,
                end_sample=0,
                start_symbol=frame_start,
                end_symbol=frame_end,
                preamble_errors=preamble_errors,
                sync_errors=sync_errors,
                preamble_strength=preamble_soft,
                first_byte_errors=first_byte_errors,
                has_magic=has_magic,
                score=score,
                frame_hex=frame_hex,
                frame_bin=frame_bin,
                payload_hex=payload.hex(),
                payload_prefix_hex=payload[:12].hex(),
                payload=payload,
                packet=packet,
            )
        )

    candidates.sort(key=candidate_sort_key)
    return candidates[:top_n]


def bit_errors(lhs: np.ndarray, rhs: np.ndarray) -> int:
    return int(np.count_nonzero(lhs.astype(np.uint8) ^ rhs.astype(np.uint8)))


def preamble_window_errors(bits: np.ndarray) -> tuple[int, int]:
    ref_a = PREAMBLE_BITS
    ref_b = PREAMBLE_BITS_INV
    errors_a = bit_errors(bits, ref_a)
    errors_b = bit_errors(bits, ref_b)
    if errors_a <= errors_b:
        return errors_a, 0
    return errors_b, 1


def choose_preamble_start(bits: np.ndarray, sync_pos: int) -> tuple[int, int, int] | None:
    if sync_pos < 8:
        return None

    best: tuple[int, int, int, int] | None = None
    search_start = max(0, sync_pos - PREAMBLE_BITS.size)

    for start in range(search_start, sync_pos - 7):
        captured_len = sync_pos - start
        if captured_len < MIN_CAPTURED_PREAMBLE_BITS:
            continue
        if captured_len % 8 != 0:
            continue

        first_byte = bits[start:start + 8]
        first_byte_errors = bit_errors(first_byte, PREAMBLE_BITS[:8])
        expected = np.resize(PREAMBLE_BITS, captured_len)
        preamble_errors = bit_errors(bits[start:sync_pos], expected)
        preamble_error_rate = (preamble_errors * 1000) // captured_len
        key = (first_byte_errors, preamble_error_rate, preamble_errors, -captured_len, start)
        if best is None or key < best:
            best = key

    if best is None:
        return None

    first_byte_errors, _preamble_error_rate, preamble_errors, neg_len, start = best
    return start, preamble_errors, -neg_len


def snap_to_first_preamble_byte(bits: np.ndarray, frame_start: int, sync_pos: int) -> tuple[int, int, int]:
    best: tuple[int, int, int, int] | None = None
    exact_match_start: int | None = None

    for start in range(frame_start, sync_pos - 7, 8):
        captured_len = sync_pos - start
        if captured_len < 8:
            continue
        first_byte_errors = bit_errors(bits[start:start + 8], PREAMBLE_BITS[:8])
        expected = np.resize(PREAMBLE_BITS, captured_len)
        preamble_errors = bit_errors(bits[start:sync_pos], expected)
        if first_byte_errors == 0 and exact_match_start is None:
            exact_match_start = start
        key = (first_byte_errors, preamble_errors, -captured_len, start)
        if best is None or key < best:
            best = key

    if exact_match_start is not None:
        captured_len = sync_pos - exact_match_start
        expected = np.resize(PREAMBLE_BITS, captured_len)
        preamble_errors = bit_errors(bits[exact_match_start:sync_pos], expected)
        return exact_match_start, preamble_errors, captured_len

    if best is None:
        captured_len = sync_pos - frame_start
        expected = np.resize(PREAMBLE_BITS, captured_len)
        preamble_errors = bit_errors(bits[frame_start:sync_pos], expected)
        return frame_start, preamble_errors, captured_len

    _first_byte_errors, preamble_errors, neg_len, start = best
    return start, preamble_errors, -neg_len


def search_aligned_frame(
    stream: np.ndarray,
    burst_index: int,
    freq_offset_hz: float,
    target_sps: int,
    sample_offset: int,
    polarity: str,
    max_sync_errors: int,
    max_preamble_errors: int,
) -> DecodeCandidate | None:
    needed_after_sync = SYNC_BITS.size + PAYLOAD_BITS
    if stream.size < needed_after_sync + 8:
        return None

    best_candidate: DecodeCandidate | None = None
    last_sync_start = stream.size - needed_after_sync

    for sync_start in range(0, last_sync_start + 1):
        sync_errors = bit_errors(stream[sync_start:sync_start + SYNC_BITS.size], SYNC_BITS)
        if sync_errors > max_sync_errors:
            continue

        preamble_choice = choose_preamble_start(stream, sync_start)
        if preamble_choice is None:
            continue
        frame_start, preamble_errors, captured_preamble_bits = preamble_choice
        frame_start, preamble_errors, captured_preamble_bits = snap_to_first_preamble_byte(stream, frame_start, sync_start)

        frame_end = sync_start + SYNC_BITS.size + PAYLOAD_BITS
        frame_bits = stream[frame_start:frame_end]
        payload_bits = stream[sync_start + SYNC_BITS.size:frame_end]
        payload = np.packbits(payload_bits, bitorder="big").tobytes()
        magic_errors = bit_errors(payload_bits[:MAGIC_BITS.size], MAGIC_BITS)
        preamble_like_errors = min(
            bit_errors(payload_bits[:16], PREAMBLE_BITS[:16]),
            bit_errors(payload_bits[:16], PREAMBLE_BITS_INV[:16]),
        )
        has_magic = payload[:2] == b"RS"
        packet = parse_packet(payload)
        frame_hex, frame_bin = bits_to_hex_and_bin(frame_bits)
        first_byte_errors = bit_errors(frame_bits[:8], PREAMBLE_BITS[:8])
        start_symbol = frame_start
        end_symbol = frame_end
        demod_start_sample = float(sample_offset + frame_start * target_sps)
        demod_end_sample = float(sample_offset + frame_end * target_sps)
        preamble_strength = float(captured_preamble_bits)

        score = (
            (0 if packet is not None else 50_000)
            + first_byte_errors * 20_000
            + sync_errors * 2_000
            + magic_errors * 600
            + preamble_errors * 150
            + max(0, 8 - preamble_like_errors) * 3_000
            - captured_preamble_bits * 8
        )

        candidate = DecodeCandidate(
            burst_index=burst_index,
            freq_offset_hz=float(freq_offset_hz),
            target_sps=target_sps,
            timing_sps=float(target_sps),
            timing_phase=float(sample_offset),
            polarity=polarity,
            sample_offset=sample_offset,
            demod_start_sample=demod_start_sample,
            demod_end_sample=demod_end_sample,
            start_sample=0,
            end_sample=0,
            start_symbol=start_symbol,
            end_symbol=end_symbol,
            preamble_errors=preamble_errors,
            sync_errors=sync_errors,
            preamble_strength=preamble_strength,
            first_byte_errors=first_byte_errors,
            has_magic=has_magic,
            score=score,
            frame_hex=frame_hex,
            frame_bin=frame_bin,
            payload_hex=payload.hex(),
            payload_prefix_hex=payload[:12].hex(),
            payload=payload,
            packet=packet,
        )

        if best_candidate is None or (
            (0 if candidate.packet is not None else 1,
             candidate.first_byte_errors,
             0 if candidate.has_magic else 1,
             candidate.score,
             candidate.preamble_errors,
             candidate.sync_errors,
             -int(candidate.preamble_strength))
            <
            (0 if best_candidate.packet is not None else 1,
             best_candidate.first_byte_errors,
             0 if best_candidate.has_magic else 1,
             best_candidate.score,
             best_candidate.preamble_errors,
             best_candidate.sync_errors,
             -int(best_candidate.preamble_strength))
        ):
            best_candidate = candidate

    return best_candidate


def sample_symbols_float(demod_samples: np.ndarray, start_sample: float, sps: float, symbol_count: int) -> np.ndarray:
    if symbol_count <= 0 or sps <= 1.0:
        return np.empty(0, dtype=np.float32)

    last_needed = start_sample + symbol_count * sps
    if start_sample < 0.0 or last_needed >= float(demod_samples.size - 1):
        return np.empty(0, dtype=np.float32)

    symbol_idx = np.arange(symbol_count, dtype=np.float64)[:, None]
    tap_offsets = np.array([0.30, 0.50, 0.70], dtype=np.float64)[None, :]
    positions = start_sample + (symbol_idx + tap_offsets) * sps
    sampled = np.interp(positions.ravel(), np.arange(demod_samples.size, dtype=np.float64), demod_samples)
    return sampled.reshape(symbol_count, 3).mean(axis=1).astype(np.float32)


def transition_signal(demod_samples: np.ndarray) -> np.ndarray:
    smoothed = moving_average(demod_samples.astype(np.float32), 3)
    prod = smoothed[:-1] * smoothed[1:]
    return np.maximum(0.0, -prod).astype(np.float32)


def strong_edge_positions(transitions: np.ndarray, sample_limit: int, count: int, min_gap: int) -> list[int]:
    limit = min(sample_limit, transitions.size)
    if limit <= 0:
        return []

    order = np.argsort(transitions[:limit])[::-1]
    selected: list[int] = []
    for idx in order:
        pos = int(idx)
        if transitions[pos] <= 0.0:
            break
        if any(abs(pos - prev) < min_gap for prev in selected):
            continue
        selected.append(pos)
        if len(selected) >= count:
            break
    selected.sort()
    return selected


def nearest_peak(transitions: np.ndarray, center: float, tolerance: int) -> tuple[int | None, float]:
    lo = max(0, int(round(center)) - tolerance)
    hi = min(transitions.size, int(round(center)) + tolerance + 1)
    if lo >= hi:
        return None, 0.0
    rel = int(np.argmax(transitions[lo:hi]))
    pos = lo + rel
    strength = float(transitions[pos])
    if strength <= 0.0:
        return None, 0.0
    return pos, strength


def detect_preamble_timing(
    demod_samples: np.ndarray,
    coarse_sps: float,
) -> tuple[float, float, float] | None:
    transitions = transition_signal(demod_samples)
    prefix_limit = int(min(transitions.size, coarse_sps * MAX_PREAMBLE_START_SYMBOLS))
    edge_candidates = strong_edge_positions(
        transitions,
        prefix_limit,
        count=MAX_CANDIDATES_PER_OFFSET * 4,
        min_gap=max(1, int(round(coarse_sps * 0.6))),
    )
    if not edge_candidates:
        return None

    best_hits = -1
    best_score = -1.0
    best_start = 0.0
    best_sps = coarse_sps

    for first_edge in edge_candidates:
        for sps in np.linspace(coarse_sps - 1.0, coarse_sps + 1.0, 9):
            if sps <= 2.0:
                continue
            tolerance = max(1, int(round(sps * 0.30)))
            total = 0.0
            hits = 0
            matched_edges: list[int] = []
            for k in range(PREAMBLE_BITS.size - 1):
                peak_pos, strength = nearest_peak(transitions, first_edge + k * sps, tolerance)
                if peak_pos is None:
                    continue
                total += strength
                hits += 1
                matched_edges.append(peak_pos)

            if hits < PREAMBLE_BITS.size // 2:
                continue

            local_sps = float(np.median(np.diff(matched_edges))) if len(matched_edges) >= 2 else float(sps)
            rewind_edge = matched_edges[0]
            while True:
                prev_peak, prev_strength = nearest_peak(transitions, rewind_edge - local_sps, tolerance)
                if prev_peak is None or prev_strength < (total / max(1, hits)) * 0.35:
                    break
                rewind_edge = prev_peak

            start = float(rewind_edge) - local_sps
            score = total / hits
            if hits > best_hits or (hits == best_hits and (score > best_score or (abs(score - best_score) < 1e-6 and start < best_start))):
                best_hits = hits
                best_score = score
                best_start = start
                best_sps = local_sps

    if best_hits < 0 or best_score <= 0.0:
        return None
    return best_start, best_sps, best_score


def optimize_frame_timing(
    demod_samples: np.ndarray,
    coarse_start: float,
    coarse_sps: float,
) -> tuple[float, float, np.ndarray, int, int, float, str] | None:
    best_score = 10**9
    best_start = coarse_start
    best_sps = coarse_sps
    best_bits = np.empty(0, dtype=np.uint8)
    best_preamble_errors = PREAMBLE_BITS.size + 1
    best_sync_errors = SYNC_BITS.size + 1
    best_strength = 0.0
    best_polarity = "normal"

    for sps_delta in np.linspace(-0.8, 0.8, 9):
        trial_sps = coarse_sps + float(sps_delta)
        if trial_sps <= 2.0:
            continue
        for start_delta in np.linspace(-1.0 * coarse_sps, 1.0 * coarse_sps, 17):
            trial_start = coarse_start + float(start_delta)
            frame_values = sample_symbols_float(demod_samples, trial_start, trial_sps, FRAME_BITS)
            if frame_values.size != FRAME_BITS:
                continue

            abs_strength = float(np.mean(np.abs(frame_values[:PREAMBLE_BITS.size])))
            phase_options = (
                ("normal", (frame_values > 0.0).astype(np.uint8)),
                ("inverted", ((frame_values > 0.0).astype(np.uint8) ^ 1)),
            )
            for polarity_name, bits in phase_options:
                preamble = bits[:PREAMBLE_BITS.size]
                preamble_errors, _ = preamble_window_errors(preamble)
                sync = bits[PREAMBLE_BITS.size:PREAMBLE_BITS.size + SYNC_BITS.size]
                sync_errors = int(np.count_nonzero(sync ^ SYNC_BITS))
                score = preamble_errors * 32 + sync_errors * 128 - int(round(abs_strength * 40.0))

                if score < best_score:
                    best_score = score
                    best_start = trial_start
                    best_sps = trial_sps
                    best_bits = bits
                    best_preamble_errors = preamble_errors
                    best_sync_errors = sync_errors
                    best_strength = abs_strength
                    best_polarity = polarity_name

    if best_bits.size != FRAME_BITS:
        return None
    return best_start, best_sps, best_bits, best_preamble_errors, best_sync_errors, best_strength, best_polarity


def align_to_preamble_start(
    demod_samples: np.ndarray,
    coarse_start: float,
    sps: float,
    polarity: str,
) -> tuple[float, np.ndarray, int, int] | None:
    guard_bits = PREAMBLE_BITS.size
    start = coarse_start - guard_bits * sps
    symbol_count = FRAME_BITS + guard_bits * 2
    values = sample_symbols_float(demod_samples, start, sps, symbol_count)
    if values.size != symbol_count:
        return None

    base_bits = (values > 0.0).astype(np.uint8)
    stream = base_bits if polarity == "normal" else (base_bits ^ 1)
    max_shift = guard_bits * 2
    best_shift = None
    best_key: tuple[int, int, int] | None = None

    for shift in range(max_shift + 1):
        if shift + FRAME_BITS > stream.size:
            continue

        run = 1
        idx = shift
        while idx + run < stream.size and stream[idx + run] != stream[idx + run - 1]:
            run += 1

        aligned_shift = shift
        if stream[aligned_shift] == 0 and run >= 2:
            aligned_shift += 1
            run -= 1

        if aligned_shift + 8 > stream.size:
            continue
        if not np.array_equal(stream[aligned_shift:aligned_shift + 8], PREAMBLE_BITS[:8]):
            continue
        if aligned_shift + FRAME_BITS > stream.size:
            continue

        frame = stream[aligned_shift:aligned_shift + FRAME_BITS]
        preamble = frame[:PREAMBLE_BITS.size]
        preamble_errors, _ = preamble_window_errors(preamble)
        sync = frame[PREAMBLE_BITS.size:PREAMBLE_BITS.size + SYNC_BITS.size]
        sync_errors = int(np.count_nonzero(sync ^ SYNC_BITS))
        key = (-run, preamble_errors, aligned_shift, sync_errors)
        if best_key is None or key < best_key:
            best_key = key
            best_shift = aligned_shift

    if best_shift is None:
        return None

    final_start = start + best_shift * sps
    final_values = sample_symbols_float(demod_samples, final_start, sps, FRAME_BITS)
    if final_values.size != FRAME_BITS:
        return None
    final_bits = (final_values > 0.0).astype(np.uint8)
    if polarity == "inverted":
        final_bits ^= 1

    preamble = final_bits[:PREAMBLE_BITS.size]
    best_preamble_errors, _ = preamble_window_errors(preamble)
    sync = final_bits[PREAMBLE_BITS.size:PREAMBLE_BITS.size + SYNC_BITS.size]
    best_sync_errors = int(np.count_nonzero(sync ^ SYNC_BITS))

    return final_start, final_bits, best_preamble_errors, best_sync_errors


def align_output_to_preamble_byte(
    demod_samples: np.ndarray,
    coarse_start: float,
    sps: float,
    polarity: str,
) -> tuple[float, np.ndarray] | None:
    search_before = PREAMBLE_BITS.size * 2
    search_after = PREAMBLE_BITS.size * 2
    window_start = coarse_start - search_before * sps
    symbol_count = FRAME_BITS + search_before + search_after
    values = sample_symbols_float(demod_samples, window_start, sps, symbol_count)
    if values.size != symbol_count:
        return None

    base_stream = (values > 0.0).astype(np.uint8)
    polarity_options = [polarity, "inverted" if polarity == "normal" else "normal"]

    best_shift = None
    best_polarity = polarity
    best_key: tuple[int, int, int, int] | None = None

    for polarity_name in polarity_options:
        stream = base_stream if polarity_name == "normal" else (base_stream ^ 1)
        for shift in range(search_before + search_after + 1):
            if shift + FRAME_BITS > stream.size:
                continue

            frame = stream[shift:shift + FRAME_BITS]
            first_byte_errors = int(np.count_nonzero(frame[:8] ^ PREAMBLE_BITS[:8]))
            first_two_bytes_errors = int(np.count_nonzero(frame[:16] ^ PREAMBLE_BITS[:16]))
            preamble_errors, _ = preamble_window_errors(frame[:PREAMBLE_BITS.size])
            sync = frame[PREAMBLE_BITS.size:PREAMBLE_BITS.size + SYNC_BITS.size]
            sync_errors = int(np.count_nonzero(sync ^ SYNC_BITS))
            key = (first_byte_errors, first_two_bytes_errors, preamble_errors, shift)

            if best_key is None or key < best_key:
                best_key = key
                best_shift = shift
                best_polarity = polarity_name

    if best_shift is None:
        return None

    final_start = window_start + best_shift * sps
    final_values = sample_symbols_float(demod_samples, final_start, sps, FRAME_BITS)
    if final_values.size != FRAME_BITS:
        return None
    final_bits = (final_values > 0.0).astype(np.uint8)
    if best_polarity == "inverted":
        final_bits ^= 1
    return final_start, final_bits


def search_packet(
    demod_samples: np.ndarray,
    burst_index: int,
    freq_offset_hz: float,
    target_sps: int,
    max_sync_errors: int,
    max_preamble_errors: int,
) -> tuple[DecodeCandidate | None, list[DecodeCandidate]]:
    candidates: list[DecodeCandidate] = []

    if demod_samples.size < target_sps * (SYNC_BITS.size + PAYLOAD_BITS + 8):
        return None, []

    scale = float(np.median(np.abs(demod_samples)))
    scale = max(scale, 1e-6)
    normalized = demod_samples / scale
    coarse_seed_candidates = coarse_header_seeds(normalized, burst_index, freq_offset_hz, target_sps)
    seeds = coarse_seed_candidates[:8]

    for seed in seeds:
        candidates.extend(
            refine_seed_candidate(
                normalized,
                seed,
                burst_index,
                freq_offset_hz,
                target_sps,
                max_sync_errors,
                max_preamble_errors,
            )
        )

    if not candidates:
        candidates = coarse_seed_candidates

    candidates.sort(key=candidate_sort_key)
    return (candidates[0] if candidates else None), candidates[:20]


def decode_burst(
    burst: Burst,
    samples: np.ndarray,
    sample_rate: int,
    freq_offsets: list[float],
    target_sps_list: list[int],
    max_sync_errors: int,
    max_preamble_errors: int,
) -> tuple[DecodeCandidate | None, list[DecodeCandidate], dict[tuple[int, float], np.ndarray]]:
    all_candidates: list[DecodeCandidate] = []
    demodulated: dict[tuple[int, float], np.ndarray] = {}
    margin = int(sample_rate * ANALYSIS_MARGIN_MS / 1000.0)
    analysis_start = max(0, burst.start_sample - margin)
    analysis_end = min(samples.size, burst.end_sample + margin)
    burst_samples = samples[analysis_start:analysis_end]
    estimated_offset = estimate_peak_offset(burst_samples, sample_rate)

    freq_search = [estimated_offset - 1000.0, estimated_offset, estimated_offset + 1000.0]
    for offset_hz in freq_offsets:
        if all(abs(offset_hz - existing) > 1.0 for existing in freq_search):
            freq_search.append(offset_hz)

    for target_sps in target_sps_list:
        for offset_hz in freq_search:
            demod = demodulate_burst(burst_samples, sample_rate, target_sps, offset_hz)
            demodulated[(target_sps, offset_hz)] = demod
            best, candidates = search_packet(demod, burst.index, offset_hz, target_sps, max_sync_errors, max_preamble_errors)
            adjusted_candidates = [
                DecodeCandidate(
                    burst_index=item.burst_index,
                    freq_offset_hz=item.freq_offset_hz,
                    target_sps=item.target_sps,
                    timing_sps=item.timing_sps,
                    timing_phase=item.timing_phase,
                    polarity=item.polarity,
                    sample_offset=item.sample_offset,
                    demod_start_sample=item.demod_start_sample,
                    demod_end_sample=item.demod_end_sample,
                    start_sample=int(round(analysis_start + item.demod_start_sample * sample_rate / float(BITRATE * item.target_sps))),
                    end_sample=int(round(analysis_start + item.demod_end_sample * sample_rate / float(BITRATE * item.target_sps))),
                    start_symbol=item.start_symbol,
                    end_symbol=item.end_symbol,
                    preamble_errors=item.preamble_errors,
                    sync_errors=item.sync_errors,
                    preamble_strength=item.preamble_strength,
                    first_byte_errors=item.first_byte_errors,
                    has_magic=item.has_magic,
                    score=item.score,
                    frame_hex=item.frame_hex,
                    frame_bin=item.frame_bin,
                    payload_hex=item.payload_hex,
                    payload_prefix_hex=item.payload_prefix_hex,
                    payload=item.payload,
                    packet=item.packet,
                )
                for item in candidates
            ]
            all_candidates.extend(adjusted_candidates)
            if adjusted_candidates and adjusted_candidates[0].packet is not None:
                return adjusted_candidates[0], all_candidates, demodulated

    all_candidates.sort(
        key=lambda item: (
            0 if item.packet is not None else 1,
            item.first_byte_errors,
            0 if item.has_magic else 1,
            item.score,
            item.preamble_errors,
            item.sync_errors,
            abs(item.freq_offset_hz),
        )
    )
    return (all_candidates[0] if all_candidates else None), all_candidates[:20], demodulated


def decode_all_bursts(
    bursts: list[Burst],
    samples: np.ndarray,
    sample_rate: int,
    freq_offsets: list[float],
    target_sps_list: list[int],
    max_sync_errors: int,
    max_preamble_errors: int,
) -> tuple[list[tuple[Burst, DecodeCandidate | None, list[DecodeCandidate], dict[tuple[int, float], np.ndarray]]], dict[tuple[int, int], Packet]]:
    results = []
    decoded_packets: dict[tuple[int, int], Packet] = {}

    for burst in bursts:
        best, candidates, demodulated = decode_burst(
            burst,
            samples,
            sample_rate,
            freq_offsets,
            target_sps_list,
            max_sync_errors,
            max_preamble_errors,
        )
        results.append((burst, best, candidates, demodulated))
        if best is not None and best.packet is not None:
            key = (best.packet.sequence, best.packet.uptime_ms)
            decoded_packets[key] = best.packet

    return results, decoded_packets


def plot_analysis(
    samples: np.ndarray,
    sample_rate: int,
    bursts: list[Burst],
    power_env: np.ndarray,
    discrim_env: np.ndarray,
    threshold: float,
    decode_results: list[tuple[Burst, DecodeCandidate | None, list[DecodeCandidate], dict[float, np.ndarray]]],
    chosen_burst: Burst | None,
    demod: np.ndarray | None,
    chosen_target_sps: int | None,
    output: Path | None,
) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), constrained_layout=True)

    t = np.arange(samples.size, dtype=np.float64) / float(sample_rate)
    mag = np.abs(samples)
    decim = max(1, samples.size // 20_000)

    axes[0].plot(t[::decim], mag[::decim], lw=0.7)
    axes[0].set_title("IQ Magnitude")
    axes[0].set_ylabel("Magnitude")

    env_t = np.arange(power_env.size, dtype=np.float64) / float(sample_rate)
    axes[1].plot(env_t[::decim], power_env[::decim], lw=0.7, label="power")
    axes[1].plot(env_t[::decim], discrim_env[::decim], lw=0.6, alpha=0.7, label="|discriminator|")
    axes[1].axhline(threshold, color="red", linestyle="--", lw=0.8)
    axes[1].set_title("Burst Detection Envelope")
    axes[1].set_ylabel("Envelope")
    axes[1].legend(loc="upper right")

    decode_map = {burst.index: best for burst, best, _candidates, _demodulated in decode_results}
    for burst in bursts:
        start_t = burst.start_sample / float(sample_rate)
        end_t = burst.end_sample / float(sample_rate)
        axes[0].axvspan(start_t, end_t, color="#7bb661", alpha=0.2)
        axes[1].axvspan(start_t, end_t, color="#7bb661", alpha=0.2)
        best = decode_map.get(burst.index)
        if best is not None and best.packet is not None:
            label = f"#{burst.index} seq={best.packet.sequence}"
        else:
            label = f"#{burst.index}"
        axes[0].text(start_t, np.max(mag[::decim]) * 0.92, label, fontsize=8, va="top")

    if chosen_burst is not None:
        burst_samples = samples[chosen_burst.start_sample:chosen_burst.end_sample]
        burst_t = np.arange(burst_samples.size, dtype=np.float64) / float(sample_rate)
        burst_mag = np.abs(burst_samples)
        axes[2].plot(burst_t, burst_mag, lw=0.7)
        axes[2].set_title(
            f"Selected Burst #{chosen_burst.index} ({(chosen_burst.end_sample - chosen_burst.start_sample) * 1000.0 / sample_rate:.1f} ms)"
        )
        axes[2].set_ylabel("Magnitude")
        axes[2].set_xlabel("Time within burst [s]")

        best = decode_map.get(chosen_burst.index)
        if best is not None:
            if best.packet is not None:
                text = format_packet(best.packet)
            else:
                text = (
                    f"best candidate: freq_offset={best.freq_offset_hz:+.0f}Hz polarity={best.polarity} "
                    f"target_sps={best.target_sps} timing_sps={best.timing_sps:.2f} "
                    f"offset={best.sample_offset} start={best.start_symbol} end={best.end_symbol} "
                    f"preamble_err={best.preamble_errors} preamble_strength={best.preamble_strength:.2f} "
                    f"sync_err={best.sync_errors} magic={int(best.has_magic)}\n"
                    f"frame_hex={best.frame_hex}"
                )
            axes[2].text(
                0.01,
                0.98,
                text,
                transform=axes[2].transAxes,
                va="top",
                ha="left",
                fontsize=8,
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "#cccccc"},
            )

    if demod is not None and chosen_target_sps is not None:
        demod_t = np.arange(demod.size, dtype=np.float64) / float(BITRATE * chosen_target_sps)
        axes[3].plot(demod_t, demod, lw=0.7)
        axes[3].set_title("Demodulated FSK (resampled)")
        axes[3].set_ylabel("Discriminator")
        axes[3].set_xlabel("Time within burst [s]")
        if chosen_burst is not None:
            best = decode_map.get(chosen_burst.index)
            if best is not None:
                frame_start = best.demod_start_sample / float(BITRATE * chosen_target_sps)
                frame_end = best.demod_end_sample / float(BITRATE * chosen_target_sps)
                axes[3].axvspan(frame_start, frame_end, color="#7bb661", alpha=0.18)

    decoded_lines = []
    for burst, best, _candidates, _demodulated in decode_results:
        if best is not None and best.packet is not None:
            decoded_lines.append(f"burst {burst.index}: {format_packet(best.packet)}")
    if decoded_lines:
        fig.suptitle("\n".join(decoded_lines[:4]), fontsize=9)

    if output is not None:
        fig.savefig(output, dpi=140)
        print(f"plot saved to {output}")
    else:
        plt.show()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline analyzer for SI4032 RS41 FSK bursts")
    parser.add_argument("input_file", nargs="?", default="tools/rs41_g10.cu8")
    parser.add_argument("--sample-rate", type=int, default=1_000_000)
    parser.add_argument("--threshold-mad", type=float, default=20.0)
    parser.add_argument("--min-duration-ms", type=float, default=80.0)
    parser.add_argument("--env-window-ms", type=float, default=10.0)
    parser.add_argument("--merge-gap-ms", type=float, default=80.0)
    parser.add_argument("--pad-ms", type=float, default=0.0)
    parser.add_argument("--target-sps", type=int, default=16)
    parser.add_argument("--target-sps-list", default="16")
    parser.add_argument("--freq-offsets", default="0")
    parser.add_argument("--max-sync-errors", type=int, default=2)
    parser.add_argument("--max-preamble-errors", type=int, default=16)
    parser.add_argument("--plot-file")
    parser.add_argument("--no-plot", action="store_true")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    input_path = Path(args.input_file)
    plot_path = Path(args.plot_file) if args.plot_file else None
    freq_offsets = [float(x.strip()) for x in args.freq_offsets.split(",") if x.strip()]
    target_sps_list = [int(x.strip()) for x in args.target_sps_list.split(",") if x.strip()]
    if args.target_sps not in target_sps_list:
        target_sps_list.append(args.target_sps)
    target_sps_list = sorted(set(x for x in target_sps_list if x > 1))

    samples = load_cu8(input_path)
    bursts, power_env, discrim_env, threshold = detect_bursts(
        samples,
        args.sample_rate,
        args.threshold_mad,
        args.min_duration_ms,
        args.env_window_ms,
        args.merge_gap_ms,
        args.pad_ms,
    )

    print(f"file={input_path} iq_samples={samples.size} duration={samples.size / args.sample_rate:.3f}s")
    print(f"detected_bursts={len(bursts)} threshold={threshold:.5f}")
    print(f"power_noise_floor={float(np.median(power_env)):.5f} power_peak={float(np.max(power_env)):.5f}")
    print(f"discriminator_noise_floor={float(np.median(discrim_env)):.5f} discriminator_peak={float(np.max(discrim_env)):.5f}")

    for burst in bursts:
        duration_ms = (burst.end_sample - burst.start_sample) * 1000.0 / args.sample_rate
        peak_offset = estimate_peak_offset(samples[burst.start_sample:burst.end_sample], args.sample_rate)
        print(
            f"burst[{burst.index}] start={burst.start_sample / args.sample_rate:.6f}s "
            f"end={burst.end_sample / args.sample_rate:.6f}s duration={duration_ms:.1f}ms "
            f"peak_env={burst.peak_env:.5f} peak_offset={peak_offset:+.0f}Hz"
        )

    decode_results, decoded_packets = decode_all_bursts(
        bursts,
        samples,
        args.sample_rate,
        freq_offsets,
        target_sps_list,
        args.max_sync_errors,
        args.max_preamble_errors,
    )

    chosen_burst = None
    demod = None
    chosen_target_sps = None
    for burst, best, _candidates, demodulated in decode_results:
        if chosen_burst is None:
            chosen_burst = burst
            if demodulated:
                first_key = next(iter(demodulated))
                chosen_target_sps = first_key[0]
                demod = demodulated[first_key]
        if best is not None and best.packet is not None:
            chosen_burst = burst
            chosen_target_sps = best.target_sps
            demod = demodulated.get((best.target_sps, best.freq_offset_hz), next(iter(demodulated.values())))
            break
        if best is not None and chosen_burst == burst:
            chosen_target_sps = best.target_sps
            demod = demodulated.get((best.target_sps, best.freq_offset_hz), next(iter(demodulated.values())))

    printed_any = False
    for burst, best, _candidates, _demodulated in decode_results:
        if best is not None and best.packet is not None:
            printed_any = True
            print(
                f"burst={best.burst_index} target_sps={best.target_sps} freq_offset={best.freq_offset_hz:+.0f}Hz "
                f"timing_sps={best.timing_sps:.2f} "
                f"polarity={best.polarity} sample_offset={best.sample_offset} "
                f"start_sample={best.start_sample} end_sample={best.end_sample} "
                f"start={best.start_symbol} end={best.end_symbol} "
                f"preamble_errors={best.preamble_errors} preamble_strength={best.preamble_strength:.2f} "
                f"sync_errors={best.sync_errors}"
            )
            print(f"frame_hex={best.frame_hex}")
            print(f"frame_bin={best.frame_bin}")
            print(f"payload_hex={best.payload_hex}")
            print(format_packet(best.packet))
            print("payload fields:")
            for line in decode_payload_fields(best.payload):
                print(f"  {line}")
        elif best is not None:
            print(
                f"burst={best.burst_index} target_sps={best.target_sps} freq_offset={best.freq_offset_hz:+.0f}Hz "
                f"timing_sps={best.timing_sps:.2f} "
                f"polarity={best.polarity} sample_offset={best.sample_offset} "
                f"start_sample={best.start_sample} end_sample={best.end_sample} "
                f"start={best.start_symbol} end={best.end_symbol} "
                f"preamble_errors={best.preamble_errors} preamble_strength={best.preamble_strength:.2f} "
                f"sync_errors={best.sync_errors}"
            )
            print(f"frame_hex={best.frame_hex}")
            print(f"frame_bin={best.frame_bin}")
            print(f"payload_hex={best.payload_hex}")
            print("payload fields:")
            for line in decode_payload_fields(best.payload):
                print(f"  {line}")

    if not printed_any and not decode_results:
        print("no frame candidate found")
    elif not printed_any and decode_results and all(best is None for _burst, best, _candidates, _demodulated in decode_results):
        print("no frame candidate found")

    if not args.no_plot:
        plot_analysis(
            samples,
            args.sample_rate,
            bursts,
            power_env,
            discrim_env,
            threshold,
            decode_results,
            chosen_burst,
            demod,
            chosen_target_sps,
            plot_path,
        )

    return 0 if decoded_packets else 1


if __name__ == "__main__":
    raise SystemExit(main())
