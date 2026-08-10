"""parallax_subpixel_char — WHAT BINDS 126000's 0.12-rad rotation bound?
(rung 127000, the frontier lever AFFINE §11 named: "SUB-PIXEL / MULTI-RESOLUTION
SENSOR to push the discretization bound".)

126000 rescued the rotation carve to ~0.12 rad via full-field efference as a
search-centre remap, and its 2x2 ablation proved affine grouping contributed 0%.
Its standing meta-lesson: WHEN A NAMED FIX DOESN'T HELP, ABLATE — the fix may be
aimed at the WRONG LAYER. This rung applies it to the THREE un-run levers 126000
named (sub-pixel/multi-res sensor; remap granularity; >=3 frames), expressing each
as an ablatable SENSOR-variant arm (measurement-harness code, exactly as 126000's
`vector_field_eff` is — NOT agent seed logic; the seeds/carve are UNTOUCHED and
the DEFAULT arm is byte-identical to 126000's full_cf).

THE GOVERNING INVARIANT (CLAUDE.md) THIS RUNG TESTS: "non-integer math is
CROSS-FRAME, never IN-frame." The observable render `b` is INTEGER by construction
(grounding is stepped); the pose->flow prediction, interpolation, and the SAD
verdict are CROSS-FRAME and may be real. A sub-pixel SENSOR (interpolating the
integer-rendered `b`, refining the SAD minimum) is the admissible "bins propose,
continuous decides" verdict; a sub-pixel RENDER is INADMISSIBLE (it would make the
observable non-stepped) and is kept only as a diagnostic to price the render step.

THE ARMS (a SENSOR selected by name; DEFAULT unchanged):
  int_int       DEFAULT = 126000 full_cf: integer pred @ block-centre, integer SAD.
  subpix_sensor REAL pred + PARABOLIC sub-pixel refine of the SAD minimum; render
                INTEGER (admissible — cross-frame verdict).       [lever a: displacement res]
  subpix_render INTEGER search, but `b` rendered by LINEAR interp (fractional
                shift). INADMISSIBLE — a DIAGNOSTIC pricing the render step.
  finer_block   block 6 (nw 24) not 8; multi-resolution finer aperture. [lever a: spatial res]
  percol_remap  efference remap at per-COLUMN granularity (warp `b` by the known
                per-column pose) then rigid block match.          [lever b: remap granularity]
  oracle        TRUE per-block-mean displacement `t` minus pred — bypasses the SAD
                block match. The credit LOCALIZER + single-frame-pair upper bound.

REUSES 126000's scene synthesis byte-for-byte (`scene`, `efference_field`,
`vector_field_eff`) and the inherited SAD sensor. NO Rust, NO new seed.
"""
from __future__ import annotations
import numpy as np

from parallax_affine_char import (scene, efference_field, vector_field_eff,
                                  block_centers, BLOCK, GRID)
from parallax_char import group_common_fate, SQRT5
from parallax_real_char import _load_gray
from parallax_motion_char import project_columns


# ---------------------------------------------------------------------------
# per-column KNOWN pose (continuous, a CROSS-FRAME map — may be real).
# ---------------------------------------------------------------------------
def efference_percol(sc):
    """Per-COLUMN predicted x-flow of the fixated plane from the KNOWN pose:
    base/Z_ref + rot*(f0+(x-cx)^2/f0). Continuous (cross-frame)."""
    grid = GRID
    base = sc["base"]; Zref = float(sc["depths"][sc["ref_idx"]]); rot = sc["rot"]
    f0 = float(grid); cx = grid / 2.0; x = np.arange(grid)
    ex = np.full(grid, base / max(Zref, 1e-3))
    if rot != 0.0:
        ex = ex + rot * (f0 + (x - cx) ** 2 / f0)
    return ex


def efference_field_block(sc, block):
    """Per-block-centre predicted x-flow at an arbitrary block size (finer_block)."""
    grid = GRID; nw = grid // block
    base = sc["base"]; Zref = float(sc["depths"][sc["ref_idx"]]); rot = sc["rot"]
    f0 = float(grid); cx = grid / 2.0
    xc = np.array([c * block + (block - 1) / 2.0 for c in range(nw)])
    ex = np.full(nw, base / max(Zref, 1e-3))
    if rot != 0.0:
        ex = ex + rot * (f0 + (xc - cx) ** 2 / f0)
    return ex


def owner_per_block(sc, block):
    """Band owner per block-column at an arbitrary block size."""
    grid = GRID; nw = grid // block; band = sc["band_of"]
    ow = np.zeros(nw, dtype=int)
    for c in range(nw):
        owners = set(int(band[x]) for x in range(c * block, (c + 1) * block))
        ow[c] = owners.pop() if len(owners) == 1 else min(owners)
    return ow


def _band_order_ok(band_resid):
    """near(idx2) > ref(idx1) > far(idx0)."""
    return bool(band_resid[2] > band_resid[1] > band_resid[0])


def _band_resid_from_R(R, owner2d, N):
    return np.array([float(R[owner2d == i][..., 1].mean()) if (owner2d == i).any()
                     else np.nan for i in range(N)])


