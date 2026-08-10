#!/usr/bin/env python3
"""EYE-ON-DOOM PROBE (block 152000-152999) — point the eye at Doom RGB pixels
and SCORE its carve against VizDoom's per-pixel labels-buffer GROUND TRUTH.

Pre-registration: VISION_EYE_ON_DOOM_PREREG.md. Honest exploratory PROBE, NO
CONFIRM target (like the first real-video probe, 143000) — the deliverable is a
ground-truth-scored baseline + the precisely isolated wall, not a pass/fail.

Everything here is MECHANICAL I/O:

  * a VizDoom world adapter (defend_the_center, headless, fixed seed + fixed
    action sequence) hands the eye raw RGB / depth pixels and, FRAME-ALIGNED,
    the labels buffer + labels list as the SCORING ORACLE (never fed to the
    eye);
  * the carve is the EXISTING Rust primitive (`native.segment` value-carve and
    `native.segment_motion` common-fate-carve, via `falling_world`), byte for
    byte the shipped eye;
  * scoring is pure set arithmetic (per-object IoU / precision / recall /
    false-positive regions) against the downsampled labels buffer.

No agent decision in Python; no Rust change; no seed. The carve regions are read
back from the graph via `within` edges (cell -within-> Region) and scored by
POSITION (IoU), never by cross-process region-id identity (§ discipline 5).

The SCORER functions (downsample_*, quantize, iou, score_frame) are importable
and gated on a CONSTRUCTED synthetic case in
tests/test_eye_on_doom_migrated.py.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---- DECLARED RESIDUALS (§13 — grid / block / L / seed are NOT tuned to the
#      score; they are the sensor's aperture, stated up front) ---------------
GH, GW = 60, 80          # grid rows x cols = exact 4x downsample of 240x320
DOWN = 4                 # 240/60 = 320/80 = 4 : area-mean downsample factor
BLOCK = 4                # vector_field aperture (nh=15, nw=20); a §13 residual
LEVELS = (4, 8)          # L=4 is the eye's shipped default; L=8 reported too
DOOM_SEED = 152000       # tie to the claim block base; fixed => reproducible
N_FRAMES = 60            # capture up to this many tics, or until episode ends
SCEN = "defend_the_center"
IOU_THRESHOLDS = (0.1, 0.25, 0.5)   # recovery reported at several; raw dist too


# ======================================================================
#  SCORER — pure, importable, gated on a synthetic constructed case
# ======================================================================
def downsample_grey(rgb, gh, gw):
    """RGB (H,W,3) uint8 -> luma grid (gh,gw) uint8 by area-mean over blocks.
    Luma = ITU-R 601 (0.299R+0.587G+0.114B). Mechanical, no decision."""
    rgb = np.asarray(rgb)
    if rgb.ndim == 3 and rgb.shape[0] == 3:      # (3,H,W) -> (H,W,3)
        rgb = np.transpose(rgb, (1, 2, 0))
    H, W = rgb.shape[:2]
    luma = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1]
            + 0.114 * rgb[..., 2]).astype(np.float64)
    return _block_mean(luma, gh, gw).astype(np.uint8)


def downsample_scalar(buf, gh, gw):
    """A single-channel buffer (depth) -> grid by area-mean."""
    return _block_mean(np.asarray(buf, dtype=np.float64), gh, gw).astype(np.uint8)


def _block_mean(a, gh, gw):
    H, W = a.shape
    bh, bw = H // gh, W // gw
    a = a[:gh * bh, :gw * bw].reshape(gh, bh, gw, bw)
    return a.mean(axis=(1, 3))


def downsample_labels(labels_buf, gh, gw):
    """Per-pixel object-id mask -> per-cell MODAL label value grid (gh,gw).
    A cell owns the object that owns the plurality of its pixels (ties -> the
    lower value, deterministic). 0 = background."""
    lab = np.asarray(labels_buf)
    H, W = lab.shape
    bh, bw = H // gh, W // gw
    out = np.zeros((gh, gw), dtype=np.int64)
    lab = lab[:gh * bh, :gw * bw]
    for r in range(gh):
        for c in range(gw):
            block = lab[r * bh:(r + 1) * bh, c * bw:(c + 1) * bw].reshape(-1)
            vals, cnts = np.unique(block, return_counts=True)
            # plurality; tie -> lower value (argmax picks first on tie after sort)
            order = np.lexsort((vals, -cnts))
            out[r, c] = int(vals[order[0]])
    return out


def quantize(luma_u8, L):
    """The eye's native scheme: v = (luma * L) // 256 -> L distinct levels."""
    return ((np.asarray(luma_u8).astype(np.int32) * L) // 256)


def iou(a, b):
    """Jaccard IoU of two cell-sets (frozensets of (r,c))."""
    a, b = set(a), set(b)
    if not a and not b:
        return 0.0
    u = len(a | b)
    return (len(a & b) / u) if u else 0.0


def gt_object_cells(gt_grid, object_values=None):
    """{label_value: frozenset((r,c))} for GT objects.

    object_values : if given, ONLY these label values are GT objects (all other
    cells, including the value-1/0 WORLD GEOMETRY VizDoom writes for floor and
    walls, are background). If None, every non-zero value is an object (used by
    the synthetic scorer gate)."""
    out = {}
    for v in np.unique(gt_grid):
        v = int(v)
        if v == 0:
            continue
        if object_values is not None and v not in object_values:
            continue
        cells = frozenset((int(r), int(c))
                          for r, c in zip(*np.where(gt_grid == v)))
        out[v] = cells
    return out


def score_frame(carve_cellsets, gt_grid, iou_thresholds=IOU_THRESHOLDS,
                object_values=None):
    """Score one frame's carve against the labels grid.

    carve_cellsets : list of frozenset((r,c)) — the NON-GROUND carved regions.
    gt_grid        : (gh,gw) modal-label grid (0 = background).

    Returns a dict with, per GT object value: best IoU over carved regions;
    and frame-level precision/recall of GT objects at each IoU threshold, plus
    the count of carved regions that match NO GT object (false positives)."""
    gt = gt_object_cells(gt_grid, object_values)
    per_obj_best = {}
    matched_carves = defaultdict(set)   # threshold -> set(carve idx that matched some GT)
    for v, cells in gt.items():
        best, best_i = 0.0, -1
        for i, cs in enumerate(carve_cellsets):
            j = iou(cells, cs)
            if j > best:
                best, best_i = j, i
        per_obj_best[v] = {"iou": best, "carve_idx": best_i,
                           "gt_area_cells": len(cells)}
        for t in iou_thresholds:
            if best >= t and best_i >= 0:
                matched_carves[t].add(best_i)
    n_gt = len(gt)
    n_carve = len(carve_cellsets)
    out = {"per_obj_best": per_obj_best, "n_gt": n_gt, "n_carve": n_carve,
           "recovery": {}, "precision": {}, "false_positive_regions": {}}
    for t in iou_thresholds:
        recovered = sum(1 for v in gt if per_obj_best[v]["iou"] >= t)
        out["recovery"][str(t)] = recovered / n_gt if n_gt else 0.0
        # a carve region is a false positive at t if it matched no GT object
        fp = n_carve - len(matched_carves[t])
        out["false_positive_regions"][str(t)] = fp
        out["precision"][str(t)] = (len(matched_carves[t]) / n_carve) if n_carve else 0.0
    return out


# ======================================================================
#  CARVE DRIVER — reads regions back from the graph as cell-sets
# ======================================================================
def _region_cell_sets(native, game, id2idx, gw, *, only_nonground=True):
    """Read carved Region nodes back out as (attrs, frozenset((r,c))) via the
    `within` edges the carve wrote (cell -within-> Region). POSITION-anchored;
    region node-id is used ONLY as this-frame handle."""
    out = []
    for rn in native.neighbours(game, "has_region"):
        a = native.node(rn)["attrs"]
        is_ground = float(a.get("is_ground", 0.0))
        if only_nonground and is_ground == 1.0:
            continue
        cells = set()
        for cn in native.in_neighbours(rn, "within"):
            cid = int(str(cn).lstrip("#"))
            if cid in id2idx:
                idx = id2idx[cid]
                cells.add((idx // gw, idx % gw))
        out.append({
            "rid": int(str(rn).lstrip("#")),
            "is_ground": is_ground,
            "count": float(a.get("count", 0.0)),
            "cy": float(a.get("cy", 0.0)),
            "cx": float(a.get("cx", 0.0)),
            "cells": frozenset(cells),
        })
    return out


def run_value_carve(frames_q, gh, gw):
    """Drive the VALUE carve (`native.segment`) over quantized-luma frames.
    Returns per-frame list of region records (with cell-sets) + wall times."""
    from domains import falling_world as fw
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    id2idx = {cid: i for i, cid in enumerate(cell_ids)}
    per_frame, walls = [], []
    for fi in range(frames_q.shape[0]):
        vals = frames_q[fi].reshape(-1).tolist()
        t0 = time.perf_counter()
        native.set_attr(game, "frame", float(fi))
        native.segment(game, gh, gw, vals, cell_ids)
        regs = _region_cell_sets(native, game, id2idx, gw)
        walls.append(time.perf_counter() - t0)
        per_frame.append(regs)
    return per_frame, walls


def run_motion_carve(frames_q, gh, gw, block):
    """Drive the COMMON-FATE carve (`native.segment_motion`): per-cell flow from
    `vector_field` between consecutive quantized-luma frames, upsampled to the
    grid. Frame 0 has no predecessor -> zero field."""
    from domains import falling_world as fw
    from domains.motion_group_world import vector_field
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, gh, gw)
    id2idx = {cid: i for i, cid in enumerate(cell_ids)}
    per_frame, walls = [], []
    prev = None
    for fi in range(frames_q.shape[0]):
        cur = frames_q[fi].astype(np.float64)
        if prev is None:
            vy = np.zeros((gh, gw)); vx = np.zeros((gh, gw))
        else:
            vf = vector_field(prev, cur, block=block)       # (nh,nw,2)
            vy = np.repeat(np.repeat(vf[:, :, 0], block, 0), block, 1)
            vx = np.repeat(np.repeat(vf[:, :, 1], block, 0), block, 1)
            fy = np.zeros((gh, gw)); fx = np.zeros((gh, gw))
            fy[:vy.shape[0], :vy.shape[1]] = vy[:gh, :gw]
            fx[:vx.shape[0], :vx.shape[1]] = vx[:gh, :gw]
            vy, vx = fy, fx
        t0 = time.perf_counter()
        native.set_attr(game, "frame", float(fi))
        native.segment_motion(game, gh, gw,
                              vy.reshape(-1).tolist(), vx.reshape(-1).tolist(),
                              cell_ids)
        regs = _region_cell_sets(native, game, id2idx, gw)
        walls.append(time.perf_counter() - t0)
        per_frame.append(regs)
        prev = cur
    return per_frame, walls


# ======================================================================
#  VizDoom world adapter — mechanical I/O, decides nothing
# ======================================================================
def capture_doom(action_name, n_frames=N_FRAMES, seed=DOOM_SEED):
    """Drive defend_the_center headless with a FIXED action every tic; capture
    frame-aligned (rgb, labels_buffer, depth_buffer, labels-list). Returns a
    list of frame dicts. Pure world-adapter I/O."""
    import vizdoom as vzd
    scen_dir = os.path.join(os.path.dirname(vzd.__file__), "scenarios")
    g = vzd.DoomGame()
    g.load_config(os.path.join(scen_dir, f"{SCEN}.cfg"))
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)
    g.set_labels_buffer_enabled(True)
    g.set_window_visible(False)
    g.set_seed(seed)
    g.init()
    g.new_episode()
    buttons = g.get_available_buttons()
    # button vector for the requested fixed action
    act = [0] * len(buttons)
    name2btn = {"turn_left": vzd.Button.TURN_LEFT,
                "turn_right": vzd.Button.TURN_RIGHT,
                "attack": vzd.Button.ATTACK}
    if action_name in name2btn and name2btn[action_name] in buttons:
        act[buttons.index(name2btn[action_name])] = 1
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
            "depth": np.array(st.depth_buffer, copy=True),
            "labels": [{"object_id": int(l.object_id), "name": l.object_name,
                        "value": int(l.value)} for l in st.labels],
        })
        g.make_action(act, 1)      # advance ONE tic so we capture each frame
    g.close()
    return frames


