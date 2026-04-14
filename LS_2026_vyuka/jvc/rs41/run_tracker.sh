#!/bin/bash
# RS41 GTK Tracker Launcher

cd "$(dirname "$0")"

echo "Starting RS41 Radiosonde GTK Tracker..."
echo "Frequency: 433.92 MHz"
echo "Gain: 20 dB"
echo ""
echo "Make sure your RTL-SDR dongle is connected!"
echo ""

python3 rs41_gtk_tracker.py