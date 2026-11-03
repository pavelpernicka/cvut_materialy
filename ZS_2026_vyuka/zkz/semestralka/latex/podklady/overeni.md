# Ověření aktuální revize

- Návrh: jeden NE555P, D1 1N4148, R1 3,3 kΩ, P1 25 kΩ, R2 221 kΩ, C1 120 nF.
- Schéma: všech osm vývodů U1; propojení jezdce W a konce B potenciometru; dioda anodou na pin 7, katodou na piny 2/6; společná zem a blokování.
- Výpočet ověřen Pythonem: pro model konstantního úbytku diody 0,6 V násobitel 0,940983; rozsah pulzu 0,3726–3,1956 ms; ideální mezera 18,3823 ms.
- Po nastavení pulzů 0,5–2,5 ms nominální frekvence 52,96–47,89 Hz. Nejde o simulaci reálného NE555 ani měření; je nutná kalibrace a ověření kompatibility konkrétního serva.
- Program Arduina nebyl touto revizí změněn. Dříve byl přeložen pro arduino:avr:uno, AVR core 1.8.8, Servo 1.3.0.
- Fyzické měření serva ani obvodu nebylo provedeno.
- Aktuální PDF: 30 stran, šest kapitol; překlad pdfLaTeX/Biber bez varování, nedefinovaných odkazů a přetečených boxů.
- Regulace je oddělena od pěti pododdílů snímačů (princip, použití, přednosti a omezení). Optický enkodér zahrnuje kvadraturu A/B, směr, index Z a vyhodnocení ×4.
- Resolver a indukční snímač mají převzaté ilustrace principu od Novanta a TI; doplněno srovnání konstrukcí.
- Běžné modely: SG90 Digital, MG90S, MG996R 180°. Parametry 180° varianty jsou odděleny od obecného katalogového listu MG996R s rozsahem 120°. Pulzy 500–2500 µs jsou ukázkové meze, nikoli zaručená specifikace všech kusů.
- Bibliografie obsahuje 36 citovaných položek: 24 technických a 12 obrazových. Ověřena úplnost citací, existence všech obrázků a absence opakovaných fotografií.
- Vizuálně zkontrolovány stránky dokumentu, samostatně zejména snímače, tabulky a zapojení. Upraveno stránkování a společná sazba tabulky a fotografie MG996R.
- Program změněn pouze v komentáři; časování NE555 a hodnoty jeho součástek zůstávají stejné. Hardware nebyl měřen.

- Obrázek 5.1: upraveno rozložení úplného zapojení, popisky mimo součástky, samostatný návrat země Arduina do G0 a přehledné blokování napájení serva. Zkontrolována výsledná stránka PDF; překlad bez varování.

- Napájení sjednoceno na stabilizovaný zdroj 5 V / alespoň 4 A. Arduino přes pin 5V, při provozu bez USB; před programováním odpojit externí zdroj i 5V přívod desky. Silový proud serva obchází Arduino. Sériová D2 odstraněna kvůli úbytku napětí; polaritu zajišťuje nezáměnný konektor. Ověření napětí pod zátěží zůstává podmínkou realizace.
- Optické snímání: převzatý obrázek principu Nidec a vlastní průběhy A/B s posunem T/4, oběma směry a posloupností stavů. Vizuálně ověřena sazba dotčených stránek a úplnost citací; překlad bez varování.
