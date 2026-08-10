#!/usr/bin/env python3
"""E1M1 + SALIENCE WIRING PROBE (block 156000-156999).

A WIRING rung. No new perception mechanism — connect existing pieces and SCORE
them against VizDoom's labels-buffer ground truth. Pre-registration:
VISION_E1M1_SALIENCE_PREREG.md.

W1  Switch the Doom eye probe from the bundled `defend_the_center` scenario to
    the REAL map E1M1 (real DOOM.WAD, deterministic scripted walk). Carve from
    the RGB screen with the EXISTING `native.segment` value carve (via
    falling_world), score per-object IoU vs the downsampled labels buffer, and
    compare to `defend_the_center` at the identical grid.

W2  (HEADLINE) Wire the EXISTING salience signal —
    `substrate_rs._native.Substrate.shape_salience(seq) -> float`, the Rust
    `memory::order_n_shape_salience` operator the effort dial's
    `salience_threshold` consumes — to RANK the carved-region trajectories by
    surprise. Track regions across frames (mechanical nearest-overlap, no GT);
    each track's salience = max shape_salience over its centroid-x / centroid-y /
    area trajectories. Score whether salience ranks the GT foreground objects
    (live enemies + looming items) ABOVE the view-fixed apparatus and the static
    background (AUC, salience@k, per-category distributions).

W3  Re-run 155000's efference-copy egomotion cancellation on the E1M1 WALK.
    Textured corridors should make egomotion sensor-visible (nonzero flow, a
    coherent dominant vector) where `defend_the_center`'s bare arena gave gain
    (0,0). Report egomotion visibility + cancelled-vs-raw enemy IoU.

ARCHITECTURE (CLAUDE.md — the agent is Rust). No agent decision in Python. The
carve is the EXISTING Rust primitive; the salience is the EXISTING Rust operator
(a mechanical measurement over a trajectory the world adapter extracted, the peer
of `vector_field` / `quantize`); the tracker is a mechanical position
association; the scripted walk is a known world-adapter fact (a fixed action
sequence); the labels buffer is the SCORING ORACLE, never fed to the eye; scoring
is IoU by POSITION and salience ranking, never cross-process region-id. NO Rust
added, NO seed, NO default moved — new files only, so the shipped carve path is
byte-identical by construction.

Reuses the GATED primitives from scripts/eye_on_doom_probe.py (scorer, quantize,
downsample, value carve + region read-back) and scripts/efference_egomotion_probe.py
(efference_carve, calibrate_gain, raw_carve) so the carve/cancellation paths are
provably 152000-155000's.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.eye_on_doom_probe import (  # noqa: E402
    _block_mean, downsample_grey, downsample_labels, quantize, iou,
    run_value_carve, score_frame,
)
from scripts.efference_egomotion_probe import (  # noqa: E402
    calibrate_gain, efference_carve, raw_carve, best_iou_to,
)

# ---- DECLARED RESIDUALS (§13 — the sensor's aperture, NOT tuned to the score) --
WAD_DEFAULT = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"
DOOM_SEED = 156000        # block base => reproducible
DOWN = 2                  # ~2x downsample per the real-time ceiling => 120x160
GH, GW = 240 // DOWN, 320 // DOWN
BLOCK = max(1, 16 // DOWN)   # ~16 px physical flow aperture (as 153000): 8
LEVEL = 4                 # the eye's shipped quantization default
N_FRAMES = 160            # covers the imp sighting (f90-124) + looming items
SKILL = 3                 # Hurt Me Plenty (the default retail skill)
IOU_THRESHOLDS = (0.1, 0.25, 0.5)
KSWEEP = (1, 2, 3, 5, 8)  # salience@k report (no tuned threshold)

# GT object taxonomy on E1M1 (labels-buffer object_name).
MONSTER = {"DoomImp", "ZombieMan", "Zombieman", "ShotgunGuy", "ChaingunGuy",
           "Demon", "Spectre", "Cacodemon", "LostSoul", "BaronOfHell"}
# static world objects that LOOM as the agent approaches (pickups + decor + corpses)
ITEM = {"ExplosiveBarrel", "ArmorBonus", "HealthBonus", "GreenArmor", "BlueArmor",
        "DeadMarine", "GibbedMarine", "Gibs", "Column", "TechPillar", "Clip",
        "Shotgun", "Stimpack", "Medikit", "Backpack", "TechLamp"}
APPARATUS = {"DoomPlayer"}   # the marine's own weapon sprite / HUD, view-fixed


def _default_action_seq():
    """The FIXED deterministic scripted walk. Buttons = [forward, turn_left,
    turn_right]. Forward with a right-turn burst into the courtyard (tics 40-60)
    and a dwell scan (78-160) so a live DoomImp and the looming items enter view.
    A known world-adapter fact (the action sequence the agent issues), not a
    decision over graph state."""
    seq = []
    for i in range(N_FRAMES):
        if 40 <= i < 60:
            seq.append([1, 0, 1])            # forward + turn right: into courtyard
        elif 78 <= i < 86:
            seq.append([0, 0, 1])            # slow turn: hold the imp in view
        elif 86 <= i < 160 and (i // 6) % 2 == 0:
            seq.append([1, 0, 1])            # forward + scan-turn
        else:
            seq.append([1, 0, 0])            # forward
    return seq


# ======================================================================
#  E1M1 world adapter — mechanical I/O over the REAL WAD. Decides nothing.
# ======================================================================
def capture_e1m1(n_frames=N_FRAMES, seed=DOOM_SEED, wad=WAD_DEFAULT, skill=SKILL,
                 action_seq=None):
    """Drive E1M1 headless on the real WAD with a FIXED scripted walk; capture
    frame-aligned (rgb, labels_buf, depth, labels). Returns a list of frame
    dicts, or None if VizDoom or the (copyrighted, uncommitted) WAD is absent —
    the caller SKIPS explicitly, same pattern as the vizdoom-absent skip."""
    try:
        import vizdoom as vzd
    except Exception:
        return None
    if not os.path.exists(wad):
        return None
    if action_seq is None:
        action_seq = _default_action_seq()
    g = vzd.DoomGame()
    g.set_doom_game_path(wad)
    g.set_doom_scenario_path(wad)
    g.set_doom_map("E1M1")
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)
    g.set_labels_buffer_enabled(True)
    g.set_render_hud(True)
    g.set_render_weapon(True)
    g.set_window_visible(False)
    g.set_mode(vzd.Mode.PLAYER)
    g.set_doom_skill(skill)
    g.set_living_reward(0.0)
    g.set_death_penalty(0.0)
    for b in (vzd.Button.MOVE_FORWARD, vzd.Button.TURN_LEFT, vzd.Button.TURN_RIGHT):
        g.add_available_button(b)
    g.set_seed(seed)
    g.init()
    g.new_episode()
    frames = []
    for i in range(n_frames):
        if g.is_episode_finished() or g.is_player_dead():
            break
        st = g.get_state()
        if st is None:
            break
        frames.append({
            "rgb": np.array(st.screen_buffer, copy=True),
            "labels_buf": np.array(st.labels_buffer, copy=True),
            "depth": np.array(st.depth_buffer, copy=True),
            "labels": [{"object_id": int(l.object_id), "name": l.object_name,
                        "value": int(l.value)} for l in st.labels],
        })
        g.make_action(action_seq[i], 1)     # advance ONE tic; capture each frame
    g.close()
    return frames


def capture_defend(n_frames=N_FRAMES, seed=DOOM_SEED):
    """defend_the_center at the IDENTICAL grid, for the apples-to-apples W1
    comparison. Fixed turn action every tic (matches 152000's turning cond)."""
    try:
        import vizdoom as vzd
    except Exception:
        return None
    scen_dir = os.path.join(os.path.dirname(vzd.__file__), "scenarios")
    cfg = os.path.join(scen_dir, "defend_the_center.cfg")
    if not os.path.exists(cfg):
        return None
    g = vzd.DoomGame()
    g.load_config(cfg)
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)
    g.set_labels_buffer_enabled(True)
    g.set_window_visible(False)
    g.set_seed(seed)
    g.init()
    g.new_episode()
    buttons = g.get_available_buttons()
    act = [0] * len(buttons)
    if vzd.Button.TURN_RIGHT in buttons:
        act[buttons.index(vzd.Button.TURN_RIGHT)] = 1
    frames = []
    for _ in range(n_frames):
        if g.is_episode_finished() or g.is_player_dead():
            break
        st = g.get_state()
        if st is None:
            break
        frames.append({
            "rgb": np.array(st.screen_buffer, copy=True),
            "labels_buf": np.array(st.labels_buffer, copy=True),
            "labels": [{"object_id": int(l.object_id), "name": l.object_name,
                        "value": int(l.value)} for l in st.labels],
        })
        g.make_action(act, 1)
    g.close()
    return frames


