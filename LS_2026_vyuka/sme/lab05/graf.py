#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

vin = np.array([0.0, 0.060, 1.0, 2.5, 5.0, 7.5, 9.0, 9.9])
digital = np.array([0, 1, 25, 64, 128, 192, 231, 254])

ideal = np.round(vin / 10.0 * 255.0)
deviation = digital - ideal

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(vin, digital, marker='o', label='Naměřená charakteristika')
ax.plot(vin, ideal, marker='s', linestyle='--', label='Ideální charakteristika')
ax.set_xlabel('Vstupní napětí $V_{in}$ [V]')
ax.set_ylabel('Digitální hodnota [arb.]')
ax.grid(True)
ax.legend()
plt.tight_layout()
path1 = "char.pdf"
plt.savefig(path1)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 5))
ax.axhline(0, linestyle='--', color='red')
ax.plot(vin, deviation, marker='o')
ax.set_xlabel('Vstupní napětí $V_{in}$ [V]')
ax.set_ylabel('Odchylka hodnoty [arb.]')
ax.grid(True)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
plt.tight_layout()
path2 = "odchylka.pdf"
plt.savefig(path2)
plt.close(fig)
