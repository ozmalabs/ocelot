#!/usr/bin/env python3
"""DOOM FINER GRID + HUD MASK (block 153000-153999) — attack the two walls the
152000 eye-on-Doom probe isolated in the clean stationary/no-egomotion regime:

  H1  the SUB-GRID RESOLUTION wall (dominant): sweep the downsample factor
      DOWN in {4,2,1} -> grids 60x80 / 120x160 / 240x320 (full VizDoom res).
      The SAME stationary enemies (one capture, three downsamples) grow from
      ~2 cells -> ~8 -> ~16+ cells. Does enemy IoU jump (wall was sub-grid) or
      stay on its ~0.25 plateau (a DEEPER carve wall)?

  H2  the WEAPON-SPRITE ego-attached self-apparatus percept: a FIXED bottom-band
      screen-region crop of the carve readout (rows >= 150 of 240 — where the
      DoomPlayer weapon sprite renders; render_hud=false so no status bar). Crops
      the weapon percept; leaves enemies (world objects, horizon rows ~116-130)
      untouched.

      NB the weapon/HUD are NOT false objects — the eye perceives them
      correctly. They are the agent's own apparatus (senses its state through
      the HUD, acts THROUGH the weapon), EGO-ATTACHED: fixed in view-space, they
      do not obey world-motion. A hardcoded screen-region mask is exactly the
      kind of magic-number the architecture avoids; it is a DISCLOSED
      STEPPING-STONE to isolate the enemy-carving measurement, NOT the principled
      treatment. The principled treatment (a future rung, not built here):
      recognize self/apparatus by INVARIANCE TO EGOMOTION — under player turning
      the world optic-flow moves but the ego-stable overlay stays fixed, so what
      is motion-invariant-to-egomotion is SELF. A discoverable boundary (typed
      edges from agent_root: senses / acts_on), never a mask.

MECHANICAL I/O ONLY. The carve is the EXISTING Rust primitive
(`native.segment` value / `native.segment_motion` common-fate), byte-identical
to the shipped eye. The VizDoom driver is a world adapter; the labels buffer is
the SCORING ORACLE, never fed to the eye. The HUD mask is a fixed geometric crop
of the readout (POSITION only, no graph-state conditional). Scoring is pure set
arithmetic by IoU/POSITION, never by cross-process region-id. No Rust change, no
seed, no existing-file change (new files only).

Reuses the GATED scorer + carve drivers from scripts/eye_on_doom_probe.py so the
carve path is provably identical to 152000's.

Pre-registration: VISION_DOOM_FINER_GRID_PREREG.md.
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

# Reuse the 152000 probe's gated primitives (same scorer, same carve drivers,
# same VizDoom adapter) — this rung adds only the resolution sweep + the mask.
from scripts.eye_on_doom_probe import (  # noqa: E402
    _block_mean, downsample_labels, quantize, score_frame, iou,
    _enemy_values, _player_values, _value_to_objid,
    run_value_carve, run_motion_carve, capture_doom,
)

# ---- DECLARED RESIDUALS (§13 — stated, NOT tuned to the score) -------------
RESOLUTIONS = [(4, 60, 80), (2, 120, 160), (1, 240, 320)]  # (DOWN, GH, GW)
SCREEN_H, SCREEN_W = 240, 320
MASK_ROW_PX = 150        # weapon sprite measured rows [155..239]; enemies [116..130]
DOOM_SEED = 153000       # block base; fixed => reproducible
N_FRAMES = 60
SCEN = "defend_the_center"
LEVEL = 4                # the eye's shipped quantization default; L is not the lever
IOU_THRESHOLDS = (0.1, 0.25, 0.5)


def band_grid_row(gh):
    """The mask-band boundary in GRID rows for grid height gh — the fixed pixel
    band (rows >= MASK_ROW_PX of SCREEN_H) mapped into the grid. Resolution
    independent."""
    return int(round(MASK_ROW_PX / SCREEN_H * gh))


# ======================================================================
#  THE HUD MASK — a fixed geometric crop of the carve readout
# ======================================================================
def mask_regions(regs, band_row):
    """Drop carved regions lying ENTIRELY in the HUD band (all cells at
    grid-row >= band_row). A fixed screen-region crop: no graph state read, no
    agent decision — position only. A region straddling the boundary is KEPT
    (it may be a low enemy). Pure, importable, gated."""
    out = []
    for r in regs:
        cells = r["cells"]
        if cells and all(rr >= band_row for (rr, _cc) in cells):
            continue
        out.append(r)
    return out


def full_luma(rgb):
    """RGB (H,W,3) or (3,H,W) uint8 -> full-resolution luma (H,W) float64
    (ITU-R 601). Mechanical."""
    rgb = np.asarray(rgb)
    if rgb.ndim == 3 and rgb.shape[0] == 3:
        rgb = np.transpose(rgb, (1, 2, 0))
    return (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1]
            + 0.114 * rgb[..., 2]).astype(np.float64)


def down_luma(luma_full, gh, gw):
    return _block_mean(luma_full, gh, gw).astype(np.uint8)


def modal_labels(lab, gh, gw, down):
    """Per-cell modal label grid. DOWN=1 is the identity (1px blocks); the
    modal loop is only needed for real downsampling."""
    lab = np.asarray(lab)
    if down == 1:
        return lab[:gh, :gw].astype(np.int64)
    return downsample_labels(lab, gh, gw)


# ======================================================================
#  ANALYSIS — per resolution / carve mode / {masked, unmasked}
# ======================================================================
def analyse(frames, carve_per_frame, gt_grids, label_lists, band_row,
            masked):
    """Score one (resolution, carve-mode, mask) combination. Returns enemy IoU
    stats + raw, survival count, weapon-sprite IoU, false-positive count, and a
    per-(frame,enemy_value) IoU map for the cross-resolution matched subset."""
    enemy_ious, weapon_ious, n_fp, n_nonground = [], [], [], []
    survived = 0
    enemy_present = 0
    per_frame_enemy = {}   # frame_idx -> {enemy_value: iou}
    for fi in range(len(frames)):
        gt = gt_grids[fi]
        labels = label_lists[fi]
        regs = carve_per_frame[fi]
        if masked:
            regs = mask_regions(regs, band_row)
        carve_sets = [r["cells"] for r in regs]
        n_nonground.append(len(carve_sets))
        enemy_vals = _enemy_values(labels)
        player_vals = _player_values(labels)
        if enemy_vals:
            enemy_present += 1
        sc = score_frame(carve_sets, gt, object_values=(enemy_vals | player_vals))
        fmap = {}
        any_survived = False
        for v in enemy_vals:
            if v in sc["per_obj_best"]:      # survived downsample into the grid
                b = sc["per_obj_best"][v]
                enemy_ious.append(b["iou"])
                fmap[v] = b["iou"]
                any_survived = True
        if any_survived:
            survived += 1
        per_frame_enemy[fi] = fmap
        for v in player_vals:
            if v in sc["per_obj_best"]:
                weapon_ious.append(sc["per_obj_best"][v]["iou"])
        n_fp.append(sc["false_positive_regions"][str(IOU_THRESHOLDS[0])])

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "min": float(np.min(xs)), "max": float(np.max(xs)),
                 "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "n": 0})

    return {
        "enemy_iou": stat(enemy_ious),
        "enemy_iou_raw": [round(x, 4) for x in enemy_ious],
        "enemy_recovery": {
            str(t): float(np.mean([1.0 if x >= t else 0.0 for x in enemy_ious]))
            if enemy_ious else 0.0 for t in IOU_THRESHOLDS},
        "enemy_present_frames": enemy_present,
        "enemy_survived_frames": survived,
        "weapon_sprite_iou": stat(weapon_ious),
        "false_positive_regions": stat([float(x) for x in n_fp]),
        "n_nonground_regions": stat([float(x) for x in n_nonground]),
        "per_frame_enemy": per_frame_enemy,
    }


def iou_vs_cellcount(frames, carve_per_frame, gt_grids, label_lists):
    """Enemy IoU as a function of GT enemy area (grid cells) — the resolution
    wall as a curve. Unmasked (enemies are above the band anyway)."""
    pts = []
    for fi in range(len(frames)):
        gt = gt_grids[fi]
        carves = [r["cells"] for r in carve_per_frame[fi]]
        ev = _enemy_values(label_lists[fi])
        sc = score_frame(carves, gt,
                         object_values=(ev | _player_values(label_lists[fi])))
        for v in ev:
            if v in sc["per_obj_best"]:
                b = sc["per_obj_best"][v]
                pts.append((b["gt_area_cells"], round(b["iou"], 4)))
    return pts


def matched_subset(per_res_enemy, label_lists):
    """Enemy IoU restricted to (frame, enemy_value) pairs that SURVIVED
    downsample at ALL THREE resolutions (identical enemies) — isolates the pure
    IoU-vs-resolution effect from the survival-count confound.

    per_res_enemy : {down: {frame_idx: {value: iou}}}
    Returns {down: {mean, n}} over the common pair set + the pair count."""
    downs = list(per_res_enemy.keys())
    # the set of (frame, value) present at EVERY resolution
    common = None
    for d in downs:
        pairs = {(fi, v) for fi, fm in per_res_enemy[d].items() for v in fm}
        common = pairs if common is None else (common & pairs)
    common = common or set()
    out = {}
    for d in downs:
        vals = [per_res_enemy[d][fi][v] for (fi, v) in common]
        out[str(d)] = {"mean": float(np.mean(vals)) if vals else 0.0,
                       "n": len(vals)}
    return {"per_resolution": out, "n_matched_pairs": len(common)}


# ======================================================================
def _save_triptych(frames, carve_per_frame, gt_grids, gh, gw, out_dir, tag,
                   fi, band_row):
    """RGB | labels | carve triptych for one frame at a given resolution.
    Draws the mask-band boundary line on the carve panel."""
    try:
        from PIL import Image
    except Exception:
        return None
    if not frames:
        return None
    rgb = np.asarray(frames[fi]["rgb"])
    if rgb.ndim == 3 and rgb.shape[0] == 3:
        rgb = np.transpose(rgb, (1, 2, 0))
    gt = gt_grids[fi]
    carve_img = np.zeros((gh, gw, 3), dtype=np.uint8)
    palette = [(230, 60, 60), (60, 200, 60), (60, 120, 240), (240, 200, 40),
               (200, 60, 220), (40, 220, 220), (240, 140, 40), (140, 90, 240)]
    for k, c in enumerate(carve_per_frame[fi]):
        col = palette[k % len(palette)]
        for (r, cc) in c["cells"]:
            carve_img[r, cc] = col
    if 0 <= band_row < gh:
        carve_img[band_row, :] = (255, 255, 255)   # mask boundary
    gt_img = np.zeros((gh, gw, 3), dtype=np.uint8)
    for v in np.unique(gt):
        if v == 0:
            continue
        gt_img[gt == v] = (int(v) % 256, (255 - int(v)) % 256, 128)
    # scale so all resolutions render at a comparable pixel size
    disp_w = 320
    scale = max(1, disp_w // gw)
    def up(a, H, W):
        return Image.fromarray(a).resize((W * scale, H * scale), Image.NEAREST)
    rgb_small = Image.fromarray(rgb).resize((gw * scale, gh * scale), Image.NEAREST)
    strip = Image.new("RGB", (gw * scale * 3 + 16, gh * scale), (20, 20, 20))
    strip.paste(rgb_small, (0, 0))
    strip.paste(up(gt_img, gh, gw), (gw * scale + 8, 0))
    strip.paste(up(carve_img, gh, gw), (2 * (gw * scale + 8), 0))
    path = os.path.join(out_dir, f"doom_finer_{tag}_f{fi}.png")
    strip.save(path)
    return os.path.basename(path)


def _largest_enemy_frame(frames, gt_grids, label_lists):
    best_fi, best = 0, -1
    for i in range(len(frames)):
        ev = _enemy_values(label_lists[i])
        area = sum(int((gt_grids[i] == v).sum()) for v in ev)
        if area > best:
            best_fi, best = i, area
    return best_fi


def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    # STATIONARY regime: fixed `attack` every tic (no egomotion). One capture,
    # scored at three downsample resolutions.
    frames = capture_doom("attack", n_frames=N_FRAMES, seed=DOOM_SEED)
    if not frames:
        raise SystemExit("no frames captured")
    label_lists = [f["labels"] for f in frames]
    luma_full = [full_luma(f["rgb"]) for f in frames]

    img_dir = os.path.join(ROOT, "results", "doom_finer_grid_imgs")
    os.makedirs(img_dir, exist_ok=True)

    result = {
        "scenario": SCEN, "doom_seed": DOOM_SEED, "level": LEVEL,
        "resolutions": [{"down": d, "grid": [gw, gh]} for (d, gh, gw) in RESOLUTIONS],
        "mask_row_px": MASK_ROW_PX, "screen": [SCREEN_W, SCREEN_H],
        "n_frames": len(frames),
        "iou_thresholds": list(IOU_THRESHOLDS),
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
        "by_resolution": {},
    }

    # collect per-(frame,value) IoU maps per resolution for BOTH carve modes,
    # unmasked, for the matched-subset analysis
    per_res_enemy = {"value": {}, "motion": {}}

    for (down, gh, gw) in RESOLUTIONS:
        band = band_grid_row(gh)
        gt_grids = [modal_labels(f["labels_buf"], gh, gw, down) for f in frames]
        fq = quantize(np.stack([down_luma(L, gh, gw) for L in luma_full]), LEVEL)
        block = max(1, 16 // down)   # constant ~16px physical flow aperture

        pv, wv = run_value_carve(fq, gh, gw)
        pm, wm = run_motion_carve(fq, gh, gw, block)

        res_out = {"grid": [gw, gh], "down": down, "band_grid_row": band,
                   "motion_block": block,
                   "value_wall_ms_per_frame": float(np.mean(wv) * 1e3),
                   "motion_wall_ms_per_frame": float(np.mean(wm) * 1e3)}
        for mode, carves in (("value", pv), ("motion", pm)):
            for masked in (False, True):
                a = analyse(frames, carves, gt_grids, label_lists, band, masked)
                per_res_enemy[mode].setdefault(down, {})
                if not masked:
                    per_res_enemy[mode][down] = a.pop("per_frame_enemy")
                else:
                    a.pop("per_frame_enemy", None)
                res_out[f"{mode}_{'masked' if masked else 'unmasked'}"] = a
        res_out["iou_vs_cellcount_value"] = iou_vs_cellcount(
            frames, pv, gt_grids, label_lists)
        res_out["iou_vs_cellcount_motion"] = iou_vs_cellcount(
            frames, pm, gt_grids, label_lists)

        # triptych at the largest-enemy frame, at this resolution (value carve)
        fi = _largest_enemy_frame(frames, gt_grids, label_lists)
        res_out["png_value"] = _save_triptych(
            frames, pv, gt_grids, gh, gw, img_dir, f"value_d{down}", fi, band)
        res_out["png_motion"] = _save_triptych(
            frames, pm, gt_grids, gh, gw, img_dir, f"motion_d{down}", fi, band)

        result["by_resolution"][str(down)] = res_out
        ev_u = res_out["value_unmasked"]["enemy_iou"]
        em_u = res_out["motion_unmasked"]["enemy_iou"]
        print(f"[down={down} {gw}x{gh}] survived {res_out['value_unmasked']['enemy_survived_frames']}"
              f"/{res_out['value_unmasked']['enemy_present_frames']} present | "
              f"enemy IoU value {ev_u['mean']:.3f} (n={ev_u['n']}) "
              f"motion {em_u['mean']:.3f} (n={em_u['n']}) | "
              f"weapon IoU value unmasked {res_out['value_unmasked']['weapon_sprite_iou']['mean']:.3f} "
              f"masked {res_out['value_masked']['weapon_sprite_iou']['mean']:.3f} | "
              f"value {res_out['value_wall_ms_per_frame']:.1f}ms motion {res_out['motion_wall_ms_per_frame']:.1f}ms")

    result["matched_subset_value"] = matched_subset(per_res_enemy["value"], label_lists)
    result["matched_subset_motion"] = matched_subset(per_res_enemy["motion"], label_lists)
    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())

    out = os.path.join(ROOT, "results", "doom_finer_grid.json")
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    print("matched-subset value :", result["matched_subset_value"]["per_resolution"],
          "n=", result["matched_subset_value"]["n_matched_pairs"])
    print("matched-subset motion:", result["matched_subset_motion"]["per_resolution"],
          "n=", result["matched_subset_motion"]["n_matched_pairs"])
    return result


if __name__ == "__main__":
    main()
