"""Insight() generalization pass, migrated — runs in the WorldAdapter (no
CuriousAgent). Covers tests/test_insight.

Two graph-data operations, both mechanical aggregations over the mirrored
WorldInstance graph that the adapter's `insight()` performs:

  - **Type-level promotion**: per-instance properties (incl. the in_/out_ edge
    participation counters derived from the mirrored instance->instance edges)
    that hold for at least the seeded `insight_threshold` fraction of a
    BodyType's instances get promoted to a `typical_<attr>` flag on the
    BodyType — encoding the generalization once instead of per instance.
  - **Category discovery**: instances with the same edge fingerprint get a new
    `cat_*` BodyType they additionally link to via `instance_of` (OO-style
    multiple inheritance).

The DECISION threshold is the seeded `insight_threshold` Lit the agent reads,
not a Python constant; the adapter only counts and reifies.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(node_specs, edge_specs=()):
    g = TypedGraph()
    nid_by_label = {}
    for label, typ, attrs in node_specs:
        nid_by_label[label] = g._insert_node(typ, attrs)
    for src_label, edge_type, tgt_label in edge_specs:
        g._insert_edge(nid_by_label[src_label], edge_type, nid_by_label[tgt_label])
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_insight_threshold_seeded():
    wa = WorldAdapter()
    assert wa.get_scalar_policy("insight_threshold", -1) == 0.7


def test_promotion_when_default_outweighs_specific():
    """Three AgentMarkers all receive 'to_agent' edges (they're all targets
    of invitations). After observation, insight() should promote
    'typical_in_to_agent' to the AgentMarker BodyType."""
    wa = WorldAdapter()
    sub = _world(
        [
            ("a0", "AgentMarker", {"id": "agent_0"}),
            ("a1", "AgentMarker", {"id": "agent_1"}),
            ("a2", "AgentMarker", {"id": "agent_2"}),
            ("inv0", "Invitation", {"id": "inv_0"}),
            ("inv1", "Invitation", {"id": "inv_1"}),
            ("inv2", "Invitation", {"id": "inv_2"}),
        ],
        [
            ("inv0", "to_agent", "a0"),
            ("inv1", "to_agent", "a1"),
            ("inv2", "to_agent", "a2"),
        ],
    )
    wa.observe(sub)
    result = wa.insight()
    bt_id = wa.body_type("AgentMarker")
    attrs = wa.s.node(bt_id)["attrs"]
    assert "typical_in_to_agent" in attrs
    assert ("AgentMarker", "in_to_agent") in result["promoted"]


def test_no_promotion_when_only_one_instance():
    """Promotion requires >= 2 instances to generalise over."""
    wa = WorldAdapter()
    sub = _world(
        [
            ("a0", "AgentMarker", {"id": "agent_0"}),
            ("inv0", "Invitation", {"id": "inv_0"}),
        ],
        [("inv0", "to_agent", "a0")],
    )
    wa.observe(sub)
    wa.insight()
    bt_id = wa.body_type("AgentMarker")
    attrs = wa.s.node(bt_id)["attrs"]
    assert "typical_in_to_agent" not in attrs


def test_category_discovery_groups_instances_by_edge_fingerprint():
    """Two AgentMarkers that share the same edges become a category;
    a third with a different edge pattern doesn't join."""
    wa = WorldAdapter()
    sub = _world(
        [
            ("a0", "AgentMarker", {"id": "agent_0"}),  # gets to_agent only
            ("a1", "AgentMarker", {"id": "agent_1"}),  # gets to_agent only
            ("a2", "AgentMarker", {"id": "agent_2"}),  # gets has_player only
            ("inv0", "Invitation", {"id": "inv_0"}),
            ("inv1", "Invitation", {"id": "inv_1"}),
            ("g0", "Game", {"id": "g_0"}),
        ],
        [
            ("inv0", "to_agent", "a0"),
            ("inv1", "to_agent", "a1"),
            ("g0", "has_player", "a2"),
        ],
    )
    wa.observe(sub)
    result = wa.insight()
    # At least one new category should have formed (cat_*).
    cat_names = [c[0] for c in result["categories"]]
    assert len(cat_names) >= 1
    # The category that groups a0+a1 should have those as instance_of:
    found_pair = False
    for cat_name in cat_names:
        if not cat_name.startswith("cat_"):
            continue
        cat_id = wa._body_types[cat_name]
        members = set()
        for wid, wi_id in wa._instances.items():
            for tgt in wa.inner.neighbours(wi_id, "instance_of"):
                if tgt == cat_id:
                    members.add(wid)
        if {("AgentMarker", "agent_0"), ("AgentMarker", "agent_1")} <= members:
            found_pair = True
            break
    assert found_pair, "expected a category grouping the two like-edged AgentMarkers"


def test_insight_is_idempotent():
    """Running insight twice doesn't duplicate promotions or categories."""
    wa = WorldAdapter()
    sub = _world(
        [
            ("a0", "AgentMarker", {"id": "agent_0"}),
            ("a1", "AgentMarker", {"id": "agent_1"}),
            ("inv0", "Invitation", {"id": "inv_0"}),
            ("inv1", "Invitation", {"id": "inv_1"}),
        ],
        [
            ("inv0", "to_agent", "a0"),
            ("inv1", "to_agent", "a1"),
        ],
    )
    wa.observe(sub)
    wa.insight()
    second = wa.insight()
    # Second pass shouldn't promote anything new — both promotion lists
    # describe newly-added marker attrs / categories.
    assert second["promoted"] == []
    assert second["categories"] == []
    # And the type-level attr stays:
    bt_id = wa.body_type("AgentMarker")
    assert wa.s.node(bt_id)["attrs"].get("typical_in_to_agent") is True


def test_instance_has_multiple_instance_of_after_category_discovery():
    """After category discovery, a member instance has TWO instance_of
    edges: one to its original type, one to the new category. Multiple
    inheritance, OO-style."""
    wa = WorldAdapter()
    sub = _world(
        [
            ("a0", "AgentMarker", {"id": "agent_0"}),
            ("a1", "AgentMarker", {"id": "agent_1"}),
            ("inv0", "Invitation", {"id": "inv_0"}),
            ("inv1", "Invitation", {"id": "inv_1"}),
        ],
        [
            ("inv0", "to_agent", "a0"),
            ("inv1", "to_agent", "a1"),
        ],
    )
    wa.observe(sub)
    wa.insight()
    wi_id = wa._instances[("AgentMarker", "agent_0")]
    parents = [wa.s.node(tgt)["attrs"].get("name")
               for tgt in wa.inner.neighbours(wi_id, "instance_of")]
    assert "AgentMarker" in parents
    assert any(p.startswith("cat_") for p in parents)
    assert len(parents) >= 2
