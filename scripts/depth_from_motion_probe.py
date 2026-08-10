#!/usr/bin/env python3
"""DEPTH-FROM-MOTION / DEPTH-AWARE EGOMOTION (block 158000-158999).

THE WALL (157000): a single global egomotion vector cannot cancel a FORWARD
WALK, whose optic flow is DEPTH-DEPENDENT (parallax — near flows faster than
far). 157000's dominant-mode gain CAPTURED E1M1's egomotion (154/159 frames) but
the end-to-end cancellation FAILED because one uniform vector can't cancel
parallax; the mover stayed buried in the near/far residual.

THE MECHANISM — forward walk = global radial expansion from the FOE. This is
154000's expansion/divergence op ([[looming]]) applied GLOBALLY. Two things fall
out, and one is DEPTH-INDEPENDENT (the key):

  DIRECTION is depth-INDEPENDENT. Every static point flows radially AWAY from the
  Focus Of Expansion (FOE = heading) regardless of depth. Decompose flow into a
  RADIAL component (along p-FOE) + a TANGENTIAL component; static forward-walk
  flow is purely radial => tangential ~= 0 at ANY depth, while a non-radial mover
  keeps a tangential residual. RESIDUAL = the tangential (direction-inconsistent)
  component => isolates independently-moving objects WITHOUT per-cell depth. The
  robust, depth-independent egomotion cancellation.

  MAGNITUDE gives DEPTH. For a static (radial-consistent) cell,
  |flow| = speed * r / Z  (r = |p-FOE|, Z = depth) => recovered depth
  = r / |flow| = Z / speed  (the r cancels exactly). A depth-from-motion field up
  to the unknown translation-speed scale.

REUSED (154000, looming_common_fate_probe): divergence_field (the SAME
central-difference stencil) for the expansion gate; the FOE/affine idea. REUSED
(157000, residual_salience_probe): dominant_mode_gain (the single-vector baseline
that FAILS on parallax), shape_salience, the tracker, _auc, the E1M1 world
adapter + walk/seed/grid + labels-buffer scorer. ADDED (mechanical numpy sensors,
peers of vector_field / divergence_field): estimate_foe (least-squares
intersection of the flow lines — falls out, no tuned point), the
radial-direction-consistency (tangential) residual, depth-from-radial-magnitude,
curl_field, and Otsu on the residual (the direction cutoff falls out of the
angular-residual distribution, §13).

ARCHITECTURE (CLAUDE.md — the agent is Rust). NO agent decision in Python. FOE /
radial-consistency / depth-from-magnitude / divergence / curl are MECHANICAL
sensors over pixel/flow arrays (no conditional over graph state); the salience is
the EXISTING Rust Substrate.shape_salience; the tracker is the EXISTING
_collect_tracks; the carve is the EXISTING value carve; capture_e1m1 is a world
adapter over the real WAD; the DEPTH + labels buffers are the SCORING ORACLE,
never fed to the eye (scoring is Spearman/IoU/AUC by position, never
cross-process region-id). NO Rust added, NO seed, NO default moved — new files
only, so the shipped carve / 154000 / 155000 / 157000 paths are byte-identical BY
CONSTRUCTION.

Pre-registration: VISION_DEPTH_FROM_MOTION_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Reuse 157000's E1M1 world adapter, flow, tracker, scorer, constants.
from scripts.e1m1_salience_probe import (  # noqa: E402
    capture_e1m1, _collect_tracks, _track_gt_category, _cat_values,
    _e1m1_flow_fields, _luma_stack, _default_action_seq,
    GH, GW, DOWN, BLOCK, LEVEL, N_FRAMES, SKILL, DOOM_SEED,
)
from scripts.eye_on_doom_probe import (  # noqa: E402
    quantize, run_value_carve, downsample_labels, downsample_grey, _block_mean,
)
# Reuse 157000's single-global-vector baseline (the thing that FAILS on parallax)
# and 155000's median-over-all baseline, and 154000's divergence stencil.
from scripts.residual_salience_probe import (  # noqa: E402
    dominant_mode_gain, median_all_gain,
)
from scripts.looming_common_fate_probe import divergence_field  # noqa: E402

# ---- DECLARED RESIDUALS (§13 — the sensor's aperture, NOT tuned) ------------
FLOOR = 0.5        # the block-matcher's one-pixel integer step (155000/157000's
                   # ZERO_FLOOR): |flow| < 0.5 is "no motion". Falls out of the
                   # sensor, not tuned to the score.
R_MIN = 2.0        # min radius from the FOE to define a radial DIRECTION (r>0 is
                   # required for a unit vector; 2 cells ~ the flow block). A
                   # geometric necessity, not a knob.
BLOCK_SEED = 158000


# ======================================================================
#  MECHANICAL SENSORS (numpy) — peers of vector_field / divergence_field.
# ======================================================================
def curl_field(vy, vx):
    """Per-cell curl (vorticity) curl_z = d(vy)/dx - d(vx)/dy of a flow field,
    central differences interior + one-sided border. The rotational counterpart
    of divergence_field. Pure array math (154000's stencil, transposed sign)."""
    vy = np.asarray(vy, np.float64); vx = np.asarray(vx, np.float64)
    c = np.zeros_like(vy)
    c[:, 1:-1] += (vy[:, 2:] - vy[:, :-2]) * 0.5          # d(vy)/dx
    c[1:-1, :] -= (vx[2:, :] - vx[:-2, :]) * 0.5          # -d(vx)/dy
    c[:, 0] += vy[:, 1] - vy[:, 0]
    c[:, -1] += vy[:, -1] - vy[:, -2]
    c[0, :] -= vx[1, :] - vx[0, :]
    c[-1, :] -= vx[-1, :] - vx[-2, :]
    return c


def expansion_gate(vy, vx, floor=FLOOR):
    """Is this flow field an EXPANSION (forward translation) or a ROTATION?
    A ratio that TRANSFERS (§13: ratios transfer, absolutes do not): compare the
    mean divergence to the mean |curl|. Forward translation => divergence
    dominates (radial outflow); pure rotation => curl dominates, divergence ~0.
    Returns (expansion_dominant: bool, diag)."""
    vy = np.asarray(vy, np.float64); vx = np.asarray(vx, np.float64)
    mag = np.sqrt(vy * vy + vx * vx)
    nz = mag > floor
    div = divergence_field(vy, vx)
    curl = curl_field(vy, vx)
    if not nz.any():
        return False, {"mean_div": 0.0, "mean_abs_curl": 0.0, "n_flow": 0}
    md = float(np.mean(div[nz]))
    mc = float(np.mean(np.abs(curl[nz])))
    dom = (md > mc) and (md > floor * 0.02)   # expansion outflow, not curl
    return bool(dom), {"mean_div": round(md, 4), "mean_abs_curl": round(mc, 4),
                       "n_flow": int(nz.sum())}


def estimate_foe(vy, vx, floor=FLOOR):
    """Focus Of Expansion = the least-squares intersection of the flow LINES.
    For pure translation every static flow vector v at position p lies on a line
    through the FOE: the FOE q satisfies vy*qx - vx*qy = vy*px - vx*py for every
    cell (the cross-product (q-p) x v = 0). Stack over the flow cells, weight by
    |flow| (stronger flows are more reliable), solve. The FOE FALLS OUT of the
    field — no tuned point. Returns ((foe_x, foe_y) or None, diag)."""
    vy = np.asarray(vy, np.float64); vx = np.asarray(vx, np.float64)
    gh, gw = vy.shape
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float64)
    mag = np.sqrt(vy * vy + vx * vx)
    nz = mag > floor
    n = int(nz.sum())
    if n < 8:
        return None, {"n": n, "cond": None}
    px = xx[nz]; py = yy[nz]
    fx = vx[nz]; fy = vy[nz]
    w = mag[nz]                                    # magnitude weighting
    A = np.column_stack([fy, -fx]) * w[:, None]    # rows [vy, -vx]
    b = (fy * px - fx * py) * w                    # rhs vy*px - vx*py
    ATA = A.T @ A
    sv = np.linalg.svd(ATA, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf")
    q, *_ = np.linalg.lstsq(A, b, rcond=None)
    return (float(q[0]), float(q[1])), {"n": n, "cond": round(cond, 2),
                                        "sv_ratio": round(float(sv[-1] / sv[0]), 5)}


def radial_decompose(vy, vx, foe, floor=FLOOR, r_min=R_MIN):
    """Decompose each flow vector into RADIAL (along p-FOE) + TANGENTIAL.
    Returns dict of per-cell arrays: radial_comp (signed, +ve = outward),
    tangential_mag (|flow perpendicular to radial| = the DIRECTION-INCONSISTENCY
    residual, depth-INDEPENDENT), mag (|flow|), r (|p-FOE|), and `valid` (a cell
    has enough flow AND radius to have a defined radial direction)."""
    vy = np.asarray(vy, np.float64); vx = np.asarray(vx, np.float64)
    gh, gw = vy.shape
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float64)
    fx0, fy0 = foe
    dx = xx - fx0; dy = yy - fy0
    r = np.sqrt(dx * dx + dy * dy)
    mag = np.sqrt(vy * vy + vx * vx)
    rr = np.where(r > 1e-9, r, 1.0)
    ux = dx / rr; uy = dy / rr                     # radial unit r̂ (x,y)
    radial_comp = vx * ux + vy * uy                # flow . r̂  (signed)
    tx = vx - radial_comp * ux
    ty = vy - radial_comp * uy
    tang = np.sqrt(tx * tx + ty * ty)              # |tangential| (residual)
    valid = (mag > floor) & (r > r_min)
    return {"radial_comp": radial_comp, "tangential_mag": tang, "mag": mag,
            "r": r, "valid": valid}


