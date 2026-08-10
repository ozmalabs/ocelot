"""doom_map_ingest — the MECHANICAL world-adapter side of the persistent in-graph map
(block 161000-161999). NO agent decision lives here (CLAUDE.md): every function is either
(a) sensor -> graph tokens, (b) fire the existing space_quantize primitive + run_rules, or
(c) read the graph map back out for scoring / display. The ACCUMULATION and area-TYPING
decisions are all rules in seeds/doom_ingraph_map.json.

The three mechanical jobs:

  ingest_frame  pose (self-motion / efference copy) + depth range-vision -> ObsCell world
                points on the game node.  The agent's own cell is walk-free; each depth ray
                is free up to its hit and a wall AT the hit (depth < range).  Pure geometry,
                the marine's LIDAR (doom_world frames the depth buffer as "range vision").

  accumulate    run_rules (the dm_* accumulation rules GROW/merge the belief) -> clean up the
                consumed ObsCells -> space_quantize (existing Rust primitive: belief ->
                SpaceQuantum passable/frontier boxes) -> run_rules (the dm_kind_* typing rules
                label each area).  The exact cadence of quanta_flood_step; decisions are rules.

  read_map / render_png   read the has_cell belief + SpaceQuantum boxes FROM the graph and
                (optionally) rasterise a small top-down PNG.  Mechanical query only.

Calibration reused, not tuned (§13): cell size 64 world units is doom_world's OWN grid
(x_bin = x // 64); FOV 90 deg + distance = raw_depth * depth_scale is the GraphEye's own
depth front-end (domains/vision_graph.py); depth_scale / observation_radius come from the
world's vision_calibration.  None of these fall out of a score.
"""
from __future__ import annotations

import math

CELL = 64.0  # world units per map cell — doom_world's own bin (Body.x_bin = int(x // 64)).


# --------------------------------------------------------------------------- ingest
def _pose_from_sub(sub):
    """Read the marine's pose (x, y, angle_deg) from the Body node the doom_world adapter
    built. Mechanical query — no interpretation."""
    for n in sub.graph.nodes("Body"):
        a = n.attrs
        return float(a["x"]), float(a["y"]), float(a.get("angle", 0.0))
    return None


def _emit(wa, game, obs):
    """Emit a frame's (pose, src) observations as ObsCell nodes, after per-frame sensor
    fusion (one obs per cell, walk > depth_wall > depth_free — mechanical, NOT a map
    decision; cross-FRAME merges stay the rules' job)."""
    S, I = wa.s, wa.inner
    _rank = {"walk": 2, "depth_wall": 1, "depth_free": 0}
    best = {}
    for pose, src in obs:
        if pose not in best or _rank[src] > _rank[best[pose]]:
            best[pose] = src
    for (cx, cy), src in best.items():
        o = S.add_node("ObsCell", {"pose": [int(cx), int(cy)], "src": src})
        I.add_edge_unchecked(game, "observed", o)
    return len(best)


def ingest_walk(wa, game, pose_xy, *, cell=CELL):
    """Mechanical (efference copy / self-motion, block 155000): the cell the agent STANDS in
    is first-hand FREE. Emits one walk ObsCell. Returns the agent cell (cx, cy)."""
    px, py = float(pose_xy[0]), float(pose_xy[1])
    acx, acy = int(math.floor(px / cell)), int(math.floor(py / cell))
    _emit(wa, game, [((acx, acy), "walk")])
    return (acx, acy)


def ingest_seen_walls(wa, game, pose_xyang, az_depths, *, cell=CELL, max_range_cells=16):
    """Mechanical: register SEEN wall geometry into the map from depth-from-MOTION output.

    az_depths is a list of (azimuth_offset_rad, Z_world) the caller recovered by SEEING —
    depth-from-motion on the RGB flow (block 158000: estimate_foe / radial_decompose /
    depth_from_motion), calibrated to world units by the agent's own forward displacement
    (efference copy). This function does NO perception and reads NO depth buffer — it only
    places the SEEN depth at world coordinates via the known pose. Cells before each hit are
    free line-of-sight; the hit cell is a wall. Returns the number of observations emitted."""
    px, py, ang = float(pose_xyang[0]), float(pose_xyang[1]), float(pose_xyang[2])
    facing = math.radians(ang)
    obs = []
    for az, Z in az_depths:
        if Z is None or Z <= 0:
            continue
        dist_cells = (Z / cell)
        world_ang = facing + az
        steps = int(min(dist_cells, max_range_cells))
        for s in range(1, steps + 1):
            wx = px + math.cos(world_ang) * s * cell
            wy = py + math.sin(world_ang) * s * cell
            obs.append(((int(math.floor(wx / cell)), int(math.floor(wy / cell))), "depth_free"))
        if dist_cells < max_range_cells:
            wx = px + math.cos(world_ang) * dist_cells * cell
            wy = py + math.sin(world_ang) * dist_cells * cell
            obs.append(((int(math.floor(wx / cell)), int(math.floor(wy / cell))), "depth_wall"))
    return _emit(wa, game, obs)


