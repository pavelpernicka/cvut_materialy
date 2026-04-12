#!/usr/bin/env python3

import argparse
from pathlib import Path
import signal
import subprocess
import sys


def build_rtl_fm_command(args: argparse.Namespace) -> list[str]:
    command = [
        args.rtl_fm_bin,
        "-f",
        f"{args.freq:.0f}",
        "-M",
        "fm",
        "-s",
        str(args.audio_rate),
        "-g",
        str(args.gain),
        "-A",
        "fast",
        "-E",
        "dc",
    ]
    if args.ppm:
        command.extend(["-p", str(args.ppm)])
    command.append("-")
    return command


def build_direwolf_command(args: argparse.Namespace) -> list[str]:
    return [
        args.direwolf_bin,
        "-c",
        args.direwolf_config,
        "-q",
        args.quiet,
        "-r",
        str(args.audio_rate),
        "-b",
        "16",
        "-B",
        "1200",
        "-n",
        "1",
        "-",
    ]


def main() -> int:
    default_config = Path(__file__).with_name("direwolf.conf")
    parser = argparse.ArgumentParser(description="Receive APRS from the RS41 firmware using rtl_fm piped into Dire Wolf")
    parser.add_argument("--freq", type=float, default=433.920e6)
    parser.add_argument("--gain", type=float, default=20.0)
    parser.add_argument("--ppm", type=int, default=0)
    parser.add_argument("--audio-rate", type=int, default=24000)
    parser.add_argument("--rtl-fm-bin", default="rtl_fm")
    parser.add_argument("--direwolf-bin", default="direwolf")
    parser.add_argument("--direwolf-config", default=str(default_config))
    parser.add_argument("--quiet", default="h", help="Dire Wolf quiet flags, default keeps decoded packets visible")
    args = parser.parse_args()

    rtl_fm_command = build_rtl_fm_command(args)
    direwolf_command = build_direwolf_command(args)

    print("rtl_fm:", " ".join(rtl_fm_command), file=sys.stderr, flush=True)
    print("direwolf:", " ".join(direwolf_command), file=sys.stderr, flush=True)

    try:
        rtl_fm = subprocess.Popen(rtl_fm_command, stdout=subprocess.PIPE, stderr=None)
    except FileNotFoundError:
        print(f"rtl_fm binary not found: {args.rtl_fm_bin}", file=sys.stderr, flush=True)
        return 1

    if rtl_fm.stdout is None:
        print("rtl_fm stdout pipe was not created", file=sys.stderr, flush=True)
        rtl_fm.terminate()
        return 1

    try:
        direwolf = subprocess.Popen(direwolf_command, stdin=rtl_fm.stdout, stderr=None)
    except FileNotFoundError:
        rtl_fm.terminate()
        rtl_fm.wait(timeout=2)
        print(f"direwolf binary not found: {args.direwolf_bin}", file=sys.stderr, flush=True)
        return 1

    rtl_fm.stdout.close()

    def stop_handler(_signum, _frame):
        if rtl_fm.poll() is None:
            rtl_fm.terminate()
        if direwolf.poll() is None:
            direwolf.terminate()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    direwolf_return = direwolf.wait()
    if rtl_fm.poll() is None:
        rtl_fm.terminate()
    try:
        rtl_fm.wait(timeout=2)
    except subprocess.TimeoutExpired:
        rtl_fm.kill()
        rtl_fm.wait(timeout=2)

    return direwolf_return


if __name__ == "__main__":
    raise SystemExit(main())