def depth_from_motion(vy, vx, foe, floor=FLOOR, r_min=R_MIN):
    """Recovered depth field = r / |flow| = Z / speed on cells with defined
    radial geometry. Returns (depth array, valid mask). Depth-from-motion up to
    the unknown translation-speed scale (a positive monotone of true depth)."""
    d = radial_decompose(vy, vx, foe, floor, r_min)
    mag = np.where(d["mag"] > 1e-9, d["mag"], np.nan)
    depth = d["r"] / mag
    return depth, d["valid"]


def otsu_cutoff(vals):
    """Otsu threshold on a 1-D array — the cutoff that FALLS OUT of the value's
    own distribution (§13). Used to split radial-consistent (low tangential) from
    direction-inconsistent (high) cells, and to flag movers. No magic angle."""
    v = np.asarray(vals, np.float64).reshape(-1)
    v = v[np.isfinite(v)]
    hi = v.max() if v.size else 0.0
    if hi <= 0 or v.size < 2:
        return 0.0
    bins = np.linspace(0, hi, 64)
    hist, edges = np.histogram(v, bins=bins)
    tot = hist.sum()
    if tot == 0:
        return 0.0
    w = np.cumsum(hist)
    mids = (edges[:-1] + edges[1:]) / 2
    mu = np.cumsum(hist * mids)
    mu_t = mu[-1]
    best_t, best_var = 0.0, -1.0
    for i in range(1, len(hist)):
        w0 = w[i - 1]; w1 = tot - w0
        if w0 == 0 or w1 == 0:
            continue
        m0 = mu[i - 1] / w0; m1 = (mu_t - mu[i - 1]) / w1
        var = w0 * w1 * (m0 - m1) ** 2
        if var > best_var:
            best_var, best_t = var, mids[i]
    return float(best_t)


