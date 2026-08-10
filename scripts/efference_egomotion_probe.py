#!/usr/bin/env python3
"""EFFERENCE-COPY EGOMOTION CANCELLATION (block 155000-155999).

THE GENERAL CAPABILITY (not Doom support), grounded in a confirmed principle —
ACTIVE INFERENCE / SENSORY ATTENUATION: an agent predicts the sensory
consequences of its OWN actions via an EFFERENCE COPY (a forward model of its
motor command), CANCELS them, and the RESIDUAL is the world / the other.

Applied to vision under EGOMOTION (self-turning):

  * predict the optic flow caused by the agent's OWN turn (`E_pred = gain x
    turn_command`, a ~uniform field because pure rotation is depth-independent),
  * CANCEL it   (`residual = observed_flow - E_pred`),
  * the residual isolates INDEPENDENTLY-MOVING world objects (background -> 0),
  * regions with ~zero OBSERVED flow while the world flows are the agent's own
    view-fixed APPARATUS (self) -- identified, and folded into the reference so
    they are never mislabeled as a world object.

ONE self-prediction mechanism -> (a) world/object carving under egomotion,
(b) static-background separation, (c) self-apparatus identification.

THE FORWARD MODEL IS GROUNDED, NOT TUNED (VISION_PROTOCOL sec.13). The turn->flow
gain is CALIBRATED from the agent's OWN turning observations (turn with the
scene, measure the resulting dominant/median flow = the egomotion gain). We ALSO
report the model-free baseline (cancel the per-frame MEAN / MEDIAN observed flow
= global-motion compensation, the codec move) and COMPARE: does predicting from
the agent's own command (efference copy, self-grounded) match or beat estimating
the dominant flow?

ARCHITECTURE (CLAUDE.md -- the agent is Rust). The grouping is the EXISTING Rust
primitive `segment_motion_and_track`, byte-for-byte unchanged (NO Rust added, NO
seed, NO default moved -- new files only, so the shipped carve path is
byte-identical BY CONSTRUCTION). The forward model (turn command -> predicted
flow), the cancellation subtraction, the apparatus zero-flow readout, and the
gain fit are MECHANICAL sensor / measurement transforms over arrays (no
conditional over graph state, no agent decision -- the peer of `vector_field`,
`divergence_field`, `quantize`). The VizDoom driver is a world adapter; the turn
command is a known world-adapter fact (the action the agent issued); the labels
buffer is the SCORING ORACLE, never fed to the eye. Scoring is set arithmetic
(IoU) by POSITION, never by cross-process region-id.

Reuses the gated primitives from scripts/eye_on_doom_probe.py and
scripts/looming_common_fate_probe.py (identical scorer, VizDoom adapter,
translation carve = `segment_motion`, region read-back) so the uncancelled
baseline is provably 152000/153000's.

Pre-registration: VISION_EFFERENCE_EGOMOTION_PREREG.md.
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

from scripts.eye_on_doom_probe import (  # noqa: E402
    _block_mean, downsample_labels, quantize, iou,
    _enemy_values, _player_values, capture_doom,
)
from scripts.looming_common_fate_probe import (  # noqa: E402
    translation_carve, best_region,
)

# ---- DECLARED RESIDUALS (sec.13 -- NOT tuned to the score) ------------------
BLOCK = 4               # vector_field aperture / flow block (the sensor aperture)
DOOM_SEED = 155000      # block base; fixed => reproducible
DOWN_DOOM = 2           # Doom downsample (per 153000's real-time value-carve ceiling)
N_FRAMES = 60
SCEN = "defend_the_center"
LEVEL = 4               # the eye's shipped quantization default; not the lever
SYNTH_GH, SYNTH_GW = 60, 80   # Doom-shaped synthetic grid
ZERO_FLOOR = 0.5        # the block-matcher's integer/sub-pixel floor: |flow|<0.5
                        # is "no motion". A falls-out quantity (one pixel step),
                        # NOT a tuned constant.


# ======================================================================
#  THE EFFERENCE COPY -- a learned forward model, grounded in the agent's
#  own turning. Calibrate the turn->flow gain from observed flow during a
#  turn; predict a uniform egomotion field from the command.
# ======================================================================
def flow_stats(vy, vx):
    """Global summaries of an observed flow field: robust MEDIAN and MEAN of
    each component + the median flow magnitude. Pure array math."""
    vy = np.asarray(vy, float).reshape(-1)
    vx = np.asarray(vx, float).reshape(-1)
    mag = np.sqrt(vy * vy + vx * vx)
    return {
        "median": (float(np.median(vy)), float(np.median(vx))),
        "mean": (float(np.mean(vy)), float(np.mean(vx))),
        "median_mag": float(np.median(mag)),
    }


def calibrate_gain(flow_fields):
    """GROUND the forward model: turn with the scene, measure the resulting
    DOMINANT flow = the egomotion gain (flow-per-turn-unit). Robust median over
    the calibration frames (the background is the plurality of the view, so its
    median flow IS the egomotion). Returns (gain_vy, gain_vx). No tuned constant
    -- the gain is MEASURED from the agent's own action."""
    ys, xs = [], []
    for (vy, vx) in flow_fields:
        st = flow_stats(vy, vx)
        ys.append(st["median"][0]); xs.append(st["median"][1])
    return (float(np.median(ys)), float(np.median(xs)))


