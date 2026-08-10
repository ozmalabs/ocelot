"""parallax_motion_char — TRUE-MOTION twin of parallax_real_char (rung 125000).

THE ONE VARIABLE THIS RUNG CHANGES vs the parallax rungs (116000/124000): the
image displacement is no longer a HAND-SET uniform per-band shift (a "windowed
slide"). It FALLS OUT of depth + camera motion via PERSPECTIVE PROJECTION.

A moving pinhole camera over a scene at depth Z produces image displacement
d = f*T / Z  (a lateral translation T, focal f) — nearer surfaces (small Z)
sweep FASTER. That is TRUE motion parallax, DERIVED, not imposed. The agent's
efference copy is its KNOWN camera pose (T, and the gaze that FIXATES the
reference plane); it subtracts the fixated plane's predicted flow and the
residual for the OTHER planes = f*T*(1/Z_i - 1/Z_ref) separates them BY DEPTH.

Everything else — the byte-identical static frame `a`, the common-fate grouping,
the participation-ratio knee, the SAD sensor, REAL BSDS300 photometry (proven
in 124000, kept unchanged) — is REUSED from the parallax rungs.

    STAGE A (fronto-parallel planes, camera TRANSLATION): displacement is still
    piecewise-constant per plane (Z constant over a fronto-parallel plane), so a
    projected scene is BYTE-IDENTICAL to the windowed slide with the derived
    integer shifts — but the shifts fall out of 1/Z and the DEPTH ORDER
    (nearer = larger residual) is now a CHECKABLE prediction, not a label. A
    STATIC-camera control (T=0 -> all shifts 0 -> b==a) gives one blob.

    STAGE B (a SLANTED plane and/or camera ROTATION): Z varies WITHIN a surface,
    so d(x)=f*T/Z(x) is a GRADIENT within one surface — NOT one vector.
    Common-fate grouping ASSUMES surface = one motion. This is the real test.

THE FRAME/CONTINUUM INVARIANT (CLAUDE.md): the projection carries continuous
(f, T, Z, slant, rot) as a CROSS-FRAME map; the OBSERVABLE displacement is the
STEPPED integer render (round to a pixel). We render by integer per-column shift
(`np.round`), exactly as the sensor senses integers. The continuous parameters
live only in the map that PRODUCES the frame, never in a frame coordinate.

NO fabrication, NO wrap (the 124000 discipline): every displaced pixel is a REAL
scene neighbour, sourced from a crop WIDER than the grid (off0 = max shift). A
toroidal roll would inject a false wrap-seam — a new confound, not photometry.
"""
from __future__ import annotations
import os
import numpy as np
from PIL import Image

# REUSE the parallax rungs' carve machinery UNCHANGED — the whole point.
from parallax_char import (group_common_fate, field_discontinuity, size_dist, SQRT5)
from parallax_real_char import bsds_paths, _load_gray, make_real_scene
from domains.motion_group_world import vector_field

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)


