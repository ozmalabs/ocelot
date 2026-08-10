#!/usr/bin/env python3
"""SUB-CELL CROSS-FRAME REGISTRATION SENSOR (block 149000-149999).

A mechanical numpy sensor — the ink twin of `motion_group_world.vector_field`.
It READS ONLY PIXEL ARRAYS (a tracked object's grey patch in two consecutive
frames) and EMITS a per-frame-pair DISPLACEMENT as a FINER-UNIT INTEGER
(offset x S, for an integer scale S), i.e. a finer STEPPED rendering of the
continuous cross-frame translation. NO agent decision, NO graph state, no
`if` over graph — every order-N verdict remains the seed rule downstream.

THE FRAME/CONTINUUM INVARIANT — WHERE PRECISION IS ALLOWED TO LIVE
------------------------------------------------------------------
147000 added precision to the IN-FRAME grid, where the block aperture pays for
it. The invariant says in-frame coordinates are INTEGER (a frame's observed
lattice); non-integer / sub-cell structure is CROSS-FRAME — it lives in the MAP
`Hom(frame, frame)`, never in an object's coordinate. A per-frame displacement
(velocity) IS such a map. So sub-cell precision is admissible here and ONLY
here, and its observable is the STEPPED (finer-unit INTEGER) rendering.

Discipline enforced by construction:
  * The object's grid location (the carve centroid) enters only through
    `round(...)` — the coarse INTEGER anchor that CENTERS the residual search.
    Its sub-cell (float) part is NEVER read (that would be the forbidden
    "sub-pixel float centroid").
  * The bilinear upsample interpolates grey VALUES on a finer grid — a rendering
    inside the cross-frame comparator. Grey values are not coordinates.
  * The search is over INTEGER fine-grid offsets `sy, sx in [-R, R]`. The argmin
    is an INTEGER. The emitted offset is that integer (finer units of 1/S cell).
  * NO float is ever returned as, or written into, an in-frame coordinate slot.

`S` is a DECLARED resolution residual (like `block` / `k`, §13): the finer unit.
It is the registration's sub-cell step (1/S cell); it is NOT a tuned witness
tolerance (the witness's tolerance falls out of integer bit-costs unchanged).
"""
from __future__ import annotations

import numpy as np


def bilinear_upsample(p: np.ndarray, S: int) -> np.ndarray:
    """Render `p` on an S-times-finer grid by bilinear interpolation of grey
    VALUES (a cross-frame rendering — not a coordinate). Pixel-centre aligned."""
    p = np.asarray(p, dtype=np.float64)

    def interp_axis(arr, S, axis):
        n = arr.shape[axis]
        coords = (np.arange(n * S) + 0.5) / S - 0.5
        coords = np.clip(coords, 0.0, n - 1.0)
        i0 = np.floor(coords).astype(np.int64)
        i1 = np.minimum(i0 + 1, n - 1)
        w = (coords - i0)
        a0 = np.take(arr, i0, axis=axis)
        a1 = np.take(arr, i1, axis=axis)
        shape = [1] * arr.ndim
        shape[axis] = len(coords)
        w = w.reshape(shape)
        return a0 * (1.0 - w) + a1 * w

    p = interp_axis(p, S, 0)
    p = interp_axis(p, S, 1)
    return p


def _window(frame: np.ndarray, r0: int, c0: int, half: int) -> np.ndarray:
    """Extract a (2*half+1) square window centred at integer (r0, c0), edge-clamped."""
    H, W = frame.shape
    rs = np.clip(np.arange(r0 - half, r0 + half + 1), 0, H - 1)
    cs = np.clip(np.arange(c0 - half, c0 + half + 1), 0, W - 1)
    return frame[np.ix_(rs, cs)]


