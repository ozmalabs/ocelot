"""frontier seeking, migrated — the freshening signal + per-action frontier EMA
run in the WorldAdapter (no CuriousAgent). Covers all of
tests/test_frontier_seeking: zero on id-less nodes, first-observe freshens,
stable re-observe doesn't, attr changes don't, a new edge freshens both
endpoints, noop gives zero, the action frontier EMA converges, map-agnostic.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(nodes, edges=()):
    g = TypedGraph()
    ids = [g._insert_node(t, a) for (t, a) in nodes]
    for s, et, t in edges:
        g._insert_edge(ids[s], et, ids[t])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_zero_on_id_less_nodes():
    wa = WorldAdapter()
    wa.ingest(_world([("Body", {"hp": 100})]))
    assert wa.last_freshening_count == 0


def test_first_observation_freshens():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "a"})]))
    assert wa.last_freshening_count == 1


def test_stable_reobserve_does_not_freshen():
    wa = WorldAdapter()
    w = _world([("AgentMarker", {"id": "a"})])
    wa.ingest(w)
    wa.ingest(w)
    assert wa.last_freshening_count == 0


def test_attr_change_does_not_freshen():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "a", "hunger": 0})]))
    wa.ingest(_world([("AgentMarker", {"id": "a", "hunger": 5})]))
    assert wa.last_freshening_count == 0


def test_new_edge_freshens_both_endpoints():
    wa = WorldAdapter()
    no_edge = _world([("SpatialLocation", {"id": "A"}), ("SpatialLocation", {"id": "B"})])
    wa.ingest(no_edge)
    wa.ingest(no_edge)
    assert wa.last_freshening_count == 0
    wa.ingest(_world([("SpatialLocation", {"id": "A"}), ("SpatialLocation", {"id": "B"})],
                     edges=[(0, "adjacent_to", 1)]))
    assert wa.last_freshening_count == 2


def test_noop_at_known_location_gives_zero():
    wa = WorldAdapter()
    sub = _world([("SpatialLocation", {"id": "A"}), ("SpatialLocation", {"id": "B"})],
                 edges=[(0, "adjacent_to", 1)])
    wa.ingest(sub)
    for _ in range(5):
        wa.ingest(sub)
    assert wa.last_freshening_count == 0


def test_action_frontier_estimate_is_ema():
    wa = WorldAdapter()
    for _ in range(1000):
        wa.record_action_outcome("explore", novelty_delta=0, frontier_after=3)
    assert abs(wa.action_frontier_estimate("explore") - 3.0) < 0.1


def test_freshening_is_map_agnostic():
    wa = WorldAdapter()
    sub = _world([("AgentMarker", {"id": "X"}), ("AgentMarker", {"id": "Y"})],
                 edges=[(0, "interacted_with", 1)])
    wa.ingest(sub)
    assert wa.last_freshening_count == 2
    wa.ingest(sub)
    assert wa.last_freshening_count == 0
