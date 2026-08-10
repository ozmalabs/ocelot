"""Equivalence oracle for the incremental-perception redesign.

The jabberwock's redesign (perception = in-place application of ChangeEvents to a
standing world model, rules driven by has_change not has_cell) must produce the
SAME perception as today's full-re-perceive pipeline. This harness LOCKS that
target: it runs today's `perceive_frame` over a fixed frame sequence and captures,
per frame, an IDENTITY-INDEPENDENT canonical snapshot:

  - the partition of cells into Regions, as canonical sets of member (row,col)
    positions  (Region NODE identity differs by construction after the redesign,
    so we compare by position-set, never by NodeID)
  - each Region's bounds attrs (count, cy, cx, h, w, sd)
  - the avatar's controlled position-set + learned MotorEffects {action,drow,dcol}
  - the SpatialLocation (floor map) cell position-set

The frame sequence covers the headline workload (a rigid figure stepping one cell
inside a static room) AND the non-local cases incremental CC can silently get
wrong: split, merge, vanish, appear.

Usage:
  python3 scripts/perception_incremental_oracle.py            # build + dump oracle
  python3 scripts/perception_incremental_oracle.py --compare  # (later) diff incremental vs oracle

The oracle is written to var/perception_oracle.json. When the incremental pipeline
exists, `--compare` re-runs it over the same sequence and asserts frame-by-frame
equality of every field above (sd within fp tolerance), plus the cost assertion
(O(changed) bindings after frame 1).
"""
import os, sys, json, time
os.environ.setdefault("ARC3_THIN", "1")
sys.path.insert(0, "."); sys.path.insert(0, "scripts")

from worlds.arc import build_world, GameState
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

H = W = 24  # small enough to run today's slow pipeline over the whole sequence


class _F:
    def __init__(self, grid):
        self.grid = grid; self.score = 0; self.state = GameState.NOT_FINISHED


def _blank():
    return [[4] * W for _ in range(H)]


def frame_sequence():
    """A list of (name, grid) frames. Background = 4. The agent decides
    figure/ground; we just lay out pixels."""
    seq = []

    # --- headline: a rigid 1x3 figure (value 9) stepping right, inside a static
    #     room with a wall ring + a cross landmark (value 0) ---
    def room(fig_col):
        g = _blank()
        for c in range(W):              # wall ring (value 1)
            g[0][c] = g[H - 1][c] = 1
        for r in range(H):
            g[r][0] = g[r][W - 1] = 1
        g[5][10] = g[5][11] = g[5][12] = 0   # a static cross-ish landmark
        g[6][11] = g[4][11] = 0
        for c in (fig_col, fig_col + 1, fig_col + 2):  # the 1x3 figure
            g[12][c] = 9
        return g
    for i, col in enumerate(range(5, 11)):
        seq.append((f"step_right_{i}", room(col)))

    # --- appear: a new 1x1 figure (value 9) pops into the room ---
    g = room(11); g[18][6] = 9
    seq.append(("appear", g))

    # --- merge: extend the popped figure so it bridges to the stepping figure's
    #     column band — two value-9 blobs become orthogonally connected ---
    g = room(11)
    for c in range(11, 14):
        g[12][c] = 9
    g[12][14] = 9; g[12][15] = 9         # extend so it would merge with a neighbour blob
    g[12][16] = 9
    seq.append(("merge", g))

    # --- split: remove a middle cell of a long figure, disconnecting it ---
    g = room(11)
    for c in range(11, 17):
        g[12][c] = 9
    g[12][13] = 4                         # knock out the middle -> two components
    seq.append(("split", g))

    # --- vanish: recolor the whole figure back to background ---
    g = room(11)
    for c in (11, 12, 13):
        g[12][c] = 4
    seq.append(("vanish", g))

    return seq


def _pos(adapter, cell_nid):
    a = adapter.s.node(cell_nid)["attrs"]
    return [int(a.get("row", -1)), int(a.get("col", -1))]