# ======================================================================
#  ANALYSIS — GT-anchored carve + tracking + wall isolation
# ======================================================================
def _enemy_values(labels):
    """label VALUES that are enemies (monsters) — NOT DoomPlayer (self/weapon
    sprite) and NOT background."""
    return {l["value"] for l in labels if l["name"] != "DoomPlayer"}


def _player_values(labels):
    return {l["value"] for l in labels if l["name"] == "DoomPlayer"}


def _value_to_objid(labels):
    return {l["value"]: l["object_id"] for l in labels}


def analyse_run(frames, carve_per_frame, gt_grids, label_lists, tag):
    """Score a carve mode over a run. Enemy-focused IoU/precision/recall,
    tracking persistence & fragmentation (GT-object-anchored), and the wall
    diagnostics (weapon-sprite false object, background over-segmentation)."""
    n = len(frames)
    enemy_ious, weapon_ious = [], []
    recovery = {str(t): [] for t in IOU_THRESHOLDS}
    n_nonground, n_fp = [], []
    # GT object_id -> list of (frame, best carve rid, best iou) for enemies
    track = defaultdict(list)
    for fi in range(n):
        gt = gt_grids[fi]
        labels = label_lists[fi]
        carves = carve_per_frame[fi]
        carve_sets = [c["cells"] for c in carves]
        n_nonground.append(len(carves))
        enemy_vals = _enemy_values(labels)
        player_vals = _player_values(labels)
        v2o = _value_to_objid(labels)
        # GT OBJECTS = named actors only (enemies + weapon/DoomPlayer); the
        # value-0/1 world geometry is background, so a carve on the floor is a
        # FALSE POSITIVE (background/texture over-seg), not a "matched object".
        sc = score_frame(carve_sets, gt, object_values=(enemy_vals | player_vals))
        # enemy IoU (best carve per enemy GT object)
        for v in enemy_vals:
            if v in sc["per_obj_best"]:
                b = sc["per_obj_best"][v]
                enemy_ious.append(b["iou"])
                for t in IOU_THRESHOLDS:
                    recovery[str(t)].append(1.0 if b["iou"] >= t else 0.0)
                track[v2o.get(v, v)].append((fi, b["carve_idx"], b["iou"],
                                             b["gt_area_cells"]))
        # weapon-sprite (DoomPlayer) IoU — the HUD/weapon false-object probe
        for v in player_vals:
            if v in sc["per_obj_best"]:
                weapon_ious.append(sc["per_obj_best"][v]["iou"])
        # false positives at the loosest threshold (background over-seg)
        n_fp.append(sc["false_positive_regions"][str(IOU_THRESHOLDS[0])])

    # tracking persistence / fragmentation per GT enemy object_id
    persist_pairs, same_id_pairs = 0, 0
    frag_counts = []
    for objid, seq in track.items():
        seq = [s for s in seq if s[1] >= 0]     # frames where a carve overlapped
        if len(seq) < 2:
            continue
        # carve rids overlapping this GT object across its lifetime
        rids = [carve_per_frame[fi][ci]["rid"] for (fi, ci, _, _) in seq]
        frag_counts.append(len(set(rids)))
        for (a, b) in zip(seq, seq[1:]):
            if b[0] == a[0] + 1:                # consecutive frames
                persist_pairs += 1
                ra = carve_per_frame[a[0]][a[1]]["rid"]
                rb = carve_per_frame[b[0]][b[1]]["rid"]
                if ra == rb:
                    same_id_pairs += 1

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "min": float(np.min(xs)), "max": float(np.max(xs)), "n": len(xs)}
                if xs else {"mean": 0.0, "median": 0.0, "min": 0.0,
                            "max": 0.0, "n": 0})

    return {
        "tag": tag, "n_frames": n,
        "enemy_iou": stat(enemy_ious),
        "enemy_iou_raw": [round(x, 4) for x in enemy_ious],
        "enemy_recovery": {t: float(np.mean(v)) if v else 0.0
                           for t, v in recovery.items()},
        "weapon_sprite_iou": stat(weapon_ious),
        "n_nonground_regions": stat([float(x) for x in n_nonground]),
        "false_positive_regions": stat([float(x) for x in n_fp]),
        "tracking_persistence_same_id_rate":
            (same_id_pairs / persist_pairs) if persist_pairs else 0.0,
        "tracking_persist_pairs": persist_pairs,
        "tracking_fragmentation_mean":
            float(np.mean(frag_counts)) if frag_counts else 0.0,
        "tracking_fragmentation_max":
            int(np.max(frag_counts)) if frag_counts else 0,
        "n_gt_enemy_tracks": len(frag_counts),
    }