# ======================================================================
#  GT category helpers (E1M1-aware; SCORING only, never fed to the eye)
# ======================================================================
def _value_category(labels):
    """label VALUE -> category string, from the frame's labels list."""
    out = {}
    for l in labels:
        nm = l["name"]
        if nm in APPARATUS:
            out[l["value"]] = "apparatus"
        elif nm in MONSTER:
            out[l["value"]] = "monster"
        elif nm in ITEM:
            out[l["value"]] = "item"
        else:
            out[l["value"]] = "other"     # unknown named actor -> its own bucket
    return out


def _cat_values(labels, cat):
    return {l["value"] for l in labels
            if _value_category(labels).get(l["value"]) == cat}


# ======================================================================
#  W1 — value carve scored vs the labels buffer
# ======================================================================
def _luma_stack(frames):
    return np.stack([downsample_grey(f["rgb"], GH, GW) for f in frames])


def w1_carve_score(frames, tag):
    """Value carve (existing native.segment, L=LEVEL) over the frames; per-object
    best IoU vs the modal-label grid, split by GT category. FP regions/frame +
    ms/frame. Mechanical scoring."""
    fq = quantize(_luma_stack(frames), LEVEL)
    per_frame, walls = run_value_carve(fq, GH, GW)
    gt_grids = [downsample_labels(f["labels_buf"], GH, GW) for f in frames]
    cat_ious = defaultdict(list)          # category -> list of best IoU
    recov = {c: {str(t): [] for t in IOU_THRESHOLDS}
             for c in ("monster", "item", "apparatus")}
    fp_per_frame, n_regions = [], []
    for fi, f in enumerate(frames):
        labels = f["labels"]
        gt = gt_grids[fi]
        carves = [c["cells"] for c in per_frame[fi]]
        n_regions.append(len(carves))
        obj_vals = (_cat_values(labels, "monster") | _cat_values(labels, "item")
                    | _cat_values(labels, "apparatus") | _cat_values(labels, "other"))
        sc = score_frame(carves, gt, object_values=obj_vals)
        v2c = _value_category(labels)
        for v, rec in sc["per_obj_best"].items():
            cat = v2c.get(v, "other")
            cat_ious[cat].append(rec["iou"])
            if cat in recov:
                for t in IOU_THRESHOLDS:
                    recov[cat][str(t)].append(1.0 if rec["iou"] >= t else 0.0)
        fp_per_frame.append(sc["false_positive_regions"][str(IOU_THRESHOLDS[0])])

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "max": float(np.max(xs)), "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "max": 0.0, "n": 0})
    return {
        "tag": tag, "n_frames": len(frames),
        "grid": [GW, GH], "level": LEVEL,
        "iou_by_category": {c: stat(cat_ious[c]) for c in cat_ious},
        "recovery": {c: {t: (float(np.mean(v)) if v else 0.0)
                         for t, v in recov[c].items()} for c in recov},
        "false_positive_regions_per_frame": stat([float(x) for x in fp_per_frame]),
        "n_regions_per_frame": stat([float(x) for x in n_regions]),
        "ms_per_frame": float(np.mean(walls) * 1e3) if walls else 0.0,
        "gt_frames_with_monster": sum(1 for f in frames
                                      if _cat_values(f["labels"], "monster")),
        "gt_frames_with_item": sum(1 for f in frames
                                   if _cat_values(f["labels"], "item")),
    }, per_frame, gt_grids


