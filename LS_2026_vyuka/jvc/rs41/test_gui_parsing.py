#!/usr/bin/env python3
"""Test script to verify GUI packet parsing"""

from rs41_gtk_tracker import RS41Tracker

def test_packet_parsing():
    """Test the text packet parsing function"""

    tracker = RS41Tracker()

    # Test sample packet line (typical output from rtl_rfm_rs41)
    test_lines = [
        "seq=1234 uptime=567890ms gps=1 sats=8 lat=50.1234567 lon=14.4567890 alt=1234.56m speed=12.34m/s batt=3300mV temp=25.67C",
        "seq=1235 uptime=568000ms gps=1 sats=7 lat=50.1234600 lon=14.4567920 alt=1235.00m speed=12.40m/s batt=3295mV temp=25.70C",
        "seq=1236 uptime=568110ms gps=0 batt=3290mV temp=25.72C"  # No GPS
    ]

    print("Testing packet parsing:")
    for i, line in enumerate(test_lines, 1):
        print(f"\nTest {i}: {line}")

        # Parse the line
        data = {}
        parts = line.split()

        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)

                if key == 'seq':
                    data['sequence'] = int(value)
                elif key == 'uptime':
                    data['uptime_ms'] = int(value.replace('ms', ''))
                elif key == 'gps':
                    data['gps_valid'] = int(value) == 1
                elif key == 'lat':
                    data['latitude'] = float(value)
                elif key == 'lon':
                    data['longitude'] = float(value)
                elif key == 'alt':
                    data['altitude_m'] = float(value.replace('m', ''))
                elif key == 'speed':
                    data['speed_m_s'] = float(value.replace('m/s', ''))
                elif key == 'sats':
                    data['satellites'] = int(value)
                elif key == 'batt':
                    data['battery_mv'] = int(value.replace('mV', ''))
                elif key == 'temp':
                    data['mcu_temp_c'] = float(value.replace('C', ''))

        print(f"Parsed data: {data}")

        # Create packet
        packet = tracker.create_packet_from_data(data)
        if packet:
            print(f"Created packet: seq={packet.sequence}, uptime={packet.uptime_ms}ms")
            if packet.latitude and packet.longitude:
                print(f"GPS: {packet.latitude:.6f}, {packet.longitude:.6f}")
            print(f"Flags: 0x{packet.flags:02x}")
        else:
            print("Failed to create packet")

if __name__ == "__main__":
    test_packet_parsing()