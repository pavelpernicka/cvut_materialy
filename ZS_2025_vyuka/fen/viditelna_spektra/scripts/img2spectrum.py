#!/usr/bin/env python3
import math
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Sequence, Optional

import numpy as np
from PIL import Image

Point = Tuple[float, float]

@dataclass
class SpectroConfig:
    step_px: float = 1.0
    half_width_px: float = 2.0
    width_samples: int = 7

    smooth_win: int = 9
    min_prom: float = 0.03
    min_dist: int = 12

    enforce_x_increasing: bool = True
    
@dataclass
class PickMode(str, Enum):
    ABSOLUTE = "absolute"
    SNAP = "snap"


@dataclass
class Calibration:
    deg: int
    coeff: List[float]

    def __call__(self, x: np.ndarray) -> np.ndarray:
        return np.polyval(self.coeff, x).astype(np.float32)

    @staticmethod
    def fit(x: Sequence[float], lam: Sequence[float], deg: int = 1) -> "Calibration":
        coeff = np.polyfit(x, lam, deg=int(deg)).tolist()
        return Calibration(deg=deg, coeff=[float(c) for c in coeff])

    def to_json(self) -> dict:
        return {"deg": self.deg, "coeff": self.coeff}

    @staticmethod
    def from_json(obj: dict) -> "Calibration":
        return Calibration(deg=int(obj["deg"]), coeff=list(obj["coeff"]))


def load_tiff_grayscale(path: str) -> np.ndarray:
    arr = np.asarray(Image.open(path))

    if arr.ndim == 2:
        g = arr.astype(np.float32)
    else:
        rgb = arr[..., :3].astype(np.float32)
        g = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]

    g -= g.min()
    if g.max() > 0:
        g /= g.max()
    return g.astype(np.float32)


def bilinear(im: np.ndarray, x: float, y: float) -> float:
    h, w = im.shape
    if x < 0 or y < 0 or x >= w - 1 or y >= h - 1:
        return float("nan")

    x0, y0 = int(x), int(y)
    dx, dy = x - x0, y - y0

    return (
        im[y0, x0] * (1 - dx) * (1 - dy)
        + im[y0, x0 + 1] * dx * (1 - dy)
        + im[y0 + 1, x0] * (1 - dx) * dy
        + im[y0 + 1, x0 + 1] * dx * dy
    )


def sample_polyline(
    im: np.ndarray,
    points: Sequence[Point],
    cfg: SpectroConfig,
) -> Tuple[np.ndarray, np.ndarray]:

    X, I = [], []

    for p0, p1 in zip(points[:-1], points[1:]):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy)
        n = max(2, int(L / cfg.step_px))

        nx, ny = -dy / L, dx / L

        for t in np.linspace(0, 1, n):
            x = p0[0] + dx * t
            y = p0[1] + dy * t

            samples = []
            for o in np.linspace(-cfg.half_width_px, cfg.half_width_px, cfg.width_samples):
                samples.append(bilinear(im, x + o * nx, y + o * ny))

            X.append(x)
            I.append(np.nanmean(samples))

    X = np.asarray(X, dtype=np.float32)
    I = np.asarray(I, dtype=np.float32)

    if cfg.enforce_x_increasing and X[0] > X[-1]:
        X, I = X[::-1], I[::-1]

    return X, I

