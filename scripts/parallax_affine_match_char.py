"""parallax_affine_match_char — WITHIN-BLOCK AFFINE/WARP FLOW-MODEL BLOCK MATCH
(rung 128000, the corrected next lever 127000 named).

127000 proved, with a ground-truth ORACLE flat in rotation to 0.5 rad, that the
info to separate depth from rotation is ALREADY IN THE TWO-FRAME PAIR, and named
the binding constraint as the SAD block-match's within-block correspondence bias
— a rigid (dx,dy) match on a block that under rotation WARPS rather than
translates. It named the fix: estimate an AFFINE/WARP flow model DURING the match
(image-only Lucas-Kanade, `v(x,y)=A·[dx,dy]+b` fit by least squares over the
block), instead of a single rigid vector — distinct from 126000's affine GROUPING
(post-sensor, 0% credit) and from 127000's sub-pixel refine (harmed).

THIS RUNG BUILDS that sensor and measures whether it recovers the oracle. It is a
MEASUREMENT HARNESS (host-side sensor construction, exactly as 126000/127000's
`vector_field_eff` / `vector_field_eff_subpix` are) — the seeds/carve are
UNTOUCHED and the DEFAULT rigid arm is byte-identical to 127000's int_int.

THE FRAME/CONTINUUM INVARIANT (CLAUDE.md): the observable render `b` is INTEGER;
the pose→flow prediction and the affine fit's continuous parameters are CROSS-FRAME
maps and may be real. The affine fit is the admissible "bins propose, continuous
decides" verdict at the block scale.

IMAGE-ONLY DISCIPLINE (audited by the gate): the SENSOR (`affine_match_field`)
touches ONLY the two frames `a`,`b`, the block size, and the KNOWN-POSE efference
`pred_x` (= exactly what the default sensor uses as its search centre —
`round(efference_field(sc,True))`). It NEVER reads `t` / `d_col` / `s_col` /
`band_of` (the ground-truth projection). The oracle-init DRIFT and est-err
DIAGNOSTICS below DO read `t` — they are UPPER-BOUND / validation quantities
(labelled `_diag`), never the sensor, exactly as 127000's oracle is.

THE ARMS (a SENSOR selected by name; DEFAULT unchanged):
  rigid        DEFAULT = 127000 int_int: integer per-block efference remap + integer
               SAD argmin (byte-identical to 126000 full_cf).
  affine_match IMAGE-ONLY within-block affine LK: coarse translation from the rigid
               integer SAD, then LK-refine translation then the full 6-param affine
               (both with residual BACKTRACKING — robust, no tuned constant), then
               an MDL guard (inherited τ=√5, FLOW units — affine_group's exact
               rule): keep the affine block-mean ONLY if the fitted within-block
               flow SPREAD exceeds τ (a real ramp), else keep the translation mean.
  oracle       reused from 127000 (true per-block-mean `t` — the credit LOCALIZER /
               single-pair upper bound). NOT a buildable sensor.

`affine_match` and `rigid` both run at a swept BLOCK size (the ablation arm: an
affine fit needs enough pixels, so block scale is an identifiability variable).
"""
from __future__ import annotations
import numpy as np

from parallax_affine_char import (scene, efference_field, vector_field_eff, GRID, BLOCK)
from parallax_char import SQRT5
from parallax_subpixel_char import (efference_field_block, owner_per_block,
                                    _band_resid_from_R, _band_order_ok, arm_oracle)


# ---------------------------------------------------------------------------
# Bilinear sampler + robust affine Lucas-Kanade (IMAGE-ONLY).
# ---------------------------------------------------------------------------
def _bilinear(img, xs, ys):
    H, W = img.shape
    x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
    fx = xs - x0; fy = ys - y0
    x0c = np.clip(x0, 0, W - 1); x1c = np.clip(x0 + 1, 0, W - 1)
    y0c = np.clip(y0, 0, H - 1); y1c = np.clip(y0 + 1, 0, H - 1)
    Ia = img[y0c, x0c]; Ib = img[y0c, x1c]; Ic = img[y1c, x0c]; Id = img[y1c, x1c]
    return (Ia * (1 - fx) * (1 - fy) + Ib * fx * (1 - fy)
            + Ic * (1 - fx) * fy + Id * fx * fy)


def _warp_resid(Tblk, b, xs, ys, dx, dy, p):
    u = p[0] + p[1] * dx + p[2] * dy; w = p[3] + p[4] * dx + p[5] * dy
    return float(np.mean(np.abs(Tblk - _bilinear(b, xs + u, ys + w))))


