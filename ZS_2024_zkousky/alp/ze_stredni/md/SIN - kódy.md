# SIN - kódy
## Příklady
```python=
#!/usr/bin/env python3
import sys
import random

op = []
znaky = ["+", "-", "*", "/"]
hodnoceni = ["hrůza", "uč se", "za 3", "ještě trénuj", "paráda"]
x = 0
ok = 0

def exitp():
    print("Ukončení")
    if x>0:
        proc = int(ok/x*100)
        print("-----------")
        print("Statistiky: ")
        print("Celkem příkladů:", x)
        print("Celkem správně:", ok)
        print("Procento:", proc, "%")
        print("Hodnocení:", hodnoceni[int(proc/(100/len(hodnoceni)))])
    sys.exit()

def numinput(txt):
    try:
        i = input(txt)
        if(i == "exit"):
            exitp()
        return(int(i))
    except ValueError:
        print("Zadejte numerickou hodnotu!")
        return(numinput(txt))

def gen(maxnum, oper, resmax):
    if(oper==0): #scitani
        n = random.randint(1, maxnum)
        res = random.randint(n, resmax)
        m = res-n
    elif(oper==1): #odcitani
        n = random.randint(1, resmax)
        m = random.randint(0, n)
        res = n-m
    elif(oper==2): #nasobeni
        n = random.randint(1, maxnum)
        res = random.randint(0, resmax)
        res = res-(res%n)
        m = res/n
    else: #deleni
        n = random.randint(0, resmax)
        m = random.randint(1, maxnum)
        n = n-(n%m)
        res = n/m
    zadani = "{}{}{}=".format(int(n), znaky[oper], int(m))
    return zadani, int(res)

if __name__ == '__main__':
    try:
        print("Vítej v trenažéru příkladů. Níže prosím zadej maximální číslo, se kterým umíš počítat. Pokud kdykoliv napíšeš \"exit\", program se ukončí")
        maxnum = numinput("Maximální číslo: ")
        resmax = numinput("Maximální výsledek/jmenovatel: ")
        print("Dále zadej operaci, kterou chceš trénovat. Můžeš jich volit více. Operaci vybereš zadáním řetězce obsahujícího příslušné číslice.")
        print("(1) sčítání")
        print("(2) odčítání")
        print("(3) násobení")
        print("(4) dělení")
        while not op:
            operace = input("Operace: ")
            for i in range(1, 5):
                if str(i) in operace:
                    op.append(i)
                elif operace == "exit":
                    exitp()
        print("Takové je nastavení: ")
        print("Operace: ", op)
        print("Maximální číslo", maxnum)
        while 1:
            oper = op[random.randint(0, len(op)-1)]
            zadani, vysledek = gen(maxnum, oper-1, resmax)
            response = numinput(zadani)
            if(vysledek == response):
                print("OK")
                ok+=1
            else:
                print("Blbě, správně je: ", vysledek)
            x+=1
    except KeyboardInterrupt:
        exitp()
```
## To samé v hodině
```python=
numdobre = 0
numspatne = 0
maxvysledek = 10
print("Jsem program na cvičení matiky. Zadej dvě čísla a výsledek, já ti pak řeknu, zda je to dobře")
while 1:
    cislo1 = int(input("Zadej první číslo: "))
    cislo2 = int(input("Zadej druhé číslo:"))
    vysl = cislo1+cislo2
    if(vysl > maxvysledek):
        print("Tento příklad neumíš řešit.")
        continue
    vysledek = int(input("Zadej výsledek: "))
    if(vysl==vysledek):
        print("spravne")
        numdobre += 1
    else:
        print("spatne, je to:", vysl)
        numspatne += 1
    prompt = input("Chceš pokračovat? ")
    if(prompt=="ano"):
        print("Okej, lets go")
    else:
        break
print("Končíme")
print("Dobře: ", numdobre)
print("Špatně: ", numspatne)
```

## Pokladna - hodina
```python=
print("Vítejte uživateli, slunce naše jasné! Postupně zadejte prosím číselné hodnoty. Zadáním 0 se program ukončí.")

cena = 0
pokracovat = True
celkovacena = 0
celkempolozek = 0
nejlevnejsi = 0
nejdrazsi = 0

while pokracovat==True:
    cena = int(input("Zadej cenu zboží: "))
    if cena==0:
        pokracovat = False
    else:
        celkempolozek = celkempolozek+1
        celkovacena+=cena
        if(cena > nejdrazsi):
            nejdrazsi = cena
        if((cena < nejlevnejsi or nejlevnejsi==0) and cena > 0):
            nejlevnejsi = cena
if celkempolozek==0:
    print("nic se neděje")
else:
    print("Celkem počet: ", celkempolozek)
    print("Celkem cena: ", celkovacena)
    prumernacena = celkovacena/celkempolozek
    if(celkempolozek != 0):
        print("Průměrná cena: ", prumernacena)
    print("Nejlevnější: ", nejlevnejsi)
    print("Nejdrazsi: ", nejdrazsi)
```

