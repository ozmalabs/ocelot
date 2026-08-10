"""per-(type,attr) epistemic state, migrated — Attribute-node saturation runs
in the WorldAdapter and is decided by the SEEDED saturation_predicate (no
CuriousAgent). Covers tests/test_epistemic_state: Attribute nodes carry the
counters, observed_count climbs, saturation resets on a new value, distinct_count
grows, the saturation policy is a graph-resident Term-tree (Gte(Attr(..,
"saturation_count"), Lit(30))) attached to the agent by a `saturation_predicate`
edge, is_saturated reads that graph-resident policy (one policy, both scopes),
editing the threshold Lit changes the decision, and unsaturated_attributes
surfaces the "what I don't yet know" catalogue.

The one original assertion with no migrated equivalent is
`test_saturation_predicate_is_admitted_by_meta_gamma`: it asserts the
`saturation_predicate` edge is a Γ_meta production. In the seed-boot architecture
the policy edge is installed by the epistemics_core seed as graph data (an
unchecked edge); only theorem_core registers meta productions (asserts/predicate),
so `saturation_predicate` is NOT in `grammar_to_json()` / `meta_productions()`.
The old `meta_grammar()` enumeration that produced that production is a
CuriousAgent construction the migration deliberately did not reproduce. That
assertion is therefore not portable without re-introducing agent-construction
logic into the seed boot.
"""
from __future__ import annotations

from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph
from substrate.world_adapter import WorldAdapter


def _world(nodes):
    g = TypedGraph()
    for nm, (t, a) in nodes.items():
        g._insert_node(t, a)
    return Substrate(graph=g, checker=ConsistencyChecker(Grammar([])))


def test_attribute_nodes_carry_counters():
    """Maps test_attribute_nodes_appear_in_mind_graph: after perception the agent
    has Attribute nodes for the (type, attr) pairs it has seen, each carrying the
    saturation-tracking counters — substrate state, not Python state."""
    wa = WorldAdapter()
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 3})}))
    # at least one Attribute node exists in the graph
    assert len(list(wa.s.nodes("Attribute"))) > 0
    st = wa.attribute_state("AgentMarker", "hunger")
    for k in ("observed_count", "saturation_count", "distinct_count",
              "type_name", "attr_name"):
        assert k in st


def test_observed_count_and_saturation_climb_on_stable_value():
    """Part of test_attribute_saturation_resets_on_new_value: observed_count and
    saturation_count climb while a value stays stable; distinct_count is 1."""
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "a", "hunger": 3})})
    for _ in range(3):
        wa.ingest(w)
    st = wa.attribute_state("AgentMarker", "hunger")
    assert st["observed_count"] == 3
    assert st["distinct_count"] == 1
    assert st["saturation_count"] == 2


def test_saturation_resets_on_new_value():
    """Maps test_attribute_saturation_resets_on_new_value: a never-seen value
    resets saturation_count to 0, bumps distinct_count, and observed_count keeps
    climbing — the agent has just learned its world was bigger than it thought."""
    wa = WorldAdapter()
    for _ in range(3):
        wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 3})}))
    wa.ingest(_world({"a": ("AgentMarker", {"id": "a", "hunger": 9})}))
    st = wa.attribute_state("AgentMarker", "hunger")
    assert st["saturation_count"] == 0
    assert st["distinct_count"] == 2
    assert st["observed_count"] == 4


def test_saturation_policy_is_a_term_tree_in_graph():
    """Maps test_saturation_policy_is_a_term_tree_in_mind_graph: the 'is_saturated'
    decision is a graph-resident Term-tree, not Python. Exactly one
    `saturation_predicate` edge from the agent; its target is a Term node of shape
    Gte(Attr(.., "saturation_count"), Lit(30)) — the threshold (30) lives as a Lit
    in graph data, so the agent can read (and in principle edit) its own policy."""
    wa = WorldAdapter()
    preds = list(wa.inner.neighbours(wa.agent, "saturation_predicate"))
    assert len(preds) == 1, "agent should have exactly one saturation policy"
    root = preds[0]
    root_node = wa.s.node(root)
    assert root_node["type"].startswith("Term."), (
        "saturation policy target should be a Term node")
    # shape: Gte(Attr(Var, "saturation_count"), Lit(30))
    assert root_node["type"] == "Term.Gte"
    a_children = list(wa.inner.neighbours(root, "child.a"))
    b_children = list(wa.inner.neighbours(root, "child.b"))
    assert len(a_children) == 1 and len(b_children) == 1
    attr_node = wa.s.node(a_children[0])
    assert attr_node["type"] == "Term.Attr"
    assert attr_node["attrs"]["key"] == "saturation_count"
    lit_node = wa.s.node(b_children[0])
    assert lit_node["type"] == "Term.Lit"
    assert lit_node["attrs"]["value"] == 30, (
        f"default saturation threshold should be 30 (lives as a Lit in graph "
        f"data); got {lit_node['attrs']['value']}")


def test_is_saturated_reads_seeded_policy():
    """Maps test_unsaturated_attributes_query + the climbing half of
    test_is_saturated_reads_from_graph: is_saturated evaluates the seeded
    saturation_predicate over the Attribute node — at threshold 30 a few
    observations are unsaturated (and surface in the catalogue), and once
    saturation_count crosses 30 the agent's own policy says saturated."""
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "a", "hunger": 3})})
    for _ in range(3):
        wa.ingest(w)
    assert wa.is_saturated("AgentMarker", "hunger") is False
    assert len(wa.unsaturated_attributes()) > 0
    for _ in range(30):
        wa.ingest(w)
    assert wa.is_saturated("AgentMarker", "hunger") is True


def test_is_saturated_reflects_edited_threshold_lit():
    """Maps the editing half of test_is_saturated_reads_from_graph: is_saturated
    reads the Term-tree policy from the graph, not Python. Editing the threshold
    Lit (the Gte's child.b) to 0 — the agent's own policy — makes every observed
    attribute saturated, with no Python touched; restoring the Lit restores the
    decision."""
    wa = WorldAdapter()
    w = _world({"a": ("AgentMarker", {"id": "a", "hunger": 3})})
    for _ in range(3):
        wa.ingest(w)
    # with the default threshold (30) and few observations: not saturated
    assert wa.is_saturated("AgentMarker", "hunger") is False
    # find the Lit child (the threshold node) of the seeded policy Term-tree
    root = wa.inner.neighbours(wa.agent, "saturation_predicate")[0]
    lit = wa.inner.neighbours(root, "child.b")[0]
    original = wa.s.node(lit)["attrs"]["value"]
    wa.inner.set_attr(lit, "value", 0)
    try:
        assert wa.is_saturated("AgentMarker", "hunger") is True, (
            "after lowering threshold to 0, agent's own policy should say saturated")
    finally:
        wa.inner.set_attr(lit, "value", original)
    assert wa.is_saturated("AgentMarker", "hunger") is False