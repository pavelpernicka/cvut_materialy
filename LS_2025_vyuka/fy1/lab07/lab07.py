import matplotlib.pyplot as plt
import numpy as np

def print_table(matrix):
    rounded = np.round(matrix.astype(float), 4).astype(str)
    col_widths = [max(len(cell) for cell in rounded[:, i]) for i in range(rounded.shape[1])]
    border = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'

    def format_row(row):
        return "| " + " | ".join(cell.ljust(w) for cell, w in zip(row, col_widths)) + " |"

    print('=' * (sum(col_widths) + 3 * len(col_widths) + 1))
    print(format_row(rounded[0]))
    print('=' * (sum(col_widths) + 3 * len(col_widths) + 1))
    for row in rounded[1:]:
        print(format_row(row))
        print(border)

Ils = np.array([1, 2, 3, 4, 5])
Ims = np.array([0.20, 0.38, 0.54, 0.72, 0.90])
initial_gramms = np.array([33.42, 38.72])
lengths = [25, 50]
g = 9.81

l25_grams = np.array([
    [33.43, 33.53, 33.67, 33.74, 33.84],
    [33.60, 33.80, 34.00, 34.16, 34.35],
    [33.70, 34.00, 34.27, 34.60, 34.85],
    [33.81, 34.20, 34.55, 34.93, 35.33],
    [33.93, 34.41, 34.87, 35.41, 35.80],
])

l50_grams = np.array([
    [38.97, 39.13, 39.33, 39.50, 39.67],
    [39.20, 39.54, 39.90, 40.24, 40.57],
    [39.40, 39.92, 40.47, 41.00, 41.42],
    [39.67, 40.33, 41.02, 41.73, 42.30],
    [39.89, 40.70, 41.52, 42.42, 43.21],
])

all_grams = [l25_grams, l50_grams]
corrected = [grams - initial_gramms[i] for i, grams in enumerate(all_grams)]
F = [c * g for c in corrected]

fixed_Il = 3
fixed_Im = 0.90
fixed_Im_index = 3
F_per_l = {12.5: (34.21-33.35)*g, 25: F[0][fixed_Il][fixed_Im_index], 50:F[1][fixed_Il][fixed_Im_index], 100: (44.93-39.40)*g}

initial_B = 168 #mT
initial_Im = 0.87 #A
B_factor = initial_B/initial_Im
B_conversion_dict = {}
for Im in Ims:
	B_conversion_dict[Im] = Im*B_factor
	
theoretical_F_per_l = {}
for l in F_per_l.keys(): # [mN]
	theoretical_F_per_l[l] = B_conversion_dict[fixed_Im] * fixed_Il * l /1000 # because A used instead of mA

theoretical_F_per_Im = {}
for Im, B in B_conversion_dict.items():
	theoretical_F_per_Im[Im] = B * Ils[0] * lengths[1] /1000

print("Původní hodnoty:")
for i, length in enumerate(lengths):
    print(f"Délka l={length}:")
    print_table(all_grams[i])

print("Corrected hmotnosti:")
for i, length in enumerate(lengths):
    print(f"Délka l={length}:")
    print_table(corrected[i])

print("Spočítané síly:")
for i, length in enumerate(lengths):
    print(f"Délka l={length}:")
    print_table(F[i])
    
print(f"Závislost síly na délce (Im={fixed_Im}, Il={fixed_Il}):")
print(F_per_l)

print(f"Převodní tabulka B:")
print(B_conversion_dict)

print(f"Teoretické F pro délky:")
print(theoretical_F_per_l)

print(f"Teoretické F pro Im:")
print(theoretical_F_per_Im)

# tady chci vykreslit tyto grafy (každý z bodů níže je jeden graf, nekombinuj do sebe):
# závislost F na Il z array F, bude víc přímek - pro  všechna Im, prolož jednotlivé datové sady přímkami
# závislost F na Im z array F, bude víc přímek - pro  všechna Il, prolož jednotlivé datové sady přímkami
# závislost F na délce z F_per_l, a teorerickou hodnotu z theoretical_F_per_l, prolož naměřené hodnoty přímkami
# závislost F na Im z array F při Ils[0] a lengths[1], ateoretickou hodnotu theoretical_F_per_Im, prolož naměřené hodnoty přímkami

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "text.latex.preamble": r"\usepackage[czech]{babel}"
})

