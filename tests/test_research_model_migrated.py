from __future__ import annotations

import pytest

from scripts.ocelot_research import ResearchError, ResearchGraph
from scripts.ocelot_research_model import create_model_candidate, execute_model_candidate


def _paper_claim(tmp_path):
    graph = ResearchGraph.create("Interpret a paper claim", root=tmp_path,
                                 investigation_id="model-bridge")
    source = graph.record("Source", locator={"root_id": "paper", "path": "paper.md",
                                              "start_line": 12, "sha256": "a" * 64})
    claim = graph.record("Claim", wording="A stated paper claim", claim_type="theorem",
                         status="open", provenance={"reader": "paper_reader"})
    graph.link(claim["id"], "cites", source["id"],
               provenance={"method": "reader_import"})
    return graph, claim


def test_candidate_requires_source_provenance_and_explicit_review(tmp_path):
    graph, claim = _paper_claim(tmp_path)
    result = create_model_candidate(
        graph, claim_id=claim["id"], term={"type": "Lit", "value": True},
        residuals=["The Term does not encode the theorem's domain quantifier."],
        reviewer="researcher", review_note="Boolean toy encoding only.")
    candidate = result["candidate"]
    assert candidate["representation_of"] == claim["id"]
    assert candidate["model_candidate"] is True
    assert candidate["source_provenance"]["status"] == "recorded_assertion_not_reverified"
    assert candidate["source_provenance"]["locators"][0]["source_id"]
    assert result["residuals"]
    assert result["truth_assessed"] is False
    assert result["lean"]["status"] == "available"
    assert result["lean"]["kernel_checked"] is False
    assert result["review_required"] is True


def test_candidate_records_assumptions_and_executes_only_supplied_term(tmp_path):
    pytest.importorskip("substrate_rs")
    from substrate_rs import Substrate

    graph, claim = _paper_claim(tmp_path)
    assumption = graph.record("Assumption", wording="Finite Boolean input")
    graph.record("Claim", wording="Explicit assumed input", term={"type": "Lit", "value": True},
                 bindings={})
    dependency = graph.state()["nodes"][-1]
    result = create_model_candidate(
        graph, claim_id=claim["id"],
        term={"type": "EvalSubgraph", "node": {"type": "Var", "name": "input"}},
        bindings={"input": dependency["id"]}, assumption_ids=[assumption["id"]],
        residuals=[], reviewer="researcher", review_note="Test supplied representation.")
    candidate_id = result["candidate"]["id"]
    edges = graph.state()["edges"]
    assert any(e["type"] == "assumes" and e["src"] == candidate_id and e["tgt"] == assumption["id"] for e in edges)
    assert any(e["type"] == "derived_from" and e["src"] == candidate_id and e["tgt"] == dependency["id"] for e in edges)
    executed = execute_model_candidate(graph, candidate_id, Substrate())
    assert executed["status"] == "computed"
    assert executed["value"] is True
    assert executed["truth_assessed"] is False


def test_candidate_rejects_missing_source_hash_or_missing_review(tmp_path):
    graph = ResearchGraph.create("Missing locator hash", root=tmp_path,
                                 investigation_id="model-no-hash")
    source = graph.record("Source", locator={"root_id": "paper", "path": "paper.md"})
    claim = graph.record("Claim", wording="A stated paper claim")
    graph.link(claim["id"], "cites", source["id"])
    with pytest.raises(ResearchError, match="path and sha256"):
        create_model_candidate(graph, claim_id=claim["id"], term={"type": "Lit", "value": True},
                               residuals=[], reviewer="reviewer", review_note="reviewed")
    graph2, claim2 = _paper_claim(tmp_path / "second")
    with pytest.raises(ResearchError, match="review_note"):
        create_model_candidate(graph2, claim_id=claim2["id"], term={"type": "Lit", "value": True},
                               residuals=[], reviewer="reviewer", review_note=" ")


def test_unsupported_lean_keeps_candidate_and_bad_dependency_fails_before_write(tmp_path):
    graph, claim = _paper_claim(tmp_path)
    before = len(graph.state()["nodes"])
    with pytest.raises(ResearchError, match="explicit native Term"):
        create_model_candidate(graph, claim_id=claim["id"],
                               term={"type": "Lit", "value": 1},
                               bindings={"missing_term": claim["id"]}, residuals=[],
                               reviewer="researcher", review_note="review")
    assert len(graph.state()["nodes"]) == before
    result = create_model_candidate(
        graph, claim_id=claim["id"],
        term={"type": "Div", "a": {"type": "Lit", "value": 1},
                                    "b": {"type": "Lit", "value": 2}},
        residuals=["No mapping from the paper's domain semantics."],
        reviewer="researcher", review_note="Explicit numeric toy model.")
    assert result["candidate"]["id"] in {n["id"] for n in graph.state()["nodes"]}
    assert result["lean"]["status"] == "unsupported"
    assert result["lean"]["kernel_checked"] is False


def test_scoped_math_symbols_definitions_and_assumptions_are_linked(tmp_path):
    graph = ResearchGraph.create("Interpret a scoped equation", root=tmp_path,
                                 investigation_id="scoped-math")
    frame = graph.record("Frame", wording="Real-valued model", domain="real numbers")
    symbol = graph.record("MathematicalSymbol", name="x", notation="x",
                          sort="real", arity=0, identity="model.x")
    definition = graph.record("MathematicalDefinition", wording="x is the measured length",
                              status="proposed", provenance="researcher interpretation")
    assumption = graph.record("Assumption", wording="x is nonnegative",
                              formal_constraint="x >= 0")
    claim = graph.record("Claim", wording="The measured length is zero",
                         claim_type="inference", status="open")

    graph.link(symbol["id"], "scoped_by", frame["id"])
    graph.link(definition["id"], "scoped_by", frame["id"])
    graph.link(definition["id"], "defines", symbol["id"])
    graph.link(claim["id"], "uses_symbol", symbol["id"])
    graph.link(assumption["id"], "constrains", symbol["id"])
    graph.link(claim["id"], "assumes", assumption["id"])

    state = graph.state()
    assert graph.inspect(symbol["id"], transitive=True)["transitive"]
    assert {(edge["type"], edge["src"], edge["tgt"]) for edge in state["edges"]} >= {
        ("scoped_by", symbol["id"], frame["id"]),
        ("defines", definition["id"], symbol["id"]),
        ("uses_symbol", claim["id"], symbol["id"]),
        ("constrains", assumption["id"], symbol["id"]),
        ("assumes", claim["id"], assumption["id"]),
    }
    loaded = ResearchGraph.load("scoped-math", root=tmp_path)
    assert loaded.state()["nodes"] == state["nodes"]
    assert loaded.state()["edges"] == state["edges"]


def test_math_graph_rejects_mistyped_symbol_relationships(tmp_path):
    graph = ResearchGraph.create("Test symbol relationship typing", root=tmp_path,
                                 investigation_id="math-edge-types")
    claim = graph.record("Claim", wording="Claim")
    symbol = graph.record("MathematicalSymbol", name="x")
    with pytest.raises(ResearchError, match="incompatible"):
        graph.link(claim["id"], "defines", symbol["id"])
    with pytest.raises(ResearchError, match="incompatible"):
        graph.link(symbol["id"], "constrains", claim["id"])
