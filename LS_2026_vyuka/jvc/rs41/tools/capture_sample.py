#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture RS41 IQ into a persistent sample file")
    parser.add_argument("--freq", type=float, default=433.920e6)
    parser.add_argument("--sample-rate", type=int, default=500000)
    parser.add_argument("--gain", type=float, default=20.0)
    parser.add_argument("--ppm", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument("--output", default="tools/samples/latest_500ksps.cu8")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "rtl_sdr",
        "-f", str(int(args.freq)),
        "-s", str(args.sample_rate),
        "-g", str(args.gain),
        "-n", str(int(args.sample_rate * args.seconds)),
        str(output),
    ]
    if args.ppm:
        cmd[1:1] = ["-p", str(args.ppm)]

    print("capture:", " ".join(cmd), flush=True)
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"saved: {output}", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
