"""parallax_affine_char — AFFINE-FLOW grouping + FULL-FIELD efference, the two
fixes rung 125000's rotation FALSIFY named (VISION_PARALLAX_MOTION_RESULTS.md §4,
§11). This rung BUILDS both and measures which (if either) rescues the carve.

125000 proved the parallax carve survives camera TRANSLATION (depth order ρ=1.00)
but FALSIFIES under camera ROTATION (0.02 rad → depth order 100%→44%→0%). Its
diagnosis: rotation's depth-INDEPENDENT within-field curvature gradient cannot be
(a) nulled by a SINGLE-vector efference subtraction, nor (b) separated by
common-fate (which assumes surface = ONE motion vector) from depth parallax. It
named two coupled fixes: common-fate → AFFINE-FLOW grouping, and single-vector →
FULL-FIELD efference subtraction.

TWO MECHANISMS, BOTH BUILT (each ablatable as graph DATA — the arm is a flag, not
a Python fork, PROTOCOL §0):

1. FULL-FIELD EFFERENCE (`carve_full`). The known camera pose predicts the
   fixated plane's flow EVERYWHERE: d_ref(x) = base/Z_ref + rot·(f0+(x-cx)²/f0)
   (translation const + the DEPTH-INDEPENDENT rotational curvature). The single-
   vector baseline (`carve_single`, = 125000 EXACT) knows only base/Z_ref.

   THE MECHANISM INSIGHT THIS RUNG EARNED: the full field cannot be applied as a
   POST-HOC vector subtraction (V − field), because rotation adds up to ~7 px of
   flow, pushing the ABSOLUTE displacement past the SAD sensor's aperture
   (radius = block = 8), so V is already SATURATED before you subtract. The
   efference must re-centre the sensor's SEARCH APERTURE on the predicted
   self-motion (predictive remapping) — `vector_field_eff` — so the sensor spends
   its aperture on the small DEPTH residual, not the large self-motion. The
   depth-independent rotation is then compensated and only depth parallax remains.
   When rot=0 the predicted field is a single vector and this reduces to the
   single-vector carve (the DEGENERATE case).

2. AFFINE-FLOW GROUPING (`affine_group`). Group cells by consistency with ONE
   local affine model v(pos)=A·pos+b (flow linear in image position), not a single
   vector, so a slant's ramp / a rotation's curvature is ONE affine surface not
   many strips. Translation's uniform flow is the DEGENERATE affine case (A=0): an
   MDL guard engages the slope ONLY when a within-region variation EXCEEDS the
   sensor tolerance τ AND an affine fit brings it back UNDER τ (a real ramp, not a
   confab outlier) — so on piecewise-constant fields affine reduces to common-fate.

NO new number is picked: τ is the inherited sensor tolerance √5 (94000's
Otsu-within-aperture accuracy = ‖(1,2)‖, MEASURED); the affine MDL threshold IS
that same τ; the search aperture is the sensor's own radius=block (94000, falls
out of overlap). The rotation magnitude the rescue tolerates is MEASURED (swept),
never chosen. FRAME/CONTINUUM INVARIANT (CLAUDE.md): the predicted flow is a
CROSS-FRAME map carrying continuous (rot, f0) intensionally; the observable is the
STEPPED integer render — and the rescue's own bound falls out of exactly this
(the continuously-cancelled rotation leaves a stepped residual).

REUSES 125000's scene synthesis byte-for-byte (`make_projected_scene`,
`project_columns`) and the inherited SAD sensor (`vector_field`) for the single-
vector arm. NO Rust, NO new seed — a measurement extending the parallax carve,
exactly as 125000 was.
"""
from __future__ import annotations
import numpy as np

from parallax_char import group_common_fate, SQRT5
from parallax_motion_char import (make_projected_scene, project_columns, carve,
                                  STAGE_A_BASE, STAGE_A_DEPTHS, STAGE_A_REF)
from domains.motion_group_world import vector_field

BLOCK, GRID = 8, 144


def eff_count(sizes):
    p = np.asarray(sizes, float); p = p / p.sum()
    return float(1.0 / np.sum(p * p))


