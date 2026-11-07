# Ověření zkrácené verze – 2026-11-03

- Výstup má 19 stran celkem včetně titulní strany, obsahu, literatury a zdrojů obrázků. Původní verze měla 30 stran.
- Zachováno šest kapitol zadání, obecná regulace a snímače, běžné RC modely, návrh 0–180°, jeden NE555, Arduino s programem, napájení a zemní smyčky.
- Odstraněny opakované výklady, vedlejší rozbory a duplicitní ilustrace. Písmo a základní okraje nebyly zmenšeny.
- Překlad pdfLaTeX/Biber bez varování, přetečených boxů a nedefinovaných odkazů. Ověřena existence vstupních souborů a obrázků.
- Bibliografie: 33 citovaných položek, z toho 9 obrazových. Nejsou nepoužité bibliografické záznamy ani opakované převzaté obrázky.
- Vizuálně zkontrolovány všechny stránky zkrácené verze; po závěrečné úpravě samostatně zkontrolovány změněné stránky návrhu zapojení.
- Napájení: společný stabilizovaný zdroj 5 V / alespoň 4 A, samostatné přívody a návraty do G0. Arduino přes pin 5V; před programováním odpojit externí zdroj i 5V přívod. Provoz bez USB.
- Časování NE555 ani funkční kód Arduina se krácením nezměnily. Dřívější překlad programu: arduino:avr:uno, AVR core 1.8.8, Servo 1.3.0; v této revizi neopakován.
- Hardware nebyl změřen; kalibrace pulzů, napětí pod zátěží a ověření jištění zůstávají podmínkou realizace.

## Rozšíření přehledu serv

- Sekce 1.3 má šest podsekcí: modelářská polohová, průmyslová, kontinuální, převodovaná, přímá a lineární serva. Uvedena jsou odlišná hlediska dělení.
- Čtyři fotografie jsou vedle příslušného výkladu, dvě byly doplněny ze zdokumentovaných internetových zdrojů.
- Po překladu vizuálně ověřeny změněné stránky 6–7 PDF. Překlad bez varování a přetečených či nedoplněných boxů; všech 33 bibliografických záznamů je citováno.

- Opraveno odsazení sekce 1.3: podnadpisy mimo minipage mají standardní mezery, text a fotografie jsou zarovnány nahoru. Vizuální kontrola stran 6–7, celkem stále 19 stran; překlad bez varování.
