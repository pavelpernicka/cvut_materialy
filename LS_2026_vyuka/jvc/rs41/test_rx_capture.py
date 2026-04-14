#!/usr/bin/env python3
"""Test script to capture rx.py output"""

import subprocess
import os
import sys
from pathlib import Path

def test_rx_capture():
    print("Testing rx.py output capture...")

    cmd = [
        "python3",
        "tools/rx.py",
        "--freq", "433.92e6",
        "--gain", "20"
    ]

    print(f"Running: {' '.join(cmd)}")

    # Try using unbuffered mode and pty
    import pty
    import select

    # Create a pseudo-terminal
    master, slave = pty.openpty()

    process = subprocess.Popen(
        cmd,
        stdout=slave,
        stderr=slave,
        stdin=subprocess.DEVNULL,
        cwd=Path(__file__).parent,
        env=dict(os.environ, PYTHONUNBUFFERED='1')
    )

    os.close(slave)  # Close slave end in parent

    print(f"Process started with PID: {process.pid}")
    line_count = 0

    try:
        while process.poll() is None:
            # Check if there's data to read
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    data = os.read(master, 1024)
                    if data:
                        text = data.decode('utf-8', errors='ignore')
                        lines = text.split('\n')
                        for line in lines:
                            if line.strip():
                                line_count += 1
                                print(f"[{line_count:03d}] {line}")

                                # Look for packet data
                                if 'seq=' in line:
                                    print(f"*** PACKET FOUND: {line}")
                except OSError:
                    break

        print(f"Process ended. Total lines: {line_count}")

    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        process.terminate()
        os.close(master)

if __name__ == "__main__":
    test_rx_capture()