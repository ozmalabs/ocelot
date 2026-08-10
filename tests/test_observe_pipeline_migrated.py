"""observe pipeline, migrated — the instance-tracking fold runs in the
WorldAdapter (no CuriousAgent). Covers the core assertions of the old
test_world_instances / test_instance_edge_mirroring / test_frontier_seeking:
WorldInstance creation + (world_type, world_id) attrs, n_observations
accumulation, instance-instance edge mirroring with dedup, and the freshening
count (new info = a new instance or a new edge, NOT an attr change).
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


def test_instance_created_with_type_and_id():
    wa = WorldAdapter()
    wa.ingest(_world({"g": ("Game", {"id": "game_5"})}))
    nid = wa._instances[("Game", "game_5")]
    attrs = wa.s.node(nid)["attrs"]
    assert attrs["world_type"] == "Game" and attrs["world_id"] == "game_5"


def test_n_observations_accumulates():
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "agent_0"})})
    for _ in range(7):
        wa.ingest(w)
    nid = wa._instances[("AgentMarker", "agent_0")]
    assert wa.s.node(nid)["attrs"]["n_observations"] == 7


def test_edge_mirrored_and_deduplicated():
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "a"}), "b": ("AgentMarker", {"id": "b"})},
               [("a", "knows_human", "b")])
    for _ in range(4):
        wa.ingest(w)
    aw, bw = wa._instances[("AgentMarker", "a")], wa._instances[("AgentMarker", "b")]
    out = wa.inner.neighbours(aw, "knows_human")
    assert len(out) == 1 and bw in out


def test_freshening_counts_new_info_only():
    wa = WorldAdapter()
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a"})}))
    assert wa.last_freshening_count == 1                      # new instance
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a"})}))
    assert wa.last_freshening_count == 0                      # stable re-observe
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 1})}))
    assert wa.last_freshening_count == 0                      # attr change ≠ fresh


def test_no_id_nodes_do_not_freshen():
    wa = WorldAdapter()
    wa.ingest(_world({"b": ("Body", {"hp": 100})}))
    assert wa.last_freshening_count == 0
