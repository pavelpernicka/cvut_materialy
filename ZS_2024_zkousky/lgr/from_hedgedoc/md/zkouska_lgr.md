# Zkouška LGR
## Šance
- minimum: $50$ b.
- bonus ze semestru: $21-10=11$ b.
- musím dostat alespoň: $39$ b.

## Co tam bude
- výroková logika (min. 5 bodů)
- predikátová logika (min. 5 bodů)
- teorie grafů (min. 8 bodů)

## Zdroje
- přednášky z covidu: https://www.youtube.com/playlist?list=PLQL6z4JeTTQkjV5JYF0gB599ekq4zFfPK
- Matěj Dostál: https://www.youtube.com/playlist?list=PLQL6z4JeTTQlC5EzzuBCCkKE-XY9NOrk1
- jak zrychlit Gollovou: ```document.getElementsByTagName("video")[0].playbackRate = 2.5```
- minulé písemky přelouskané z obrázku do latexu: https://poznamky.pernicka.cz/E5H5zF-3Tki_Ytg19uJ3RA

## Grafové algoritmy
- [x] - hledání eulerovského tahu
    - přeskakování z čísla na číslo, škrtání předchozího, začínám vrcholem s lichým počtem prvků
- [x] - topologické očíslování vrcholů
    - tabulka in, out vrcholů. Pole se všemi iny a počtem outů vedoucích do nich. Vložím vrchol se stupněm 0, škrtnu jednu čárku v poli tam, kde má tento vrchol výstup.
- [x] - hledání jádra grafu
    - začínám nejvýše očíslovaným prvkem, ten dám do pole jader, do pole exkluzí dám všechny prvky, které z něj vedou. Potom přidám do jádra další neexkludovaný prvek podle očíslování.
- [x] - Borůvkův-Kruskalův algoritmus O(m*logm)
     - seřaď hrany podle ceny neklesajícně
     - vybere vždy nejlevnější hranu, že nevytvoří kružnici
- [x] - Jarníkův-Primův algoritmus  O(n2)
     - zvětšuje komponentu souvislosti o nejlevnější hranu, která z ní trčí
- [x] - hledání komponent (silné) souvislosti - BFS a DFS
- [x] - Kosarajův-Sharirův algoritmus - silně souvislé komponenty
    - pomocí DFS očísluji vrcholy podle opouštění, poslední je zdrojový. Potom v grafu otočím šipky, znovu prohledám pomocí DFS/BFS, vezme vrchol z topu předchozího zásobníku (nenavštívený, jinak jej vyhodí), hledáme komponenty, škrtáme navštívené
- [x] - algoritmus barvení dvěma barvami
    - BFS
- [x] - algoritmus sekvenčního barvení

## Postupy
- [x] - přirozená dedukce
- [x] - úpravy formulí ve výrokové logice
- [x] - rezoluční metoda ve výrokové logice
- [x] - úpravy formulí v predikátové logice
- [x] - rezoluční metoda v predikátové logice

## TODO fronta
- prezentace 12 - Kosarajův-Sharirův algoritmus

## Definice
### Výroková logika
- **Úplný systém logických spojek**: Množina logických spojek $\Delta$ tvoří úplný systém logických spojek, pokud pro každou formuli $\varphi$ existuje formule $\varphi_\Delta$, která používá pouze spojky z množiny $\Delta$ a platí $\varphi_\Delta$ |=| $\varphi$
- **rozšířený systém spojek**: $\implies$ (implikace), $\iff$ (ekvivalence), $\lor$ (OR), $land$ (AND), $\neg$ (NOT), ⊕ (XOR), | (NAND - Shefferova čárka), ↓ (NOR - Piersova šipka), $tt$ (TRUE), $ff$ (FALSE)
- **Formule výrokové logiky**: Definujeme rekurzivně: 
    1) každá logická proměnná je atomická formule (taktéž tt, ff)
    2) když $\alpha$, $\beta$ jsou formule, pak také $\neg a$, $\alpha \implies \beta$, ... jsou formule
    3) každá formule vznikla konečným počtem kroků 1 a 2
- **Pravdivostní ohodnocení** je zobrazení u z množiny všech formulí nad $At$ do množiny ${0,1}$, které respektuje sémantiku logických spojek. 
    - u: Fle(At) → {0,1}
