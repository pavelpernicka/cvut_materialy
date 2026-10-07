#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SRC_DIR="$ROOT_DIR/anki_export/media"
DEFAULT_DST="$HOME/.local/share/Anki2/Uživatel 1/collection.media"
DST_DIR="${1:-$DEFAULT_DST}"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "Missing source media directory: $SRC_DIR" >&2
  exit 1
fi

mkdir -p "$DST_DIR"
cp --update=none "$SRC_DIR"/* "$DST_DIR"/

echo "Copied media from:"
echo "  $SRC_DIR"
echo "to:"
echo "  $DST_DIR"