def predict_egomotion(gain, shape):
    """Forward model: turn command (magnitude 1 for the fixed turn action) x the
    calibrated gain -> a UNIFORM predicted flow field (rotation is
    depth-independent, so one vector predicts the whole field)."""
    gy, gx = gain
    return (np.full(shape, gy, float), np.full(shape, gx, float))


def cancel(vy, vx, evy, evx):
    """Cancellation is arithmetic: residual = observed - predicted."""
    return (np.asarray(vy, float) - evy, np.asarray(vx, float) - evx)


# ======================================================================
#  APPARATUS IDENTIFICATION -- a mechanical readout. Cells with ~zero
#  OBSERVED flow while the global scene flows (median magnitude > floor) are
#  the view-fixed self-apparatus. Tolerance FALLS OUT of the block-matcher's
#  integer floor (|flow| < 0.5 = one pixel step), NOT tuned.
# ======================================================================
def zero_flow_mask(vy, vx, floor=ZERO_FLOOR):
    """Boolean grid: True where the cell has ~zero OBSERVED flow (magnitude below
    the block-matcher's one-pixel floor). Pure array math."""
    vy = np.asarray(vy, float); vx = np.asarray(vx, float)
    mag = np.sqrt(vy * vy + vx * vx)
    return mag < floor


def mask_to_cells(mask):
    return frozenset((int(r), int(c)) for r, c in zip(*np.where(mask)))


# ======================================================================
#  THE EFFERENCE CARVE -- cancel egomotion, fold the apparatus into the
#  reference, carve the residual with the UNCHANGED Rust `segment_motion`.
# ======================================================================
def efference_carve(vy, vx, egomotion, gh, gw, *, use_apparatus=True,
                    floor=ZERO_FLOOR):
    """Cancel `egomotion` (evy, evx) from the observed flow, fold the apparatus
    (zero-observed-flow) cells into the reference (residual 0 -> they join
    background, never a false world object), and carve the residual via the
    EXISTING segment_motion translation carve.

    THE SELF-GROUNDING: the DECISION that the world is flowing (so a zero-flow
    cell reads as SELF-apparatus rather than a static world) comes from the
    EGOMOTION MAGNITUDE -- i.e. from the agent's OWN command (efference copy),
    NOT from the observed field. A pure OBSERVATION-based estimate that reads
    ~zero flow (e.g. because the apparatus fills >half the view) concludes 'no
    motion' and cannot identify the apparatus; the command knows the agent
    turned. Returns (world_regions, app_cells, residual_vy, residual_vx)."""
    evy, evx = egomotion
    ry, rx = cancel(vy, vx, evy, evx)
    world_flowing = (evy * evy + evx * evx) ** 0.5 > floor   # from the COMMAND
    if use_apparatus and world_flowing:
        app = zero_flow_mask(vy, vx, floor)
        ry = ry.copy(); rx = rx.copy()
        ry[app] = 0.0; rx[app] = 0.0   # fold self into the reference frame
        app_cells = mask_to_cells(app)
    else:
        app_cells = frozenset()
    regs, _tol = translation_carve(ry, rx, gh, gw)
    return regs, app_cells, ry, rx


