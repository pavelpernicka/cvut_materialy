# MA2 -- Zápočtové minimum
:::warning
Tento souhrn pokrývá pouze praktickou aplikaci poznatků z Analýzy 2, která je požadována na zápočtové testy. Látky je mnohem více.
:::
## 1. semestrální písemka
### Množiny a body
- **vnitřní body $int(M)$** -- bod včetně jeho okolí je prvkem množiny (pokud jsou všechny body množiny vnitřní, je otevřená)
- **hraniční body $\partial M$** -- každé okolí bodu zasahuje do množiny
- **uzávěr $\bar{M}$** -- $\bar{M} = M \cup \partial M$
- **hromadný bod** -- bod, ke kterému konvergují body z $M$
- **izolovaný bod** -- bod, v jehož okolí není žádný jiný bod

### Hladina funkce
- práce s vektorovými funkcemi -- stejné, ale po složkách
- kdy je funkční hodnota rovna nějaké konstantě hladiny: $f(x,y) = c$

### Směrová derivace
- praktický výpočet podle diferenciálu:
$$
\nabla_v f(a) = \nabla f(a) \cdot v
$$
- podle definice (směrová derivace podle $v$ v bodě $a$):
$$
\nabla_v f(a) = \lim_{t\to 0}{\frac{f(a+tv)-f(a)}{t}}
$$
($a$, $a+tv$ jsou vektory)

### Parciální derivace
- všechny kromě daných proměnných považujeme za konstanty
- parciální derivace podle více proměnných:
$$
\frac{\partial f}{\partial x \partial y} = \frac{\partial f}{\partial x}\left(\frac{\partial f}{\partial y}\right)
$$
- **Laplaceův operátor** (součet druhých parciálních derivací podle všech proměnných):
$$
\Delta f = \frac{\partial^2 f}{\partial x^2} + \frac{\partial^2 f}{\partial y^2}
$$

### Diferenciál
- lineární aproximace změny v bodě $a$ ve směru $h$
$$
df(a)(h) = \nabla_h f(a) = \nabla f(a) \cdot h = J_f(a) \cdot h
$$
(takže jej zapisujeme buď pomocí gradientu, nebo Jacobiho matice)

### Gradient
- $\nabla f(x,y)$: směr největšího **růstu**
- $-\nabla f(x,y)$: směr největšího **poklesu**
- dává normálový vektor tečné roviny
$$
\nabla f(a) = \left(\frac{\partial f}{\partial x}(a), \frac{\partial f}{\partial y}(a), \dotsi \right)
$$

### Jacobiho matice
$$
J_{\vec{f}}(x) =
\begin{pmatrix}
\frac{\partial f_1}{\partial x_1} & \frac{\partial f_1}{\partial x_2} & \cdots & \frac{\partial f_1}{\partial x_n} \\
\frac{\partial f_2}{\partial x_1} & \frac{\partial f_2}{\partial x_2} & \cdots & \frac{\partial f_2}{\partial x_n} \\
\vdots & \vdots & \ddots & \vdots \\
\frac{\partial f_m}{\partial x_1} & \frac{\partial f_m}{\partial x_2} & \cdots & \frac{\partial f_m}{\partial x_n}
\end{pmatrix}
$$

### Tečné roviny
- výpočet tečné roviny pro funkci $f$ k bodu $a$:
$$
g(\vec{x}) = f(\vec{a}) + \nabla f(\vec{a}) \cdot (\vec{x}-\vec{a}) \\
g(x, y) = f(1, 2) + \nabla f(1, 2) \cdot 
\left(
\begin{pmatrix}
x \\
y
\end{pmatrix} -
\begin{pmatrix}
1 \\
2
\end{pmatrix}
\right)
$$
- rovnoběžnost: normálový vektor je násobkem jiného normálového vektoru

### Taylorův polynom
- Dám vzorcem:
$$
T_k(x) = \sum_{i=0}^{k} \frac{1}{i!} \nabla_{x - a}^i f(a)
$$
- speciální případy:
$$
T_0(x) = f(a), \\
T_1(x) = f(a) + \nabla f(a) \cdot (x - a), \\
T_2(x) = f(a) + \nabla f(a) \cdot (x - a) + \tfrac{1}{2} (x - a) \cdot (H_f(a)(x - a))
$$
- Příklad -- taylorův polynom 2. řádu funkce $f$ v bodě $(1,2)$:
$$
T_2(x, y) = f(1,2) + \nabla f(1,2)((x,y)-(1,2)) + \frac{1}{2} \cdot ((x,y)-(1,2)) \cdot H_f(a) \cdot ((x,y)-(1,2))
$$

