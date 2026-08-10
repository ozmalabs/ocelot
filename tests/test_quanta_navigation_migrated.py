"""Part D tests for dynamic, foveated, N-dimensional quanta navigation (FLOOD_DESIGN.md):
the Rust `space_quantize` primitive (belief -> SpaceQuantum boxes + portals + frontiers,
body-conditional, per-dimension residual splits, focus-bounded) composed with the qf_* rules
in seeds/quanta_navigation.json (flood seeding, Bellman relax over portals, hop via the
is_self Region -> responds_via -> ControlResponse chain, frontier commitment, block-driven
stale/portal-flip, closed detection).

Conventions: boots the standard `WorldAdapter` core (substrate.boot_core via WorldAdapter),
loads the ACTUAL seed file through the native `load_seed_manifest` (the same loader
substrate/boot_all.py uses for every seeds/*.json), skips when substrate_rs is missing,
deterministic and self-contained (hand-authored beliefs + the repo's own gen_maze).

The two-phase tick (run_rules; closed=0; run_rules) mirrors the adapter
(domains/spatial_sense.quanta_flood_step): qf_closed must read the CONVERGED qdist field —
the move-space CLOSED-before-FLOOD two-phase precedent.
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "quanta_navigation.json")
FLOOR, WALL = 4, 3


# ---------------------------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------------------------

def _fresh():
    """A core-booted WorldAdapter carrying ONLY the quanta_navigation seed (deterministic,
    no cross-seed interference; the full-boot integration is scripts/maze_run.py's job)."""
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)
    return wa


def _mk_game(wa, avatar_pose):
    return wa.s.add_node("WorldInstance", {"world_type": "Game", "nav_repr": "quanta",
                                           "nav_mode": "seek", "avatar_pose": list(avatar_pose),
                                           "flood_epoch": 0.0})


def _mk_cells_2d(wa, game, grid, values=None):
    """Belief points from a 2D char/int grid: '#'/WALL -> wall value, else floor. Returns
    {(r,c): NodeID}. UNKNOWN cells are simply not created (None entries)."""
    cells = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v is None:
                continue
            val = float(WALL if v in ("#", WALL, 1) else FLOOR)
            n = wa.s.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                                "col": float(c), "value": val})
            cells[(r, c)] = n
            wa.inner.add_edge_unchecked(game, "has_cell", n)
    return cells


def _seed_controls_2d(wa, game):
    """The is_self Region -> responds_via -> ControlResponse chain the qf hop rules Dot-pick
    against (world DATA: the world's action vocabulary and its displacement semantics)."""
    sr = wa.s.add_node("Region", {"is_self": 1.0})
    wa.inner.add_edge_unchecked(game, "has_region", sr)
    for name, (dr, dc) in (("Up", (-1, 0)), ("Down", (1, 0)), ("Left", (0, -1)), ("Right", (0, 1))):
        cr = wa.s.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc), "dz": 0.0,
                                               "cname": name})
        wa.inner.add_edge_unchecked(sr, "responds_via", cr)
    return sr


def _commit_goal(wa, game, pose):
    g = wa.s.add_node("Goal", {"pose": list(pose), "committed": 1.0, "world": 1.0})
    wa.inner.add_edge_unchecked(game, "committed_goal", g)
    return g


def _tick2(wa, game, epoch):
    """The adapter's two-phase tick: stamp the flood epoch, flood to fixpoint, then detect
    closed against the CONVERGED field."""
    I = wa.inner
    I.set_attr(game, "chosen_action", "")
    I.set_attr(game, "closed", -1.0)   # sentinel: flood in progress (disarms qf_closed/qf_mint_hyp)
    I.set_attr(game, "flood_epoch", float(epoch))
    I.run_rules()
    I.set_attr(game, "closed", 0.0)    # armed: detect closed against the CONVERGED field only
    I.run_rules()
    return wa.s.node(game)["attrs"].get("chosen_action") or ""


def _quanta(wa, game=None):
    out = []
    for q in wa.s.nodes("SpaceQuantum"):
        a = wa.s.node(q)["attrs"]
        out.append((q, tuple(a["lo"]), tuple(a["hi"]), a.get("kind")))
    return out


DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}