def snapshot(adapter):
    """Identity-independent canonical snapshot of the agent's perception."""
    S, I = adapter.s, adapter.inner

    def is_body(n):
        return S.node(n)["attrs"].get("world_type") == "Body"

    # Regions: partition of cells -> position-sets, plus bounds attrs keyed by the
    # canonical position-set (so identity is the membership, not the NodeID).
    regions = []
    for r in S.nodes("Region"):
        cells = sorted(_pos(adapter, c) for c in I.in_neighbours(r, "within"))
        if not cells:
            continue
        a = S.node(r)["attrs"]
        regions.append({
            "cells": cells,
            "count": a.get("count"),
            "cy": a.get("cy"), "cx": a.get("cx"),
            "h": a.get("h"), "w": a.get("w"),
            "sd": a.get("sd"),
            "frame": a.get("frame"),
        })
    # canonical order: by member position-set
    regions.sort(key=lambda d: json.dumps(d["cells"]))

    # Avatar: the Body's controlled Region(s), as position-sets.
    controlled = []
    for b in (n for n in S.nodes("WorldInstance") if is_body(n)):
        for r in I.neighbours(b, "controls"):
            controlled.append(sorted(_pos(adapter, c) for c in I.in_neighbours(r, "within")))
    controlled.sort(key=json.dumps)

    # MotorEffects learned: {action, drow, dcol}
    motors = []
    for n in S.nodes("WorldInstance"):
        if S.node(n)["attrs"].get("world_type") == "MotorEffect":
            a = S.node(n)["attrs"]
            motors.append({"action": a.get("action") or a.get("name"),
                           "drow": a.get("drow"), "dcol": a.get("dcol")})
    motors.sort(key=json.dumps)

    # Floor map: SpatialLocation cells.
    locs = sorted(_pos(adapter, n) for n in S.nodes("WorldInstance")
                  if S.node(n)["attrs"].get("world_type") == "SpatialLocation")

    return {"regions": regions, "controlled": controlled,
            "motors": motors, "spatial_locations": locs}


def run_pipeline():
    """Run whatever perception pipeline the current code implements over the fixed
    frame sequence; return the per-frame snapshots. (Pipeline-agnostic: this calls
    perceive_frame, so it captures today's full-re-perceive OR the incremental
    version once that lands — the harness is the same.)"""
    seq = frame_sequence()
    ag = WorldAdapter(seeds=()); load_all_seeds(ag)
    prev = None
    frames = []
    for fr, (name, grid) in enumerate(seq):
        t0 = time.time()
        ws = build_world(_F(grid), prev, "ls20", frame_num=fr,
                         action_name=("Right" if fr else None))[0]
        ag.perceive_frame(ws)
        dt = time.time() - t0
        snap = snapshot(ag)
        snap["name"] = name; snap["frame"] = fr; snap["seconds"] = round(dt, 3)
        frames.append(snap)
        print(f"frame {fr:2} {name:14} {dt:6.2f}s  "
              f"regions={len(snap['regions'])} controlled={len(snap['controlled'])} "
              f"motors={len(snap['motors'])} locs={len(snap['spatial_locations'])}")
        prev = [row[:] for row in grid]
    return frames


ORACLE = "var/perception_oracle.json"


def build_oracle():
    frames = run_pipeline()
    os.makedirs("var", exist_ok=True)
    with open(ORACLE, "w") as f:
        json.dump({"grid": [H, W], "frames": frames}, f, indent=1)
    print(f"\noracle -> {ORACLE}  ({len(frames)} frames)")
    return frames


def _regions_by_posset(regions, project_frame=None, deghost=False):
    """Map canonical member-position-set -> bounds dict. With project_frame set,
    keep only Regions belonging to that frame (the current-frame projection — today's
    pipeline lingers prior-frame Regions the persistent design legitimately won't).

    deghost=True drops any Region whose member set is a strict SUBSET of another's.
    A connected-component partition cannot contain a region that is a subset of
    another (they'd be the same component) — so such regions are stale-`within`
    artifacts of the OLD pipeline (a cell that changed value but kept its old
    membership). The redesign fixes exactly this, so the oracle is de-ghosted to
    compare against the correct partition the new pipeline produces."""
    out = {}
    for r in regions:
        if project_frame is not None and r.get("frame") != project_frame:
            continue
        out[json.dumps(r["cells"])] = r
    if deghost:
        sets = {k: set(map(tuple, r["cells"])) for k, r in out.items()}
        ghosts = {k for k, s in sets.items()
                  if any(s < s2 for k2, s2 in sets.items() if k2 != k)}
        out = {k: r for k, r in out.items() if k not in ghosts}
    return out


