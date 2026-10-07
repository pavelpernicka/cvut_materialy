#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

import genanki


ROOT = Path(__file__).resolve().parents[1]
ANKI_DIR = ROOT / "anki_export"
TSV_PATH = ANKI_DIR / "notes.tsv"
MEDIA_DIR = ANKI_DIR / "media"
APKG_PATH = ANKI_DIR / "SME_otazky_final.apkg"

DECK_ID = 2052701001
MODEL_ID = 2052701002

CSS = """
.card {
  font-family: Arial, sans-serif;
  font-size: 20px;
  line-height: 1.45;
  text-align: left;
  color: #222;
  background: #fff;
}

.section {
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
}

.question {
  font-weight: 700;
  margin-bottom: 12px;
}

.answer {
  margin-top: 8px;
}

.figure {
  margin: 14px 0;
}

.figure img {
  max-width: 100%;
  height: auto;
}

.caption {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

code {
  font-family: "DejaVu Sans Mono", monospace;
}
""".strip()


def load_rows() -> list[tuple[str, str, list[str]]]:
    rows: list[tuple[str, str, list[str]]] = []
    with TSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue
            front = row[0]
            back = row[1]
            tags = row[2].split() if len(row) > 2 and row[2].strip() else []
            rows.append((front, back, tags))
    return rows


def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "SME Basic HTML",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=\"answer\"><div class=\"answer\">{{Back}}</div>",
            }
        ],
        css=CSS,
    )


def main() -> None:
    rows = load_rows()
    model = build_model()
    deck = genanki.Deck(DECK_ID, "SME otázky final")

    for index, (front, back, tags) in enumerate(rows, start=1):
        note = genanki.Note(
            model=model,
            fields=[front, back],
            tags=tags,
            guid=genanki.guid_for("sme_otazky_final", str(index), front),
        )
        deck.add_note(note)

    media_files = sorted(str(path) for path in MEDIA_DIR.iterdir() if path.is_file())
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(APKG_PATH)

    print(f"rows={len(rows)}")
    print(f"media={len(media_files)}")
    print(f"apkg={APKG_PATH}")


if __name__ == "__main__":
    main()