def _walk_2d(wa, game, start, goal, true_passable, max_steps=64, on_step=None):
    """Drive the chosen_action loop like a world adapter: tick, read the action, move a 1x1
    point if the TRUE grid allows it. Returns (pose, steps, path). `true_passable(rc)` is the
    world's ground truth; `on_step(pose, step)` lets a caller ingest/observe per step."""
    I = wa.inner
    pos = tuple(start)
    path = [pos]
    for step in range(max_steps):
        if pos == tuple(goal):
            return pos, step, path
        I.set_attr(game, "avatar_pose", [int(pos[0]), int(pos[1])])
        act = _tick2(wa, game, epoch=step + 1)
        if not act:
            return pos, step, path
        d = DISP[act]
        tgt = (pos[0] + d[0], pos[1] + d[1])
        if true_passable(tgt):
            pos = tgt
        path.append(pos)
        if on_step is not None:
            on_step(pos, step)
    return pos, max_steps, path


# ---------------------------------------------------------------------------------------------
# 1. 2D corridor / rooms: decode shape + route via the qf rules
# ---------------------------------------------------------------------------------------------

def test_corridor_decodes_to_one_coarse_quantum_and_routes():
    """A 1xN corridor is ONE quantum, coarse along its length (dynamic quantization: no
    per-cell flood), and the hop walks it to the goal in exactly N-1 moves."""
    wa = _fresh()
    game = _mk_game(wa, [0, 0])
    _mk_cells_2d(wa, game, [[0] * 8])
    gid = int(str(game).lstrip("#"))
    summ = wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], [0, 0], [0, 7], 1)
    assert summ["quanta"] == 1
    (q, lo, hi, kind), = _quanta(wa)
    assert (lo, hi, kind) == ((0, 0), (0, 7), "passable")
    _seed_controls_2d(wa, game)
    _commit_goal(wa, game, [0, 7])
    pos, steps, _ = _walk_2d(wa, game, (0, 0), (0, 7), lambda rc: rc in {(0, c) for c in range(8)})
    assert pos == (0, 7)
    assert steps == 7                      # straight line: one move per cell, no detour


def test_rooms_decode_and_route_through_the_hole():
    """Two 5x2 rooms + a 1-cell hole in the wall between: 3 quanta (rooms coarse in BOTH dims,
    the hole a unit residual — 'remainder goes to more detail'), 4 portals, and the qf flood +
    hop route the avatar through the hole to the far room."""
    wa = _fresh()
    grid = [["#" if (c == 2 and r != 2) else 0 for c in range(5)] for r in range(5)]
    game = _mk_game(wa, [0, 0])
    _mk_cells_2d(wa, game, grid)
    gid = int(str(game).lstrip("#"))
    summ = wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], [0, 0], [4, 4], 1)
    assert summ["quanta"] == 3 and summ["portals"] == 4
    boxes = {(lo, hi) for _, lo, hi, k in _quanta(wa) if k == "passable"}
    assert boxes == {((0, 0), (4, 1)), ((0, 3), (4, 4)), ((2, 2), (2, 2))}
    _seed_controls_2d(wa, game)
    _commit_goal(wa, game, [0, 4])
    passable = {(r, c) for r in range(5) for c in range(5) if grid[r][c] == 0}
    pos, steps, path = _walk_2d(wa, game, (0, 0), (0, 4), lambda rc: rc in passable)
    assert pos == (0, 4)
    assert steps <= 12                     # optimal is 8 (down to the hole, across, up)
    assert (2, 2) in path                  # the route crossed THROUGH the hole
    # two-phase closed: the map is reachable, so closed must have stayed 0 and no hypothesis
    assert wa.s.node(game)["attrs"].get("closed") == 0.0
    assert list(wa.inner.neighbours(game, "minted")) == []


