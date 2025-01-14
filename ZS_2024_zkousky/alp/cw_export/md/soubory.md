# Soubory a streamy

## Streamy

Na cvičení často používáme termíny \"standardní vstup\" a \"standardní
výstup\". Jsou to tzv. streamy (proudy), které vytváří operační systém
pro všechny spouštěné procesy. V dokumentaci typicky najdeme označení
`stdin` a `stdout`, tedy \"standard input\" a \"standard output\". Kromě
těchto dvou streamů existuje ještě třetí, chybový, který se označuje
jako `stderr` a slouží pro chybové výpisy.

V počítačových vědách je stream obecný koncept a existují dva základní
druhy, vstupní a výstupní. Pokud je stream vstupní, lze z něj číst.
Pokud je stream výstupní, lze do něj zapisovat. Pro představu nám může
posloužit například potrubní pošta: z jednoho (vstupního) potrubí
přichází nové zprávy, které můžeme číst, a do jiného (výstupního)
potrubí můžeme své zprávy vhazovat a odesílat je.

V případě třech standardních streamů platí, že `stdin` je vstupní stream
a `stdout` i `stderr` jsou výstupní. To by mělo být konzistentní s vaší
intuicí: vždy jsme ze standardního vstupu četli a výsledky jsme
zapisovali na standardní výstup. Se streamem `stderr` jste se jistě už
také setkali. Pro ilustraci např.:

    >>> 1 / 0
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ZeroDivisionError: division by zero

Chybová hláška \"Traceback \... division by zero\" byla vypsána na
chybový výstup (vizuálně se ale pravděpodobně neliší od standardního
výstupu).

Pokud chceme číst řádky ze vstupního streamu, lze použít `for` cyklus:

``` python
import sys
for line in sys.stdin:
    print("A line from stdin:", line)
```

Po spuštění bude program číst vstup z klávesnice, tak dlouho, dokud
nedojde na konec streamu `stdin`. Konec streamu `stdin` nastane, když se
rozhodneme, že už nechceme zadávat žádný další vstup a stiskneme
`CTRL + D` (Linux, Mac?) nebo `CTRL + Z` (Windows?).

Pro zápis na standardní výstup jsme používali funkci `print`:

``` python
print("Hello world")
```

Pokud bychom chtěli vypsat (z jakéhokoliv důvodu) výstup do jiného
streamu, než je `stdout`, lze použít:

``` python
import sys
print("Hello world", file=sys.stderr)
```

Všimněte si, že argument, který jsme použili, se jmenuje `file`
(soubor). Níže zjistíte proč.

Pro další a detailnější informace viz
[LINFO](http://www.linfo.org/stdio.html).

\<note\> Služby jako Netflix, Spotify, HBO Go aj. se často označují jako
\"streamovací\" služby. V případě těchto služeb nemáte video (nebo zvuk)
uložené u sebe v počítači, ale postupně si stahujete části, které rovnou
přehráváte; jinak (a zjednodušeně) řečeno: čtete ze vstupního streamu.
\</note\>

## Soubory

Existují i jiné streamy než ty standardní. Jako streamy lze vnímat i
soubory: v případě čtení jde o vstupní streamy, v případě zápisu o
výstupní.

Pro získání streamu soubor otevřeme pomocí funkce `open` (viz
[dokumentace](https://docs.python.org/3/library/functions.html#open)).

``` python
f_in = open("cesta/k/souboru.txt", "r") # "r" znamená otevření pro čtení
f_out = open("cesta/k/souboru2.txt", "w") # "w" znamená otevření pro zápis
```

Při otevírání souboru specifikujeme režim, ve kterém chceme soubor
otevřít (dokumentace uvádí i další režimy kromě \"r\" a \"w\").

Nyní lze využívat vše, co jsme si ukázali pro streamy.

``` python
# Čtení řádek ze souboru
f_in = open("cesta/k/souboru.txt", "r")
for line in f_in:
    print(line)
    
# Zápis řádek do souboru
f_out = open("cesta/k/souboru2.txt", "w")
print("Hello world!", file=f_out)
```

### Uzavírání

Předchozí výpis není zcela správně, protože je důležité, abychom soubory
po použití nezapomněli zavřít. K tomu slouží funkce `close`.

``` python
# Čtení řádek ze souboru
f_in = open("cesta/k/souboru.txt", "r")
for line in f_in:
    print(line)
f_in.close()
    
# Zápis řádek do souboru
f_out = open("cesta/k/souboru2.txt", "w")
print("Hello world!", file=f_out)
f_out.close()
```

Otevřením souboru nám operační systém poskytuje své prostředky a
uzavřením je navracíme zpět. Pokud bychom soubory neuzavřeli, můžou se
naše programy chovat neočekávaně (např. ve výstupním souboru chybí
některá data, která jsme určitě zapsali) nebo můžou i selhat (kvůli
nedostatku paměti nebo file descriptorů).

Je potřeba myslet také na následující situace:

``` python
def func():
    f_out = open("cesta/k/souboru2.txt", "w")
    slozity_vypocet_ktery_skonci_chybou()
    f_out.close()
```

Funkce `slozity_vypocet_ktery_skonci_chybou` vyhodí chybu a soubor se
neuzavře (`f_out.close()` se nikdy neprovede). Abychom tomuto předešli,
použijeme tzv. `with` statement a předchozí kód upravíme na:

``` python
def func():
    with open("cesta/k/souboru2.txt", "w") as f_out:
        slozity_vypocet_ktery_skonci_chybou()
```

Python se postará o uzavření souboru za nás.

## Streamy a BRUTE

Vaše domácí úkoly jsou testovány automaticky. BRUTE spustí váš program a
vloží zadání na standardní vstup vašeho programu. Poté čte výsledky ze
standardního výstupu vašeho programu a porovnává je se správnými
výsledky. Proto následující řešení nebude hodnoceno jako korektní:

``` python
# volání input("Enter number:") zapíše řetězec "Enter number:" na standardní výstup
number = int(input("Enter number:"))
result = compute_result(number)
print(result)
```

## Pole v souboru

### Čísla oddělená mezerou

Mějme soubor `pole.txt` obsahující čísla oddělená mezerou:

    1 3 5 -4 2 5 3

Pro načtení lze použít

``` python
with open("pole.txt", "r") as f:
    line = f.readline()          # line = "1 3 5 -4 2 5 3\n"

# Zde už je soubor uzavřený
words = line.split()             # words = ["1", "3", "5", "-4", "2", "5", "3"]
pole = list(map(int, words))     # pole = [1, 3, 5, -4, 2, 5, 3]


# To samé, ale úspornější zápis
with open("pole.txt", "r") as f:
    pole = list(map(int, f.readline().split()))
```

### Čísla oddělená novým řádkem

Mějme soubor `pole.txt` obsahující čísla oddělená novým řádkem:

    1
    3
    5
    -4
    2
    5
    3

Pro načtení lze použít

``` python
pole = []
with open('pole.txt', 'r') as f:
    for line in f:
        pole.append(int(line))

# To samé, ale úspornější zápis
with open('pole.txt', 'r') as f:
    pole = [int(line) for line in f]
```

### Dvourozměrné pole

Mějme soubor `pole.txt` obsahující řádky matice oddělené novým řádkem:

    1 3 5
    -4 2 5

Pro načtení lze použít

``` python
with open("pole.txt", "r") as f:
    pole = [list(map(int, line.split())) for line in f]
```