# ----------------------------------------------------------------------------
# PERSPECTIVE PROJECTION: displacement FALLS OUT of depth + camera motion.
# ----------------------------------------------------------------------------
def project_columns(depths, base, grid, block, tilt=0.0, tilt_bands=(),
                    rot=0.0, f0=None):
    """Per-column real displacement d(x) and integer render shift s(x)=round(d).

    depths : per-band base depth Z_i.
    base   : f*T (the camera-motion strength; base=0 is the STATIC control).
    tilt   : FRACTIONAL depth variation across a band's half-width, applied to
             the bands in `tilt_bands` (Stage B). Z(x)=Z_i*(1+tilt*u), u in
             [-1,1] the normalised column within the band. A SLANTED plane: Z
             varies WITHIN the surface, so d(x)=base/Z(x) is a GRADIENT within
             one surface. Bounded |tilt|<1 keeps Z>0 (the plane never passes
             through the camera).
    rot    : y-axis camera rotation (rad). Adds a DEPTH-INDEPENDENT horizontal
             flow u(x)=rot*(f0 + (x-cx)^2/f0) (pinhole small-angle) — a gradient
             across the whole field with NO depth structure.

    Returns (edges, d_col[grid], s_col[grid], band_of_col[grid]).
    d(x)=base/Z(x) (+ rotation) — nearer (small Z) sweeps faster. round to a
    pixel: the observable is stepped (frame/continuum invariant).
    """
    N = len(depths)
    edges = [round(i * grid / N) for i in range(N + 1)]
    if f0 is None:
        f0 = float(grid)
    cx = grid / 2.0
    band_of = np.zeros(grid, dtype=int)
    d_col = np.zeros(grid)
    for x in range(grid):
        bi = N - 1
        for i in range(N):
            if edges[i] <= x < edges[i + 1]:
                bi = i
                break
        band_of[x] = bi
        Z = float(depths[bi])
        if bi in tilt_bands and tilt != 0.0:
            bc = (edges[bi] + edges[bi + 1] - 1) / 2.0
            half = max((edges[bi + 1] - edges[bi]) / 2.0, 1.0)
            u = (x - bc) / half                       # normalised in [-1, 1]
            Z = float(depths[bi]) * (1.0 + tilt * u)
        Z = max(Z, 1e-3)
        d = base / Z
        if rot != 0.0:
            d += rot * (f0 + (x - cx) ** 2 / f0)
        d_col[x] = d
    s_col = np.round(d_col).astype(int)
    return edges, d_col, s_col, band_of


def _src_crop(rng, grid, src_w, paths, select="random", n_candidates=64):
    """A REAL BSDS grayscale crop of shape (grid, src_w), drawn in the SAME rng
    order as parallax_real_char.make_real_scene (so a fronto-parallel projected
    scene is byte-identical to the windowed slide it reduces to)."""
    if select == "random":
        img_idx = int(rng.integers(len(paths)))
        g = _load_gray(paths[img_idx])
        H, W = g.shape
        if H < grid or W < src_w:
            if H >= src_w and W >= grid:
                g = g.T; H, W = g.shape
            else:
                raise RuntimeError(f"BSDS image {paths[img_idx]} too small: {g.shape}.")
        r0 = int(rng.integers(H - grid + 1)); c0 = int(rng.integers(W - src_w + 1))
    else:
        raise ValueError(select)
    return g[r0:r0 + grid, c0:c0 + src_w], img_idx, r0, c0


def make_projected_scene(rng, depths, base, block, grid, ref_idx, paths,
                         tilt=0.0, tilt_bands=(), rot=0.0, select="random"):
    """The TRUE-MOTION scene: displacement DERIVED from depth+camera-motion by
    perspective projection, rendered per-column from a REAL BSDS crop.

    Returns the parallax-family dict keys plus the projection provenance
    (`d_col`, `s_col`, `depths`, `base`, `tilt`, `rot`). `delta` is the
    efference copy = the fixated (reference) plane's predicted integer flow
    round(base/Z_ref) — the KNOWN camera pose, never estimated from pixels.
    """
    N = len(depths)
    edges, d_col, s_col, band_of = project_columns(
        depths, base, grid, block, tilt=tilt, tilt_bands=tilt_bands, rot=rot)
    off0 = int(max(int(s_col.max()), 0))
    src_w = grid + off0
    src, img_idx, r0, c0 = _src_crop(rng, grid, src_w, paths, select=select)

    a = src[:, off0:off0 + grid].copy()
    b = np.zeros_like(a)
    for x in range(grid):
        b[:, x] = src[:, x + off0 - int(s_col[x])]

    nh = nw = grid // block
    t = np.zeros((nh, nw, 2))
    owner = np.zeros((nh, nw), dtype=int)
    mixed = np.zeros((nh, nw), dtype=bool)
    within_block_step = np.zeros((nh, nw))   # Stage-B diagnostic: gradient WITHIN a block
    for c in range(nw):
        lo, hi = c * block, (c + 1) * block
        cols = list(range(lo, hi))
        owners = set(int(band_of[x]) for x in cols)
        if len(owners) == 1:
            owner[:, c] = owners.pop()
        else:
            mixed[:, c] = True
            owner[:, c] = min(owners)
        t[:, c, 1] = float(np.mean(d_col[cols]))          # mean real displacement
        within_block_step[:, c] = float(s_col[cols].max() - s_col[cols].min())

    s_ref = int(round(base / max(float(depths[ref_idx]), 1e-3)))
    delta = np.array([0.0, float(s_ref)])

    # per-block std of `a` (the sensor's cliff variable, rung 94000)
    blk = a[:nh * block, :nw * block].reshape(nh, block, nh, block)
    block_std = blk.std(axis=(1, 3))

    return dict(a=a, b=b, b_depth=b, t=t, t_depth=t, owner=owner, mixed=mixed,
                delta_ref=delta, delta=delta, ref_idx=ref_idx, edges=edges, N=N,
                block=block, depths=list(depths), base=float(base),
                tilt=float(tilt), tilt_bands=tuple(tilt_bands), rot=float(rot),
                d_col=d_col, s_col=s_col, band_of=band_of, off0=off0,
                img=os.path.basename(paths[img_idx]), crop=(r0, c0),
                within_block_step=within_block_step,
                block_std=block_std, mean_block_std=float(np.mean(block_std)),
                min_band_std=float(np.nanmin([
                    block_std[owner == i].mean() if (owner == i).any() else np.nan
                    for i in range(N)])))


