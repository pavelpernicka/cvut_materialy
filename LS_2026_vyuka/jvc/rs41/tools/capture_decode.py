#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture RS41 IQ with rtl_sdr and decode it offline.")
    parser.add_argument("--freq", type=float, default=433.920e6)
    parser.add_argument("--sample-rate", type=int, default=500000)
    parser.add_argument("--gain", type=float, default=20.0)
    parser.add_argument("--ppm", type=int, default=0)
    parser.add_argument("--center", type=float, default=0.0563)
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument("--output", default="tools/samples/latest_500ksps.cu8")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    iq_path = Path(args.output)
    iq_path.parent.mkdir(parents=True, exist_ok=True)

    capture_cmd = [
        "rtl_sdr",
        "-f", str(int(args.freq)),
        "-s", str(args.sample_rate),
        "-g", str(args.gain),
        "-n", str(int(args.sample_rate * args.seconds)),
        str(iq_path),
    ]
    if args.ppm:
        capture_cmd[1:1] = ["-p", str(args.ppm)]

    print("capture:", " ".join(capture_cmd), file=sys.stderr, flush=True)
    capture = subprocess.run(capture_cmd)
    if capture.returncode != 0:
        return capture.returncode

    decode_cmd = [
        sys.executable,
        str(Path(__file__).with_name("rx.py")),
        "--sample-rate", str(args.sample_rate),
        "--center", str(args.center),
        "--input-file", str(iq_path),
    ]
    if args.verbose:
        decode_cmd.append("--verbose")
    print("decode:", " ".join(decode_cmd), file=sys.stderr, flush=True)
    return subprocess.run(decode_cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
