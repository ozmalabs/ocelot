#!/usr/bin/env python3
"""RESIDUAL-SALIENCE PROBE (block 157000-157999).

THE ONE COUPLED FIX — efference -> residual -> salience.

156000 found two coupled failures that are ONE thing: salience
(`memory::order_n_shape_salience`) ranks the egomotion-swung WALKING BACKGROUND
highest because it runs on the RAW trajectories, and 155000's median-over-all
gain reads (0,0) below 50% flow coverage so cancellation is a no-op. THE FIX
composes existing pieces:

  1. a DOMINANT-MODE egomotion gain = the peak of the flow histogram over the
     MOVING cells (robust at 42% coverage where the all-cell median is 0);
  2. CANCEL the self-predicted flow (subtract cumulative egomotion from each
     region's trajectory; fold the view-fixed apparatus, 155000's zero-observed-
     flow readout);
  3. run SALIENCE (`Substrate.shape_salience`) on the RESIDUAL trajectories.

surprise = residual. The egomotion-swung background -> ~0 residual -> LOW
salience; the independently-moving object -> residual own-motion -> HIGH
salience; the view-fixed apparatus stays demoted. It is a general ATTENTION
ranking that works EVEN OVER A NOISY CARVE (attention needs a good ranking, not
a clean carve).

ARCHITECTURE (CLAUDE.md -- the agent is Rust). No agent decision in Python:
the dominant-mode gain is a mechanical flow-histogram peak (numpy, the peer of
`vector_field` / `quantize`); the cancellation is arithmetic; the apparatus fold
is 155000's mechanical zero-observed-flow readout; the salience is the EXISTING
Rust operator; the tracker is the EXISTING mechanical `_collect_tracks`; scoring
is IoU/position + salience rank vs the labels buffer, never cross-process
region-id. NO Rust added, NO seed, NO default moved -- new files only, so the
shipped carve path and 155000's median-gain path are byte-identical by
construction (the dominant-mode gain is an ADDITIVE new function).

Pre-registration: VISION_RESIDUAL_SALIENCE_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Reuse 156000's carve + tracking + scoring verbatim (provably the shipped path).
from scripts.e1m1_salience_probe import (  # noqa: E402
    capture_e1m1, _collect_tracks, _track_gt_category, _auc,
    _value_category, _cat_values, _luma_stack, _e1m1_flow_fields,
    GH, GW, DOWN, BLOCK, LEVEL, N_FRAMES, SKILL, DOOM_SEED, KSWEEP,
    w1_carve_score,
)
from scripts.eye_on_doom_probe import quantize, run_value_carve  # noqa: E402

# ---- DECLARED RESIDUALS (§13 -- the sensor's aperture, NOT tuned) -----------
ZERO_FLOOR = 0.5        # the block-matcher's one-pixel integer step (155000's
                        # ZERO_FLOOR): |flow| < 0.5 is "no motion". A falls-out
                        # quantity, NOT a tuned constant.
BLOCK_SEED = 157000     # block base


# ======================================================================
#  THE NEW MECHANISM -- a DOMINANT-MODE egomotion gain. The peak of the flow
#  histogram over the MOVING cells. Robust where <50% coverage makes the
#  all-cell median (155000's calibrate_gain) read (0,0). Mechanical numpy;
#  the peak FALLS OUT of the histogram, it is not a tuned threshold.
# ======================================================================
def dominant_mode_gain(vy, vx, floor=ZERO_FLOOR):
    """Dominant-MODE egomotion gain of one observed flow field: the most common
    integer flow vector over the moving cells (|flow| > one-pixel step). The
    peak of the flow histogram. Returns (gy, gx). No tuned constant."""
    vy = np.asarray(vy, float); vx = np.asarray(vx, float)
    mag = np.sqrt(vy * vy + vx * vx)
    nz = mag > floor
    if not nz.any():
        return (0.0, 0.0)
    ys = np.rint(vy[nz]).astype(np.int64)
    xs = np.rint(vx[nz]).astype(np.int64)
    pairs = np.stack([ys, xs], axis=1)
    uniq, counts = np.unique(pairs, axis=0, return_counts=True)
    peak = uniq[int(np.argmax(counts))]
    return (float(peak[0]), float(peak[1]))


def median_all_gain(vy, vx):
    """155000's baseline: median flow over ALL cells (reads (0,0) below 50%
    coverage). For the head-to-head recovery comparison only."""
    vy = np.asarray(vy, float); vx = np.asarray(vx, float)
    return (float(np.median(vy)), float(np.median(vx)))


def otsu_moving_cutoff(mag):
    """Otsu threshold on flow magnitude -- the cross-check that the 'moving cell'
    cutoff also FALLS OUT (an alternative to the one-pixel step), not tuned."""
    mag = np.asarray(mag, float).reshape(-1)
    hi = mag.max()
    if hi <= 0:
        return 0.0
    bins = np.linspace(0, hi, 64)
    hist, edges = np.histogram(mag, bins=bins)
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


# ======================================================================
#  THE CANCELLATION -- subtract cumulative egomotion from a track's centroid
#  path; FOLD the apparatus (a track whose observed step is ~0 while the world
#  flows is SELF -> its residual step is 0, leaving it flat). 155000's readout.
# ======================================================================
def residual_trajectory(track, ego_per_frame, floor=ZERO_FLOOR):
    """Residual (egomotion-cancelled, apparatus-folded) centroid path of a track.
    residual step = observed step - egomotion step, EXCEPT a view-fixed cell
    (observed ~0 while egomotion present) is SELF -> residual step 0."""
    pts = track["pts"]
    ry = [pts[0]["cy"]]; rx = [pts[0]["cx"]]
    for i in range(1, len(pts)):
        f = pts[i]["frame"]; fprev = pts[i - 1]["frame"]
        egy = sum(ego_per_frame[k][0] for k in range(fprev + 1, f + 1)
                  if 0 <= k < len(ego_per_frame))
        egx = sum(ego_per_frame[k][1] for k in range(fprev + 1, f + 1)
                  if 0 <= k < len(ego_per_frame))
        obs_y = pts[i]["cy"] - pts[i - 1]["cy"]
        obs_x = pts[i]["cx"] - pts[i - 1]["cx"]
        ego_mag = (egy * egy + egx * egx) ** 0.5
        obs_mag = (obs_y * obs_y + obs_x * obs_x) ** 0.5
        if ego_mag > floor and obs_mag < floor:
            res_y, res_x = 0.0, 0.0        # apparatus: self, folded to reference
        else:
            res_y, res_x = obs_y - egy, obs_x - egx
        ry.append(ry[-1] + res_y)
        rx.append(rx[-1] + res_x)
    return ry, rx


def salience_raw(track, S):
    """156000's W2 salience: max shape_salience over centroid-x / centroid-y /
    area (reproduces the failure -- egomotion-swung background dominates)."""
    pts = track["pts"]
    if len(pts) < 3:
        return 0.0
    cx = [p["cx"] for p in pts]; cy = [p["cy"] for p in pts]
    ar = [float(p["area"]) for p in pts]
    return max(S.shape_salience(cx), S.shape_salience(cy), S.shape_salience(ar))


def salience_raw_motion(track, S):
    """Centroid-only raw salience (no area) -- isolates the cancellation effect
    from the area-drop in the raw-vs-residual comparison."""
    pts = track["pts"]
    if len(pts) < 3:
        return 0.0
    cx = [p["cx"] for p in pts]; cy = [p["cy"] for p in pts]
    return max(S.shape_salience(cx), S.shape_salience(cy))


def salience_residual(track, ego_per_frame, S):
    """THE FIX: salience on the RESIDUAL (egomotion-cancelled) centroid path.
    Background swung by egomotion -> flat residual -> ~0; independent mover ->
    residual own-motion -> high; apparatus folded flat -> ~0."""
    pts = track["pts"]
    if len(pts) < 3:
        return 0.0
    ry, rx = residual_trajectory(track, ego_per_frame)
    return max(S.shape_salience(ry), S.shape_salience(rx))


# ======================================================================
#  H1 -- SYNTHETIC: prove the pipeline against an ideal oracle.
# ======================================================================
def _synth_track(frame0, cy0, cx0, step, n, area, jitter_rng=None, jit=0.0):
    """A synthetic region track: centroid starts at (cy0,cx0), advances by `step`
    per frame (+ optional integer jitter for fragmentation)."""
    pts = []
    cy, cx = float(cy0), float(cx0)
    for i in range(n):
        jy = jx = 0.0
        if jitter_rng is not None and jit > 0:
            jy = float(jitter_rng.integers(-jit, jit + 1))
            jx = float(jitter_rng.integers(-jit, jit + 1))
        pts.append({"frame": frame0 + i, "cy": cy + jy, "cx": cx + jx,
                    "area": float(area), "cells": frozenset()})
        cy += step[0]; cx += step[1]
    return {"pts": pts}


def make_coverage_field(gh, gw, E, coverage, rng):
    """A flow field where `coverage` fraction of cells carry egomotion E and the
    rest are static (0). Below 50% the all-cell median reads (0,0), but the mode
    over moving cells is E. The exact 156000 failure, able to fail."""
    vy = np.zeros((gh, gw)); vx = np.zeros((gh, gw))
    n = gh * gw
    k = int(round(coverage * n))
    idx = rng.choice(n, size=k, replace=False)
    ys = idx // gw; xs = idx % gw
    vy[ys, xs] = float(E[0]); vx[ys, xs] = float(E[1])
    return vy, vx


def run_h1():
    from substrate_rs import _native as native
    S = native.Substrate
    out = {}

    # ---- gain recovery: dominant MODE vs median-over-all on a <50% coverage
    #      field with KNOWN egomotion. Able to fail. ----
    gh, gw = 60, 80
    E_true = (0, 6)
    rng = np.random.default_rng(BLOCK_SEED + 3)
    recovery = {}
    for cov in (0.42, 0.30, 0.55):
        vy, vx = make_coverage_field(gh, gw, E_true, cov, rng)
        mag = np.sqrt(vy * vy + vx * vx)
        recovery[f"coverage_{cov}"] = {
            "true_egomotion": list(map(float, E_true)),
            "gain_mode": list(dominant_mode_gain(vy, vx)),
            "gain_median_all": [round(v, 3) for v in median_all_gain(vy, vx)],
            "otsu_moving_cutoff": round(otsu_moving_cutoff(mag), 3),
            "nonzero_fraction": round(float((mag > ZERO_FLOOR).mean()), 3),
        }
    out["gain_recovery"] = recovery

    # ---- salience ranking on synthetic tracks: RAW vs RESIDUAL ----
    def build_scene(E, own_motion, n_bg=12, n_frames=12, jit=1, seed=BLOCK_SEED + 1):
        jrng = np.random.default_rng(seed)
        tracks, cats = [], []
        # background: swung by egomotion, fragmented (jitter). Placed across view.
        for b in range(n_bg):
            cy0 = 5 + (b % 4) * 12; cx0 = 5 + (b // 4) * 20
            tracks.append(_synth_track(0, cy0, cx0, E, n_frames, 40,
                                       jitter_rng=jrng, jit=jit))
            cats.append("background")
        # independent mover: observed = egomotion + own motion
        mv_step = (E[0] + own_motion[0], E[1] + own_motion[1])
        tracks.append(_synth_track(0, 30, 40, mv_step, n_frames, 12))
        cats.append("mover")
        # apparatus: view-fixed (flat centroid)
        tracks.append(_synth_track(0, 55, 40, (0, 0), n_frames, 60,
                                   jitter_rng=np.random.default_rng(seed + 9), jit=0))
        cats.append("apparatus")
        # per-frame egomotion, ESTIMATED from a coverage flow field (able to fail)
        ego_field_rng = np.random.default_rng(seed + 100)
        ego_per_frame = [(0.0, 0.0)]
        for _ in range(1, n_frames):
            fy, fx = make_coverage_field(gh, gw, E, 0.42, ego_field_rng)
            ego_per_frame.append(dominant_mode_gain(fy, fx))
        return tracks, cats, ego_per_frame

    def score_scene(tracks, cats, ego_per_frame):
        raw = [salience_raw(t, S) for t in tracks]
        raw_mot = [salience_raw_motion(t, S) for t in tracks]
        res = [salience_residual(t, ego_per_frame, S) for t in tracks]
        idx = {c: [i for i, cc in enumerate(cats) if cc == c]
               for c in ("background", "mover", "apparatus")}
        fg = idx["mover"]; bg = idx["background"]; ap = idx["apparatus"]
        rank_res = sorted(range(len(res)), key=lambda i: -res[i])
        mover_rank = rank_res.index(fg[0]) + 1 if fg else None
        return {
            "raw_salience": {"mover": [round(raw[i], 3) for i in fg],
                             "background_mean": round(float(np.mean([raw[i] for i in bg])), 3),
                             "background_max": round(float(np.max([raw[i] for i in bg])), 3),
                             "apparatus": [round(raw[i], 3) for i in ap]},
            "residual_salience": {"mover": [round(res[i], 3) for i in fg],
                                  "background_mean": round(float(np.mean([res[i] for i in bg])), 3),
                                  "background_max": round(float(np.max([res[i] for i in bg])), 3),
                                  "apparatus": [round(res[i], 3) for i in ap]},
            "auc_raw_fg_vs_bg": _auc([raw[i] for i in fg], [raw[i] for i in bg]),
            "auc_rawmotion_fg_vs_bg": _auc([raw_mot[i] for i in fg], [raw_mot[i] for i in bg]),
            "auc_residual_fg_vs_bg": _auc([res[i] for i in fg], [res[i] for i in bg]),
            "auc_raw_fg_vs_apparatus": _auc([raw[i] for i in fg], [raw[i] for i in ap]),
            "auc_residual_fg_vs_apparatus": _auc([res[i] for i in fg], [res[i] for i in ap]),
            "mover_rank_residual": mover_rank,
            "n_tracks": len(tracks),
        }

    # PRIMARY: large egomotion (0,6) + small independent object motion (0,-3)
    tr, ca, ego = build_scene((0, 6), (0, -3))
    out["primary"] = score_scene(tr, ca, ego)
    out["primary"]["egomotion_estimated_per_frame_sample"] = [list(e) for e in ego[:4]]
    out["primary"]["true_egomotion"] = [0, 6]
    out["primary"]["own_motion"] = [0, -3]

    # CONTROL: no egomotion (stationary). mode ~0 -> residual == raw ranking.
    tr0, ca0, _ = build_scene((0, 0), (0, -3))
    ego0 = [dominant_mode_gain(*make_coverage_field(gh, gw, (0, 0), 0.42,
            np.random.default_rng(BLOCK_SEED + 200 + i))) for i in range(12)]
    S_ = S
    raw0 = [salience_raw_motion(t, S_) for t in tr0]
    res0 = [salience_residual(t, ego0, S_) for t in tr0]
    out["control_no_egomotion"] = {
        "gain_mode_all_zero": all(e == (0.0, 0.0) for e in ego0),
        "ranking_identical": (sorted(range(len(raw0)), key=lambda i: -raw0[i]) ==
                              sorted(range(len(res0)), key=lambda i: -res0[i])),
        "raw_eq_residual_values": all(abs(a - b) < 1e-9 for a, b in zip(raw0, res0)),
    }

    # CONTROL: static scene + egomotion (no independent mover) -> all residual
    #          ~0 -> flat/low salience everywhere.
    jrng = np.random.default_rng(BLOCK_SEED + 5)
    E = (0, 6)
    static_tracks = []
    for b in range(12):
        cy0 = 5 + (b % 4) * 12; cx0 = 5 + (b // 4) * 20
        static_tracks.append(_synth_track(0, cy0, cx0, E, 12, 40,
                                          jitter_rng=jrng, jit=1))
    ego_s = [(0.0, 0.0)] + [dominant_mode_gain(*make_coverage_field(gh, gw, E, 0.42,
             np.random.default_rng(BLOCK_SEED + 300 + i))) for i in range(11)]
    res_s = [salience_residual(t, ego_s, S) for t in static_tracks]
    out["control_static_plus_egomotion"] = {
        "residual_salience_max": round(float(np.max(res_s)), 4),
        "residual_salience_mean": round(float(np.mean(res_s)), 4),
        "all_low": bool(np.max(res_s) < 1.0),
    }

    # CONTROL: independent mover + NO egomotion -> ranked salient with AND
    #          without cancellation (residual == raw there).
    mv = _synth_track(0, 30, 40, (0, -4), 12, 12)
    bgm = [_synth_track(0, 5 + i * 8, 10, (0, 0), 12, 40,
                        jitter_rng=np.random.default_rng(BLOCK_SEED + 400 + i), jit=0)
           for i in range(6)]
    tracks_m = [mv] + bgm
    ego_m = [(0.0, 0.0)] * 12
    raw_m = [salience_raw_motion(t, S) for t in tracks_m]
    res_m = [salience_residual(t, ego_m, S) for t in tracks_m]
    out["control_mover_no_egomotion"] = {
        "mover_top_raw": int(np.argmax(raw_m)) == 0,
        "mover_top_residual": int(np.argmax(res_m)) == 0,
        "raw_eq_residual": all(abs(a - b) < 1e-9 for a, b in zip(raw_m, res_m)),
    }
    return out


# ======================================================================
#  H2 -- E1M1, ground-truth-scored (real WAD, 156000's walk/seed/grid).
# ======================================================================
def run_h2(frames):
    from substrate_rs import _native as native
    S = native.Substrate

    # carve + tracks (156000's exact path)
    fq = quantize(_luma_stack(frames), LEVEL)
    per_frame, _walls = run_value_carve(fq, GH, GW)
    from scripts.eye_on_doom_probe import downsample_labels
    gt_grids = [downsample_labels(f["labels_buf"], GH, GW) for f in frames]

    # per-frame flow + per-frame dominant-mode gain (the new mechanism)
    fields, _gts = _e1m1_flow_fields(frames)
    ego_per_frame, median_per_frame, nz_fracs = [], [], []
    for fi, (vy, vx) in enumerate(fields):
        if fi == 0:
            ego_per_frame.append((0.0, 0.0)); median_per_frame.append((0.0, 0.0))
            nz_fracs.append(0.0); continue
        ego_per_frame.append(dominant_mode_gain(vy, vx))
        median_per_frame.append(median_all_gain(vy, vx))
        mag = np.sqrt(np.asarray(vy) ** 2 + np.asarray(vx) ** 2)
        nz_fracs.append(float((mag > ZERO_FLOOR).mean()))

    tracks = [t for t in _collect_tracks(per_frame) if len(t["pts"]) >= 3]
    scored = []
    for t in tracks:
        cat = _track_gt_category(t, gt_grids, frames)
        scored.append({
            "cat": cat,
            "raw": float(salience_raw(t, S)),
            "raw_motion": float(salience_raw_motion(t, S)),
            "residual": float(salience_residual(t, ego_per_frame, S)),
            "len": len(t["pts"]),
        })

    def group(key, cat):
        return [s[key] for s in scored if s["cat"] == cat]
    fg_raw = group("raw", "monster") + group("raw", "item")
    fg_rawmot = group("raw_motion", "monster") + group("raw_motion", "item")
    fg_res = group("residual", "monster") + group("residual", "item")
    bg_raw = group("raw", "background"); bg_rawmot = group("raw_motion", "background")
    bg_res = group("residual", "background")
    app_raw = group("raw", "apparatus"); app_res = group("residual", "apparatus")
    mon_res = group("residual", "monster"); mon_raw = group("raw", "monster")

    # salience@k, raw vs residual
    def topk_cats(key):
        order = sorted(range(len(scored)), key=lambda i: -scored[i][key])
        return {str(k): [scored[i]["cat"] for i in order[:k]] for k in KSWEEP}

    def stat(xs):
        return ({"mean": round(float(np.mean(xs)), 3),
                 "median": round(float(np.median(xs)), 3),
                 "max": round(float(np.max(xs)), 3), "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "max": 0.0, "n": 0})

    by_cat = defaultdict(lambda: defaultdict(list))
    for s in scored:
        by_cat[s["cat"]]["raw"].append(s["raw"])
        by_cat[s["cat"]]["residual"].append(s["residual"])

    # egomotion capture: fraction of frames where the mode is nonzero vs median
    mode_nonzero = sum(1 for e in ego_per_frame[1:] if e != (0.0, 0.0))
    median_nonzero = sum(1 for m in median_per_frame[1:] if m != (0.0, 0.0))

    return {
        "grid": [GW, GH], "down": DOWN, "block": BLOCK, "level": LEVEL,
        "n_frames": len(frames), "n_tracks_scored": len(scored),
        "egomotion_capture": {
            "nonzero_flow_fraction_mean": round(float(np.mean(nz_fracs[1:])), 3),
            "mode_nonzero_frames": mode_nonzero,
            "median_all_nonzero_frames": median_nonzero,
            "total_motion_frames": len(ego_per_frame) - 1,
            "dominant_mode_sample": [list(e) for e in ego_per_frame[1:9]],
            "median_all_sample": [[round(v, 2) for v in m] for m in median_per_frame[1:9]],
        },
        "salience_by_category": {
            c: {"raw": stat(by_cat[c]["raw"]), "residual": stat(by_cat[c]["residual"])}
            for c in ("monster", "item", "apparatus", "background") if by_cat[c]["raw"]},
        "auc_raw_fg_vs_bg": _auc(fg_raw, bg_raw),
        "auc_rawmotion_fg_vs_bg": _auc(fg_rawmot, bg_rawmot),
        "auc_residual_fg_vs_bg": _auc(fg_res, bg_res),
        "auc_raw_fg_vs_apparatus": _auc(fg_raw, app_raw),
        "auc_residual_fg_vs_apparatus": _auc(fg_res, app_res),
        "auc_raw_monster_vs_bg": _auc(mon_raw, bg_raw),
        "auc_residual_monster_vs_bg": _auc(mon_res, bg_res),
        "n_monster_tracks": len(mon_res),
        "salience_at_k_raw": topk_cats("raw"),
        "salience_at_k_residual": topk_cats("residual"),
    }


# ======================================================================
def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    result = {
        "block": 157000, "doom_seed": DOOM_SEED, "map": "E1M1",
        "grid": [GW, GH], "down": DOWN, "block_aperture": BLOCK, "level": LEVEL,
        "zero_floor": ZERO_FLOOR, "skill": SKILL,
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
    }

    print("== H1 synthetic (dominant-mode gain -> cancel -> residual salience) ==")
    result["H1"] = run_h1()
    h1 = result["H1"]
    for cov, r in h1["gain_recovery"].items():
        print(f"  [{cov}] true={r['true_egomotion']} mode={r['gain_mode']} "
              f"median_all={r['gain_median_all']} nz_frac={r['nonzero_fraction']}")
    p = h1["primary"]
    print(f"  PRIMARY raw AUC(fg>bg)={p['auc_raw_fg_vs_bg']} "
          f"rawmotion AUC={p['auc_rawmotion_fg_vs_bg']} "
          f"-> residual AUC(fg>bg)={p['auc_residual_fg_vs_bg']}")
    print(f"    mover rank (residual) = {p['mover_rank_residual']} "
          f"residual AUC(fg>apparatus)={p['auc_residual_fg_vs_apparatus']}")
    print(f"    raw sal: mover={p['raw_salience']['mover']} bg_max={p['raw_salience']['background_max']} "
          f"apparatus={p['raw_salience']['apparatus']}")
    print(f"    res sal: mover={p['residual_salience']['mover']} bg_max={p['residual_salience']['background_max']} "
          f"apparatus={p['residual_salience']['apparatus']}")
    for k in ("control_no_egomotion", "control_static_plus_egomotion",
              "control_mover_no_egomotion"):
        print(f"  [{k}] {h1[k]}")

    # ---- H2 E1M1 ----
    print("== H2 E1M1 (real WAD, 156000 walk/seed/grid) ==")
    frames = capture_e1m1()
    if not frames:
        result["H2_skipped"] = "vizdoom or DOOM.WAD absent"
        print("  SKIPPED:", result["H2_skipped"])
    else:
        result["H2_e1m1_frames"] = len(frames)
        h2 = run_h2(frames)
        result["H2"] = h2
        ec = h2["egomotion_capture"]
        print(f"  frames={h2['n_frames']} tracks={h2['n_tracks_scored']} "
              f"nz_flow={ec['nonzero_flow_fraction_mean']*100:.0f}%")
        print(f"  egomotion CAPTURED: mode nonzero in {ec['mode_nonzero_frames']}/"
              f"{ec['total_motion_frames']} frames vs median-all "
              f"{ec['median_all_nonzero_frames']}/{ec['total_motion_frames']}")
        print(f"  AUC fg-vs-bg: raw(W2)={h2['auc_raw_fg_vs_bg']} "
              f"rawmotion={h2['auc_rawmotion_fg_vs_bg']} "
              f"-> RESIDUAL={h2['auc_residual_fg_vs_bg']}  (156000 raw=0.588)")
        print(f"  AUC fg-vs-apparatus: raw={h2['auc_raw_fg_vs_apparatus']} "
              f"-> residual={h2['auc_residual_fg_vs_apparatus']}  (156000 raw=0.717)")
        print(f"  monster tracks={h2['n_monster_tracks']} "
              f"(0 => sub-pixel imp DEGRADE, 156000 wall)")
        print(f"  salience@k raw:      {h2['salience_at_k_raw']['5']}")
        print(f"  salience@k residual: {h2['salience_at_k_residual']['5']}")

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "residual_salience.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
