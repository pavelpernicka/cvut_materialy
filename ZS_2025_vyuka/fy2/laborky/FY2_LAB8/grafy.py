#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

nu_s = np.array([0.799, 0.750, 0.705, 0.666, 0.631])
W_s  = np.array([1.2550, 1.0802, 0.9352, 0.8322, 0.7163])

nu_f = np.array([0.519, 0.549, 0.688, 0.735])
W_f  = np.array([0.268, 0.395, 0.841, 1.055])

I = np.array([100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0])

U_375 = np.array([-0.0023, 0.0615, 0.1252, 0.1929, 0.2677,
                  0.3467, 0.4405, 0.5582, 0.6772, 0.8547, 1.2550])

U_425 = np.array([-0.0044, 0.0481, 0.1031, 0.1580, 0.2164,
                  0.2797, 0.3470, 0.4214, 0.5223, 0.6500, 0.9352])

U_475 = np.array([0.0010, 0.0446, 0.0843, 0.1299, 0.1758,
                  0.2241, 0.2737, 0.3335, 0.4031, 0.4982, 0.7163])
                  
coef_s = np.polyfit(nu_s, W_s, 1)
coef_f = np.polyfit(nu_f, W_f, 1)

nu_s_fit = np.linspace(min(nu_s)-0.01, max(nu_s)+0.01, 200)
nu_f_fit = np.linspace(min(nu_f)-0.01, max(nu_f)+0.01, 200)

W_s_fit = coef_s[0] * nu_s_fit + coef_s[1]
W_f_fit = coef_f[0] * nu_f_fit + coef_f[1]

plt.figure(figsize=(8, 5))
plt.scatter(nu_s, W_s, marker="+", label="Spekol – naměřené", s=100)
plt.plot(nu_s_fit, W_s_fit,
         label=fr"Spekol – fit",
          linestyle="--")

plt.scatter(nu_f, W_f, marker="+", label="Filtry – naměřené", s=100)
plt.plot(nu_f_fit, W_f_fit,
         label=fr"Filtry – fit",
         linestyle="--")

plt.xlabel(r"$\nu\ \mathrm{[PHz]}$")
plt.ylabel(r"$W_k\ \mathrm{[eV]}$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/wk_vs_nu.pdf")
plt.close()

plt.figure(figsize=(8, 5))
plt.plot(I, U_375, marker="o", label=r"$\lambda = 375\,\mathrm{nm}$")
plt.plot(I, U_425, marker="o", label=r"$\lambda = 425\,\mathrm{nm}$")
plt.plot(I, U_475, marker="o", label=r"$\lambda = 475\,\mathrm{nm}$")

plt.xlabel(r"$I\ \mathrm{[\mu A]}$")
plt.ylabel(r"$U\ \mathrm{[V]}$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/U_vs_I.pdf")
plt.close()