# --------------------------------------------------------------------------- accumulate
def accumulate(wa, game, *, focus=None, body_extents=(1, 1), passable_values=(0, 2), epoch=1):
    """Mechanical cadence (the quanta_flood_step precedent): let the accumulation rules GROW
    the belief, clean up consumed ObsCells, fire space_quantize, let the typing rules label.
    Every DECISION inside is a rule; this only ticks and calls the primitive."""
    S, I = wa.s, wa.inner
    I.run_rules()                                        # dm_free_new / dm_wall_new / dm_walk_frees_wall
    for o in list(I.neighbours(game, "observed")):       # consumed by the accumulation this tick
        I.remove_node(o)
    # decode the persistent belief into SpaceQuantum boxes over the current focus
    poses = [tuple(S.node(c)["attrs"]["pose"]) for c in I.neighbours(game, "has_cell")]
    if not poses:
        return {"quanta": 0, "portals": 0, "frontiers": 0}
    xs = [p[0] for p in poses]; ys = [p[1] for p in poses]
    if focus is None:
        focus = ([min(xs), min(ys)], [max(xs), max(ys)])
    lo = [int(focus[0][0]), int(focus[0][1])]
    hi = [int(focus[1][0]), int(focus[1][1])]
    gid = int(str(game).lstrip("#"))
    res = I.space_quantize(gid, 2, "%dx%d" % (int(body_extents[0]), int(body_extents[1])),
                           [int(v) for v in passable_values], lo, hi, int(epoch),
                           [int(body_extents[0]), int(body_extents[1])], None,
                           [int(body_extents[0]), int(body_extents[1])])
    I.run_rules()                                        # dm_kind_room / _corridor / _area / _frontier / _lava
    return dict(res)


# --------------------------------------------------------------------------- read / display
def read_map(wa, game):
    """Mechanical read of the graph map: {cells:{(x,y):value}, quanta:[{lo,hi,kind,region_kind}],
    objects:[{pose,name}]}. Everything is read FROM the graph — nothing is a Python array."""
    S, I = wa.s, wa.inner
    cells = {}
    for c in I.neighbours(game, "has_cell"):
        a = S.node(c)["attrs"]
        cells[tuple(int(v) for v in a["pose"])] = float(a["value"])
    quanta = []
    for q in S.nodes("SpaceQuantum"):
        if game not in list(I.neighbours(q, "in_space")):
            continue
        a = S.node(q)["attrs"]
        quanta.append({"lo": tuple(int(v) for v in a["lo"]), "hi": tuple(int(v) for v in a["hi"]),
                       "kind": a.get("kind"), "region_kind": a.get("region_kind")})
    objects = []
    for m in I.neighbours(game, "map_object"):
        a = S.node(m)["attrs"]
        objects.append({"pose": tuple(int(v) for v in a["pose"]), "name": a.get("name")})
    return {"cells": cells, "quanta": quanta, "objects": objects}


# top-down colours for the human area kinds (RGB)
_KIND_RGB = {"room": (70, 130, 200), "corridor": (90, 200, 120), "area": (200, 190, 90),
             "lava": (210, 90, 60), "frontier": (120, 90, 160), None: (110, 110, 110)}


def render_png(wa, game, path, *, trajectory=None, scale=10):
    """Mechanical rasteriser: top-down PNG of the graph map. Free cells grey, walls black,
    unknown (absent) white, region-kind tint over passable quanta, objects as dots, the
    trajectory as a red path. Reads FROM the graph only — the 'watch it build its world
    model' readout."""
    import numpy as np
    m = read_map(wa, game)
    cells = m["cells"]
    if not cells and not (trajectory or []):
        return None
    allpts = list(cells.keys()) + list(trajectory or [])
    xs = [p[0] for p in allpts]; ys = [p[1] for p in allpts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    Wc, Hc = (x1 - x0 + 1), (y1 - y0 + 1)
    img = np.full((Hc, Wc, 3), 255, np.uint8)            # unknown = white (absence, first-class)
    for (x, y), v in cells.items():
        img[y - y0, x - x0] = (30, 30, 30) if v == 1.0 else (190, 190, 190)  # wall dark / free grey
    # tint passable quanta by region kind (drawn under objects/trajectory)
    for q in m["quanta"]:
        col = _KIND_RGB.get(q["region_kind"], _KIND_RGB[None])
        (lx, ly), (hx, hy) = q["lo"], q["hi"]
        for x in range(lx, hx + 1):
            for y in range(ly, hy + 1):
                if (x, y) in cells and cells[(x, y)] != 1.0:
                    px = img[y - y0, x - x0].astype(int)
                    img[y - y0, x - x0] = tuple((px + np.array(col)) // 2)
    for o in m["objects"]:
        x, y = o["pose"]
        if x0 <= x <= x1 and y0 <= y <= y1:
            img[y - y0, x - x0] = (255, 220, 0)
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
