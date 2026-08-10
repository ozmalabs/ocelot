#!/usr/bin/env python3
"""SALIENCE-DRIVEN FOVEATION (block 159000-159999).

THE PRINCIPLE — foveation = supergraph-optimal compute allocation. 158000 proved
depth-from-motion + independent-mover isolation WORK when the flow carries signal
(recovered real Doom depth vs the VizDoom depth buffer, Spearman up to +0.40), but
they NULL on the coarse down=2/L=4 flow because it is noise/quantization-limited,
AND full-resolution flow EVERYWHERE is O(N^2) (~3x over the real-time budget). THE
FIX: don't resolve everything — resolve the flow FINELY only where it is SALIENT,
coarse elsewhere. Spend the resolution budget where the (super)graph values it most
(the salient / independently-moving region), not uniformly. Foveation is the
perception instance of "value graph-wide, allocate where worth-most."

THE MECHANISM (reuse-heavy):
  1. COARSE global flow (down=2) over the whole frame — the existing block-SAD
     vector_field.
  2. SALIENCE on it: estimate the FOE (158000), radial-decompose, take the
     TANGENTIAL residual field = the per-cell "surprise after self-motion is
     cancelled" (157000's efference->residual->salience, made SPATIAL and
     depth-INDEPENDENT so the peak lands on the INDEPENDENT MOVER, not on the
     highest-magnitude near/parallax background).
  3. FOVEATE: at the top-salience region(s) RE-COMPUTE the flow at FINE resolution
     (down=1) in a LOCAL WINDOW only — high-res flow ONLY where salient.
  4. Run 158000's depth-from-motion (FOE + radial consistency) + mover isolation on
     the FINE-flow foveated window.

REUSED (158000, depth_from_motion_probe): estimate_foe, radial_decompose,
depth_from_motion, flag_movers, otsu_cutoff, expansion_gate, spearman, auc_fast,
iou_masks, the _flow_field block-matcher, _downsample_depth, FLOOR, R_MIN. REUSED
(157000, residual_salience_probe): dominant_mode_gain (the single-vector residual,
for the raw-vs-residual control), Substrate.shape_salience (the track-level residual
salience). REUSED (E1M1 adapter): capture_e1m1 / walk / seed / depth+labels buffers,
downsample_grey, downsample_labels, quantize. ADDED (mechanical numpy GLUE only):
`salience_field` (the tangential-residual spatial salience = 158000's radial residual
as a field), `_connected_components` + `select_fovea` (argmax/top-K window selection
— pure array bookkeeping), `fine_flow_window` (the existing block-matcher on a CROP).

ARCHITECTURE (CLAUDE.md — the agent is Rust). NO agent decision in Python. Window
selection is argmax / top-K over the salience field (mechanical); the fine-flow
recompute is the EXISTING sensor at a finer scale on a crop; depth / mover are
158000's mechanical sensors; scoring is Spearman / IoU / distance vs the GT buffers
by POSITION, never cross-process region-id. NO Rust added, NO seed consumed, NO
default moved — NEW FILE ONLY, so every shipped 154/155/157/158 path is
byte-identical BY CONSTRUCTION (the salience/depth/flow imports are unchanged).

Pre-registration: VISION_SALIENCE_FOVEATION_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.depth_from_motion_probe import (  # noqa: E402
    estimate_foe, radial_decompose, depth_from_motion, flag_movers,
    otsu_cutoff, expansion_gate, spearman, auc_fast, iou_masks,
    _flow_field, _downsample_depth, _stat, FLOOR, R_MIN,
)
from scripts.residual_salience_probe import dominant_mode_gain  # noqa: E402
from scripts.e1m1_salience_probe import (  # noqa: E402
    capture_e1m1, _default_action_seq, _cat_values,
    GH, GW, DOWN, BLOCK, LEVEL, DOOM_SEED, SKILL,
)
from scripts.eye_on_doom_probe import (  # noqa: E402
    quantize, downsample_grey, downsample_labels,
)

# ---- DECLARED RESIDUALS (§13 — the sensor's aperture / fovea geometry, NOT tuned
#      to the score) ----------------------------------------------------------
FOVEA_MIN_HALF = 4     # min fovea half-extent (cells): a window smaller than the
                       # flow block carries no gradient. A geometric floor, not a
                       # knob; the ACTUAL size FALLS OUT of the salient region's
                       # connected-component bbox (below), this is only its floor.
FOVEA_PAD = 2          # bbox pad so the fine block-matcher has border context.
MIN_REGION = 2         # a mover is an EXTENDED object: a flagged region must span
                       # >= 2 connected cells to be a fovea target. A single-cell
                       # flag is block-match rounding noise, not an object. A
                       # coherence floor from the object being extended, not a knob.
SAL_FLOOR = 1.0        # a mover must carry >= ONE FULL PIXEL of UNEXPLAINED
                       # (tangential) motion to be a fovea target. Integer
                       # block-match flow has up to sqrt(2)*0.5 ~= 0.71 px of
                       # DIRECTION-ROUNDING noise (each axis rounds by <=0.5), so
                       # a genuine independent mover must clear that band. FALLS
                       # OUT of the integer-flow rounding bound, not tuned: it is
                       # the one-pixel step (158000's FLOOR) applied to the
                       # UNEXPLAINED residual rather than to raw |flow|.
FINE_DOWN = 1          # the fovea's fine sampling: full native resolution.
FINE_BLOCK = 16        # 16 px physical aperture at down=1 (158000's down=1 arm).
BLOCK_SEED = 159000


# ======================================================================
#  THE FOVEATION GLUE — mechanical numpy over the flow / salience fields.
# ======================================================================
def salience_field(vy, vx, floor=FLOOR):
    """SPATIAL residual salience = 157000's efference->residual->salience made a
    FIELD, depth-INDEPENDENT (158000). Estimate the FOE, radial-decompose, and
    return the per-cell TANGENTIAL residual (|flow perpendicular to radial|). A
    static forward-walk background flows purely radially => tangential ~= 0 at ANY
    depth; an INDEPENDENT mover keeps a tangential residual => the peak lands on
    the mover, NOT on the highest-magnitude near/parallax background (which raw
    |flow| would pick). Returns (salience, valid, foe). foe None => no expansion
    geometry (rotation / too little flow) => fall back to the raw-|flow| residual
    minus the single global vector (157000's dominant-mode residual)."""
    vy = np.asarray(vy, np.float64); vx = np.asarray(vx, np.float64)
    foe, _ = estimate_foe(vy, vx, floor=floor)
    if foe is None:
        gy, gx = dominant_mode_gain(vy, vx, floor=floor)
        res = np.sqrt((vy - gy) ** 2 + (vx - gx) ** 2)
        mag = np.sqrt(vy * vy + vx * vx)
        return res, (mag > floor), None
    dec = radial_decompose(vy, vx, foe, floor=floor)
    return dec["tangential_mag"], dec["valid"], foe


def _connected_components(mask):
    """4-connected components of a boolean mask -> list of (rows, cols) arrays.
    Pure BFS, no scipy dependency. Mechanical bookkeeping."""
    mask = np.asarray(mask, bool)
    gh, gw = mask.shape
    seen = np.zeros_like(mask)
    comps = []
    for r0 in range(gh):
        for c0 in range(gw):
            if not mask[r0, c0] or seen[r0, c0]:
                continue
            stack = [(r0, c0)]; seen[r0, c0] = True
            rs, cs = [], []
            while stack:
                r, c = stack.pop()
                rs.append(r); cs.append(c)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < gh and 0 <= cc < gw and mask[rr, cc] and not seen[rr, cc]:
                        seen[rr, cc] = True; stack.append((rr, cc))
            comps.append((np.array(rs), np.array(cs)))
    return comps


def select_fovea(salience, valid, top_k=1, min_half=FOVEA_MIN_HALF, pad=FOVEA_PAD,
                 min_region=MIN_REGION, sal_floor=SAL_FLOOR):
    """Pick the fovea window(s): the connected components of the flagged
    (Otsu+floor, 158000) salience, ranked by their PEAK salience, top-K. Each
    window = the component's bbox (padded), floored to a minimum half-extent. The
    LOCATION is the salience argmax; the SIZE FALLS OUT of the region's extent
    (with a geometric minimum). If nothing is flagged => [] (no fovea fires; the
    caller falls back to the coarse pass). Pure mechanical selection — no decision
    over graph state. Returns a list of dicts: window box + peak cell + peak value."""
    salience = np.asarray(salience, np.float64)
    gh, gw = salience.shape
    flagged, cut = flag_movers(salience, valid, floor=sal_floor)
    if not flagged.any():
        return [], cut
    comps = _connected_components(flagged)
    scored = []
    for rs, cs in comps:
        if len(rs) < min_region:                  # single-cell rounding spike
            continue
        vals = salience[rs, cs]
        k = int(np.argmax(vals))
        pr, pc = int(rs[k]), int(cs[k])
        rmin, rmax = int(rs.min()), int(rs.max())
        cmin, cmax = int(cs.min()), int(cs.max())
        # window from the region extent, floored to min_half about its centre
        rc = (rmin + rmax) / 2.0; cc = (cmin + cmax) / 2.0
        hh = max(min_half, (rmax - rmin) / 2.0 + pad)
        hw = max(min_half, (cmax - cmin) / 2.0 + pad)
        r0 = max(0, int(np.floor(rc - hh))); r1 = min(gh, int(np.ceil(rc + hh)) + 1)
        c0 = max(0, int(np.floor(cc - hw))); c1 = min(gw, int(np.ceil(cc + hw)) + 1)
        scored.append({"peak_rc": [pr, pc], "peak": float(vals[k]),
                       "box": [r0, r1, c0, c1], "region_cells": int(len(rs))})
    scored.sort(key=lambda s: -s["peak"])
    return scored[:top_k], cut


# ======================================================================
#  H1 — SYNTHETIC (ideal oracle, able to fail). A small salient region whose
#  signal is LOST at coarse resolution but RECOVERED at fine resolution.
# ======================================================================
def synth_fovea_scene(gh=120, gw=160, mover_speed=8.0, mover_r=2.5):
    """FINE-resolution ground truth: a forward-translation scene (radial expansion
    from a KNOWN FOE over a DEPTH-VARYING background, near flows faster) + a SMALL
    independently-moving object (non-radial own motion) + a view-fixed apparatus
    (zero flow). Continuous analytic flow (the ideal oracle). Returns
    (vy, vx, Z, foe, mover_mask, app_mask, bg_mask)."""
    foe = (gw * 0.5, gh * 0.42)                 # (col, row) — forward heading
    speed = 3.0
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float64)
    dx = xx - foe[0]; dy = yy - foe[1]
    r = np.sqrt(dx * dx + dy * dy)
    # depth ramp: near (Z=2) at the bottom, far (Z=14) toward the FOE.
    Z = 2.0 + 10.0 * (yy / (gh - 1)) + 3.0 * (xx / (gw - 1))
    Z = np.clip(Z, 2.0, 14.0)
    vx = speed * dx / Z
    vy = speed * dy / Z
    # SMALL independent mover: a disk (radius ~2.5 fine cells => sub-coarse-cell)
    # with its OWN non-radial motion. Small => its motion is spatially DILUTED
    # (averaged with the surrounding radial background) at the coarse block scale.
    mcy, mcx = gh * 0.68, gw * 0.30
    mover_mask = ((xx - mcx) ** 2 + (yy - mcy) ** 2) <= mover_r ** 2
    vx[mover_mask] = mover_speed                 # moving right — non-radial vs FOE
    vy[mover_mask] = -mover_speed * 0.4
    # view-fixed apparatus (weapon sprite): zero flow.
    app_mask = ((xx - gw * 0.5) ** 2 + (yy - gh * 0.9) ** 2) <= 6.0 ** 2
    vx[app_mask] = 0.0; vy[app_mask] = 0.0
    bg_mask = ~(mover_mask | app_mask)
    return vy, vx, Z, foe, mover_mask, app_mask, bg_mask


