"""FALLING WORLD — a thin pixel-only world adapter (physics from observation).

The world's ONLY output is a **pixel/cell value field** (0 = background,
1 = object). A single blob falls under ONE untuned constant gravity; each tick
the adapter renders the blob's CURRENT position into a value grid and hands the
pixels to the eye (`segment_and_track`). It then advances the blob's Python-local
position by semi-implicit Euler integer physics (v += g; y += v).

DISCIPLINE (CLAUDE.md — the agent is a graph; Python is only the world adapter):
- The blob's position / velocity / gravity live ONLY as Python locals inside the
  generator. **They are NEVER written to the graph.** The graph sees pixels
  (via `segment`) and the eye's own Region perception (cy/cx/drow — the carve).
- No decisions over graph state. `render_*` are pure functions; the perception
  and order-N discovery are EXISTING machinery (`segment_and_track`, the
  `time_axis` seed's order-N rule) the caller composes. This module only
  translates external I/O into pixels and mechanically reads the eye's carve
  back out.

Semi-implicit Euler with integer g is a legitimate DISCRETE gravity: with y0=0,
v0=0, g=1 the perceived centroid walks 0,1,3,6,10,15,21,... (triangular numbers)
whose SECOND difference is the constant g — a uniformly-accelerated fall the
substrate can discover as an order-2 generator from the pixels alone.
"""
from __future__ import annotations

from typing import Iterator


def render_blob(h: int, w: int, top: int, left: int, k: int,
                bg: int = 0, obj: int = 1) -> list[int]:
    """A `h*w` row-major value field: `bg` everywhere, a `k*k` square of `obj`
    at (top, left), clipped to the field. Pure pixels — no kinematics."""
    grid = [bg] * (h * w)
    for r in range(top, top + k):
        if 0 <= r < h:
            base = r * w
            for c in range(left, left + k):
                if 0 <= c < w:
                    grid[base + c] = obj
    return grid


def render_noise(h: int, w: int, rng, hi: int = 2) -> list[int]:
    """A field of incoherent random 0/1 pixels — no object to carve."""
    return [int(x) for x in rng.integers(0, hi, size=h * w)]


def fall_pixels(h: int, w: int, k: int, g: int, *, left: int, v0: int = 0,
                y0: int = 0, max_frames: int = 64) -> list[list[int]]:
    """The untuned constant-gravity fall, as a list of pixel frames.

    Semi-implicit Euler INTEGER physics: each tick `v += g; y += v`. The blob is
    rendered at each position while FULLY VISIBLE (`y + k <= h`), so the eye sees
    a rigid square translating downward. `g` is the untuned gravity constant;
    `y`/`v`/`g` are Python locals only — nothing kinematic reaches the graph.
    """
    frames: list[list[int]] = []
    y, v = y0, v0
    while y + k <= h and len(frames) < max_frames:
        frames.append(render_blob(h, w, y, left, k))
        v += g
        y += v
    return frames


def static_pixels(h: int, w: int, k: int, *, top: int, left: int,
                  n: int) -> list[list[int]]:
    """A stationary blob rendered `n` times — the no-motion control."""
    frame = render_blob(h, w, top, left, k)
    return [list(frame) for _ in range(n)]


def noise_pixels(h: int, w: int, rng, n: int) -> list[list[int]]:
    """`n` frames of incoherent noise — the no-coherent-object control."""
    return [render_noise(h, w, rng) for _ in range(n)]


def setup_world(native, h: int, w: int):
    """Mint the WorldInstance game hub + one bare Cell (WorldInstance) node per
    grid position. Cells carry NO position attribute — `segment_and_track`
    addresses them positionally through the `cell_ids` array, so the object's
    coordinates never appear as a node attribute anywhere. Returns
    (game_node, cell_ids)."""
    game = native.add_node("WorldInstance", {"frame": 0.0})
    cells = [native.add_node("WorldInstance", {}) for _ in range(h * w)]
    cell_ids = [int(str(n).lstrip("#")) for n in cells]
    return game, cell_ids