def _iou_vs_size(frames, carve_per_frame, gt_grids, label_lists):
    """The small/distant-enemy wall: enemy IoU as a function of GT enemy area
    (in grid cells). Returns list of (gt_area_cells, iou)."""
    pts = []
    for fi in range(len(frames)):
        gt = gt_grids[fi]
        carves = [c["cells"] for c in carve_per_frame[fi]]
        ev = _enemy_values(label_lists[fi])
        sc = score_frame(carves, gt, object_values=(ev | _player_values(label_lists[fi])))
        for v in ev:
            if v in sc["per_obj_best"]:
                b = sc["per_obj_best"][v]
                pts.append((b["gt_area_cells"], round(b["iou"], 4)))
    return pts


# ======================================================================
def _save_pngs(frames, carve_per_frame, gt_grids, out_dir, tag, fi=None):
    """Small representative triptych: RGB frame | labels buffer | eye carve."""
    try:
        from PIL import Image
    except Exception:
        return None
    n = len(frames)
    if n == 0:
        return None
    if fi is None:
        # pick the frame with the largest enemy GT area (most to carve)
        best_fi, best_area = 0, -1
        for i in range(n):
            gt = gt_grids[i]
            enemy = _enemy_values(frames[i]["labels"])
            area = sum(int((gt == v).sum()) for v in enemy)
            if area > best_area:
                best_fi, best_area = i, area
        fi = best_fi
    rgb = frames[fi]["rgb"]
    if rgb.ndim == 3 and rgb.shape[0] == 3:
        rgb = np.transpose(rgb, (1, 2, 0))
    gt = gt_grids[fi]
    # colour the carve: each non-ground region a distinct hue
    carve_img = np.zeros((GH, GW, 3), dtype=np.uint8)
    palette = [(230, 60, 60), (60, 200, 60), (60, 120, 240), (240, 200, 40),
               (200, 60, 220), (40, 220, 220), (240, 140, 40), (140, 90, 240)]
    for k, c in enumerate(carve_per_frame[fi]):
        col = palette[k % len(palette)]
        for (r, cc) in c["cells"]:
            carve_img[r, cc] = col
    # labels grid as greyscale-ish
    gt_img = np.zeros((GH, GW, 3), dtype=np.uint8)
    for v in np.unique(gt):
        if v == 0:
            continue
        mask = gt == v
        gt_img[mask] = (int(v), 255 - int(v), 128)
    scale = 4
    def up(a, H, W):
        im = Image.fromarray(a).resize((W * scale, H * scale), Image.NEAREST)
        return im
    rgb_small = Image.fromarray(rgb).resize((GW * scale, GH * scale), Image.NEAREST)
    strip = Image.new("RGB", (GW * scale * 3 + 16, GH * scale), (20, 20, 20))
    strip.paste(rgb_small, (0, 0))
    strip.paste(up(gt_img, GH, GW), (GW * scale + 8, 0))
    strip.paste(up(carve_img, GH, GW), (2 * (GW * scale + 8), 0))
    path = os.path.join(out_dir, f"eye_on_doom_{tag}_f{fi}.png")
    strip.save(path)
    return os.path.basename(path)


