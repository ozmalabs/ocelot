"""Gate for the persistent, graph-native in-graph spatial map (block 161000-161999).

The map is graph DATA (has_cell Cell belief + SpaceQuantum area boxes, unknown = ABSENCE)
grown and TYPED entirely by the dm_* rules in seeds/doom_ingraph_map.json; the ingest
(pose/depth -> ObsCell) and the display are mechanical world-adapter I/O
(domains/doom_map_ingest.py). This gate proves:

  M1  the map is graph-native (read FROM has_cell / SpaceQuantum nodes) and GROWS; on a
      CONSTRUCTED known layout it registers the expected free/occupied cells (able to fail).
  M2  the geometry is consistent with ground truth: walking a cell a depth ray mis-called a
      wall corrects it to FREE (the merge rule is load-bearing), so the map never keeps a
      wall on a walked cell; and human area KINDS (room/corridor/area) fall out of geometry.
  M3  unknown is first-class ABSENCE: an unobserved cell is neither free nor wall (no node),
      and a frontier quantum marks the border.
  ARCH  the accumulation/merge is a RULE, not a Python occupancy update (source audit).
  E1M1  the real seeded route builds a trajectory-consistent map (skips if WAD/VizDoom absent).

Deterministic and cross-process-stable: every assertion is on OCCUPANCY / POSITION / COUNTS,
never on node ids (map node ids are a HashMap artifact).
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "doom_ingraph_map.json")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"


# --------------------------------------------------------------------------- harness
def _fresh():
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)
    return wa


def _game(wa, body_w=1.0):
    return wa.s.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                           "body_w": float(body_w), "flood_epoch": 0.0})


def _observe(wa, game, cells):
    """Mechanical ingest: (pose, src) tuples -> ObsCell; run the accumulation rules; clean up.
    Per-frame dedup (one obs per cell, walk>wall>free) mirrors the adapter's sensor fusion."""
    S, I = wa.s, wa.inner
    _rank = {"walk": 2, "depth_wall": 1, "depth_free": 0}
    best = {}
    for pose, src in cells:
        p = (int(pose[0]), int(pose[1]))
        if p not in best or _rank[src] > _rank[best[p]]:
            best[p] = src
    for p, src in best.items():
        o = S.add_node("ObsCell", {"pose": [p[0], p[1]], "src": src})
        I.add_edge_unchecked(game, "observed", o)
    I.run_rules()
    for o in list(I.neighbours(game, "observed")):
        I.remove_node(o)


def _belief(wa, game):
    S, I = wa.s, wa.inner
    return {tuple(int(v) for v in S.node(c)["attrs"]["pose"]): float(S.node(c)["attrs"]["value"])
            for c in I.neighbours(game, "has_cell")}


def _decode_and_type(wa, game, lo, hi, epoch=1, body=(1, 1), passable=(0, 2)):
    I = wa.inner
    gid = int(str(game).lstrip("#"))
    res = I.space_quantize(gid, 2, "%dx%d" % body, [int(v) for v in passable],
                           list(lo), list(hi), int(epoch), list(body), None, list(body))
    I.run_rules()
    return dict(res)


def _quanta(wa, game):
    S, I = wa.s, wa.inner
    out = []
    for q in S.nodes("SpaceQuantum"):
        if game in list(I.neighbours(q, "in_space")):
            a = S.node(q)["attrs"]
            out.append({"lo": tuple(a["lo"]), "hi": tuple(a["hi"]), "kind": a.get("kind"),
                        "region_kind": a.get("region_kind")})
    return out


# a small KNOWN layout: a 3x3 room (rows/cols 1..3) + a 1-wide corridor (row 2, cols 4..6).
_ROOM = [(r, c) for r in (1, 2, 3) for c in (1, 2, 3)]
_CORR = [(2, 4), (2, 5), (2, 6)]
_WALLS = ([(0, c) for c in range(8)] + [(4, c) for c in range(8)] + [(r, 0) for r in range(5)]
          + [(1, 4), (3, 4), (1, 5), (3, 5), (1, 6), (3, 6), (2, 7)])


