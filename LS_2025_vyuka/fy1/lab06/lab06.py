"""
  Výpočetní a vizualizační skript pro laborku 6
"""

import matplotlib.pyplot as plt
import numpy as np

#np.set_printoptions(precision=30, suppress=True)

# Data
U_z = np.array([500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000])
Ux_cervene = np.array([0.56, 1.00, 1.45, 1.95, 2.6, 2.92, 3.50, 4.00, 4.40, 4.95])
Ux_vzduch1 = np.array([0.22, 0.38, 0.56, 0.74, 0.91, 1.15, 1.25, 1.40, 1.60, 1.75])
Ux_pruhledne = np.array([0.74, 1.45, 2.10, 2.85, 3.45, 4.10, 4.90, 5.60, 6.10, 7.10])
Ux_vzduch2 = np.array([0.24, 0.42, 0.60, 0.79, 0.98, 1.20, 1.40, 1.55, 1.70, 1.90])
C_REF = 0.22e-6  # [F]

# Výpočet náboje v uC
def Q(Uz, Ux): return C_REF * (Uz * Ux) / (Uz - Ux)
Q_cervene = Q(U_z, Ux_cervene)
Q_vzduch1 = Q(U_z, Ux_vzduch1)
Q_pruhledne = Q(U_z, Ux_pruhledne)
Q_vzduch2 = Q(U_z, Ux_vzduch2)

# Aproximace polynomem 1. stupně - vyplivne array členů polynomu, zde [A, b]
fit_cervene = np.polyfit(U_z, Q_cervene, 1)
fit_vzduch1 = np.polyfit(U_z, Q_vzduch1, 1)
fit_pruhledne = np.polyfit(U_z, Q_pruhledne, 1)
fit_vzduch2 = np.polyfit(U_z, Q_vzduch2, 1)

# Odchylka podle směrnice
def odchylka(x, y):
    n = len(x)
    x_mean = np.mean(x)
    S_xx = np.sum((x - x_mean) ** 2)
    y_pred = np.polyval(np.polyfit(x, y, 1), x)
    residuals = y - y_pred
    s = np.sqrt(np.sum(residuals ** 2) / (n - 2))
    return s / np.sqrt(S_xx)

u_cervene = odchylka(U_z, Q_cervene)
u_vzduch1 = odchylka(U_z, Q_vzduch1)
u_pruhledne = odchylka(U_z, Q_pruhledne)
u_vzduch2 = odchylka(U_z, Q_vzduch2)

out = {
    "Červený plast": {
        "fit": f"Q = {fit_cervene[0]:.5f}·U + {fit_cervene[1]:.2f}",
        "kapacita": fit_cervene[0], #[F]
        "nejistota": u_cervene,
    },
    "Vzduch (d_č)": {
        "fit": f"Q = {fit_vzduch1[0]:.5f}·U + {fit_vzduch1[1]:.2f}",
        "kapacita": fit_vzduch1[0],
        "nejistota": u_vzduch1,
    },
    "Průhledný plast": {
        "fit": f"Q = {fit_pruhledne[0]:.5f}·U + {fit_pruhledne[1]:.2f}",
        "kapacita": fit_pruhledne[0],
        "nejistota": u_pruhledne,
    },
    "Vzduch (d_p)": {
        "fit": f"Q = {fit_vzduch2[0]:.5f}·U + {fit_vzduch2[1]:.2f}",
        "kapacita": fit_vzduch2[0],
        "nejistota": u_vzduch2
    }
}

print(out)
x_fit = np.linspace(500, 5000, 200)

# Červený plast + vzduch
plt.figure()
plt.scatter(U_z, Q_cervene, color="blue", marker="+", s=100, label="Červený plast")
plt.scatter(U_z, Q_vzduch1, color="red", marker="x", s=100, label="Vzduch (d_č)")
plt.plot(x_fit, np.polyval(fit_cervene, x_fit), "b-", linewidth=1)
plt.plot(x_fit, np.polyval(fit_vzduch1, x_fit), "r-", linewidth=1)
plt.xlabel("U [V]")
plt.ylabel("Q [µC]")
plt.title("Závislost náboje kondenzátoru na napětí")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/cerveny_plast.pdf")

# Průhledný plast + vzduch
plt.figure()
plt.scatter(U_z, Q_pruhledne, color="blue", marker="+", s=100, label="Průhledný plast")
plt.scatter(U_z, Q_vzduch2, color="red", marker="x", s=100, label="Vzduch (d_p)")
plt.plot(x_fit, np.polyval(fit_pruhledne, x_fit), "b-", linewidth=1)
plt.plot(x_fit, np.polyval(fit_vzduch2, x_fit), "r-", linewidth=1)
plt.xlabel("U [V]")
plt.ylabel("Q [µC]")
plt.title("Závislost náboje kondenzátoru na napětí")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/pruhledny_plast.pdf")
plt.show()

