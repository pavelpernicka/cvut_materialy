#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from get_lines import retrieve_nist_lines
import os

from img2spectrum import Spectrum, SpectroConfig, VisualSpectrum

def _scale_sticks_to_match(y_sticks, y_target):
    ys = np.asarray(y_sticks, dtype=float)
    yt = np.asarray(y_target, dtype=float)

    ys_max = float(np.max(ys)) if ys.size else 0.0
    yt_max = float(np.max(yt)) if yt.size else 0.0

    if ys_max <= 0.0 or yt_max <= 0.0:
        return ys

    return ys * (0.8 * yt_max / ys_max)


def plot_nist_only(element: str, lambda_from: float, lambda_to: float, title=None, save=None, show_visible_band=True):
    wl, inten = retrieve_nist_lines(element, lambda_from, lambda_to)

    wl = np.asarray(wl, dtype=float)
    inten = np.asarray(inten, dtype=float)

    fig, ax = plt.subplots(figsize=(8, 5))

    if show_visible_band:
        ax.axvspan(380, 750, color="violet", alpha=0.3, label="Viditelné spektrum (cca 380–750 nm)")

    ax.vlines(wl, ymin=0, ymax=inten, colors="red", linewidth=1.2, alpha=0.8)

    ax.set_xlabel("λ [nm]")
    ax.set_ylabel("Rel. intenzita")
    ax.set_title(title if title is not None else f"Spektrální čáry z NIST: {element}")
    ax.grid(True)

    cursor_line = ax.axvline(wl[0] if wl.size else lambda_from, linestyle="--", linewidth=1)
    ann = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(10, 10),
        textcoords="offset points",
        bbox=dict(boxstyle="round", fc="white", ec="0.5", alpha=0.9),
        fontsize=9,
        visible=False,
    )

    wl_sorted_idx = np.argsort(wl)
    wl_sorted = wl[wl_sorted_idx]
    inten_sorted = inten[wl_sorted_idx]

    def on_move(event):
        if event.inaxes is not ax or event.xdata is None:
            ann.set_visible(False)
            fig.canvas.draw_idle()
            return

        x = float(event.xdata)

        j = int(np.searchsorted(wl_sorted, x))
        if j <= 0:
            k = 0
        elif j >= wl_sorted.size:
            k = wl_sorted.size - 1
        else:
            left = j - 1
            right = j
            k = left if abs(wl_sorted[left] - x) <= abs(wl_sorted[right] - x) else right

        lam = float(wl_sorted[k])
        h = float(inten_sorted[k])

        cursor_line.set_xdata([lam, lam])
        ann.xy = (lam, h)
        ann.set_text(f"{lam:.3f} nm")
        ann.set_visible(True)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)

    if show_visible_band:
        ax.legend(loc="upper right")

    fig.tight_layout()
    if save:
        fig.savefig(save)
    plt.show()

    
def _plot_image(im, title, polyline=None, save=None):
    plt.figure(figsize=(8, 5))
    plt.imshow(im, cmap="gray", aspect="auto")
    plt.xlabel("x [px]")
    plt.ylabel("y [px]")
    plt.title(title)
    if polyline is not None and len(polyline) >= 2:
        xs = [p[0] for p in polyline]
        ys = [p[1] for p in polyline]
        plt.plot(xs, ys, linewidth=2)
    plt.tight_layout()
    if save:
    	plt.savefig(save)
    plt.show()


def _plot_image_with_band(im, polyline, half_width_px, title, save=None):
    plt.figure(figsize=(8, 5))
    plt.imshow(im, cmap="gray", aspect="auto")
    plt.xlabel("x [px]")
    plt.ylabel("y [px]")
    plt.title(title)

    if polyline is None or len(polyline) < 2:
        plt.show()
        return

    xs = [p[0] for p in polyline]
    ys = [p[1] for p in polyline]
    plt.plot(xs, ys, linewidth=2)

    (x0, y0), (x1, y1) = polyline[0], polyline[1]
    dx = x1 - x0
    dy = y1 - y0
    L = float(np.hypot(dx, dy))
    if L > 0:
        nx = -dy / L
        ny = dx / L

        bw = float(half_width_px)
        xsa = [x0 + bw * nx, x1 + bw * nx]
        ysa = [y0 + bw * ny, y1 + bw * ny]
        xsb = [x0 - bw * nx, x1 - bw * nx]
        ysb = [y0 - bw * ny, y1 - bw * ny]

        plt.plot(xsa, ysa, linestyle="--", linewidth=1)
        plt.plot(xsb, ysb, linestyle="--", linewidth=1)
    plt.tight_layout()
    if save:
    	plt.savefig(save)
    plt.show()


def _plot_profile_px(spec, title, with_peaks, save=None):
    plt.figure(figsize=(8, 5))
    plt.plot(spec.X, spec.I_smooth if spec.I_smooth is not None else spec.I)
    plt.xlabel("x [px]")
    plt.ylabel("Rel. intenzita")
    plt.title(title)
    plt.grid(True)

    if with_peaks and spec.peaks is not None and len(spec.peaks) > 0:
        y = spec.I_smooth if spec.I_smooth is not None else spec.I
        p = np.asarray(spec.peaks, dtype=int)
        plt.scatter(spec.X[p], y[p])
    plt.tight_layout()
    if save:
    	plt.savefig(save)
    plt.show()