# --------------------------------------------------------------------------- M1
def test_M1_map_is_graph_native_and_grows():
    wa = _fresh(); game = _game(wa)
    _observe(wa, game, [((2, 2), "walk")])
    n1 = len(_belief(wa, game))
    _observe(wa, game, [(p, "depth_free") for p in _ROOM] + [(p, "depth_wall") for p in _WALLS])
    n2 = len(_belief(wa, game))
    assert n1 == 1 and n2 > n1, ("map must GROW as it is sensed", n1, n2)
    # graph-native: the belief IS has_cell Cell nodes on the game (not a Python array),
    # and it is ONE Cell per pose (the accumulation guard + per-frame sensor fusion)
    cell_nodes = list(wa.inner.neighbours(game, "has_cell"))
    assert len(cell_nodes) == n2, (len(cell_nodes), n2)  # no duplicate Cell per pose
    poses = [tuple(wa.s.node(c)["attrs"]["pose"]) for c in cell_nodes]
    assert len(set(poses)) == len(poses), "one Cell per pose"
    for c in cell_nodes:
        assert wa.s.node(c)["attrs"]["world_type"] == "Cell"
    # decode produces graph SpaceQuantum area nodes
    _decode_and_type(wa, game, [0, 0], [4, 7])
    assert any(q["kind"] == "passable" for q in _quanta(wa, game))


def test_M1_constructed_route_registers_expected_cells_ABLE_TO_FAIL():
    wa = _fresh(); game = _game(wa)
    _observe(wa, game, [((2, 2), "walk")]
             + [(p, "depth_free") for p in _ROOM + _CORR]
             + [(p, "depth_wall") for p in _WALLS])
    b = _belief(wa, game)
    # expected FREE (able to fail: if accumulation broke, these are absent -> KeyError/assert)
    for p in _ROOM + _CORR:
        assert b.get(p) == 0.0, ("expected free", p, b.get(p))
    # expected WALL
    for p in [(0, 1), (4, 2), (1, 4), (2, 7)]:
        assert b.get(p) == 1.0, ("expected wall", p, b.get(p))


# --------------------------------------------------------------------------- M2
def test_M2_walk_overrides_depth_wall_merge_is_load_bearing():
    """Depth mis-calls (2,2) a wall; walking it corrects to FREE. The wall->free transition
    IS the merge rule doing load-bearing work (§13.2): without dm_walk_frees_wall (2,2) would
    stay a wall on a walked cell — the exact M2 inconsistency the rule prevents."""
    wa = _fresh(); game = _game(wa)
    _observe(wa, game, [((2, 2), "depth_wall")])
    assert _belief(wa, game).get((2, 2)) == 1.0        # depth alone: a wall
    _observe(wa, game, [((2, 2), "walk")])
    assert _belief(wa, game).get((2, 2)) == 0.0        # after walking it: corrected to free
    # depth_free must NOT overwrite a standing wall (conservative), proving the flip is
    # specifically the WALK rule, not "any later observation wins"
    wa2 = _fresh(); g2 = _game(wa2)
    _observe(wa2, g2, [((5, 5), "depth_wall")])
    _observe(wa2, g2, [((5, 5), "depth_free")])
    assert _belief(wa2, g2).get((5, 5)) == 1.0


def test_M2_region_kinds_fall_out_of_geometry_ABLE_TO_FAIL():
    wa = _fresh(); game = _game(wa)
    _observe(wa, game, [((2, 2), "walk")]
             + [(p, "depth_free") for p in _ROOM + _CORR]
             + [(p, "depth_wall") for p in _WALLS])
    _decode_and_type(wa, game, [0, 0], [4, 7])
    qs = {(q["lo"], q["hi"]): q["region_kind"] for q in _quanta(wa, game)}
    assert qs.get(((1, 1), (3, 3))) == "room", ("3x3 open box must be room", qs)
    assert qs.get(((2, 4), (2, 6))) == "corridor", ("1-wide passage must be corridor", qs)


def test_M2_lava_kind_is_value_keyed():
    """The human taxonomy is extensible past geometry: a passable area over HAZARD cells
    (value 2) types as lava. Proves dm_kind_lava fires (the mechanism), separate from the
    real-route residual that a live lava sense is not yet wired."""
    wa = _fresh(); game = _game(wa)
    S, I = wa.s, wa.inner
    # three hazard cells in a row (value 2) — passable but damaging
    for c in (1, 2, 3):
        n = S.add_node("Cell", {"world_type": "Cell", "pose": [2, c], "value": 2.0})
        I.add_edge_unchecked(game, "has_cell", n)
    _decode_and_type(wa, game, [1, 0], [3, 4], passable=(0, 2))
    assert any(q["region_kind"] == "lava" for q in _quanta(wa, game))


