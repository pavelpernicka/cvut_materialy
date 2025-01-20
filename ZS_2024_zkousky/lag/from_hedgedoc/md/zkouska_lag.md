# Zkouška LAG
## Šance
- bonus ze semestru: $15+13=28$ bodů
- minimum bodů z písemky: $30/60$ bodů
- minimum, co můžu získat, abych prošel: $58$ bodů -- $E$ o $2$ body
- od $75$ bodů ústní zkouška (bez risku)
- musím dát alespoň $30$ b.

## Osnova
- Lineární prostory.
- Lineární obal, lineární závislost a nezávislost.
- Báze, dimenze, souřadnice vektoru v bázi.
- Lineární zobrazení, matice jako lineární zobrazení.
- Matice lineárního zobrazení, transformace souřadnic.
- Soustavy lineárních rovnic, Frobeniova věta, geometrie řešení soustav.
- Determinant čtvercové matice.
- Vlastní hodnoty a diagonalisace, Jordanův tvar.
- Abstraktní skalární součin.
- Ortogonální projekce a ortogonalisace.
- Metoda nejmenších čtverců, SVD a pseudoinverse.
- Vzájemná poloha afinních podprostorů a vzdálenost afinních podprostorů.
- Vektorový součin a metrické výpočty v R^n.