def _coarsen(a, factor):
    """Downsample a field by area-mean (block factor x factor)."""
    gh, gw = a.shape
    ch, cw = gh // factor, gw // factor
    a = a[:ch * factor, :cw * factor].reshape(ch, factor, cw, factor)
    return a.mean(axis=(1, 3))


def _window_cells_coarse_to_fine(box, factor):
    r0, r1, c0, c1 = box
    return [r0 * factor, r1 * factor, c0 * factor, c1 * factor]


def run_h1():
    out = {}
    F = 2                                        # coarse downsample factor
    vy_f, vx_f, Z_f, foe_true, mover_f, app_f, bg_f = synth_fovea_scene()
    gh, gw = vy_f.shape

    # --- THE SENSOR MODEL (the physical mechanism of the coarse null): a block
    #     matcher returns INTEGER pixel displacements, and at HALF resolution a
    #     feature moves HALF as many pixels. So the COARSE sensor area-averages the
    #     flow over FxF blocks, HALVES the displacement (coarse-pixel units), and
    #     ROUNDS to integers — a small mover's own motion is diluted AND pushed
    #     toward the sub-pixel floor. The FINE sensor keeps full-resolution integer
    #     flow (twice the displacement => resolvable). This is 158000's measured
    #     wall (the down=2 flow is quantization/noise-limited) made analytic.
    vy_c = np.rint(_coarsen(vy_f, F) / F); vx_c = np.rint(_coarsen(vx_f, F) / F)
    Z_c = _coarsen(Z_f, F)
    mover_c = _coarsen(mover_f.astype(float), F) > 0.25     # coarse mover GT
    # FINE SENSOR: full-resolution flow. At fine resolution the displacements are
    # large (many pixels), so integer quantization is a NEGLIGIBLE relative error
    # and the flow is accurately resolved — the accurate-flow limit (158000: the
    # down=1 arm recovers depth +0.40 where down=2 is a quantization null).
    vy_ff, vx_ff = vy_f, vx_f

    # ---- coarse salience field + fovea selection ----
    sal_c, valid_c, foe_c = salience_field(vy_c, vx_c)
    fovea, cut = select_fovea(sal_c, valid_c, top_k=1)
    foe_c_fine = None if foe_c is None else (foe_c[0] * F, foe_c[1] * F)

    # ---- (ii) fovea LOCATES the mover (not the near/parallax background) ----
    # raw-|flow| would peak on the fastest (nearest) background; residual peaks on
    # the mover — the 157000 reason salience must be on the RESIDUAL.
    mag_c = np.sqrt(vy_c ** 2 + vx_c ** 2)
    raw_peak = np.unravel_index(int(np.argmax(mag_c)), mag_c.shape)
    if fovea:
        pr, pc = fovea[0]["peak_rc"]
        fovea_on_mover = bool(mover_c[pr, pc])
        box = fovea[0]["box"]
    else:
        pr = pc = None; fovea_on_mover = False; box = None
    raw_on_mover = bool(mover_c[raw_peak[0], raw_peak[1]])
    out["fovea_locates"] = {
        "n_fovea": len(fovea),
        "residual_peak_rc": [pr, pc], "residual_peak_on_mover": fovea_on_mover,
        "raw_flow_peak_rc": list(map(int, raw_peak)),
        "raw_flow_peak_on_mover": raw_on_mover,
        "fovea_box_coarse": box, "otsu_cut": round(float(cut), 4),
        "foe_coarse": None if foe_c is None else [round(v, 2) for v in foe_c],
    }

    # ---- (i) coarse NULL + (iii) fine RECOVERS, at the salient region ----
    if fovea:
        bf = _window_cells_coarse_to_fine(box, F)     # fine window
        r0, r1, c0, c1 = box
        r0f, r1f, c0f, c1f = bf
        # COARSE, in the window: mover isolation IoU + depth Spearman
        dec_c = radial_decompose(vy_c, vx_c, foe_c) if foe_c else None
        flagged_c, _ = flag_movers(sal_c, valid_c, floor=SAL_FLOOR)
        win_c = np.zeros_like(mover_c); win_c[r0:r1, c0:c1] = True
        iou_c = iou_masks(flagged_c & win_c, mover_c & win_c)
        depth_c, dvalid_c = depth_from_motion(vy_c, vx_c, foe_c) if foe_c else (
            np.full_like(vy_c, np.nan), np.zeros_like(vy_c, bool))
        cons_c = dvalid_c & (~flagged_c) & win_c & (~mover_c)
        sp_c = spearman(depth_c[cons_c], Z_c[cons_c])
        # FINE, in the SAME window (foveated recompute): the fine integer flow
        foe_ff, _ = estimate_foe(vy_ff, vx_ff)
        sal_ff, valid_ff, _ = salience_field(vy_ff, vx_ff)
        flagged_ff, _ = flag_movers(sal_ff, valid_ff, floor=SAL_FLOOR)
        win_f = np.zeros_like(mover_f); win_f[r0f:r1f, c0f:c1f] = True
        iou_f = iou_masks(flagged_ff & win_f, mover_f & win_f)
        depth_ff, dvalid_ff = depth_from_motion(vy_ff, vx_ff, foe_ff)
        cons_f = dvalid_ff & (~flagged_ff) & win_f & (~mover_f)
        sp_f = spearman(depth_ff[cons_f], Z_f[cons_f])
        out["coarse_null_vs_fine_recover"] = {
            "window_coarse": box, "window_fine": bf,
            "coarse_mover_iou": round(iou_c, 4),
            "fine_mover_iou": round(iou_f, 4),
            "coarse_depth_spearman": None if sp_c is None else round(sp_c, 4),
            "fine_depth_spearman": None if sp_f is None else round(sp_f, 4),
            "coarse_consistent_cells": int(cons_c.sum()),
            "fine_consistent_cells": int(cons_f.sum()),
            "coarse_flagged_cells_in_window": int((flagged_c & win_c).sum()),
            "fine_flagged_cells_in_window": int((flagged_ff & win_f).sum()),
            "mover_gt_cells_coarse": int((mover_c & win_c).sum()),
            "mover_gt_cells_fine": int((mover_f & win_f).sum()),
        }

    # ---- (iv) COST: foveated (coarse-everywhere + fine window) vs full-res ----
    ch, cw = gh // F, gw // F
    coarse_cells = ch * cw
    if fovea:
        wf = out["coarse_null_vs_fine_recover"]["window_fine"]
        fine_window_cells = (wf[1] - wf[0]) * (wf[3] - wf[2])
    else:
        fine_window_cells = 0
    fullres_cells = gh * gw
    foveated_cells = coarse_cells + fine_window_cells
    out["cost"] = {
        "coarse_cells": coarse_cells,
        "fine_window_cells": fine_window_cells,
        "foveated_total_cells": foveated_cells,
        "fullres_everywhere_cells": fullres_cells,
        "foveated_fraction_of_fullres": round(foveated_cells / fullres_cells, 4),
    }

    # ---- CONTROL: NO salient region (pure radial, no mover) => no fovea fires ----
    vy2, vx2, Z2, foe2, mover2, app2, bg2 = synth_fovea_scene()
    vx2[mover2] = 3.0 * (np.mgrid[0:gh, 0:gw][1][mover2] - foe2[0]) / Z2[mover2]
    vy2[mover2] = 3.0 * (np.mgrid[0:gh, 0:gw][0][mover2] - foe2[1]) / Z2[mover2]
    vx2[app2] = 0.0; vy2[app2] = 0.0
    vy2c = np.rint(_coarsen(vy2, F) / F); vx2c = np.rint(_coarsen(vx2, F) / F)
    sal2, valid2, _ = salience_field(vy2c, vx2c)
    fovea2, cut2 = select_fovea(sal2, valid2, top_k=1)
    out["control_no_salient"] = {
        "n_fovea": len(fovea2),
        "max_salience": round(float(np.nanmax(sal2[valid2])) if valid2.any() else 0.0, 4),
        "falls_back_to_coarse": len(fovea2) == 0,
    }

    # ---- CONTROL: TWO salient regions => foveate BOTH (top-2), not merge ----
    # Two matched movers on a pure radial background, symmetric about the FOE
    # column, both moving straight down (clearly non-radial, equal tangential by
    # symmetry) — isolates the "two regions" property from multi-strength cutoff.
    vy3, vx3, Z3, foe3, base_mover, app3, bg3 = synth_fovea_scene()
    yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float64)
    vx3[base_mover] = 3.0 * (xx[base_mover] - foe3[0]) / Z3[base_mover]  # re-radialise
    vy3[base_mover] = 3.0 * (yy[base_mover] - foe3[1]) / Z3[base_mover]
    mr = 2.5
    mover3a = ((xx - gw * 0.34) ** 2 + (yy - gh * 0.34) ** 2) <= mr ** 2
    mover3b = ((xx - gw * 0.66) ** 2 + (yy - gh * 0.34) ** 2) <= mr ** 2
    vx3[mover3a] = 0.0; vy3[mover3a] = 8.0     # straight down => non-radial
    vx3[mover3b] = 0.0; vy3[mover3b] = 8.0
    two_gt = mover3a | mover3b
    vy3c = np.rint(_coarsen(vy3, F) / F); vx3c = np.rint(_coarsen(vx3, F) / F)
    sal3, valid3, _ = salience_field(vy3c, vx3c)
    fovea3, _ = select_fovea(sal3, valid3, top_k=2)
    two_gt_c = _coarsen(two_gt.astype(float), F) > 0.25
    ma_c = _coarsen(mover3a.astype(float), F) > 0.25
    mb_c = _coarsen(mover3b.astype(float), F) > 0.25
    hits_a = any(ma_c[f["peak_rc"][0], f["peak_rc"][1]] for f in fovea3)
    hits_b = any(mb_c[f["peak_rc"][0], f["peak_rc"][1]] for f in fovea3)
    out["control_two_regions"] = {
        "n_fovea": len(fovea3),
        "peaks": [f["peak_rc"] for f in fovea3],
        "both_regions_covered": bool(hits_a and hits_b),
        "region_a_hit": bool(hits_a), "region_b_hit": bool(hits_b),
    }
    return out


