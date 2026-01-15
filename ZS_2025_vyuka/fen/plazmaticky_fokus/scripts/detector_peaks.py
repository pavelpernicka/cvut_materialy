#!/usr/bin/env python3
import argparse
import csv
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class Trace:
    t: list[float]   # seconds
    y: list[float]


def moving_average(y: list[float], win: int) -> list[float]:
    if win <= 1:
        return y[:]
    out = [0.0] * len(y)
    s = 0.0
    q = []
    for i, v in enumerate(y):
        q.append(v)
        s += v
        if len(q) > win:
            s -= q.pop(0)
        out[i] = s / len(q)
    return out


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    a = sorted(values)
    n = len(a)
    mid = n // 2
    if n % 2 == 1:
        return a[mid]
    return 0.5 * (a[mid - 1] + a[mid])


def load_tektronix_csv(path: str, ch1_name: str = "CH1", ch2_name: str = "CH2") -> tuple[Trace, Trace]:
    with open(path, "r", newline="") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("TIME,"):
            header_idx = i
            break
    if header_idx is None:
        raise SystemExit("Nenalezen řádek 'TIME,...' v CSV.")

    reader = csv.reader(lines[header_idx:])
    cols = next(reader)

    idx_time = cols.index("TIME") if "TIME" in cols else 0
    idx_ch1 = cols.index(ch1_name)
    idx_ch2 = cols.index(ch2_name)

    t = []
    y1 = []
    y2 = []
    for row in reader:
        if not row or len(row) <= max(idx_time, idx_ch1, idx_ch2):
            continue
        if row[idx_time].strip() == "":
            continue
        t.append(float(row[idx_time]))
        y1.append(float(row[idx_ch1]))
        y2.append(float(row[idx_ch2]))

    return Trace(t, y1), Trace(t, y2)


def find_peaks_indices(
    t: list[float],
    y: list[float],
    smooth_win: int,
    min_sep_s: float,
    baseline_n: int,
    k_sigma: float,
    max_peaks: int = 4,
) -> list[int]:
    n = len(y)
    if n < 5:
        return []

    b = median(y[: max(10, min(baseline_n, n))])
    y0 = [v - b for v in y]

    ys = moving_average(y0, smooth_win)
    abs_ys = [abs(v) for v in ys]

    base = abs_ys[: max(10, min(baseline_n, n))]
    m = median(base)
    mad = median([abs(v - m) for v in base])
    robust_sigma = 1.4826 * mad if mad > 0 else (m if m > 0 else 1e-12)
    thr = k_sigma * robust_sigma

    cand = []
    for i in range(1, n - 1):
        if abs_ys[i] > thr and abs_ys[i] >= abs_ys[i - 1] and abs_ys[i] >= abs_ys[i + 1]:
            cand.append(i)

    cand.sort(key=lambda i: abs_ys[i], reverse=True)

    selected = []
    for i in cand:
        ok = True
        for j in selected:
            if abs(t[i] - t[j]) < min_sep_s:
                ok = False
                break
        if ok:
            selected.append(i)
        if len(selected) >= max_peaks:
            break

    selected.sort(key=lambda i: t[i])
    return selected