def block_centers(grid, block):
    nw = grid // block
    return np.array([c * block + (block - 1) / 2.0 for c in range(nw)])


# ---------------------------------------------------------------------------
# FULL-FIELD EFFERENCE.
# ---------------------------------------------------------------------------
def efference_field(sc, full):
    """Per-block predicted x-flow of the FIXATED plane, from the KNOWN pose.

    full=False → the single scalar base/Z_ref (125000's single-vector delta,
                 broadcast — the DEGENERATE case).
    full=True  → + rot·(f0+(x-cx)²/f0), the DEPTH-INDEPENDENT rotational curvature.
    Continuous (a cross-frame map); the caller rounds to the stepped observable.
    """
    grid, block = sc["grid_"], sc["block"]
    nw = grid // block
    base = sc["base"]; Zref = float(sc["depths"][sc["ref_idx"]]); rot = sc["rot"]
    f0 = float(grid); cx = grid / 2.0
    xc = block_centers(grid, block)
    ex = np.full(nw, base / max(Zref, 1e-3))
    if full and rot != 0.0:
        ex = ex + rot * (f0 + (xc - cx) ** 2 / f0)
    return ex


def vector_field_eff(a, b, block, pred_x):
    """SAD sensor with the efference copy as a SEARCH-CENTRE prior: the search
    window is centred on the predicted per-block integer x-shift `pred_x`,
    searching ±block AROUND it. Returns the RESIDUAL (measured − predicted), so
    self-motion within aperture of the prediction is nulled and the aperture is
    spent on the DEVIATION (depth parallax). Same SAD, same offset order, same
    Occam tie-break as `vector_field`; only the search CENTRE moves."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    r = int(block); H, W = a.shape
    nh, nw = H // block, W // block

    def blocks(x):
        return (x[:nh * block, :nw * block]
                .reshape(nh, block, nw, block).transpose(0, 2, 1, 3))

    A = blocks(a)
    pmax = int(np.abs(pred_x).max())
    padx = r + pmax
    bp = np.pad(b, ((r, r), (padx, padx)), mode="edge")
    best = np.full((nh, nw), np.inf); vy = np.zeros((nh, nw)); rx = np.zeros((nh, nw))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
    offs.sort(key=lambda o: (o[0] * o[0] + o[1] * o[1], o[0], o[1]))
    pcol = np.asarray(pred_x, int)
    for dy, dx in offs:
        sh = np.empty_like(a)
        for c in range(nw):
            adx = int(pcol[c]) + dx
            lo, hi = c * block, (c + 1) * block
            sh[:, lo:hi] = bp[r + dy:r + dy + H, padx + adx + lo: padx + adx + hi]
        sad = np.abs(A - blocks(sh)).sum(axis=(2, 3))
        upd = sad < best
        best = np.where(upd, sad, best)
        vy = np.where(upd, float(dy), vy)
        rx = np.where(upd, float(dx), rx)
    return np.stack([vy, rx], axis=-1)


# ---------------------------------------------------------------------------
# AFFINE-FLOW GROUPING (MDL-guarded degenerate reduction to common-fate).
# ---------------------------------------------------------------------------
def affine_group(field, tau, grid=GRID, block=BLOCK):
    """Region-grow by consistency with ONE affine model v(pos)=A·pos+b per region.
    A region uniform within τ (or <3 cells, or an outlier the slope cannot bring
    under τ) uses the CONSTANT model (b=mean, A=0) — the join test is EXACTLY
    common-fate's. The slope engages ONLY when a within-region variation exceeds τ
    AND an affine fit brings the max residual back under τ (a genuine ramp). The
    only threshold is τ; nothing is picked. Deterministic raster seeding."""
    nh, nw = field.shape[:2]
    xc = block_centers(grid, block); yc = block_centers(grid, block)
    POS = np.zeros((nh, nw, 2)); POS[..., 0] = xc[None, :]; POS[..., 1] = yc[:, None]
    lab = -np.ones((nh, nw), dtype=int); nxt = 0
    for r0 in range(nh):
        for c0 in range(nw):
            if lab[r0, c0] >= 0:
                continue
            members = [(r0, c0)]; lab[r0, c0] = nxt
            changed = True
            while changed:
                changed = False
                Vm = np.array([field[r, c] for r, c in members])
                b = Vm.mean(axis=0)
                const_resid = float(np.hypot(*(Vm - b).T).max())
                use_affine = False; coef = None
                if len(members) >= 3 and const_resid > tau:
                    P = np.array([POS[r, c] for r, c in members])
                    Xd = np.hstack([P, np.ones((len(members), 1))])
                    coef, *_ = np.linalg.lstsq(Xd, Vm, rcond=None)
                    aff_resid = float(np.hypot(*(Vm - Xd @ coef).T).max())
                    use_affine = aff_resid < const_resid and aff_resid <= tau
                frontier = set()
                for (r, c) in members:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < nh and 0 <= cc < nw and lab[rr, cc] < 0:
                            frontier.add((rr, cc))
                for (rr, cc) in sorted(frontier):
                    pred = (np.array([POS[rr, cc, 0], POS[rr, cc, 1], 1.0]) @ coef
                            if use_affine else b)
                    if np.hypot(*(field[rr, cc] - pred)) <= tau:
                        lab[rr, cc] = nxt; members.append((rr, cc)); changed = True
            nxt += 1
    return lab, nxt


COMMON_FATE = lambda f, t: group_common_fate(f, t)
AFFINE = lambda f, t: affine_group(f, t, GRID, BLOCK)


# ---------------------------------------------------------------------------
# THE CARVE — two efference arms × a pluggable grouper.
# ---------------------------------------------------------------------------
def _read_off(sc, R, lab, nl):
    sizes = sorted([(lab == k).sum() for k in range(nl)], reverse=True)
    depths = np.asarray(sc["depths"], float)
    band_resid = np.array([float(R[sc["owner"] == i][..., 1].mean())
                           if (sc["owner"] == i).any() else np.nan
                           for i in range(sc["N"])])
    inv_Z = 1.0 / depths
    order_resid = list(np.argsort(-band_resid)); order_invZ = list(np.argsort(-inv_Z))
    def _ranks(a): return np.argsort(np.argsort(a))
    rho = (float(np.corrcoef(_ranks(band_resid), _ranks(inv_Z))[0, 1])
           if sc["N"] > 1 else 1.0)
    refmask = (sc["owner"] == sc["ref_idx"])
    return dict(eff=eff_count(sizes), largest=sizes[0] / lab.size, count=nl,
                depth_order_correct=bool(order_resid == order_invZ),
                depth_rank_rho=rho,
                ref_resid_se=float(np.abs(R[refmask][..., 1]).max()),
                band_resid=band_resid.tolist(), inv_Z=inv_Z.tolist())


def carve_single(sc, tau, grouper=COMMON_FATE):
    """125000 EXACT: single-vector post-hoc subtraction, then group. grouper=
    COMMON_FATE reproduces 125000's carve byte-for-byte (verified in the gate)."""
    V = vector_field(sc["a"], sc["b"], sc["block"])
    s_ref = int(round(sc["base"] / max(float(sc["depths"][sc["ref_idx"]]), 1e-3)))
    R = V - np.array([0.0, float(s_ref)])
    lab, nl = grouper(R, tau)
    return _read_off(sc, R, lab, nl)


def carve_full(sc, tau, grouper=COMMON_FATE):
    """FULL-FIELD efference as a search-centre remap, then group."""
    sc["grid_"] = sc.get("grid_", GRID)
    pred_x = np.round(efference_field(sc, True)).astype(int)
    R = vector_field_eff(sc["a"], sc["b"], sc["block"], pred_x)
    lab, nl = grouper(R, tau)
    return _read_off(sc, R, lab, nl)


CARVES = {"single": carve_single, "full": carve_full}
GROUPERS = {"cf": COMMON_FATE, "affine": AFFINE}


def scene(rng_seed, depths, base, ref_idx, tilt=0.0, tilt_bands=(), rot=0.0, paths=None):
    sc = make_projected_scene(np.random.default_rng(rng_seed), depths, base, BLOCK, GRID,
                              ref_idx, paths, tilt=tilt, tilt_bands=tilt_bands, rot=rot)
    sc["grid_"] = GRID
    return sc