def flag_movers(tang, valid, floor=FLOOR):
    """Direction-inconsistent (mover) cells: valid cells whose tangential residual
    exceeds BOTH the Otsu split of the residual distribution AND the sensor's
    one-pixel floor. The floor is load-bearing: a PERFECTLY radial field has only
    numerical-noise tangential (~1e-16), on which Otsu manufactures a meaningless
    split — a mover must carry at least ~1px of UNEXPLAINED (tangential) motion to
    be resolvable. Both cutoffs fall out (§13): Otsu from the distribution, the
    floor from the block-matcher's step. Returns (flagged_mask, otsu_cut)."""
    tv = np.asarray(tang, np.float64)
    cut = otsu_cutoff(tv[valid]) if np.asarray(valid).any() else 0.0
    thr = max(cut, floor)
    return (valid & (tv > thr)), cut


# ======================================================================
#  METRICS — mechanical (Spearman / AUC / IoU), never agent cognition.
# ======================================================================
def _avg_ranks(x):
    """Tie-averaged ranks of a 1-D array (for Spearman / fast AUC)."""
    x = np.asarray(x, np.float64)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), np.float64)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0   # average rank (1-based)
        i = j + 1
    return ranks


def spearman(a, b):
    """Spearman rank correlation of two paired arrays (finite pairs only)."""
    a = np.asarray(a, np.float64); b = np.asarray(b, np.float64)
    m = np.isfinite(a) & np.isfinite(b)
    a = a[m]; b = b[m]
    if a.size < 3:
        return None
    ra = _avg_ranks(a); rb = _avg_ranks(b)
    ra = ra - ra.mean(); rb = rb - rb.mean()
    den = np.sqrt((ra * ra).sum() * (rb * rb).sum())
    if den == 0:
        return None
    return float((ra * rb).sum() / den)


def auc_fast(pos, neg):
    """Mann-Whitney AUC via tie-averaged ranks (O(n log n)). 0.5 = no
    separation. None if either side empty."""
    pos = np.asarray(pos, np.float64); neg = np.asarray(neg, np.float64)
    pos = pos[np.isfinite(pos)]; neg = neg[np.isfinite(neg)]
    npos, nneg = len(pos), len(neg)
    if npos == 0 or nneg == 0:
        return None
    allv = np.concatenate([pos, neg])
    ranks = _avg_ranks(allv)
    r_pos = ranks[:npos].sum()
    u = r_pos - npos * (npos + 1) / 2.0
    return float(u / (npos * nneg))


def iou_masks(a, b):
    """IoU of two boolean masks (same shape)."""
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


# ======================================================================
#  H1 — SYNTHETIC ground truth (ideal oracle, able to fail).
# ======================================================================
def synth_forward_scene():
    """A forward-translation scene: radial expansion from a KNOWN FOE over a
    DEPTH-VARYING background (near flows faster than far) + an INDEPENDENTLY-
    moving object (non-radial) + a view-fixed apparatus (zero flow). Returns
    (vy, vx, true_depth, foe_true, mover_mask, app_mask, bg_mask). Floats — the
    ideal oracle (E1M1 quantizes; here we prove the mechanism analytically)."""
    gh, gw = 60, 80
    foe = (48.0, 28.0)                     # (col, row), off-centre (tests estimate)
    speed = 3.0
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float64)
    dx = xx - foe[0]; dy = yy - foe[1]
    r = np.sqrt(dx * dx + dy * dy)
    # depth ramp: near (Z=2) at the bottom, far (Z=12) at the top + column tilt.
    Z = 2.0 + 10.0 * (yy / (gh - 1)) * 0.6 + 4.0 * (xx / (gw - 1))
    Z = np.clip(Z, 2.0, 14.0)
    # static forward-walk flow: radial, magnitude = speed * r / Z (near faster).
    rr = np.where(r > 1e-9, r, 1.0)
    vx = speed * dx / Z
    vy = speed * dy / Z
    # independent mover: a disk whose flow is its OWN (non-radial) motion.
    mover_mask = ((xx - 20.0) ** 2 + (yy - 45.0) ** 2) <= 6.0 ** 2
    vx[mover_mask] = 4.0                   # moving right — non-radial vs the FOE
    vy[mover_mask] = 0.0
    # view-fixed apparatus: zero flow (weapon sprite).
    app_mask = ((xx - 40.0) ** 2 + (yy - 53.0) ** 2) <= 5.0 ** 2
    vx[app_mask] = 0.0; vy[app_mask] = 0.0
    bg_mask = ~(mover_mask | app_mask)
    return vy, vx, Z, foe, mover_mask, app_mask, bg_mask