- Formule je **pravdivá** v ohodnocení u, když u(φ)=1.
- Formule je **splnitelná**, když existuje ohodnocení, v němž je pravdivá (tj. u(φ)=1).
- Formule je **tautologie**, když je pravdivá ve všech ohodnoceních.
- Formule je **kontradikce**, když není pravdivá v žádném ohodnocení.
- Formule φ, ψ jsou **tautologicky ekvivalentní**, když pro každé ohodnocení u platí: u(φ) = u(ψ).
- **Boolovská funkce** $n$ proměnných je libovolná funkce $f: [0;1]n \to {0,1}, f(x1,...,xn)=y$
    - formule jsou tautologie $\iff$ jim příslušné boolovské funkce jsou stejné
    - logický součet: x+y=max(x,y)
    - logický součin: x・y=min(x, y)
    - logický doplněk: x_hat = 1 - x
- **Úplný systém spojek** je taková množina spojek Δ, že pro každou formuli φ existuje formule φΔ, která má jen spojky z Δ tak, že platí φΔ=φ.
- **Literál** je logická proměnná nebo její negace.
- **Minterm** je konjunkce literálů nebo jeden literál nebo žádný literál (tt).
- **Maxterm (klauzule)** je disjunkce literálů nebo jeden literál nebo žádný literál ($ff$).
- Formule je v **konjuntivní normální formě (CNF)**, když je konjunkcí maxtermů nebo maxterm (nebo žádný - $tt$).
- Formule je v **disjunktivní normální formě (DNF)**, když je disjunkcí mintermů nebo minterm (nebo žádný - $ff$).
- **Množina formulí S je splnitelná**, pokud existuje ohodnocení u, ve kterém jsou pravdivé všechny formule z S.
- **Množina formulí je pravdivá v ohodnocení u**, pokud jsou v něm pravdivé všechny formule z S.
- Nechť $S$ je množina formulí a φ je formule. φ je **sémantický důsledek** $S$, pokud v každém ohodnocení u, kde jsou pravdivé všechny formule z $S$, je pravdivá také φ.
    - Alt. def.: $S$ má za důsledek φ, pokud pro všechna ohodnocení u platí, že $u(S)\Leftarrow u(φ)$.
- Věta (**sémantický důkaz sporem**): Nechť S je množina formulí, φ je formule. S⊨φ iff S’=S ∪ {￢φ} je nesplnitelná.
- Nechť $\alpha$, $\beta$ jsou klauzule s komplementárním literálem (např. x). Pak **resolventa** z ɑ, ꞵ přes x je disjunkce všech ostatních literálů z ɑ, ꞵ, kromě x, ￢x.
- **Odvození (důkaz) formule** φ z množiny S je posloupnost formulí φ1,...,φn, kde každá φi (1≤i≤n) je buď formule z S nebo je to tautologický předpoklad nebo je φi odvozena z předchozích některým pravidlem a všechny pomocné předpoklady jsou pasivní.
- φ je **logický důsledek** množiny formulí S, když existuje odvození pro φ z formulí v S.

### Predikátová logika
- **Term** v predikátové logice:
    1) Každá proměnná a každá konstanta je term
    2) Je-li f funkční symbol arity n a jsou-li $t_1,…, t_n$ termy, pak $f(t_1,…, t_n)$ je term.
    3) Každý term vznikl konečným počtem kroků 1 a 2.
- **Syntaktický strom** pro term: pro proměnnou/konstantu jeden prvek, pro funkci arity $n$ je to f s n syny
- **Formule** predikátové logiky:
    1) Je-li P predikátový symbol arity n a jsou-li $t_1,..., t_n$ termy, pak $P(t_1,...,t_n)$ je atomická formule.
    2) Jsou-li $\alpha$, $\beta$ formule, pak $tt$, $ff$ a kombinace ɑ, ꞵ s log. spojkami jsou také formule.
    3) Je-li ɑ atomická formule a x proměnná, pak ∀x ɑ, ∃x ɑ jsou formule.
    4) Každá formule vznikla konečným počtem kroků 1-3.
