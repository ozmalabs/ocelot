"""Goals — migrated to the seed-booted WorldAdapter (no CuriousAgent).

Covers ALL of tests/test_goals.py:
  * a goal is a graph-resident `wants` edge (set_goal single / add_goal
    concurrent / remove_goal), each carrying its raw priority — mechanical;
  * the adhd priority modulation (intensity 0 = raw pass-through, 1 = bimodal
    snap, partial = interpolation) is the seeded `_ADHD_PRIORITY_TERM` the DSL
    evaluates — the DECISION as graph data, the adapter supplies raw + intensity;
  * pick_goal (nearest reachable UNSATURATED instance, else most salient) is the
    seeded `_GOAL_CHOICE_TERM` Argmax over BFS-stamped candidates — the
    saturation channel is the seeded predicate;
  * intent-failure freshening (an intended next-locus the action didn't achieve
    resets the failure-locus saturation) — mechanical bookkeeping;
  * BFS goal planning (bfs_distances_to_goal / plan_to_goal) — pure traversal.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world_with_body_at(loc_id, locs, edges):
    g = TypedGraph()
    body = g._insert_node("Body", {})
    nids = {n: g._insert_node("SpatialLocation", {"id": n}) for n in locs}
    for a, b in edges:
        g._insert_edge(nids[a], "adjacent_to", nids[b])
    g._insert_edge(body, "at_location", nids[loc_id])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _at(loc_id, locs, edges):
    """Boot an adapter observing a body at `loc_id`; return (wa, {loc: wi})."""
    wa = WorldAdapter()
    wa.observe_locus(_world_with_body_at(loc_id, locs, edges))
    wis = {n: wa._instances[("SpatialLocation", n)] for n in locs}
    return wa, wis


def _wants(wa):
    return list(wa.inner.neighbours(wa.agent, "wants"))


def _prio_map(wa):
    """raw priority per wants-target, read from the edges."""
    out, idx = {}, {}
    for e in wa.inner.graph_to_dict()["edges"]:
        if e["type"] == "wants":
            idx[e["tgt"]] = float(e.get("attrs", {}).get("priority", 1.0))
    for nid in _wants(wa):
        out[nid] = idx.get(int(str(nid).lstrip("#")), 1.0)
    return out


# --- single goal pointer (set_goal) -------------------------------------

def test_set_goal_creates_wants_edge_with_priority():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.set_goal(wis["B"], priority=0.7)
    assert _wants(wa) == [wis["B"]]
    assert abs(_prio_map(wa)[wis["B"]] - 0.7) < 1e-9
    assert wa.current_goal_wi == wis["B"]


def test_set_goal_replaces_old_goal():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("A", "C")])
    wa.set_goal(wis["B"])
    wa.set_goal(wis["C"])
    assert _wants(wa) == [wis["C"]]


def test_set_goal_none_clears_edge():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.set_goal(wis["B"])
    wa.set_goal(None)
    assert _wants(wa) == []
    assert wa.current_goal_wi is None


# --- concurrent goals (add_goal / remove_goal) --------------------------

def test_add_goal_supports_multiple_concurrent():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("A", "C")])
    wa.add_goal(wis["B"], 0.3)
    wa.add_goal(wis["C"], 1.5)
    assert set(_wants(wa)) == {wis["B"], wis["C"]}


def test_add_goal_updates_priority_if_present():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.add_goal(wis["B"], 0.3)
    wa.add_goal(wis["B"], 1.0)
    assert _wants(wa) == [wis["B"]]
    assert abs(_prio_map(wa)[wis["B"]] - 1.0) < 1e-9


def test_remove_goal_drops_specific_goal():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("A", "C")])
    wa.add_goal(wis["B"])
    wa.add_goal(wis["C"])
    wa.remove_goal(wis["B"])
    assert _wants(wa) == [wis["C"]]


# --- adhd priority modulation (the seeded transform Term) ---------------

def test_adhd_off_priorities_pass_through():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("A", "C")])
    wa.add_goal(wis["B"], 0.3)
    wa.add_goal(wis["C"], 1.5)
    p = dict(wa.get_goals())
    assert p[wis["B"]] == 0.3
    assert p[wis["C"]] == 1.5


def test_adhd_full_snaps_to_extremes():
    wa, wis = _at("A", ["A", "B", "C", "D"],
                  [("A", "B"), ("A", "C"), ("A", "D")])
    wa.set_scalar_policy("adhd_intensity", 1.0)
    wa.add_goal(wis["B"], 0.3)
    wa.add_goal(wis["C"], 1.5)
    wa.add_goal(wis["D"], 0.9)
    p = dict(wa.get_goals())
    assert p[wis["B"]] == 0.05   # below 1 -> ignored
    assert p[wis["C"]] == 2.0    # at/above 1 -> fixation
    assert p[wis["D"]] == 0.05


def test_adhd_partial_interpolates():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.set_scalar_policy("adhd_intensity", 0.5)
    wa.add_goal(wis["B"], 1.0)
    p = dict(wa.get_goals())[wis["B"]]
    assert abs(p - 1.5) < 1e-9   # 1.0*0.5 + 2.0*0.5


def test_adhd_can_be_turned_off_to_restore_raw():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.add_goal(wis["B"], 0.3)
    wa.set_scalar_policy("adhd_intensity", 1.0)
    assert dict(wa.get_goals())[wis["B"]] == 0.05
    wa.set_scalar_policy("adhd_intensity", 0.0)
    assert dict(wa.get_goals())[wis["B"]] == 0.3


# --- pick_goal (the seeded goal-choice Argmax) --------------------------

def test_pick_goal_returns_nearest_unsaturated():
    wa, wis = _at("A", ["A", "B", "C", "D"],
                  [("A", "B"), ("B", "C"), ("C", "D")])
    for n in ("A", "B", "C"):
        wa.saturate_instance(wis[n])
    assert wa.pick_goal(horizon=10) == wis["D"]


def test_pick_goal_falls_back_to_most_salient_when_all_saturated():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.saturate_instance(wis["A"])
    wa.saturate_instance(wis["B"])
    wa.inner.set_attr(wis["B"], "last_observed_tick", 0)
    wa.inner.set_attr(wis["A"], "last_observed_tick", 100)
    assert wa.pick_goal(horizon=10) == wis["B"]


# --- intent-failure freshening ------------------------------------------

def test_intent_failure_freshens_locus():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("B", "C")])
    wa.saturate_instance(wis["A"])
    assert wa.is_instance_saturated(wis["A"])
    wa.current_intent_wi = wis["B"]                 # intended to reach B
    wa.observe_locus(_world_with_body_at("C", ["A", "B", "C"],
                                         [("A", "B"), ("B", "C")]))  # ended at C
    assert int(wa.s.node(wis["A"])["attrs"].get("saturation_count", -1)) == 0


def test_intent_success_does_not_freshen():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    wa.saturate_instance(wis["A"])
    wa.current_intent_wi = wis["B"]
    wa.observe_locus(_world_with_body_at("B", ["A", "B"], [("A", "B")]))  # reached B
    # intent achieved -> NOT freshened: A's saturation is not reset to 0
    # (it stays high; re-observe may bump it, but the freshening never fires).
    assert int(wa.s.node(wis["A"])["attrs"].get("saturation_count", 0)) > 0
    assert wa.is_instance_saturated(wis["A"])


# --- BFS goal planning ---------------------------------------------------

def test_bfs_distances_to_goal_returns_correct_dists():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("B", "C")])
    d = wa.bfs_distances_to_goal(wis["C"], horizon=10)
    assert d[wis["C"]] == 0
    assert d[wis["B"]] == 1
    assert d[wis["A"]] == 2


def test_plan_to_goal_returns_first_hop():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B"), ("B", "C")])
    assert wa.plan_to_goal(wis["A"], wis["C"], horizon=10) == wis["B"]


def test_plan_to_goal_returns_none_when_unreachable():
    wa, wis = _at("A", ["A", "B", "C"], [("A", "B")])   # C disconnected
    assert wa.plan_to_goal(wis["A"], wis["C"], horizon=10) is None


def test_plan_to_goal_returns_goal_directly_if_adjacent():
    wa, wis = _at("A", ["A", "B"], [("A", "B")])
    assert wa.plan_to_goal(wis["A"], wis["B"], horizon=10) == wis["B"]