## Definice -- moje
- **Lineární kombinace** seznamu vektorů $(\vec{x_1} ... \vec{x_n})$ je vektor $\vec{v}=\sum_{i=1}^{n} a_i \cdot \vec{x_i}$, kde $(a_1 ... a_n)$ jsou koeficienty z tělesa $F$.
- **Lineární nezávislost** je vlastnost pro nějaký seznam vektorů $S$. Ten je lineárně nezávislý, pokud je buď prázdný, nebo pokud seznam není prázdný a $\vec{o}$ lze vytvořit pouze kombinací vektorů $(\vec{x_1} ... \vec{x_n})$ za použití koeficientů $a_1 ... a_n = 0$. Tedy $\sum_{i=1}^n a_i \cdot \vec{x_i} = \vec{o}$, kde $\vec{x_1} ... \vec{x_n}\in S$ a $a_1 = a_2 ... = a_n = 0$.
- **Lineární závislost**: Seznam vektoru $S$ je lineárně závislý, pokud není lineárně nezávislý. Tedy pokud není prázdný a lze $\vec{o}$ sestavit kombinací vektorů $(\vec{x_1} ... \vec{x_n})S$ za použití nenulových koeficientů $(a_1 ... a_n) \in F \setminus \{0\}$. Matematicky: $\vec{o} = \sum_{i=1}^{n} a_i \cdot \vec{x_i}$, $\vec{x_1} ... \vec{x_n} \in S$ a $(a_1 ... a_n) \in F \setminus \{0\}$
- **Lineární obal** množiny $M$ jakýchkoliv vektorů lineárního prostoru $L$ je množina všech lineárních kombinací vektorů z množiny $M$, pokud $M \neq \{\}$. Pokud $M = \{\}$, tak je lineární obal $span(\{\}) = \vec{o}$
- **Lineární podprostor** prostoru $L$ je taková podmnožina $W$ prostoru $L$, pro kterou platí, že $span(W)$ je podmnožinou $W$. $W$ je tedy uzavřena na tvorbu lineárních kombinací.
- **Množina generátorů** $G$ je množina vektorů, pomocí jejíchž všech lineárních kombinací jsme schopni vytvořit lineární podprostor $W$ prostoru $L$. Tedy: $span(G) = W$.
- **Konečně generovaný podprostor**: Lineární podprostor $W$ prostoru $L$ je konečně generovaný, pokud množina jeho generátorů $G$ má konečný počet prvků.
- **Báze** $B$ prostoru $L$ je lineárně nezávislá množina generátorů prostoru $L$. Napíšeme-li $B$ jako seznam (seznam = uspořádaná n-tice prvků), označujeme ji jako uspořádanou bázi.
- **Dimenze** konečně generovaného lineárního prostoru $L$ je počet prvků jeho báze. $dim(L) = card(B)$, $B$ je báze prostoru $L$.
- **Souřadnice** vektoru $\vec{v}$ vzhledem k uspořádané bázi $B = (\vec{b_1} ... \vec{b_n})$ je uspořádaný seznam $(a_1 ... a_n) \in F$ takový, že $\vec{v} = \sum_{i=1}^{n} a_i \cdot \vec{b_i}$. Značíme jej $coord_B(\vec{v}) = \begin{pmatrix} a_1 \\ \vdots \\ a_n \end{pmatrix}$. (Jednoduše řečeno: souřadnice $\vec{v}$, kterou vytvoříme pomocí lineární kombinace báze $B$)
- **Lineární zobrazení** z lineárního prostoru $L_1$ do lin. prostoru $L_2$, značeno $f: L_1 \to L_2$, je takové zobrazení, kde pro $\vec{x}, \vec{y}$ a skaláry $a$ z $F$ platí: $f(\vec{x} + \vec{y}) = f(\vec{x}) + f(\vec{y})$ a $f(a \cdot \vec{x}) = a \cdot f(\vec{x})$ (zachovává vektorové operace sčítání a násobení skalárem)
- **Jádro** lineárního zobrazení $f: L_1 \to L_2$ je množina všech $\vec{x} \in L_1$, pro které platí $f(\vec{x}) = \vec{o}$. Matematicky: $ker(f) = \{\vec{x} | f(\vec{x}) = \vec{o}\}$. Lidsky: množina všech vektorů, které se při zobrazení „ztratí“, tedy převedou na nulový vektor. Jádro indikuje, jak moc je $f$ monomorfismus.
- **Obraz** lineárního zobrazení $L_1 \to L_2$ je množina všech $\vec{y} \in L_2$ pro které existuje $\vec{x}$ takové, že $f(\vec{x}) = \vec{y}$. Matematicky: $im(f) = \{\vec{y}| \exists \vec{x}: f(\vec{x}) = \vec{y}\}$. Lidsky: množina všech vektorů, do kterých mohou být převedeny vektory z jiného prostoru zobrazením. Obraz indikuje, jak foc je $f$ epimorfismus.
- **Hodnost** lineárního zobrazení $f: L_1 \to L_2$ je dimenze obrazu tohoto zobrazení. Matematicky: $rank(f) = dim(im(f))$
- **Defekt** lineárního zobrazení $f: L_1 \to L_2$ je dimenze jádra tohoto zobrazení. Matematicky: $rank(f) = dim(ker(f))$
- **Monomorfismus**: Lineární zobrazení $f: L_1 \to L_2$ je monomorfismus, pokud je prosté. Tedy když pro každé $x_1, x_2 \in L_1$ platí $f(x_1) = f(x_2) \implies x_1 = x_2$. Z toho plyne: $ker(f) = \vec{o}$ (různé vstupy mají různé výstupy, nic se nesrazí do $\vec{o}$)
- **Epimorfismus** Lineární zobrazení $f: L_1 \to L_2$ je epimorfismus, pokud je na (surjektivní). Tedy když pro všechna $y\in L_2$ existuje $x \in L_1$ takové, že $f(x) = y$. Z toho plyne: $im(f) = L_2$ (pro každý vektor v $L_2$ je odpovídající vektor v $L_1$, zobrazení pokrývá celá prostor $L_2$)
- **Isomorfismus**: Lineární zobrazení $f: L_1 \to L_2$ je isoformismus, pokud je prosté a na zároveň (bijektivní).
- **Regulární matice** $M$ je matice, která má inverzi $A^{-1}$ a platí: $A^{-1} \cdot A = A \cdot A^{-1} = E$
- **Singulární matice** je matice $M$, která není regulární.
- **elementární řádkové úpravy matice** - takové úpravy soustavy lineárních rovnic, které nemění řešní dané soustavy lin. rovnic ani jejich hodnost. Dělí se na 3 typy:
    - přičtení $a$-násobku řádku $i_1$ k řádku $i_0$
    - prohození rádku $i_1$ s řádkem $i_0$
    - vynásobení řádku $i_0$ skalárem $a$, $a\neq 0$
