# Servomotory – semestrální práce

Hlavní soubor je `main.tex`, výstup `semestralni-prace.pdf`.

## Překlad

Projekt používá pdfLaTeX, český Babel, TikZ/CircuitikZ, Biber a biblatex-iso690.
Ve složce `latex` spusťte `make`. Na Overleafu zvolte `main.tex` a pdfLaTeX.
Obrázky jsou uložené lokálně; překlad nepotřebuje přístup k internetu.

## Struktura

- `kapitoly/`: šest kapitol podle zadání.
- `obrazky/`: vlastní schémata a diagramy; `foto/` obsahuje převzaté ilustrace a `zdroje.json`.
- `literatura.bib`: citované podklady; záznamy s klíčovým slovem `obrazek` patří do seznamu zdrojů obrázků.
- `kod/servo_potenciometr/`: program pro Arduino Uno R3, vložený také do dokumentu.
- `styl.tex`, `titulni-strana.tex`: sazba a titulní strana.
- `podklady/`: použití zdrojů a záznam ověření.
- `build/`: pomocné výstupy, nejsou součástí archivu projektu.

## Návrh

Zvolený pohon je MG996R v polohovém provedení 180°. Pulzy 500–2500 µs jsou návrhové meze, které je nutné kalibrovat pro skutečný kus. Analogový ovladač používá
jeden NE555P a diodu 1N4148; šířka pulzu i perioda vyžadují ověření a kalibraci.
Druhou variantou je Arduino s potenciometrem. Obě varianty využívají společný stabilizovaný zdroj 5 V / alespoň 4 A pro řízení i servo, se samostatnými přívody. Arduino se napájí pinem 5V; při programování se externí 5V přívod odpojí před připojením USB. PWM expandér je vysvětlen jako
obecná možnost rozšíření na více serv. Program nepředstírá měření skutečné polohy.

Práce obsahuje návrh, nikoli vlastní měření hardwaru. Zdrojové dokumenty jsou
v části Literatura, převzaté fotografie v části Zdroje obrázků.
Vlastní schémata nepotřebují externí obrazový zdroj. Původní `seminarka.pdf`
nebyla změněna.