## Úkol - počítadlo mezd
* zadáme výplaty zaměstnancům; min=0
* vypsat:
    * počet zaměstnanců
    * celková výplata
    * nejvyšší výplata
    * nejvyšší plat
    * průměrný plat
    * (medián - bonus na příště)
```python=
#!/usr/bin/env python3
print("Vítejte v počítači výplat. Postupně zadávej výplaty, pro ukončení a výpis statistik napište 0.")

cont = True
celkem = 0
mnozstvi = 0
minimal = 0
maximal = 0
lidibezpenez = 0
#moneylist = []
"""
def calcmedian(l):
    sortedlist = sorted(l)
    delka = len(l)
    i = int((delka-1)/2)
    if(delka % 2):
        median = sortedlist[i]
    else:
        median = (sortedlist[i] + sortedlist[i+1])/2
    return median
"""

while cont==True:
    try:
        cena = float(input("Zadej výplatu: "))
    except ValueError:
    	cena = None
    if cena==0:
        cont = False
        print("Opouštím zadávací smyčku")
    elif cena == None:
        print("Zadejte prosím platné číslo (tečka pro desetiny)")
    elif cena > 0:
        #moneylist.append(cena)
        mnozstvi += 1
        celkem += cena
        if(cena > maximal):
            maximal = cena
        if(cena < minimal or minimal==0):
            minimal = cena
    else:
        print("Tak to asi někdo něco krutě pokazil, takže s ním radši ani nepočítáme.")
        lidibezpenez += 1
if mnozstvi==0:
    print("Nezdány žádné výplaty")
else:
    print("Statistiky:")
    print("-----------")
    print("Počet zaměstnanců s výplatou: ", mnozstvi)
    print("Počet zaměstnanců, co platili nám: ", lidibezpenez)
    print("Celková výplata: ", celkem, "Kč")
    print("Nejnižší výplata: ", minimal, "Kč")
    print("Nejvyšší výplata: ", maximal, "Kč")
    print("Průměrná výplata: ", round(celkem/mnozstvi, 2), "Kč")
    #print("Medián výplat: ", calcmedian(moneylist), "Kč")
```

