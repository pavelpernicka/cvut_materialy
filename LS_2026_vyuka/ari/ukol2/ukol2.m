%% stabilita
% Zjistím vlastní čísla té matice
A = [ 0       0       0       1      0      0;
      0       0       0       0      1      0;
      0       0       0       0      0      1;
      7.3809  0       0       0      2      0;
      0      -2.1904  0      -2      0      0;
      0       0      -3.1904  0      0      0 ];

lambda = eig(A)
% Musí splňovat Re lambda < 0 - to nesplňují => systém je nestabilní

%% Pomocí kterého vstupu je systém řiditelný?
% Pro každý vstup b1, b2, b3 sestavíme matici řiditelnosti C ([b, Ab, A^2b ... A^{n-1}b], resp. funkce ctrb(A,bn);) a podíváme se
% na její rank. Pokud By byl systém některým vstupem řiditelný, měla by
% rank(C) = řád systému = 6.
A = [ 0       0       0       1      0      0;
      0       0       0       0      1      0;
      0       0       0       0      0      1;
      7.3809  0       0       0      2      0;
      0      -2.1904  0      -2      0      0;
      0       0      -3.1904  0      0      0 ];

b1 = [0;0;0;1;0;0];
b2 = [0;0;0;0;1;0];
b3 = [0;0;0;0;0;1];

Co1 = ctrb(A,b1);
Co2 = ctrb(A,b2);
Co3 = ctrb(A,b3);

r1 = rank(Co1) %4
r2 = rank(Co2) %4
r3 = rank(Co3) %2

% Z toho plyne, že systém není plně řiditelný pomocí žádného z motorů (pokud je bereme samostatně)

%% Přenosy u každého motoru jednotlivě
% Přenos z matice A a vstupů b1, b2, b3 spočítám jako
% H(s) = (sIdentita-A)^{-1} * b_n.

A = [ 0       0       0       1      0      0;
      0       0       0       0      1      0;
      0       0       0       0      0      1;
      7.3809  0       0       0      2      0;
      0      -2.1904  0      -2      0      0;
      0       0      -3.1904  0      0      0 ];

b1 = [0;0;0;1;0;0];
b2 = [0;0;0;0;1;0];
b3 = [0;0;0;0;0;1];

syms s
I = eye(size(A,1));

H1 = simplify((s*I - A)\b1)
H2 = simplify((s*I - A)\b2)
H3 = simplify((s*I - A)\b3)

% v maticích přenosů vidíme nulové řádky, což nám ukazuje na totéž, co
% předchozí bod.

%% Řiditelnost všemi motory zaráz
A = [ 0       0       0       1      0      0;
      0       0       0       0      1      0;
      0       0       0       0      0      1;
      7.3809  0       0       0      2      0;
      0      -2.1904  0      -2      0      0;
      0       0      -3.1904  0      0      0 ];

b1 = [0;0;0;1;0;0];
b2 = [0;0;0;0;1;0];
b3 = [0;0;0;0;0;1];

B  = [b1 b2 b3];
Co = ctrb(A,B);
rank(Co)

% Zde nám vyjde rank 6, systém je tedy řiditený pomocí všech motorů zaráz

%% Přenos se všemi motory zaráz
A = [ 0       0       0       1      0      0;
      0       0       0       0      1      0;
      0       0       0       0      0      1;
      7.3809  0       0       0      2      0;
      0      -2.1904  0      -2      0      0;
      0       0      -3.1904  0      0      0 ];

b1 = [0;0;0;1;0;0];
b2 = [0;0;0;0;1;0];
b3 = [0;0;0;0;0;1];

B  = [b1 b2 b3];

syms s
I = eye(size(A,1));

H1 = simplify((s*I - A)\B)

% Tady už nejsou nulové řádky
%[  -(10000*(625*s^2 + 1369))/(- 6250000*s^4 + 7440625*s^2 + 101044521),                -(12500000*s)/(- 6250000*s^4 + 7440625*s^2 + 101044521),                        0]
%[               (12500000*s)/(- 6250000*s^4 + 7440625*s^2 + 101044521),   -(625*(10000*s^2 - 73809))/(- 6250000*s^4 + 7440625*s^2 + 101044521),                        0]
%[                                                                    0,                                                                      0,     625/(625*s^2 + 1994)]
%[-(10000*s*(625*s^2 + 1369))/(- 6250000*s^4 + 7440625*s^2 + 101044521),              -(12500000*s^2)/(- 6250000*s^4 + 7440625*s^2 + 101044521),                        0]
%[             (12500000*s^2)/(- 6250000*s^4 + 7440625*s^2 + 101044521), -(625*s*(10000*s^2 - 73809))/(- 6250000*s^4 + 7440625*s^2 + 101044521),                        0]
%[                                                                    0,                                                                      0, (625*s)/(625*s^2 + 1994)]
 