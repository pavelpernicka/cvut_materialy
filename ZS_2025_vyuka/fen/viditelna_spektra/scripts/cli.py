#!/usr/bin/env python3
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt

from img2spectrum import VisualSpectrum, Calibration, PickMode, SpectroConfig


def _parse_polyline(vals):
    if vals is None:
        return None
    if len(vals) < 4 or len(vals) % 2 != 0:
        raise SystemExit("--line expects: x1 y1 x2 y2 [x3 y3 ...]")
    return [(float(vals[i]), float(vals[i + 1])) for i in range(0, len(vals), 2)]


def _print_peaks_nm(spec: VisualSpectrum, top_n: int = 30):
    if spec.peaks is None or len(spec.peaks) == 0:
        print("No peaks detected.")
        return
    if spec.lambda_nm is None or spec.I_smooth is None:
        print("Cannot print peaks in nm: missing calibration or smoothed profile")
        return

    peak_idx = np.asarray(spec.peaks, dtype=int)

    lam = spec.lambda_nm[peak_idx]
    inten = spec.I_smooth[peak_idx]

    order = np.argsort(lam)
    order = order[: min(int(top_n), order.size)]

    print(f"Peaks:")
    print("  #   lambda_nm     intensity")
    for k, j in enumerate(order, start=1):
        print(f"{k:3d}  {lam[j]:9.3f}  {inten[j]:12.6f}")


def _plot_profile_nm_with_peaks(spec: VisualSpectrum):
    if spec.lambda_nm is None or spec.I_smooth is None:
        raise SystemExit("Cannot plot peak chart: missing calibration or smoothed profile.")
    if spec.peaks is None or len(spec.peaks) == 0:
        raise SystemExit("Cannot plot peak chart: no peaks detected.")

    peak_idx = np.asarray(spec.peaks, dtype=int)

    plt.figure()
    plt.plot(spec.lambda_nm, spec.I_smooth)
    plt.scatter(spec.lambda_nm[peak_idx], spec.I_smooth[peak_idx])
    plt.xlabel("wavelength [nm]")
    plt.ylabel("Intensity (smoothed) [a.u.]")
    plt.title("Peaks on calibrated spectrum")
    plt.grid(True)
    plt.show()