# ======================================================================
#  W2 — track regions (no GT) and rank by the EXISTING salience operator
# ======================================================================
def _region_centroid(cells):
    if not cells:
        return (0.0, 0.0)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return (float(np.mean(rs)), float(np.mean(cs)))


def _collect_tracks(per_frame, max_gap=6.0):
    """Greedy nearest-overlap tracker (mechanical, NO GT). Link each frame's
    carved region to the active track it most overlaps (cell IoU), else the
    nearest centroid within `max_gap` cells, else start a new track. Retains
    ALL tracks ever created; each track is {last_cells, last_cf, pts:[{frame,
    cells, cy, cx, area}]}."""
    all_tracks = []
    active = []
    for fi, regs in enumerate(per_frame):
        recs = [{"cells": set(r["cells"]), "cf": _region_centroid(r["cells"]),
                 "area": len(r["cells"])} for r in regs if r["cells"]]
        used = set()
        still = []
        for tr in active:
            best_j, best_score = -1, 0.0
            for j, rc in enumerate(recs):
                if j in used:
                    continue
                inter = len(tr["last_cells"] & rc["cells"])
                un = len(tr["last_cells"] | rc["cells"])
                j_iou = inter / un if un else 0.0
                if j_iou > best_score:
                    best_score, best_j = j_iou, j
            if best_j < 0:
                bd = None
                for j, rc in enumerate(recs):
                    if j in used:
                        continue
                    d = ((tr["last_cf"][0] - rc["cf"][0]) ** 2
                         + (tr["last_cf"][1] - rc["cf"][1]) ** 2) ** 0.5
                    if d <= max_gap and (bd is None or d < bd):
                        bd, best_j = d, j
            if best_j >= 0:
                rc = recs[best_j]
                used.add(best_j)
                tr["last_cells"] = rc["cells"]
                tr["last_cf"] = rc["cf"]
                tr["pts"].append({"frame": fi, "cells": frozenset(rc["cells"]),
                                  "cy": rc["cf"][0], "cx": rc["cf"][1],
                                  "area": rc["area"]})
                still.append(tr)
            # tracks that failed to link this frame END here (dropped from active)
            else:
                all_tracks.append(tr)
        for j, rc in enumerate(recs):
            if j in used:
                continue
            still.append({"last_cells": rc["cells"], "last_cf": rc["cf"],
                          "pts": [{"frame": fi, "cells": frozenset(rc["cells"]),
                                   "cy": rc["cf"][0], "cx": rc["cf"][1],
                                   "area": rc["area"]}]})
        active = still
    all_tracks.extend(active)
    return all_tracks


