"""Relational production, migrated — the agent renders a binary-relation meaning
to surface text on the seed-booted WorldAdapter (no CuriousAgent), via the SAME
graph-resident Render engine the jabberwock built for Term rendering.

CuriousAgent's `utterance_for` delegated to the pure-Python `produce()` fold (a
composition the architecture rule forbids in the adapter). Instead the meaning is
mirrored to a Term.Relation / Term.Leaf subgraph (mechanical structure
translation; each concept resolved to its sign form, the marker baked onto the
form) and rendered by ONE pair of RenderRules — Relation (`left form right`) and
Leaf (`form`). The per-relation word rides on the node's `form` scalar attr (a
scalar-bound slot), so the Rust Render engine folds the whole tree, recursing on
nested relations. Word order / surface is decided by the graph RenderRules.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _adapter():
    wa = WorldAdapter()
    # relation signs (form, concept[, marker])
    for form, concept, marker in [
        ("uses", "uses", ""), ("depends", "depends_on", "on"),
        ("runs", "runs_on", "on"), ("is_a", "is_a", ""),
        ("contains", "contains", ""), ("optimised", "optimised_for", "for"),
    ]:
        wa.learn_sign(form, concept, marker)
    # operand signs (form == concept)
    for w in ("process", "graph", "agent", "linux", "mind", "design", "data",
              "amd"):
        wa.learn_sign(w, w)
    return wa


def test_infix_relation_renders_X_verb_Y():
    wa = _adapter()
    assert wa.utterance_for({"uses": {"left": "process", "right": "graph"}}) \
        == "process uses graph"


def test_marked_relation_renders_X_form_marker_Y():
    wa = _adapter()
    assert wa.utterance_for({"runs_on": {"left": "agent", "right": "linux"}}) \
        == "agent runs on linux"


def test_taxonomy_relation_renders():
    wa = _adapter()
    assert wa.utterance_for({"is_a": {"left": "agent", "right": "mind"}}) \
        == "agent is_a mind"


def test_nested_relation_renders_a_chain():
    """A relation whose subject is itself a relation — recursion through the
    Render engine: 'process uses graph' nested inside 'runs on linux'."""
    wa = _adapter()
    nested = {"runs_on": {
        "left": {"uses": {"left": "process", "right": "graph"}},
        "right": "linux"}}
    assert wa.utterance_for(nested) == "process uses graph runs on linux"


def test_predicate_argument_renders_form_role_arg():
    """A predicate with ONE named-role argument ({pred: {role: arg}}) renders
    'predform role arg' via the Pred RenderRule — distinct from a binary
    relation. The role word is the connector; the predicate's sign form + role
    bake onto `form`, the single argument renders recursively on the `arg`
    slot. This is the shape mental-state / capability meanings take, e.g.
    {believe: {of: X}} -> 'believe of X'."""
    wa = _adapter()
    wa.learn_sign("determinant", "det")
    # known predicate sign -> its form; unknown arg -> bare concept word
    assert wa.utterance_for({"det": {"of": "M"}}) == "determinant of M"
    # no sign for the predicate -> the bare concept name carries through
    assert wa.utterance_for({"believe": {"of": "gravity"}}) \
        == "believe of gravity"
    # the argument may itself be a relation — recursion through the engine
    nested = {"believe": {"of": {"uses": {"left": "process", "right": "graph"}}}}
    assert wa.utterance_for(nested) == "believe of process uses graph"


def test_compositional_relations_examples():
    wa = _adapter()
    cases = [
        ({"uses": {"left": "design", "right": "graph"}}, "design uses graph"),
        ({"runs_on": {"left": "agent", "right": "linux"}}, "agent runs on linux"),
        ({"depends_on": {"left": "process", "right": "data"}},
         "process depends on data"),
        ({"is_a": {"left": "agent", "right": "mind"}}, "agent is_a mind"),
        ({"contains": {"left": "graph", "right": "process"}},
         "graph contains process"),
        ({"optimised_for": {"left": "design", "right": "amd"}},
         "design optimised for amd"),
    ]
    for meaning, expected in cases:
        assert wa.utterance_for(meaning) == expected, meaning


def test_signs_and_render_rules_are_graph_resident():
    """The lexicon Signs and the relational RenderRules are graph data."""
    wa = _adapter()
    wa.install_relations_renderer()
    assert any(wa.s.node(n)["attrs"].get("concept") == "uses"
               for n in wa.s.nodes("Sign"))
    assert len(wa.render_rules_for("relations", "Relation")) == 1
    assert len(wa.render_rules_for("relations", "Leaf")) == 1


# --- install half: the relation taxonomy is graph data (relations seed) --

from substrate.boot_core import load_seeds_into  # noqa: E402
from domains.relations import (  # noqa: E402  (pure data — the seed's truth)
    _INFIX_RELATIONS, _MARKED_RELATIONS, _TAXONOMY_RELATIONS, _RELATIONS_MT)


def _relations_booted():
    wa = WorldAdapter()
    load_seeds_into(wa.s, wa.agent, ["relations"])
    return wa


def test_install_creates_relations_mt():
    wa = _relations_booted()
    mts = {wa.s.node(n)["attrs"].get("name") for n in wa.s.nodes("Microtheory")}
    assert _RELATIONS_MT in mts


def test_install_creates_all_infix_concepts():
    wa = _relations_booted()
    for _form, concept, _desc in _INFIX_RELATIONS:
        assert wa._concept_by_name(concept) is not None, concept


def test_install_creates_all_marked_concepts():
    wa = _relations_booted()
    for _form, concept, _marker, _desc in _MARKED_RELATIONS:
        assert wa._concept_by_name(concept) is not None, concept


def test_install_creates_taxonomy_concepts():
    wa = _relations_booted()
    for _form, concept, _desc in _TAXONOMY_RELATIONS:
        assert wa._concept_by_name(concept) is not None, concept


def test_relations_seed_is_idempotent():
    wa = _relations_booted()
    n = len(wa.s.nodes("Concept"))
    load_seeds_into(wa.s, wa.agent, ["relations"])
    assert len(wa.s.nodes("Concept")) == n