- **horní blokový tvar matice** - Matice $M$ je v horním blokovém tvaru, pokud jsou splněny následující podmínky: 
    - každý nenulový řádek matice $M$ je nad jakýmkoliv řádkem samých nul
    - každý pivot (první nenulová položka zleva) jakéhokoliv nenulového řádku matice $M$ je vždy více napravo, než pivot předchozího řádku
- **ekvivalentní soustavy lineárních rovnic** - Řekneme, že soustavy lineárních rovnic $(A \bigm | b)$ a $(A' \bigm | b')$ o $r$ rovnicích a $s$ neznámých jsou ekvivalentní, pokud pro každý vektor $\vec{x_p}$ z prostoru $F^s$ platí, že vektor $\vec{x_p}$ je řešením soustavy $(A \bigm | b)$ právě tehdy, když $\vec{x_p}$ je řešením soustavy $(A' \bigm | b')$. Značíme: $(A \bigm | b) \sim (A' \bigm | b')$.
- **Frobeniova věta** - Nechť $f: L_1 \to L_2$ je lineární zobrazení a $\vec{b}$ je jakýkoliv vektor v prostoru $L_2$. Potom platí:
    - Rovnice $f(\vec{x}) = \vec{b}$ má řešení právě tehdy, když $\vec{b}$ leží v prostoru $im(f)$. Jinak řečeno, soustava $(A \bigm | \vec{b})$ má řešení právě tehdy, když $rank(A) = rank(A \bigm | \vec{b})$, kde matice $A: F^s \to F^r$ a tedy $\vec{b} \in F^r$.
    - Pokud má soustava výše řešení a $\vec{p}$ je partikulární řešení (jeden z vektorů, které vyhovují rovnosti) této rovnice, pak platí, že každé řešení rovnice lze zapsat jako $x = \vec{p} + \vec{x_h}$, kde $\vec{x_h}$ je nějaké prvek z $ker(f)$.
- **permutace** - Permutace množiny {1,2...,n} je zobrazení π: {1,2...,n} $\to$ {1,2...,n}, které je bijekce (prosté a na zároveň) (použije všechny prvky výstupního prostoru a pro každý vstup je jiný výstup).
- **determinant** - Nechť A: $F^{n} \to F^{n}$ (čtvercová matice) s položkami $a_{i,j}$, determinant $det(A)$ je skalár z tělesa $F$ vyjádřený formulí: $det(A) = \sum_{π\in S_n} sign(π) \cdot a_{π(1), 1} \cdot a_{π(2), 2} ... \cdot a_{π(n), n}$, kde $S_n$ je množina všech permutací $\{1 ... n\}$.
- **algebraický doplněk** - Ať $M$ je matice typu $n$ x $n$ nad $F$, $n \geq 2$. Označme jako $A_ij$ matici typu $(n − 1)$ x $(n − 1)$ vzniklou z matice $M$ vynecháním $i$-tého řádku a $j$-tého sloupce. Potom algebraický doplněk je výraz $A_{ij} = (−1)^{i+j} \cdot det(M_{ij})$.
- **adjungovaná matice** - adjungovaná matice čtvercové matice $A$, značeno $adj(A)$, je transponovaná matice algebraických doplňků matice $A$. (vždy místo původního prvku na pozici $(x, y)$ dáme algebraický doplněk $A_{x, y}$, potom takto vzniklou matici transponujeme, tedy bereme řádky jako sloupce a naopak)
- **Cramerovo pravidlo** - Nechť A: $F^{n} \to F^{n}$ regulární čtvercová matice a $\vec{b}$ $\in$  $F^{n}$. Potom $j$-tá položka jediného řešení $\vec{x} = A^{-1} \cdot \vec{b}$ je ve tvaru: $x_j$ =$\frac{1} {det(A)} \cdot det \hspace{2mm}$($a_{1}$ ... $a_{j-1}, \vec{b}, a_{j+1} ... a_{n}$)
- **rozvoj determinantu podle řádku/sloupce** Uvažujeme čtvercovou matici nxn matici A. Zvolíme-li řádek k $\in$ {1,...,n} lze determinant A vyjádřit jako: det(A) = $\sum_{j=1}^{n}$ $A_{kj}$ $D_{kj}$, kde $D_{kj}$ jsou tzv. algebraické doplňky matice A. Podobně můžeme rozvinout determinant podle l-tého sloupce, l $\in$ {1,...,n}, det(A) = $\sum_{i=1}^{r}$ $A_{il}$ $D_{il}$
- **vyjádření inverzní matice pomocí adjungované** Pro regulární matici A plati: $A^{-1}$ = $\frac{1} {det(A)} * adj(A)$, kde adj(A) je adjungovaná matice, tj. $[adj(A)]_{ji}$ = $D_{ji}$, kde $D_{ji}$ = $(-1)^{i+j}$ det A, s vyhozeným j-tým řádkem a i-tým sloupcem.