def test_unreachable_goal_sets_closed_and_mints_hypothesis():
    """No route (goal beyond a full wall): the avatar's quantum never gets a fresh qdist ->
    qf_closed -> qf_mint_hyp mints the need_non_movement_affordance Hypothesis (the CLOSED
    cognition live at quantum grain)."""
    wa = _fresh()
    grid = [["#" if c == 2 else 0 for c in range(5)] for r in range(5)]
    game = _mk_game(wa, [0, 0])
    _mk_cells_2d(wa, game, grid)
    gid = int(str(game).lstrip("#"))
    wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], [0, 0], [4, 4], 1)
    _seed_controls_2d(wa, game)
    _commit_goal(wa, game, [0, 4])
    act = _tick2(wa, game, epoch=1)
    assert act == ""                       # no bogus hop
    assert wa.s.node(game)["attrs"].get("closed") == 1.0
    minted = list(wa.inner.neighbours(game, "minted"))
    assert len(minted) == 1
    assert wa.s.node(minted[0])["attrs"].get("kind") == "need_non_movement_affordance"


# ---------------------------------------------------------------------------------------------
# 2. PARTIAL maze: view-radius world -> frontiers, exploration, persistent map, completion
# ---------------------------------------------------------------------------------------------

class _ViewMaze:
    """Test-local world variant (design Part C): the TRUE maze is hidden; each step it emits
    only the cells within Chebyshev view radius of the avatar (with their TRUE values — floor
    or wall). Pure ingest: no conditionals over graph state, only over its own world truth."""

    def __init__(self, wa, game, grid, radius=2):
        self.wa, self.game, self.grid, self.radius = wa, game, grid, radius
        self.H, self.W = len(grid), len(grid[0])
        self.cells = {}
        self.exit_seen = False

    def emit(self, pose):
        S, I = self.wa.s, self.wa.inner
        new = 0
        r0, c0 = pose
        for r in range(max(0, r0 - self.radius), min(self.H, r0 + self.radius + 1)):
            for c in range(max(0, c0 - self.radius), min(self.W, c0 + self.radius + 1)):
                if (r, c) in self.cells:
                    continue
                val = float(WALL if self.grid[r][c] == 1 else FLOOR)
                n = S.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                                 "col": float(c), "value": val})
                I.add_edge_unchecked(self.game, "has_cell", n)
                self.cells[(r, c)] = n
                new += 1
        return new


def test_partial_maze_frontiers_exploration_persistence_completion():
    from domains.maze_world import gen_maze
    from domains.spatial_sense import quanta_flood_step, bump_belief_epoch

    grid, start, exit_rc = gen_maze(4, seed=7)      # deterministic 9x9 perfect maze
    wa = _fresh()
    game = _mk_game(wa, list(start))
    _seed_controls_2d(wa, game)
    world = _ViewMaze(wa, game, grid, radius=2)
    H, W = world.H, world.W
    focus = ([0, 0], [H - 1, W - 1])                # world bounds (world knowledge); the
    # moving-focus behaviour is test 6's subject
    passable = {(r, c) for r in range(H) for c in range(W) if grid[r][c] == 0}

    saw_frontier = False
    saw_frontier_goal = False
    start_quantum = None                            # (node, lo, hi) decoded early, asserted later
    pos = start
    solved_at = None
    for step in range(400):
        if world.emit(pos):
            bump_belief_epoch(wa)
        if not world.exit_seen and exit_rc in world.cells:
            world.exit_seen = True                  # world knowledge: it just emitted its exit
            _commit_goal(wa, game, list(exit_rc))
        wa.inner.set_attr(game, "frame", float(step))
        wa.inner.set_attr(game, "chosen_action", "")
        quanta_flood_step(wa, game, pos, (1, 1), [FLOOR], 1, (H, W), focus=focus)
        qs = _quanta(wa)
        if any(k == "frontier" for _, _, _, k in qs):
            saw_frontier = True
        if start_quantum is None:
            for q, lo, hi, k in qs:
                if k == "passable" and lo[0] <= start[0] <= hi[0] and lo[1] <= start[1] <= hi[1]:
                    start_quantum = (q, lo, hi)
        if not world.exit_seen:
            for g in wa.inner.neighbours(game, "committed_goal"):
                if wa.s.node(g)["attrs"].get("world") != 1.0:
                    saw_frontier_goal = True        # exploration committed a frontier goal
        act = wa.s.node(game)["attrs"].get("chosen_action") or ""
        if not act:
            break
        d = DISP[act]
        tgt = (pos[0] + d[0], pos[1] + d[1])
        if tgt in passable:
            pos = tgt
        if pos == exit_rc:
            solved_at = step
            break

    assert saw_frontier, "no frontier quantum was ever minted from the partial belief"
    assert saw_frontier_goal, "exploration never committed a frontier goal"
    assert solved_at is not None, "the partial maze was not completed"
    # THE MAP PERSISTS: the quantum decoded around the start early in the run still exists,
    # same box, even though the avatar (and its view) is now at the exit — remembered, not
    # re-observed.
    assert start_quantum is not None
    q, lo, hi = start_quantum
    assert wa.inner.has_node(q)
    a = wa.s.node(q)["attrs"]
    assert (tuple(a["lo"]), tuple(a["hi"])) == (lo, hi)
    # and the belief cells seen early are still there (no re-observation was needed)
    assert start in world.cells


