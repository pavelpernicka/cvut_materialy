#!/usr/bin/env python3

from pathlib import Path


def main() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "web"
    print(f"Web assets are currently served as source files from {web_dir}")
    print("Next step: gzip assets and generate main/web_assets.c for embedded serving.")


if __name__ == "__main__":
    main()
