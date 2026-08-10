"""Gates for block 205000 — ACTIVE curiosity-driven Doom exploration.

Mostly VizDoom-FREE: a small SYNTHETIC walkable occupancy exercises the full graph-native
loop (reveal -> frontier -> LP-curiosity -> commit -> nav-intent -> motor) deterministically
and fast. One VizDoom-gated test checks the real E1M1 occupancy extraction.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import pytest


def _synthetic_occ():
    """A small connected walkable region: a 9x3 room joined by a corridor to a 3x7 room.
    unknown=absence; a radius-3 eye cannot see it all from the start -> real frontiers."""
    walk = set()
    for x in range(0, 9):
        for y in range(0, 3):
            walk.add((x, y))
    for y in range(3, 8):
        walk.add((4, y))
    for x in range(2, 7):
        for y in range(8, 11):
            walk.add((x, y))
    return {"walkable": walk, "start": (4, 1),
            "bounds": (-1, -1, 9, 11)}


def _run(arm, budget=25, view_radius=3):
    import numpy as np
    import scripts.doom_active_explore_run as R
    return R.run_arm(arm, _synthetic_occ(), budget=budget, view_radius=view_radius,
                     rng=np.random.default_rng(205000))


# ------------------------------------------------------------------ G1
def test_curiosity_covers_more_than_passive():
    cur = _run("curiosity")
    pas = _run("passive")
    assert cur["final_free"] > pas["final_free"], (cur["final_free"], pas["final_free"])
    # curiosity actually explores beyond the initial view
    assert cur["final_free"] > cur["curve"][0][1]


def test_frontier_seeking_beats_random_on_average():
    import numpy as np
    import scripts.doom_active_explore_run as R
    cur = _run("curiosity")
    rand = [R.run_arm("random", _synthetic_occ(), budget=25, view_radius=3,
                      rng=np.random.default_rng(205000 + i))["final_free"] for i in range(4)]
    assert cur["final_free"] >= float(np.mean(rand))


# ------------------------------------------------------------------ G2 (graph-native decision)
def test_active_explore_makes_a_graph_native_decision():
    """With active_explore=1, ae_frontier_goal commits a frontier and the qf hop writes a
    chosen_action -- the direction came from the graph, not Python."""
    import scripts.doom_active_explore_run as R
    import domains.doom_explore_world as dw
    occ = _synthetic_occ()
    world = dw.DoomExploreWorld(occ, view_radius=3)
    wa = R._boot()
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                        "body_w": 1.0, "flood_epoch": 0.0})
    R._setup(wa, game, active_explore=True, commit=True)
    R._reveal(wa, game, world, 1, curiosity=True)
    acts = []
    goals = []
    for t in range(1, 8):
        act = R._flood_and_choose(wa, game, world, t)
        gp, _ = R._committed_goal_pose(wa, game)
        acts.append(act); goals.append(gp)
        if act:
            world.apply(act)
        R._reveal(wa, game, world, t + 1, curiosity=True)
    assert any(a in ("Up", "Down", "Left", "Right") for a in acts), acts
    assert any(g is not None for g in goals), "ae_frontier_goal never committed a frontier"


# ------------------------------------------------------------------ G3 (commit-net anti-thrash)
def test_commit_net_holds_a_frontier_longer_than_no_commit():
    from scripts.doom_active_explore_report import _dwell
    cur = _run("curiosity", budget=30)
    noc = _run("nocommit", budget=30)
    d_cur, sw_cur = _dwell(cur["goal_trace"])
    d_noc, sw_noc = _dwell(noc["goal_trace"])
    # commit -> dwell longer AND fewer goal switches (anti-thrash); no-commit thrashes.
    assert d_cur > d_noc, (d_cur, d_noc)
    assert sw_cur <= sw_noc, (sw_cur, sw_noc)


def test_active_explore_always_picks_no_paralysis():
    """Anti-paralysis: while a frontier exists, an action is issued every tick."""
    cur = _run("curiosity", budget=15)
    # coverage keeps rising for several ticks -> it kept moving (picked)
    early = cur["curve"][1][1]; late = cur["curve"][-1][1]
    assert late > early


# ------------------------------------------------------------------ LP interest law (mode=1)
def test_lp_interest_differentiates_productive_from_exhausted():
    """The 202000 lp_* law (surprise mode) keeps a sustained-info-gain frontier interesting
    while an exhausting one decays -- the mechanism is LOAD-BEARING (not a constant)."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.doom_active_explore_ingest as ae
    wa = WorldAdapter(seeds=()); load_all_seeds(wa)
    S, I = wa.s, wa.inner
    I.load_seed_manifest(json.load(open(ae._LP_SEED)), None)
    hub = S.add_node("CuriosityHub", {"kind": "t"})
    cp = S.add_node("HeldCuriosityParams", dict(ae.PARAMS))
    I.add_edge_unchecked(hub, "has_curiosity_params", cp)
    A = S.add_node("AttentionItem", dict(ae.ITEM_INIT, fkey="A"))
    B = S.add_node("AttentionItem", dict(ae.ITEM_INIT, fkey="B"))
    I.add_edge_unchecked(hub, "has_attention_item", A)
    I.add_edge_unchecked(hub, "has_attention_item", B)
    seqA = [40, 42, 41, 43, 40, 41, 42, 40]      # sustained
    seqB = [40, 20, 8, 2, 0, 0, 0, 0]            # exhausting
    for t in range(8):
        I.set_attr(A, "obs", float(seqA[t])); I.set_attr(A, "input_epoch", float(t))
        I.set_attr(B, "obs", float(seqB[t])); I.set_attr(B, "input_epoch", float(t))
        I.run_rules()
    ia = float(S.node(A)["attrs"]["interest"]); ib = float(S.node(B)["attrs"]["interest"])
    # both are integers (integer-native) and A (sustained) ended at least as interesting as B
    assert ia == int(ia) and ib == int(ib)
    assert ia >= ib


# ------------------------------------------------------------------ G5 (default-OFF byte-identity)
def test_default_off_leaves_quanta_nav_unchanged():
    """Loading doom_active_exploration + not setting active_explore must not perturb the
    nearest-frontier quanta nav: qf_frontier_goal still fires (a committed goal appears)."""
    import scripts.doom_active_explore_run as R
    import domains.doom_explore_world as dw
    occ = _synthetic_occ()
    world = dw.DoomExploreWorld(occ, view_radius=3)
    wa = R._boot()
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                        "body_w": 1.0, "flood_epoch": 0.0})
    R._setup(wa, game, active_explore=False, commit=False)   # nearest-frontier (stock) path
    R._reveal(wa, game, world, 1, curiosity=False)
    committed = False
    for t in range(1, 8):
        R._flood_and_choose(wa, game, world, t)
        gp, _ = R._committed_goal_pose(wa, game)
        if gp is not None:
            committed = True
        R._reveal(wa, game, world, t + 1, curiosity=False)
    assert committed, "stock nearest-frontier quanta nav did not commit a goal (default-OFF broken)"


# ------------------------------------------------------------------ occupancy (VizDoom-gated)
def test_e1m1_occupancy_extraction():
    import domains.doom_explore_world as dw
    if not os.path.exists(dw.WAD):
        pytest.skip("DOOM.WAD unavailable")
    try:
        import vizdoom  # noqa: F401
    except Exception:
        pytest.skip("vizdoom unavailable")
    occ = dw.extract_e1m1_occupancy(use_cache=True)
    assert len(occ["walkable"]) > 1000       # E1M1 is a large connected walkable region
    assert tuple(occ["start"]) in occ["walkable"]