def run_h1():
    out = {}

    vy, vx, Z, foe_true, mover_mask, app_mask, bg_mask = synth_forward_scene()

    # ---- FOE estimation ----
    foe_est, foe_diag = estimate_foe(vy, vx)
    exp_dom, exp_diag = expansion_gate(vy, vx)
    foe_err = (None if foe_est is None else
               round(float(np.hypot(foe_est[0] - foe_true[0],
                                    foe_est[1] - foe_true[1])), 3))
    out["foe"] = {"true": list(foe_true),
                  "estimated": (None if foe_est is None else
                                [round(v, 2) for v in foe_est]),
                  "error_cells": foe_err, "expansion_dominant": exp_dom,
                  **exp_diag, **foe_diag}

    dec = radial_decompose(vy, vx, foe_est)
    tang = dec["tangential_mag"]; mag = dec["mag"]; valid = dec["valid"]

    # ---- (i) single-vector FAILS on parallax ----
    # Two single-global-vector baselines: 157000's dominant MODE and 155000's
    # median-over-all. On depth-varying (parallax) flow NEITHER describes the
    # field, so subtracting it leaves the near/far background as salient as the
    # mover; the mover is not separable.
    gvec = dominant_mode_gain(vy, vx)
    gmed = median_all_gain(vy, vx)
    sv_res = np.sqrt((vy - gvec[0]) ** 2 + (vx - gvec[1]) ** 2)
    md_res = np.sqrt((vy - gmed[0]) ** 2 + (vx - gmed[1]) ** 2)
    flow_cells = mag > FLOOR
    mv = mover_mask & flow_cells
    bgf = bg_mask & flow_cells
    auc_sv = auc_fast(sv_res[mv], sv_res[bgf])
    auc_md = auc_fast(md_res[mv], md_res[bgf])
    # ---- (ii) radial-consistency ISOLATES the mover ----
    auc_rad = auc_fast(tang[mv], tang[bgf])
    flagged, cut = flag_movers(tang, valid)              # movers = inconsistent
    iou_rad = iou_masks(flagged, mover_mask)
    # single-vector "flag" for the same IoU comparison (over flow cells)
    sv_cut = max(otsu_cutoff(sv_res[flow_cells]), FLOOR)
    sv_flag = flow_cells & (sv_res > sv_cut)
    iou_sv = iou_masks(sv_flag, mover_mask)
    out["mover_isolation"] = {
        "single_vector_mode": list(gvec),
        "single_vector_median": [round(v, 3) for v in gmed],
        "auc_singlevec_mode_mover_vs_bg": (None if auc_sv is None else round(auc_sv, 4)),
        "auc_singlevec_median_mover_vs_bg": (None if auc_md is None else round(auc_md, 4)),
        "auc_radial_mover_vs_bg": (None if auc_rad is None else round(auc_rad, 4)),
        "iou_singlevec_flag_vs_mover": round(iou_sv, 4),
        "iou_radial_flag_vs_mover": round(iou_rad, 4),
        "tangential_otsu_cut": round(cut, 4),
        "bg_singlevec_residual_p90": round(float(np.percentile(sv_res[bgf], 90)), 3),
        "mover_singlevec_residual_median": round(float(np.median(sv_res[mv])), 3),
    }

    # ---- (iii) recovered depth CORRELATES with known depth ----
    depth, dvalid = depth_from_motion(vy, vx, foe_est)
    # radial-consistent static cells only (NOT flagged as a mover, has flow+radius)
    consistent = dvalid & (~flagged) & bg_mask
    sp = spearman(depth[consistent], Z[consistent])
    out["depth_recovery"] = {
        "spearman_recovered_vs_true": (None if sp is None else round(sp, 4)),
        "n_consistent_cells": int(consistent.sum()),
        "true_depth_range": [round(float(Z.min()), 2), round(float(Z.max()), 2)],
    }

    # ---- (iv) apparatus stays demoted (radial) vs promoted (single-vector) ----
    # The view-fixed apparatus has ZERO flow. Radial: no flow => no defined
    # direction => never valid => never flagged (demoted, correct). Single-vector:
    # cancellation subtracts the global vector from EVERY cell, so a zero-flow
    # apparatus gets residual |gvec| = |global vector| > 0 => PROMOTED to a
    # spurious "−gvec" mover (157000's measured apparatus promotion, here on GT).
    app_cells = app_mask
    app_flagged_radial = int((flagged & app_cells).sum())
    app_sv_residual = float(np.hypot(gvec[0], gvec[1]))     # |0 − gvec| on apparatus
    app_promoted_sv = app_sv_residual > sv_cut
    out["apparatus"] = {
        "n_apparatus_cells": int(app_cells.sum()),
        "radial_flagged_as_mover": app_flagged_radial,          # expect 0
        "singlevec_residual_on_apparatus": round(app_sv_residual, 3),
        "singlevec_flag_cut": round(sv_cut, 3),
        "singlevec_promotes_apparatus": bool(app_promoted_sv),  # expect True
    }

    # ---- CONTROL: pure ROTATION (uniform-ish flow, no translation) ----
    gh, gw = vy.shape
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float64)
    cx, cy = gw / 2, gh / 2
    omega = 0.15
    rvx = -omega * (yy - cy)
    rvy = omega * (xx - cx)
    rot_dom, rot_diag = expansion_gate(rvy, rvx)
    rfoe, rfoe_diag = estimate_foe(rvy, rvx)
    out["control_rotation"] = {
        "expansion_dominant": rot_dom,                          # expect False
        **rot_diag,
        "foe_would_be_spurious": rfoe is not None and rot_dom,  # expect False
    }

    # ---- CONTROL: static scene + forward translation (NO mover) ----
    vy2, vx2, Z2, foe2, _, app2, _ = synth_forward_scene()
    vx2[mover_mask] = 3.0 * (xx[mover_mask] - foe2[0]) / Z2[mover_mask]  # radialise
    vy2[mover_mask] = 3.0 * (yy[mover_mask] - foe2[1]) / Z2[mover_mask]
    vx2[app2] = 0.0; vy2[app2] = 0.0
    foe2e, _ = estimate_foe(vy2, vx2)
    dec2 = radial_decompose(vy2, vx2, foe2e)
    flagged2, cut2 = flag_movers(dec2["tangential_mag"], dec2["valid"])
    depth2, dvalid2 = depth_from_motion(vy2, vx2, foe2e)
    cons2 = dvalid2 & (~flagged2) & (~app2)
    sp2 = spearman(depth2[cons2], Z2[cons2])
    # a REAL mover would exceed the field tangential scale; here max ~ noise floor
    tvalid = dec2["tangential_mag"][dec2["valid"]]
    out["control_static_forward"] = {
        "n_flagged_as_mover": int(flagged2.sum()),
        "max_tangential": round(float(tvalid.max()) if tvalid.size else 0.0, 4),
        "median_tangential": round(float(np.median(tvalid)) if tvalid.size else 0.0, 4),
        "depth_spearman": (None if sp2 is None else round(sp2, 4)),
        "n_consistent_cells": int(cons2.sum()),
    }

    # ---- CONTROL: independent mover + NO egomotion (plain residual flags it) ----
    vy3 = np.zeros((gh, gw)); vx3 = np.zeros((gh, gw))
    vx3[mover_mask] = 4.0
    exp3_dom, exp3_diag = expansion_gate(vy3, vx3)
    mag3 = np.sqrt(vy3 * vy3 + vx3 * vx3)
    plain_flag = mag3 > FLOOR                                   # plain residual
    out["control_mover_no_ego"] = {
        "expansion_dominant": exp3_dom,                         # expect False
        **exp3_diag,
        "plain_residual_flags_mover_iou": round(
            iou_masks(plain_flag, mover_mask), 4),               # expect high
        "radial_is_noop": exp3_dom is False,
    }
    return out