# ---------------------------------------------------------------------------------------------
# 3. 3D: 4x4x4 lattice, wall plane with a hole — N-dim boxes + route over portals
# ---------------------------------------------------------------------------------------------

def test_3d_lattice_wall_plane_with_hole_routes():
    wa = _fresh()
    game = wa.s.add_node("WorldInstance", {"world_type": "Game", "nav_repr": "quanta",
                                           "nav_mode": "seek", "avatar_pose": [1, 1, 0],
                                           "flood_epoch": 0.0})
    passable_true = set()
    for x in range(4):
        for y in range(4):
            for z in range(4):
                wallv = z == 2 and not (x == 1 and y == 1)
                if not wallv:
                    passable_true.add((x, y, z))
                n = wa.s.add_node("WorldInstance", {"world_type": "Cell", "pose": [x, y, z],
                                                    "value": float(WALL if wallv else FLOOR)})
                wa.inner.add_edge_unchecked(game, "has_cell", n)
    gid = int(str(game).lstrip("#"))
    summ = wa.inner.space_quantize(gid, 3, "1x1x1", [FLOOR], [0, 0, 0], [3, 3, 3], 1)
    boxes = {(lo, hi) for _, lo, hi, k in _quanta(wa) if k == "passable"}
    # per-dim extents prove N-dim boxes: the two slabs stay COARSE across x,y (4x4) and are
    # quantized only along z; the hole is the unit residual.
    assert boxes == {((0, 0, 0), (3, 3, 1)), ((0, 0, 3), (3, 3, 3)), ((1, 1, 2), (1, 1, 2))}
    assert summ["portals"] == 4
    # 6-action control chain (the world's 3D vocabulary)
    sr = wa.s.add_node("Region", {"is_self": 1.0})
    wa.inner.add_edge_unchecked(game, "has_region", sr)
    acts = {"Xp": (1, 0, 0), "Xm": (-1, 0, 0), "Yp": (0, 1, 0),
            "Ym": (0, -1, 0), "Zp": (0, 0, 1), "Zm": (0, 0, -1)}
    for name, (dr, dc, dz) in acts.items():
        cr = wa.s.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc),
                                               "dz": float(dz), "cname": name})
        wa.inner.add_edge_unchecked(sr, "responds_via", cr)
    _commit_goal(wa, game, [2, 2, 3])
    pos = (1, 1, 0)
    for step in range(32):
        if pos == (2, 2, 3):
            break
        wa.inner.set_attr(game, "avatar_pose", list(pos))
        act = _tick2(wa, game, epoch=step + 1)
        assert act, f"no action at {pos} (step {step})"
        d = acts[act]
        tgt = (pos[0] + d[0], pos[1] + d[1], pos[2] + d[2])
        if tgt in passable_true:
            pos = tgt
    assert pos == (2, 2, 3)


# ---------------------------------------------------------------------------------------------
# 4. Two bodies over ONE belief: 1x1 fits the 1-wide gap, 2x2 must go around
# ---------------------------------------------------------------------------------------------