def track_salience(track, native_substrate):
    """The WIRING: a track's salience = max shape_salience over its centroid-x /
    centroid-y / area trajectories, using the EXISTING Rust operator. Directed /
    looming / moving -> high; view-fixed / flat -> 0 (by the operator's own
    construction). No re-implementation."""
    pts = track["pts"]
    if len(pts) < 3:
        return 0.0, {"cx": 0.0, "cy": 0.0, "area": 0.0, "len": len(pts)}
    cx = [p["cx"] for p in pts]
    cy = [p["cy"] for p in pts]
    ar = [float(p["area"]) for p in pts]
    s_cx = native_substrate.shape_salience(cx)
    s_cy = native_substrate.shape_salience(cy)
    s_ar = native_substrate.shape_salience(ar)
    return max(s_cx, s_cy, s_ar), {"cx": s_cx, "cy": s_cy, "area": s_ar,
                                   "len": len(pts)}


def _track_gt_category(track, gt_grids, frames):
    """Attribute a track to a GT category by the plurality GT label of its cells
    across its frames (SCORING only). Background = value 0/1 / no object."""
    counts = defaultdict(int)
    total = 0
    for p in track["pts"]:
        gt = gt_grids[p["frame"]]
        v2c = _value_category(frames[p["frame"]]["labels"])
        for (r, c) in p["cells"]:
            v = int(gt[r, c])
            total += 1
            cat = v2c.get(v)
            if cat in ("monster", "item", "apparatus", "other"):
                counts[cat] += 1
            else:
                counts["background"] += 1
    if not counts:
        return "background"
    # a track is a foreground object if a non-background category owns a
    # plurality of its object-labelled cells; else background.
    fg = {k: v for k, v in counts.items() if k != "background"}
    if fg and max(fg.values()) >= 0.15 * total:
        return max(fg, key=fg.get)
    return "background"


