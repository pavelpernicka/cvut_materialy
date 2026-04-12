#!/usr/bin/env python3

from __future__ import annotations

import re
from dataclasses import dataclass


PACKET_LEN = 64
AX25_CONTROL_UI = 0x03
AX25_PID_NO_LAYER3 = 0xF0
AX25_INFO_LEN = 46

_POSITION_RE = re.compile(
    r"^!"
    r"(?P<lat_deg>\d{2})(?P<lat_min>\d{2}\.\d{2})(?P<lat_hemi>[NS])/"
    r"(?P<lon_deg>\d{3})(?P<lon_min>\d{2}\.\d{2})(?P<lon_hemi>[EW])"
    r"(?P<symbol>.)(?P<course>\d{3})/(?P<speed_knots>\d{3})"
    r"/A=(?P<altitude_ft>\d{6})"
    r"V(?P<battery_mv>\d{4})"
    r"T(?P<temp_c>[+-]\d{2})\s*$"
)
_STATUS_RE = re.compile(
    r"^>NOFIX "
    r"V(?P<battery_mv>\d{4}) "
    r"T(?P<temp_c>[+-]\d{2}) "
    r"U(?P<uptime_s>\d{8}) "
    r"Q(?P<satellites>\d{2})\s*$"
)


@dataclass(frozen=True)
class Packet:
    source: str
    destination: str
    info: str
    gps_valid: bool
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    speed_m_s: float | None
    battery_mv: int | None
    temp_c: int | None
    uptime_s: int | None
    satellites: int | None

    @property
    def dedupe_key(self) -> tuple[str, str]:
        return (self.source, self.info)


def crc16_x25(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return (~crc) & 0xFFFF


def looks_like_ax25_ui_frame(raw: bytes) -> bool:
    return len(raw) == PACKET_LEN and raw[14] == AX25_CONTROL_UI and raw[15] == AX25_PID_NO_LAYER3


def decode_ax25_address(addr: bytes) -> str:
    callsign = "".join(chr(byte >> 1) for byte in addr[:6]).rstrip()
    ssid = (addr[6] >> 1) & 0x0F
    if ssid:
        return f"{callsign}-{ssid}"
    return callsign


def _parse_degrees(degrees: str, minutes: str, hemisphere: str) -> float:
    value = int(degrees) + float(minutes) / 60.0
    if hemisphere in ("S", "W"):
        value = -value
    return value


def parse_packet(raw: bytes) -> Packet | None:
    if not looks_like_ax25_ui_frame(raw):
        return None

    fcs_rx = int.from_bytes(raw[-2:], "little")
    if fcs_rx != crc16_x25(raw[:-2]):
        return None

    destination = decode_ax25_address(raw[:7])
    source = decode_ax25_address(raw[7:14])
    info = raw[16:16 + AX25_INFO_LEN].decode("ascii", errors="replace")
    info_stripped = info.rstrip(" \x00")

    match = _POSITION_RE.match(info_stripped)
    if match:
        altitude_ft = int(match.group("altitude_ft"))
        speed_knots = int(match.group("speed_knots"))
        return Packet(
            source=source,
            destination=destination,
            info=info_stripped,
            gps_valid=True,
            latitude=_parse_degrees(match.group("lat_deg"), match.group("lat_min"), match.group("lat_hemi")),
            longitude=_parse_degrees(match.group("lon_deg"), match.group("lon_min"), match.group("lon_hemi")),
            altitude_m=altitude_ft * 0.3048,
            speed_m_s=speed_knots * 0.514444,
            battery_mv=int(match.group("battery_mv")),
            temp_c=int(match.group("temp_c")),
            uptime_s=None,
            satellites=None,
        )

    match = _STATUS_RE.match(info_stripped)
    if match:
        return Packet(
            source=source,
            destination=destination,
            info=info_stripped,
            gps_valid=False,
            latitude=None,
            longitude=None,
            altitude_m=None,
            speed_m_s=None,
            battery_mv=int(match.group("battery_mv")),
            temp_c=int(match.group("temp_c")),
            uptime_s=int(match.group("uptime_s")),
            satellites=int(match.group("satellites")),
        )

    return Packet(
        source=source,
        destination=destination,
        info=info_stripped,
        gps_valid=False,
        latitude=None,
        longitude=None,
        altitude_m=None,
        speed_m_s=None,
        battery_mv=None,
        temp_c=None,
        uptime_s=None,
        satellites=None,
    )


def format_packet(packet: Packet) -> str:
    parts = [f"src={packet.source}", f"dst={packet.destination}"]
    if packet.gps_valid:
        parts.extend([
            "gps=1",
            f"lat={packet.latitude:.5f}",
            f"lon={packet.longitude:.5f}",
            f"alt={packet.altitude_m:.1f}m",
            f"speed={packet.speed_m_s:.2f}m/s",
        ])
    else:
        parts.append("gps=0")
        if packet.uptime_s is not None:
            parts.append(f"uptime={packet.uptime_s}s")
        if packet.satellites is not None:
            parts.append(f"sats={packet.satellites}")

    if packet.battery_mv is not None:
        parts.append(f"batt={packet.battery_mv}mV")
    if packet.temp_c is not None:
        parts.append(f"temp={packet.temp_c}C")
    parts.append(f"info={packet.info}")
    return " ".join(parts)
