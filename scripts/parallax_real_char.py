"""parallax_real_char — REAL-PHOTOMETRY twin of parallax_char (rung 124000).

THE ONE VARIABLE THIS RUNG CHANGES: the SOURCE of the pixels. Everything else
— the depth/shift geometry, the band layout, the block, the ground-truth field,
the byte-identical-static-frame control, the efference-copy subtraction, the
common-fate grouping, the knee discriminator — is REPRODUCED EXACTLY from the
parallax rung (116000). Only `a` (and the frames rolled from it) come from a
REAL BSDS300 crop instead of a synthetic Fourier texture.

WHY A WINDOWED CROP, NOT A TOROIDAL ROLL (the honest analog):
The synthetic texture wraps EXACTLY (built in the Fourier domain), so
`np.roll(a, s)` is a rigid translation with NO border fabrication — b[:,x] =
a[:,x-s]. A real photo does NOT wrap; rolling it toroidally would inject a
FALSE wrap-seam discontinuity that is NOT "real photometry" — it is a NEW
confound absent from the synthetic construction. The faithful real analog
reproduces b[:,x] = a[:,x-s] EXACTLY, without wrap, by taking the pixels from a
SOURCE crop wider than the grid: with off0 = max(shifts),

    a[:,x]              = src[:, x + off0]
    b_depth[:,x in i]   = src[:, x + off0 - s_i]   (== a[:, x - s_i], real pixels)
    b_flat[:,x]         = src[:, x + off0 - s_ref]  (== a[:, x - s_ref])

Every displaced pixel is a REAL neighbour in the scene (genuine parallax reveals
adjacent texture), never a fabricated edge, never a wrap. The static frame `a`
is byte-identical between DEPTH and FLAT (one crop). Ground truth, owner, edges,
delta_ref are IDENTICAL to the synthetic construction by geometry — so the ONLY
new variable is photometry. This is the exact analog: an exact toroidal roll
maps to an exact windowed slide; the difference is Fourier vs BSDS pixels.

THE EXPECTED ANTAGONIST (the sensor's real-texture error, rung 94000): the SAD
sensor is fine until a block carries less than one 8-bit quantisation step of
structure (mean block std < 0.4), then confabulates (silent miss 0.0003 ->
0.0641; confidently wrong 0.0166 -> 0.0544); and it silent-misses 50-75% of the
time on a straight edge (aperture problem). Real BSDS crops have low-contrast
regions (sky, walls) and long edges that clean Fourier texture does not. So we
MEASURE where the carve degrades and tie it to the block-std cliff.
"""
from __future__ import annotations
import os
import numpy as np
from PIL import Image

# Reuse the parallax rung's carve machinery UNCHANGED — this is the whole point.
from parallax_char import (make_scene, group_common_fate, field_discontinuity,
                           size_dist, SQRT5)
from domains.motion_group_world import vector_field

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_BSDS = os.path.join(_ROOT, "data", "vision_curriculum", "BSDS300", "images", "train")


def bsds_paths():
    if not os.path.isdir(_BSDS):
        raise RuntimeError(f"BSDS300 absent at {_BSDS} — symlink data/ (PROTOCOL §10.2).")
    ps = sorted(os.path.join(_BSDS, f) for f in os.listdir(_BSDS) if f.endswith(".jpg"))
    if not ps:
        raise RuntimeError(f"BSDS300 EMPTY at {_BSDS}.")
    return ps


def _load_gray(path):
    """A BSDS photograph as an 8-bit grayscale float64 array (the sensor's real
    input domain — luminance is structure; memory: luminance carries the eye's
    navigation, colour is a separate sparse sign)."""
    return np.asarray(Image.open(path).convert("L"), np.float64)


def _band_owner(grid, block, edges, N):
    nh = grid // block
    ob = np.zeros(nh, dtype=int)
    for c in range(nh):
        lo = c * block
        for i in range(N):
            if edges[i] <= lo < edges[i + 1]:
                ob[c] = i
                break
    return ob


def _min_band_std_of_crop(g, r0, c0, grid, off0, block, N, owner_bands):
    """mean block-std of the LOWEST-contrast band of the static frame `a` for a
    candidate crop — the sensor's cliff variable (rung 94000)."""
    a = g[r0:r0 + grid, c0 + off0:c0 + off0 + grid]
    nh = grid // block
    bstd = a[:nh * block, :nh * block].reshape(nh, block, nh, block).std(axis=(1, 3))
    return float(np.nanmin([bstd[owner_bands == i].mean() if (owner_bands == i).any() else np.nan
                            for i in range(N)]))


# Cache of the flattest-band crop for every corpus image (built once per process).
_FLAT_CACHE = None