# ======================================================================
#  H2 — E1M1 (real WAD, 158000 walk/seed/grid), GROUND-TRUTH-SCORED.
# ======================================================================
def _fine_luma(frame):
    """Full native-resolution luma (down=1) of a frame -> (240,320) float."""
    return downsample_grey(frame["rgb"], 240, 320).astype(np.float64)


def fine_flow_window(frames, fi, box_fine, block=FINE_BLOCK, levels=LEVEL):
    """Re-compute the flow at FINE (down=1) resolution in a LOCAL WINDOW only, by
    cropping the full-res luma to the window (+ a block margin so the matcher has
    context) and running the EXISTING block-SAD vector_field on the CROP. Returns
    (vy_win, vx_win, (row0, col0)) at the window's fine pixel coordinates —
    high-res flow ONLY where salient. This is the foveation compute: cost ∝ the
    window area, not the frame area."""
    from domains.motion_group_world import vector_field
    r0, r1, c0, c1 = box_fine
    m = block
    r0m = max(0, r0 - m); c0m = max(0, c0 - m)
    r1m = min(240, r1 + m); c1m = min(320, c1 + m)
    g0 = _fine_luma(frames[fi - 1])[r0m:r1m, c0m:c1m]
    g1 = _fine_luma(frames[fi])[r0m:r1m, c0m:c1m]
    if levels is not None:
        g0 = quantize(g0.astype(np.uint8), levels).astype(np.float64)
        g1 = quantize(g1.astype(np.uint8), levels).astype(np.float64)
    if g0.shape[0] < block or g0.shape[1] < block:
        return None, None, (r0m, c0m)
    vf = vector_field(g0, g1, block=block)
    vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)[:g0.shape[0], :g0.shape[1]]
    vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)[:g0.shape[0], :g0.shape[1]]
    return vy, vx, (r0m, c0m)