def register_residual_offset(prev, cur, *, anchor_prev, coarse, count,
                             S, search_cells, half=None):
    """Measure the object's TRUE prev->cur displacement as a finer-unit integer.

    `anchor_prev`  : integer (row, col) locating the object in `prev` (from
                     `round(carve centroid)` — the COARSE INTEGER anchor only).
    `coarse`       : integer (drow, dcol) coarse predicted displacement
                     (`round(cy[t+1]) - round(cy[t])`, integer cells). It only
                     CENTRES the residual search; the returned total is
                     independent of its noise as long as the true residual is
                     within +/- `search_cells` (the residual absorbs anchor noise).
    `count`        : the carve's object pixel count -> the ball TEMPLATE is the
                     `count` brightest pixels of the prev window (falls out of the
                     carve, no tuned threshold). SAD is computed over this mask
                     only -> static background (the ruler) is immune by construction.
    `S`            : the finer unit (1/S cell) — declared resolution residual.
    `search_cells` : residual half-window in cells (+/-), searched at 1/S steps.

    Returns (dy_fine, dx_fine): the total displacement as FINER-UNIT INTEGERS,
        dy_fine = coarse_row * S + residual_row_fine (both integers), and a
        diagnostics dict. Purely a pixel read; no float coordinate is produced.
    """
    prev = np.asarray(prev, dtype=np.float64)
    cur = np.asarray(cur, dtype=np.float64)
    ar, ac = int(anchor_prev[0]), int(anchor_prev[1])
    cdr, cdc = int(coarse[0]), int(coarse[1])
    if half is None:
        # window half-extent falls out of the carve's own object size (count),
        # padded so the whole object + a small rim is captured. Not tuned.
        half = int(np.ceil(np.sqrt(max(count, 1.0)))) + 2

    # prev template window at the object; cur window at anchor+coarse (ball ~centred).
    pw = _window(prev, ar, ac, half)
    cw = _window(cur, ar + cdr, ac + cdc, half + search_cells)

    # TEMPLATE MASK: the `count` brightest prev-window pixels = the ball. SAD is
    # restricted to this mask, so the static background never enters the match.
    k = int(min(max(count, 1), pw.size))
    thresh = np.partition(pw.ravel(), pw.size - k)[pw.size - k]
    mask = (pw >= thresh)

    pwU = bilinear_upsample(pw, S)
    cwU = bilinear_upsample(cw, S)
    maskU = np.repeat(np.repeat(mask, S, 0), S, 1)          # nearest — mask is binary
    mr, mc = np.nonzero(maskU)                               # fine mask coords
    denom = float(mr.size)
    if denom <= 0:
        return cdr * S, cdc * S, {"denom": 0.0}
    tmpl = pwU[mr, mc]                                       # ball template values

    R = search_cells * S
    # candidate fine residual offsets, ascending magnitude (Occam tie-break: the
    # smallest residual wins an exact tie — minimal correction to the coarse move).
    offs = [(sy, sx) for sy in range(-R, R + 1) for sx in range(-R, R + 1)]
    offs.sort(key=lambda o: (o[0] * o[0] + o[1] * o[1], o[0], o[1]))

    best = np.inf
    bsy = bsx = 0
    sad0 = None
    for sy, sx in offs:
        # align cur under prev: prev pixel p matches cur at p + (coarse+residual);
        # cwU is offset by (R+sy, R+sx) relative to the coarse-centred window, so
        # gather cur at the (shifted) template coords only — background never enters.
        vals = cwU[mr + R + sy, mc + R + sx]
        sad = float(np.abs(tmpl - vals).sum())
        if sy == 0 and sx == 0:
            sad0 = sad
        if sad < best:
            best = sad
            bsy, bsx = sy, sx

    # sharpness: how much the best beats the coarse-centre (residual 0,0) SAD —
    # a pure diagnostic (registration confidence), not fed to any decision.
    diag = {"denom": denom, "best_sad": best / denom,
            "centre_sad": (sad0 / denom) if sad0 is not None else None,
            "resid_fine": [bsy, bsx], "half": half}
    return cdr * S + bsy, cdc * S + bsx, diag