def _build_flat_cache(paths, grid, block, edges, N, off0, src_w, stride=24):
    """For every image, the crop position MINIMISING its lowest band's block-std.
    A corpus-wide scan so the low-contrast probe can reach the confab tail that a
    single random image cannot (measured: 1/200 BSDS images has a band < 0.4;
    35/200 below 1.0). Cached; deterministic; no RNG."""
    global _FLAT_CACHE
    if _FLAT_CACHE is not None:
        return _FLAT_CACHE
    ob = _band_owner(grid, block, edges, N)
    entries = []
    for idx, p in enumerate(paths):
        g = _load_gray(p); H, W = g.shape
        if H < grid or W < src_w:
            if H >= src_w and W >= grid:
                g = g.T; H, W = g.shape
            else:
                continue
        best = None
        for r0 in range(0, H - grid + 1, stride):
            for c0 in range(0, W - src_w + 1, stride):
                m = _min_band_std_of_crop(g, r0, c0, grid, off0, block, N, ob)
                if best is None or m < best[0]:
                    best = (m, r0, c0)
        entries.append((best[0], idx, best[1], best[2]))
    entries.sort(key=lambda e: e[0])       # ascending flatness
    _FLAT_CACHE = entries
    return entries


def make_real_scene(rng, shifts, block, grid, ref_idx, paths, select="random",
                    n_candidates=64):
    """The REAL-PHOTOMETRY twin of parallax_char.make_scene.

    Identical geometry (bands, shifts, block, owner, ground truth, delta_ref) as
    the synthetic construction; the pixels come from a real BSDS crop via the
    windowed slide (no wrap, no fabrication). Returns the SAME dict keys plus
    provenance (`img`, `crop`) and per-band block-std diagnostics.

    `select`: 'random' — a random crop (the NATURAL rate of degradation); or
    'lowcon' — the LOWEST-contrast crop among `n_candidates` random positions in
    the chosen image (an ADVERSARIAL probe that hunts toward the sensor's <0.4
    block-std cliff to exhibit the bound). Geometry is identical in both; only
    WHICH real pixels are cropped differs — still purely a photometry choice.
    """
    N = len(shifts)
    if ref_idx is None:
        ref_idx = N // 2
    max_shift = int(max(shifts))
    src_w = grid + max_shift
    off0 = max_shift
    edges = [round(i * grid / N) for i in range(N + 1)]

    if select == "random":
        img_idx = int(rng.integers(len(paths)))
        g = _load_gray(paths[img_idx])
        H, W = g.shape
        if H < grid or W < src_w:
            if H >= src_w and W >= grid:
                g = g.T; H, W = g.shape
            else:
                raise RuntimeError(f"BSDS image {paths[img_idx]} too small: {g.shape} < ({grid},{src_w}).")
        r0 = int(rng.integers(H - grid + 1)); c0 = int(rng.integers(W - src_w + 1))
    elif select == "lowcon":
        # Pick one of the flattest-`n_candidates` images corpus-wide (seeded), and
        # use ITS flattest-band crop — an adversarial probe into the confab tail.
        cache = _build_flat_cache(paths, grid, block, edges, N, off0, src_w)
        pool = cache[:min(n_candidates, len(cache))]
        m, img_idx, r0, c0 = pool[int(rng.integers(len(pool)))]
        g = _load_gray(paths[img_idx])
        if g.shape[0] < grid or g.shape[1] < src_w:
            g = g.T
    else:
        raise ValueError(select)
    src = g[r0:r0 + grid, c0:c0 + src_w]

    a = src[:, off0:off0 + grid].copy()

    b_depth = np.zeros_like(a)
    for i, s in enumerate(shifts):
        lo, hi = edges[i], edges[i + 1]
        b_depth[:, lo:hi] = src[:, off0 - int(s) + lo: off0 - int(s) + hi]

    s_ref = int(shifts[ref_idx])
    b_flat = src[:, off0 - s_ref: off0 - s_ref + grid].copy()

    # Ground truth / owner / mixed — IDENTICAL to the synthetic geometry.
    nh, nw = grid // block, grid // block
    t_depth = np.zeros((nh, nw, 2))
    owner = np.zeros((nh, nw), dtype=int)
    mixed = np.zeros((nh, nw), dtype=bool)
    for c in range(nw):
        lo, hi = c * block, (c + 1) * block
        owners = set()
        for x in range(lo, hi):
            for i in range(N):
                if edges[i] <= x < edges[i + 1]:
                    owners.add(i)
        if len(owners) == 1:
            i = owners.pop()
        else:
            mixed[:, c] = True
            i = min(owners)
        owner[:, c] = i
        t_depth[:, c, 1] = float(shifts[i])
    t_flat = np.zeros((nh, nw, 2))
    t_flat[..., 1] = float(s_ref)

    # Per-block std of the STATIC frame `a` (the sensor's cliff variable, rung
    # 94000: confabulation when mean block std < 0.4). Reference = frame `a`
    # because that is what the sensor matches blocks OF.
    blk = a[:nh * block, :nw * block].reshape(nh, block, nw, block)
    block_std = blk.std(axis=(1, 3))            # (nh, nw)
    band_block_std = np.array([block_std[owner == i].mean() if (owner == i).any() else np.nan
                               for i in range(N)])

    return dict(a=a, b_depth=b_depth, b_flat=b_flat, t_depth=t_depth,
                t_flat=t_flat, owner=owner, mixed=mixed,
                delta_ref=np.array([0.0, float(s_ref)]), ref_idx=ref_idx,
                edges=edges, N=N, block=block, shifts=list(shifts),
                img=os.path.basename(paths[img_idx]), crop=(r0, c0),
                block_std=block_std, band_block_std=band_block_std,
                min_band_std=float(np.nanmin(band_block_std)),
                mean_block_std=float(np.mean(block_std)))