# --------------------------------------------------------------------------- M3
def test_M3_unknown_is_absence_and_frontier_marks_the_border():
    wa = _fresh(); game = _game(wa)
    free = [(r, c) for r in (1, 2, 3) for c in (1, 2)]
    walls = [(0, c) for c in (0, 1, 2, 3)] + [(4, c) for c in (0, 1, 2, 3)] + [(1, 0), (2, 0), (3, 0)]
    _observe(wa, game, [((2, 1), "walk")] + [(p, "depth_free") for p in free]
             + [(p, "depth_wall") for p in walls])
    b = _belief(wa, game)
    # the unexplored right side is ABSENT — neither free nor wall (first-class unknown)
    assert (2, 3) not in b and (2, 4) not in b, "unexplored cells must be absent, not free/wall"
    _decode_and_type(wa, game, [0, 0], [4, 4], epoch=5)
    fr = [q for q in _quanta(wa, game) if q["kind"] == "frontier"]
    assert fr, "a frontier quantum must mark the unknown border"
    assert all(q["region_kind"] == "frontier" for q in fr)


# --------------------------------------------------------------------------- ARCH (source audit)
def test_accumulation_is_a_rule_not_a_python_update():
    # (a) the accumulation + merge live in the seed as graph data
    man = json.load(open(SEED_PATH))
    names = {r["name"] for r in man["rules"]}
    assert {"dm_free_new", "dm_wall_new", "dm_walk_frees_wall"} <= names
    assert {"dm_kind_room", "dm_kind_corridor", "dm_kind_area", "dm_kind_frontier"} <= names
    # (b) the ingest adapter makes NO occupancy-merge decision: it never WRITES has_cell Cell
    #     values from a conditional — it emits ObsCell + calls run_rules/space_quantize only.
    src = open(os.path.join(ROOT, "domains", "doom_map_ingest.py")).read()
    assert 'add_edge_unchecked(game, "observed"' in src   # emits observations
    assert 'add_edge_unchecked(game, "has_cell"' not in src  # never writes the belief itself
    assert "space_quantize(" in src and "run_rules(" in src


# --------------------------------------------------------------------------- E1M1 real run
@pytest.mark.skipif(not os.path.exists(WAD), reason="DOOM.WAD absent")
def test_E1M1_real_route_builds_a_seen_map_correlated_with_the_oracle():
    """The WHOLE map is SEEN: walls via depth-from-motion on the RGB flow (block 158000),
    calibrated by the agent's own forward displacement (efference copy). The VizDoom depth
    buffer is the SCORING ORACLE only. Deterministic (fixed seed + fixed route)."""
    pytest.importorskip("vizdoom")
    import scripts.doom_ingraph_map_run as R
    s = R.run(frames=40, seed=1234, checkpoints=(10, 20))
    # geometry was SEEN (forward-parallax frames registered walls), not read from any buffer
    assert s["seen_forward_frames"] > 0, s
    assert s["final_cells"] > 20 and s["final_walls"] > 0, s
    # M1 grows: last cell count strictly exceeds an early one
    gc = s["growth_curve"]
    assert gc[-1][1] > gc[3][1], ("map must grow over the walk", gc[:5], gc[-1])
    # M2a: the map never keeps a wall on a cell the agent walked through
    assert s["M2_walls_on_walked_cells"] == 0 and s["M2_trajectory_consistency"] == 1.0, s
    # M2b: the SEEN depth POSITIVELY correlates with the depth-buffer oracle it is scored
    #      against (majority of frames rho>0) — bounded seeing, ties 158000's flow wall.
    sp = s["M2_seen_vs_depthbuffer_spearman"]
    assert sp["n"] > 0 and sp["frac_pos"] > 0.5, ("seen depth must correlate with GT", sp)
    # M3: the unknown border is first-class (frontier quanta minted)
    assert s["frontier_quanta"] > 0 and s["passable_quanta"] > 0, s
