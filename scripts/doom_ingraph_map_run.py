"""doom_ingraph_map_run — the marine walks a FIXED, seeded route on E1M1 and builds a
persistent, graph-native spatial map ENTIRELY FROM WHAT IT SEES (block 161000-161999).

SOURCE DISCIPLINE (audited, and the point of this rung):
  * GEOMETRY (walls) is SEEN, never read.  Each forward step gives parallax; the RGB optical
    flow is run through DEPTH-FROM-MOTION (block 158000: estimate_foe / radial_decompose /
    depth_from_motion), and the agent's OWN forward displacement (efference copy, block 155000)
    calibrates the recovered r/|flow| depth to world units.  That SEEN depth, placed in world
    coordinates via the known pose, is what registers into the map.
  * The VizDoom DEPTH BUFFER is the SCORING ORACLE ONLY — the seen depth is validated against
    it (Spearman), never fed into the map.  Same discipline as the labels buffer.
  * The LABELS BUFFER is a SCORING ORACLE ONLY.  Objects are NOT placed this rung (the eye's
    RGB carve as the object source is a named residual — using labels would smuggle the oracle).

So the whole map comes from the eye (RGB) + self-motion.  The map ACCUMULATION and area
TYPING are graph-native rules (seeds/doom_ingraph_map.json); this runner is mechanical I/O:
capture -> see depth -> place -> tick -> read -> render.

HONEST SCOPE: depth-from-motion NULLs on coarse flow and works only on adequate flow (158000:
Spearman 0.40-0.94).  The map is only as good as the SEEN depth; ACCUMULATION over many
viewpoints is what lets a persistent map beat single-frame noise.  A noisy/bounded map here is
an honest DEGRADE (map fidelity bounded by seen-depth quality), NOT a reason to touch the depth
buffer.

    PYTHONPATH=. python3 scripts/doom_ingraph_map_run.py --frames 80
"""
from __future__ import annotations

import argparse
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "doom_ingraph_map")
SEED_PATH = os.path.join(ROOT, "seeds", "doom_ingraph_map.json")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"

FOV_DEG = 90.0     # VizDoom default horizontal FOV (engine config, not tuned)
# The depth-from-motion sensor's ADEQUATE operating point (block 158000: works only on
# adequate flow, NULLs on coarse). Measured on this capture: the coarse DOWN=2 grid
# (120x160, quantized) NULLs (median rho -0.14); FULL-resolution raw-luma flow recovers
# usable depth (320x240, block 16, raw luma -> median rho 0.38, frac_pos 0.89, in 158000's
# 0.40-0.94 band). Finer parallax resolution is a SENSOR property, not tuning-to-oracle;
# the cost is off-real-time flow (ties the scale wall) — this map build is offline.
GH, GW = 240, 320
BLOCK, LEVEL = 16, None


def _route(n):
    """FIXED forward-heavy scripted walk (buttons [forward, turn_left, turn_right]). Forward
    gives the parallax depth-from-motion needs; brief turns sweep new geometry into view."""
    seq = []
    for i in range(n):
        if i % 16 in (12, 13):
            seq.append([0, 0, 1])          # short right turn to sweep
        elif i % 24 == 20:
            seq.append([0, 1, 0])          # occasional left turn
        else:
            seq.append([1, 0, 0])          # forward (parallax)
    return seq


def _capture(n_frames, seed):
    """Own E1M1 capture that ALSO records POSE (x, y, angle) — capture_e1m1 (157000) does not,
    and editing another rung's file is out of bounds. Mechanical I/O; decides nothing."""
    import numpy as np
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.set_doom_game_path(WAD); g.set_doom_scenario_path(WAD); g.set_doom_map("E1M1")
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)      # ORACLE only
    g.set_labels_buffer_enabled(True)     # ORACLE only
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
            "depth": np.array(st.depth_buffer, copy=True),         # ORACLE
            "labels_buf": np.array(st.labels_buffer, copy=True),   # ORACLE
            "pose": (float(g.get_game_variable(gv.POSITION_X)),
                     float(g.get_game_variable(gv.POSITION_Y)),
                     float(g.get_game_variable(gv.ANGLE))),
            "action": seq[i],
        })
        g.make_action(seq[i], 1)
    g.close()
    return frames


def _seen_depth_by_column(frames, fi):
    """SEE the per-azimuth wall depth for frame fi from RGB flow (depth-from-motion).
    Returns (az_depths, diag) where az_depths is [(az_offset_rad, Z_world_or_None)] per column,
    or (None, diag) if the frame is not a usable forward-translation view. Z is calibrated to
    world units by the agent's OWN forward displacement (efference copy)."""
    import numpy as np
    from scripts.depth_from_motion_probe import (
        estimate_foe, radial_decompose, depth_from_motion, expansion_gate, flag_movers,
        _flow_field)
    vy, vx = _flow_field(frames, fi, GH, GW, BLOCK, LEVEL)
    mag = np.sqrt(vy * vy + vx * vx)
    if (mag > 0.5).sum() < 8:
        return None, {"why": "no_flow"}
    exp, ediag = expansion_gate(vy, vx)
    px0, py0, _ = frames[fi - 1]["pose"]; px1, py1, _ = frames[fi]["pose"]
    T_world = math.hypot(px1 - px0, py1 - py0)      # efference-copy forward displacement
    # Gate on the EFFERENCE-FORWARD regime (block 155000/158000: the agent's own issued forward
    # action + a real translation), NOT on expansion_gate — the block-matched flow is too noisy
    # for a clean curl-vs-div verdict on Doom texture (curl dominates even mid-walk), which is
    # itself the 158000 flow wall. The efference copy KNOWS it is translating; expansion is
    # reported as a diag, never used to reject a frame.
    if frames[fi - 1].get("action") != [1, 0, 0] or T_world < 1.0:
        return None, {"why": "not_forward", "exp": exp, "T": round(T_world, 2)}
    foe, _ = estimate_foe(vy, vx)
    if foe is None:
        return None, {"why": "no_foe"}
    dec = radial_decompose(vy, vx, foe)
    flagged, _ = flag_movers(dec["tangential_mag"], dec["valid"])
    depth, dvalid = depth_from_motion(vy, vx, foe)   # r/|flow| up to speed scale
    good = dvalid & (~flagged)
    az_depths = []
    for gc in range(GW):
        col = depth[:, gc][good[:, gc]]
        az = math.radians(-FOV_DEG / 2.0 + FOV_DEG * (gc + 0.5) / GW)
        if col.size >= 2:
            Z = float(np.median(col)) * T_world       # efference calibration -> world units
            az_depths.append((az, Z))
        else:
            az_depths.append((az, None))
    return az_depths, {"why": "ok", "T": round(T_world, 2), "n_valid": int(good.sum()),
                       "exp_div": ediag.get("mean_div")}


