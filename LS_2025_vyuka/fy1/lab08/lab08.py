import matplotlib.pyplot as plt
import numpy as np

# Časové body pro graf amplitudy v čase
time_steps = np.arange(8)
T_half = 1.739 / 2  # půlperiody pro lokální extrémy
times = time_steps * T_half

# Amplitudy v čase z tabulky posloupnosti
A_IB0 = np.array([19, 18, 17, 16, 16, 14, 14, 13])
A_IB1 = np.array([18, 18, 17, 16, 14, 13, 12, 11])
A_IB2 = np.array([18, 17, 17, 13, 9, 8, 7, 6])
A_IB3 = np.array([15, 15, 15, 9, 5, 4, 3, 2])
A_IB4 = np.array([11, 11, 11, 4, 2, 1, 1, 1])

def fit_line(x, y):
    coef = np.polyfit(x, y, 1)  # lineární fit (1. stupeň)
    return coef

# Fitování jednotlivých dat
coef_IB0 = fit_line(times, A_IB0)
coef_IB1 = fit_line(times, A_IB1)
coef_IB2 = fit_line(times, A_IB2)
coef_IB3 = fit_line(times, A_IB3)
coef_IB4 = fit_line(times, A_IB4)

# === Graf 1: Amplituda v čase ===
plt.figure()
plt.scatter(times, A_IB0, label='$I_{B0}=0$ A', marker='+')
plt.plot(times, np.polyval(coef_IB0, times), linestyle='--')

plt.scatter(times, A_IB1, label='$I_{B1}=0.25$ A', marker='+')
plt.plot(times, np.polyval(coef_IB1, times), linestyle='--')

plt.scatter(times, A_IB2, label='$I_{B2}=0.40$ A', marker='+')
plt.plot(times, np.polyval(coef_IB2, times), linestyle='--')

plt.scatter(times, A_IB3, label='$I_{B3}=0.55$ A', marker='+')
plt.plot(times, np.polyval(coef_IB3, times), linestyle='--')

plt.scatter(times, A_IB4, label='$I_{B4}=0.90$ A', marker='+')
plt.plot(times, np.polyval(coef_IB4, times), linestyle='--')

plt.xlabel('Čas [s]')
plt.ylabel('Amplituda [dílky]')
plt.title('Závislost amplitudy na čase')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig('img/amp_cas.pdf')

# === Graf 2: Amplitudové charakteristiky ===
frequencies = np.array([4.0, 6.3, 6.9, 7.5, 8.0, 9.0, 9.7, 11.0])

def average_amplitude(A_plus, A_minus):
    return (np.abs(A_plus) + np.abs(A_minus)) / 2

# Výchylky z tabulky pro různá tlumení
A_plus_IB0 = np.array([-0.1, -1, -2, -6, -20, -20, -7, -0.1])
A_minus_IB0 = np.array([1.2, 2, 3, 7.2, 20, 20, 8, 1.2])

A_plus_IB1 = np.array([-0.1, -1, -2.2, -7.3, -16, -2, -0.3, 0])
A_minus_IB1 = np.array([1.2, 2.1, 3.1, 8.9, 17, 3, 1.9, 1.1])

A_plus_IB2 = np.array([-0.1, -1, -9, -7, -8, -1, -0.2, 0])
A_minus_IB2 = np.array([1.3, 2.2, 10, 8, 9, 2.1, 1.9, 1.1])

A_plus_IB3 = np.array([-0.1, -0.9, -2, -4.1, -5, -1, -0.2, 0])
A_minus_IB3 = np.array([1.2, 2.1, 3, 5.3, 6.1, 2.2, 1.3, 1.1])

A_plus_IB4 = np.array([-0.1, -1, -1.2, -2, -2, -1, -0.1, 0])
A_minus_IB4 = np.array([1.2, 2, 2.2, 3, 3, 2, 1.3, 1.1])

# Průměrné amplitudy
A_avg_IB0 = average_amplitude(A_plus_IB0, A_minus_IB0)
A_avg_IB1 = average_amplitude(A_plus_IB1, A_minus_IB1)
A_avg_IB2 = average_amplitude(A_plus_IB2, A_minus_IB2)
A_avg_IB3 = average_amplitude(A_plus_IB3, A_minus_IB3)
A_avg_IB4 = average_amplitude(A_plus_IB4, A_minus_IB4)


# Vykreslení amplitudové charakteristiky
plt.figure()
plt.plot(frequencies, A_avg_IB0, marker='o', label='$I_{B0}=0$ A')
plt.plot(frequencies, A_avg_IB1, marker='o', label='$I_{B1}=0.25$ A')
plt.plot(frequencies, A_avg_IB2, marker='o', label='$I_{B2}=0.40$ A')
plt.plot(frequencies, A_avg_IB3, marker='o', label='$I_{B3}=0.55$ A')
plt.plot(frequencies, A_avg_IB4, marker='o', label='$I_{B4}=0.90$ A')

plt.xlabel('Napětí motoru [V]')
plt.ylabel('Průměrná amplituda [dílky]')
plt.title('Amplitudová charakteristika Pohlova kyvadla')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig('img/amp_char.pdf')

