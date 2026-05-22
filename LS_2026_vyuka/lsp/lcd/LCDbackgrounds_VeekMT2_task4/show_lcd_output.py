#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
WIDTH = 800
HEIGHT = 480
TEXT_OUTPUT = os.path.join(ROOT, "simulation", "testbenchLCD.txt")
IMAGE_OUTPUT = os.path.join(ROOT, "simulation", "testbenchLCD.ppm")
FRAMES_DIR = os.path.join(ROOT, "simulation", "frames")
VIDEO_OUTPUT = os.path.join(ROOT, "simulation", "testbenchLCD.mp4")


def read_frames():
    if not os.path.exists(TEXT_OUTPUT) or os.path.getsize(TEXT_OUTPUT) == 0:
        raise SystemExit("missing simulation output")

    frames = []
    rows = []
    row = None
    last = 0

    with open(TEXT_OUTPUT, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("## "):
                continue
            if line.startswith("##="):
                if line == "##=0,0" and rows:
                    if len(rows) >= HEIGHT:
                        frames.append(rows[:HEIGHT])
                    rows = []
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
    if len(rows) >= HEIGHT:
        frames.append(rows[:HEIGHT])

    if not frames:
        raise SystemExit("no complete frame found")

    return frames


def write_ppm(rows, path):
    rgb = bytearray()
    for y in range(HEIGHT):
        row = rows[y]
        if len(row) < WIDTH:
            raise SystemExit("image row is too short")
        for x in range(WIDTH):
            color = row[x]
            rgb.extend(((color >> 16) & 255, (color >> 8) & 255, color & 255))

    with open(path, "wb") as handle:
        handle.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        handle.write(rgb)


def write_all_frames(frames):
    os.makedirs(FRAMES_DIR, exist_ok=True)
    for name in os.listdir(FRAMES_DIR):
        if name.endswith(".ppm"):
            os.unlink(os.path.join(FRAMES_DIR, name))

    for index, frame in enumerate(frames, start=1):
        path = os.path.join(FRAMES_DIR, f"frame_{index:03d}.ppm")
        write_ppm(frame, path)


def write_video(fps):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found")

    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        os.path.join(FRAMES_DIR, "frame_%03d.ppm"),
        "-pix_fmt",
        "yuv420p",
        VIDEO_OUTPUT,
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)


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
    all_frames = "--all-frames" in sys.argv[1:]
    make_video = "--video" in sys.argv[1:]
    fps = 6

    if "--fps" in sys.argv[1:]:
        pos = sys.argv.index("--fps")
        try:
            fps = int(sys.argv[pos + 1])
        except (IndexError, ValueError):
            raise SystemExit("invalid --fps value")

    frames = read_frames()

    if all_frames or make_video:
        write_all_frames(frames)
        print(os.path.relpath(FRAMES_DIR, ROOT))
        if make_video:
            write_video(fps)
            print(os.path.relpath(VIDEO_OUTPUT, ROOT))
        return

    write_ppm(frames[0], IMAGE_OUTPUT)
    print(os.path.relpath(IMAGE_OUTPUT, ROOT))

    if not no_open:
        open_image()


if __name__ == "__main__":
    main()