def crop_trace(tr: Trace, tmin: float | None, tmax: float | None) -> Trace:
    if tmin is None and tmax is None:
        return tr
    tt = []
    yy = []
    for ti, yi in zip(tr.t, tr.y):
        if tmin is not None and ti < tmin:
            continue
        if tmax is not None and ti > tmax:
            continue
        tt.append(ti)
        yy.append(yi)
    return Trace(tt, yy)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--smooth-win", type=int, default=200)
    ap.add_argument("--min-sep-ns", type=float, default=20.0)
    ap.add_argument("--baseline-n", type=int, default=20000)
    ap.add_argument("--k-sigma", type=float, default=8.0)
    ap.add_argument("--tmin", type=float, default=None)
    ap.add_argument("--tmax", type=float, default=None)
    ap.add_argument("--save", default=None, help="např. ../tex/img/charts/peaks.pdf")
    ap.add_argument("--dt-from", choices=["ch1", "ch2"], default="ch2")
    args = ap.parse_args()

    tr1, tr2 = load_tektronix_csv(args.csv_path, "CH1", "CH2")
    tr1 = crop_trace(tr1, args.tmin, args.tmax)
    tr2 = crop_trace(tr2, args.tmin, args.tmax)

    min_sep_s = args.min_sep_ns * 1e-9

    p1 = find_peaks_indices(tr1.t, tr1.y, args.smooth_win, min_sep_s, args.baseline_n, args.k_sigma)
    p2 = find_peaks_indices(tr2.t, tr2.y, args.smooth_win, min_sep_s, args.baseline_n, args.k_sigma)

    if len(p1) < 2 or len(p2) < 2:
        raise SystemExit(f"Jsou potřeba alespon 2 peaky CH1={len(p1)}, CH2={len(p2)}.")

    # Peak 1 = fotony, Peak 2 = neutrony
    i_g1, i_n1 = p1[0], p1[1]
    i_g2, i_n2 = p2[0], p2[1]

    t_g1, t_n1 = tr1.t[i_g1], tr1.t[i_n1]
    t_g2, t_n2 = tr2.t[i_g2], tr2.t[i_n2]

    dt_ng_ch1 = t_n1 - t_g1
    dt_ng_ch2 = t_n2 - t_g2

    print("Peaky t[ns]:")
    print(f"  CH1: gamma t = {t_g1*1e9:.3f} ns, neutron t = {t_n1*1e9:.3f} ns, Δt(n-γ) = {dt_ng_ch1*1e9:.3f} ns")
    print(f"  CH2: gamma t = {t_g2*1e9:.3f} ns, neutron t = {t_n2*1e9:.3f} ns, Δt(n-γ) = {dt_ng_ch2*1e9:.3f} ns")

    dt_used = dt_ng_ch2 if args.dt_from == "ch2" else dt_ng_ch1
    print(f"\nPoužité dt(n-γ) z {args.dt_from.upper()}: {dt_used*1e9:.3f} ns")

    # ---- Plot in microseconds ----
    t1_us = [ti * 1e6 for ti in tr1.t]
    t2_us = [ti * 1e6 for ti in tr2.t]

    t_g1_us, t_n1_us = t_g1 * 1e6, t_n1 * 1e6
    t_g2_us, t_n2_us = t_g2 * 1e6, t_n2 * 1e6

    fig, ax = plt.subplots(figsize=(8, 5))
    #ax.plot(t1_us, tr1.y, label="CH1 (bližší)")
    ax.plot(t2_us, tr2.y, label="CH2 (vzdálenější)")

    #ax.scatter([t_g1_us], [tr1.y[i_g1]], marker="x", s=80, label="CH1 fotonový peak")
    #ax.scatter([t_n1_us], [tr1.y[i_n1]], marker="o", s=80, label="CH1 neutronový peak")
    ax.scatter([t_g2_us], [tr2.y[i_g2]], marker="o", s=80, label="CH2 fotonový peak", color="red")
    ax.scatter([t_n2_us], [tr2.y[i_n2]], marker="o", s=80, label="CH2 neutronový peak", color="orange")

    #ax.axvline(t_g1_us, linestyle="--", linewidth=1.2)
    #ax.axvline(t_n1_us, linestyle="--", linewidth=1.2)
    ax.axvline(t_g2_us, linestyle="--", linewidth=1.2, color="red")
    ax.axvline(t_n2_us, linestyle="--", linewidth=1.2, color="orange")

    ax.set_title(rf"$\Delta t_{{n-\gamma}}$ ({args.dt_from.upper()}) = {dt_used*1e9:.3f} ns")
    ax.set_xlabel(r"Čas $[\mu\mathrm{s}]$")
    ax.set_ylabel(r"Napětí $[\mathrm{V}]$")
    ax.grid(True, alpha=0.3)

    ax.set_xlim(0.25, 1.25)

    ax.legend()
    plt.tight_layout()

    if args.save is not None:
        fig.savefig(args.save)

    plt.show()


if __name__ == "__main__":
    main()