def raw_carve(vy, vx, gh, gw):
    """The UNCANCELLED baseline: segment_motion on the observed flow, no
    egomotion cancellation, no apparatus folding (152000/153000's carve)."""
    regs, _tol = translation_carve(np.asarray(vy, float), np.asarray(vx, float),
                                   gh, gw)
    return regs


def region_cells_union(regs):
    out = set()
    for r in regs:
        out |= set(r["cells"])
    return frozenset(out)


def best_iou_to(regs, gt):
    _, j = best_region(regs, gt)
    return j


# ======================================================================
#  SYNTHETIC GROUND TRUTH -- H1 (the ideal oracle). Build the OBSERVED flow
#  field directly: background flows with egomotion E; an independent object
#  flows with E + its own image motion; a view-fixed apparatus flows with 0.
# ======================================================================
def make_scene(gh, gw, E, obj_motion, *, obj_center=None, obj_R=6,
               apparatus_rows=0, bg_noise=0, rng=None):
    """Construct an observed flow field (vy, vx) + ground-truth masks.

    E            : egomotion vector (evy, evx) -- the uniform background flow.
    obj_motion   : the object's OWN image motion (added to E over the object).
    apparatus_rows : height of a bottom view-fixed band (flow 0) = the apparatus.
    bg_noise     : integer +-noise added to the background flow (block-SAD
                   quantization noise -- makes the textured background FRAGMENT,
                   the Doom-faithful regime).
    Returns dict with vy, vx, gt_object, gt_apparatus, gt_background, E."""
    evy, evx = E
    vy = np.full((gh, gw), float(evy))
    vx = np.full((gh, gw), float(evx))
    if bg_noise and rng is not None:
        vy += rng.integers(-bg_noise, bg_noise + 1, size=(gh, gw))
        vx += rng.integers(-bg_noise, bg_noise + 1, size=(gh, gw))
    # apparatus: a bottom band, view-fixed (flow 0), overwrites everything there
    app = np.zeros((gh, gw), bool)
    if apparatus_rows > 0:
        app[gh - apparatus_rows:, :] = True
        vy[app] = 0.0; vx[app] = 0.0
    # independent object: a disk in the upper field, observed flow = E + motion
    if obj_center is None:
        obj_center = (gh // 3, gw // 2)
    oy, ox = obj_center
    yy, xx = np.mgrid[0:gh, 0:gw]
    obj = ((yy - oy) ** 2 + (xx - ox) ** 2 <= obj_R * obj_R) & (~app)
    my, mx = obj_motion
    vy[obj] = float(evy + my); vx[obj] = float(evx + mx)
    gt_object = frozenset((int(r), int(c)) for r, c in zip(*np.where(obj)))
    gt_apparatus = frozenset((int(r), int(c)) for r, c in zip(*np.where(app)))
    bg = (~obj) & (~app)
    gt_background = frozenset((int(r), int(c)) for r, c in zip(*np.where(bg)))
    return {"vy": vy, "vx": vx, "gt_object": gt_object,
            "gt_apparatus": gt_apparatus, "gt_background": gt_background,
            "E": (float(evy), float(evx))}


def _carve_report(scene, egomotion, gh, gw, *, use_apparatus=True):
    """Run the raw and efference carves on a scene, score against GT."""
    vy, vx = scene["vy"], scene["vx"]
    gt_obj = scene["gt_object"]
    gt_app = scene["gt_apparatus"]
    gt_bg = scene["gt_background"]
    # RAW (uncancelled) carve
    raw = raw_carve(vy, vx, gh, gw)
    raw_obj_iou = best_iou_to(raw, gt_obj)
    raw_app_iou = best_iou_to(raw, gt_app) if gt_app else 0.0
    # EFFERENCE carve
    eff, app_cells, ry, rx = efference_carve(vy, vx, egomotion, gh, gw,
                                             use_apparatus=use_apparatus)
    eff_obj_iou = best_iou_to(eff, gt_obj)
    eff_app_iou = best_iou_to(eff, gt_app) if gt_app else 0.0
    # static-background residual (mean |residual| over background cells)
    if gt_bg:
        bg_idx = np.array(sorted(gt_bg))
        rmag = np.sqrt(ry[bg_idx[:, 0], bg_idx[:, 1]] ** 2 +
                       rx[bg_idx[:, 0], bg_idx[:, 1]] ** 2)
        bg_resid = float(np.mean(rmag))
    else:
        bg_resid = 0.0
    # apparatus identification: IoU of recovered zero-flow region to GT apparatus
    app_iou = iou(app_cells, gt_app) if gt_app else 0.0
    # is the moving object (nonzero observed flow) mislabeled apparatus?
    obj_in_app = len(set(gt_obj) & set(app_cells)) / len(gt_obj) if gt_obj else 0.0
    return {
        "raw_object_iou": round(raw_obj_iou, 4),
        "raw_apparatus_iou_as_object": round(raw_app_iou, 4),
        "raw_n_regions": len(raw),
        "eff_object_iou": round(eff_obj_iou, 4),
        "eff_apparatus_iou_as_object": round(eff_app_iou, 4),
        "eff_n_regions": len(eff),
        "apparatus_identified_iou": round(app_iou, 4),
        "object_fraction_in_apparatus": round(obj_in_app, 4),
        "background_residual_mean": round(bg_resid, 6),
    }


def carves_identical(regs_a, regs_b):
    """POSITION-anchored equality of two carve outputs (sets of cell-sets) --
    used for byte-identity-when-off controls."""
    A = sorted(tuple(sorted(r["cells"])) for r in regs_a)
    B = sorted(tuple(sorted(r["cells"])) for r in regs_b)
    return A == B


# ======================================================================
#  H1 -- synthetic mechanism + controls
# ======================================================================
def run_h1():
    gh, gw = SYNTH_GH, SYNTH_GW
    rng = np.random.default_rng(DOOM_SEED + 1)
    out = {"grid": [gw, gh], "cases": {}}

    # --- PRIMARY: KNOWN uniform egomotion + independent object + view-fixed
    #     apparatus (the ideal oracle). Large uniform egomotion (6), SMALL
    #     independent object motion (2), a big view-fixed apparatus band. ---
    E = (0, 6)
    scene = make_scene(gh, gw, E, obj_motion=(0, -2), obj_center=(14, 40),
                       obj_R=6, apparatus_rows=18, bg_noise=0, rng=rng)
    # efference: gain calibrated from a calibration TURN (the agent turns; the
    # world flows with E; measure the median flow = the gain -- grounded in the
    # agent's own action, NOT set).
    calib = [make_scene(gh, gw, E, obj_motion=(0, 0), obj_center=(14, 40),
                        obj_R=0, apparatus_rows=18, bg_noise=0, rng=None)
             for _ in range(5)]
    gain = calibrate_gain([(c["vy"], c["vx"]) for c in calib])
    out["calibrated_gain"] = [round(v, 4) for v in gain]
    out["true_egomotion"] = list(map(float, E))
    rep = _carve_report(scene, gain, gh, gw)
    # ABLATION: cancel egomotion but DON'T fold the apparatus (isolates whether
    # the fix is the uniform cancellation or the apparatus identification).
    eff_na, _, _, _ = efference_carve(scene["vy"], scene["vx"], gain, gh, gw,
                                      use_apparatus=False)
    # DIAGNOSTIC: the SAME scene with NO apparatus -> raw carve isolates the
    # object fine, proving the apparatus is what breaks the raw carve.
    scene_noapp = make_scene(gh, gw, E, obj_motion=(0, -2), obj_center=(14, 40),
                             obj_R=6, apparatus_rows=0, bg_noise=0)
    raw_noapp = raw_carve(scene_noapp["vy"], scene_noapp["vx"], gh, gw)
    # model-free baselines: cancel per-frame MEAN / MEDIAN observed flow
    st = flow_stats(scene["vy"], scene["vx"])
    mean_rep = _carve_report(scene, st["mean"], gh, gw)
    med_rep = _carve_report(scene, st["median"], gh, gw)
    out["cases"]["primary"] = {
        "efference": rep,
        "efference_no_apparatus_fold_object_iou":
            round(best_iou_to(eff_na, scene["gt_object"]), 4),
        "raw_without_apparatus_object_iou":
            round(best_iou_to(raw_noapp, scene_noapp["gt_object"]), 4),
        "model_free_mean": {"cancel_vec": [round(v, 3) for v in st["mean"]],
                            "object_iou": mean_rep["eff_object_iou"],
                            "background_residual_mean": mean_rep["background_residual_mean"]},
        "model_free_median": {"cancel_vec": [round(v, 3) for v in st["median"]],
                             "object_iou": med_rep["eff_object_iou"],
                             "background_residual_mean": med_rep["background_residual_mean"]},
        "efference_object_iou": rep["eff_object_iou"],
        "efference_background_residual_mean": rep["background_residual_mean"],
    }

    # --- SELF-GROUNDING EDGE CASE: apparatus fills >HALF the view. A pure
    #     OBSERVATION estimate reads ~zero global flow ('world not moving') and
    #     cannot identify the apparatus; the EFFERENCE COPY knows the agent
    #     turned (gain calibrated from a NORMAL turn) and proceeds. ---
    scene_big = make_scene(gh, gw, E, obj_motion=(0, -2), obj_center=(8, 40),
                           obj_R=5, apparatus_rows=36, bg_noise=0)
    st_big = flow_stats(scene_big["vy"], scene_big["vx"])
    eff_big, appc_big, _, _ = efference_carve(scene_big["vy"], scene_big["vx"],
                                              gain, gh, gw)             # command
    # model-free = cancel the observed MEDIAN (which is ~0 here -> apparatus ID
    # disabled by construction, exactly the failure the efference copy avoids).
    mf_big, appc_mf, _, _ = efference_carve(scene_big["vy"], scene_big["vx"],
                                            st_big["median"], gh, gw)
    out["cases"]["self_grounding_apparatus_majority"] = {
        "apparatus_fraction_of_view": round(len(scene_big["gt_apparatus"]) /
                                            (gh * gw), 3),
        "observed_median_flow": [round(v, 3) for v in st_big["median"]],
        "efference_gain": [round(v, 4) for v in gain],
        "efference_object_iou": round(best_iou_to(eff_big, scene_big["gt_object"]), 4),
        "efference_apparatus_identified": len(appc_big) > 0,
        "model_free_median_object_iou": round(best_iou_to(mf_big, scene_big["gt_object"]), 4),
        "model_free_apparatus_identified": len(appc_mf) > 0,
    }

    # --- CONTROL: no egomotion (stationary). Predicted flow ~ 0 -> cancellation
    #     is a no-op; the residual carve must be byte-identical to the raw carve.
    rng2 = np.random.default_rng(DOOM_SEED + 2)
    scene0 = make_scene(gh, gw, (0, 0), obj_motion=(0, -4), obj_center=(20, 40),
                        obj_R=6, apparatus_rows=0, bg_noise=0, rng=rng2)
    gain0 = calibrate_gain([(np.zeros((gh, gw)), np.zeros((gh, gw)))])
    raw0 = raw_carve(scene0["vy"], scene0["vx"], gh, gw)
    eff0, app0, _, _ = efference_carve(scene0["vy"], scene0["vx"], gain0, gh, gw)
    out["cases"]["control_no_egomotion"] = {
        "calibrated_gain": [round(v, 4) for v in gain0],
        "carves_byte_identical": carves_identical(raw0, eff0),
        "apparatus_cells": len(app0),
        "object_iou_raw": round(best_iou_to(raw0, scene0["gt_object"]), 4),
        "object_iou_eff": round(best_iou_to(eff0, scene0["gt_object"]), 4),
    }

    # --- CONTROL: static scene + egomotion (no independent object). Residual
    #     must be ~0 everywhere -> nothing carved. ---
    scene_s = make_scene(gh, gw, E, obj_motion=(0, 0), obj_center=(14, 40),
                         obj_R=0, apparatus_rows=18, bg_noise=0, rng=None)
    eff_s, app_s, ry_s, rx_s = efference_carve(scene_s["vy"], scene_s["vx"],
                                               E, gh, gw)
    out["cases"]["control_static_plus_egomotion"] = {
        "n_world_regions_carved": len(eff_s),
        "residual_mean_abs": round(float(np.mean(np.abs(ry_s)) +
                                         np.mean(np.abs(rx_s))), 6),
        "apparatus_cells": len(app_s),
    }

    # --- CONTROL: moving object + NO egomotion. Cancellation must not change
    #     the carve (E=0 -> residual == observed, apparatus mask empty). ---
    rng3 = np.random.default_rng(DOOM_SEED + 3)
    scene_m = make_scene(gh, gw, (0, 0), obj_motion=(0, -4), obj_center=(25, 45),
                         obj_R=7, apparatus_rows=0, bg_noise=0, rng=rng3)
    raw_m = raw_carve(scene_m["vy"], scene_m["vx"], gh, gw)
    eff_m, app_m, _, _ = efference_carve(scene_m["vy"], scene_m["vx"], (0, 0),
                                         gh, gw)
    out["cases"]["control_moving_object_no_egomotion"] = {
        "carves_byte_identical": carves_identical(raw_m, eff_m),
        "object_iou": round(best_iou_to(eff_m, scene_m["gt_object"]), 4),
        "apparatus_cells": len(app_m),
    }

    # --- CONTROL: apparatus-not-carved + moving-object-not-apparatus (read off
    #     the primary scene report). ---
    out["cases"]["control_apparatus_discrimination"] = {
        "apparatus_identified_iou": rep["apparatus_identified_iou"],
        "apparatus_carved_as_world_object_iou": rep["eff_apparatus_iou_as_object"],
        "object_fraction_mislabeled_apparatus": rep["object_fraction_in_apparatus"],
        "raw_carves_apparatus_as_object_iou": rep["raw_apparatus_iou_as_object"],
    }
    return out


# ======================================================================
#  H2 -- DOOM defend_the_center, TURNING, ground-truth scored
# ======================================================================
def _doom_flow_fields(frames, gh, gw, block):
    """Per-frame observed flow (vy, vx) on quantized luma + the GT enemy / player
    cell-sets. Mechanical; identical pipeline to 152-154."""
    from domains.motion_group_world import vector_field

    def luma(rgb):
        rgb = np.asarray(rgb)
        if rgb.ndim == 3 and rgb.shape[0] == 3:
            rgb = np.transpose(rgb, (1, 2, 0))
        L = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])
        return _block_mean(L.astype(np.float64), gh, gw).astype(np.uint8)

    fq = quantize(np.stack([luma(f["rgb"]) for f in frames]), LEVEL)
    gt_grids = [downsample_labels(f["labels_buf"], gh, gw) for f in frames]
    fields, gts = [], []
    prev = None
    for fi in range(len(frames)):
        cur = fq[fi].astype(np.float64)
        if prev is None:
            vy = np.zeros((gh, gw)); vx = np.zeros((gh, gw))
        else:
            vf = vector_field(prev, cur, block=block)
            vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)[:gh, :gw]
            vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)[:gh, :gw]
            fy = np.zeros((gh, gw)); fx = np.zeros((gh, gw))
            fy[:vy.shape[0], :vy.shape[1]] = vy
            fx[:vx.shape[0], :vx.shape[1]] = vx
            vy, vx = fy, fx
        prev = cur
        labels = frames[fi]["labels"]
        gt = gt_grids[fi]
        ev = _enemy_values(labels); pv = _player_values(labels)
        gt_enemy = frozenset((int(r), int(c)) for v in ev
                             for r, c in zip(*np.where(gt == v)))
        gt_player = frozenset((int(r), int(c)) for v in pv
                              for r, c in zip(*np.where(gt == v)))
        fields.append((vy, vx))
        gts.append({"enemy": gt_enemy, "player": gt_player,
                    "enemy_present": bool(ev)})
    return fields, gts


