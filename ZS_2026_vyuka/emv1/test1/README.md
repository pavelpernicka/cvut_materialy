# EMV1 – otázky, LaTeX a Anki

Stručné odpovědi na všech 66 otázek z `otazky.md`, založené výhradně na sedmi dodaných přednáškách. PDF obsahuje pouze otázky, odpovědi a související obrázky. Anki má jednu kartu na otázku, vzorce přes MathJax a obrázky vložené do balíčku.

## Struktura projektu

- `Přednáška *.pdf`: původní podklady, ponechané beze změn.
- `otazky.md`: původní zadání a pořadí otázek.
- `latex/otazky/q01.tex` až `q66.tex`: jediný zdroj textů odpovědí pro PDF i Anki.
- `latex/emv1_otazky.tex`: hlavní dokument, obnovovaný sestavovacím skriptem.
- `latex/obrazky/`: 54 použitých obrázků v PDF a dva editovatelné zdroje TikZ.
- `anki/media/`: stejných 54 obrázků v PNG pro Anki.
- `scripts/metadata.json`: zadání, názvy, odkazy na přednášky a přiřazení obrázků.
- `scripts/obrazky.json`: původ, popisky a provedené úpravy obrázků.
- `scripts/overeni_obsahu.json`: záznam ruční kontroly obsahu a pokrytí zadání, včetně kontrolních součtů odpovědí.
- `video/`: sedm českých Manim videí podle přednášek, scénáře a reprodukovatelná výroba; postup viz [video/README.md](video/README.md).

Do Gitu patří přednášky, zadání, LaTeX, používané obrázky, metadata a skripty. `.gitignore` vyřazuje hotové exporty, pracovní adresář `tmp`, výsledky kontrol a místní prostředí. PDF obrázky jsou verzované; běžné sestavení je znovu nevyřezává.

## Sestavení

Potřebujete Python 3, Pandoc a XeLaTeX s českým Babelem, fonty TeX Gyre Pagella a Lato a balíčky používanými v hlavním dokumentu (`amsmath`, `amssymb`, `graphicx`, `xcolor`, `enumitem`, `titlesec`, `hyperref`, `fontspec`, `geometry`).

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r scripts/requirements.txt
bash scripts/sestavit.sh
```

Výsledky:

- `output/pdf/EMV1_otazky.pdf`: dokument s odpověďmi, aktuálně 28 stran.
- `anki/EMV1_Test1.apkg`: 66 karet v sedmi tematických podbalíčcích, včetně médií.
- `anki/EMV1_Test1.tsv`: alternativní textový export bez přibalených médií a šablony.
- `output/export_audit.json`: počty karet a médií při sestavení.

V Anki zvolte **Soubor → Importovat** a vyberte APKG. Ruční kopírování obrázků ani instalace TeXu pro zobrazení vzorců nejsou potřeba. Identifikátory poznámek zůstávají při opakovaném exportu stabilní; aktualizaci existujících karet řídí nastavení importu Anki.

## Úpravy

Text upravujte v `latex/otazky/qNN.tex`, výběr obrázků a odkazy v `scripts/metadata.json`. Potom znovu spusťte sestavení. Ruční změny hlavního souboru `latex/emv1_otazky.tex` by sestavení přepsalo; sazbu upravujte v `scripts/sestavit.py`.

Samotné PDF lze bez Pythonu a Pandocu sestavit také přímo:

```sh
mkdir -p tmp/pdfs
cd latex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=../tmp/pdfs emv1_otazky.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=../tmp/pdfs emv1_otazky.tex
```

## Obnova obrázků a kontrola

Pro obnovu obrázků z původních přednášek spusťte ve virtuálním prostředí:

```sh
python scripts/vyrezy.py
bash scripts/sestavit.sh
```

Obnova navíc potřebuje TikZ a `standalone`. Skript kontroluje ořezy rozpoznaných slov, přidává okraj a ukládá výsledek do `output/overeni_orezu.json`. Po změně ořezů je nutná i vizuální kontrola obrázků.

Paschenova křivka (`emv1_p3_s66.tex`) je čitelně překreslena podle P3, s. 66. Viskozitní křivka (`emv1_p4_s41.tex`) vychází z P4, s. 40–41; názvy hranic tvarování jsou sjednoceny podle tabulky na s. 40. Obě schémata mají schematické vodorovné osy. Ostatní obrázky jsou výřezy; úpravy okolního textu se provádějí jen v pracovní kopii, nikoliv v původních PDF.

Volitelný test importu do dočasné kolekce vyžaduje Python s dostupným modulem `anki`:

```sh
python scripts/overit_anki.py
```

Kontroluje počet karet, jejich číslování a přítomnost médií. Výsledek ukládá do `output/overeni_anki.json`.

## Zdroje a rozsah ověření

P1–P7 označují přednášky podle čísla v názvu; čísla stran jsou pořadím stran původního PDF od 1. Autorem přednášek je Ing. Ladislav Chladil, Ph.D. Původní odkazy převzatých obrázků zůstávají v přednáškách.

Ruční kontrola všech 66 odpovědí je zaznamenána v `scripts/overeni_obsahu.json`; po obsahové změně je potřeba příslušný záznam znovu ověřit. U otázky 65 prezentace neuvádí kmitočtový zákon ztrát magnetickým zpožděním, což odpověď přiznává. Nejasná „magnetizační smyčka“ v otázce 61 je podle navazujících snímků vyložena jako křivka prvotní magnetizace.

Před úklidem projektu bylo vizuálně zkontrolováno všech 28 stran a všech 66 karet v prohlížeči: 228 matematických výrazů, 54 obrázků a devět kontrol při mobilní šířce, bez zjištěných chyb. AnkiDroid ani AnkiMobile nebyly přímo testovány.

Po úklidu byla ověřena obnova obrázků, sestavení PDF a import Anki z čisté kopie souborů určených pro Git, bez pracovních dat a předchozích exportů. Všech 28 stran PDF bylo pixelově shodných s předchozí verzí; texty, média a identifikátory 66 karet zůstaly stejné.