:::danger
Doplnit témata: eigenvectors and eigenvalues a dál
:::

- Podobné matice: mají stejný determinant, znázorňují stejnou lin. transformaci, ale k jiným bázím. $A \approx B$ platí tehdy, když $B=T^{-1}\cdot A \cdot T$
- vlastní prostor: množina vektorů, v jejíchž směrech lineární transformace pouze škáluje vektory
- Jordanův tvar: tvar $M= D(x_1, x_2, x_2, ..., x_n) + N$, kde D je diagonalizovaná matice a N je zbytek
- Metoda nejmenších čtverců: $(A| \vec{b}) \to (A^T \cdot A | A^T \cdot \vec{b})$
    - nenalezne řešení, ale nejlepší přímku, kterou lze proložit body -- regresní přímku
- Gramova matice: $G = (T_{K_2 \to B})^T \cdot T_{K_2 \to B}$
- $T_{A \to B} = B^{-1} \cdot A$
- $A = T_{A \to K_n}$
- $T_{A \to C} = T_{B \to C} \cdot T_{A \to B}$ (vektorem násobit na konci)
- determinant je imunní vůči změně báze
- ortogonalizace báze:
    - $c_1 = b_1$
    - $c_2 = rej_{span(c_1)}(b_2)$
    - $c_3 = rej_{span(c_1, c_2)}(b_3)$
- projekce: $proj_W (u) = \frac{<u|v_n>}{<v_n|v_n>} \cdot v$ pro každý vektor $b_n \in W$ (suma)
- rejekce: $rej_W (u) = u - proj_W (u)$
- standartní skalární součin: $<u|v> = u^T \cdot G \cdot v$ $G$ = metrický tensor
- metoda nejmenších čtverců: $(A^T \cdot A | A^T \cdot b)$
- vektorový součin: $\times (u, v, w) = det(u, w, w, e_1) \cdot e_1 + $det(u, w, w, e_2) \cdot e_2 + det(u, w, w, e_3) \cdot e_3$ (zde jsou vektory jsou z $R^3$)

## Příklady
- jsou rovnoběžné = $span(W)$ je podmonožinou $span(W')$ a naopak
- jsou různoběžné = existuje řešení rovnice $(W, W' | p-p')$
- vzdálenost afinních podprostorů: $\omega(\pi, \pi') = || rej_{W \vee W'}(p-p') ||$

## Poznámky ze semestrálních testů
- když $det(A) \neq 0$, tak $A$ je regulární (a naopak)
- $A^{-1} = \frac{1}{det(A)} \cdot adj(A)$
- když v $(A \bigm | \vec{b})$ je $A$ čtvercová a soustava má jediné řešení, tak je $A$ regulární. Řešení je pak $A^{-1} \cdot \vec{b}$
- před použitím Cramerova pravidla musím dát podmínku, kdy je determinant nenulový a tedy $A$ regulární, pokud je $A$ s parametrem.
- při GEM: prohození řádků změní znaménko det, vynásobení řádku změní det. x-krát. 
- $det(A) = det(A^T)$ => předchozí platí i pro sloupcové úpravy
- det je součin prvků na diagonále matice v horním blokovém tvaru