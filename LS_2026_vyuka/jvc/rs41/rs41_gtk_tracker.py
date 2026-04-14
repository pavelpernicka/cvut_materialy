#!/usr/bin/env python3
"""
RS41 Radiosonde GTK Tracker
Live telemetry display with GPS mapping using WebKit
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')

import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

import gi
from gi.repository import Gtk, GObject, GLib, WebKit2
from tools.telemetry_packet import parse_packet, format_packet


class RS41Tracker(Gtk.Window):
    def __init__(self):
        super().__init__(title="RS41 Radiosonde Tracker")

        self.set_default_size(1200, 800)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Data storage
        self.packets = []
        self.receiver_process = None
        self.receiver_thread = None
        self.running = False
        self.test_mode = False

        # Build UI
        self.setup_ui()

        # Connect signals
        self.connect("destroy", self.on_destroy)

        # Initialize map
        GLib.timeout_add(1000, self.init_map)

    def setup_ui(self):
        # Main container
        main_box = Gtk.VBox(spacing=6)
        main_box.set_margin_left(10)
        main_box.set_margin_right(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        self.add(main_box)

        # Header with controls
        header_box = Gtk.HBox(spacing=10)
        main_box.pack_start(header_box, False, False, 0)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>RS41 Radiosonde Tracker</b>")
        header_box.pack_start(title_label, False, False, 0)

        # Spacer
        header_box.pack_start(Gtk.Label(), True, True, 0)

        # Controls
        self.start_button = Gtk.Button(label="Start Tracking")
        self.start_button.connect("clicked", self.on_start_clicked)
        header_box.pack_start(self.start_button, False, False, 0)


        self.test_button = Gtk.Button(label="Test Mode")
        self.test_button.connect("clicked", self.on_test_clicked)
        header_box.pack_start(self.test_button, False, False, 0)

        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.set_sensitive(False)
        self.stop_button.connect("clicked", self.on_stop_clicked)
        header_box.pack_start(self.stop_button, False, False, 0)

        # Status
        self.status_label = Gtk.Label()
        self.status_label.set_text("Ready to start tracking")
        header_box.pack_start(self.status_label, False, False, 0)


        # Main content in horizontal panes
        paned = Gtk.HPaned()
        main_box.pack_start(paned, True, True, 0)

        # Left panel for telemetry data
        left_box = Gtk.VBox(spacing=6)
        left_box.set_size_request(400, -1)
        paned.add1(left_box)

        # Current data frame
        current_frame = Gtk.Frame(label="Current Telemetry")
        left_box.pack_start(current_frame, False, False, 0)

        self.current_data = Gtk.TextView()
        self.current_data.set_editable(False)
        self.current_data.set_wrap_mode(Gtk.WrapMode.WORD)
        current_frame.add(self.current_data)

        # Packet log frame
        log_frame = Gtk.Frame(label="Packet Log")
        left_box.pack_start(log_frame, True, True, 0)

        # Scrolled window for packet log
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_frame.add(scrolled)

        self.packet_log = Gtk.TextView()
        self.packet_log.set_editable(False)
        self.packet_log.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.packet_log)

        # Right panel for map
        map_frame = Gtk.Frame(label="GPS Track")
        paned.add2(map_frame)

        # Web view for map
        self.webview = WebKit2.WebView()
        map_frame.add(self.webview)

        # Set initial pane position
        paned.set_position(400)

    def init_map(self):
        """Initialize the map with OpenStreetMap"""
        html = self.get_map_html()
        self.webview.load_html(html, None)
        return False  # Don't repeat this timeout

    def get_map_html(self):
        """Generate HTML for the map with Leaflet"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>RS41 GPS Track</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        html, body { margin: 0; padding: 0; height: 100%; }
        #mapid { height: 100%; }
        .packet-marker {
            background: red;
            border: 2px solid white;
            border-radius: 50%;
            width: 12px;
            height: 12px;
        }
        .current-marker {
            background: lime;
            border: 2px solid white;
            border-radius: 50%;
            width: 16px;
            height: 16px;
        }
    </style>