def smooth(y: np.ndarray, win: int) -> np.ndarray:
    if win < 3:
        return y
    win |= 1
    k = np.ones(win) / win
    return np.convolve(np.pad(y, win // 2, mode="edge"), k, mode="valid")


def find_peaks(y: np.ndarray, min_prom: float, min_dist: int) -> np.ndarray:
    m = (y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:])
    idx = np.where(m)[0] + 1

    good = []
    for i in idx:
        if y[i] - min(y[max(0, i - min_dist)], y[min(len(y) - 1, i + min_dist)]) >= min_prom:
            good.append(i)
    return np.array(good, dtype=int)


class Spectrum:
    def __init__(self, cfg: SpectroConfig = SpectroConfig()):
        self.cfg = cfg
        self.image: Optional[np.ndarray] = None
        self.polyline: Optional[List[Point]] = None

        self.X = None
        self.I = None
        self.I_smooth = None
        self.peaks = None

        self.calib: Optional[Calibration] = None
        self.lambda_nm = None

    def load_image(self, path: str):
        self.image = load_tiff_grayscale(path)

    def set_polyline(self, pts: Sequence[Point]):
        self.polyline = list(pts)

    def build(self):
        self.X, self.I = sample_polyline(self.image, self.polyline, self.cfg)
        self.I_smooth = smooth(self.I, self.cfg.smooth_win)

    def detect_peaks(self):
        self.peaks = find_peaks(self.I_smooth, self.cfg.min_prom, self.cfg.min_dist)

    def calibrate(self, x: Sequence[float], lam: Sequence[float], deg: int = 1):
        self.calib = Calibration.fit(x, lam, deg)
        self.lambda_nm = self.calib(self.X)

    def apply_calibration(self, calib: Calibration):
        self.calib = calib
        self.lambda_nm = calib(self.X)

class VisualSpectrum(Spectrum):
    """
    Interactive tools - (poly)line picking and calibration points picking
    """

    def pick_polyline_interactive(self, title: str = "Choose (poly)line points, ENTER to continue") -> List[Point]:
        if self.image is None:
            raise RuntimeError("Image not loaded")

        import matplotlib.pyplot as plt # must load here, not glabally for whole lib

        fig, ax = plt.subplots()
        ax.imshow(self.image, cmap="gray")
        ax.set_title(title)
        pts = plt.ginput(n=-1, timeout=0)
        plt.close(fig)

        pts2 = [(float(x), float(y)) for (x, y) in pts]
        self.set_polyline(pts2)
        return pts2

    def _ensure_profile_ready(self) -> None:
        if self.X is None or self.I_smooth is None:
            raise RuntimeError("Profile is not ready")

    def _ensure_peaks_ready(self) -> None:
        if self.peaks is None:
            raise RuntimeError("Peaks not computed")
        if len(self.peaks) == 0:
            raise RuntimeError("No peaks detected")

    def plot_profile_px(self, with_peaks: bool = True, title: str = "I(x) profile") -> None:
        self._ensure_profile_ready()
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot(self.X, self.I_smooth)
        if with_peaks and self.peaks is not None and len(self.peaks) > 0:
            ax.scatter(self.X[self.peaks], self.I_smooth[self.peaks])
        ax.set_xlabel("x [px]")
        ax.set_ylabel("intensity")
        ax.set_title(title)
        ax.grid(True)
        plt.show()

    def pick_x_points_on_profile(
        self,
        n: int,
        title: str = "Select peaks from profile, ENTER to continue",
    ) -> List[float]:
        self._ensure_profile_ready()
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot(self.X, self.I_smooth)
        ax.set_title(title)
        ax.set_xlabel("x [px]")
        ax.set_ylabel("intensity")
        ax.grid(True)

        pts = plt.ginput(n=n, timeout=0)
        plt.close(fig)

        if len(pts) != n:
            raise ValueError(f"Expected {n} points, got {len(pts)} instead")

        return [float(x) for (x, _y) in pts]

    def _snap_x_to_nearest_peak(self, x: float) -> float:
        self._ensure_peaks_ready()
        peak_x = self.X[self.peaks]
        j = int(np.argmin(np.abs(peak_x - float(x))))
        return float(peak_x[j])

    def pick_calibration_points_interactive(
        self,
        n: int,
        mode: PickMode = PickMode.ABSOLUTE,
        snap_show: bool = True,
    ) -> Tuple[List[float], List[float]]:
        """
        Interactive calibration picker modes:
            ABSOLUTE: x = clicked x
            SNAP:     x = nearest detected peak x
        """
        self._ensure_profile_ready()

        if mode == PickMode.SNAP:
            self._ensure_peaks_ready()

        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot(self.X, self.I_smooth)
        if self.peaks is not None and len(self.peaks) > 0:
            ax.scatter(self.X[self.peaks], self.I_smooth[self.peaks])
        ax.set_xlabel("x [px]")
        ax.set_ylabel("intensity")
        ax.set_title(
            "Click calibration peaks "
            + ("SNAP mode" if mode == PickMode.SNAP else "ABSOLUTE mode")
        )
        ax.grid(True)

        pts = plt.ginput(n=n, timeout=0)
        plt.close(fig)

        if len(pts) != n:
            raise ValueError(f"Expected {n} selected peaks, got {len(pts)}.")

        xs: List[float] = []
        ls: List[float] = []

        for i, (x_click, _y_click) in enumerate(pts, start=1):
            x_click = float(x_click)

            if mode == PickMode.SNAP:
                x_used = self._snap_x_to_nearest_peak(x_click)
                if snap_show:
                    print(f"[{i}/{n}]: x={x_click:.2f} snapped to x={x_used:.2f}")
            else:
                x_used = x_click
                print(f"[{i}/{n}]: absolute x={x_used:.2f}")

            while True:
                s = input(f"Enter wavelength for x={x_used:.2f}: ").strip()
                try:
                    lam_nm = float(s.replace(",", "."))
                except ValueError:
                    print("Invalid value!")
                    continue
                xs.append(x_used)
                ls.append(lam_nm)
                break

        return xs, ls

    def calibrate_click_interactive(
        self,
        n: int,
        deg: int = 1,
        mode: PickMode = PickMode.SNAP,
    ) -> Calibration:
        xs, ls = self.pick_calibration_points_interactive(n=n, mode=mode)
        self.calibrate(xs, ls, deg=deg)
        return self.calib
