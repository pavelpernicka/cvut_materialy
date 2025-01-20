# Logika a grafy -- test 2

## Neorientované grafy (8)
- **Neorientovaný graf** je dvojice $(V, E)$, kde $V$ je neprázdná konečná množina vrcholů, $E$ je množina některých dvouprvkových podmnožin množiny $V$, těmto prvkům říkáme hrany
- spojuje vrcholy = je incidentní s vrcholy
- **úplný graf** = každé dva vrcholy jsou spojeny hranou (má $\binom{n}{2} = \frac{n(n-1)}{2}$ hran), je $(n-1)$-regulární)
- **diskrétní graf** = graf bez hran
- **bipartitní graf** = graf, jehož množina vrcholů jze rozdělit na dvě disjunktní podmnožiny $V_1$ a $V_2$, každá hrana grafů má jeden vrchol z $V_1$ a druhý z $V_2$
- **stupeň vrcholu** = počet hran incidentních s vrcholem (značeno $deg(v)$)
- **hands shaking lemma** = součet stupňu vrcholů je 2x počet hran
- **$r$-regulární graf** je graf, jehož všechny vrcholy mají stejný stupeň $r$, neexistuje licho-regulérní graf s lichým počtem vrcholů
- **skóre grafu** - n-tice stupňů vrcholů uspořádaná sestupně, aby graf existoval, musí být její suma sudá
- **sled** = posloupnost vrcholů a hran, kde každá hrana spojuje dva po sobě jdoucí vrcholy (vrcholy a hrany se mohou opakovat)
- **tah** = sled, kde se neopakují hrany
- **cesta** = tah, kde se neopakují vrcholy

## Eulerovské grafy (9b)
- **eulerovský tah** = tah, který obsahuje všechny hrany (každou jen jednou) a všechny vrcholy grafu
- **eulerovský graf** = graf, ve kterém existuje uzavřený eulerovský tah (je souvislý a každý vrchol má sudý stupeň)
- **uzavřený tah** = všechny vrcholy mají sudý stupeň a nelze prodloužit
- **otevřený tah** = dva krají vrcholy mají lichý stupeň, zbytem má sudý stupeň

## Stromy (10a)
- **strom** = souvislý graf neobsahující kružnici (má $n-1$ hran)
- počet stromů o $n$ vrcholech je $n^{n-2}$
- strom existuje, pokud je suma ze skóre rovna $2(n-1)$, kde $n$ je počet vrcholů

## Orientované grafy (11a)
- **silně souvislý graf** = graf, pro jehož každé dva vrcholy $u, v$ existuje orientovaná cesta z $u$ do $v$

## Acyklické grafy (11b)
- **jádro acyklického grafu** = množina $J\subseteq V$ taková, že mezi vrcholy z $J$ není žádná hrana a z každého vrcholu mimo $J$ vede alespoň jedna hrana do $J$