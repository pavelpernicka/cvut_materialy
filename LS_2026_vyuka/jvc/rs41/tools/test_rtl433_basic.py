#!/usr/bin/env python3
"""
Basic RTL_433 FSK test - simpler approach to verify FSK detection works
"""

import subprocess
import sys
import signal


def test_rtl433_fsk():
    """Test basic RTL_433 FSK detection without custom decoder"""

    cmd = [
        "rtl_433",
        "-f", "433920000",        # 433.920 MHz
        "-s", "250000",           # 250k sample rate
        "-Y", "minmax",           # FSK detector
        "-Y", "level=-8.0",       # Detection level
        "-F", "json",             # JSON output
        "-M", "time:local",       # Add timestamps
        "-M", "level",            # Add signal levels
        "-v"                      # Verbose for debugging
    ]

    print("Testing basic RTL_433 FSK detection...")
    print("Command:", " ".join(cmd))
    print("Listening for ANY FSK signals at 433.920 MHz...")
    print("Press Ctrl+C to stop\n")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        def signal_handler(signum, frame):
            print("\nStopping...")
            process.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Print all output to see what's detected
        for line in process.stdout:
            print(line.rstrip())

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(test_rtl433_fsk())