def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    result = {
        "scenario": SCEN, "doom_seed": DOOM_SEED,
        "grid": [GW, GH], "downsample": DOWN, "block": BLOCK,
        "levels": list(LEVELS), "n_frames_cap": N_FRAMES,
        "iou_thresholds": list(IOU_THRESHOLDS),
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
        "runs": {},
    }
    img_dir = os.path.join(ROOT, "results", "eye_on_doom_imgs")
    os.makedirs(img_dir, exist_ok=True)

    # Two conditions: STATIONARY (isolates object-motion) and TURNING (egomotion
    # wall). defend_the_center: player fixed unless it turns.
    for action, cond in [("attack", "stationary"), ("turn_right", "turning")]:
        frames = capture_doom(action)
        if not frames:
            result["runs"][cond] = {"error": "no frames captured"}
            continue
        gt_grids = [downsample_labels(f["labels_buf"], GH, GW) for f in frames]
        label_lists = [f["labels"] for f in frames]
        luma = np.stack([downsample_grey(f["rgb"], GH, GW) for f in frames])
        depth = np.stack([downsample_scalar(f["depth"], GH, GW) for f in frames])

        cond_out = {"n_frames": len(frames),
                    "gt_enemy_present_frames":
                        sum(1 for L in label_lists if _enemy_values(L)),
                    "value_carve": {}, "motion_carve": {}, "depth_carve": {}}

        for L in LEVELS:
            fq = quantize(luma, L)
            pv, wv = run_value_carve(fq, GH, GW)
            cond_out["value_carve"][str(L)] = analyse_run(
                frames, pv, gt_grids, label_lists, f"value_L{L}_{cond}")
            cond_out["value_carve"][str(L)]["wall_ms_per_frame"] = \
                float(np.mean(wv) * 1e3)
            pm, wm = run_motion_carve(fq, GH, GW, BLOCK)
            cond_out["motion_carve"][str(L)] = analyse_run(
                frames, pm, gt_grids, label_lists, f"motion_L{L}_{cond}")
            cond_out["motion_carve"][str(L)]["wall_ms_per_frame"] = \
                float(np.mean(wm) * 1e3)
            if L == LEVELS[0]:
                cond_out["iou_vs_gt_enemy_area_value_carve"] = \
                    _iou_vs_size(frames, pv, gt_grids, label_lists)
                cond_out["png"] = _save_pngs(frames, pv, gt_grids, img_dir, cond)

        # DEPTH-assisted carve (bonus channel): objects pop in depth.
        dq = quantize(depth, LEVELS[0])
        pd, wd = run_value_carve(dq, GH, GW)
        cond_out["depth_carve"][str(LEVELS[0])] = analyse_run(
            frames, pd, gt_grids, label_lists, f"depth_L{LEVELS[0]}_{cond}")
        cond_out["depth_carve"][str(LEVELS[0])]["wall_ms_per_frame"] = \
            float(np.mean(wd) * 1e3)
        cond_out["iou_vs_gt_enemy_area_depth_carve"] = \
            _iou_vs_size(frames, pd, gt_grids, label_lists)

        result["runs"][cond] = cond_out
        ev = cond_out["value_carve"][str(LEVELS[0])]["enemy_iou"]
        dv = cond_out["depth_carve"][str(LEVELS[0])]["enemy_iou"]
        print(f"[{cond:10s}] frames={len(frames):2d} "
              f"enemy_IoU(RGB L4) mean={ev['mean']:.3f} median={ev['median']:.3f} "
              f"| enemy_IoU(depth) mean={dv['mean']:.3f} "
              f"| fp_regions/frame={cond_out['value_carve'][str(LEVELS[0])]['false_positive_regions']['mean']:.1f}")

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "eye_on_doom.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
