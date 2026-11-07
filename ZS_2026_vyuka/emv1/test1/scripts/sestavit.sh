#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
mkdir -p tmp/pdfs output/pdf anki
python3 scripts/sestavit.py
(
  cd latex
  xelatex -interaction=nonstopmode -halt-on-error -output-directory=../tmp/pdfs emv1_otazky.tex
  xelatex -interaction=nonstopmode -halt-on-error -output-directory=../tmp/pdfs emv1_otazky.tex
)
cp tmp/pdfs/emv1_otazky.pdf output/pdf/EMV1_otazky.pdf
