#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Decode a previously saved RS41 IQ sample.")
    parser.add_argument("--input-file", default="tools/samples/latest_500ksps.cu8")
    parser.add_argument("--sample-rate", type=int, default=500000)
    parser.add_argument("--center", type=float, default=0.0563)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(Path(__file__).with_name("rx.py")),
        "--sample-rate", str(args.sample_rate),
        "--center", str(args.center),
        "--input-file", args.input_file,
    ]
    if args.verbose:
        cmd.append("--verbose")

    print("decode:", " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
