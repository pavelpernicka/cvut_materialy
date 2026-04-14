#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass


PACKET_LEN = 48
SYNC_BYTES_V1 = b"\x2d\xd4"
SYNC_BYTES_V2 = b"\x2d\xd4"
HEADER_BYTES_V2 = b"RS"
MAGIC = b"RS"
PROTOCOL_VERSION_V1 = 1
PROTOCOL_VERSION_V2 = 2
WHITEN_START = 2
SYNC_BYTES = SYNC_BYTES_V1
PROTOCOL_VERSION = PROTOCOL_VERSION_V1

FLAG_GPS_POSITION_VALID = 1 << 0
FLAG_GPS_ALTITUDE_VALID = 1 << 1
FLAG_GPS_SPEED_VALID = 1 << 2

TLV_BOARD_STATUS = 0x01
TLV_GPS_POSITION = 0x02
TLV_GPS_MOTION = 0x03


@dataclass(frozen=True)
class Packet:
    sequence: int
    uptime_ms: int
    flags: int
    battery_mv: int | None
    mcu_temp_c: float | None
    satellites: int | None
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    speed_m_s: float | None

    @property
    def dedupe_key(self) -> tuple[int, int]:
        return (self.sequence, self.uptime_ms)


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


def _whiten_byte(lfsr: int) -> tuple[int, int]:
    mask = 0
    for bit in range(8):
        feedback = ((lfsr >> 0) ^ (lfsr >> 5)) & 0x01
        mask |= (lfsr & 0x01) << bit
        lfsr = (lfsr >> 1) | (feedback << 8)
    return mask, lfsr


def dewhiten_packet(raw: bytes) -> bytes:
    data = bytearray(raw)
    lfsr = 0x01FF
    for index in range(WHITEN_START, len(data)):
        mask, lfsr = _whiten_byte(lfsr)
        data[index] ^= mask
    return bytes(data)


def _u16le(raw: bytes) -> int:
    return int.from_bytes(raw, "little", signed=False)


def _s16le(raw: bytes) -> int:
    return int.from_bytes(raw, "little", signed=True)


def _s32le(raw: bytes) -> int:
    return int.from_bytes(raw, "little", signed=True)


def parse_packet(raw: bytes) -> Packet | None:
    if len(raw) != PACKET_LEN:
        return None

    parsed = _parse_packet_version(raw)
    if parsed is not None:
        return parsed

    if raw[:2] != MAGIC:
        return None
    return _parse_packet_version(dewhiten_packet(raw))


def _parse_packet_version(raw: bytes) -> Packet | None:
    if raw[:2] != MAGIC:
        return None
    if raw[2] not in (PROTOCOL_VERSION_V1, PROTOCOL_VERSION_V2):
        return None

    crc_rx = _u16le(raw[-2:])
    crc_calc = crc16_ccitt_false(raw[:-2])
    if crc_rx != crc_calc:
        return None

    flags = raw[3]
    sequence = _u16le(raw[4:6])
    uptime_ms = int.from_bytes(raw[6:10], "little", signed=False)
    payload_len = raw[10]
    payload = raw[12:12 + payload_len]

    if payload_len > (PACKET_LEN - 14):
        return None

    battery_mv: int | None = None
    mcu_temp_c: float | None = None
    satellites: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    speed_m_s: float | None = None

    pos = 0
    while pos + 2 <= len(payload):
        tlv_type = payload[pos]
        tlv_len = payload[pos + 1]
        pos += 2
        if pos + tlv_len > len(payload):
            return None
        value = payload[pos:pos + tlv_len]
        pos += tlv_len

        if tlv_type == TLV_BOARD_STATUS and tlv_len == 4:
            battery_mv = _u16le(value[0:2])
            mcu_temp_c = _s16le(value[2:4]) / 100.0
        elif tlv_type == TLV_GPS_MOTION and tlv_len == 3:
            speed_m_s = _u16le(value[0:2]) / 100.0
            satellites = value[2]
        elif tlv_type == TLV_GPS_POSITION and tlv_len == 12:
            latitude = _s32le(value[0:4]) / 1e7
            longitude = _s32le(value[4:8]) / 1e7
            altitude_m = _s32le(value[8:12]) / 100.0

    if not (flags & FLAG_GPS_POSITION_VALID):
        latitude = None
        longitude = None
    if not (flags & FLAG_GPS_ALTITUDE_VALID):
        altitude_m = None
    if not (flags & FLAG_GPS_SPEED_VALID):
        speed_m_s = None

    return Packet(
        sequence=sequence,
        uptime_ms=uptime_ms,
        flags=flags,
        battery_mv=battery_mv,
        mcu_temp_c=mcu_temp_c,
        satellites=satellites,
        latitude=latitude,
        longitude=longitude,
        altitude_m=altitude_m,
        speed_m_s=speed_m_s,
    )


def format_packet(packet: Packet) -> str:
    parts = [f"seq={packet.sequence}", f"uptime={packet.uptime_ms}ms"]

    gps_valid = packet.latitude is not None and packet.longitude is not None
    parts.append(f"gps={1 if gps_valid else 0}")

    if packet.satellites is not None:
        parts.append(f"sats={packet.satellites}")
    if packet.latitude is not None and packet.longitude is not None:
        parts.append(f"lat={packet.latitude:.7f}")
        parts.append(f"lon={packet.longitude:.7f}")
    if packet.altitude_m is not None:
        parts.append(f"alt={packet.altitude_m:.2f}m")
    if packet.speed_m_s is not None:
        parts.append(f"speed={packet.speed_m_s:.2f}m/s")
    if packet.battery_mv is not None:
        parts.append(f"batt={packet.battery_mv}mV")
    if packet.mcu_temp_c is not None:
        parts.append(f"temp={packet.mcu_temp_c:.2f}C")

    return " ".join(parts)