def _lk_refine(Tblk, b, xs, ys, dx, dy, p, n_params, n_iter):
    """Gauss-Newton LK refine of the first n_params flow params (2=translation,
    6=affine) with residual BACKTRACKING (accept a step only if it lowers the warp
    residual; else halve up to 4×; else stop) — robust, no tuned constant.
    Returns (p, warp_resid, tt_eigmin) where tt_eigmin is the smallest eigenvalue
    of the translation structure tensor (the identifiability / aperture read)."""
    tteig = np.nan
    p = p.copy(); cur = _warp_resid(Tblk, b, xs, ys, dx, dy, p)
    for _ in range(n_iter):
        u = p[0] + p[1] * dx + p[2] * dy
        w = p[3] + p[4] * dx + p[5] * dy
        sx = xs + u; sy = ys + w
        bw = _bilinear(b, sx, sy)
        bwx = 0.5 * (_bilinear(b, sx + 1, sy) - _bilinear(b, sx - 1, sy))
        bwy = 0.5 * (_bilinear(b, sx, sy + 1) - _bilinear(b, sx, sy - 1))
        cols = [bwx, bwx * dx, bwx * dy, bwy, bwy * dx, bwy * dy][:n_params]
        SD = np.stack(cols, axis=1)
        g = SD.T @ (Tblk - bw); Hn = SD.T @ SD
        tteig = float(np.linalg.eigvalsh(np.array(
            [[float((bwx * bwx).sum()), float((bwx * bwy).sum())],
             [float((bwx * bwy).sum()), float((bwy * bwy).sum())]]))[0])
        dp = np.linalg.lstsq(Hn, g, rcond=None)[0]
        step = 1.0; accepted = False
        for _bt in range(5):
            pt = p.copy(); pt[:n_params] += step * dp
            rt = _warp_resid(Tblk, b, xs, ys, dx, dy, pt)
            if rt < cur:
                p = pt; cur = rt; accepted = True; break
            step *= 0.5
        if not accepted or np.abs(step * dp).max() < 1e-4:
            break
    return p, cur, tteig


def _affine_block(a, b, x0, y0, block, u_init, tau, n_iter):
    """One block's IMAGE-ONLY affine match. Returns
    (u0 block-mean x-flow, tt_eigmin, used_affine, warp_resid, flow_spread)."""
    ys, xs = np.mgrid[y0:y0 + block, x0:x0 + block]
    ys = ys.ravel().astype(float); xs = xs.ravel().astype(float)
    xc = x0 + (block - 1) / 2.0; yc = y0 + (block - 1) / 2.0
    dx = xs - xc; dy = ys - yc
    Tblk = _bilinear(a, xs, ys)
    p0 = np.array([u_init, 0., 0., 0., 0., 0.])
    p_t, r_t, tte = _lk_refine(Tblk, b, xs, ys, dx, dy, p0, 2, n_iter)   # translation
    p_a, r_a, tte = _lk_refine(Tblk, b, xs, ys, dx, dy, p_t, 6, n_iter)  # affine
    # MDL guard (affine_group's EXACT rule, τ in FLOW units): engage the slope only
    # when the fitted within-block x-flow SPREAD exceeds the sensor tolerance τ.
    spread = float(np.max(np.abs(p_a[1] * dx + p_a[2] * dy)))
    used = spread > tau
    u0 = p_a[0] if used else p_t[0]
    return float(u0), tte, bool(used), (r_a if used else r_t), spread