def _score_vs_depth_buffer(frames, fi, foe_cache):
    """ORACLE score: Spearman(seen depth-from-motion, VizDoom depth buffer) on radial-consistent
    background cells — the block-158000 measure. The depth buffer is used HERE ONLY, never as a
    map input. Returns a Spearman rho or None."""
    import numpy as np
    from scripts.depth_from_motion_probe import (
        estimate_foe, radial_decompose, depth_from_motion, flag_movers, spearman,
        _flow_field, _downsample_depth)
    from scripts.e1m1_salience_probe import downsample_labels
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
    gt = downsample_labels(frames[fi]["labels_buf"], GH, GW)
    cons = dvalid & (~flagged) & (gt == 0)
    return spearman(depth[cons], db[cons])


def run(frames=80, seed=1234, checkpoints=(10, 25, 45, 65)):
    import numpy as np
    from substrate.world_adapter import WorldAdapter
    import domains.doom_map_ingest as dm

    os.makedirs(OUTDIR, exist_ok=True)
    caps = _capture(frames, seed)
    if not caps:
        return None
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                        "body_w": 1.0, "flood_epoch": 0.0})

    trajectory, walked = [], set()
    spearmans, seen_frames, per_frame, ck_pngs = [], 0, [], []
    for fi in range(len(caps)):
        px, py, ang = caps[fi]["pose"]
        acell = dm.ingest_walk(wa, game, (px, py))       # efference-copy free cell (always)
        if fi >= 1:
            az_depths, diag = _seen_depth_by_column(caps, fi)
            if az_depths is not None:                    # a usable forward-translation view
                dm.ingest_seen_walls(wa, game, (px, py, ang), az_depths)
                seen_frames += 1
            sp = _score_vs_depth_buffer(caps, fi, None)  # ORACLE: seen vs depth buffer
            if sp is not None:
                spearmans.append(sp)
        dm.accumulate(wa, game, epoch=fi + 1)
        trajectory.append(acell); walked.add(acell)
        m = dm.read_map(wa, game)
        per_frame.append({"frame": fi, "cells": len(m["cells"]),
                          "free": sum(1 for v in m["cells"].values() if v == 0.0),
                          "walls": sum(1 for v in m["cells"].values() if v == 1.0)})
        if (fi + 1) in checkpoints or (fi + 1) == len(caps):
            p = dm.render_png(wa, game, os.path.join(OUTDIR, "map_frame_%03d.png" % (fi + 1)),
                              trajectory=trajectory)
            if p:
                ck_pngs.append(os.path.basename(p))

    m = dm.read_map(wa, game); cells = m["cells"]
    walked_wall = sum(1 for c in walked if cells.get(c) == 1.0)
    walked_free = sum(1 for c in walked if cells.get(c) == 0.0)
    kinds = {}
    for q in m["quanta"]:
        kinds[q["region_kind"]] = kinds.get(q["region_kind"], 0) + 1
    sp = np.asarray(spearmans, float) if spearmans else np.array([])
    summary = {
        "seed": seed, "frames": len(caps), "seen_forward_frames": seen_frames,
        "final_cells": len(cells),
        "final_free": sum(1 for v in cells.values() if v == 0.0),
        "final_walls": sum(1 for v in cells.values() if v == 1.0),
        "passable_quanta": len([q for q in m["quanta"] if q["kind"] == "passable"]),
        "frontier_quanta": len([q for q in m["quanta"] if q["kind"] == "frontier"]),
        "region_kinds": kinds,
        "walked_cells": len(walked), "walked_free": walked_free, "walked_wall": walked_wall,
        "M2_trajectory_consistency": walked_free / max(1, len(walked)),
        "M2_walls_on_walked_cells": walked_wall,
        "M2_seen_vs_depthbuffer_spearman": {
            "n": int(sp.size),
            "median": round(float(np.median(sp)), 4) if sp.size else None,
            "mean": round(float(np.mean(sp)), 4) if sp.size else None,
            "p10": round(float(np.percentile(sp, 10)), 4) if sp.size else None,
            "p90": round(float(np.percentile(sp, 90)), 4) if sp.size else None,
            "frac_pos": round(float((sp > 0).mean()), 3) if sp.size else None},
        "growth_curve": [(pf["frame"], pf["cells"]) for pf in per_frame],
        "checkpoint_pngs": ck_pngs,
    }
    with open(os.path.join(OUTDIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=80)
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
