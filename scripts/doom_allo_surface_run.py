"""doom_allo_surface_run — the marine walks a FIXED, seeded route on real E1M1 and the moving
eye RECONSTRUCTS the level MAP as the pose-compensated, ALLOCENTRIC HELD SURFACE (block
203000-203999). The held-prediction / decay / demotion loop (200000) accumulated in WORLD
coordinates via the marine's pose — a persistent, super-resolving, DECAYING reconstruction of
E1M1 built from what the eye SEES as it moves.

SOURCE DISCIPLINE (audited, 161000's discipline):
  * GEOMETRY + APPEARANCE are SEEN, never read. Each forward step gives parallax; the RGB optical
    flow is run through DEPTH-FROM-MOTION (158000), calibrated to world units by the agent's OWN
    forward displacement (efference copy, 155000); the appearance is the RGB column luma. That
    SEEN depth + luma, placed at world coordinates via the known pose, is what accumulates.
  * The VizDoom DEPTH BUFFER is a SCORING ORACLE ONLY — an oracle top-down occupancy is built
    from it (depth-buffer hits placed by pose) and the reconstruction's fidelity is scored
    against it (IoU / correlation). NEVER fed into the map.
  * The LABELS BUFFER is not used at all.

The map ACCUMULATION / DECAY / DEMOTION are graph-native rules (seeds/doom_allocentric_surface.json);
this runner is mechanical I/O + measurement: capture -> see depth+luma -> pose-register -> tick ->
read -> score -> render. IMPORT-INERT: nothing runs at import; use run() / __main__.

    PYTHONPATH=. python3 scripts/doom_allo_surface_run.py --frames 60
"""
from __future__ import annotations

import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "doom_allo_surface")
SEED_PATH = os.path.join(ROOT, "seeds", "doom_allocentric_surface.json")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"

FOV_DEG = 90.0
GH, GW = 240, 320
BLOCK, LEVEL = 16, None
CELL = 64.0