def _plot_spectrum_nm(
    spec,
    title,
    with_peaks,
    save=None,
    nist_series=None,
    show_visible_band=False,
):
    plt.figure(figsize=(8, 5))

    if show_visible_band:
        plt.axvspan(
            380, 750,
            color="violet",
            alpha=0.3,
            label="Viditelné spektrum",
        )

    plt.plot(spec.lambda_nm, spec.I_smooth)
    plt.xlabel("λ [nm]")
    plt.ylabel("Rel. intenzita")
    plt.title(title)
    plt.grid(True)

    if nist_series is not None:
        nist_wl, nist_inten = nist_series
        scaled = _scale_sticks_to_match(nist_inten, spec.I_smooth)
        plt.vlines(
            nist_wl,
            ymin=0,
            ymax=scaled,
            colors="red",
            alpha=0.8,
            linewidth=1.2,
            label="Dataset NIST",
        )

    if with_peaks and spec.peaks is not None and len(spec.peaks) > 0:
        p = np.asarray(spec.peaks, dtype=int)
        plt.scatter(spec.lambda_nm[p], spec.I_smooth[p])

        lam = spec.lambda_nm[p]
        order = np.argsort(lam)
        for j in order[:min(10, order.size)]:
            plt.annotate(
                f"{lam[j]:.1f} nm",
                (lam[j], spec.I_smooth[p][j]),
                textcoords="offset points",
                xytext=(0, 6),
                ha="center",
                fontsize=8,
            )

    if show_visible_band or nist_series is not None:
        plt.legend(loc="upper right")

    plt.tight_layout()
    if save:
        plt.savefig(save)
    plt.show()


def _print_peaks_nm(spec, top_n=30):
    p = np.asarray(spec.peaks, dtype=int)
    lam = spec.lambda_nm[p]
    inten = (spec.I_smooth if spec.I_smooth is not None else spec.I)[p]

    order = np.argsort(lam)  # keep order by wavelength
    order = order[:min(int(top_n), order.size)]

    print("--- Peaks ---")
    print("  #   lambda_nm     intensity")
    for k, j in enumerate(order, start=1):
        print(f"{k:3d}  {lam[j]:9.3f}  {inten[j]:12.6f}")
    print("-----------------------------------")


def main():
    cfg = SpectroConfig()
    # cfg.step_px = 1
    cfg.half_width_px = 20
    cfg.width_samples = 14
    # cfg.smooth_win = 11
    # cfg.min_prom = 0.03
    # cfg.min_dist = 10

    cal_path = "../data/zn.tiff"
    polyline = [(12, 560), (1932, 560)]

    # ---------------------------
    # Calibration
    # ---------------------------
    calib_spec = VisualSpectrum(cfg)
    calib_spec.load_image(cal_path)
    calib_spec.set_polyline(polyline)
    calib_spec.build()
    calib_spec.detect_peaks()

    #_plot_image(calib_spec.image, "Original image", polyline=None)
    #_plot_image(calib_spec.image, "Original image with selected line", polyline=polyline)
    #_plot_image_with_band(
    #    calib_spec.image, polyline, cfg.half_width_px,
    #    "Original image with line + gap"
    #)
    #_plot_profile_px(calib_spec, "Profile I(x) before calibration", with_peaks=True)

    x_refs = [
        float(calib_spec.X[calib_spec.peaks[0]]),
        float(calib_spec.X[calib_spec.peaks[1]]),
        float(calib_spec.X[calib_spec.peaks[2]]),
        float(calib_spec.X[calib_spec.peaks[3]]),
    ]
    lambda_refs = [637.0, 481.5, 472.0, 468.0]

    calib_spec.calibrate(x_refs, lambda_refs, deg=1)
    print("Calibration")
    print(f"  deg={calib_spec.calib.deg}")
    print(f"  coeff={calib_spec.calib.coeff}")

    calib_spec.apply_calibration(calib_spec.calib)
    #_plot_spectrum_nm(calib_spec, "Calibration spectrum", with_peaks=True)
    #_print_peaks_nm(calib_spec, top_n=30)

    # ---------------------------
    # Apply to measurement
    # ---------------------------
	
	# Measured image details
    image_path = "../data/mobil.tiff"
    fullname = "Bílá LED"
    nist_element = None #"Zn I"
    polyline = [(12, 490), (1932, 490)]
    
    meas_spec = Spectrum(cfg)
    meas_spec.load_image(image_path)
    meas_spec.set_polyline(polyline)
    meas_spec.build()
    meas_spec.detect_peaks()
    meas_spec.apply_calibration(calib_spec.calib)
    
    name = os.path.splitext(os.path.basename(image_path))[0]
    lam_min = float(np.min(meas_spec.lambda_nm))
    lam_max = float(np.max(meas_spec.lambda_nm))
    nist_series = retrieve_nist_lines(nist_element, lam_min, lam_max)
    series = None
    if nist_element:
    	series = nist_series

    _plot_image(meas_spec.image, f"Černobílý snímek ({fullname})", polyline=None, save=f"../tex/img/charts/{name}_orig.pdf")
    _plot_image_with_band(
        meas_spec.image, polyline, cfg.half_width_px,
        f"Černobílý snímek s linií ({fullname})",
        save=f"../tex/img/charts/{name}_line.pdf"
    )
    _plot_profile_px(meas_spec, f"Profil podél linie ({fullname})", with_peaks=True, save=f"../tex/img/charts/{name}_profile.pdf")
    _plot_spectrum_nm(meas_spec, f"Spektrum I(λ) ({fullname})", with_peaks=True, save=f"../tex/img/charts/{name}_spectrum.pdf", nist_series=series, show_visible_band=True)
    _print_peaks_nm(meas_spec, top_n=30)
    #plot_nist_only(nist_element, lam_min, lam_max, save=f"../tex/img/charts/{name}_nist.pdf")


if __name__ == "__main__":
    main()