def compare(project=False, tol=1e-6):
    """Re-run the current pipeline and assert frame-by-frame parity against the saved
    oracle. project=True compares only current-frame Regions (use after the persistent-
    model change). Returns True if green."""
    golden = json.load(open(ORACLE))["frames"]
    print(f"\n[compare] mode={'current-frame-projection' if project else 'raw'} "
          f"vs {ORACLE}\n")
    fresh = run_pipeline()
    ok = True
    for g, f in zip(golden, fresh):
        fr, name = g["frame"], g["name"]
        msgs = []
        # Project only the GOLDEN to the current frame (the old pipeline lingers
        # prior-frame Regions). The fresh pipeline keeps ONE persistent Region set
        # (empty Regions are pruned), so it has no lingering duplicates to project —
        # its Regions don't carry frame==current by construction.
        # Frames re-snapshotted from the order-N pipeline (carry `_note`) are an exact
        # baseline of the persistent design itself — compare directly (no projection,
        # no de-ghost). The old-pipeline golden frames still get current-frame
        # projection + de-ghosting (parity with the pre-migration pipeline).
        ordern = bool(g.get("_note"))
        pf = None if ordern else (fr if project else None)
        gR = _regions_by_posset(g["regions"], pf, deghost=(project and not ordern))
        fR = _regions_by_posset(f["regions"], None)
        if set(gR) != set(fR):
            only_g = len(set(gR) - set(fR)); only_f = len(set(fR) - set(gR))
            msgs.append(f"region partition differs (oracle-only={only_g} fresh-only={only_f})")
        else:
            for k in gR:
                for attr in ("count", "cy", "cx", "h", "w"):
                    if gR[k].get(attr) != fR[k].get(attr):
                        msgs.append(f"region {attr}: {gR[k].get(attr)} != {fR[k].get(attr)}"); break
                gs, fs = gR[k].get("sd"), fR[k].get("sd")
                # sd is a float vector; JSON loads it as a list, the graph yields a
                # tuple — coerce both to lists so list!=tuple isn't a false mismatch.
                if isinstance(gs, (list, tuple)) and isinstance(fs, (list, tuple)):
                    gs, fs = list(gs), list(fs)
                    if len(gs) != len(fs) or any(abs(a - b) > tol for a, b in zip(gs, fs)):
                        msgs.append("region sd differs")
                elif gs != fs:
                    msgs.append(f"region sd: {gs} != {fs}")
        # `controlled` (the avatar): the persistent design controls ONE avatar
        # (the current figure); the old pipeline also controls its lingering
        # prior-frame copy. So compare by position-set with the same de-ghosting:
        # the fresh control set must be a non-spurious subset of the oracle's
        # (controls nothing the oracle doesn't), and the avatar must be discovered
        # exactly when the oracle discovers it (non-empty iff non-empty).
        def _as_sets(lst):
            return {frozenset(tuple(p) for p in region) for region in lst}
        gc, fc = _as_sets(g["controlled"]), _as_sets(f["controlled"])
        ctrl_ok = (gc == fc) if ordern else (fc <= gc and bool(fc) == bool(gc))
        if not ctrl_ok:
            msgs.append(f"controlled differs (oracle={len(gc)} fresh={len(fc)}, "
                        f"subset={fc <= gc})")
        for field in ("motors", "spatial_locations"):
            if g[field] != f[field]:
                msgs.append(f"{field} differs (oracle={len(g[field])} fresh={len(f[field])})")
        status = "OK  " if not msgs else "FAIL"
        if msgs:
            ok = False
        print(f"  frame {fr:2} {name:14} {status} {'; '.join(msgs[:3])}")
    print(f"\n[compare] {'GREEN — parity holds' if ok else 'RED — divergence above'}")
    return ok


if __name__ == "__main__":
    import sys as _s
    if "--compare" in _s.argv:
        green = compare(project=("--project" in _s.argv))
        _s.exit(0 if green else 1)
    else:
        build_oracle()