# ======================================================================
#  H2 — E1M1, GROUND-TRUTH-SCORED against the VizDoom DEPTH + labels buffers.
# ======================================================================
def _downsample_depth(depth_buf, gh=GH, gw=GW):
    """Depth buffer -> (gh,gw) float grid by area-mean. Mechanical I/O."""
    return _block_mean(np.asarray(depth_buf, np.float64), gh, gw)


def _flow_field(frames, fi, gh, gw, block, levels):
    """Block-matched flow (vy,vx) between frames fi-1,fi at grid (gh,gw). `levels`
    None => raw luma (256); else quantize to `levels` (157000's carve uses L=4).
    Mechanical: downsample_grey + the EXISTING vector_field block-matcher."""
    from domains.motion_group_world import vector_field
    g0 = downsample_grey(frames[fi - 1]["rgb"], gh, gw).astype(np.float64)
    g1 = downsample_grey(frames[fi]["rgb"], gh, gw).astype(np.float64)
    if levels is not None:
        g0 = quantize(g0.astype(np.uint8), levels).astype(np.float64)
        g1 = quantize(g1.astype(np.uint8), levels).astype(np.float64)
    vf = vector_field(g0, g1, block=block)
    vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)[:gh, :gw]
    vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)[:gh, :gw]
    return vy, vx


def _stat(xs):
    if not xs:
        return {"median": 0.0, "mean": 0.0, "n": 0}
    return {"median": round(float(np.median(xs)), 4),
            "mean": round(float(np.mean(xs)), 4),
            "p10": round(float(np.percentile(xs, 10)), 4),
            "p90": round(float(np.percentile(xs, 90)), 4),
            "frac_pos": round(float((np.asarray(xs) > 0).mean()), 3),
            "n": len(xs)}