# ----------------------------------------------------------------------------
# THE CARVE (reused verbatim) + the DEPTH-ORDER read-off.
# ----------------------------------------------------------------------------
def carve(sc, tau):
    """The eye's carve on one TRUE-MOTION scene: efference-copy subtraction +
    common-fate grouping of the SENSED field. Adds the depth-order read-off:
    per-band mean residual velocity, and whether it is MONOTONIC in true 1/Z
    (nearer -> larger residual) — a prediction that FALLS OUT of the projection,
    never told to the carve."""
    V = vector_field(sc["a"], sc["b"], sc["block"])
    t = sc["t"]
    delta = sc["delta"]
    R_se = V - delta
    R_gt = t - delta
    lab, nl = group_common_fate(R_se, tau)
    sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
    p = np.asarray(sizes, float); p = p / p.sum()
    eff = float(1.0 / np.sum(p * p))
    confab = float(np.mean(np.abs(V - t).sum(axis=-1) > 0.5))
    refmask = (sc["owner"] == sc["ref_idx"])

    # DEPTH ORDER: per-band mean sensed residual (x-displacement, index 1).
    depths = np.asarray(sc["depths"], float)
    band_resid = np.array([float(R_se[sc["owner"] == i][..., 1].mean())
                           if (sc["owner"] == i).any() else np.nan
                           for i in range(sc["N"])])
    inv_Z = 1.0 / depths                      # nearer (small Z) -> large 1/Z
    # order bands by recovered residual (descending) vs by true 1/Z (descending)
    order_resid = list(np.argsort(-band_resid))
    order_invZ = list(np.argsort(-inv_Z))
    depth_order_correct = (order_resid == order_invZ)
    # rank correlation (Spearman via ranks) as a graded read
    def _ranks(a):
        return np.argsort(np.argsort(a))
    rho = float(np.corrcoef(_ranks(band_resid), _ranks(inv_Z))[0, 1]) if sc["N"] > 1 else 1.0

    return dict(
        eff=eff, largest=sizes[0] / lab.size, count=nl,
        median=float(np.median(sizes)),
        top5=[s / lab.size for s in sizes[:5]] + [0.0] * max(0, 5 - len(sizes)),
        ref_resid_se=float(np.abs(R_se[refmask]).max()),
        ref_resid_gt=float(np.abs(R_gt[refmask]).max()),
        sensor_err_max=float(np.abs(V - t).max()),
        confab_rate=confab, disc_gt=field_discontinuity(R_gt),
        band_resid=band_resid.tolist(), inv_Z=inv_Z.tolist(),
        depth_order_correct=bool(depth_order_correct), depth_rank_rho=rho,
        within_block_step_max=float(sc["within_block_step"].max()),
    )


