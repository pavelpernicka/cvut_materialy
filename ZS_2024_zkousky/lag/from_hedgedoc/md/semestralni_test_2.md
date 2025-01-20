# LAG 2 definice / formulace tvrzení 
***Jura Velebil - YOU SHALL PASS***

---

### DEFINICE: 

- **permutace:** Permutace množiny {1,2...,n} je jakákoliv bijekce - (vzájemně jednoznačné zobrazení) π: {1,2...,n} $\to$ {1,2...,n}.
- **inverze v permutaci:** 
- **znaménko permutace:** Ať π je permutace množiny {1,2...,n}. Znaménko permutace π je číslo sign π, které je buď +1 (pokud strunový diagram π obsahuje sudý počet překřížení strun, říkáme že π je sudá permutace), anebo -1 (pokud strunový diagram π obsahuje lichý počet překřížení strun, říkáme že π je lichá permutace).
- **determinant:** Buď A: $F^{n} \to F^{n}$, definujeme její determinant detA = $\sum_{π\in Sn} sign(π) * A_1π_{(1)} ...A_n π_{(n)}$.
- **regulární matice:** Matice A: $F^n \to F^n$ je regulární , pokud existuje jednoznačně určená matice $A^{-1}$ * A = $E_n$ = A *  $A^{-1}$. Matici $A^{-1}$ říkáme inverse matice A.
- **singulární matice:** Matice A: $F^n \to F^n$ je singulární, pokud není regulární.
- **inverzní matice:** Matici $A^{-1}$ říkáme inverze matice A.(*****zkontroluj poderžele krátké*****)
- **algebraický doplněk:**  Determinantu $A_{ij} = det (a_1,...,a_{j-1},e_i,a_{j+1},...,a_n)$ říkáme algebraický doplněk pozice (i,j) v matici A = $(a_1,...a_n)$.
- **adjungovaná matice:** Pro matici A tzpu n*n je její adjungovaná matice adj(A) transponovaná matice algebraických doplňků pozic v matici A.
- **bijektivní zobrazení:** Nechť f: V $\to$ W je bijektivní zobrazení. Potom $f^{-1}$ je rovněž lineární.

---

### FORMUACE TVRZENÍ: 

- **Frobeniova věta** Nechť F je těleso. Dále buď A: $F^s \to F^r$ matice a $\vec{b} \in F^r$ vektor. Soustava A $\vec{x}$ = $\vec{b}$ má řešení právě tehdy, když rank(A) = rank (A|$\vec{b}$). Množinu řešeni S = {$\vec{x}$| A$\vec{x}$ = $\vec{b}$} lze napsat jako S = $\vec{x}_p$ + $S_0$, kde $S_0$ = {$\vec{x}$| A$\vec{x}$ = $\vec{0}$} = ker (A) je množina všech řešení bez pravé strany a $\vec{x}_p$ je jakékoliv (konkrétní, tzv. partikulární) řešení.
- **rozvoj determinantu podle řádku/sloupce** Uvažujeme čtvercovou matici nxn matici A. Zvolíme-li řádek k $\in$ {1,...,n} lze determinant A vyjádřit jako: det(A) = $\sum_{j=1}^{n}$ $A_{kj}$ $D_{kj}$, kde $D_{kj}$ jsou tzv. algebraické doplňky matice A. Podobně můžeme rozvinout determinant podle l-tého sloupce, l $\in$ {1,...,n}, det(A) = $\sum_{i=1}^{r}$ $A_{il}$ $D_{il}$
- **cramerovo pravidlo:** Buďte A: $F^{n} \to F^{n}$ regulární matice $\vec{b}$ $\in$  $F^{n}$. Potom lze složky řešení rovnice A $\vec{x}$ = $\vec{b}$ vyjádřit jako: $X_j$ =$\frac{1} {detA} * det \hspace{2mm}$($A_{o1}$ ... $A_{oj-1} \vec{b} A_{oj+1} ... A_{on}$)
- **vyjádření inverzní matice pomocí adjungované** Pro regulární matici A plati: $A^{-1}$ = $\frac{1} {det(A)} * adj(A)$, kde adj(A) je adjungovaná matice, tj. $[adj(A)]_{ji}$ = $D_{ji}$, kde $D_{ji}$ = $(-1)^{i+j}$ det A, s vyhozeným j-tým řádkem a i-tým sloupcem.

---

### Rondošův koutek
- **elementární řádkové úpravy matice** - takové úpravy soustavy lineárních rovnic, které nemění řešní dané soustavy lin. rovnic ani jejich hodnost. Dělí se na 3 typy:
    - přičtení $a$-násobku řádku $i_1$ k řádku $i_0$
    - prohození rádku $i_1$ s řádkem $i_0$
    - vynásobení řádku $i_0$ skalárem $a$, $a\neq 0$
- **horní blokový tvar matice** - Matice $M$ je v horním blokovém tvaru, pokud jsou splněny následující podmínky: 
    - každý nenulový řádek matice $M$ je nad jakýmkoliv řádkem samých nul
    - každý pivot (první nenulová položka zleva) jakéhokoliv nenulového řádku matice $M$ je vždy více napravo, než pivot předchozího řádku
- **ekvivalentní soustavy lineárních rovnic** - Řekneme, že soustavy lineárních rovnic $(A \bigm | b)$ a $(A' \bigm | b')$ o $r$ rovnicích a $s$ neznámých jsou ekvivalentní, pokud pro každý vektor $\vec{x_p}$ z prostoru $F^s$ platí, že vektor $\vec{x_p}$ je řešením soustavy $(A \bigm | b)$ právě tehdy, když $\vec{x_p}$ je řešením soustavy $(A' \bigm | b')$. Značíme: $(A \bigm | b) \sim (A' \bigm | b')$.
- **Regulární matice** $A$ je matice, která má inverzi $A^{-1}$ a platí: $A^{-1} \cdot A = A \cdot A^{-1} = E$
- **Singulární matice** je matice $M$, která není regulární.
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

#### Poznatky
- když $det(A) \neq 0$, tak $A$ je regulární (a naopak)
- $A^{-1} = \frac{1}{det(A)} \cdot adj(A)$
- když v $(A \bigm | \vec{b})$ je $A$ čtvercová a soustava má jediné řešení, tak je $A$ regulární. Řešení je pak $A^{-1} \cdot \vec{b}$
- před použitím Cramerova pravidla musím dát podmínku, kdy je determinant nenulový a tedy $A$ regulární, pokud je $A$ s parametrem.
- při GEM: prohození řádků změní znaménko det, vynásobení řádku změní det. x-krát. 
- $det(A) = det(A^T)$ => předchozí platí i pro sloupcové úpravy
- det je součin prvků na diagonále matice v horním blokovém tvaru