def main():
    ap = argparse.ArgumentParser(description="Image to spectrochart tool.")
    ap.add_argument("image", help="Input image")

    # (Poly)line selection
    ap.add_argument("--click-line", action="store_true", help="Pick polyline from image")
    ap.add_argument("--line", nargs="+", type=float, default=None, help="Polyline points: x1 y1 x2 y2 [x3 y3 ...]")

    # Peak detection
    ap.add_argument("--no-peaks", action="store_true", help="Skip peak detection")

    # Calibration json
    ap.add_argument("--load-calib", default=None, help="Load calibration JSON")
    ap.add_argument("--save-calib", default=None, help="Save calibration JSON")

    # Calibration modes
    ap.add_argument("--calib-click", type=int, default=None, help="Click on peaks and enter their lambda")
    ap.add_argument("--calib-deg", type=int, default=1, help="Polynomial degree to fit (defaultly linear)")
    ap.add_argument(
        "--calib-mode",
        choices=["snap", "absolute"],
        default="snap",
        help="snap: enter lambda for closest detected peak, absolute: use clicked x directly",
    )

    # Peaks
    ap.add_argument("--show-peaks", action="store_true", help="After calibration: show peak chart in wavelength domain")
    ap.add_argument("--print-peaks", action="store_true", help="After calibration: print peak values in nm")
    ap.add_argument("--top-peaks", type=int, default=30, help="How many peaks to print (default 30)")

    # Export
    ap.add_argument("--export", default="out.csv", help="Output CSV (lambda,intensity)")
    ap.add_argument("--export-calib-only", action="store_true", help="Only export calibration and exit")

    # Other config
    ap.add_argument("--step", type=float, default=None, help="Sampling step in px")
    ap.add_argument("--half-width", type=float, default=None, help="Half width of averaging strip in px")
    ap.add_argument("--width-samples", type=int, default=None, help="Samples across strip width")
    ap.add_argument("--smooth-win", type=int, default=None, help="Smoothing window of moving average")
    ap.add_argument("--min-prom", type=float, default=None, help="Min prominence for peak detection")
    ap.add_argument("--min-dist", type=int, default=None, help="Min distance between peaks")

    ap.add_argument("--no-show", action="store_true", help="Disable showing plots")
    args = ap.parse_args()

    cfg = SpectroConfig()
    if args.step is not None:
        cfg.step_px = float(args.step)
    if args.half_width is not None:
        cfg.half_width_px = float(args.half_width)
    if args.width_samples is not None:
        cfg.width_samples = int(args.width_samples)
    if args.smooth_win is not None:
        cfg.smooth_win = int(args.smooth_win)
    if args.min_prom is not None:
        cfg.min_prom = float(args.min_prom)
    if args.min_dist is not None:
        cfg.min_dist = int(args.min_dist)

    spec = VisualSpectrum(cfg)
    spec.load_image(args.image)

    # Line selection
    if args.click_line:
        spec.pick_polyline_interactive()
        line_args = " ".join(f"{x} {y}" for x, y in spec.polyline)
        print(f"Polyline args: --line {line_args}")
    else:
        pts = _parse_polyline(args.line)
        if pts is None:
            raise SystemExit("You must set --click-line or --line")
        spec.set_polyline(pts)

    # Build profile
    spec.build()

    # Detect peaks (needed for snap + peak chart/printing)
    if not args.no_peaks:
        spec.detect_peaks()

    # --- Calibration ---
    if args.load_calib:
        with open(args.load_calib, "r", encoding="utf-8") as f:
            calib = Calibration.from_json(json.load(f))
        spec.apply_calibration(calib)
        print(f"Loaded calibration from: {args.load_calib}")
        if spec.calib is not None:
            print(f"Calibration: deg={spec.calib.deg}, coeff={spec.calib.coeff}")

    elif args.calib_click is not None:
        n = int(args.calib_click)
        deg = int(args.calib_deg)
        mode = PickMode.SNAP if args.calib_mode == "snap" else PickMode.ABSOLUTE

        if mode == PickMode.SNAP:
            if args.no_peaks:
                raise SystemExit("Snap calibration requires peaks, but disabled by --no-peaks")
            if spec.peaks is None or len(spec.peaks) == 0:
                raise SystemExit("No peaks detected, try adjusting detection config (--min-prom/--min-dist/--smooth-win)")

        spec.calibrate_click_interactive(n=n, deg=deg, mode=mode)
        print("Fit:")
        print(f"  deg={spec.calib.deg}")
        print(f"  coeff={spec.calib.coeff}")
        coeff_str = " ".join(f"{c:.12g}" for c in spec.calib.coeff)
        print(f"--calib-poly {spec.calib.deg} {coeff_str}")

    else:
        raise SystemExit("No calibration! Use --load-calib or --calib-click.")

    # Save calibration
    if args.save_calib:
        if spec.calib is None:
            raise SystemExit("Cannot save calibration: nothing fitted/loaded.")
        with open(args.save_calib, "w", encoding="utf-8") as f:
            json.dump(spec.calib.to_json(), f, indent=2)
        print(f"Saved calibration: {args.save_calib}")

    if args.export_calib_only:
        return

    if not args.no_peaks:
        if args.print_peaks:
            _print_peaks_nm(spec, top_n=args.top_peaks)
        if args.show_peaks and not args.no_show:
            _plot_profile_nm_with_peaks(spec)

    if not args.no_show:
        if spec.lambda_nm is None or spec.I is None:
            raise SystemExit("Cannot plot: no lambda_nm or intensities.")
        plt.figure()
        plt.plot(spec.lambda_nm, spec.I)
        plt.xlabel("wavelength [nm]")
        plt.ylabel("Intensity [a.u.]")
        plt.title("Spectrum I(λ)")
        plt.grid(True)
        plt.show()

    # Export spectrum
    if spec.lambda_nm is None or spec.I is None:
        raise SystemExit("Spectrum not calibrated correctly")

    out = np.column_stack([spec.lambda_nm, spec.I])
    np.savetxt(args.export, out, delimiter=",", header="lambda_nm,intensity", comments="")
    print(f"Exported spectrum: {args.export}")


if __name__ == "__main__":
    main()