# The Stage-A geometry, realizing the windowed-slide floor's [0,3,6] shifts from
# DEPTH: base=f*T=30; Z=[300,10,5] -> d=[0.1,3,6] -> round [0,3,6]. ref=middle.
# The far band (Z=300) has SUB-PIXEL parallax that rounds to 0 — an honest
# distant background (the frame/continuum invariant: the map is continuous, the
# observable is stepped). Residuals after delta=round(30/10)=3: [-3,0,+3].
STAGE_A_BASE = 30.0
STAGE_A_DEPTHS = [300.0, 10.0, 5.0]          # far, mid(ref), near -> d=[0,3,6]
STAGE_A_REF = 1


if __name__ == "__main__":
    import sys
    sys.path.insert(0, _HERE)
    paths = bsds_paths()
    base, depths = STAGE_A_BASE, STAGE_A_DEPTHS
    print("=== BYTE-IDENTITY: fronto-parallel projection == windowed slide [0,3,6] ===")
    for sd in (116000, 116001, 116002):
        sc_p = make_projected_scene(np.random.default_rng(sd), depths, base, 8, 144, 1, paths)
        sc_w = make_real_scene(np.random.default_rng(sd), [0, 3, 6], 8, 144, 1, paths, select="random")
        print(f"  seed {sd}: a identical={np.array_equal(sc_p['a'], sc_w['a'])} "
              f"b identical={np.array_equal(sc_p['b'], sc_w['b_depth'])} "
              f"shifts={sc_p['s_col'][::48].tolist()} img={sc_p['img']}")

    print("\n=== STAGE A: depth order falls out (nearer=larger residual) ===")
    e0, e5, dok = [], [], []
    for sd in range(116000, 116030):
        sc = make_projected_scene(np.random.default_rng(sd), depths, base, 8, 144, 1, paths)
        r0 = carve(sc, 0.0); r5 = carve(sc, SQRT5)
        e0.append(r0["eff"]); e5.append(r5["eff"]); dok.append(r5["depth_order_correct"])
    print(f"  n=30 eff(t0)={np.mean(e0):.2f} eff(s5)={np.mean(e5):.2f} "
          f"depth_order_ok(s5)={np.mean(dok):.2f}")

    print("\n=== STATIC control: base=0 -> one blob ===")
    es = [carve(make_projected_scene(np.random.default_rng(sd), depths, 0.0, 8, 144, 1, paths), SQRT5)["eff"]
          for sd in range(116000, 116010)]
    print(f"  static eff(s5) mean={np.mean(es):.3f} max={np.max(es):.3f}")

    print("\n=== STAGE B(i): SINGLE full-frame slanted plane, sweep tilt ===")
    Z0 = 7.5   # d0 = base/Z0 = 4 px central flow
    for tilt in (0.0, 0.2, 0.4, 0.6, 0.8):
        e0s, e5s, wbs, grad = [], [], [], []
        for sd in range(116000, 116020):
            sc = make_projected_scene(np.random.default_rng(sd), [Z0], base, 8, 144, 0, paths,
                                      tilt=tilt, tilt_bands=(0,))
            r0 = carve(sc, 0.0); r5 = carve(sc, SQRT5)
            e0s.append(r0["eff"]); e5s.append(r5["eff"]); wbs.append(r5["within_block_step_max"])
            grad.append(float(np.abs(np.diff(sc["s_col"][::8])).max()))   # per-block step
        print(f"  tilt={tilt:.1f}: eff(t0)={np.mean(e0s):.2f} eff(s5)={np.mean(e5s):.2f} "
              f"per_block_step_max={max(grad):.0f} within_block_step_max={max(wbs):.0f}")

    print("\n=== STAGE B(ii): 3 planes, MIDDLE slanted, sweep tilt (merge-wrongly?) ===")
    for tilt in (0.0, 0.2, 0.4, 0.6):
        e5s, dok5 = [], []
        for sd in range(116000, 116020):
            sc = make_projected_scene(np.random.default_rng(sd), depths, base, 8, 144, 1, paths,
                                      tilt=tilt, tilt_bands=(1,))
            r5 = carve(sc, SQRT5)
            e5s.append(r5["eff"]); dok5.append(r5["depth_order_correct"])
        print(f"  tilt={tilt:.1f}: eff(s5)={np.mean(e5s):.2f} depth_order_ok={np.mean(dok5):.2f}")