def _auc(pos, neg):
    """Mann-Whitney AUC of `pos` scores over `neg` scores (0.5 = no separation)."""
    if not pos or not neg:
        return None
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else (0.5 if p == n else 0.0)
    return wins / (len(pos) * len(neg))


def w2_salience_ranking(per_frame, gt_grids, frames, native_substrate):
    """Track carved regions, rank by the existing salience operator, score vs GT."""
    tracks = _collect_tracks(per_frame)
    tracks = [t for t in tracks if len(t["pts"]) >= 3]      # need a trajectory
    scored = []
    for t in tracks:
        sal, comp = track_salience(t, native_substrate)
        cat = _track_gt_category(t, gt_grids, frames)
        scored.append({"salience": float(sal), "category": cat,
                       "len": len(t["pts"]), "components": comp,
                       "mean_area": float(np.mean([p["area"] for p in t["pts"]]))})
    by_cat = defaultdict(list)
    for s in scored:
        by_cat[s["category"]].append(s["salience"])

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "max": float(np.max(xs)), "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "max": 0.0, "n": 0})

    fg = [s["salience"] for s in scored if s["category"] in ("monster", "item")]
    mon = [s["salience"] for s in scored if s["category"] == "monster"]
    app = [s["salience"] for s in scored if s["category"] == "apparatus"]
    bg = [s["salience"] for s in scored if s["category"] == "background"]

    # salience@k: fraction of GT foreground categories PRESENT whose best track
    # is within the top-K most-salient tracks, swept k.
    order = sorted(range(len(scored)), key=lambda i: -scored[i]["salience"])
    fg_cats_present = {s["category"] for s in scored
                       if s["category"] in ("monster", "item")}
    sal_at_k = {}
    for k in KSWEEP:
        topk = set(order[:k])
        hit_cats = {scored[i]["category"] for i in topk
                    if scored[i]["category"] in ("monster", "item")}
        sal_at_k[str(k)] = {
            "foreground_categories_in_topk": sorted(hit_cats),
            "n_foreground_categories_present": len(fg_cats_present),
            "topk_categories": [scored[i]["category"] for i in order[:k]],
            "topk_salience": [round(scored[i]["salience"], 4) for i in order[:k]],
        }

    from substrate_rs import _native as _n
    dial = _n.EffortDial()
    thr = dial.salience_threshold()
    above = {c: (float(np.mean([1.0 if x > thr else 0.0 for x in by_cat[c]]))
                 if by_cat[c] else 0.0) for c in by_cat}

    return {
        "n_tracks_scored": len(scored),
        "salience_by_category": {c: stat(by_cat[c]) for c in by_cat},
        "auc_foreground_vs_apparatus": _auc(fg, app),
        "auc_foreground_vs_background": _auc(fg, bg),
        "auc_monster_vs_background": _auc(mon, bg),
        "auc_monster_vs_apparatus": _auc(mon, app),
        "salience_at_k": sal_at_k,
        "effort_dial_salience_threshold": thr,
        "fraction_above_effort_dial_threshold": above,
        "top_tracks": [
            {"salience": round(scored[i]["salience"], 4),
             "category": scored[i]["category"], "len": scored[i]["len"],
             "mean_area": round(scored[i]["mean_area"], 2),
             "components": {k: round(v, 4) for k, v in scored[i]["components"].items()}}
            for i in order[:12]],
    }