def depth_headline_arm(frames, seq, gh, gw, block, levels):
    """DEPTH-FROM-MOTION vs the VizDoom DEPTH BUFFER for one flow config.
    Per frame: estimate the FOE, decompose, recover depth r/|flow| on
    radial-consistent cells, Spearman vs the downsampled depth buffer. Gated to
    EFFERENCE-FORWARD frames (the agent's own issued action == pure forward, the
    translation regime) AND reported over all motion frames. The buffer polarity
    is MEASURED (sign reported), never assumed."""
    sps_all, sps_fwd = [], []
    for fi in range(1, len(frames)):
        vy, vx = _flow_field(frames, fi, gh, gw, block, levels)
        mag = np.sqrt(vy * vy + vx * vx)
        if (mag > FLOOR).sum() < 8:
            continue
        foe, _ = estimate_foe(vy, vx)
        if foe is None:
            continue
        dec = radial_decompose(vy, vx, foe)
        tang = dec["tangential_mag"]; valid = dec["valid"]
        flagged, _cut = flag_movers(tang, valid)
        depth, dvalid = depth_from_motion(vy, vx, foe)
        db = _downsample_depth(frames[fi]["depth"], gh, gw)
        gt = downsample_labels(frames[fi]["labels_buf"], gh, gw)
        cons = dvalid & (~flagged) & (gt == 0)           # radial-consistent bg
        sp = spearman(depth[cons], db[cons])
        if sp is None:
            continue
        sps_all.append(sp)
        if seq[fi - 1] == [1, 0, 0]:                     # efference == pure forward
            sps_fwd.append(sp)
    return {"grid": [gw, gh], "block": block, "levels": levels,
            "all_frames": _stat(sps_all), "forward_frames": _stat(sps_fwd)}


def run_h2(frames):
    from substrate_rs import _native as native
    S = native.Substrate
    seq = _default_action_seq()

    # 157000's reused pipeline flow (L=4, down=2) for FOE + per-cell + track.
    fields, _gts = _e1m1_flow_fields(frames)
    gt_grids = [downsample_labels(f["labels_buf"], GH, GW) for f in frames]

    # ---- FOE per motion frame (always estimated; the expansion gate is the
    #      ROTATION control, not a hard gate — real mixed forward+turn flow is
    #      noisy so div>|curl| rarely fires, reported as a diagnostic count) ----
    foes = [None]
    exp_frames = 0
    fg_tang, bg_tang, fg_sv, bg_sv = [], [], [], []
    per_frame = []
    for fi in range(1, len(frames)):
        vy, vx = fields[fi]
        exp_dom, exp_diag = expansion_gate(vy, vx)
        if exp_dom:
            exp_frames += 1
        foe, foe_diag = estimate_foe(vy, vx)
        foes.append(foe)
        rec = {"frame": fi, "fwd": seq[fi - 1] == [1, 0, 0],
               "expansion_dominant": exp_dom, **exp_diag,
               "foe": (None if foe is None else [round(v, 1) for v in foe]),
               "foe_cond": foe_diag.get("cond")}
        # per-cell fg/bg residual on FORWARD frames with a FOE (mover isolation)
        if foe is not None and seq[fi - 1] == [1, 0, 0]:
            gvec = dominant_mode_gain(vy, vx)
            sv_res = np.sqrt((vy - gvec[0]) ** 2 + (vx - gvec[1]) ** 2)
            dec = radial_decompose(vy, vx, foe)
            tang = dec["tangential_mag"]; valid = dec["valid"]
            gt = gt_grids[fi]; labels = frames[fi]["labels"]
            fg_vals = _cat_values(labels, "monster") | _cat_values(labels, "item")
            fg_mask = (np.isin(gt, list(fg_vals)) if fg_vals
                       else np.zeros_like(gt, bool))
            bg_mask = (gt == 0)
            ff = fg_mask & valid; bb = bg_mask & valid
            fg_tang.extend(tang[ff].tolist()); bg_tang.extend(tang[bb].tolist())
            fg_sv.extend(sv_res[ff].tolist()); bg_sv.extend(sv_res[bb].tolist())
        per_frame.append(rec)

    foe_est = [f for f in foes if f is not None]
    foe_xs = [f[0] for f in foe_est]; foe_ys = [f[1] for f in foe_est]

    # ---- HEADLINE: depth-from-motion vs the depth buffer, across flow arms ----
    # PRIMARY = the 157000-reused pipeline (L=4, down=2). DIAGNOSTIC arms isolate
    # the flow-quality wall: raw luma (same grid) and a finer grid (down=1).
    depth_arms = {
        "reused_L4_down2": depth_headline_arm(frames, seq, GH, GW, BLOCK, LEVEL),
        "raw_luma_down2": depth_headline_arm(frames, seq, GH, GW, BLOCK, None),
        "raw_luma_down1": depth_headline_arm(frames, seq, 240, 320, 16, None),
    }

    # ---- track-level: DEPTH-AWARE (radial-projected) residual salience vs 157000 ----
    fq = quantize(_luma_stack(frames), LEVEL)
    per_frame_carve, _walls = run_value_carve(fq, GH, GW)
    tracks = [t for t in _collect_tracks(per_frame_carve) if len(t["pts"]) >= 3]
    foe_pf = foes + [None] * (len(frames) - len(foes))

    def radial_residual_track(track):
        """Depth-aware residual path: project OUT the radial component of each
        centroid step (egomotion is radial) => keep only the tangential (mover)
        motion. Background walking radially => ~flat => low salience."""
        pts = track["pts"]
        ry = [0.0]; rx = [0.0]
        for i in range(1, len(pts)):
            f = pts[i]["frame"]
            oy = pts[i]["cy"] - pts[i - 1]["cy"]
            ox = pts[i]["cx"] - pts[i - 1]["cx"]
            foe = foe_pf[f] if 0 <= f < len(foe_pf) else None
            if foe is None:
                ty, tx = oy, ox                      # no FOE => plain residual
            else:
                dx = pts[i]["cx"] - foe[0]; dy = pts[i]["cy"] - foe[1]
                rn = (dx * dx + dy * dy) ** 0.5 or 1.0
                ux, uy = dx / rn, dy / rn
                rc = ox * ux + oy * uy               # radial component (egomotion)
                tx = ox - rc * ux; ty = oy - rc * uy  # tangential residual
            ry.append(ry[-1] + ty); rx.append(rx[-1] + tx)
        return ry, rx

    def salience_singlevec(track):
        pts = track["pts"]
        cx = [p["cx"] for p in pts]; cy = [p["cy"] for p in pts]
        return max(S.shape_salience(cx), S.shape_salience(cy))

    def salience_radial(track):
        ry, rx = radial_residual_track(track)
        return max(S.shape_salience(ry), S.shape_salience(rx))

    scored = []
    for t in tracks:
        cat = _track_gt_category(t, gt_grids, frames)
        scored.append({"cat": cat,
                       "sv": float(salience_singlevec(t)),
                       "rad": float(salience_radial(t))})
    fg = [s for s in scored if s["cat"] in ("monster", "item")]
    bgt = [s for s in scored if s["cat"] == "background"]
    mon_tracks = [s for s in scored if s["cat"] == "monster"]

    def _r(a):
        return None if a is None else round(a, 4)

    return {
        "grid": [GW, GH], "down": DOWN, "block": BLOCK, "level": LEVEL,
        "n_frames": len(frames),
        "expansion_dominant_frames": exp_frames,
        "total_motion_frames": len(frames) - 1,
        "n_forward_frames": sum(1 for i in range(1, len(frames))
                                if seq[i - 1] == [1, 0, 0]),
        "foe": {"n": len(foe_est),
                "median_x": round(float(np.median(foe_xs)), 2) if foe_xs else None,
                "median_y": round(float(np.median(foe_ys)), 2) if foe_ys else None,
                "image_centre": [GW / 2, GH / 2],
                "iqr_x": (round(float(np.percentile(foe_xs, 75) -
                                np.percentile(foe_xs, 25)), 2) if foe_xs else None),
                "iqr_y": (round(float(np.percentile(foe_ys, 75) -
                                np.percentile(foe_ys, 25)), 2) if foe_ys else None)},
        "depth_from_motion": depth_arms,
        "mover_isolation_per_cell_forward": {
            "auc_radial_fg_vs_bg": _r(auc_fast(fg_tang, bg_tang)),
            "auc_singlevec_fg_vs_bg": _r(auc_fast(fg_sv, bg_sv)),
            "n_fg_cells": len(fg_tang), "n_bg_cells": len(bg_tang),
        },
        "mover_isolation_track": {
            "n_tracks": len(scored), "n_monster_tracks": len(mon_tracks),
            "auc_radial_fg_vs_bg": _r(auc_fast([s["rad"] for s in fg],
                                               [s["rad"] for s in bgt])),
            "auc_singlevec_fg_vs_bg": _r(auc_fast([s["sv"] for s in fg],
                                                  [s["sv"] for s in bgt])),
            "baseline_157000_singlevec_auc": 0.563,
        },
        "per_frame_sample": per_frame[:12],
    }