# ---------------------------------------------------------------------------
# ARM: subpix_sensor — parabolic sub-pixel refine of the SAD minimum along dx.
# ---------------------------------------------------------------------------
def vector_field_eff_subpix(a, b, block, pred_real):
    """REAL pred centre + PARABOLIC sub-pixel interpolation of the integer SAD
    minimum along dx. Render (b) stays INTEGER — the sub-pixel is a CROSS-FRAME
    verdict (interpolating the SAD curve), invariant-respecting. Returns residual
    (pred_int + sub-pixel dx) - pred_real."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    r = int(block); H, W = a.shape; nh, nw = H // block, W // block

    def blocks(x):
        return (x[:nh * block, :nw * block]
                .reshape(nh, block, nw, block).transpose(0, 2, 1, 3))

    A = blocks(a)
    pred_i = np.round(pred_real).astype(int)
    pmax = int(np.abs(pred_i).max()); padx = r + pmax
    bp = np.pad(b, ((r, r), (padx, padx)), mode="edge")
    ndy = 2 * r + 1; ndx = 2 * r + 1
    # full SAD tensor over (dy,dx) so the argmin's dx-neighbours are available.
    sad4 = np.full((nh, nw, ndy, ndx), np.inf)
    for iy, dy in enumerate(range(-r, r + 1)):
        for ix, dx in enumerate(range(-r, r + 1)):
            sh = np.empty_like(a)
            for c in range(nw):
                adx = int(pred_i[c]) + dx; lo, hi = c * block, (c + 1) * block
                sh[:, lo:hi] = bp[r + dy:r + dy + H, padx + adx + lo: padx + adx + hi]
            sad4[:, :, iy, ix] = np.abs(A - blocks(sh)).sum(axis=(2, 3))
    vy = np.zeros((nh, nw)); rx_sub = np.zeros((nh, nw))
    for i in range(nh):
        for j in range(nw):
            flat = np.argmin(sad4[i, j])
            iy, ix = np.unravel_index(flat, (ndy, ndx))
            vy[i, j] = iy - r
            row = sad4[i, j, iy]
            if 0 < ix < ndx - 1:
                s0, s1, s2 = row[ix - 1], row[ix], row[ix + 1]
                denom = (s0 - 2 * s1 + s2)
                delta = 0.5 * (s0 - s2) / denom if abs(denom) > 1e-9 else 0.0
                delta = max(-0.5, min(0.5, delta))
            else:
                delta = 0.0
            rx_sub[i, j] = (ix - r) + delta
    resid_x = (pred_i.astype(float)[None, :] + rx_sub) - pred_real[None, :]
    return np.stack([vy, resid_x], axis=-1)


# ---------------------------------------------------------------------------
# ARM: percol_remap — warp b by the known per-column pose, then rigid match.
# ---------------------------------------------------------------------------
def vector_field_percol(a, b, block, pred_col, continuous=False):
    """Warp b PER COLUMN by pred_col (undo the predicted self-motion) then a rigid
    block match searches +-block for the residual DEPTH shift. continuous=False:
    integer roll (admissible, b stays stepped). continuous=True: LINEAR interp of
    b (a cross-frame sub-pixel warp)."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    r = int(block); H, W = a.shape; nh, nw = H // block, W // block
    pad = int(np.ceil(np.abs(pred_col).max())) + r + 2
    bp = np.pad(b, ((0, 0), (pad, pad)), mode="edge")
    bw = np.empty_like(b)
    for x in range(W):
        pos = pad + x + pred_col[x]
        if continuous:
            p0 = int(np.floor(pos)); f = pos - p0
            bw[:, x] = (1 - f) * bp[:, p0] + f * bp[:, p0 + 1]
        else:
            bw[:, x] = bp[:, pad + x + int(round(pred_col[x]))]

    def blocks(x):
        return (x[:nh * block, :nw * block]
                .reshape(nh, block, nw, block).transpose(0, 2, 1, 3))

    A = blocks(a); bwp = np.pad(bw, r, mode="edge")
    best = np.full((nh, nw), np.inf); vy = np.zeros((nh, nw)); rx = np.zeros((nh, nw))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
    offs.sort(key=lambda o: (o[0] * o[0] + o[1] * o[1], o[0], o[1]))
    for dy, dx in offs:
        sh = bwp[r + dy:r + dy + H, r + dx:r + dx + W]
        sad = np.abs(A - blocks(sh)).sum(axis=(2, 3)); upd = sad < best
        best = np.where(upd, sad, best); vy = np.where(upd, float(dy), vy); rx = np.where(upd, float(dx), rx)
    return np.stack([vy, rx], axis=-1)