def affine_match_field(a, b, block, pred_x, tau=SQRT5, n_iter=12):
    """IMAGE-ONLY within-block affine flow-model match. `pred_x` is the KNOWN-POSE
    per-block efference (integer, = the default sensor's search centre). Returns
    (R[nh,nw,2] residual (0, u0-pred), diagnostics dict). Touches ONLY a,b,pred_x."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    H, W = a.shape; nh, nw = H // block, W // block
    Rrig = vector_field_eff(a, b, block, np.asarray(pred_x, int))  # image-only coarse
    u_init = np.asarray(pred_x, float)[None, :] + Rrig[..., 1]
    R = np.zeros((nh, nw, 2)); tt = np.zeros((nh, nw)); used = np.zeros((nh, nw))
    for i in range(nh):
        for j in range(nw):
            u0, tte, ua, _, _ = _affine_block(a, b, j * block, i * block, block,
                                              float(u_init[i, j]), tau, n_iter)
            R[i, j, 1] = u0 - float(pred_x[j]); tt[i, j] = tte; used[i, j] = ua
    diag = {"tt_eigmin_med": float(np.median(tt)), "used_affine": float(np.mean(used))}
    return R, diag


# ---------------------------------------------------------------------------
# THE ARMS — each returns (order_ok, band_resid, diag).
# ---------------------------------------------------------------------------
def arm_rigid(sc, block=None):
    """DEFAULT = 127000 int_int: integer efference remap + integer SAD argmin."""
    block = block or sc["block"]
    pred = np.round(efference_field_block(sc, block)).astype(int)
    R = vector_field_eff(sc["a"], sc["b"], block, pred)
    ow = np.tile(owner_per_block(sc, block), (R.shape[0], 1))
    br = _band_resid_from_R(R, ow, sc["N"])
    return _band_order_ok(br), br, {"tt_eigmin_med": np.nan, "used_affine": 0.0}


def arm_affine_match(sc, block=None, tau=SQRT5, n_iter=12):
    block = block or sc["block"]
    pred = np.round(efference_field_block(sc, block)).astype(int)
    R, diag = affine_match_field(sc["a"], sc["b"], block, pred, tau=tau, n_iter=n_iter)
    ow = np.tile(owner_per_block(sc, block), (R.shape[0], 1))
    br = _band_resid_from_R(R, ow, sc["N"])
    return _band_order_ok(br), br, diag


# ---------------------------------------------------------------------------
# DIAGNOSTICS (read GROUND TRUTH t — validation / upper-bound, NEVER the sensor).
# ---------------------------------------------------------------------------
def true_block_mean(sc, block):
    """The oracle's quantity: per-block spatial mean of the true per-column flow."""
    d_col = sc["d_col"]; nw = GRID // block
    return np.array([float(np.mean(d_col[j * block:(j + 1) * block])) for j in range(nw)])


def est_err_diag(sc, block=None):
    """|estimated block-mean − TRUE block-mean|, mean over blocks, for rigid vs
    affine. DIAGNOSTIC (reads t): how close the image-only estimator gets to what
    the oracle knows. affine > rigid means the affine model does NOT recover it."""
    block = block or sc["block"]
    pred = np.round(efference_field_block(sc, block)).astype(int)
    tmean = true_block_mean(sc, block)
    Rrig = vector_field_eff(sc["a"], sc["b"], block, pred)
    rig_abs = pred[None, :].astype(float) + Rrig[..., 1]
    Raff, _ = affine_match_field(sc["a"], sc["b"], block, pred)
    aff_abs = pred[None, :].astype(float) + Raff[..., 1]
    return (float(np.mean(np.abs(rig_abs - tmean[None, :]))),
            float(np.mean(np.abs(aff_abs - tmean[None, :]))))


def drift_from_truth_diag(sc, block=None, n_iter=12):
    """Initialise the fit AT the TRUE block-mean and measure how far u0 DRIFTS.
    DIAGNOSTIC (reads t): if the affine drifts away from truth on well-conditioned
    blocks, the intensity-match OBJECTIVE's optimum is off the true mean — the
    binding constraint is the objective, not identifiability or the optimizer.
    Returns (translation_drift, affine_drift), mean over blocks."""
    block = block or sc["block"]; a = np.asarray(sc["a"], float); b = np.asarray(sc["b"], float)
    tmean = true_block_mean(sc, block); nh = GRID // block; nw = GRID // block
    dt = []; da = []
    for i in range(nh):
        for j in range(nw):
            x0, y0 = j * block, i * block
            ys, xs = np.mgrid[y0:y0 + block, x0:x0 + block]
            ys = ys.ravel().astype(float); xs = xs.ravel().astype(float)
            xc = x0 + (block - 1) / 2.0; yc = y0 + (block - 1) / 2.0
            dx = xs - xc; dy = ys - yc; Tblk = _bilinear(a, xs, ys)
            p0 = np.array([float(tmean[j]), 0., 0., 0., 0., 0.])
            p_t, _, _ = _lk_refine(Tblk, b, xs, ys, dx, dy, p0, 2, n_iter)
            p_a, _, _ = _lk_refine(Tblk, b, xs, ys, dx, dy, p_t.copy(), 6, n_iter)
            dt.append(abs(p_t[0] - tmean[j])); da.append(abs(p_a[0] - tmean[j]))
    return float(np.mean(dt)), float(np.mean(da))


ARMS = {"rigid": arm_rigid, "affine_match": arm_affine_match, "oracle": arm_oracle}
