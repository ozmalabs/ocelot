"""Research derivation tracing bridges only to explicitly bound native Terms."""
from __future__ import annotations

import pytest

from scripts.ocelot_research import ResearchError
from scripts.ocelot_research_trace import bind_term, execute, trace_chain


def _state(edges=()):
    return {"nodes": [
        {"id": "claim-1", "type": "Claim", "wording": "An assertion", "status": "supported_within_scope"},
        {"id": "evidence-1", "type": "Evidence", "provenance": {"source": "authored"}},
        {"id": "source-1", "type": "Source"},
    ], "edges": list(edges)}


def test_linear_trace_preserves_provenance_and_does_not_assess_truth():
    state = _state([
        {"id": "edge-1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1", "provenance": {"author": "A"}},
        {"id": "edge-2", "type": "derived_from", "src": "evidence-1", "tgt": "source-1"},
    ])
    result = trace_chain(state, "claim-1")
    assert result["status"] == "complete"
    assert result["path"] == ["claim-1", "evidence-1", "source-1"]
    assert result["edges"][0]["provenance"] == {"author": "A"}
    assert result["truth_assessed"] is False


@pytest.mark.parametrize("edges,status", [
    ([], "missing"),
    ([{"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
      {"id": "e2", "type": "derived_from", "src": "claim-1", "tgt": "source-1"}], "branch"),
    ([{"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
      {"id": "e2", "type": "derived_from", "src": "evidence-1", "tgt": "claim-1"}], "cycle"),
])
def test_trace_surfaces_non_linear_and_incomplete_chains(edges, status):
    assert trace_chain(_state(edges), "claim-1")["status"] == status


def test_branch_trace_visits_both_dependency_edges():
    state = _state([
        {"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
        {"id": "e2", "type": "derived_from", "src": "claim-1", "tgt": "source-1"},
    ])
    trace = trace_chain(state, "claim-1")
    assert trace["status"] == "branch"
    assert {n["id"] for n in trace["nodes"]} == {"claim-1", "evidence-1", "source-1"}
    assert {e["id"] for e in trace["edges"]} == {"e1", "e2"}


def test_trace_retains_both_paths_through_a_shared_dependency():
    state = {"nodes": [{"id": n, "type": "Evidence"} for n in "abcd"], "edges": [
        {"id": "e1", "type": "derived_from", "src": "a", "tgt": "b"},
        {"id": "e2", "type": "derived_from", "src": "a", "tgt": "c"},
        {"id": "e3", "type": "derived_from", "src": "b", "tgt": "d"},
        {"id": "e4", "type": "derived_from", "src": "c", "tgt": "d"},
    ]}
    trace = trace_chain(state, "a")
    assert trace["status"] == "branch"
    assert trace["paths"] == [["a", "b", "d"], ["a", "c", "d"]]
    assert {edge["id"] for edge in trace["edges"]} == {"e1", "e2", "e3", "e4"}


def test_trace_depth_is_bounded():
    state = _state([
        {"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
        {"id": "e2", "type": "derived_from", "src": "evidence-1", "tgt": "source-1"},
    ])
    assert trace_chain(state, "claim-1", max_depth=1)["status"] == "bound_exceeded"


def test_native_evalsubgraph_requires_explicit_term_binding_and_is_not_truth_verdict():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    sub = Substrate()
    state = _state([{"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"}])
    state["nodes"][0]["term"] = {"type": "EvalSubgraph", "node": {"type": "Var", "name": "evidence"}}
    state["nodes"][0]["bindings"] = {"evidence": "evidence-1"}
    state["nodes"][1]["term"] = {"type": "Lit", "value": True}
    result = execute(state, "claim-1", sub)
    assert result["value"] is True
    assert result["materialized_nodes"] == ["claim-1", "evidence-1"]
    assert result["truth_assessed"] is False
    assert "not assessed" in result["interpretation"]


def test_bindings_require_a_matching_derived_from_edge():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    sub = Substrate()
    state = _state()
    state["nodes"][0]["term"] = {"type": "Lit", "value": 1}
    state["nodes"][0]["bindings"] = {"evidence": "evidence-1"}
    with pytest.raises(ResearchError, match="lacks a derived_from edge"):
        execute(state, "claim-1", sub)


def test_native_execution_supports_multiple_dependencies_and_deduplicates_shared_nodes():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    sub = Substrate()
    state = _state([
        {"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
        {"id": "e2", "type": "derived_from", "src": "claim-1", "tgt": "source-1"},
    ])
    state["nodes"][0]["term"] = {"type": "Plus", "items": [
        {"type": "EvalSubgraph", "node": {"type": "Var", "name": "left"}},
        {"type": "EvalSubgraph", "node": {"type": "Var", "name": "right"}},
    ]}
    state["nodes"][0]["bindings"] = {"left": "evidence-1", "right": "source-1"}
    state["nodes"][1]["term"] = {"type": "Lit", "value": 2}
    state["nodes"][2]["term"] = {"type": "Lit", "value": 3}
    result = execute(state, "claim-1", sub)
    assert result["value"] == 5
    assert set(result["materialized_nodes"]) == {"claim-1", "evidence-1", "source-1"}


def test_native_execution_rejects_binding_cycles():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    state = _state([
        {"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
        {"id": "e2", "type": "derived_from", "src": "evidence-1", "tgt": "claim-1"},
    ])
    state["nodes"][0].update(term={"type": "Lit", "value": 1}, bindings={"e": "evidence-1"})
    state["nodes"][1].update(term={"type": "Lit", "value": 2}, bindings={"c": "claim-1"})
    with pytest.raises(ResearchError, match="cyclic term binding"):
        execute(state, "claim-1", Substrate())


def test_native_execution_resolves_aliases_at_three_levels():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    state = _state([
        {"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
        {"id": "e2", "type": "derived_from", "src": "evidence-1", "tgt": "source-1"},
    ])
    state["nodes"][0].update(term={"type": "EvalSubgraph", "node": {"type": "Var", "name": "evidence"}},
                             bindings={"evidence": "evidence-1"})
    state["nodes"][1].update(term={"type": "EvalSubgraph", "node": {"type": "Var", "name": "source"}},
                             bindings={"source": "source-1"})
    state["nodes"][2]["term"] = {"type": "Lit", "value": 9}
    result = execute(state, "claim-1", Substrate())
    assert result["value"] == 9


def test_native_execution_rejects_alias_collision_across_dependencies():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    state = _state([
        {"id": "e1", "type": "derived_from", "src": "claim-1", "tgt": "evidence-1"},
        {"id": "e2", "type": "derived_from", "src": "evidence-1", "tgt": "source-1"},
    ])
    state["nodes"][0].update(term={"type": "EvalSubgraph", "node": {"type": "Var", "name": "x"}},
                             bindings={"x": "evidence-1"})
    state["nodes"][1].update(term={"type": "Lit", "value": 4}, bindings={"x": "source-1"})
    state["nodes"][2]["term"] = {"type": "Lit", "value": 5}
    with pytest.raises(ResearchError, match="ambiguous binding alias"):
        execute(state, "claim-1", Substrate())


def test_reserved_target_term_alias_and_external_env_are_rejected():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    state = _state()
    state["nodes"][0]["term"] = {"type": "Lit", "value": 1}
    state["nodes"][0]["bindings"] = {"target_term": "evidence-1"}
    state["nodes"][1]["term"] = {"type": "Lit", "value": 2}
    with pytest.raises(ResearchError, match="reserved"):
        execute(state, "claim-1", Substrate())

    state["nodes"][0]["bindings"] = {}
    with pytest.raises(ResearchError, match="reserved"):
        execute(state, "claim-1", Substrate(), {"target_term": 99})


def test_unbound_native_variable_is_reported_unresolved_not_computed():
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    state = _state()
    state["nodes"][0]["term"] = {"type": "Var", "name": "missing_input"}
    result = execute(state, "claim-1", Substrate())
    assert result["status"] == "unresolved"
    assert result["value"] is None
    assert "ambiguous" in result["interpretation"]
    assert result["truth_assessed"] is False
