"""glyph_descriptor — a fixed-dim, order-invariant SHAPE descriptor for a written character.

The point-set / part recognisers are non-parametric (variable-size). To LEARN a writer-invariant
metric from the Omniglot background (the WCCN / within-class whitening the agent built for speakers,
transferred to writers) we need a FIXED-dimension feature per character so a covariance can be
estimated. This descriptor is a small occupancy + tangent-orientation histogram over the normalised
pen points — order- and segmentation-invariant (it pools points), so it pairs with the holistic
match. Mechanical perception; no decision.
"""
from __future__ import annotations

import numpy as np


def char_descriptor(strokes, grid: int = 8, r: float = 2.4) -> np.ndarray:
    """Pen strokes (list of (k,2) point arrays, already jointly normalised) -> a fixed-dim vector:
    a grid x grid OCCUPANCY map + a grid x grid mean TANGENT-ORIENTATION map (undirected, via 2*theta).
    Order/segmentation-invariant (pools all points). L2-normalised. dim = 3 * grid^2."""
    occ = np.zeros((grid, grid))
    ori = np.zeros((grid, grid, 2))
    for s in strokes:
        s = np.asarray(s, dtype=float)
        if s.shape[0] < 1:
            continue
        if s.shape[0] >= 2:
            d = np.diff(s, axis=0)
            d = np.vstack([d, d[-1:]])               # tangent per point (forward diff)
        else:
            d = np.zeros((1, 2))
        for p, tp in zip(s, d):
            gx = (p[0] + r) / (2 * r) * grid - 0.5
            gy = (p[1] + r) / (2 * r) * grid - 0.5
            x0, y0 = int(np.floor(gx)), int(np.floor(gy))
            fx, fy = gx - x0, gy - y0
            nt = float(np.hypot(tp[0], tp[1]))
            ca = sa = 0.0
            if nt > 1e-9:
                ang = 2.0 * np.arctan2(tp[1], tp[0])
                ca, sa = np.cos(ang), np.sin(ang)
            for dx, wx in ((0, 1 - fx), (1, fx)):       # bilinear soft-binning into 4 cells
                for dy, wy in ((0, 1 - fy), (1, fy)):
                    ix, iy = x0 + dx, y0 + dy
                    if 0 <= ix < grid and 0 <= iy < grid:
                        w = wx * wy
                        occ[iy, ix] += w
                        ori[iy, ix, 0] += w * ca
                        ori[iy, ix, 1] += w * sa
    v = np.concatenate([occ.reshape(-1), ori.reshape(-1)])
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-9 else v


__all__ = ["char_descriptor"]