def _col_luma(rgb, gc, GW):
    """Mechanical photometry: mean luma of the RGB image column that corresponds to azimuth
    column gc (the SEEN surface appearance in that direction). RGB is (H,W,3) or (3,H,W)."""
    import numpy as np
    a = np.asarray(rgb)
    if a.ndim == 3 and a.shape[0] == 3:
        a = np.transpose(a, (1, 2, 0))
    H, W = a.shape[0], a.shape[1]
    ic = int(min(W - 1, max(0, round((gc + 0.5) / GW * W))))
    band = a[H // 4: 3 * H // 4, max(0, ic - 2): ic + 3, :].astype(float)
    if band.size == 0:
        return 0.0
    return float(0.299 * band[..., 0].mean() + 0.587 * band[..., 1].mean() + 0.114 * band[..., 2].mean())


def _seen_by_column(frames, fi):
    """SEE per-azimuth (az, Z_world, luma) for frame fi via depth-from-motion on RGB flow, plus
    the column luma. Returns (list or None, diag). Z calibrated to world units by the agent's OWN
    forward displacement (efference copy). Reads NO depth/labels buffer."""
    import numpy as np
    from scripts.depth_from_motion_probe import (
        estimate_foe, radial_decompose, depth_from_motion, expansion_gate, flag_movers, _flow_field)
    vy, vx = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
    mag = np.sqrt(vy * vy + vx * vx)
    if (mag > 0.5).sum() < 8:
        return None, {"why": "no_flow"}
    _, ediag = expansion_gate(vy, vx)
    px0, py0, _ = frames[fi - 1]["pose"]; px1, py1, _ = frames[fi]["pose"]
    T_world = math.hypot(px1 - px0, py1 - py0)
    if frames[fi - 1].get("action") != [1, 0, 0] or T_world < 1.0:
        return None, {"why": "not_forward", "T": round(T_world, 2)}
    foe, _ = estimate_foe(vy, vx)
    if foe is None:
        return None, {"why": "no_foe"}
    dec = radial_decompose(vy, vx, foe)
    flagged, _ = flag_movers(dec["tangential_mag"], dec["valid"])
    depth, dvalid = depth_from_motion(vy, vx, foe)
    good = dvalid & (~flagged)
    rgb = frames[fi]["rgb"]
    out = []
    for gc in range(GW):
        col = depth[:, gc][good[:, gc]]
        az = math.radians(-FOV_DEG / 2.0 + FOV_DEG * (gc + 0.5) / GW)
        if col.size >= 2:
            Z = float(np.median(col)) * T_world
            out.append((az, Z, _col_luma(rgb, gc, GW)))
        else:
            out.append((az, None, 0.0))
    return out, {"why": "ok", "T": round(T_world, 2), "n_valid": int(good.sum())}


def _oracle_occupancy(frames, fi, *, cell=CELL, max_range_cells=16):
    """ORACLE ONLY: build the depth-BUFFER top-down occupancy for frame fi (depth-buffer hits
    placed at world coords via the known pose — the SAME geometry the SEEN path builds, but from
    the ground-truth depth buffer). Returns {(x,y): 0 free / 1 wall}. USED ONLY to score the
    reconstruction (fidelity IoU) — NEVER fed into the map."""
    import numpy as np
    from scripts.depth_from_motion_probe import _downsample_depth
    px, py, ang = frames[fi]["pose"]
    facing = math.radians(ang)
    db = _downsample_depth(frames[fi]["depth"], GH, GW)  # per-column ground-truth range
    # VizDoom depth buffer units -> world: use the same per-column median row band, scaled so a
    # full-range column reaches ~max_range. This is a coarse oracle map (scoring only).
    col_range = np.median(db[GH // 3: 2 * GH // 3, :], axis=0).astype(float)
    scale = (max_range_cells * cell) / (float(col_range.max()) + 1e-6)
    occ = {}
    for gc in range(GW):
        Z = col_range[gc] * scale
        dist_cells = Z / cell
        world_ang = facing + math.radians(-FOV_DEG / 2.0 + FOV_DEG * (gc + 0.5) / GW)
        steps = int(min(dist_cells, max_range_cells))
        for s in range(1, steps + 1):
            wx = px + math.cos(world_ang) * s * cell; wy = py + math.sin(world_ang) * s * cell
            occ.setdefault((int(math.floor(wx / cell)), int(math.floor(wy / cell))), 0)
        if dist_cells < max_range_cells:
            wx = px + math.cos(world_ang) * dist_cells * cell; wy = py + math.sin(world_ang) * dist_cells * cell
            occ[(int(math.floor(wx / cell)), int(math.floor(wy / cell)))] = 1
    return occ


def _seen_vs_oracle_spearman(frames, fi):
    """ORACLE score (161000's measure): Spearman(seen depth-from-motion, VizDoom depth buffer) on
    radial-consistent background cells. The depth buffer is used HERE ONLY, never as a map input.
    Returns rho or None — the honest 'the SEEN depth correlates with ground truth' number."""
    import numpy as np
    from scripts.depth_from_motion_probe import (
        estimate_foe, radial_decompose, depth_from_motion, flag_movers, spearman, _flow_field,
        _downsample_depth)
    vy, vx = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
    if (np.sqrt(vy * vy + vx * vx) > 0.5).sum() < 8:
        return None
    foe, _ = estimate_foe(vy, vx)
    if foe is None:
        return None
    dec = radial_decompose(vy, vx, foe)
    flagged, _ = flag_movers(dec["tangential_mag"], dec["valid"])
    depth, dvalid = depth_from_motion(vy, vx, foe)
    db = _downsample_depth(frames[fi]["depth"], GH, GW)
    cons = dvalid & (~flagged)
    return spearman(depth[cons], db[cons])


def _route(n):
    """FIXED forward-heavy scripted walk, with a RETURN leg so a demoted region can be revisited
    (G2 loop-closure analog): forward out, turn around, come back."""
    seq = []
    half = n // 2
    for i in range(n):
        if i == half:
            seq += [[0, 0, 1]] * 0  # marker; turns handled below
        if i < half:
            seq.append([0, 0, 1] if i % 16 in (12, 13) else [1, 0, 0])
        elif i < half + 6:
            seq.append([0, 0, 1])   # turn around (~180 over 6 steps)
        else:
            seq.append([0, 1, 0] if i % 16 in (12, 13) else [1, 0, 0])
    return seq


def _capture(n_frames, seed):
    """Own E1M1 capture recording POSE (x, y, angle). Mechanical I/O."""
    import numpy as np
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.set_doom_game_path(WAD); g.set_doom_scenario_path(WAD); g.set_doom_map("E1M1")
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)      # ORACLE only
    g.set_render_hud(True); g.set_render_weapon(True)
    g.set_window_visible(False); g.set_mode(vzd.Mode.PLAYER); g.set_doom_skill(3)
    g.set_living_reward(0.0); g.set_death_penalty(0.0)
    for b in (vzd.Button.MOVE_FORWARD, vzd.Button.TURN_LEFT, vzd.Button.TURN_RIGHT):
        g.add_available_button(b)
    gv = vzd.GameVariable
    for v in (gv.POSITION_X, gv.POSITION_Y, gv.ANGLE):
        g.add_available_game_variable(v)
    g.set_seed(int(seed)); g.init(); g.new_episode()
    seq = _route(n_frames)
    frames = []
    for i in range(n_frames):
        if g.is_episode_finished() or g.is_player_dead():
            break
        st = g.get_state()
        if st is None:
            break
        frames.append({
            "rgb": np.array(st.screen_buffer, copy=True),
            "depth": np.array(st.depth_buffer, copy=True),       # ORACLE
            "pose": (float(g.get_game_variable(gv.POSITION_X)),
                     float(g.get_game_variable(gv.POSITION_Y)),
                     float(g.get_game_variable(gv.ANGLE))),
            "action": seq[i]})
        g.make_action(seq[i], 1)
    g.close()
    return frames


def _iou(recon, oracle):
    """Geometry fidelity: IoU of the reconstructed FREE cells vs the oracle FREE cells (coverage
    of the walkable structure), and cell-overlap agreement. Oracle is scoring-only."""
    rf = {p for p, c in recon.items() if c["geom"] == 0}
    of = {p for p, v in oracle.items() if v == 0}
    inter = len(rf & of); union = len(rf | of)
    return (inter / union) if union else 0.0


def run(frames=60, seed=1234, checkpoints=(10, 25, 40), decay=True, outdir=OUTDIR):
    import numpy as np
    from substrate.world_adapter import WorldAdapter
    import domains.doom_allo_surface_ingest as al

    os.makedirs(outdir, exist_ok=True)
    caps = _capture(frames, seed)
    if not caps:
        return None
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom", "map_epoch": 0.0})
    if decay:
        al.install_params(wa, game)          # opt-in: enable the decay/demotion loop

    # accumulate a per-frame ORACLE map (scoring only) in lockstep for the IoU fidelity curve
    oracle_map = {}
    trajectory, per_frame, ck_pngs = [], [], []
    spearmans = []
    seen_frames = 0
    tier_hist = {}                            # (x,y) -> list of (frame, tier) for a sample region
    for fi in range(len(caps)):
        px, py, ang = caps[fi]["pose"]
        floor_lum = _col_luma(caps[fi]["rgb"], GW // 2, GW)
        acell = al.ingest_walk(wa, game, (px, py), floor_lum, fi + 1)
        if fi >= 1:
            seen, diag = _seen_by_column(caps, fi)
            if seen is not None:
                al.ingest_seen(wa, game, (px, py, ang), seen, fi + 1)
                seen_frames += 1
                for p, v in _oracle_occupancy(caps, fi).items():   # ORACLE only
                    if v == 1 or p not in oracle_map:
                        oracle_map[p] = v
                sp = _seen_vs_oracle_spearman(caps, fi)             # ORACLE only
                if sp is not None:
                    spearmans.append(sp)
        work = al.accumulate(wa, game, fi + 1)
        trajectory.append(acell)
        recon = al.read_map(wa, game)
        fid = _iou(recon, oracle_map) if oracle_map else 0.0
        tiers = [c["tier"] for c in recon.values()]
        per_frame.append({
            "frame": fi, "cells": len(recon), "seen": seen_frames,
            "fidelity_iou": round(fid, 4), "oracle_cells": len(oracle_map),
            "work": work["work"], "minted": work["minted"], "blended": work["blended"],
            "mean_tier": round(float(np.mean(tiers)), 3) if tiers else 0.0,
            "fresh": sum(1 for t in tiers if t == 2), "gist": sum(1 for t in tiers if t == 1),
            "latent": sum(1 for t in tiers if t == 0),
            "max_dwell": max((c["dwell"] for c in recon.values()), default=0)})
        if (fi + 1) in checkpoints or (fi + 1) == len(caps):
            p = al.render_png(wa, game, os.path.join(outdir, "allo_frame_%03d.png" % (fi + 1)),
                              trajectory=trajectory)
            if p:
                ck_pngs.append(os.path.basename(p))

    recon = al.read_map(wa, game)
    # side-by-side final figure: reconstruction vs oracle
    fig = _render_compare(recon, oracle_map, trajectory, os.path.join(outdir, "reconstruction_vs_true.png"))
    dwells = sorted((c["dwell"] for c in recon.values()), reverse=True)
    sp = np.asarray(spearmans, float) if spearmans else np.array([])
    summary = {
        "seed": seed, "frames": len(caps), "seen_forward_frames": seen_frames, "decay": decay,
        "final_cells": len(recon), "oracle_cells": len(oracle_map),
        "final_fidelity_iou": per_frame[-1]["fidelity_iou"],
        "seen_vs_oracle_spearman": {
            "n": int(sp.size),
            "median": round(float(np.median(sp)), 4) if sp.size else None,
            "mean": round(float(np.mean(sp)), 4) if sp.size else None,
            "frac_pos": round(float((sp > 0).mean()), 3) if sp.size else None},
        "fidelity_curve": [(pf["frame"], pf["fidelity_iou"]) for pf in per_frame],
        "coverage_curve": [(pf["frame"], pf["cells"]) for pf in per_frame],
        "tier_curve": [(pf["frame"], pf["fresh"], pf["gist"], pf["latent"]) for pf in per_frame],
        "work_curve": [(pf["frame"], pf["work"], pf["minted"], pf["blended"]) for pf in per_frame],
        "max_dwell": dwells[0] if dwells else 0, "top_dwells": dwells[:10],
        "tier_counts_final": {"fresh": per_frame[-1]["fresh"], "gist": per_frame[-1]["gist"],
                              "latent": per_frame[-1]["latent"]},
        "checkpoint_pngs": ck_pngs, "compare_png": os.path.basename(fig) if fig else None,
    }
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def _render_compare(recon, oracle, trajectory, path):
    """Side-by-side: reconstructed allocentric held surface (left) vs the depth-oracle occupancy
    (right, scoring only). Mechanical rasteriser."""
    import numpy as np
    pts = list(recon.keys()) + list(oracle.keys()) + list(trajectory or [])
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    Wc, Hc = (x1 - x0 + 1), (y1 - y0 + 1)
    L = np.full((Hc, Wc, 3), 255, np.uint8); R = np.full((Hc, Wc, 3), 255, np.uint8)
    vals = [c["value"] for c in recon.values() if c["geom"] == 0]
    vlo, vhi = (min(vals), max(vals)) if vals else (0.0, 1.0); vspan = max(1e-6, vhi - vlo)
    tint = {2: (90, 200, 120), 1: (200, 190, 90), 0: (150, 110, 160)}
    for (x, y), c in recon.items():
        if c["geom"] == 1:
            L[y - y0, x - x0] = (30, 30, 30)
        else:
            g = max(0, min(255, int(60 + 180 * (c["value"] - vlo) / vspan)))
            L[y - y0, x - x0] = tuple((np.array([g, g, g]) + np.array(tint[c["tier"]])) // 2)
    for (x, y), v in oracle.items():
        R[y - y0, x - x0] = (30, 30, 30) if v == 1 else (190, 190, 190)
    for (x, y) in (trajectory or []):
        if x0 <= x <= x1 and y0 <= y <= y1:
            L[y - y0, x - x0] = (220, 30, 30); R[y - y0, x - x0] = (220, 30, 30)
    gap = np.full((Hc, 2, 3), 128, np.uint8)
    img = np.concatenate([L, gap, R], axis=1)
    big = np.repeat(np.repeat(img, 8, 0), 8, 1)
    try:
        from PIL import Image
        Image.fromarray(big, "RGB").save(path)
    except Exception:
        return None
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1234)
    args = ap.parse_args()
    try:
        import vizdoom  # noqa: F401
        if not os.path.exists(WAD):
            raise RuntimeError("WAD absent")
    except Exception as e:
        print("SKIP: VizDoom/WAD unavailable:", e)
        raise SystemExit(0)
    s = run(frames=args.frames, seed=args.seed)
    print(json.dumps(s, indent=2))
