"""world instances, migrated — WorldInstance creation/sharing + OO body-type
structure run in the WorldAdapter (no CuriousAgent). Covers all of
tests/test_world_instances: creation, type/id attrs, n_observations, sharing,
distinct ids, Term.* skipped, knows-edges, instance_of -> shared BodyType,
type-level attr inheritance via traversal.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(nodes):
    g = TypedGraph()
    for (t, a) in nodes:
        g._insert_node(t, a)
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_instance_created_and_attrs():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "agent_1"})]))
    assert ("AgentMarker", "agent_1") in wa._instances
    wa2 = WorldAdapter()
    wa2.ingest(_world([("Game", {"id": "game_5"})]))
    a = wa2.s.node(wa2._instances[("Game", "game_5")])["attrs"]
    assert a["world_type"] == "Game" and a["world_id"] == "game_5"


def test_n_observations_accumulates():
    wa = WorldAdapter()
    w = _world([("AgentMarker", {"id": "agent_0"})])
    for _ in range(7):
        wa.ingest(w)
    assert wa.s.node(wa._instances[("AgentMarker", "agent_0")])["attrs"]["n_observations"] == 7


def test_instance_shared_across_observations():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "agent_0"})]))
    first = wa._instances[("AgentMarker", "agent_0")]
    wa.ingest(_world([("AgentMarker", {"id": "agent_0"})]))
    assert wa._instances[("AgentMarker", "agent_0")] == first


def test_distinct_ids_get_distinct_instances():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": f"agent_{i}"}) for i in range(3)]))
    assert len({wa._instances[k] for k in wa._instances}) == 3


def test_term_nodes_not_tracked():
    wa = WorldAdapter()
    wa.ingest(_world([("Term.Lit", {"value": "hello", "id": "ignored"})]))
    assert not any(t.startswith("Term.") for (t, _) in wa._instances)


def test_knows_edge_per_instance():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "agent_1"}), ("Game", {"id": "game_0"})]))
    known = wa.inner.neighbours(wa.agent, "knows")
    assert len(known) == 2
    assert {wa.s.node(n)["type"] for n in known} == {"WorldInstance"}


def test_instance_of_edge_to_body_type():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "agent_1"}), ("Game", {"id": "game_0"})]))
    for (wt, wid), wi in wa._instances.items():
        bts = wa.inner.neighbours(wi, "instance_of")
        assert len(bts) == 1
        bt = wa.s.node(bts[0])
        assert bt["type"] == "BodyType" and bt["attrs"]["name"] == wt


def test_all_instances_share_one_body_type():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": f"agent_{i}"}) for i in range(3)]))
    bts = set()
    for (wt, _), wi in wa._instances.items():
        if wt == "AgentMarker":
            bts.update(wa.inner.neighbours(wi, "instance_of"))
    assert len(bts) == 1


def test_type_level_attr_inherited_via_traversal():
    wa = WorldAdapter()
    wa.ingest(_world([("AgentMarker", {"id": "agent_0"})]))
    bt = wa.body_type("AgentMarker")
    wa.inner.set_attr(bt, "can_message", True)
    wi = wa._instances[("AgentMarker", "agent_0")]
    tgt = wa.inner.neighbours(wi, "instance_of")[0]
    assert wa.s.node(tgt)["attrs"]["can_message"] is True