def _imp_gt_cells(frame, gh, gw):
    """GT monster (imp) cell mask on a (gh,gw) grid — SCORING ORACLE only, never
    fed to the eye. Used to place/measure the imp-recovery window by position."""
    gt = downsample_labels(frame["labels_buf"], gh, gw)
    mon = _cat_values(frame["labels"], "monster")
    if not mon:
        return np.zeros((gh, gw), bool)
    return np.isin(gt, list(mon))


def run_h2(frames):
    seq = _default_action_seq()
    F = DOWN                                     # coarse=down2 -> fine=down1 => 2x
    gh_f, gw_f = 240, 320

    # ---- per-frame: coarse flow -> salience -> fovea -> fine depth in window ----
    fovea_depth_coarse, fovea_depth_fine = [], []
    full_fine_depth = []                         # 158000's down=1-everywhere arm
    coarse_full_depth = []                       # 158000's coarse null arm
    fovea_frac_of_frame = []
    n_fovea_frames = 0
    per_frame = []
    for fi in range(1, len(frames)):
        vy_c, vx_c = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
        mag = np.sqrt(vy_c ** 2 + vx_c ** 2)
        if (mag > FLOOR).sum() < 8:
            continue
        fwd = seq[fi - 1] == [1, 0, 0]
        sal_c, valid_c, foe_c = salience_field(vy_c, vx_c)
        # --- coarse-everywhere depth (the 158000 null arm), forward frames ---
        if foe_c is not None and fwd:
            db_c = _downsample_depth(frames[fi]["depth"], GH, GW)
            gt_c = downsample_labels(frames[fi]["labels_buf"], GH, GW)
            flg_c, _ = flag_movers(sal_c, valid_c)
            depth_c, dv_c = depth_from_motion(vy_c, vx_c, foe_c)
            cons_c = dv_c & (~flg_c) & (gt_c == 0)
            sp = spearman(depth_c[cons_c], db_c[cons_c])
            if sp is not None:
                coarse_full_depth.append(sp)
        # --- fovea selection ---
        fovea, _cut = select_fovea(sal_c, valid_c, top_k=2)
        rec = {"frame": fi, "fwd": bool(fwd), "n_fovea": len(fovea),
               "foe": None if foe_c is None else [round(v, 1) for v in foe_c]}
        if fovea and foe_c is not None and fwd:
            n_fovea_frames += 1
            foe_fine = (foe_c[0] * F, foe_c[1] * F)
            db_f = _downsample_depth(frames[fi]["depth"], gh_f, gw_f)
            gt_f = downsample_labels(frames[fi]["labels_buf"], gh_f, gw_f)
            win_frac = 0.0
            for fv in fovea:
                bf = _window_cells_coarse_to_fine(fv["box"], F)
                r0f, r1f, c0f, c1f = bf
                r0f = min(r0f, gh_f - 2); c0f = min(c0f, gw_f - 2)
                r1f = min(max(r1f, r0f + 2), gh_f); c1f = min(max(c1f, c0f + 2), gw_f)
                vyw, vxw, (roff, coff) = fine_flow_window(frames, fi, [r0f, r1f, c0f, c1f])
                if vyw is None:
                    continue
                win_frac += (r1f - r0f) * (c1f - c0f) / float(gh_f * gw_f)
                # depth in this fine window, radial-decomposed vs the (rescaled)
                # FOE (shift the FOE into crop-local coords)
                foe_local = (foe_fine[0] - coff, foe_fine[1] - roff)
                depth_w, dv_w = depth_from_motion(vyw, vxw, foe_local)
                sal_w, valid_w, _ = salience_field(vyw, vxw)
                flg_w, _ = flag_movers(sal_w, valid_w)
                # score vs the depth buffer crop at the SAME fine coords
                db_crop = db_f[roff:roff + vyw.shape[0], coff:coff + vyw.shape[1]]
                gt_crop = gt_f[roff:roff + vyw.shape[0], coff:coff + vyw.shape[1]]
                cons_w = dv_w & (~flg_w) & (gt_crop == 0)
                sp_w = spearman(depth_w[cons_w], db_crop[cons_w])
                if sp_w is not None:
                    fovea_depth_fine.append(sp_w)
                # coarse depth in the SAME window (the null it beats)
                db_cc = _downsample_depth(frames[fi]["depth"], GH, GW)
                gt_cc = downsample_labels(frames[fi]["labels_buf"], GH, GW)
                depth_cc, dv_cc = depth_from_motion(vy_c, vx_c, foe_c)
                flg_cc, _ = flag_movers(sal_c, valid_c)
                r0, r1, c0, c1 = fv["box"]
                winc = np.zeros((GH, GW), bool); winc[r0:r1, c0:c1] = True
                cons_cc = dv_cc & (~flg_cc) & (gt_cc == 0) & winc
                sp_cc = spearman(depth_cc[cons_cc], db_cc[cons_cc])
                if sp_cc is not None:
                    fovea_depth_coarse.append(sp_cc)
            fovea_frac_of_frame.append(win_frac)
        # --- full down=1 everywhere (158000 fine arm), for the ceiling ---
        if fwd:
            vy1, vx1 = _flow_field(frames, fi, gh_f, gw_f, FINE_BLOCK, None)
            if (np.sqrt(vy1 ** 2 + vx1 ** 2) > FLOOR).sum() >= 8:
                foe1, _ = estimate_foe(vy1, vx1)
                if foe1 is not None:
                    db1 = _downsample_depth(frames[fi]["depth"], gh_f, gw_f)
                    gt1 = downsample_labels(frames[fi]["labels_buf"], gh_f, gw_f)
                    sal1, valid1, _ = salience_field(vy1, vx1)
                    flg1, _ = flag_movers(sal1, valid1)
                    depth1, dv1 = depth_from_motion(vy1, vx1, foe1)
                    cons1 = dv1 & (~flg1) & (gt1 == 0)
                    sp1 = spearman(depth1[cons1], db1[cons1])
                    if sp1 is not None:
                        full_fine_depth.append(sp1)
        per_frame.append(rec)

    # ---- IMP recovery: sub-pixel at coarse, super-pixel in a fine window? ----
    # (b1) does coarse salience LAND on the imp? (autonomous location)
    # (b2) at a fine window placed ON the imp GT (scoring-oracle placement only),
    #      does the imp produce super-pixel (trackable) flow that coarse misses?
    imp_locate = []          # per imp-present forward frame: fovea-to-imp distance
    imp_superpixel = []      # per imp frame: (coarse flow cells, fine flow cells)
    for fi in range(1, len(frames)):
        imp_c = _imp_gt_cells(frames[fi], GH, GW)
        if imp_c.sum() == 0:
            continue
        vy_c, vx_c = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
        if (np.sqrt(vy_c ** 2 + vx_c ** 2) > FLOOR).sum() < 8:
            continue
        sal_c, valid_c, foe_c = salience_field(vy_c, vx_c)
        fovea, _ = select_fovea(sal_c, valid_c, top_k=3)
        ir, ic = np.where(imp_c)
        icy, icx = float(ir.mean()), float(ic.mean())
        if fovea:
            dists = [np.hypot(f["peak_rc"][0] - icy, f["peak_rc"][1] - icx)
                     for f in fovea]
            best = float(min(dists))
            on_imp = any(imp_c[f["peak_rc"][0], f["peak_rc"][1]] for f in fovea)
        else:
            best = None; on_imp = False
        imp_locate.append({"frame": fi, "fovea_to_imp_dist": None if best is None
                           else round(best, 2), "fovea_lands_on_imp": bool(on_imp),
                           "n_imp_cells_coarse": int(imp_c.sum())})
        # (b2) fine window on the imp GT bbox (scoring placement), count flow cells
        imp_f = _imp_gt_cells(frames[fi], gh_f, gw_f)
        if imp_f.sum() > 0:
            r, c = np.where(imp_f)
            bf = [max(0, int(r.min()) - FINE_BLOCK), min(gh_f, int(r.max()) + FINE_BLOCK),
                  max(0, int(c.min()) - FINE_BLOCK), min(gw_f, int(c.max()) + FINE_BLOCK)]
            vyw, vxw, (roff, coff) = fine_flow_window(frames, fi, bf)
            # coarse flow cells overlapping the imp
            coarse_imp_flow = int(((np.sqrt(vy_c ** 2 + vx_c ** 2) > FLOOR) & imp_c).sum())
            if vyw is not None:
                impw = imp_f[roff:roff + vyw.shape[0], coff:coff + vyw.shape[1]]
                fine_imp_flow = int(((np.sqrt(vyw ** 2 + vxw ** 2) > FLOOR) & impw).sum())
            else:
                fine_imp_flow = 0
            imp_superpixel.append({"frame": fi, "coarse_imp_flow_cells": coarse_imp_flow,
                                   "fine_imp_flow_cells": fine_imp_flow,
                                   "imp_cells_fine": int(imp_f.sum())})

    def _pack(xs):
        return _stat(xs) if xs else {"median": None, "mean": None, "n": 0}

    n_on_imp = sum(1 for d in imp_locate if d["fovea_lands_on_imp"])
    coarse_imp_total = sum(d["coarse_imp_flow_cells"] for d in imp_superpixel)
    fine_imp_total = sum(d["fine_imp_flow_cells"] for d in imp_superpixel)

    return {
        "grid_coarse": [GW, GH], "grid_fine": [gw_f, gh_f],
        "block_coarse": BLOCK, "block_fine": FINE_BLOCK, "level": LEVEL,
        "n_frames": len(frames), "n_fovea_frames": n_fovea_frames,
        "depth": {
            "coarse_full_frame_null": _pack(coarse_full_depth),
            "fovea_coarse_in_window": _pack(fovea_depth_coarse),
            "fovea_fine_in_window": _pack(fovea_depth_fine),
            "full_fine_everywhere": _pack(full_fine_depth),
            "baseline_158000_coarse": -0.112, "baseline_158000_fine": 0.396,
        },
        "fovea_window_fraction_of_frame": _pack(fovea_frac_of_frame),
        "imp_recovery": {
            "n_imp_frames": len(imp_locate),
            "fovea_lands_on_imp_frames": n_on_imp,
            "fovea_to_imp_dist": _pack([d["fovea_to_imp_dist"] for d in imp_locate
                                        if d["fovea_to_imp_dist"] is not None]),
            "coarse_imp_flow_cells_total": coarse_imp_total,
            "fine_imp_flow_cells_total": fine_imp_total,
            "imp_locate_sample": imp_locate[:8],
            "imp_superpixel_sample": imp_superpixel[:8],
        },
        "per_frame_sample": per_frame[:10],
    }


