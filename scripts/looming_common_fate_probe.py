#!/usr/bin/env python3
"""LOOMING / EXPANSION COMMON-FATE (block 154000-154999).

THE GENERAL CAPABILITY (not Doom support): carve an object by the coherent
TRANSFORM its cells undergo across frames, generalizing common-fate from
TRANSLATION ("moving together") to SCALE / EXPANSION ("looming together"). An
approaching object LOOMS: its cells expand radially from a focus of expansion
(FOE) — near-zero net TRANSLATION flow, so the translation-only common-fate
carve (`native.segment_motion` grouping cells by a shared translation vector)
misses or FRAGMENTS it. Looming is depth-from-motion / time-to-contact (the
looming rate s ∝ 1/TTC). Doom (block 153000) is the eval that hands us per-pixel
GROUND TRUTH; the capability is general.

THE MECHANISM — AFFINE common-fate, minimal case SCALE (expansion).
A rigid mover has UNIFORM flow (divergence 0). A looming object has coherent
radial EXPANSION about a shared FOE: flow v(p) = s·(p − foe), whose divergence
div = ∂vx/∂x + ∂vy/∂y = 2s is CONSTANT and positive across the whole object
(negative for a receding object; 0 for pure translation). So:

  EXPANSION CARVE = the SAME common-fate union-find (`native.segment_motion`,
  UNCHANGED), fed the per-cell DIVERGENCE scalar instead of the raw flow vector.
  Cells sharing a common local expansion rate group together; the looming object
  (uniform positive divergence) is one coherent region where the translation
  carve fragments it into per-ring directional pieces. The Otsu tolerance FALLS
  OUT of the divergence field's own dispersion (§13) — the SAME criterion the
  translation carve uses, no expansion constant appears.

  AFFINE READ-OUT (depth-from-motion): fit v(p) = A·(p − c) + t over a region's
  flow by least squares. trace(A)/2 = the isotropic SCALE RATE s (loom > 0,
  recede < 0, translate ≈ 0); t = translation; the antisymmetric part = rotation;
  the FOE is where the fitted flow vanishes; TTC ≈ 1/s. This is a pure
  MEASUREMENT read-out (like IoU scoring), not agent cognition.

ARCHITECTURE (CLAUDE.md — the agent is Rust). The grouping is the EXISTING Rust
primitive `segment_motion_and_track`, byte-for-byte unchanged (no Rust added, no
seed, no default moved — new files only, so the shipped carve path is
byte-identical BY CONSTRUCTION). The divergence field and the affine fit are
MECHANICAL sensor / measurement transforms over pixel/flow arrays (the position
`quantize()` and `vector_field()` occupy — an opaque signal → the smallest graph
token / a scored read-out), no conditional over graph state, no agent decision.
The VizDoom driver is a world adapter; the labels buffer is the SCORING ORACLE,
never fed to the eye. Scoring is set arithmetic (IoU) by POSITION, never by
cross-process region-id.

Reuses the GATED primitives from scripts/eye_on_doom_probe.py (same scorer, same
VizDoom adapter, same translation carve, same region read-back) so the
translation baseline is provably 153000's.

Pre-registration: VISION_LOOMING_COMMON_FATE_PREREG.md.
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

# Reuse 152000/153000's gated primitives: identical scorer, translation carve,
# region read-back, VizDoom adapter, downsample/quantize.
from scripts.eye_on_doom_probe import (  # noqa: E402
    _block_mean, _region_cell_sets, downsample_labels, quantize, iou,
    score_frame, _enemy_values, _player_values, capture_doom,
    run_motion_carve,
)

# ---- DECLARED RESIDUALS (§13 — stated, NOT tuned to the score) -------------
BLOCK = 4               # vector_field aperture / flow block (the sensor aperture)
DOOM_SEED = 154000      # block base; fixed => reproducible
DOWN_DOOM = 2           # Doom downsample (per 153000's real-time value-carve ceiling)
N_FRAMES = 60
SCEN = "defend_the_center"
LEVEL = 4               # the eye's shipped quantization default; not the lever
IOU_THRESHOLDS = (0.1, 0.25, 0.5)
SYNTH_G = 48            # synthetic grid side (H1)


# ======================================================================
#  DIVERGENCE — a mechanical sensor transform of the flow field (§13:
#  a fixed central-difference stencil, no tuned constant). div[p] measures
#  the LOCAL EXPANSION rate; it is the trace of the flow Jacobian.
# ======================================================================
def divergence_field(vy, vx):
    """Per-cell divergence div = ∂vx/∂x + ∂vy/∂y of a flow field, central
    differences interior + one-sided at the border. Pure array math."""
    vy = np.asarray(vy, dtype=np.float64)
    vx = np.asarray(vx, dtype=np.float64)
    d = np.zeros_like(vy)
    d[:, 1:-1] += (vx[:, 2:] - vx[:, :-2]) * 0.5
    d[1:-1, :] += (vy[2:, :] - vy[:-2, :]) * 0.5
    d[:, 0] += vx[:, 1] - vx[:, 0]
    d[:, -1] += vx[:, -1] - vx[:, -2]
    d[0, :] += vy[1, :] - vy[0, :]
    d[-1, :] += vy[-1, :] - vy[-2, :]
    return d


# ======================================================================
#  AFFINE FLOW FIT — the depth-from-motion READ-OUT (a measurement, not a
#  decision). v(p) = A·(p − c) + t by least squares over a region's cells.
# ======================================================================
def affine_flow_fit(cells, vy, vx):
    """Least-squares affine flow over `cells` (a set of (r,c)). Returns a dict:
    scale_rate = trace(A)/2 (isotropic expansion; loom>0, recede<0, translate≈0),
    rotation   = (A[1,0]-A[0,1])/2,
    translation = (ty, tx) at the region centroid,
    foe        = (x,y) focus of expansion (where fitted flow ≈ 0), None if
                 the scale part is ~0 (translation-only, no focus),
    ttc        = 1/scale_rate (frames to contact), None if |rate| tiny,
    n          = cell count."""
    cells = list(cells)
    n = len(cells)
    if n < 3:
        return {"scale_rate": 0.0, "rotation": 0.0, "translation": (0.0, 0.0),
                "foe": None, "ttc": None, "n": n}
    P = np.array([[c, r] for (r, c) in cells], dtype=np.float64)   # (x, y)
    c0 = P.mean(axis=0)
    Q = P - c0
    Vx = np.array([vx[r, c] for (r, c) in cells], dtype=np.float64)
    Vy = np.array([vy[r, c] for (r, c) in cells], dtype=np.float64)
    M = np.column_stack([Q[:, 0], Q[:, 1], np.ones(n)])           # [dx, dy, 1]
    bx, *_ = np.linalg.lstsq(M, Vx, rcond=None)
    by, *_ = np.linalg.lstsq(M, Vy, rcond=None)
    axx, axy, tx = bx
    ayx, ayy, ty = by
    scale_rate = 0.5 * (axx + ayy)
    rotation = 0.5 * (ayx - axy)
    # focus of expansion: solve A (foe - c0) + t = 0  =>  foe = c0 - A^{-1} t
    A = np.array([[axx, axy], [ayx, ayy]])
    foe = None
    if abs(np.linalg.det(A)) > 1e-6:
        d = -np.linalg.solve(A, np.array([tx, ty]))
        foe = (float(c0[0] + d[0]), float(c0[1] + d[1]))
    ttc = (1.0 / scale_rate) if abs(scale_rate) > 1e-4 else None
    return {"scale_rate": float(scale_rate), "rotation": float(rotation),
            "translation": (float(ty), float(tx)), "foe": foe,
            "ttc": (float(ttc) if ttc is not None else None), "n": n}


# ======================================================================
#  CARVE DRIVERS — both reuse the SAME Rust primitive segment_motion.
#  translation carve: feed (vy, vx).   expansion carve: feed (divergence, 0).
# ======================================================================
def _boot():
    from domains import falling_world as fw
    s, ag, native = fw.boot_falling()
    return fw, native


def carve_flow(native, fw, gh, gw, fy, fx):
    """One-shot common-fate carve of a scalar/vector field (fy, fx) via the
    UNCHANGED Rust `segment_motion`. Returns the list of NON-GROUND region
    records (position-anchored cell-sets). Fresh world per call (matches the
    eye_on_doom driver's pattern)."""
    game, cell_ids = fw.setup_world(native, gh, gw)
    id2idx = {cid: i for i, cid in enumerate(cell_ids)}
    native.segment_motion(game, gh, gw,
                          np.asarray(fy, dtype=np.float64).reshape(-1).tolist(),
                          np.asarray(fx, dtype=np.float64).reshape(-1).tolist(),
                          cell_ids)
    regs = _region_cell_sets(native, game, id2idx, gw)
    mtol = float(native.node(game)["attrs"].get("mtol", 0.0))
    return regs, mtol


def translation_carve(vy, vx, gh, gw):
    fw, native = _boot()
    regs, tol = carve_flow(native, fw, gh, gw, vy, vx)
    return [r for r in regs if r["is_ground"] == 0.0], tol


def expansion_carve(vy, vx, gh, gw):
    """The EXPANSION carve: group by coherent DIVERGENCE (shared expansion)."""
    div = divergence_field(vy, vx)
    fw, native = _boot()
    regs, tol = carve_flow(native, fw, gh, gw, div, np.zeros_like(div))
    return [r for r in regs if r["is_ground"] == 0.0], tol, div


def best_region(regs, gt_cells):
    """The non-ground region with the highest IoU to a GT cell-set."""
    if not regs:
        return None, 0.0
    scored = [(iou(gt_cells, r["cells"]), r) for r in regs]
    j, r = max(scored, key=lambda x: x[0])
    return r, j


# ======================================================================
#  SYNTHETIC GROUND TRUTH — H1 (the ideal oracle)
# ======================================================================
def radial_flow(g, cx, cy, R, s, trans=(0.0, 0.0), rot=0.0, quant=True):
    """A flow field with a disk (radius R @ (cx,cy)) undergoing expansion s
    (radial), optional rigid rotation `rot`, and a global translation `trans`
    (egomotion of the whole field). `quant` rounds to INTEGER displacements —
    the block-matcher's native output; the regime where the translation carve
    fragments a loom into per-ring directional pieces. Returns (vy, vx, mask)."""
    yy, xx = np.mgrid[0:g, 0:g].astype(np.float64)
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= R * R
    tvy, tvx = trans
    vx = np.full((g, g), float(tvx))
    vy = np.full((g, g), float(tvy))
    vx[mask] += s * (xx - cx)[mask] - rot * (yy - cy)[mask]
    vy[mask] += s * (yy - cy)[mask] + rot * (xx - cx)[mask]
    if quant:
        vx = np.round(vx)
        vy = np.round(vy)
    gt = frozenset((int(r), int(c)) for r, c in zip(*np.where(mask)))
    return vy, vx, gt


def render_loom_sequence(g, cx, cy, R0, scale_per_frame, nframes, rng):
    """A RENDERED textured looming disk (H1b): a static-background scene with a
    disk whose texture SCALES with it (the pixels a block-matcher will chase).
    Returns (frames[list of luma], masks[list of bool])."""
    bg = rng.integers(40, 90, size=(g, g)).astype(np.float64)
    base_tex = rng.integers(120, 240, size=(g, g)).astype(np.float64)
    yy, xx = np.mgrid[0:g, 0:g].astype(np.float64)
    frames, masks = [], []
    for t in range(nframes):
        R = R0 * (scale_per_frame ** t)
        s = R / R0
        oy = np.clip(((yy - cy) / s + cy).astype(int), 0, g - 1)
        ox = np.clip(((xx - cx) / s + cx).astype(int), 0, g - 1)
        img = bg.copy()
        m = (xx - cx) ** 2 + (yy - cy) ** 2 <= R * R
        img[m] = base_tex[oy, ox][m]
        frames.append(img)
        masks.append(m)
    return frames, masks


def mask_to_cells(mask, gh, gw):
    """Modal-downsample a boolean pixel mask to grid cells (>50% object)."""
    H, W = mask.shape
    bh, bw = H // gh, W // gw
    out = set()
    for r in range(gh):
        for c in range(gw):
            if mask[r * bh:(r + 1) * bh, c * bw:(c + 1) * bw].mean() > 0.5:
                out.add((r, c))
    return frozenset(out)


# ======================================================================
#  H1 — analytic flow (pure mechanism) + controls
# ======================================================================
def run_h1_analytic():
    g = SYNTH_G
    cx = cy = g // 2
    R = 12
    out = {"grid": g, "disk_R": R, "cases": {}}
    cases = [
        ("loom_s0.15", dict(s=0.15)),
        ("loom_s0.25", dict(s=0.25)),
        ("loom_s0.08", dict(s=0.08)),
        ("recede_s-0.15", dict(s=-0.15)),
        ("translate_no_scale", dict(s=0.0, trans=(3.0, 0.0))),
        ("static", dict(s=0.0)),
        ("noise", dict(s=0.0, noise=True)),
        ("loom_plus_egomotion", dict(s=0.15, trans=(2.0, 0.0))),
        ("loom_offaxis_foe", dict(s=0.15, cx=g // 2 + 6)),
    ]
    rng = np.random.default_rng(DOOM_SEED + 1)
    for name, cfg in cases:
        s = cfg.get("s", 0.0)
        ccx = cfg.get("cx", cx)
        if cfg.get("noise"):
            vy = rng.integers(-3, 4, size=(g, g)).astype(np.float64)
            vx = rng.integers(-3, 4, size=(g, g)).astype(np.float64)
            _, _, gt = radial_flow(g, ccx, cy, R, 0.0)
        else:
            vy, vx, gt = radial_flow(g, ccx, cy, R, s,
                                     trans=cfg.get("trans", (0.0, 0.0)))
        tr, ttol = translation_carve(vy, vx, g, g)
        ex, etol, div = expansion_carve(vy, vx, g, g)
        _, tr_iou = best_region(tr, gt)
        breg, ex_iou = best_region(ex, gt)
        fit = affine_flow_fit(breg["cells"], vy, vx) if breg else \
            affine_flow_fit(gt, vy, vx)   # empty carve: fit the GT to show rate
        # recovered rate over the GT region (oracle grouping) — the pure read-out
        gt_fit = affine_flow_fit(gt, vy, vx)
        out["cases"][name] = {
            "true_scale_rate": s,
            "translation_carve_iou": round(tr_iou, 4),
            "translation_carve_nfrag": len(tr),
            "expansion_carve_iou": round(ex_iou, 4),
            "expansion_carve_nreg": len(ex),
            "recovered_scale_rate_bestreg": round(fit["scale_rate"], 4),
            "recovered_scale_rate_gt": round(gt_fit["scale_rate"], 4),
            "recovered_foe": (None if gt_fit["foe"] is None
                              else [round(v, 1) for v in gt_fit["foe"]]),
            "ttc_frames": (None if gt_fit["ttc"] is None
                           else round(gt_fit["ttc"], 2)),
            "mtol_expansion": round(etol, 4),
        }
    return out


# ======================================================================
#  H1b — RENDERED textured loom -> block-SAD flow -> carve (realistic)
# ======================================================================
def run_h1_rendered():
    from domains.motion_group_world import vector_field
    g = 96
    block = 6
    nh, nw = g // block, g // block
    rng = np.random.default_rng(DOOM_SEED + 2)
    frames, masks = render_loom_sequence(g, g // 2, g // 2, 14.0, 1.12, 10, rng)
    out = {"grid": g, "block": block, "scale_per_frame": 1.12, "per_frame": []}
    for fi in range(2, len(frames)):
        vf = vector_field(frames[fi - 1], frames[fi], block=block)  # (nh,nw,2)
        vy, vx = vf[:, :, 0], vf[:, :, 1]
        gt = mask_to_cells(masks[fi], nh, nw)
        tr, _ = translation_carve(vy, vx, nh, nw)
        ex, _, div = expansion_carve(vy, vx, nh, nw)
        _, tr_iou = best_region(tr, gt)
        breg, ex_iou = best_region(ex, gt)
        fit = affine_flow_fit(breg["cells"], vy, vx) if breg else {"scale_rate": 0.0}
        true_s = 1.12 - 1.0
        out["per_frame"].append({
            "frame": fi, "gt_cells": len(gt),
            "translation_carve_iou": round(tr_iou, 4),
            "translation_carve_nfrag": len(tr),
            "expansion_carve_iou": round(ex_iou, 4),
            "recovered_scale_rate": round(fit["scale_rate"], 4),
            "true_scale_rate": round(true_s, 4),
        })
    ex_ious = [p["expansion_carve_iou"] for p in out["per_frame"]]
    tr_ious = [p["translation_carve_iou"] for p in out["per_frame"]]
    out["expansion_iou_mean"] = float(np.mean(ex_ious)) if ex_ious else 0.0
    out["translation_iou_mean"] = float(np.mean(tr_ious)) if tr_ious else 0.0
    return out


# ======================================================================
#  H2 — DOOM defend_the_center, ground-truth scored
# ======================================================================
def _doom_flow_carves(frames, gh, gw, down, block):
    """Per-frame translation + expansion carves over Doom quantized-luma flow,
    scored against the labels buffer. Returns per-frame stats + timing."""
    from domains.motion_group_world import vector_field
    # luma grid per frame
    def luma(rgb):
        rgb = np.asarray(rgb)
        if rgb.ndim == 3 and rgb.shape[0] == 3:
            rgb = np.transpose(rgb, (1, 2, 0))
        L = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2])
        return _block_mean(L.astype(np.float64), gh, gw).astype(np.uint8)

    fq = quantize(np.stack([luma(f["rgb"]) for f in frames]), LEVEL)
    gt_grids = [downsample_labels(f["labels_buf"], gh, gw) if down > 1
                else np.asarray(f["labels_buf"])[:gh, :gw].astype(np.int64)
                for f in frames]
    label_lists = [f["labels"] for f in frames]

    tr_ious, ex_ious = [], []
    tr_walls, ex_walls = [], []
    recovered_rates = []
    enemy_present = 0
    per_frame = []
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
        gt = gt_grids[fi]
        labels = label_lists[fi]
        enemy_vals = _enemy_values(labels)
        player_vals = _player_values(labels)
        if enemy_vals:
            enemy_present += 1
        # GT enemy cell-set (union of enemy label values)
        gt_enemy = frozenset(
            (int(r), int(c))
            for v in enemy_vals
            for r, c in zip(*np.where(gt == v)))
        if not gt_enemy:
            continue
        t0 = time.perf_counter()
        tr, _ = translation_carve(vy, vx, gh, gw)
        tr_walls.append(time.perf_counter() - t0)
        t1 = time.perf_counter()
        ex, _, div = expansion_carve(vy, vx, gh, gw)
        ex_walls.append(time.perf_counter() - t1)
        _, tr_iou = best_region(tr, gt_enemy)
        breg, ex_iou = best_region(ex, gt_enemy)
        tr_ious.append(tr_iou)
        ex_ious.append(ex_iou)
        if breg:
            fit = affine_flow_fit(breg["cells"], vy, vx)
            if abs(fit["scale_rate"]) > 1e-4:
                recovered_rates.append(fit["scale_rate"])
        per_frame.append({"frame": fi, "tr_iou": round(tr_iou, 4),
                          "ex_iou": round(ex_iou, 4)})

    def stat(xs):
        return ({"mean": float(np.mean(xs)), "median": float(np.median(xs)),
                 "max": float(np.max(xs)), "n": len(xs)} if xs else
                {"mean": 0.0, "median": 0.0, "max": 0.0, "n": 0})
    return {
        "down": down, "grid": [gw, gh], "block": block,
        "enemy_present_frames": enemy_present,
        "translation_carve_enemy_iou": stat(tr_ious),
        "expansion_carve_enemy_iou": stat(ex_ious),
        "translation_iou_raw": [round(x, 4) for x in tr_ious],
        "expansion_iou_raw": [round(x, 4) for x in ex_ious],
        "recovered_scale_rates": [round(x, 4) for x in recovered_rates],
        "recovered_scale_rate_mean":
            (float(np.mean(recovered_rates)) if recovered_rates else 0.0),
        "translation_ms_per_frame": float(np.mean(tr_walls) * 1e3) if tr_walls else 0.0,
        "expansion_ms_per_frame": float(np.mean(ex_walls) * 1e3) if ex_walls else 0.0,
        "per_frame": per_frame,
    }


def run_h2_doom():
    frames = capture_doom("attack", n_frames=N_FRAMES, seed=DOOM_SEED)
    if not frames:
        return {"error": "no frames captured (vizdoom absent?)"}
    down = DOWN_DOOM
    gh, gw = 240 // down, 320 // down
    block = max(1, BLOCK * (4 // down)) if down <= 4 else BLOCK
    block = max(1, 16 // down)   # constant ~16px physical aperture (as 153000)
    return _doom_flow_carves(frames, gh, gw, down, block)


# ======================================================================
def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble()
    prov = provenance_stamp(strict=False)
    load0 = os.getloadavg()

    result = {
        "block": 154000, "doom_seed": DOOM_SEED, "block_aperture": BLOCK,
        "engine_source_match": prov.get("source_match"),
        "engine_source_fingerprint": prov.get("source_fingerprint"),
    }
    print("== H1 analytic (pure mechanism + controls) ==")
    result["h1_analytic"] = run_h1_analytic()
    for name, c in result["h1_analytic"]["cases"].items():
        print(f"  {name:22s} TRANS iou={c['translation_carve_iou']:.3f}"
              f"(nfrag={c['translation_carve_nfrag']}) | "
              f"EXPAND iou={c['expansion_carve_iou']:.3f} | "
              f"rec_rate(gt)={c['recovered_scale_rate_gt']:+.3f}"
              f"(true{c['true_scale_rate']:+.3f}) foe={c['recovered_foe']}")

    print("== H1b rendered textured loom (block-SAD flow) ==")
    result["h1_rendered"] = run_h1_rendered()
    r = result["h1_rendered"]
    print(f"  expansion IoU mean={r['expansion_iou_mean']:.3f} "
          f"translation IoU mean={r['translation_iou_mean']:.3f}")

    print("== H2 Doom defend_the_center (ground-truth scored) ==")
    result["h2_doom"] = run_h2_doom()
    h2 = result["h2_doom"]
    if "error" not in h2:
        print(f"  down={h2['down']} grid={h2['grid']} block={h2['block']} "
              f"enemy_present={h2['enemy_present_frames']}")
        print(f"  translation enemy IoU mean={h2['translation_carve_enemy_iou']['mean']:.4f}"
              f" (n={h2['translation_carve_enemy_iou']['n']})")
        print(f"  EXPANSION  enemy IoU mean={h2['expansion_carve_enemy_iou']['mean']:.4f}"
              f" (n={h2['expansion_carve_enemy_iou']['n']})")
        print(f"  recovered scale rate mean={h2['recovered_scale_rate_mean']:+.4f}"
              f" (n={len(h2['recovered_scale_rates'])})")
        print(f"  ms/frame translation={h2['translation_ms_per_frame']:.1f}"
              f" expansion={h2['expansion_ms_per_frame']:.1f}")
    else:
        print("  ", h2["error"])

    result["loadavg_start"] = list(load0)
    result["loadavg_end"] = list(os.getloadavg())
    out = os.path.join(ROOT, "results", "looming_common_fate.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", out)
    return result


if __name__ == "__main__":
    main()