# F na I_l
plt.figure(figsize=(8, 5))
x_fit = np.linspace(min(Ils), max(Ils), 200)
l_index = 1

for j, Im in enumerate(Ims):
    y_vals = F[l_index][:, j]  # všechna Il (osová řada), daný Im
    fit = np.polyfit(Ils, y_vals, 1)
    plt.scatter(Ils, y_vals, s=100, marker="+", label=f"$I_m={Im:.2f}\ A$")
    plt.plot(x_fit, np.polyval(fit, x_fit), linewidth=1)
plt.xlabel("$I_L$ [A]")
plt.ylabel("$F$ [mN]")
#plt.title("Závislost síly $F$ na $I_L$ při $l=50\ mm$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/F_vs_Il.pdf", bbox_inches='tight', pad_inches=0)

# F na I_m
plt.figure(figsize=(8, 5))
x_fit = np.linspace(min(Ims), max(Ims), 200)
l_index = 1  # délka 50 cm

for i, Il in enumerate(Ils):
    y_vals = F[l_index][i, :]  # všechna Im pro daný Il
    fit = np.polyfit(Ims, y_vals, 1)
    plt.scatter(Ims, y_vals, s=100, marker="+", label=f"$I_L={Il}\ A$")
    plt.plot(x_fit, np.polyval(fit, x_fit), linewidth=1)
plt.xlabel("$I_m$ [A]")
plt.ylabel("$F$ [mN]")
#plt.title("Závislost síly $F$ na $I_m$ při $l=50\ mm$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/F_vs_Im.pdf", bbox_inches='tight', pad_inches=0)

# F na l + porovnání s teorií
plt.figure(figsize=(8, 5))
real_lengths = list(F_per_l.keys())
real_forces = list(F_per_l.values())
theoretical_forces = [theoretical_F_per_l[l] for l in real_lengths]
fit = np.polyfit(real_lengths, real_forces, 1)
x_fit = np.linspace(min(real_lengths), max(real_lengths), 200)

plt.scatter(real_lengths, real_forces, color="blue", marker="+", s=100, label="Naměřené hodnoty")
plt.plot(x_fit, np.polyval(fit, x_fit), "b-", linewidth=1)
plt.plot(real_lengths, theoretical_forces, "r--", label="Teoretické hodnoty")
plt.xlabel("$l$ [mm]")
plt.ylabel("$F$ [mN]")
#plt.title("Srovnání závislosti síly $F$ na délce $l$ ($I_m={:.2f}\ A$, $I_L={}\ A$) s teorií".format(fixed_Im, fixed_Il))
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/F_vs_l_measured_theory.pdf", bbox_inches='tight', pad_inches=0)

# F na Im + porovnání s teorií
plt.figure(figsize=(8, 5))
F_for_Im = [F[1][0, i] for i in range(len(Ims))]
F_theoretical_Im = [theoretical_F_per_Im[Im] for Im in Ims]
fit = np.polyfit(Ims, F_for_Im, 1)
x_fit = np.linspace(min(Ims), max(Ims), 200)

plt.scatter(Ims, F_for_Im, color="blue", marker="+", s=100, label="Naměřené hodnoty")
plt.plot(x_fit, np.polyval(fit, x_fit), "b-", linewidth=1)
plt.plot(Ims, F_theoretical_Im, "r--", label="Teoretické hodnoty")
plt.xlabel("$I_m$ [A]")
plt.ylabel("$F$ [mN]")
#plt.title("Srovnání závislost síly $F$ na $I_m$ ($I_L={}\ A$, $l=50\ mm$) s teorií".format(Ils[0]))
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/F_vs_Im_theory_single.pdf", bbox_inches='tight', pad_inches=0)

plt.show()
