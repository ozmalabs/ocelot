"""fuzzy_smooth — OWNED multi-scale Gaussian smoothing for the sense-hats' compare.

The insight (Axiom 0): the compare has been a RIGID rule (exact match over the
feature grid) when "rules are more like guidelines" — it should be FUZZY. A rigid
metric counts every high-frequency detail; but at low resolution that detail is
ALIASING (toy hat) and across the synthetic-vs-real boundary it is the DOMAIN GAP
(audio hat). Both are the SAME nuisance: high-frequency structure the compare
should IGNORE. Smoothing the feature grid before the residual removes both.

This is OWNED DSP — a separable Gaussian blur over the 2D feature grid (no net, no
fit, no learned filter). It lives in the HATS' encode/synth/compare; the CortexLoop
is untouched. MULTI-SCALE: smooth at a small coarse-to-fine set of scales and
concatenate (a pyramid), so the residual sees the shape at several blur levels at
once. The scale is SWEPT because over-smoothing erases the signal too.

NB: over-smoothing is a real failure mode — at a large enough sigma every grid
becomes a featureless blob and the residual goes to zero everywhere. The sweep
finds the scale that removes the grain WITHOUT erasing the word/shape.
"""
from __future__ import annotations

from typing import List, Sequence

import numpy as np


def _gaussian_kernel1d(sigma: float, radius: int = None) -> np.ndarray:
    """A normalised 1-D Gaussian kernel (owned: just exp(-x^2/2sigma^2))."""
    if sigma <= 0:
        return np.array([1.0])
    if radius is None:
        radius = max(1, int(round(3.0 * sigma)))
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    k = np.exp(-(x * x) / (2.0 * sigma * sigma))
    k /= k.sum()
    return k


def _conv1d_reflect(a: np.ndarray, k: np.ndarray, axis: int) -> np.ndarray:
    """Separable 1-D convolution along `axis` with reflect padding (edge-safe).
    Owned numpy — no scipy/cv2 dependency in the metric path."""
    if k.size == 1:
        return a
    r = (k.size - 1) // 2
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, r)
    ap = np.pad(a, pad, mode="reflect")
    out = np.zeros_like(a)
    for i in range(k.size):
        sl = [slice(None)] * a.ndim
        sl[axis] = slice(i, i + a.shape[axis])
        out += k[i] * ap[tuple(sl)]
    return out


def blur2d(grid: np.ndarray, sigma: float) -> np.ndarray:
    """Separable 2-D Gaussian blur of a (H, W) grid at scale `sigma`. sigma<=0 ->
    identity (the un-smoothed / rigid compare)."""
    if sigma <= 0:
        return grid
    k = _gaussian_kernel1d(sigma)
    g = _conv1d_reflect(grid, k, axis=0)
    g = _conv1d_reflect(g, k, axis=1)
    return g


def multiscale_grid(grid: np.ndarray, scales: Sequence[float],
                    l2norm: bool = True) -> np.ndarray:
    """Smooth `grid` (H x W) at each sigma in `scales` and STACK the flattened,
    per-scale-normalised results into one feature vector (a blur pyramid). With a
    single scale [s] this is just blur-then-flatten; with several scales the residual
    sees the shape at coarse AND fine blur at once. scales == [0] -> the un-smoothed
    grid (the rigid baseline). Per-scale L2 so no single scale dominates the metric."""
    pieces: List[np.ndarray] = []
    for s in scales:
        g = blur2d(grid, float(s)).reshape(-1)
        if l2norm:
            nrm = float(np.linalg.norm(g))
            g = g / nrm if nrm > 1e-9 else g
        pieces.append(g)
    return np.concatenate(pieces) if pieces else grid.reshape(-1)


def smooth_traj(traj: np.ndarray, sigma_t: float, sigma_f: float) -> np.ndarray:
    """Blur a (frames x bands) cochleagram/trajectory over BOTH time and frequency
    (separable Gaussian). The audio analogue of blur2d: time-axis blur tolerates
    rate/alignment jitter, freq-axis blur tolerates the synthetic-vs-real spectral
    grain (the domain gap). sigma==0 on an axis -> no blur on that axis."""
    g = traj
    if sigma_t > 0:
        g = _conv1d_reflect(g, _gaussian_kernel1d(sigma_t), axis=0)
    if sigma_f > 0:
        g = _conv1d_reflect(g, _gaussian_kernel1d(sigma_f), axis=1)
    return g