# ======================================================================
def _save_pngs(frames, out_dir):
    """Small PNG: recovered depth-from-motion vs the VizDoom depth buffer, on the
    EFFERENCE-FORWARD frame with the best per-frame depth Spearman (down=1 raw
    luma — where the flow carries signal). Mechanical rendering; small."""
    try:
        from PIL import Image
    except Exception:
        return []
    seq = _default_action_seq()
    gh, gw, block = 240, 320, 16
    best_fi, best_sp, best = 0, -2.0, None
    for fi in range(1, len(frames)):
        if seq[fi - 1] != [1, 0, 0]:
            continue
        vy, vx = _flow_field(frames, fi, gh, gw, block, None)
        if (np.sqrt(vy * vy + vx * vx) > FLOOR).sum() < 8:
            continue
        foe, _ = estimate_foe(vy, vx)
        if foe is None:
            continue
        depth, valid = depth_from_motion(vy, vx, foe)
        db = _downsample_depth(frames[fi]["depth"], gh, gw)
        dec = radial_decompose(vy, vx, foe)
        flagged, _c = flag_movers(dec["tangential_mag"], dec["valid"])
        gt = downsample_labels(frames[fi]["labels_buf"], gh, gw)
        cons = valid & (~flagged) & (gt == 0)
        sp = spearman(depth[cons], db[cons])
        if sp is not None and sp > best_sp:
            best_fi, best_sp, best = fi, sp, (depth, valid, db)
    if best is None:
        return []
    fi = best_fi
    depth, valid, db = best

    def norm(a, m):
        a = np.array(a, np.float64); a[~m] = np.nan
        lo, hi = np.nanpercentile(a, 5), np.nanpercentile(a, 95)
        z = np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)
        z = np.nan_to_num(z)
        img = (z * 255).astype(np.uint8)
        return np.stack([img, img, img], -1)

    scale = 2
    paths = []
    try:
        rec = norm(depth, valid)
        tru = norm(db, np.ones_like(db, bool))
        strip = Image.new("RGB", (gw * scale * 2 + 8, gh * scale), (20, 20, 20))
        strip.paste(Image.fromarray(rec).resize((gw * scale, gh * scale),
                    Image.NEAREST), (0, 0))
        strip.paste(Image.fromarray(tru).resize((gw * scale, gh * scale),
                    Image.NEAREST), (gw * scale + 8, 0))
        p = os.path.join(out_dir, f"depth_from_motion_f{fi}_sp{best_sp:.2f}.png")
        strip.save(p)
        paths.append(os.path.basename(p))
    except Exception:
        pass
    return paths