</head>
<body>
    <div id="mapid"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('mapid').setView([50.0755, 14.4378], 10);  // Prague default

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        var trackLine = L.polyline([], {color: 'blue', weight: 3, opacity: 0.7});
        trackLine.addTo(map);

        var currentMarker = null;
        var markers = [];

        function addPosition(lat, lon, data) {
            // Add to track line
            trackLine.addLatLng([lat, lon]);

            // Remove old current marker
            if (currentMarker) {
                map.removeLayer(currentMarker);
            }

            // Add current position marker
            currentMarker = L.circleMarker([lat, lon], {
                radius: 8,
                fillColor: '#00ff00',
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map);

            // Add popup with telemetry data
            var popup = '<b>RS41 Telemetry</b><br/>';
            popup += 'Sequence: ' + data.sequence + '<br/>';
            popup += 'GPS: ' + lat.toFixed(6) + ', ' + lon.toFixed(6) + '<br/>';
            if (data.altitude_m !== null) {
                popup += 'Altitude: ' + data.altitude_m.toFixed(1) + ' m<br/>';
            }
            if (data.speed_m_s !== null) {
                popup += 'Speed: ' + data.speed_m_s.toFixed(1) + ' m/s<br/>';
            }
            if (data.satellites !== null) {
                popup += 'Satellites: ' + data.satellites + '<br/>';
            }
            popup += 'Uptime: ' + (data.uptime_ms / 1000).toFixed(1) + ' s';

            currentMarker.bindPopup(popup);

            // Center map on current position
            map.setView([lat, lon], Math.max(map.getZoom(), 12));
        }

        function clearTrack() {
            trackLine.setLatLngs([]);
            if (currentMarker) {
                map.removeLayer(currentMarker);
                currentMarker = null;
            }
            markers.forEach(marker => map.removeLayer(marker));
            markers = [];
        }
    </script>
</body>
</html>
"""

    def on_start_clicked(self, button):
        """Start the RS41 receiver"""
        if not self.running:
            self.running = True
            self.test_mode = False
            self.start_button.set_sensitive(False)
            self.test_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.status_label.set_text("Starting receiver...")

            # Clear previous data
            self.packets.clear()
            self.update_current_data(None)
            self.clear_packet_log()
            self.clear_map_track()

            # Start receiver in thread
            self.receiver_thread = threading.Thread(target=self.run_receiver)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()

    def on_test_clicked(self, button):
        """Start test mode with simulated data"""
        if not self.running:
            self.running = True
            self.test_mode = True
            self.start_button.set_sensitive(False)
            self.test_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.status_label.set_text("Starting test mode...")

            # Clear previous data
            self.packets.clear()
            self.update_current_data(None)
            self.clear_packet_log()
            self.clear_map_track()

            # Start test data simulation in thread
            self.receiver_thread = threading.Thread(target=self.run_test_simulation)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()


    def on_stop_clicked(self, button):
        """Stop the RS41 receiver or test mode"""
        if self.running:
            self.running = False
            self.start_button.set_sensitive(True)
            self.test_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)

            if self.test_mode:
                self.status_label.set_text("Stopping test mode...")
                self.test_mode = False
            else:
                self.status_label.set_text("Stopping receiver...")
                if self.receiver_process:
                    self.receiver_process.terminate()
                    self.receiver_process = None

    def run_test_simulation(self):
        """Run a test simulation with fake RS41 data"""
        import random
        import math

        try:
            print("Starting test simulation...")
            GLib.idle_add(self.status_label.set_text, "Test mode active")

            # Simulate a radiosonde launch from Prague
            base_lat = 50.0755  # Prague
            base_lon = 14.4378
            sequence = 1000
            uptime = 3600000  # 1 hour in milliseconds

            packet_count = 0

            while self.running and self.test_mode:
                try:
                    # Simulate radiosonde movement (ascending and drifting)
                    time_hours = uptime / 3600000.0

                    # Altitude increases with time (balloon ascending)
                    altitude = 500 + (time_hours * 1000)  # Start at 500m, rise 1000m/hour

                    # Drift with wind (simulate eastward drift)
                    lat_offset = random.uniform(-0.001, 0.001)  # Small random movement
                    lon_offset = time_hours * 0.01 + random.uniform(-0.001, 0.001)  # Eastward drift

                    latitude = base_lat + lat_offset
                    longitude = base_lon + lon_offset

                    # Simulate other telemetry
                    speed = random.uniform(5.0, 15.0)  # Wind speed
                    satellites = random.randint(6, 12)
                    battery = 3300 - int(time_hours * 50)  # Battery drain
                    temp = 25.0 - (altitude / 100.0)  # Temperature drops with altitude

                    # Create realistic packet line
                    packet_line = (f"seq={sequence} uptime={uptime}ms gps=1 "
                                 f"sats={satellites} lat={latitude:.7f} lon={longitude:.7f} "
                                 f"alt={altitude:.2f}m speed={speed:.2f}m/s "
                                 f"batt={battery}mV temp={temp:.2f}C")

                    print(f"SIMULATION: Generated packet: {packet_line}")
                    self.process_text_packet(packet_line)

                    # Update for next packet
                    sequence += 1
                    uptime += 1000  # 1 second intervals
                    packet_count += 1

                    # Update status
                    if packet_count % 5 == 0:
                        GLib.idle_add(self.status_label.set_text,
                                    f"Test mode: {packet_count} packets, alt={altitude:.0f}m")

                    # Wait 1 second between packets
                    time.sleep(1.0)

                except Exception as e:
                    print(f"Error in test simulation: {e}")
                    break

            print("Test simulation ended")

        except Exception as e:
            print(f"Exception in test simulation: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(self.status_label.set_text, f"Test error: {e}")
        finally:
            print("Test simulation thread ending...")
            GLib.idle_add(self.on_receiver_stopped)

    def run_receiver(self):
        """Just run rx.py directly and capture its output"""
        try:
            print("DEBUG: Running rx.py directly...")

            # Simply run the working rx.py script
            cmd = [
                "python3",
                "tools/rx.py",
                "--freq", "433.92e6",
                "--gain", "20"
            ]

            print(f"DEBUG: Command: {' '.join(cmd)}")
            GLib.idle_add(self.status_label.set_text, "Starting rx.py...")

            # Try different approaches to capture the output
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # Force Python to be unbuffered

            self.receiver_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Keep separate for now
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=0,  # Completely unbuffered
                universal_newlines=True,
                cwd=Path(__file__).parent,
                env=env
            )

            print(f"Process started, PID: {self.receiver_process.pid}")
            GLib.idle_add(self.status_label.set_text, f"rx.py running (PID: {self.receiver_process.pid})")

            line_count = 0
            import select
            import time

            # Process lines from receiver - monitor both stdout and stderr
            while self.running and self.receiver_process:
                try:
                    # Check if process is still alive
                    poll_result = self.receiver_process.poll()
                    if poll_result is not None:
                        print(f"DEBUG: Process terminated with code: {poll_result}")
                        # Try to read any remaining output from both streams
                        remaining_stdout = self.receiver_process.stdout.read()
                        remaining_stderr = self.receiver_process.stderr.read()
                        if remaining_stdout:
                            print(f"DEBUG: Final STDOUT: {repr(remaining_stdout)}")
                        if remaining_stderr:
                            print(f"DEBUG: Final STDERR: {repr(remaining_stderr)}")
                        break

                    # Use select to monitor both streams
                    ready, _, _ = select.select([self.receiver_process.stdout, self.receiver_process.stderr], [], [], 0.1)

                    if not ready:
                        # No data ready, continue loop
                        continue

                    # Read from available streams
                    for stream in ready:
                        if stream == self.receiver_process.stdout:
                            line = self.receiver_process.stdout.readline()
                            source = "STDOUT"
                        elif stream == self.receiver_process.stderr:
                            line = self.receiver_process.stderr.readline()
                            source = "STDERR"
                        else:
                            continue

                        if not line:
                            continue

                        # Show raw line before processing
                        raw_line = repr(line)
                        line = line.strip()
                        line_count += 1

                        print(f"DEBUG: {source} {line_count}: {raw_line}")
                        if line:
                            print(f"DEBUG: {source} processed {line_count}: '{line}'")

                            # Update status to show we're receiving data
                            if line_count % 3 == 0:  # Update every 3 lines
                                GLib.idle_add(self.status_label.set_text,
                                            f"rx.py active: {line_count} lines")

                            # Check for various indicators
                            if '>> GOT SYNC WORD' in line:
                                print(f"DEBUG: *** SYNC WORD in {source}: {line}")
                                GLib.idle_add(self.status_label.set_text, "Signal detected!")

                            if 'FRAME=' in line:
                                print(f"DEBUG: FRAME in {source}: {line}")

                            # Look for packet data anywhere in the line
                            if 'seq=' in line:
                                print(f"DEBUG: *** PACKET in {source} ***: {line}")
                                # Extract just the packet part
                                seq_pos = line.find('seq=')
                                if seq_pos >= 0:
                                    # Find the end of this packet (usually before next >>)
                                    packet_part = line[seq_pos:]
                                    end_pos = packet_part.find('>>')
                                    if end_pos > 0:
                                        packet_part = packet_part[:end_pos]
                                    packet_part = packet_part.strip()
                                    print(f"DEBUG: *** EXTRACTED PACKET ***: '{packet_part}'")
                                    self.process_text_packet(packet_part)
                                else:
                                    print(f"DEBUG: seq= found but couldn't extract position")

                            # Show all lines for now to see what we're getting
                            print(f"DEBUG: {source} content: {line}")

                except Exception as e:
                    print(f"DEBUG: Error in receiver loop: {e}")
                    import traceback
                    traceback.print_exc()
                    break

            print(f"Receiver loop ended. Lines processed: {line_count}")

            if self.receiver_process:
                print("Terminating receiver process...")
                self.receiver_process.terminate()
                try:
                    self.receiver_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("Force killing receiver process...")
                    self.receiver_process.kill()
                self.receiver_process = None

        except Exception as e:
            print(f"Exception in receiver thread: {e}")
            import traceback
            traceback.print_exc()
            GLib.idle_add(self.status_label.set_text, f"Error: {e}")
        finally:
            print("Receiver thread ending...")
            GLib.idle_add(self.on_receiver_stopped)

    def process_text_packet(self, line):
        """Process text packet from rx.py output"""
        try:
            print(f"PACKET: Processing line: {line}")

            # Check if this looks like a packet line (contains seq=)
            if 'seq=' not in line:
                print(f"PACKET: Line doesn't contain seq=, skipping")
                return

            # Parse the formatted text output
            # Example from your output: "seq=56 uptime=560503ms gps=0 sats=0 batt=3444mV temp=-6.16C"

            # Extract data using simple parsing
            data = {}
            parts = line.split()

            print(f"PACKET: Split into parts: {parts}")

            for part in parts:
                if '=' in part:
                    try:
                        key, value = part.split('=', 1)
                        print(f"PACKET: Parsing {key}={value}")

                        if key == 'seq':
                            data['sequence'] = int(value)
                        elif key == 'uptime':
                            # Remove 'ms' suffix and convert to int
                            data['uptime_ms'] = int(value.replace('ms', ''))
                        elif key == 'gps':
                            data['gps_valid'] = int(value) == 1
                        elif key == 'lat':
                            data['latitude'] = float(value)
                        elif key == 'lon':
                            data['longitude'] = float(value)
                        elif key == 'alt':
                            # Remove 'm' suffix
                            data['altitude_m'] = float(value.replace('m', ''))
                        elif key == 'speed':
                            # Remove 'm/s' suffix
                            data['speed_m_s'] = float(value.replace('m/s', ''))
                        elif key == 'sats':
                            data['satellites'] = int(value)
                        elif key == 'batt':
                            # Remove 'mV' suffix
                            data['battery_mv'] = int(value.replace('mV', ''))
                        elif key == 'temp':
                            # Remove 'C' suffix and handle negative values
                            temp_value = value.replace('C', '')
                            data['mcu_temp_c'] = float(temp_value)
                    except ValueError as e:
                        print(f"PACKET: Error parsing {part}: {e}")

            print(f"PACKET: Parsed data: {data}")

            # Create packet object from parsed data
            if 'sequence' in data and 'uptime_ms' in data:
                packet = self.create_packet_from_data(data)
                if packet:
                    print(f"PACKET: Created packet successfully - seq={packet.sequence}")
                    GLib.idle_add(self.on_packet_received, packet)
                else:
                    print(f"PACKET: Failed to create packet from data")
            else:
                print(f"PACKET: Missing required fields (seq/uptime)")

        except Exception as e:
            print(f"PACKET: Error parsing line: {line}, error: {e}")
            import traceback
            traceback.print_exc()

    def create_packet_from_data(self, data):
        """Create a Packet object from parsed data"""
        try:
            # Calculate flags based on available data
            flags = 0
            if data.get('gps_valid') and 'latitude' in data and 'longitude' in data:
                flags |= 1  # FLAG_GPS_POSITION_VALID
            if 'altitude_m' in data:
                flags |= 2  # FLAG_GPS_ALTITUDE_VALID
            if 'speed_m_s' in data:
                flags |= 4  # FLAG_GPS_SPEED_VALID

            from tools.telemetry_packet import Packet

            packet = Packet(
                sequence=data.get('sequence', 0),
                uptime_ms=data.get('uptime_ms', 0),
                flags=flags,
                battery_mv=data.get('battery_mv'),
                mcu_temp_c=data.get('mcu_temp_c'),
                satellites=data.get('satellites'),
                latitude=data.get('latitude') if data.get('gps_valid') else None,
                longitude=data.get('longitude') if data.get('gps_valid') else None,
                altitude_m=data.get('altitude_m'),
                speed_m_s=data.get('speed_m_s')
            )
            return packet

        except Exception as e:
            print(f"Error creating packet from data: {data}, error: {e}")
            return None

    def on_packet_received(self, packet):
        """Handle a received RS41 packet"""
        if not self.running:
            return

        # Store packet
        self.packets.append(packet)

        # Update displays
        self.update_current_data(packet)
        self.append_packet_log(packet)

        # Update map if we have GPS data
        if packet.latitude is not None and packet.longitude is not None:
            self.update_map_position(packet)

        # Update status
        self.status_label.set_text(f"Received {len(self.packets)} packets")

    def on_receiver_stopped(self):
        """Handle receiver or test mode stop"""
        self.running = False
        self.start_button.set_sensitive(True)
        self.test_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)

        if self.test_mode:
            self.status_label.set_text("Test mode stopped")
            self.test_mode = False
        else:
            self.status_label.set_text("Receiver stopped")

    def update_current_data(self, packet):
        """Update current telemetry display"""
        buffer = self.current_data.get_buffer()

        if packet is None:
            buffer.set_text("No data")
            return

        text = f"""Sequence: {packet.sequence}
Uptime: {packet.uptime_ms/1000:.1f} seconds ({packet.uptime_ms/3600000:.2f} hours)
Flags: 0x{packet.flags:02x}

GPS Status: {"Valid" if (packet.latitude and packet.longitude) else "Invalid"}
"""

        if packet.latitude is not None and packet.longitude is not None:
            text += f"Latitude: {packet.latitude:.7f}°\n"
            text += f"Longitude: {packet.longitude:.7f}°\n"

        if packet.altitude_m is not None:
            text += f"Altitude: {packet.altitude_m:.1f} m\n"

        if packet.speed_m_s is not None:
            text += f"Speed: {packet.speed_m_s:.1f} m/s ({packet.speed_m_s*3.6:.1f} km/h)\n"

        if packet.satellites is not None:
            text += f"Satellites: {packet.satellites}\n"

        text += "\nSensor Data:\n"
        if packet.battery_mv is not None:
            text += f"Battery: {packet.battery_mv} mV ({packet.battery_mv/1000:.2f} V)\n"

        if packet.mcu_temp_c is not None:
            text += f"MCU Temperature: {packet.mcu_temp_c:.1f}°C\n"

        buffer.set_text(text)

    def append_packet_log(self, packet):
        """Append packet to the log"""
        buffer = self.packet_log.get_buffer()

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {format_packet(packet)}\n"

        # Append to end
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, log_text)

        # Auto-scroll to bottom
        mark = buffer.get_insert()
        self.packet_log.scroll_mark_onscreen(mark)

        # Limit log size
        line_count = buffer.get_line_count()
        if line_count > 1000:
            start_iter = buffer.get_start_iter()
            delete_end = buffer.get_iter_at_line(line_count - 500)
            buffer.delete(start_iter, delete_end)

    def clear_packet_log(self):
        """Clear the packet log"""
        buffer = self.packet_log.get_buffer()
        buffer.set_text("")

    def update_map_position(self, packet):
        """Update GPS position on map"""
        if packet.latitude is None or packet.longitude is None:
            return

        # Convert packet to JSON for JavaScript
        packet_data = {
            'sequence': packet.sequence,
            'uptime_ms': packet.uptime_ms,
            'latitude': packet.latitude,
            'longitude': packet.longitude,
            'altitude_m': packet.altitude_m,
            'speed_m_s': packet.speed_m_s,
            'satellites': packet.satellites,
            'battery_mv': packet.battery_mv,
            'mcu_temp_c': packet.mcu_temp_c
        }

        # Execute JavaScript to update map
        js_code = f"addPosition({packet.latitude}, {packet.longitude}, {json.dumps(packet_data)});"
        self.webview.run_javascript(js_code)

    def clear_map_track(self):
        """Clear the GPS track on map"""
        js_code = "clearTrack();"
        self.webview.run_javascript(js_code)

    def on_destroy(self, widget):
        """Handle window close"""
        self.running = False
        if self.receiver_process:
            self.receiver_process.terminate()
        Gtk.main_quit()


def main():
    # Enable threading
    GObject.threads_init()

    app = RS41Tracker()
    app.show_all()

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()