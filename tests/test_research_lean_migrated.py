"""Lean export translates recorded Boolean syntax and preserves its graph links."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.ocelot_research import ResearchGraph
from scripts.ocelot_research_lean import LeanExportError, export_lean
from substrate.dsl import Eq, Gte, Gt, Lit, Plus, Pow, Var


_LEAN = shutil.which("lean") or (
    str(Path(__file__).resolve().parents[1] / ".venv" / "bin" / "lean")
    if (Path(__file__).resolve().parents[1] / ".venv" / "bin" / "lean").is_file()
    else None
)


def _graph(tmp_path):
    graph = ResearchGraph.create("A bounded Boolean question", root=tmp_path,
                                 mode="deductive", investigation_id="lean-demo")
    base = graph.record("Assumption", wording="An explicitly recorded Boolean premise",
                        term={"type": "Lit", "value": True}, bindings={})
    claim = graph.record("Claim", wording="A researcher-authored conditional",
                         scope="this syntax only", claim_type="hypothesis", author="tester",
                         status="open", term={"type": "And", "items": [
                             {"type": "EvalSubgraph", "node": {"type": "Var", "name": "premise"}},
                             {"type": "Not", "arg": {"type": "Lit", "value": False}},
                         ]}, bindings={"premise": base["id"]})
    graph.link(claim["id"], "derived_from", base["id"], rationale="explicit Boolean dependency")
    return graph, base, claim


def test_exports_boolean_defs_with_traceable_ids_bindings_and_no_proofs(tmp_path):
    graph, premise, claim = _graph(tmp_path)
    lean = export_lean(graph, claim["id"])

    assert "def researchTerm_0_assumption_0001 : Bool := true" in lean
    assert "def researchTerm_1_claim_0001 : Bool := ((researchTerm_0_assumption_0001) && (! false))" in lean
    assert 'def researchTerm_1_claim_0001_researchNodeId : String := "claim-0001"' in lean
    assert '[("premise", "assumption-0001")]' in lean
    assert premise["id"] in lean and claim["id"] in lean
    assert "truth are not assessed" in lean
    assert "theorem " not in lean and "axiom " not in lean and "sorry" not in lean


def test_export_all_terms_and_rejects_unsupported_constructor(tmp_path):
    graph, _, claim = _graph(tmp_path)
    all_lean = export_lean(graph)
    assert "researchTerm_0_assumption_0001" in all_lean
    assert "claim-0001" in all_lean

    state = graph.state()
    next(n for n in state["nodes"] if n["id"] == claim["id"])["term"] = {
        "type": "Attr", "node": {"type": "Var", "name": "premise"}, "key": "held"
    }
    with pytest.raises(LeanExportError, match="unsupported term constructor"):
        export_lean(state, claim["id"])


def test_missing_or_inconsistent_binding_fails_closed(tmp_path):
    graph, _, claim = _graph(tmp_path)
    state = graph.state()
    state["edges"] = []
    with pytest.raises(LeanExportError, match="lacks derived_from"):
        export_lean(state, claim["id"])

    state = graph.state()
    target = next(n for n in state["nodes"] if n["id"] == claim["id"])
    target["bindings"] = {}
    with pytest.raises(LeanExportError, match="no graph binding"):
        export_lean(state, claim["id"])


def test_dependency_cycle_is_rejected(tmp_path):
    graph, premise, claim = _graph(tmp_path)
    state = graph.state()
    base = next(n for n in state["nodes"] if n["id"] == premise["id"])
    base["term"] = {"type": "EvalSubgraph", "node": {"type": "Var", "name": "claim"}}
    base["bindings"] = {"claim": claim["id"]}
    state["edges"].append({"type": "derived_from", "src": premise["id"], "tgt": claim["id"]})
    with pytest.raises(LeanExportError, match="dependency cycle"):
        export_lean(state, claim["id"])


def test_external_boolean_var_becomes_a_typed_lean_parameter(tmp_path):
    graph = ResearchGraph.create("Input parameter", root=tmp_path,
                                 mode="deductive", investigation_id="lean-input")
    claim = graph.record("Claim", wording="p and not p", term={"type": "And", "items": [
        {"type": "Var", "name": "p"},
        {"type": "Not", "arg": {"type": "Var", "name": "p"}},
    ]}, bindings={})
    lean = export_lean(graph, claim["id"])
    assert "def researchTerm_0_claim_0001 (input_p : Bool) : Bool := (input_p && (! input_p))" in lean


def test_three_level_bound_chain_expands_dependency_first(tmp_path):
    graph = ResearchGraph.create("Three-level terms", root=tmp_path,
                                 mode="deductive", investigation_id="lean-chain")
    leaf = graph.record("Assumption", wording="leaf", term={"type": "Var", "name": "p"},
                        bindings={})
    middle = graph.record("Claim", wording="middle", term={"type": "Not", "arg": {
        "type": "EvalSubgraph", "node": {"type": "Var", "name": "leaf"}}},
                          bindings={"leaf": leaf["id"]})
    graph.link(middle["id"], "derived_from", leaf["id"])
    root = graph.record("Claim", wording="root", term={"type": "EvalSubgraph",
        "node": {"type": "Var", "name": "middle"}}, bindings={"middle": middle["id"]})
    graph.link(root["id"], "derived_from", middle["id"])

    lean = export_lean(graph, root["id"])
    assert lean.index('research_node_id: "assumption-0001"') < lean.index('research_node_id: "claim-0001"')
    assert lean.index('research_node_id: "claim-0001"') < lean.index('research_node_id: "claim-0002"')
    assert "def researchTerm_0_assumption_0001 (input_p : Bool) : Bool := input_p" in lean
    assert "(! (researchTerm_0_assumption_0001 input_p))" in lean
    assert "(researchTerm_1_claim_0001 input_p)" in lean


def test_external_inputs_that_sanitize_to_same_lean_name_are_rejected(tmp_path):
    graph = ResearchGraph.create("Sanitized name collision", root=tmp_path,
                                 mode="deductive", investigation_id="lean-collision")
    claim = graph.record("Claim", wording="collision", term={"type": "And", "items": [
        {"type": "Var", "name": "left-right"},
        {"type": "Var", "name": "left_right"},
    ]}, bindings={})
    with pytest.raises(LeanExportError, match="collide after Lean identifier sanitization"):
        export_lean(graph, claim["id"])


def test_external_alias_cannot_collide_with_binding_alias_in_chain(tmp_path):
    graph, premise, claim = _graph(tmp_path)
    state = graph.state()
    target = next(n for n in state["nodes"] if n["id"] == claim["id"])
    target["term"] = {"type": "And", "items": [
        {"type": "EvalSubgraph", "node": {"type": "Var", "name": "premise"}},
        {"type": "Var", "name": "premise"},
    ]}
    with pytest.raises(LeanExportError, match="is a NodeID"):
        export_lean(state, claim["id"])

    # A sibling dependency may use a bare external Var with a spelling that
    # is a graph binding in another node in the same chain.
    state = graph.state()
    leaf = next(n for n in state["nodes"] if n["id"] == premise["id"])
    leaf["term"] = {"type": "Eq", "a": {"type": "Var", "name": "premise"},
                    "b": {"type": "Lit", "value": 1}}
    target = next(n for n in state["nodes"] if n["id"] == claim["id"])
    target["term"] = {"type": "EvalSubgraph", "node": {"type": "Var", "name": "premise"}}
    with pytest.raises(LeanExportError, match="collide with graph binding aliases"):
        export_lean(state, claim["id"])


def test_eq_uses_native_term_json_fields_and_bool_equality(tmp_path):
    graph = ResearchGraph.create("Boolean equality", root=tmp_path,
                                 mode="deductive", investigation_id="lean-eq")
    claim = graph.record("Claim", wording="true equals true", term={"type": "Eq",
        "a": {"type": "Lit", "value": True}, "b": {"type": "Lit", "value": True}},
                        bindings={})
    lean = export_lean(graph, claim["id"])
    assert "def researchTerm_0_claim_0001 : Bool := (true == true)" in lean
    # This is the native substrate's Eq JSON shape and evaluation meaning.
    native_eq = Eq(Lit(True), Lit(True))
    assert native_eq.evaluate({}, None) is True


def test_integer_terms_use_i64_wrapping_and_typed_range_assumptions(tmp_path):
    graph = ResearchGraph.create("Integer arithmetic", root=tmp_path,
                                 mode="deductive", investigation_id="lean-int")
    claim = graph.record("Claim", wording="bounded integer comparison", term={
        "type": "Gte",
        "a": {"type": "Plus", "items": [
            {"type": "Var", "name": "count"}, {"type": "Lit", "value": 4},
        ]},
        "b": {"type": "Lit", "value": 0},
    }, bindings={})
    lean = export_lean(graph, claim["id"])
    assert "def ocelotWrapI64 (value : Int) : Int :=" in lean
    assert "def researchTerm_0_claim_0001 (input_count : Int) (input_count_range :" in lean
    assert "(decide ((ocelotWrapI64 ((ocelotWrapI64 (0 + input_count)) + 4)) ≥ 0))" in lean
    assert "may be broader than the research helper's accepted input domain" in lean
    assert "Establish overflow-free preconditions" in lean
    native_term = Gte(Plus([Var("count"), Lit(4)]), Lit(0))
    assert native_term.evaluate({"count": -3}, None) is True


def test_integer_literals_outside_native_range_and_division_are_rejected(tmp_path):
    graph = ResearchGraph.create("Unsupported integer semantics", root=tmp_path,
                                 mode="deductive", investigation_id="lean-int-reject")
    claim = graph.record("Claim", wording="too large", term={"type": "Lit", "value": 1 << 63},
                         bindings={})
    with pytest.raises(LeanExportError, match="outside the native i64 range"):
        export_lean(graph, claim["id"])

    state = graph.state()
    state["nodes"][-1]["term"] = {"type": "Div", "a": {"type": "Lit", "value": 2},
                                   "b": {"type": "Lit", "value": 1}}
    with pytest.raises(LeanExportError, match="unsupported term constructor 'Div'"):
        export_lean(state, claim["id"])

    state["nodes"][-1]["term"] = {"type": "Lit", "value": 0.125}
    with pytest.raises(LeanExportError, match="only Boolean and signed i64 Lit"):
        export_lean(state, claim["id"])
    state["nodes"][-1]["term"] = {"type": "Lit", "value": {"__rational__": [1, 3]}}
    with pytest.raises(LeanExportError, match="only Boolean and signed i64 Lit"):
        export_lean(state, claim["id"])


@pytest.mark.parametrize("exponent", [-1, 64])
def test_integer_pow_rejects_exponents_that_use_native_float_fallback(tmp_path, exponent):
    graph = ResearchGraph.create("Pow fallback", root=tmp_path,
                                 mode="deductive", investigation_id=f"lean-pow-{exponent}")
    claim = graph.record("Claim", wording="pow fallback", term={"type": "Pow",
        "a": {"type": "Lit", "value": 2}, "b": {"type": "Lit", "value": exponent}}, bindings={})
    with pytest.raises(LeanExportError, match="native integer Pow requires exponent"):
        export_lean(graph, claim["id"])


def test_integer_pow_uses_i64_wrapping_for_supported_native_case(tmp_path):
    graph = ResearchGraph.create("Integer Pow", root=tmp_path,
                                 mode="deductive", investigation_id="lean-pow-ok")
    claim = graph.record("Claim", wording="two cubed is eight", term={"type": "Eq",
        "a": {"type": "Pow", "a": {"type": "Lit", "value": 2},
              "b": {"type": "Lit", "value": 3}},
        "b": {"type": "Lit", "value": 8}}, bindings={})
    lean = export_lean(graph, claim["id"])
    assert "(ocelotWrapI64 (2 ^ 3)) == 8" in lean
    assert Pow(Lit(2), Lit(3)).evaluate({}, None) == 8


def test_finite_quantifier_is_rejected_as_unsupported_term(tmp_path):
    graph = ResearchGraph.create("Unsupported control flow", root=tmp_path,
                                 mode="deductive", investigation_id="lean-control")
    claim = graph.record("Claim", wording="unsupported quantifier", term={
        "type": "Exists", "var_name": "x", "source": {"type": "Lit", "value": True}}, bindings={})
    with pytest.raises(LeanExportError, match="unsupported term constructor"):
        export_lean(graph, claim["id"])


def test_guarded_branch_requires_boolean_condition_and_same_branch_type(tmp_path):
    graph = ResearchGraph.create("Guard typing", root=tmp_path,
                                 mode="deductive", investigation_id="lean-guard")
    claim = graph.record("Claim", wording="mismatched branches", term={"type": "IfThenElse",
        "cond": {"type": "Lit", "value": True}, "then": {"type": "Lit", "value": 1},
        "other": {"type": "Lit", "value": False}}, bindings={})
    with pytest.raises(LeanExportError, match="expected Int term, got Bool"):
        export_lean(graph, claim["id"])

    state = graph.state()
    state["nodes"][-1]["term"]["cond"] = {"type": "Lit", "value": 1}
    state["nodes"][-1]["term"]["other"] = {"type": "Lit", "value": 0}
    with pytest.raises(LeanExportError, match="expected Bool term, got Int"):
        export_lean(state, claim["id"])


def test_guarded_integer_branch_translates_to_typed_lean_if(tmp_path):
    graph = ResearchGraph.create("Guarded integer", root=tmp_path,
                                 mode="deductive", investigation_id="lean-guard-ok")
    claim = graph.record("Claim", wording="select an integer", term={"type": "IfThenElse",
        "cond": {"type": "Lit", "value": True}, "then": {"type": "Lit", "value": 3},
        "other": {"type": "Lit", "value": 2}}, bindings={})
    lean = export_lean(graph, claim["id"])
    assert "def researchTerm_0_claim_0001 : Int := (if true then 3 else 2)" in lean


@pytest.mark.skipif(_LEAN is None, reason="Lean compiler is not installed")
@pytest.mark.parametrize("term", [
    {"type": "And", "items": [{"type": "Lit", "value": True},
                                {"type": "Not", "arg": {"type": "Lit", "value": False}}]},
    {"type": "Gte", "a": {"type": "Plus", "items": [{"type": "Lit", "value": 2},
                                                            {"type": "Lit", "value": 3}]},
     "b": {"type": "Lit", "value": 1}},
    {"type": "Gte", "a": {"type": "Pow", "a": {"type": "Lit", "value": 2},
                             "b": {"type": "Lit", "value": 3}},
     "b": {"type": "Lit", "value": 8}},
    {"type": "Eq", "a": {"type": "Pow", "a": {"type": "Lit", "value": 2},
                            "b": {"type": "Lit", "value": 63}},
     "b": {"type": "Lit", "value": -(1 << 63)}},
    {"type": "Gte", "a": {"type": "IfThenElse", "cond": {"type": "Lit", "value": True},
                             "then": {"type": "Lit", "value": 3},
                             "other": {"type": "Lit", "value": 2}},
     "b": {"type": "Lit", "value": 3}},
    {"type": "Gte", "a": {"type": "Plus", "items": [
         {"type": "Var", "name": "count"}, {"type": "Lit", "value": 4}]},
     "b": {"type": "Lit", "value": 0}},
])
def test_generated_lean_compiles_when_lean_is_available(tmp_path, term):
    graph = ResearchGraph.create("Lean compile smoke", root=tmp_path,
                                 mode="deductive", investigation_id="lean-compile")
    claim = graph.record("Claim", wording="compile candidate", term=term, bindings={})
    source = tmp_path / "ResearchExport.lean"
    output = export_lean(graph, claim["id"])
    if "(input_" not in output:
        output += "\nexample : researchTerm_0_claim_0001 = true := by decide\n"
    source.write_text(output, encoding="utf-8")
    result = subprocess.run([_LEAN, str(source)], capture_output=True,
                            text=True, check=False, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_numeric_dependency_calls_pass_input_and_range_evidence(tmp_path):
    graph = ResearchGraph.create("Numeric dependency", root=tmp_path,
                                 mode="deductive", investigation_id="lean-int-chain")
    leaf = graph.record("Claim", wording="input plus one", bindings={}, term={
        "type": "Plus", "items": [{"type": "Var", "name": "n"},
                                    {"type": "Lit", "value": 1}],
    })
    root = graph.record("Claim", wording="positive", bindings={"value": leaf["id"]}, term={
        "type": "Gt", "a": {"type": "EvalSubgraph", "node": {"type": "Var", "name": "value"}},
        "b": {"type": "Lit", "value": 0},
    })
    graph.link(root["id"], "derived_from", leaf["id"])
    lean = export_lean(graph, root["id"])
    assert "def researchTerm_0_claim_0001 (input_n : Int) (input_n_range :" in lean
    assert "(researchTerm_0_claim_0001 input_n input_n_range)" in lean
    assert "def researchTerm_1_claim_0002 (input_n : Int) (input_n_range :" in lean