## Počítadlo mezd - hodina (pole)
```python=
#!/usr/bin/env python3
print("Vítejte v počítači výplat. Postupně zadávej výplaty, pro ukončení a výpis statistik napište 0.")

cont = True
celkem = 0
lidibezpenez = 0
moneylist = []
def listprinter(l, start=0, stop=None):
    maxi = len(l)
    if(stop==None or stop>maxi):
        stop = maxi
    if(stop<0):
        stop = -1
    if(start>stop):
        inc = -1
    else:
        inc = 1
    for x in range(start, stop, inc):
        print(l[x], end="")
        if(x+inc!=stop):
            print(", ", end="")
    print(".")

while cont==True:
    try:
        cena = float(input("Zadej výplatu: "))
    except ValueError:
    	cena = None
    if cena==0:
        cont = False
        print("Opouštím zadávací smyčku")
    elif cena == None:
        print("Zadejte prosím platné číslo (tečka pro desetiny)")
    elif cena > 0:
        celkem += cena
        moneylist.append(cena)
    else:
        print("Tak to asi někdo něco krutě pokazil, takže s ním radši ani nepočítáme.")
        lidibezpenez += 1
if len(moneylist)==0:
    print("Nezdány žádné výplaty")
else:
    print("-----------")
    print("Statistiky:")
    print("-----------")
    sortedlist = sorted(moneylist)
    delka = len(moneylist)
    i = int((delka-1)/2)
    if(delka % 2):
        median = sortedlist[i]
    else:
        median = (sortedlist[i] + sortedlist[i+1])/2
    print("Seznam výplat: ", end="")
    maxi = delka-1
    listprinter(moneylist)
    print("Počet zaměstnanců s výplatou: ", len(moneylist))
    print("Počet zaměstnanců, co platili nám: ", lidibezpenez)
    print("Celková výplata: ", celkem, "Kč")
    print("Nejnižší výplata: ", sortedlist[0], "Kč")
    print("Nejvyšší výplata: ", sortedlist[delka-1], "Kč")
    print("Průměrná výplata: ", round(celkem/delka, 2), "Kč")
    print("Medián výplat: ", median, "Kč")
    maxn = 0
    while maxn==0:
        try:
            maxn = int(input("Zadej max počet extrémů: "))
        except ValueError:
            print("zadej číslo")
        if(maxn<0):
            maxn = 0
    print("Zadáno:", maxn)
    print("Prvních", maxn, "minim: ", end="")
    listprinter(sortedlist, 0, maxn)
    print("Prvních", maxn, "maxim: ", end="")
    listprinter(sortedlist, len(sortedlist)-1, len(sortedlist)-maxn-1)
```
## Úkol
* to, co minule s mediánem a průměrem pomací polí
* prakticky to předchozí
## Test v hodině
zadej čísla, potom vypiš 2 maxima
```python=
print("Zdar, jsem program, kde zadáš n čísel a já ti vypíšu 2 maxima; 0 pro exit")
cont = True
seznam = []
while cont==True:
    try:
        cislo = int(input("Zadej číslo: "))
    except:
        cislo = None
    if cislo == 0:
        if(len(seznam) >= 2):
            cont=False
        else:
            print("chcu víc čísel!")
    elif(cislo==None):
        print("chcu platné číslo")
    else:
        seznam.append(cislo)
delka = len(seznam) 
print("2 maxima jsou: ", end="")
ss = sorted(seznam)
print(ss[delka-1], "a", ss[delka-2])
```
## kostky - ve škole
```python=
import random
minx = 1
maxx = 6
hraci = []

def kostka():
    hod = []
    for i in range(0, 6):
        cislo = random.randint(minx, maxx)
        hod.append(cislo)
    hod[0] = 1
    hod[1] = 1
    hod[2] = 1
    return hod

def stats(cisla):
    stats = [0, 0, 0, 0, 0, 0]
    for x in range(len(stats)):
        for i in range(len(cisla)):
            if(cisla[i]==x+1):
                stats[x] += 1
    return stats

def alesponx(cisla, x):
    count = 0
    for i in range(len(cisla)):
         if(cisla[i]==x):
            count += 1
    return count

for i in range(20):
    hod = kostka()
    print("Padlo:", hod)
    #kolikceho = stats(hod)
    #print("Statistiky:", kolikceho)
    #if(kolikceho[0] >= 3):
    #    print("Jsou tady alespoň 3 jedničky.")
```

## Úkol - kostky
* detekovat 
    * 6 * 6
    * vše sudé
    * vše liché
    * dvě trojice stejných čísel
    * tři dvolice stejných čísel
    * posloupnost 1-6

## Kostky - hotovo
```python=
#!/usr/bin/env python3
import random
minx = 1
maxx = 6

def kostka():
    hod = []
    for i in range(0, 6):
        cislo = random.randint(minx, maxx)
        hod.append(cislo)
    return hod

def stats(cisla):
    stats = [0, 0, 0, 0, 0, 0]
    for x in range(len(stats)):
        for i in range(len(cisla)):
            if(cisla[i]==x+1):
                stats[x] += 1
    return stats

pokracovat = True
while pokracovat==True:
	inp = input("Stiskni enter pro hod kostkou, napiš exit pro ukončení: ")
	if(inp == "exit"):
		pokracovat = False
	else:
		hod = kostka()
		print("Padlo:", hod)
		kolikceho = stats(hod)
		print("Statistiky:", kolikceho)
		if(kolikceho[5] == 6):
			print("Samé šestky")
		elif(kolikceho[1] == 0 and kolikceho[3] == 0 and kolikceho[5] == 0):
			print("Samá liché čísla")
		elif(kolikceho[2] == 0 and kolikceho[4] == 0 and kolikceho[0] == 0):
			print("Samá sudá čísla")
		elif(all(x == 1 for x in kolikceho)):
			print("Postupka")
		elif(kolikceho.count(3) == 2):
			print("Dvě trojice")
		elif(kolikceho.count(2) == 3):
			print("Tři dvojice")
		else:
			print("Smůla")
```