def test_two_bodies_one_belief_different_quanta_and_routes():
    wa = _fresh()
    # 6x7 room; wall column c=3 except a 1-wide gap at r=2 and open floor at rows 4-5.
    grid = [["#" if (c == 3 and r in (0, 1, 3)) else 0 for c in range(7)] for r in range(6)]
    gA = _mk_game(wa, [2, 0])                       # 1x1 body's game
    gB = _mk_game(wa, [1, 0])                       # 2x2 body's game (anchor = top-left)
    cells = {}
    for r in range(6):
        for c in range(7):
            val = float(WALL if grid[r][c] == "#" else FLOOR)
            n = wa.s.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                                "col": float(c), "value": val})
            cells[(r, c)] = n
            wa.inner.add_edge_unchecked(gA, "has_cell", n)
            wa.inner.add_edge_unchecked(gB, "has_cell", n)   # ONE belief, both bodies
    idA, idB = int(str(gA).lstrip("#")), int(str(gB).lstrip("#"))
    wa.inner.space_quantize(idA, 2, "1x1", [FLOOR], [0, 0], [5, 6], 1)
    wa.inner.space_quantize(idB, 2, "2x2", [FLOOR], [0, 0], [5, 6], 1, [2, 2])
    qa = [(q, lo, hi) for q, lo, hi, k in _quanta(wa)
          if k == "passable" and wa.s.node(q)["attrs"].get("body_key") == "1x1"]
    qb = [(q, lo, hi) for q, lo, hi, k in _quanta(wa)
          if k == "passable" and wa.s.node(q)["attrs"].get("body_key") == "2x2"]
    # body-conditional erosion: the gap cell (2,3) is admissible for the 1x1 only
    assert any(lo[0] <= 2 <= hi[0] and lo[1] <= 3 <= hi[1] for _, lo, hi in qa)
    assert not any(lo[0] <= 2 <= hi[0] and lo[1] <= 3 <= hi[1] for _, lo, hi in qb)
    _seed_controls_2d(wa, gA)
    _seed_controls_2d(wa, gB)
    _commit_goal(wa, gA, [2, 6])
    _commit_goal(wa, gB, [0, 5])

    # 1x1 routes THROUGH the gap
    passA = {(r, c) for r in range(6) for c in range(7) if grid[r][c] == 0}
    posA, stepsA, pathA = _walk_2d(wa, gA, (2, 0), (2, 6), lambda rc: rc in passA)
    assert posA == (2, 6)
    assert (2, 3) in pathA                          # crossed the 1-wide gap

    # 2x2 (anchor pose admissible iff all 4 cells floor) must go AROUND via the open bottom
    def okB(rc):
        r, c = rc
        return all((r + dr, c + dc) in passA for dr in (0, 1) for dc in (0, 1))

    posB = (1, 0)
    pathB = [posB]
    for step in range(64):
        if posB == (0, 5):
            break
        wa.inner.set_attr(gB, "avatar_pose", list(posB))
        act = _tick2(wa, gB, epoch=100 + step)
        assert act, f"2x2 body: no action at {posB} (step {step})"
        d = DISP[act]
        tgt = (posB[0] + d[0], posB[1] + d[1])
        if okB(tgt):
            posB = tgt
        pathB.append(posB)
    assert posB == (0, 5)
    # around, not through: the 2x2's anchor never sat in the 1-wide gap (inadmissible for it)
    assert (2, 3) not in pathB
    assert any(p[0] >= 4 for p in pathB), "2x2 never took the bottom detour"


# ---------------------------------------------------------------------------------------------
# 5. Residual split: interior BlockObs -> split along EXACTLY the blocked dim; reroute works
# ---------------------------------------------------------------------------------------------

