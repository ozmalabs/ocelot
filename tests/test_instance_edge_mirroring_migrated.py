"""instance edge mirroring, migrated — world edges mirror to WorldInstance
edges in the WorldAdapter (no CuriousAgent). Covers all of
tests/test_instance_edge_mirroring: mirror, dedup, spatial topology emerges,
Term.* skipped, arbitrary edge types, self-loops not mirrored.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world_from_edges(nodes, edges):
    g = TypedGraph()
    ids = [g._insert_node(t, a) for (t, a) in nodes]
    for s, et, t in edges:
        g._insert_edge(ids[s], et, ids[t])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def _out(wa, key, et):
    return wa.inner.neighbours(wa._instances[key], et)


def test_edge_mirrored_to_world_instances():
    wa = WorldAdapter()
    wa.ingest(_world_from_edges(
        [("AgentMarker", {"id": "a"}), ("AgentMarker", {"id": "b"})],
        [(0, "knows_human", 1)]))
    assert wa._instances[("AgentMarker", "b")] in _out(wa, ("AgentMarker", "a"), "knows_human")


def test_mirroring_deduplicated_across_ticks():
    wa = WorldAdapter()
    w = _world_from_edges([("AgentMarker", {"id": "a"}), ("AgentMarker", {"id": "b"})],
                          [(0, "knows_human", 1)])
    for _ in range(3):
        wa.ingest(w)
    assert len(_out(wa, ("AgentMarker", "a"), "knows_human")) == 1


def test_spatial_topology_emerges():
    wa = WorldAdapter()
    wa.ingest(_world_from_edges(
        [("SpatialLocation", {"id": "0_0"}), ("SpatialLocation", {"id": "1_0"}),
         ("SpatialLocation", {"id": "1_1"})],
        [(0, "adjacent_to", 1), (1, "adjacent_to", 2)]))
    for src, tgt in [("0_0", "1_0"), ("1_0", "1_1")]:
        assert wa._instances[("SpatialLocation", tgt)] in _out(wa, ("SpatialLocation", src), "adjacent_to")


def test_mirroring_skips_term_nodes():
    wa = WorldAdapter()
    wa.ingest(_world_from_edges(
        [("AgentMarker", {"id": "a"}), ("Term.Lit", {"id": "lit_0", "value": "x"})],
        [(0, "asserts", 1)]))
    assert ("Term.Lit", "lit_0") not in wa._instances
    assert list(wa.inner.neighbours(wa._instances[("AgentMarker", "a")], "asserts")) == []


def test_arbitrary_edge_type_first_time():
    wa = WorldAdapter()
    wa.ingest(_world_from_edges(
        [("AgentMarker", {"id": "a"}), ("AgentMarker", {"id": "b"})],
        [(0, "loves", 1)]))
    assert wa._instances[("AgentMarker", "b")] in _out(wa, ("AgentMarker", "a"), "loves")


def test_self_loop_not_mirrored():
    wa = WorldAdapter()
    wa.ingest(_world_from_edges([("AgentMarker", {"id": "a"})], [(0, "thinks_about", 0)]))
    assert list(wa.inner.neighbours(wa._instances[("AgentMarker", "a")], "thinks_about")) == []