# ======================================================================
#  W3 — efference-copy egomotion cancellation on the E1M1 walk
# ======================================================================
def _e1m1_flow_fields(frames):
    """Per-frame observed flow (vy, vx) on quantized luma + GT monster cell-sets.
    Identical pipeline to 155000, E1M1 monster taxonomy."""
    from domains.motion_group_world import vector_field
    fq = quantize(_luma_stack(frames), LEVEL)
    gt_grids = [downsample_labels(f["labels_buf"], GH, GW) for f in frames]
    fields, gts = [], []
    prev = None
    for fi in range(len(frames)):
        cur = fq[fi].astype(np.float64)
        if prev is None:
            vy = np.zeros((GH, GW)); vx = np.zeros((GH, GW))
        else:
            vf = vector_field(prev, cur, block=BLOCK)
            vy = np.repeat(np.repeat(vf[:, :, 0], BLOCK, 0), BLOCK, 1)[:GH, :GW]
            vx = np.repeat(np.repeat(vf[:, :, 1], BLOCK, 0), BLOCK, 1)[:GH, :GW]
            fy = np.zeros((GH, GW)); fx = np.zeros((GH, GW))
            fy[:vy.shape[0], :vy.shape[1]] = vy
            fx[:vx.shape[0], :vx.shape[1]] = vx
            vy, vx = fy, fx
        prev = cur
        mon = _cat_values(frames[fi]["labels"], "monster")
        gt = gt_grids[fi]
        gt_mon = frozenset((int(r), int(c)) for v in mon
                           for r, c in zip(*np.where(gt == v)))
        fields.append((vy, vx))
        gts.append({"monster": gt_mon, "present": bool(mon)})
    return fields, gts


def w3_egomotion(frames):
    fields, gts = _e1m1_flow_fields(frames)
    gain = calibrate_gain(fields[1:])       # from the walk's OWN flow
    # egomotion visibility
    nz_fracs, dom_vy, dom_vx = [], [], []
    for (vy, vx) in fields[1:]:
        mag = np.sqrt(np.asarray(vy) ** 2 + np.asarray(vx) ** 2)
        nz = mag > 0.5
        nz_fracs.append(float(nz.mean()))
        if nz.any():
            dom_vy.append(float(np.median(np.asarray(vy)[nz])))
            dom_vx.append(float(np.median(np.asarray(vx)[nz])))
    raw_ious, eff_ious, per_frame = [], [], []
    present = 0
    for fi in range(len(frames)):
        if gts[fi]["present"]:
            present += 1
        gt_mon = gts[fi]["monster"]
        if not gt_mon:
            continue
        vy, vx = fields[fi]
        raw = raw_carve(vy, vx, GH, GW)
        eff, app_cells, ry, rx = efference_carve(vy, vx, gain, GH, GW)
        r_iou = best_iou_to(raw, gt_mon)
        e_iou = best_iou_to(eff, gt_mon)
        raw_ious.append(r_iou); eff_ious.append(e_iou)
        per_frame.append({"frame": fi, "raw_iou": round(r_iou, 4),
                          "eff_iou": round(e_iou, 4), "monster_cells": len(gt_mon)})

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "max": float(np.max(xs)), "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "max": 0.0, "n": 0})
    return {
        "grid": [GW, GH], "block": BLOCK,
        "calibrated_gain": [round(v, 4) for v in gain],
        "egomotion_visibility": {
            "nonzero_flow_fraction_mean": float(np.mean(nz_fracs)) if nz_fracs else 0.0,
            "dominant_moving_flow_median": [
                float(np.median(dom_vy)) if dom_vy else 0.0,
                float(np.median(dom_vx)) if dom_vx else 0.0]},
        "monster_present_frames": present,
        "raw_monster_iou": stat(raw_ious),
        "efference_monster_iou": stat(eff_ious),
        "raw_monster_iou_dist": [round(x, 4) for x in raw_ious],
        "efference_monster_iou_dist": [round(x, 4) for x in eff_ious],
        "per_frame": per_frame,
    }


