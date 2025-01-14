#!/usr/bin/env python3

cifry = "0123456789abcdefghijklmnopqrstuvwxyz"

def validuj_vstup(zaklad, cisla):
    for cislo in cisla:
        tecka_count = 0
        for znak in cislo:
            if znak == '.':
                tecka_count += 1
                if tecka_count > 1:
                    return False
            elif znak not in cifry[:zaklad]:
                return False
    return True

def zarovnej_cisla(a, b):
    a_left, a_right = (a.split('.') + ["0"])[0:2]
    b_left, b_right = (b.split('.') + ["0"])[0:2]
    max_left_len = max(len(a_left), len(b_left))
    max_right_len = max(len(a_right), len(b_right))
    a = a_left.rjust(max_left_len, '0') + '.' + a_right.ljust(max_right_len, '0') if max_right_len > 0 else a_left.rjust(max_left_len, '0')
    b = b_left.rjust(max_left_len, '0') + '.' + b_right.ljust(max_right_len, '0') if max_right_len > 0 else b_left.rjust(max_left_len, '0')
    return a, b

def secti(zaklad, a, b):
    a, b = zarovnej_cisla(a, b)
    vysledek = []
    prechod = 0
    for i in range(len(a) - 1, -1, -1):
        if a[i] == '.':
            vysledek.append('.')
            continue
        soucet = cifry.index(a[i]) + cifry.index(b[i]) + prechod
        vysledek.append(cifry[soucet % zaklad])
        prechod = soucet // zaklad
    if prechod > 0:
        vysledek.append(cifry[prechod])
    return ''.join(vysledek[::-1])

def odecti(zaklad, a, b):
    a, b = zarovnej_cisla(a, b)
    vysledek = []
    navic = 0
    for i in range(len(a) - 1, -1, -1):
        if a[i] == '.':
            vysledek.append('.')
            continue
        cifra_a = cifry.index(a[i]) - navic
        cifra_b = cifry.index(b[i])
        if cifra_a < cifra_b:
            cifra_a += zaklad
            navic = 1
        else:
            navic = 0
        rozdil = cifra_a - cifra_b
        vysledek.append(cifry[rozdil])
    while len(vysledek) > 1 and vysledek[-1] == '0':
        vysledek.pop()
    return ''.join(vysledek[::-1])

def oddelej_nuly(vysledek):
    if '.' in vysledek:
        left, right = vysledek.split('.')
        left = left.lstrip('0') or '0'
        right = right.rstrip('0')
        return left if not right else left + '.' + right
    return vysledek.lstrip('0') or '0'

def porovnej_cisla(a, b):
    a_neg, b_neg = a.startswith('-'), b.startswith('-')
    if a_neg != b_neg:
        return b_neg
    a, b = a.lstrip('-'), b.lstrip('-')
    a, b = zarovnej_cisla(a, b)
    return a > b if not a_neg else a < b

def spocitej(zaklad, cisla):
    if not validuj_vstup(zaklad, cisla):
        return "ERROR"
    secteno = secti(zaklad, cisla[0], cisla[1])
    if porovnej_cisla(secteno, cisla[2]):
        odecteno = odecti(zaklad, secteno, cisla[2])
    else:
        odecteno = odecti(zaklad, cisla[2], secteno)
        if odecteno != '0':
            odecteno = '-' + odecteno
    return oddelej_nuly(odecteno)

# testy
def test_spocitej():
    test_cases = [
        (4, ["10.1313", "11.2302214", "23021.331"], "ERROR"),
        (2, ["1.10011", "10.011", "1101.0011"], "-1001.00111"),
        (3, ["1.2222", "1.0121", "2.12"], "0.122"),
        (31, ["o.rc704", "2s.86m", "34sr.14"], "-34p4.rg1ur"),
        (16, ["17", "1.e59385", "0.2fa"], "-b.2d464c"),
        (33, ["pm.ttnp1", "l.e12w", "n.m6hqnq"], "pk.lo8ua7")
    ]
    for index, (zaklad, cisla, expected) in enumerate(test_cases, start=1):
        result = spocitej(zaklad, cisla)
        if result == expected:
            print(f"Test {index}: Prošel ({cisla}) -> {result}")
        else:
            print(f"Test {index}: Selhal ({cisla}) -> Výsledek: {result}, Očekáváno: {expected}")

#test_spocitej()

zaklad = int(input())
a, b, c = input().strip(), input().strip(), input().strip()
vysledek = spocitej(zaklad, [a, b, c])
print(vysledek)
