"""per-instance saturation, migrated — the saturation_count bookkeeping runs in
the WorldAdapter and the SEEDED saturation_predicate classifies it (no
CuriousAgent). Covers tests/test_instance_saturation: zero on a new instance,
climbs on stable observes, decoupled from attr churn, resets on a new edge
(both endpoints), the predicate fires past threshold, under-known instances
add to novelty, saturated instances add to boredom, and a cell kept
structurally fresh via new edges never saturates.

The per-instance bookkeeping (saturation_count reset-on-fresh / climb-on-stale)
is mechanical I/O in WorldAdapter.ingest; the "is this saturated?" decision is
the seeded saturation_predicate Term-tree (is_instance_saturated). novelty_count
and boredom_count are pure mechanical tallies over a world substrate that read
that seeded predicate — no decisions of their own.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(nodes, edges=()):
    g = TypedGraph()
    ids = {}
    for nm, (t, a) in nodes.items():
        ids[nm] = g._insert_node(t, a)
    for s, et, tt in edges:
        g._insert_edge(ids[s], et, ids[tt])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _sat(wa, key):
    return wa.s.node(wa._instances[key])["attrs"].get("saturation_count", 0)


# --- mirrors test_new_instance_has_zero_saturation ---------------------------
def test_new_instance_has_zero_saturation():
    wa = WorldAdapter()
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a"})}))
    assert _sat(wa, ("AgentMarker", "a")) == 0


# --- mirrors test_saturation_increments_on_stable_observations ---------------
def test_saturation_increments_on_stable_observations():
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "a"})})
    for _ in range(5):
        wa.ingest(w)
    # First tick freshens (creation). The next 4 each tick saturation up by 1.
    assert _sat(wa, ("AgentMarker", "a")) == 4


# --- mirrors test_saturation_does_not_reset_on_attr_changes ------------------
def test_saturation_decoupled_from_attr_changes():
    wa = WorldAdapter()
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 0})}))
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 0})}))
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 0})}))
    assert _sat(wa, ("AgentMarker", "a")) == 2
    # hunger changes — attr churn, not structural news → still climbs.
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 5})}))
    assert _sat(wa, ("AgentMarker", "a")) == 3


# --- mirrors test_saturation_resets_when_new_edge_appears --------------------
def test_saturation_resets_on_new_edge_both_endpoints():
    wa = WorldAdapter()
    no_edge = _world({"l": ("SpatialLocation", {"id": "5_5"}),
                      "m": ("SpatialLocation", {"id": "6_5"})})
    for _ in range(5):
        wa.ingest(no_edge)
    assert _sat(wa, ("SpatialLocation", "5_5")) >= 4
    # A new instance-instance edge is new structural info → resets both ends.
    with_edge = _world({"l": ("SpatialLocation", {"id": "5_5"}),
                        "m": ("SpatialLocation", {"id": "6_5"})},
                       [("l", "adjacent", "m")])
    wa.ingest(with_edge)
    assert _sat(wa, ("SpatialLocation", "5_5")) == 0
    assert _sat(wa, ("SpatialLocation", "6_5")) == 0


# --- mirrors test_is_instance_saturated_uses_policy_threshold ----------------
def test_seeded_saturation_predicate_fires_past_threshold():
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "a"})})
    for _ in range(5):
        wa.ingest(w)
    nid = wa._instances[("AgentMarker", "a")]
    assert wa.is_instance_saturated(nid) is False     # ~4 < 30
    for _ in range(30):
        wa.ingest(w)
    assert wa.is_instance_saturated(nid) is True       # past 30 (policy threshold)


# --- mirrors test_under_known_instance_adds_to_novelty -----------------------
def test_under_known_instance_adds_to_novelty():
    wa = WorldAdapter()
    sub_a = _world({"a": ("AgentMarker", {"id": "a"})})
    sub_b = _world({"b": ("AgentMarker", {"id": "b"})})
    # See "a" enough to saturate it.
    for _ in range(35):
        wa.ingest(sub_a)
    wi_a = wa._instances[("AgentMarker", "a")]
    assert wa.is_instance_saturated(wi_a)
    # A different, still-fresh instance fires more novelty than the saturated one.
    novelty_for_b = wa.novelty_count(sub_b)
    novelty_for_a = wa.novelty_count(sub_a)
    assert novelty_for_b >= novelty_for_a + 1, \
        "fresh instance should add at least one to novelty over saturated one"


# --- mirrors test_saturated_instance_adds_to_boredom -------------------------
def test_saturated_instance_adds_to_boredom():
    wa = WorldAdapter()
    sub = _world({"a": ("AgentMarker", {"id": "a"})})
    boredom_initial = wa.boredom_count(sub)
    for _ in range(35):
        wa.ingest(sub)
    boredom_after = wa.boredom_count(sub)
    assert boredom_after > boredom_initial, \
        "saturated instance should raise boredom_count over fresh observation"


# --- mirrors test_freshening_via_edge_keeps_boredom_low ----------------------
def test_freshening_via_edge_keeps_boredom_low():
    wa = WorldAdapter()
    # 40 distinct neighbours each connect to "hub" — each adds a NEW edge.
    for i in range(40):
        sub = _world(
            {"hub": ("SpatialLocation", {"id": "hub"}),
             "n": ("SpatialLocation", {"id": f"n_{i}"})},
            [("hub", "adjacent", "n")],
        )
        wa.ingest(sub)
    wi_hub = wa._instances[("SpatialLocation", "hub")]
    # Hub freshened every observation (new edge each tick) → never saturates.
    assert wa.s.node(wi_hub)["attrs"]["saturation_count"] == 0
    assert not wa.is_instance_saturated(wi_hub)