- **Vázaný výskyt proměnné** x je výskyt v podformuli ∀x ɑ nebo ∃x ɑ (aneb ve stromě cestou od x ke kořeni narazíme na kvantifikátor s x)
- **Volný výskyt proměnné** x je výskyt, který není vázaný.
- Proměnná x je **volná** ve φ, má-li v ní volný výskyt a **vázaná**, má-li v ní vázaný výskyt.
- **Sentence** je formule, která nemá volné proměnné.
- **Otevřená formule** je taková, která nemá vázané proměnné.
- **Interpretace jazyka PL** je dvojice (U, ⟦-⟧) (universum a význam speciálních symbolů), kde U≠Ø a
    - P predikátový symbol arity n má ⟦P⟧⊆Un
    - f funkční symbol arity n má ⟦f⟧: Un → U
    - a konstanta ⟦a⟧ ∈ U
- **Kontext proměnných** je libovolné zobrazení ρ: Var → U.
    - ρ’ je updatem ρ v proměnné x, pokud se liší jen v hodnotě x.
    - interpretace termu t při kontextu ρ
        - t = a ∈ Kons, pak ⟦t⟧ρ = ⟦a⟧ρ
        - t = f ∈ Var, pak ⟦t⟧ρ = ρ(x)
        - t = f(t1,...,tn) ∈ Func , ar(f)=n, pak ⟦t⟧ρ = ⟦f⟧ρ(⟦t1⟧ρ,...,⟦tn⟧ρ)
- **Pravdivost formule v interpretaci při kontextu**:
    1) Atomická formule P(t1,...,tn) je pravdivá v interpretaci (U, ⟦-⟧) při kontextu ρ, když ⟦t1⟧ρ,...,⟦tn⟧ρ ∈ ⟦P⟧
    2) Pravdivost složených formulí je určena pravdivostí atomických formulí, resp. sémantikou logické spojky.
    3) Formule ∀x ɑ je pravdivá v interpretaci (U, ⟦-⟧) při kontextu ρ, když ɑ je pravdivá v interpretaci při všech updatech ρ’ kontextu ρ v proměnné x.
    4) Formule ∃x ɑ je pravdivá v interpretaci (U, ⟦-⟧) při kontextu ρ, když když ɑ je pravdivá v interpretaci při aspoň jednom updatu ρ’ kontextu ρ v proměnné x.
- **Sentence je pravdivá v interpretaci**, když je v ní pravdivá při libovolném kontextu ρ. Tuto interpretaci nazýváme model.
- **Sentence φ je splnitelná**, pokud existuje interpetace, ve které je φ pravdivá (existuje model).
- **Sentence φ je tautologie**, pokud je v každé interpretaci pravdivá (všechny jsou modelem).
- **Sentence φ je kontradikce**, pokud není v žádné interpretaci pravdivá (neexistuje model).
- **Množina sentencí S je splnitelná**, když existuje interpretace, v níž je pravdivá každá sentence z S (je modelem množiny).
- **Množina sentencí S má za sémantický důsledek sentenci** φ, když v každé interpretaci, ve které je pravdivá S, je pravdivá také φ.
    - Aneb každý model pro S je modelem pro φ. 
- Sentence φ, ψ jsou **tautologicky ekvivalentní**, pokud mají stejné modely.
- Formule φ je v **prenexním tvaru**, když má kvantikátory vepředu a pak následuje ψ, kde ψ je otevřená formule (tzv. otevřené jádro φ).
- Když klausule ɑ, ꞵ obsahují komplementární literály, pak res(ɑ, ꞵ) je disjunkce zbylých formulí, má velký kvantikátor pro všechny proměnné. 

### Grafy
- **Graf** je dvojice (V, E), kde V je konečná neprázdná množina (prvky nazýváme vrcholy) a E je množina některých dvouprvkových podmnožin množiny V: E ⊆ (V nad 2)
    - můžeme povolit i “jednice” z V - smyčky
- **Graf** je trojice (V, E, ε), kde V je konečná neprázdná množina vrcholů, E je konečná množina názvů hran a ε je zobrazení incidence 
- **Úplný graf** na n vrcholech Kn = (V, E), |V| = n
    - má n(n-1)/2 hran
- **Bipartitní graf**: G=(V, E), kde V=V1∪V2, V1∩V2=Ø a každá e={u, v} ∈ E, má u ∈ V1 a v ∈ V2
- **Úplný bipartitní graf**: Kmn: |V1| = m, |V2|=n
    - má m*n hran