def read_regions(native, game) -> list[dict]:
    """Mechanically read the eye's carve back out: the Region nodes the eye
    minted under `game -has_region->`, with their perceived centroid/motion."""
    out = []
    for n in native.neighbours(game, "has_region"):
        a = native.node(n)["attrs"]
        out.append({
            "id": int(str(n).lstrip("#")),
            "count": float(a.get("count", 0.0)),
            "cy": float(a.get("cy", 0.0)),
            "cx": float(a.get("cx", 0.0)),
            "drow": float(a.get("drow", 0.0)),
            "dcol": float(a.get("dcol", 0.0)),
            "is_ground": float(a.get("is_ground", 0.0)),
        })
    return out


def perceive(native, game, cell_ids, h: int, w: int,
             frames_pixels: list[list[int]]) -> list[dict | None]:
    """Run the eye (`segment_and_track`) over the pixel frames. For each frame,
    return the non-ground blob (smallest non-ground Region) the eye holds, or
    None if the eye carved no non-ground object. Pure I/O: render pixels in,
    tick the eye, read the carve out."""
    track: list[dict | None] = []
    for fi, vals in enumerate(frames_pixels):
        native.set_attr(game, "frame", float(fi))
        native.segment(game, h, w, vals, cell_ids)
        nonground = [r for r in read_regions(native, game) if r["is_ground"] == 0.0]
        track.append(min(nonground, key=lambda r: r["count"]) if nonground else None)
    return track


DT = ["pred", "coord:r", "coord:c", "val"]
# Order-2 witness minimum: a witnessed constant SECOND difference needs >=2
# second-differences (pyramid rule: all-equal AND len>=2), i.e. >=4 samples.
# This falls out of the finite-difference pyramid, it is not a tuned threshold.
MIN_ORBIT = 4


def boot_falling():
    """Boot a graph-native substrate ready for BOTH the eye and the order-N
    discovery: boot_core + the shape_decode loop + the `time_axis` order-N seed
    (flag ON) + the `region_grouping` productions the eye's has_region/within
    edges need. Returns (s, ag, native). Pure setup — no agent decisions."""
    import json
    import os

    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from substrate.seed_loader import manifest_for

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    s.set_attr(ag, "time_infer_enabled", 1.0)
    # a point ShapeSignature so the rule's codebook_type:ShapeSignature resolves
    s.add_node("ShapeSignature",
               {"name": "pt", "signature": json.dumps([["obj", 0, 0, "obj"]]),
                "kind": "faculty", "faculty": "pt", "dim_types": DT})
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "seeds", "region_grouping.json")) as fh:
        for prod in json.load(fh)["productions"]:
            try:
                native.add_production(prod)
            except Exception:
                pass
    return s, ag, native


def discover_order(s, ag, native, cy_seq, cx_seq):
    """Feed the PERCEIVED centroid trajectory (a point per frame at the eye's
    own cy/cx) into the order-N / `time_axis` path and run the `run_rules`
    fixpoint. The order-N DECISION is the Rust Term + the seed rule; this only
    ingests the perceived points and reads the minted dimension back out.

    Returns (obs_status, mints) where each mint is
    (generator_kind, order, coeffs, offset) read FROM THE GRAPH."""
    frames = [[["obj", int(round(cy)), int(round(cx)), "obj"]]
              for cy, cx in zip(cy_seq, cx_seq)]
    o = s.add_node("Observation",
                   {"frames": frames, "dim_types": DT,
                    "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    status = s.node(o)["attrs"].get("status")
    mints = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:time":
            mints.append((a.get("generator_kind"), a.get("order"),
                          tuple(a.get("coeffs") or ()),
                          tuple(a.get("offset") or ())))
    return status, mints


def longest_continuous_run(track: list[dict | None]) -> list[dict]:
    """The longest run of consecutive frames over which the eye held ONE Region
    id — the object's continuously-tracked trajectory. A break (a different id,
    i.e. death+birth) ends the run. Mechanical: group by adjacent id-equality."""
    best: list[dict] = []
    cur: list[dict] = []
    for b in track:
        if b is None:
            cur = []
            continue
        if cur and b["id"] == cur[-1]["id"]:
            cur.append(b)
        else:
            cur = [b]
        if len(cur) > len(best):
            best = list(cur)
    return best