### Hessova matice
- počítá se podle ní 2. diferenciál: $d^2f(a)(h) = h^\top H_f(a) \, h$ (kvadratická forma)
- je symetrická
- obecně:
$$
H_f(\mathbf{a}) =
\begin{pmatrix}
\frac{\partial^2 f}{\partial x_1^2}(\mathbf{a}) & \frac{\partial^2 f}{\partial x_1 \partial x_2}(\mathbf{a}) & \cdots & \frac{\partial^2 f}{\partial x_1 \partial x_n}(\mathbf{a}) \\
\frac{\partial^2 f}{\partial x_2 \partial x_1}(\mathbf{a}) & \frac{\partial^2 f}{\partial x_2^2}(\mathbf{a}) & \cdots & \frac{\partial^2 f}{\partial x_2 \partial x_n}(\mathbf{a}) \\
\vdots & \vdots & \ddots & \vdots \\
\frac{\partial^2 f}{\partial x_n \partial x_1}(\mathbf{a}) & \frac{\partial^2 f}{\partial x_n \partial x_2}(\mathbf{a}) & \cdots & \frac{\partial^2 f}{\partial x_n^2}(\mathbf{a})
\end{pmatrix}
$$
- pro funkci $f(x, y, z)$:
$$
H_f(\mathbf{a}) =
\begin{pmatrix}
\frac{\partial^2 f}{\partial x^2}(\mathbf{a}) & \frac{\partial^2 f}{\partial x \partial y}(\mathbf{a}) & \frac{\partial^2 f}{\partial x \partial z}(\mathbf{a}) \\
\frac{\partial^2 f}{\partial y \partial x}(\mathbf{a}) & \frac{\partial^2 f}{\partial y^2}(\mathbf{a}) & \frac{\partial^2 f}{\partial y \partial z}(\mathbf{a}) \\
\frac{\partial^2 f}{\partial z \partial x}(\mathbf{a}) & \frac{\partial^2 f}{\partial z \partial y}(\mathbf{a}) & \frac{\partial^2 f}{\partial z^2}(\mathbf{a})
\end{pmatrix}
$$

### Volné extrémy funkcí
Postup pro hledání extrémů:
1. **stacionární body** funkce $f(x,y)$ -- body, kde je platí $\nabla f(x,y) = \vec{o}$:
    - vypočítám gradient
    - pro $x$-ovou část spočítám, kde se rovná $0$
    - pro $y$-ovou část spočítám, kdy se rovná $0$
    - kombinace souřadnic $\implies$ stacionární body
2. **obecná Hessova matice** $H_f$ pro funkci $f$
3. **vyšetření** $H_f$ v konkrétním stacionárním bodu:
    - použijeme *Sylvestrovo kritérium* :
        - projdeme všechny sub-determinanty
        - pokud jsou pozitivní $\implies$ pozitivně definitní $\implies$ lok. minimum
        - pokud se střídají ve formátu ```-+-+``` $\implies$ negativně definitní $\implies$ lok. maximum
        - jinak $\implies$ indefinitní $implies$ sedlový bod

### Vázané extrémy funkcí
**TODO** (nebyly součástí 1. semestrální písemky)

---

## 2.semestrální písemka

### Změna pořadí integrace 
- nakreslím si situaci
- převedu hraniční body pro druhou souřadnici

### Převod souřadnicových systémů (substituce)
- zavedu substituci pomocí pravidel pro daný souřadnicový systém
- vyjádřím si hraniční body integrace pro souřadnicový systém
- $\Phi$ je transformace souřadnic do daného systému souřadnic
- vytvořím Jakobiho matici $J_\Phi$, spočítám Jakobián $det(J_\Phi)$
- mějme: $\iint_D f(x,y) \, dx\,dy$
- potom: $\iint_{\tilde{D}} f(\Phi(u,v)) \, ||\det(J_\Phi)|| \, du\,dv$ (vynásobíme integrovanou funkci velikostí determinantu $J_\Phi$)
- vybrané souřadnicové systémy:
    - polární: $\Phi(r, \varphi) = (r\cdot\cos(\varphi), r\cdot\sin(\varphi))$ $\implies det(J_\Phi) = r$
    - cylindrické: $\Phi(r, \varphi) = (r\cdot\cos(\varphi), r\cdot\sin(\varphi), z)$ $\implies det(J_\Phi) = r$
    - sférické: $\Phi(r, \varphi, \theta) = (r\sin\theta\cos\varphi, r\sin\theta\sin\varphi, r\cos\theta )$ $\implies det(J_\Phi) = r^2 \cdot \sin\theta$

### Křivkový integrál skalární funkce
- parametricky vyjádříme křivku, najdeme interval parametru -- $[a, b]$, označme $\varphi(t)$ vektor parametrizace
- najdeme derivaci parametrizace $\varphi'(t)$
- lifehack pro parametrizaci přímky: $\varphi(t) = (1-t)\cdot A + B\cdot t$, kde $A = (a_1, a_2), B = (b_1, b_2)$ jsou body této přímky
- integrujeme v intervalu parametru danou skalární funkci:
$$
\int_C f \, ds = \int_a^b f(\varphi(t)) \, \|\varphi'(t)\| \, dt.
$$
(původní funkci s parametrickými souřadnicemi vynásobenou velikostí $\varphi'(t)$)
- zde nezáleží na orientaci průběhu funkce

### Křivkový integrál vektorového pole
- proces je obdobný, jen ale záleží na orientaci průběhu $\tau$ (projeví se znaménkem před integrálem)
- parametricky vyjádříme křivku, najdeme interval parametru -- $[a, b]$, označme $\varphi(t)$ vektor parametrizace
- integrujeme:
$$
\int_{(C,\tau)} F \cdot d\mathbf{s} = \int_a^b F(\varphi(t)) \cdot \varphi'(t) \, dt
$$

### Důležité goniometrické identity
$$
\begin{aligned}
1 &= \sin^2 \varphi + \cos^2 \varphi \\
\sin(2\varphi) &= 2 \sin(\varphi) \cos(\varphi) \\
\cos(2\varphi) &= \cos^2 \varphi - \sin^2 \varphi \\
\cos^2 \varphi &= \frac{1 + \cos(2\varphi)}{2} \\
\sin^2 \varphi &= \frac{1 - \cos(2\varphi)}{2}
\end{aligned}
$$