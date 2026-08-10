"""doom_allo_surface_ingest — the MECHANICAL world-adapter for the ALLOCENTRIC held-surface
MAP reconstruction (block 203000-203999). NO agent decision lives here (CLAUDE.md): every
function is (a) sensor -> world-registered graph tokens, (b) advance the game innovation clock +
fire run_rules (the as_* rules mint/blend/decay/demote/promote the AlloCell belief), or (c) read
the graph map back out for scoring / display. The ACCUMULATION, DECAY, and DEMOTION decisions
are ALL rules in seeds/doom_allocentric_surface.json.

The map IS the held surface (180000) in WORLD coordinates: as the eye moves, each SEEN
observation (a world cell + its observed luminance, placed by the marine's pose) is accumulated
into a persistent AlloCell{pose,value,dwell,freshness,tier,...} on the game node. Dwelt cells
super-resolve (dwell climbs, value denoises); long-unseen cells demote (fresh->gist->latent,
retained + promotable); the occupancy geom stays SEEN (depth-from-motion, 158000).

The three mechanical jobs:

  ingest_frame  pose (self-motion / efference copy) + per-azimuth SEEN depth-from-motion +
                per-azimuth observed luminance -> world ObsCell tokens (pose, lum, src, geom,
                epoch). Pure geometry + photometry registration; NO map decision.

  accumulate    set game.map_epoch (the ONE mechanical clock write) -> run_rules (the as_* rules
                GROW/blend/decay/demote the AlloCell belief) -> clean up consumed ObsCells. The
                exact cadence; every DECISION inside is a rule. Returns a deterministic
                work-count (cells minted + cells blended this frame — the 185000 dirty tie-in).

  read_map / render_png   read the has_allo_cell belief FROM the graph and (optionally) rasterise
                a top-down PNG (occupancy + held luminance + tier). Mechanical query only.

Calibration reused, not tuned (161000 §13): cell size 64 world units is doom_world's OWN grid;
FOV 90 deg is the engine. The AlloParams (decay/tier knobs) are graph DATA on the game node — the
opt-in flag; absent them the whole loop is inert and every existing path is byte-identical.
"""
from __future__ import annotations

import math

CELL = 64.0  # world units per map cell — doom_world's own bin (Body.x_bin = int(x // 64)).


# --------------------------------------------------------------------------- params (opt-in flag)
def install_params(wa, game, **overrides):
    """Create the opt-in AlloParams node that ENABLES the loop (default-OFF: absent it, every
    as_* rule's `enabled` guard fails and the belief never grows). Mechanical config write — the
    knobs are graph DATA. `uniform=1` pins half_life (a fixed-rate control for the gate)."""
    S, I = wa.s, wa.inner
    p = {"enabled": 1.0, "c0": 64.0, "lr_min": 0.1, "hl0": 4.0, "hl_scale": 4.0, "hl_min": 1.0,
         "uniform": 0.0, "uniform_hl": 4.0, "t_fresh": 64.0, "t_gist": 8.0, "k_gist": 2.0}
    p.update({k: float(v) for k, v in overrides.items()})
    n = S.add_node("AlloParams", p)
    I.add_edge_unchecked(game, "has_allo_params", n)
    return n


# --------------------------------------------------------------------------- ingest
_RANK = {"walk": 2, "depth_wall": 1, "depth_free": 0}
_GEOM = {"walk": 0.0, "depth_free": 0.0, "depth_wall": 1.0}


def _emit(wa, game, obs, epoch):
    """Emit a frame's (pose, src, lum) observations as ObsCell tokens, after per-frame sensor
    fusion (one obs per cell, walk > depth_wall > depth_free — mechanical, NOT a map decision;
    cross-FRAME merges stay the rules' job — the 161000 within-frame-duplicate fix)."""
    S, I = wa.s, wa.inner
    best = {}
    for pose, src, lum in obs:
        p = (int(pose[0]), int(pose[1]))
        if p not in best or _RANK[src] > _RANK[best[p][0]]:
            best[p] = (src, float(lum))
    for (cx, cy), (src, lum) in best.items():
        o = S.add_node("ObsCell", {"pose": [int(cx), int(cy)], "src": src, "lum": float(lum),
                                   "geom": _GEOM[src], "epoch": float(epoch)})
        I.add_edge_unchecked(game, "observed", o)
    return len(best)


def ingest_walk(wa, game, pose_xy, lum, epoch, *, cell=CELL):
    """Mechanical (efference copy / self-motion, 155000): the cell the agent STANDS in is
    first-hand FREE, appearance = the floor luma. Returns the agent cell (cx, cy)."""
    px, py = float(pose_xy[0]), float(pose_xy[1])
    acx, acy = int(math.floor(px / cell)), int(math.floor(py / cell))
    _emit(wa, game, [((acx, acy), "walk", lum)], epoch)
    return (acx, acy)