def test_interior_block_splits_only_the_blocked_dim_and_reroutes():
    wa = _fresh()
    game = _mk_game(wa, [0, 0])
    cells = _mk_cells_2d(wa, game, [[0] * 6 for _ in range(6)])
    gid = int(str(game).lstrip("#"))
    summ = wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], [0, 0], [5, 5], 1)
    assert summ["quanta"] == 1              # one coarse box over the open room
    # the world refuses Down at (2,2): the avatar's adapter stamps the observed wall into the
    # belief and records the BlockObs (pose = the blocked cell, dim 0 = the pressed axis)
    wa.inner.set_attr(cells[(3, 2)], "value", float(WALL))
    b = wa.s.add_node("BlockObs", {"pose": [3, 2], "dim": 0.0, "dir": 1.0, "epoch": 2.0})
    wa.inner.add_edge_unchecked(game, "blocked", b)
    wa.inner.run_rules()                    # qf_stale_on_block_interior + qf_requantize_flag
    stale = [(q, wa.s.node(q)["attrs"]) for q, *_ in _quanta(wa)]
    assert any(a.get("stale") == 1.0 and a.get("stale_dim") == 0.0
               and tuple(a.get("stale_pose")) == (3, 2) for _, a in stale)
    assert wa.s.node(game)["attrs"].get("needs_quantize") == 1.0
    summ2 = wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], [0, 0], [5, 5], 2)
    assert summ2["split"] > 0
    boxes = [(lo, hi) for _, lo, hi, k in _quanta(wa) if k == "passable"]
    # split along dim0 ONLY at the failure line: the off-band boxes keep the FULL dim1 extent
    # (0..5 — other dims stay coarse); only the row-3 band (the failed line) carries detail.
    for lo, hi in boxes:
        if not (lo[0] <= 3 <= hi[0]):
            assert (lo[1], hi[1]) == (0, 5), f"off-band box {lo}-{hi} lost its dim1 coarseness"
        else:
            assert lo[0] == hi[0] == 3, f"band box {lo}-{hi} not confined to the failure line"
    assert not any(lo[0] <= 3 <= hi[0] and lo[1] <= 2 <= hi[1] for lo, hi in boxes)
    # reroute succeeds around the learned wall
    _seed_controls_2d(wa, game)
    _commit_goal(wa, game, [5, 2])
    passable = {(r, c) for r in range(6) for c in range(6) if (r, c) != (3, 2)}
    pos, steps, _ = _walk_2d(wa, game, (0, 2), (5, 2), lambda rc: rc in passable)
    assert pos == (5, 2)
    assert steps <= 12                      # optimal 7 (one sidestep around the wall)


# ---------------------------------------------------------------------------------------------
# 6. Foveation: quanta only within focus; moving focus decodes incrementally (reused > 0)
# ---------------------------------------------------------------------------------------------

def test_foveation_focus_bound_and_incremental_reuse():
    """Focus semantics of the LIVE primitive (pinned by direct probe): every decode is
    focus-bound — quanta exist only within the focus box; a moved focus re-decodes
    incrementally, REUSING overlapping non-stale quanta (reused > 0). Out-of-focus quanta are
    NOT retained across a refocus (the persistent map is the BELIEF; quanta are the fovea's
    working set — out-of-VIEW persistence under a covering focus is test 2's subject)."""
    wa = _fresh()
    game = _mk_game(wa, [0, 0])
    # 4x12 strip; wall column c=3 with one hole at (1,3) so the two sides connect
    grid = [["#" if c == 3 else 0 for c in range(12)] for r in range(4)]
    grid[1][3] = 0
    _mk_cells_2d(wa, game, grid)
    gid = int(str(game).lstrip("#"))
    focus1 = ([0, 0], [3, 5])
    summ1 = wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], focus1[0], focus1[1], 1)
    assert summ1["quanta"] > 0
    for _, lo, hi, k in _quanta(wa):
        assert lo[0] >= 0 and lo[1] >= 0 and hi[0] <= 3 and hi[1] <= 5, \
            f"quantum {lo}-{hi} decoded OUTSIDE focus {focus1}"
    assert any(k == "passable" and hi[1] <= 2 for _, lo, hi, k in _quanta(wa)), \
        "no left-of-wall quantum decoded"
    # move the focus right (overlapping cols 4-5): incremental decode of the NEW territory
    focus2 = ([0, 4], [3, 11])
    summ2 = wa.inner.space_quantize(gid, 2, "1x1", [FLOOR], focus2[0], focus2[1], 2)
    assert summ2["reused"] > 0, "focus move did not reuse any overlapping quanta"
    after = [(lo, hi) for _, lo, hi, k in _quanta(wa)]
    for lo, hi in after:
        assert lo[1] >= 4 and hi[1] <= 11 and lo[0] >= 0 and hi[0] <= 3, \
            f"quantum {lo}-{hi} outside the moved focus {focus2}"
    assert any(hi[1] >= 6 for lo, hi in after), "new focus area was not decoded"
    # the overlap slice (cols 4-5) was kept, not rebuilt from scratch
    assert any(lo[1] <= 5 and hi[1] >= 4 for lo, hi in after)