def run_h2_doom():
    down = DOWN_DOOM
    gh, gw = 240 // down, 320 // down
    block = max(1, 16 // down)   # constant ~16px physical aperture (as 153000)

    # CALIBRATION TURN: the agent turns; measure the gain from its OWN flow.
    calib_frames = capture_doom("turn_right", n_frames=N_FRAMES, seed=DOOM_SEED)
    if not calib_frames:
        return {"error": "no frames captured (vizdoom absent?)"}
    calib_fields, _ = _doom_flow_fields(calib_frames, gh, gw, block)
    # drop the zero frame-0 field (no predecessor)
    gain = calibrate_gain(calib_fields[1:])

    # EGOMOTION-VISIBILITY DIAGNOSTIC: what fraction of the view produces
    # trackable flow under turning, and is there a COHERENT (dominant) egomotion
    # vector among the moving cells? The premise of egomotion cancellation is
    # that turning makes the (textured) world flow; measure whether it does.
    nz_fracs, dom_vy, dom_vx = [], [], []
    for (vy, vx) in calib_fields[1:]:
        mag = np.sqrt(np.asarray(vy) ** 2 + np.asarray(vx) ** 2)
        nz = mag > ZERO_FLOOR
        nz_fracs.append(float(nz.mean()))
        if nz.any():
            dom_vy.append(float(np.median(np.asarray(vy)[nz])))
            dom_vx.append(float(np.median(np.asarray(vx)[nz])))
    egomotion_visibility = {
        "nonzero_flow_fraction_mean": float(np.mean(nz_fracs)) if nz_fracs else 0.0,
        "dominant_moving_flow_median": [
            float(np.median(dom_vy)) if dom_vy else 0.0,
            float(np.median(dom_vx)) if dom_vx else 0.0],
        "all_cell_median_gain": [round(v, 4) for v in gain],
    }

    # TEST TURN (same seed + same fixed action => identical capture; the gain is
    # calibrated from the agent's own turn, then applied).
    frames = capture_doom("turn_right", n_frames=N_FRAMES, seed=DOOM_SEED)
    fields, gts = _doom_flow_fields(frames, gh, gw, block)

    raw_ious, eff_ious = [], []
    app_ious, app_flow_mags, enemy_flow_mags = [], [], []
    per_frame = []
    raw_walls, eff_walls = [], []
    enemy_present = 0
    for fi in range(len(frames)):
        gt_enemy = gts[fi]["enemy"]; gt_player = gts[fi]["player"]
        if gts[fi]["enemy_present"]:
            enemy_present += 1
        if not gt_enemy:
            continue
        vy, vx = fields[fi]
        t0 = time.perf_counter()
        raw = raw_carve(vy, vx, gh, gw)
        raw_walls.append(time.perf_counter() - t0)
        t1 = time.perf_counter()
        eff, app_cells, ry, rx = efference_carve(vy, vx, gain, gh, gw)
        eff_walls.append(time.perf_counter() - t1)
        r_iou = best_iou_to(raw, gt_enemy)
        e_iou = best_iou_to(eff, gt_enemy)
        raw_ious.append(r_iou); eff_ious.append(e_iou)
        # apparatus = recovered zero-flow region; score vs the DoomPlayer weapon
        if gt_player:
            app_ious.append(iou(app_cells, gt_player))
        # flow magnitudes on apparatus vs enemy GT (the discriminator)
        mag = np.sqrt(np.asarray(vy) ** 2 + np.asarray(vx) ** 2)
        if gt_player:
            pj = np.array(sorted(gt_player))
            app_flow_mags.append(float(np.mean(mag[pj[:, 0], pj[:, 1]])))
        ej = np.array(sorted(gt_enemy))
        enemy_flow_mags.append(float(np.mean(mag[ej[:, 0], ej[:, 1]])))
        per_frame.append({"frame": fi, "raw_iou": round(r_iou, 4),
                          "eff_iou": round(e_iou, 4),
                          "enemy_cells": len(gt_enemy)})

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "max": float(np.max(xs)), "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "max": 0.0, "n": 0})

    # bimodal split: super-pixel (>=3 enemy cells) vs sub-pixel frames
    superpix = [(p["raw_iou"], p["eff_iou"]) for p in per_frame
                if p["enemy_cells"] >= 3]
    subpix = [(p["raw_iou"], p["eff_iou"]) for p in per_frame
              if p["enemy_cells"] < 3]
    return {
        "down": down, "grid": [gw, gh], "block": block,
        "calibrated_gain": [round(v, 4) for v in gain],
        "egomotion_visibility": egomotion_visibility,
        "enemy_present_frames": enemy_present,
        "raw_enemy_iou": stat(raw_ious),
        "efference_enemy_iou": stat(eff_ious),
        "raw_enemy_iou_dist": [round(x, 4) for x in raw_ious],
        "efference_enemy_iou_dist": [round(x, 4) for x in eff_ious],
        "apparatus_weapon_iou": stat(app_ious),
        "apparatus_flow_mag_mean": (float(np.mean(app_flow_mags))
                                    if app_flow_mags else 0.0),
        "enemy_flow_mag_mean": (float(np.mean(enemy_flow_mags))
                                if enemy_flow_mags else 0.0),
        "superpixel_frames": {
            "n": len(superpix),
            "raw_mean": float(np.mean([a for a, _ in superpix])) if superpix else 0.0,
            "eff_mean": float(np.mean([b for _, b in superpix])) if superpix else 0.0},
        "subpixel_frames": {
            "n": len(subpix),
            "raw_mean": float(np.mean([a for a, _ in subpix])) if subpix else 0.0,
            "eff_mean": float(np.mean([b for _, b in subpix])) if subpix else 0.0},
        "raw_ms_per_frame": float(np.mean(raw_walls) * 1e3) if raw_walls else 0.0,
        "eff_ms_per_frame": float(np.mean(eff_walls) * 1e3) if eff_walls else 0.0,
        "per_frame": per_frame,
    }


# ======================================================================
def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    result = {
        "block": 155000, "doom_seed": DOOM_SEED, "block_aperture": BLOCK,
        "zero_floor": ZERO_FLOOR,
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
    }
    print("== H1 synthetic (efference-copy cancellation + controls) ==")
    result["h1"] = run_h1()
    pc = result["h1"]["cases"]["primary"]
    ef = pc["efference"]
    print(f"  calibrated gain = {result['h1']['calibrated_gain']} "
          f"(true egomotion {result['h1']['true_egomotion']})")
    print(f"  PRIMARY object IoU: raw={ef['raw_object_iou']:.3f} "
          f"-> efference={ef['eff_object_iou']:.3f}")
    print(f"  apparatus identified IoU={ef['apparatus_identified_iou']:.3f}; "
          f"static bg residual={ef['background_residual_mean']:.4f}")
    print(f"  efference vs model-free: eff={pc['efference_object_iou']:.3f} "
          f"mean-cancel={pc['model_free_mean']['object_iou']:.3f} "
          f"median-cancel={pc['model_free_median']['object_iou']:.3f}")
    for k in ("control_no_egomotion", "control_static_plus_egomotion",
              "control_moving_object_no_egomotion",
              "control_apparatus_discrimination"):
        print(f"  [{k}] {result['h1']['cases'][k]}")

    print("== H2 Doom defend_the_center TURNING (ground-truth scored) ==")
    result["h2_doom"] = run_h2_doom()
    h2 = result["h2_doom"]
    if "error" not in h2:
        print(f"  down={h2['down']} grid={h2['grid']} block={h2['block']} "
              f"gain={h2['calibrated_gain']} enemy_present={h2['enemy_present_frames']}")
        ev = h2["egomotion_visibility"]
        print(f"  EGOMOTION VISIBILITY: nonzero-flow={ev['nonzero_flow_fraction_mean']*100:.0f}% "
              f"dominant-moving-flow={ev['dominant_moving_flow_median']} "
              f"(no coherent egomotion => nothing to cancel)")
        print(f"  RAW enemy IoU mean={h2['raw_enemy_iou']['mean']:.4f} "
              f"(n={h2['raw_enemy_iou']['n']})")
        print(f"  EFFERENCE enemy IoU mean={h2['efference_enemy_iou']['mean']:.4f} "
              f"(n={h2['efference_enemy_iou']['n']})")
        print(f"  superpixel: raw={h2['superpixel_frames']['raw_mean']:.3f} "
              f"eff={h2['superpixel_frames']['eff_mean']:.3f} "
              f"(n={h2['superpixel_frames']['n']}) | "
              f"subpixel eff={h2['subpixel_frames']['eff_mean']:.3f} "
              f"(n={h2['subpixel_frames']['n']})")
        print(f"  apparatus(weapon) IoU mean={h2['apparatus_weapon_iou']['mean']:.3f}; "
              f"flow mag apparatus={h2['apparatus_flow_mag_mean']:.2f} "
              f"vs enemy={h2['enemy_flow_mag_mean']:.2f}")
        print(f"  ms/frame raw={h2['raw_ms_per_frame']:.1f} "
              f"eff={h2['eff_ms_per_frame']:.1f}")
    else:
        print("  ", h2["error"])

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "efference_egomotion.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
