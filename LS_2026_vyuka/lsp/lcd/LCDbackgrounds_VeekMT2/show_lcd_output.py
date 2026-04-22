#!/usr/bin/env python3

import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
WIDTH = 800
HEIGHT = 480
TEXT_OUTPUT = os.path.join(ROOT, "simulation", "testbenchLCD.txt")
IMAGE_OUTPUT = os.path.join(ROOT, "simulation", "testbenchLCD.ppm")


def read_rows():
    if not os.path.exists(TEXT_OUTPUT) or os.path.getsize(TEXT_OUTPUT) == 0:
        raise SystemExit("missing simulation output")

    rows = []
    row = None
    last = 0

    with open(TEXT_OUTPUT, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("## "):
                continue
            if line.startswith("##="):
                if row is not None:
                    rows.append(row)
                row = []
                last = 0
                continue
            if line.startswith("##"):
                continue
            if line.startswith("*"):
                row.extend([last] * int(line[1:]))
                continue
            last = int(line)
            row.append(last)

    if row is not None:
        rows.append(row)

    if len(rows) < HEIGHT:
        raise SystemExit("image has too few rows")

    return rows


def write_ppm(rows):
    rgb = bytearray()
    for y in range(HEIGHT):
        row = rows[y]
        if len(row) < WIDTH:
            raise SystemExit("image row is too short")
        for x in range(WIDTH):
            color = row[x]
            rgb.extend(((color >> 16) & 255, (color >> 8) & 255, color & 255))

    with open(IMAGE_OUTPUT, "wb") as handle:
        handle.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        handle.write(rgb)


def open_image():
    for cmd in ("xdg-open", "open"):
        if shutil_which(cmd):
            subprocess.Popen([cmd, IMAGE_OUTPUT], cwd=ROOT)
            return
    raise SystemExit("no image opener found")


def shutil_which(name):
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def main():
    no_open = "--no-open" in sys.argv[1:]

    rows = read_rows()
    write_ppm(rows)
    print(os.path.relpath(IMAGE_OUTPUT, ROOT))

    if not no_open:
        open_image()


if __name__ == "__main__":
    main()
