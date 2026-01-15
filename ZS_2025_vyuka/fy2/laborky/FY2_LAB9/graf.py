#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np

t_al = np.array([23.9, 29.4, 34.7, 39.7, 44.6, 49.6, 54.6, 59.6])
l_al = np.array([0.05, 0.15, 0.23, 0.30, 0.34, 0.45, 0.50, 0.56])

t_cu = np.array([27.7, 32.7, 39.7, 42.7, 47.7, 52.7, 57.7, 62.7])
l_cu = np.array([0.04, 0.10, 0.16, 0.24, 0.29, 0.35, 0.40, 0.45])

coef_al = np.polyfit(t_al, l_al, 1)
coef_cu = np.polyfit(t_cu, l_cu, 1)

t_al_fit = np.linspace(t_al.min(), t_al.max(), 100)
l_al_fit = np.polyval(coef_al, t_al_fit)

t_cu_fit = np.linspace(t_cu.min(), t_cu.max(), 100)
l_cu_fit = np.polyval(coef_cu, t_cu_fit)

# Hliník
plt.figure(figsize=(8, 5))
plt.scatter(t_al, l_al, marker="+", s=100, label="Hliník – naměřené")
plt.plot(t_al_fit, l_al_fit, linestyle="--", label="Hliník – fit")
plt.xlabel(r"$t\ \mathrm{[^\circ C]}$")
plt.ylabel(r"$l\ \mathrm{[mm]}$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/al.pdf")
plt.close()

# Mosaz
plt.figure(figsize=(8, 5))
plt.scatter(t_cu, l_cu, marker="+", s=100, label="Mosaz – naměřené")
plt.plot(t_cu_fit, l_cu_fit, linestyle="--", label="Mosaz – fit")
plt.xlabel(r"$t\ \mathrm{[^\circ C]}$")
plt.ylabel(r"$l\ \mathrm{[mm]}$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("img/cuzn.pdf")
plt.close()