def ingest_seen(wa, game, pose_xyang, az_lum_depths, epoch, *, cell=CELL, max_range_cells=16):
    """Mechanical: register SEEN geometry + appearance into world coordinates from
    depth-from-MOTION output. az_lum_depths is [(azimuth_offset_rad, Z_world_or_None, luma)] the
    caller recovered by SEEING (depth-from-motion on the RGB flow, 158000; luma from the same RGB
    column). Depth placed at world coordinates via the KNOWN pose. Cells before each hit are
    free line-of-sight (they get the column's luma too); the hit cell is a wall with the column's
    surface luma. Reads NO depth/labels buffer. Returns the number of observations emitted."""
    px, py, ang = float(pose_xyang[0]), float(pose_xyang[1]), float(pose_xyang[2])
    facing = math.radians(ang)
    obs = []
    for az, Z, lum in az_lum_depths:
        if Z is None or Z <= 0:
            continue
        dist_cells = (Z / cell)
        world_ang = facing + az
        steps = int(min(dist_cells, max_range_cells))
        for s in range(1, steps + 1):
            wx = px + math.cos(world_ang) * s * cell
            wy = py + math.sin(world_ang) * s * cell
            obs.append(((int(math.floor(wx / cell)), int(math.floor(wy / cell))), "depth_free", lum))
        if dist_cells < max_range_cells:
            wx = px + math.cos(world_ang) * dist_cells * cell
            wy = py + math.sin(world_ang) * dist_cells * cell
            obs.append(((int(math.floor(wx / cell)), int(math.floor(wy / cell))), "depth_wall", lum))
    return _emit(wa, game, obs, epoch)


# --------------------------------------------------------------------------- accumulate
def accumulate(wa, game, epoch):
    """Mechanical cadence: set the game innovation clock (ONE write), let the as_* rules
    GROW/blend/decay/demote the AlloCell belief, clean up consumed ObsCells. Every DECISION
    inside is a rule; this only stamps the clock and ticks. Returns a deterministic work-count:
    {minted, blended} = the 185000 dirty signal (cells created + cells re-processed this frame)."""
    S, I = wa.s, wa.inner
    before = {tuple(int(v) for v in S.node(c)["attrs"]["pose"]): S.node(c)["attrs"]["last_refresh_epoch"]
              for c in I.neighbours(game, "has_allo_cell")}
    S.set_attr(game, "map_epoch", float(epoch))
    I.run_rules()
    after = {tuple(int(v) for v in S.node(c)["attrs"]["pose"]): S.node(c)["attrs"]["last_refresh_epoch"]
             for c in I.neighbours(game, "has_allo_cell")}
    minted = len([p for p in after if p not in before])
    blended = len([p for p in after if p in before and after[p] != before[p]])
    for o in list(I.neighbours(game, "observed")):
        I.remove_node(o)
    return {"minted": minted, "blended": blended, "work": minted + blended}


# --------------------------------------------------------------------------- read / display
def read_map(wa, game):
    """Mechanical read of the graph map: {(x,y): {value, dwell, freshness, tier, stored, geom}}.
    Everything read FROM the has_allo_cell belief — nothing is a Python array."""
    S, I = wa.s, wa.inner
    cells = {}
    for c in I.neighbours(game, "has_allo_cell"):
        a = S.node(c)["attrs"]
        cells[tuple(int(v) for v in a["pose"])] = {
            "value": float(a["value"]), "dwell": int(a["dwell"]), "freshness": int(a["freshness"]),
            "tier": int(a["tier"]), "stored": float(a["stored"]), "geom": int(a["geom"])}
    return cells


# tier tint (RGB) for the top-down figure: fresh bright, gist dim, latent faint
_TIER_RGB = {2: (90, 200, 120), 1: (200, 190, 90), 0: (150, 110, 160)}


def render_png(wa, game, path, *, trajectory=None, scale=10):
    """Mechanical rasteriser: top-down PNG of the reconstructed allocentric map. Walls dark,
    free cells shaded by held luminance (super-resolution visible as it denoises), tier tint over
    free cells (fresh green / gist yellow / latent violet), unknown (absent) white, trajectory
    red. Reads FROM the graph only — the 'watch it reconstruct the level' readout."""
    import numpy as np
    cells = read_map(wa, game)
    if not cells and not (trajectory or []):
        return None
    allpts = list(cells.keys()) + list(trajectory or [])
    xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    Wc, Hc = (x1 - x0 + 1), (y1 - y0 + 1)
    img = np.full((Hc, Wc, 3), 255, np.uint8)                 # unknown = white (absence)
    vals = [c["value"] for c in cells.values() if c["geom"] == 0]
    vlo, vhi = (min(vals), max(vals)) if vals else (0.0, 1.0)
    vspan = max(1e-6, vhi - vlo)
    for (x, y), c in cells.items():
        if c["geom"] == 1:
            img[y - y0, x - x0] = (30, 30, 30)                # wall dark
        else:
            g = int(60 + 180 * (c["value"] - vlo) / vspan)    # free shaded by held luminance
            g = max(0, min(255, g))
            tint = _TIER_RGB.get(c["tier"], (128, 128, 128))
            img[y - y0, x - x0] = tuple((np.array([g, g, g]) + np.array(tint)) // 2)
    for (x, y) in (trajectory or []):
        if x0 <= x <= x1 and y0 <= y <= y1:
            img[y - y0, x - x0] = (220, 30, 30)
    big = np.repeat(np.repeat(img, scale, 0), scale, 1)
    try:
        from PIL import Image
        Image.fromarray(big, "RGB").save(path)
    except Exception:
        _write_ppm(path.rsplit(".", 1)[0] + ".ppm", big)
        path = path.rsplit(".", 1)[0] + ".ppm"
    return path


def _write_ppm(path, img):
    import numpy as np
    H, W, _ = img.shape
    with open(path, "wb") as f:
        f.write(b"P6\n%d %d\n255\n" % (W, H))
        f.write(np.asarray(img, np.uint8).tobytes())
