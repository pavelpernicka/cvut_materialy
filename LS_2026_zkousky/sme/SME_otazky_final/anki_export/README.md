Anki export z `main.tex`.

Obsah:
- `notes.tsv` obsahuje 190 kartiček ve formátu `Front<TAB>Back<TAB>Tags`.
- `media/` obsahuje 96 obrázků použitých na kartičkách.
- `media_files.txt` je seznam médií.
- `SME_otazky_final.apkg` je hotový Anki balík pro přímý import včetně médií.

Import do Anki:
1. Nejsnazší varianta: importujte přímo `SME_otazky_final.apkg`.
2. Alternativně můžete použít ruční import přes `notes.tsv`.
3. V Anki vytvořte nebo použijte typ poznámky `Basic`.
4. Pole namapujte takto: sloupec 1 `Front`, sloupec 2 `Back`, sloupec 3 `Tags`.
5. V importu zapněte `Allow HTML in fields`.
6. Před importem nebo po něm nahrajte obrázky do `collection.media` vašeho Anki profilu.
7. V tomto repu na to je skript:

```bash
./scripts/install_anki_media.sh
```

8. Výchozí cíl skriptu je `~/.local/share/Anki2/Uživatel 1/collection.media`.
9. Pokud máte jiný profil, předejte cílovou složku jako argument:

```bash
./scripts/install_anki_media.sh "~/.local/share/Anki2/MujProfil/collection.media"
```

Matematika:
- Kartičky používají MathJax zápis `\(...\)` a `\[...\]`, který Anki umí bez další konfigurace.

Doporučené CSS pro typ poznámky:

```css
.card {
  font-family: "Arial", sans-serif;
  font-size: 20px;
  line-height: 1.45;
  text-align: left;
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
```