- **Podgraf grafu** G=(V, E, ε) je graf G’=(V’, E’, ε’), kde V⊆V’, E⊆E’, ale s každou e={u,v} ∈ E’ jsou koncové vrcholy u,v ∈ V’
    - podgraf indukovaný množinou V’ obsahuje všechny hrany incidentní s koncovými vrcholy ve V’, které byly v G 
        - vyhodíme některé vrcholy a hrany z nich vedoucí
    - faktor grafu je podgraf obsahující všechny vrcholy (V=V’) vyhodíme některé hrany
- **Stupeň vrcholu** je počet hran s ním incidentních (smyčka se počítá 2x), značíme deg(v) či d(v).
    - součet všech stupňů je dvojnásobek hran - hand-shaking lemma
- **R-regulární graf** má všechny vrcholy stupně $r$
- **Skóre grafu** (grafová posloupnost) je posloupnost stupňů všech vrcholů seřazená sestupně.
- Graf G=(V, E, ε) je **izomorfní** s $G’=(V’, E’, ε’)$, když existují bijekce $f: V → V’ a g: E → E’$ a platí, že $ε(e)={u,v} iff ε’(g(e))={f(u),f(v)}$
- **Sled** v grafu G je posloupnost $v_0 e_1 v_1 e_2...e_n v_n$, kde pro každé $i, 1\le i \le n$, je $ei={vi-1, vi}$.
    - **Uzavřený sled** je sled, kde $v_0=v_n$ a $n \ge 1$ (aspoň jedna hrana).
    - **Tah** je sled, kde se neopakují hrany.
    - **Cesta** je tah, kde se neopakují vrcholy (kromě $v_0=v_n$).
    - **Kružnice** je uzavřený sled, kde se neopakují hrany ani vrcholy (tah & cesta)
- Graf je **souvislý**, pokud mezi každými dvěma vrcholy existuje cesta. 
- **Komponenta souvislosti** grafu G je maximální souvislý podgraf (maximální ve smyslu - přidáme-li vrchol, porušíme souvislost).
- **Most** je hrana, jejímž odstraněním vznikne o komponentu souvislosti více.
- **Strom** je souvislý graf bez kružnic. 
- Graf bez kružnice se nazývá **les** (aneb jeho komponenty souvislosti jsou stromy).
- Nechť $G$ je souvislý graf. Faktor grafu G, který je stromem, se nazývá **kostra grafu** G.
- Nechť $G=(V, E, ε)$ je souvislý ohodnocený graf (tj. je dáno zobrazení $c: E \to ℝ+: c(e)$ je cena hrany e). Nechť K=(V, L, ε የ L), kde L⊆E je kostra v G, pak cena kostry c(K)=c(e)
- **Minimální kostra** je kostra s nejmenší cenou ze všech koster.

#### Orientované grafy
- **Orientovaný graf** G = (V, E) je dvojice, kde V je konečná neprázdná množina a E ⊆ V x V (orientované hrany)
- Orientovaný graf G = (V, E, ε), kde V je konečná neprázdná množina vrcholů, E je s ní disjunktní a ε je zobrazení incidence
    - $ε: E \to V x V: e ↦ (u,v)$
- **Vstupní stupeň** u je počet hran, pro které je u koncový vrchol.
- **Výstupní stupeň** u je počet hran, pro které je u počáteční vrchol.
- Stupeň vrcholu $d(v)=din(v)+dout(v)$
- Posloupnost $v_0 e_1 v_1 e_2...e_n v_n$, kde pro každé i, $1\le i\le n$, je $e_i=(v_i-1, v_i)$ nazýváme **orientovaný sled**.
    - analogicky orientovaný tah, cesta, kružnice - cyklus