## Uhodni číslo - úkol
```python=
import random
hints = ["trochu", "trochu víc", "tak ve středu", "celkem dost", "moc"]
minx = 0
maxx = 100000

cislo = random.randint(minx, maxx)
pokusy = []
print("Myslím si číslo mezi {} a {} včetně. Napiš nic pro exit.".format(minx, maxx))
print("Myslím si", cislo)
intx = -1
while intx != cislo:
    x = input("Co hádáš? ")
    if(x == "nic"):
        intx = cislo
        pokusy.append(None)
    else:
        intx = int(x)
        pokusy.append(intx)
        rozdil = abs(cislo-intx)
        hint = ""
        if(intx < cislo):
           print("Tvoje číslo je menší než moje o ", hint)
        elif(intx > cislo):
            print("Tvoje číslo je větší než moje o ", hint)
            print("Zatím jsi hádal:", pokusy)

if(None in pokusy):
    print("Vzdal jsi to, bídníku!!!")
else:
    print("Uhodl jsi to, číslo je", cislo)
    print("Uhodl jsi to na {}. pokus.".format(len(pokusy)))
```
- dávej hint podle přiblížení se číslu

## Hádej - hotová verze
```python=
#!/usr/bin/env python3
import random
hints = ["skoro tam", "docela blízko", "tak ve středu", "daleko", "úplně mimo"]
minx = 0
maxx = 100000 
cislo = random.randint(minx, maxx)
pokusy = []
intx = None

def mkhint(vzdalenost, intx):
    rozdil = abs(cislo - intx) # jak daleko jsme od čísla
    if(cislo < len(hints)): # aby nebyly divné nápovědy, když je gen. číslo blízko konce intervalu
        hint = "už jen kousíček od uhodnutí"
    index = int(rozdil/(vzdalenost/(len(hints)-1))) # výsledný index bude pozice rozdílu ve vzdálenosti gen. čísla od nuly převedený na index v poli
    hint = hints[index]
    return hint

def ohodnotit(intx):
    pokusy.append(intx)
    if (intx < cislo):
        print("Tvoje číslo je menší než moje, je", mkhint(cislo, intx))
    elif(intx > cislo):
        print("Tvoje číslo je větší než moje, je", mkhint(maxx-cislo, intx))
    print("Zatím jsi hádal:", pokusy)
        
print("Myslím si číslo mezi {} a {} včetně. Napiš \"nic\" pro exit.".format(minx, maxx))
print("Stupnice nápověd je:", hints)
print("Myslím si", cislo)
while intx != cislo:
    x = input("Co hádáš? ")
    if (x == "nic"):
        intx = cislo
        pokusy.append(None)
    else:
        try:
            intx = int(x)
        except ValueError:
            intx = None
        if (intx != None):
            if(intx >= minx and intx <= maxx):
                ohodnotit(intx)
            else:
                print("Číslo musí ležet v intervalu <{}; {}>".format(minx, maxx))
        else:
            print("Zadej validní číslo")

if (None in pokusy):
    print("Vzdal jsi to, bídníku!!!")
else :
    print("Uhodl jsi to, číslo je", cislo)
    print("Uhodl jsi to na {}. pokus.".format(len(pokusy)))
```
## Sorting algoritmy
### Bubblesort
```python=
import random
pocet = 10
minx = 0
maxx = 100
cisla = []

def bubblesort(cisla):
    n = len(cisla)-1
    for x in range(n):
        '''for i in range(n-x):
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
            print("průběh {}, čísla: {}".format(i, cisla))'''
        for i in reversed(range(n-x)):
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
            print("průběh {}, čísla: {}".format(i, cisla))
        print("---")
    return cisla

for i in range(pocet):
    cisla.append(random.randint(minx, maxx))

print(cisla)
print(bubblesort(cisla))
```
- Folklór: [https://youtu.be/Iv3vgjM8Pv4](zde)

### Shakersort
- oboustranný bubblesort
```python=
#!/usr/bin/env python3
import random
import time

pocet = 20
minx = 0
maxx = 100
cislain = []
'''
def shakersort_arr(cisla):
    n = len(cisla)-1
    x = 0
    pokracovat = True
    while pokracovat: # ukončit po cyklu beze změn
        pokracovat = False
        print("Průběh:", x)
        indexy = []
        indexy.extend(range(x, n-x)) # zmenšit výběr kontrolovaných prvků o jeden na každé straně s každým cyklem
        indexy.extend(reversed(range(x, n-x-1))) # průchod opačným směrem s tím, že se již teď může vynechat poslední prvek v aktuálním výběru (kontroloval se jako poslední v pčedchozím průchodu)
        print(indexy)
        for i in indexy: 
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
                pokracovat = True
            print("  {} - pozice [{}, {}]".format(cisla, i, i+1))
        x+=1
    return cisla
'''
def shakersort(cisla):
    n = len(cisla)-1
    x = 0
    pokracovat = True
    while pokracovat: # ukončit po cyklu beze změn
        pokracovat = False
        print("Průběh:", x)
        for i in range(x, n-x): # zmenšit výběr kontrolovaných prvků o jeden na každé straně s každým cyklem
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
                pokracovat = True
            print("  {} - pozice [{}, {}]".format(cisla, i, i+1))
        for i in reversed(range(x, n-x-1)): # průchod opačným směrem s tím, že se již teď může vynechat poslední prvek v aktuálním výběru (kontroloval se jako poslední v pčedchozím průchodu)
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
                pokracovat = True
            print("  {} - pozice [{}, {}]".format(cisla, i, i+1))
        x+=1
    return cisla

def bubblesort(cisla):
    n = len(cisla)-1
    for x in range(n):
        print("Průběh:", x)
        for i in range(n-x):
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
            print("  {} - pozice [{}, {}]".format(cisla, i, i+1))
    return cisla

for i in range(pocet):
    cislain.append(random.randint(minx, maxx))
print(cislain)

start1 = time.time_ns()
nase = shakersort(cislain)
end1 = time.time_ns()

kontrola = sorted(cislain)
end2 = time.time_ns()
print("--------------------------------------")
bubble = bubblesort(cislain)
end3 = time.time_ns()

#nase_arr = shakersort_arr(cislain)
#end4 = time.time_ns()

print("")
print("Shakersort:  {}, trvání: {} ns".format(nase, end1-start1))
#print("Shakersortx: {}, trvání: {} ns".format(nase_arr, end4-end3))
print("Bubblesort:  {}, trvání: {} ns".format(bubble, end3-end2))
print("Porovnání:   {}, trvání: {} ns".format(kontrola, end2-end1))
if(nase==kontrola):
    print("OK")
else:
    print("FAILED")
```
- v hodině:
```python=
#!/usr/bin/env python3
import random
import time

pocet = 10
minx = 0
maxx = 100
cislain = []

def shakersort(cisla):
    n = len(cisla)-1
    x = 0
    setrideno = False
    while(setrideno==False):
        setrideno = True
        #print("Průběh:", x)
        for i in range(x, n-x): # zmenšit výběr kontrolovaných prvků o jeden na každé straně s každým cyklem
            if(cisla[i] > cisla[i+1]):
                cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
                setrideno = False
            #print("  {} - pozice [{}, {}] - {}".format(cisla, i, i+1, setrideno))
        if(not setrideno):
            for i in reversed(range(x, n-x-1)): # průchod opačným směrem s tím, že se již teď může vynechat poslední prvek v aktuálním výběru (kontroloval se jako poslední v předchozím průchodu)
                if(cisla[i] > cisla[i+1]):
                    cisla[i], cisla[i+1] = cisla[i+1], cisla[i]
                    setrideno = False
                #print("  {} - pozice [{}, {}] - {}".format(cisla, i, i+1, setrideno))
        x+=1
    return cisla

for i in range(pocet):
    cislain.append(random.randint(minx, maxx))
#cislain = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print("Vstup:", cislain)

shaker = shakersort(cislain)
print("Shaker:", shaker)
```

## Graf v turtle
- v hodině:
```python=
#!/usr/bin/env python3
import turtle, random

pole=[]
for i in range(30):
    pole.append(random.randint(0, 100))

sizex = turtle.screensize()[0]
sizey = turtle.screensize()[1]
print(sizex)
print(sizey)
turtle.setworldcoordinates(-10, -10, sizex, sizey)
turtle.speed(0)

def mkarrow():
    uhel = 150
    turtle.left(uhel)
    turtle.forward(5)
    turtle.forward(-5)
    turtle.left(-uhel*2)
    turtle.forward(5)
    turtle.forward(-5)
    turtle.left(uhel)

def mkaxis(startpoint, offset=20):
    turtle.pensize(5)
    turtle.pendown()
    turtle.forward(sizex-offset)
    mkarrow()
    turtle.setpos((0, 0))
    turtle.left(90)
    turtle.forward(sizey-offset)
    mkarrow()

def mkpoint(pos, size=15, color="#ff0000"):
    turtle.penup()
    turtle.pensize(size)
    turtle.pencolor(color)
    turtle.setpos(pos)
    turtle.pendown()
    turtle.forward(0)
    turtle.penup()

def mklegend(x, y, val, align="center", size=16):
    turtle.setpos((x, y))
    turtle.write(val, font=("Arial", size, "normal"), align=align)

offset = 20
mkaxis(offset)
x_point_size = int((sizex-offset)/(len(pole)-1))
y_point_size = int((sizey-offset)/max(pole))
font_size = x_point_size
for poradi, cislo in enumerate(pole):
    mkpoint((x_point_size*poradi, y_point_size*cislo))
    mklegend(x_point_size*poradi, -15, poradi, "center", font_size)
    if(poradi!=0):
        mklegend(x_point_size*poradi, y_point_size*cislo+4, cislo, "center", font_size)
    else:
        mklegend(-5, y_point_size*cislo-int(font_size/2), cislo, "right", font_size)

turtle.pencolor("#000000")
turtle.setpos((sizex-10, -10))
turtle.write("X", font=("Arial", 18, "normal"))
turtle.setpos((-5, sizey-15))
turtle.write("Y", font=("Arial", 18, "normal"))

turtle.hideturtle()
turtle.done()
```
## Písemka - terč a virtuální šipky
```python=
import turtle, random, math

turtle.hideturtle()
turtle.speed(0)
labels = True
colors = [["#004020", 2], ["#505050", 5], ["#ff0000", 10], ["#ffff00", 15], ["#00ffff", 35], ["#0000ff", 50]]
sirka = sorted(turtle.screensize())[0]*2
print(sirka)
basesize = int(sirka/len(colors))
print("base: ", basesize)
def mkterc():
    for poradi, barva in enumerate(colors):
        turtle.pencolor(barva[0])
        turtle.pensize(sirka-(basesize*poradi))
        #print(sirka-(basesize*poradi))
        turtle.pendown()
        turtle.forward(0)
        turtle.penup()

def mklabels():
    turtle.pencolor("#000000")
    for k, color in enumerate(reversed(colors)):
        turtle.penup()
        turtle.setpos(int(k*basesize/2)+int(basesize/4), -10)
        turtle.write(color[1], font=("Arial", 20, "normal"), align="center")
    
def strela(pozice):
    turtle.penup()
    turtle.setpos(pozice)
    turtle.pensize(30)
    turtle.pendown()
    turtle.pencolor("#000000")
    turtle.forward(0)
    turtle.penup()

def getcoords(body):
    maxrange = (sirka/2)-int(basesize/4)
    radius = maxrange-(body*basesize)
    return((0, radius))

def randomznamenko():
    a = random.randint(0, 1)
    if(a==1):
        znamenko = -1
    else:
        znamenko = 1
    return znamenko

def randomstrela():
    y = random.randint(0, sirka/2)*randomznamenko()
    x = random.randint(0, sirka/2)*randomznamenko()
    return((x, y))

def hodnoceni(pos):
    x = pos[0]
    y = pos[1]
    radius = math.sqrt((x**2)+(y**2)) #pythagorovka
    print("radius:", radius)
    if(radius>sirka/2):
        print("Vedle!")
        hod = 0
    else:
        kolo = int(radius/(basesize/2))
        print("kolecko", kolo)
        hod = colors[len(colors)-kolo-1][1]
    return hod
def updatehodnoceni(value):
    turtle.penup()
    turtle.setpos((turtle.screensize()[0], turtle.screensize()[1]+90))
    turtle.pensize(70)
    turtle.pencolor("#ffffff")
    turtle.pendown()
    turtle.forward(-turtle.screensize()[0])
    turtle.penup()
    turtle.pencolor("#0000ff")
    turtle.setpos((turtle.screensize()[0], turtle.screensize()[1]+50))
    turtle.write(value, font=("Arial", 50, "normal"), align="right")
mkterc()
updatehodnoceni(0)
if labels:
    mklabels()
print("Enterem střílíte, exit pro ukončení")
body = 0
pokracovat = True
while pokracovat==True:
    inp = input("Enter pro střelbu: ")
    if(inp=="exit"):
        print("Končím hru")
        pokracovat = False
    else:
        bum = randomstrela()
        strela(bum)
        bodyted = hodnoceni(bum)
        body += bodyted
        updatehodnoceni(body)
        print("Dobrý pokus! Dostáváš", bodyted, "bodů.")
print("Hra ukončena. Celkem jsi dostal", body, "bodů.")
turtle.done()
```