#!/usr/bin/env python3
"""
Simple RTL_433 FSK receiver without complex flexible decoder
Just detects basic FSK patterns and shows raw data
"""

import subprocess
import sys
import signal
import json


def main():
    print("Simple RTL_433 FSK receiver for 433.920 MHz")
    print("This version just detects any FSK activity and shows raw data")
    print("Press Ctrl+C to stop\n")

    # Simple rtl_433 command without custom decoder
    cmd = [
        "rtl_433",
        "-f", "433920000",      # 433.920 MHz
        "-s", "250000",         # 250k sample rate (good for 1200 bps)
        "-Y", "minmax",         # FSK detector
        "-Y", "level=-10.0",    # More sensitive detection level
        "-Y", "minsnr=10.0",    # Minimum SNR
        "-F", "json",           # JSON output
        "-F", "log",            # Console log output
        "-M", "time:local",     # Timestamps
        "-M", "level",          # Signal levels
        "-M", "bits",           # Show bit patterns
    ]

    # Add a simple flexible decoder for any FSK patterns
    simple_decoder = "n=FSK_Test,m=FSK_PCM,s=200,l=800,r=5000,g=2000,t=200,bits>=8"
    cmd.extend(["-X", simple_decoder])

    print("Command:", " ".join(cmd))
    print()

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
        signal.signal(signal.SIGTERM, signal_handler)

        detection_count = 0

        # Read all output
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            # Try to parse JSON
            try:
                data = json.loads(line)
                if "model" in data:
                    detection_count += 1
                    print(f"[{detection_count}] DETECTED: {data}")
            except json.JSONDecodeError:
                # Non-JSON output (status messages)
                if any(keyword in line.lower() for keyword in ["found", "signal", "level", "snr", "detected"]):
                    print(f"STATUS: {line}")

    except KeyboardInterrupt:
        print(f"\nDetected {detection_count} FSK signals")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    finally:
        try:
            process.terminate()
            process.wait(timeout=2)
        except:
            pass

    return 0


if __name__ == "__main__":
    # Quick device check
    try:
        result = subprocess.run(
            ["rtl_433", "-f", "433920000"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if "No supported devices found" in result.stderr:
            print("ERROR: No RTL-SDR device found!")
            print("Please connect an RTL-SDR device")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        # Good - means device is probably available
        pass
    except Exception as e:
        print(f"Could not check device: {e}")
        print("Proceeding anyway...")

    sys.exit(main())