# ---------------------------------------------------------------------------
# ARM: subpix_render — rebuild b by LINEAR interp (INADMISSIBLE diagnostic).
# ---------------------------------------------------------------------------
def rebuild_scene_subpix_render(sd, depths, base, ref_idx, rot, paths):
    """A scene whose frame b is rendered by LINEAR interpolation at FRACTIONAL
    d_col(x) (no round). INADMISSIBLE (the observable is no longer stepped) — a
    diagnostic isolating the RENDER step's contribution. Same crop draw order as
    make_projected_scene so `a` is byte-identical to the integer-render scene."""
    rng = np.random.default_rng(sd); N = len(depths)
    edges, d_col, s_col, band_of = project_columns(depths, base, GRID, BLOCK, rot=rot)
    off0 = int(max(int(s_col.max()), 0)); src_w = GRID + off0
    img_idx = int(rng.integers(len(paths))); g = _load_gray(paths[img_idx]); H, Wd = g.shape
    if H < GRID or Wd < src_w:
        if H >= src_w and Wd >= GRID:
            g = g.T; H, Wd = g.shape
    r0 = int(rng.integers(H - GRID + 1)); c0 = int(rng.integers(Wd - src_w + 1))
    src = g[r0:r0 + GRID, c0:c0 + src_w].copy()
    a = src[:, off0:off0 + GRID].copy()
    b = np.zeros_like(a)
    for x in range(GRID):
        pos = x + off0 - d_col[x]; p0 = int(np.floor(pos)); f = pos - p0
        p0 = max(0, min(src.shape[1] - 2, p0))
        b[:, x] = (1 - f) * src[:, p0] + f * src[:, p0 + 1]
    owner = np.tile(owner_per_block_from_band(band_of, BLOCK), (GRID // BLOCK, 1))
    return dict(a=a, b=b, depths=depths, base=base, ref_idx=ref_idx, rot=rot,
                block=BLOCK, N=N, d_col=d_col, s_col=s_col, band_of=band_of,
                off0=off0, owner=owner, grid_=GRID)


def owner_per_block_from_band(band, block):
    nw = GRID // block; ow = np.zeros(nw, dtype=int)
    for c in range(nw):
        owners = set(int(band[x]) for x in range(c * block, (c + 1) * block))
        ow[c] = owners.pop() if len(owners) == 1 else min(owners)
    return ow


# ---------------------------------------------------------------------------
# THE SIX ARMS — each returns (order_ok: bool, band_resid: np.ndarray[N]).
# ---------------------------------------------------------------------------
def arm_int_int(sc):
    """DEFAULT = 126000 full_cf: integer pred @ block-centre + integer SAD."""
    pred = np.round(efference_field(sc, True)).astype(int)
    R = vector_field_eff(sc["a"], sc["b"], sc["block"], pred)
    br = _band_resid_from_R(R, sc["owner"], sc["N"])
    return _band_order_ok(br), br


def arm_subpix_sensor(sc):
    pred_real = efference_field(sc, True)  # REAL
    R = vector_field_eff_subpix(sc["a"], sc["b"], sc["block"], pred_real)
    br = _band_resid_from_R(R, sc["owner"], sc["N"])
    return _band_order_ok(br), br


def arm_finer_block(sc, block=6):
    pred = np.round(efference_field_block(sc, block)).astype(int)
    R = vector_field_eff(sc["a"], sc["b"], block, pred)
    ow = np.tile(owner_per_block(sc, block), (R.shape[0], 1))
    br = _band_resid_from_R(R, ow, sc["N"])
    return _band_order_ok(br), br


def arm_percol_remap(sc, continuous=False):
    R = vector_field_percol(sc["a"], sc["b"], sc["block"],
                            efference_percol(sc), continuous=continuous)
    br = _band_resid_from_R(R, sc["owner"], sc["N"])
    return _band_order_ok(br), br


def arm_oracle(sc, pred_real=True):
    """TRUE per-block-mean displacement minus pred — bypasses the SAD block match.
    The credit LOCALIZER: if this holds where every real sensor breaks, the SENSOR
    block-match is binding and the single frame pair holds the information."""
    t = sc["t"][..., 1]
    pred = efference_field(sc, True) if pred_real else np.round(efference_field(sc, True))
    R = np.stack([np.zeros_like(t), t - pred[None, :]], axis=-1)
    br = _band_resid_from_R(R, sc["owner"], sc["N"])
    return _band_order_ok(br), br


def continuous_oracle_band_resid(sc):
    """Per-band mean of d_col(x) - d_pred_cont(x) (NO sensor). If flat in rot,
    depth and rotation are separable in the CONTINUOUS map when the pose is known
    -> NO 2-frame entanglement."""
    grid = GRID; f0 = float(grid); cx = grid / 2.0; rot = sc["rot"]
    Zref = float(sc["depths"][sc["ref_idx"]]); x = np.arange(grid)
    d_pred = np.full(grid, sc["base"] / Zref) + (rot * (f0 + (x - cx) ** 2 / f0) if rot != 0 else 0.0)
    d_col = sc["d_col"]; band = sc["band_of"]
    return np.array([float(np.mean(d_col[band == i] - d_pred[band == i])) for i in range(sc["N"])])


ARMS = {
    "int_int": arm_int_int,
    "subpix_sensor": arm_subpix_sensor,
    "finer_block": arm_finer_block,
    "percol_remap": arm_percol_remap,
    "percol_remap_cont": lambda sc: arm_percol_remap(sc, continuous=True),
    "oracle": arm_oracle,
}