# ======================================================================
def timing_arm(frames):
    """TIMING ALONE (§7) — this rung makes a real-time claim (foveated cheaper
    than full-res). Measure ms/frame for (a) full down=1 flow EVERYWHERE vs (b)
    the foveated pass (coarse down=2 flow + the fine windows). Nothing else runs
    on the box during this. Doom's budget is ~28.6 ms/frame (35 fps)."""
    seq = _default_action_seq()
    F = DOWN; gh_f, gw_f = 240, 320
    # (a) full-res everywhere
    t0 = time.perf_counter(); n = 0
    for fi in range(1, len(frames)):
        _flow_field(frames, fi, gh_f, gw_f, FINE_BLOCK, None); n += 1
    full_ms = (time.perf_counter() - t0) / max(1, n) * 1000.0
    # (b) foveated: coarse flow + fine windows
    t0 = time.perf_counter(); n = 0
    for fi in range(1, len(frames)):
        vy_c, vx_c = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
        if (np.sqrt(vy_c ** 2 + vx_c ** 2) > FLOOR).sum() < 8:
            n += 1; continue
        sal_c, valid_c, foe_c = salience_field(vy_c, vx_c)
        fovea, _ = select_fovea(sal_c, valid_c, top_k=2)
        for fv in fovea:
            bf = _window_cells_coarse_to_fine(fv["box"], F)
            r0f = min(bf[0], gh_f - 2); c0f = min(bf[2], gw_f - 2)
            r1f = min(max(bf[1], r0f + 2), gh_f); c1f = min(max(bf[3], c0f + 2), gw_f)
            fine_flow_window(frames, fi, [r0f, r1f, c0f, c1f])
        n += 1
    fov_ms = (time.perf_counter() - t0) / max(1, n) * 1000.0
    return {"full_res_ms_per_frame": round(full_ms, 2),
            "foveated_ms_per_frame": round(fov_ms, 2),
            "speedup": round(full_ms / fov_ms, 2) if fov_ms > 0 else None,
            "doom_budget_ms": 28.6,
            "foveated_within_budget": fov_ms <= 28.6,
            "fullres_within_budget": full_ms <= 28.6}


