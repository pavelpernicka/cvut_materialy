#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
RTL_RFM_DIR = Path(__file__).resolve().parent / "rtl_rfm_rs41"
RTL_RFM_BIN = RTL_RFM_DIR / "rtl_rfm_rs41"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Receive RS41 telemetry using the adapted RTL-RFM backend.")
    parser.add_argument("--freq", type=float, default=433.92e6, help="Signal frequency in Hz.")
    parser.add_argument("--gain", type=float, default=15.0, help="RTL-SDR gain in dB.")
    parser.add_argument("--ppm", type=int, default=0, help="RTL-SDR ppm correction.")
    parser.add_argument("--quiet", action="store_true", help="Only print decoded packets.")
    parser.add_argument("--debugplot", action="store_true", help="Enable RTL-RFM debug waveform output.")
    return parser.parse_args(argv)


def ensure_built() -> None:
    subprocess.run(["make", "-C", str(RTL_RFM_DIR)], check=True, cwd=ROOT_DIR)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_built()

    cmd = [
        str(RTL_RFM_BIN),
        "-f",
        str(int(args.freq)),
        "-g",
        f"{args.gain:.1f}",
    ]
    if args.ppm:
        cmd.extend(["-p", str(args.ppm)])
    if args.quiet:
        cmd.append("-q")
    if args.debugplot:
        cmd.append("-d")

    print("rtl_rfm_rs41:", " ".join(cmd), file=sys.stderr, flush=True)
    os.execv(cmd[0], cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