def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    result = {
        "block": 158000, "doom_seed": DOOM_SEED, "map": "E1M1",
        "grid": [GW, GH], "down": DOWN, "block_aperture": BLOCK, "level": LEVEL,
        "floor": FLOOR, "r_min": R_MIN, "skill": SKILL,
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
        "engine_line": prov.get("line"),
    }

    print("== H1 synthetic (FOE + radial-consistency + depth-from-magnitude) ==")
    result["H1"] = run_h1()
    h1 = result["H1"]
    print(f"  FOE: true={h1['foe']['true']} est={h1['foe']['estimated']} "
          f"err={h1['foe']['error_cells']} cells; expansion_dominant="
          f"{h1['foe']['expansion_dominant']} (div={h1['foe']['mean_div']} "
          f"|curl|={h1['foe']['mean_abs_curl']})")
    mi = h1["mover_isolation"]
    print(f"  (i)  single-vector AUC(mover>bg): mode={mi['auc_singlevec_mode_mover_vs_bg']} "
          f"median={mi['auc_singlevec_median_mover_vs_bg']} "
          f"IoU={mi['iou_singlevec_flag_vs_mover']}  (FAILS on parallax)")
    print(f"  (ii) RADIAL      AUC(mover>bg) = {mi['auc_radial_mover_vs_bg']} "
          f"IoU={mi['iou_radial_flag_vs_mover']}  (ISOLATES the mover)")
    dr = h1["depth_recovery"]
    print(f"  (iii) depth Spearman(recovered,true) = {dr['spearman_recovered_vs_true']} "
          f"(n={dr['n_consistent_cells']}, Z {dr['true_depth_range']})")
    ap = h1["apparatus"]
    print(f"  (iv) apparatus: radial flags {ap['radial_flagged_as_mover']}/"
          f"{ap['n_apparatus_cells']} (demoted); single-vector residual "
          f"{ap['singlevec_residual_on_apparatus']} > cut {ap['singlevec_flag_cut']} "
          f"=> promotes={ap['singlevec_promotes_apparatus']}")
    print(f"  control rotation: expansion_dominant="
          f"{h1['control_rotation']['expansion_dominant']} "
          f"(div={h1['control_rotation']['mean_div']} "
          f"|curl|={h1['control_rotation']['mean_abs_curl']})")
    print(f"  control static+forward: flagged={h1['control_static_forward']['n_flagged_as_mover']} "
          f"depth_sp={h1['control_static_forward']['depth_spearman']}")
    print(f"  control mover-no-ego: expansion_dominant="
          f"{h1['control_mover_no_ego']['expansion_dominant']} "
          f"plain IoU={h1['control_mover_no_ego']['plain_residual_flags_mover_iou']}")

    print("== H2 E1M1 (real WAD, 157000 walk/seed/grid) ==")
    frames = capture_e1m1()
    if not frames:
        result["H2_skipped"] = "vizdoom or DOOM.WAD absent"
        print("  SKIPPED:", result["H2_skipped"])
    else:
        result["H2_e1m1_frames"] = len(frames)
        h2 = run_h2(frames)
        result["H2"] = h2
        print(f"  frames={h2['n_frames']} forward_frames={h2['n_forward_frames']} "
              f"expansion_dominant_frames={h2['expansion_dominant_frames']}/"
              f"{h2['total_motion_frames']} (mixed forward+turn walk => noisy flow)")
        print(f"  FOE median=({h2['foe']['median_x']},{h2['foe']['median_y']}) "
              f"centre={h2['foe']['image_centre']} IQR=({h2['foe']['iqr_x']},"
              f"{h2['foe']['iqr_y']})  (heading ~ image centre)")
        print("  HEADLINE depth-from-motion vs DEPTH BUFFER (Spearman, forward frames):")
        for name, arm in h2["depth_from_motion"].items():
            ff = arm["forward_frames"]
            print(f"    {name:16s} grid={arm['grid']} L={arm['levels']}: "
                  f"median={ff.get('median')} mean={ff.get('mean')} "
                  f"frac>0={ff.get('frac_pos')} (n={ff.get('n')})")
        pc = h2["mover_isolation_per_cell_forward"]
        print(f"  per-cell fg-vs-bg AUC (forward): RADIAL={pc['auc_radial_fg_vs_bg']} "
              f"single-vector={pc['auc_singlevec_fg_vs_bg']} "
              f"(fg={pc['n_fg_cells']} bg={pc['n_bg_cells']} cells)")
        tk = h2["mover_isolation_track"]
        print(f"  track fg-vs-bg AUC: RADIAL={tk['auc_radial_fg_vs_bg']} "
              f"single-vector={tk['auc_singlevec_fg_vs_bg']} "
              f"(157000 baseline={tk['baseline_157000_singlevec_auc']}); "
              f"monster tracks={tk['n_monster_tracks']} (0 => sub-pixel DEGRADE)")
        img_dir = os.path.join(ROOT, "results", "depth_from_motion_imgs")
        os.makedirs(img_dir, exist_ok=True)
        result["pngs"] = _save_pngs(frames, img_dir)

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "depth_from_motion.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
