#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional, Tuple
import matplotlib.pyplot as plt
import os


@dataclass
class SpeData:
    counts: List[int]
    live_time_s: Optional[int]
    real_time_s: Optional[int]
    mca_cal_keV: Optional[Tuple[float, ...]]


def read_spe(path: str) -> SpeData:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    counts = []
    live = real = None
    cal = None
    i = 0

    while i < len(lines):
        s = lines[i].strip()

        if s == "$MEAS_TIM:":
            i += 1
            live, real = map(int, lines[i].split())

        elif s == "$DATA:":
            i += 1
            a, b = map(int, lines[i].split())
            i += 1
            while len(counts) < b - a + 1:
                if lines[i].startswith("$"):
                    break
                counts.append(int(lines[i]))
                i += 1
            continue

        elif s == "$MCA_CAL:":
            i += 1
            k = int(lines[i])
            i += 1
            cal = tuple(float(x) for x in lines[i].replace("keV", "").split()[:k])

        i += 1

    return SpeData(counts, live, real, cal)


def energy_axis(n: int, cal: Tuple[float, ...]) -> List[float]:
    a = cal[0] if len(cal) > 0 else 0
    b = cal[1] if len(cal) > 1 else 0
    c = cal[2] if len(cal) > 2 else 0
    return [a + b * i + c * i * i for i in range(n)]


def smooth(y: List[int], w: int) -> List[float]:
    p = [0]
    for v in y:
        p.append(p[-1] + v)
    return [
        (p[min(len(y), i + w + 1)] - p[max(0, i - w)]) / (min(len(y), i + w + 1) - max(0, i - w))
        for i in range(len(y))
    ]


def detect_peaks(y: List[float], min_dist: int, thr: float) -> List[int]:
    peaks = []
    for i in range(min_dist, len(y) - min_dist):
        if y[i] > thr and all(y[i] >= y[j] for j in range(i - min_dist, i + min_dist)):
            peaks.append(i)
    return peaks


def plot_spectrum(spe: SpeData, title: str, save: str):
    y = spe.counts
    x = energy_axis(len(y), spe.mca_cal_keV)
    ys = smooth(y, 100)

    thr = 0.06 * max(ys)
    peaks = detect_peaks(ys, 500, thr)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.step(x, y, where="mid", alpha=0.4, label="Naměřené spektrum")
    ax.plot(x, ys, label="Vyhlazené spektrum")

    E_MIN = 200
    ax.axvspan(
        x[0], E_MIN,
        color="red",
        alpha=0.15,
        label="Ignorovaná oblast"
    )

    first_peak = True
    for i in peaks:
        if x[i] < E_MIN:
            continue

        ax.axvline(
            x[i],
            linestyle="--",
            color="red",
            label="Detekované peaky" if first_peak else None
        )
        first_peak = False

        ax.text(
            x[i],
            ys[i] * 1.04,
            f"{x[i]:.0f}",
            ha="center",
            fontsize=10,
            bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", boxstyle="round,pad=0.05")
        )

    ax.set(
        xlabel="Energie (keV)",
        ylabel="Počet impulzů",
        title=f"Gama spektrum ({title})"
    )
    ax.grid(True)
    ax.legend(loc="upper right")

    fig.tight_layout()
    fig.savefig(save)
    plt.show()



if __name__ == "__main__":
    data = [
        ("../data/co60_v1.Spe", "Cobalt 60 – měření 1"),
        ("../data/co60_v2.Spe", "Cobalt 60 – měření 2"),
        ("../data/co60_v3.Spe", "Cobalt 60 – měření 3"),
        ("../data/co60_v4.Spe", "Cobalt 60 – měření 4"),
        ("../data/na22_final.Spe", "Sodík 22 - měření 1"),
        ("../data/na22_stineny.Spe", "Sodík 22 - měření 2"),
        ("../data/pozadi_1800s.Spe", "Pozadí"),
    ]

    os.makedirs("../tex/img/charts", exist_ok=True)

    for path, name in data:
        spe = read_spe(path)
        out = f"../tex/img/charts/{os.path.splitext(os.path.basename(path))[0]}_peaks.pdf"
        plot_spectrum(spe, name, out)