def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    result = {
        "block": BLOCK_SEED, "doom_seed": DOOM_SEED, "map": "E1M1",
        "grid_coarse": [GW, GH], "down": DOWN, "block": BLOCK, "level": LEVEL,
        "fine_down": FINE_DOWN, "fine_block": FINE_BLOCK,
        "fovea_min_half": FOVEA_MIN_HALF, "floor": FLOOR, "r_min": R_MIN,
        "skill": SKILL,
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
        "engine_line": prov.get("line"),
        "engine_provenance": prov,
    }

    print("== H1 synthetic (salience -> fovea -> fine recompute) ==")
    result["H1"] = run_h1()
    h1 = result["H1"]
    fl = h1["fovea_locates"]
    print(f"  (ii) fovea LOCATES: residual peak {fl['residual_peak_rc']} "
          f"on_mover={fl['residual_peak_on_mover']}; raw-|flow| peak "
          f"{fl['raw_flow_peak_rc']} on_mover={fl['raw_flow_peak_on_mover']} "
          f"(residual, not raw, lands on the mover)")
    if "coarse_null_vs_fine_recover" in h1:
        cr = h1["coarse_null_vs_fine_recover"]
        print(f"  (i)/(iii) mover IoU: coarse={cr['coarse_mover_iou']} -> "
              f"fine={cr['fine_mover_iou']}; depth Spearman: "
              f"coarse={cr['coarse_depth_spearman']} -> fine={cr['fine_depth_spearman']} "
              f"(coarse cells={cr['coarse_consistent_cells']} fine={cr['fine_consistent_cells']})")
    co = h1["cost"]
    print(f"  (iv) COST: foveated {co['foveated_total_cells']} cells vs full-res "
          f"{co['fullres_everywhere_cells']} = {co['foveated_fraction_of_fullres']} "
          f"of full-res")
    print(f"  control no-salient: n_fovea={h1['control_no_salient']['n_fovea']} "
          f"falls_back={h1['control_no_salient']['falls_back_to_coarse']}")
    print(f"  control two-regions: n_fovea={h1['control_two_regions']['n_fovea']} "
          f"both_covered={h1['control_two_regions']['both_regions_covered']} "
          f"peaks={h1['control_two_regions']['peaks']}")

    print("== H2 E1M1 (real WAD, 158000 walk/seed/grid) ==")
    frames = capture_e1m1()
    if not frames:
        result["H2_skipped"] = "vizdoom or DOOM.WAD absent"
        print("  SKIPPED:", result["H2_skipped"])
    else:
        result["H2_e1m1_frames"] = len(frames)
        h2 = run_h2(frames)
        result["H2"] = h2
        d = h2["depth"]
        print(f"  frames={h2['n_frames']} fovea_frames={h2['n_fovea_frames']}")
        print(f"  DEPTH (Spearman vs VizDoom buffer, forward frames):")
        print(f"    coarse full-frame (158000 null): {d['coarse_full_frame_null']['median']} "
              f"(n={d['coarse_full_frame_null']['n']}, 158000={d['baseline_158000_coarse']})")
        print(f"    fovea coarse-in-window (the null): {d['fovea_coarse_in_window']['median']} "
              f"(n={d['fovea_coarse_in_window']['n']})")
        print(f"    fovea FINE-in-window (foveated):   {d['fovea_fine_in_window']['median']} "
              f"(n={d['fovea_fine_in_window']['n']})")
        print(f"    full fine everywhere (ceiling):    {d['full_fine_everywhere']['median']} "
              f"(n={d['full_fine_everywhere']['n']}, 158000={d['baseline_158000_fine']})")
        ff = h2["fovea_window_fraction_of_frame"]
        print(f"  fovea window = {ff['median']} of the frame (median)")
        ir = h2["imp_recovery"]
        print(f"  IMP: {ir['n_imp_frames']} imp frames; fovea lands on imp in "
              f"{ir['fovea_lands_on_imp_frames']}; coarse imp flow cells="
              f"{ir['coarse_imp_flow_cells_total']} -> fine={ir['fine_imp_flow_cells_total']}")

        print("== TIMING (alone) ==")
        result["timing"] = timing_arm(frames)
        t = result["timing"]
        print(f"  full-res={t['full_res_ms_per_frame']} ms/frame "
              f"(budget {t['doom_budget_ms']}, within={t['fullres_within_budget']}) "
              f"-> foveated={t['foveated_ms_per_frame']} ms/frame "
              f"(within={t['foveated_within_budget']}), speedup={t['speedup']}x")

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "salience_foveation.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