# ======================================================================
def _save_png(frames, per_frame, gt_grids, w2, out_dir):
    """One representative triptych: RGB | GT labels | carve (salience-shaded)."""
    try:
        from PIL import Image
    except Exception:
        return None
    # pick the frame with the largest monster GT area, else largest item area
    best_fi, best_area = 0, -1
    for i, f in enumerate(frames):
        gt = gt_grids[i]
        mon = _cat_values(f["labels"], "monster") or _cat_values(f["labels"], "item")
        area = sum(int((gt == v).sum()) for v in mon)
        if area > best_area:
            best_fi, best_area = i, area
    fi = best_fi
    rgb = frames[fi]["rgb"]
    if rgb.ndim == 3 and rgb.shape[0] == 3:
        rgb = np.transpose(rgb, (1, 2, 0))
    gt = gt_grids[fi]
    gt_img = np.zeros((GH, GW, 3), dtype=np.uint8)
    for v in np.unique(gt):
        if v == 0:
            continue
        gt_img[gt == v] = (int(v) % 256, (255 - int(v)) % 256, 128)
    carve_img = np.zeros((GH, GW, 3), dtype=np.uint8)
    palette = [(230, 60, 60), (60, 200, 60), (60, 120, 240), (240, 200, 40),
               (200, 60, 220), (40, 220, 220), (240, 140, 40), (140, 90, 240)]
    for k, c in enumerate(per_frame[fi]):
        col = palette[k % len(palette)]
        for (r, cc) in c["cells"]:
            carve_img[r, cc] = col
    scale = 3
    def up(a):
        return Image.fromarray(a).resize((GW * scale, GH * scale), Image.NEAREST)
    strip = Image.new("RGB", (GW * scale * 3 + 16, GH * scale), (20, 20, 20))
    strip.paste(Image.fromarray(rgb).resize((GW * scale, GH * scale), Image.NEAREST), (0, 0))
    strip.paste(up(gt_img), (GW * scale + 8, 0))
    strip.paste(up(carve_img), (2 * (GW * scale + 8), 0))
    path = os.path.join(out_dir, f"e1m1_salience_f{fi}.png")
    strip.save(path)
    return os.path.basename(path)