- Posloupnost $v_0 e_1 v_1 e_2...e_n v_n$, kde pro každé $i$, $1 \le i \le n$, je $e_i=(v_i-1, v_i)$ nebo $e_i=(v_i, v_i-1)$ nazýváme **neorientovaný sled**.
- **Kořen orientovaného grafu** je takový vrchol v, že z něj vede orientovaná cesta do každého vrcholu.
- **Kořenový strom** je orientovaný graf, který je stromem a má kořen.
- Orientovaný graf je **acyklický**, když neobsahuje cyklus (smyčky jsou také zakázány).
- **Topologické uspořádání vrcholů** v orientovaném grafu $G$ je takové uspořádání vrcholů do posloupnosti $v_1,...,v_n$, že pro každou hranu $e=(v_i,v_j)$ platí $i < j$.
- Pokud $din(v) = 0$, pak vrchol v nazýváme **zdrojem grafu**.
- Pokud $dout(v) = 0$, pak vrchol v nazýváme **výlevkou grafu**.
- **Jádro orientovaného grafu** je množina vrcholů $K⊆V$ taková, že platí:
    1) neexistuje hrana mezi vrcholy v $K$
    2) Z každého vrcholu ve $V∖K$ vede hrana do nějakého vrcholu v $K$
- Orientovaný graf je silně souvislý, pokud mezi každými dvěma vrcholy existuje orientovaná cesta.
    - graf je silně souvislý $\iff$ je souvislý a každá hrana leží v cyklu
- **Komponenta silné souvislosti** grafu $G$ je každý jeho maximální silně souvislý podgraf.
- **Kondenzace orientovaného grafu** $G$ je orientovaný graf $G’$, který má za vrcholy komponenty silné souvislosti grafu $G$ a hrany $(K_1,K_2) ∈ E’$ $\iff$ existuje vrchol $v ∈ K_1$ a $w ∈ K_2$ tak, že $(v,w) ∈ E$

#### Eulerovské grafy, barvení grafu a rovinné grafy
- **Eulerovský tah** v grafu G je takový tah, který obsahuje všechny vrcholy a všechny hrany. (Hrany se neopakují, vrcholy mohou.)
- **Graf je eulerovský**, když v něm existuje uzavřený eulerovský tah. 
    - G je eulerovský $\iff$ je souvislý a každý vrchol má sudý stupeň
    - G má **otevřený eulerovský tah**, pokud právě dva vrcholy jsou lichého stupně
- **Obarvení grafu** je zobrazení $b: V \to B$, kde $B$ je množina barev, takové, že pro všechny vrcholy $u, v$ platí, že pokud ${u, v} ∈ E$, pak $b(u)≠b(v)$
- **Barevnost grafu** (chromatické číslo) je nejmenší počet barev potřebných k obarvení grafu.
- Říkáme, že graf je **k-barevný**, když $k$ barev stačí k jeho obarvení.
- **Klika** v grafu je každá mnžoina vrcholů, která indukuje maximální úplný podgraf.
- **Klikovitost** grafu je počet vrcholů v nejpočetnější klice.
    - $ω(G)≤𝜒(G)$
- **Maximální nezávislá množina** je množina vrcholů, která indukuje maximální možný diskrétní podgraf.
- **Nezávislost grafu** je počet vrcholů v nejpočetnější maximální nezávislé množině.
    - $𝜒(G) ≤ n - α(G) + 1$
    - $𝜒(G)·α(G)>=n$
    - $𝜒(G) ≤ 1+max(d(v))$
- **Rovinné nakreslení grafu** je přiřazení vrcholům body v rovině a hranám spojité prosté (neprotínají samy sebe) křivky spojující příslušné body tak, že křivky se navzájem neprotínají.
- **Graf je rovinný**, pokud má rovinné nakreslení.
- **Sférické nakreslení grafu** je takové nakreslení grafu na kouli, že se nekříží hrany.
- G je rovinný graf spolu s rovinným nakreslením. Každá oblast roviny, která je ohraničená křivkami odpovídajícími hranám se nazývá stěna.
- **Stupeň stěny** je počet hran, které ohraničují danou stěnu, přitom hrana uvnitř stěny (most) se počítá 2x.
- **Eulerův vzorec**: Nechť $G$ je souvislý rovinný graf s $n$ vrcholy, $m$ hranami a nechť je dáno rovinné nakreslení pro $G$, které má $s$ stěn. Potom $n+s = m+2$.
- G souvislý rovinný graf s $n\ge 3$ vrcholy a $m$ hranami.
    - $m\le 3n-6$
    - nemá-li $G$ ani trojúhelníky, pak $m\le 2n-4$