def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    from substrate_rs import _native as native
    load0 = os.getloadavg()

    result = {
        "block": 156000, "doom_seed": DOOM_SEED, "map": "E1M1",
        "grid": [GW, GH], "down": DOWN, "block_aperture": BLOCK, "level": LEVEL,
        "n_frames_cap": N_FRAMES, "skill": SKILL,
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
        "engine_provenance": provenance_stamp(strict=False),
    }

    frames = capture_e1m1()
    if not frames:
        result["skipped"] = "vizdoom or DOOM.WAD absent"
        out = os.path.join(ROOT, "results", "e1m1_salience.json")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as fh:
            json.dump(result, fh, indent=2)
        print("SKIPPED:", result["skipped"], "-> wrote", out)
        return result
    result["e1m1_frames_captured"] = len(frames)

    # ---- W1: E1M1 carve, scored vs labels buffer ----
    print("== W1: E1M1 value carve vs labels buffer ==")
    w1_e1m1, per_frame, gt_grids = w1_carve_score(frames, "e1m1")
    result["W1_e1m1"] = w1_e1m1
    print(f"  frames={w1_e1m1['n_frames']} monster_frames={w1_e1m1['gt_frames_with_monster']} "
          f"item_frames={w1_e1m1['gt_frames_with_item']}")
    for c in ("monster", "item", "apparatus"):
        s = w1_e1m1["iou_by_category"].get(c)
        if s:
            print(f"  IoU[{c:9s}] mean={s['mean']:.3f} med={s['median']:.3f} n={s['n']}")
    print(f"  fp_regions/frame={w1_e1m1['false_positive_regions_per_frame']['mean']:.1f} "
          f"n_regions/frame={w1_e1m1['n_regions_per_frame']['mean']:.1f} "
          f"ms/frame={w1_e1m1['ms_per_frame']:.1f}")

    # defend_the_center at the identical grid (apples-to-apples)
    dframes = capture_defend()
    if dframes:
        w1_def, _, _ = w1_carve_score(dframes, "defend_the_center")
        result["W1_defend_same_grid"] = w1_def
        se = w1_e1m1["iou_by_category"].get("monster", {"mean": 0.0})
        sd = w1_def["iou_by_category"].get("monster", {"mean": 0.0})
        print(f"  [defend_the_center same grid] monster IoU mean={sd['mean']:.3f} "
              f"fp/frame={w1_def['false_positive_regions_per_frame']['mean']:.1f} "
              f"(E1M1 monster IoU mean={se['mean']:.3f})")

    # ---- W2: salience ranking (HEADLINE) ----
    print("== W2: salience ranks carved-region trajectories (HEADLINE) ==")
    w2 = w2_salience_ranking(per_frame, gt_grids, frames, native.Substrate)
    result["W2_salience"] = w2
    print(f"  tracks scored={w2['n_tracks_scored']}")
    for c in ("monster", "item", "apparatus", "background"):
        s = w2["salience_by_category"].get(c)
        if s:
            print(f"  salience[{c:10s}] mean={s['mean']:.3f} med={s['median']:.3f} "
                  f"max={s['max']:.3f} n={s['n']}")
    print(f"  AUC foreground-vs-apparatus = {w2['auc_foreground_vs_apparatus']}")
    print(f"  AUC foreground-vs-background = {w2['auc_foreground_vs_background']}")
    print(f"  AUC monster-vs-background   = {w2['auc_monster_vs_background']}")
    print(f"  top-5 tracks (salience,cat): "
          f"{[(t['salience'], t['category']) for t in w2['top_tracks'][:5]]}")

    # ---- W3: egomotion cancellation on the textured walk ----
    print("== W3: efference-copy egomotion cancellation on E1M1 walk ==")
    w3 = w3_egomotion(frames)
    result["W3_egomotion"] = w3
    ev = w3["egomotion_visibility"]
    print(f"  calibrated gain={w3['calibrated_gain']} "
          f"nonzero-flow={ev['nonzero_flow_fraction_mean']*100:.0f}% "
          f"dominant-flow={ev['dominant_moving_flow_median']}")
    print(f"  monster present frames={w3['monster_present_frames']} "
          f"raw IoU mean={w3['raw_monster_iou']['mean']:.4f} (n={w3['raw_monster_iou']['n']}) "
          f"-> efference IoU mean={w3['efference_monster_iou']['mean']:.4f}")

    img_dir = os.path.join(ROOT, "results", "e1m1_salience_imgs")
    os.makedirs(img_dir, exist_ok=True)
    result["png"] = _save_png(frames, per_frame, gt_grids, w2, img_dir)

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "e1m1_salience.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
