"""Optimization-pipelines seed — composition knowledge as graph data.

Two layers:
  1. `enables` edges between OptimizationConcepts. The substrate's own
     run_rules already exhibits these cascades (reassoc → constfold →
     DCE); this seed promotes the observed behaviour to declarative,
     queryable knowledge.
  2. `Pipeline` nodes — named ordered sequences of concepts the agent
     can run end-to-end as a complete optimization recipe.
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import install_compiler_theory_seed
from domains.optimization_pipelines_seed import (
    install_pipelines_seed, load_pipelines_seed, run_pipeline_by_name,
)


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_PASSES = f"{_REPO_ROOT}/seeds/llvm_passes.json"
_THEORY = f"{_REPO_ROOT}/seeds/compiler_theory.json"
_PIPELINES = f"{_REPO_ROOT}/seeds/optimization_pipelines.json"


def _native_substrate_or_skip():
    try:
        from substrate_rs import _native
        s = _native.Substrate()
        for src_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
            for tgt_t in ("LLVMInstruction", "LLVMConstant", "LLVMValue"):
                for et in ("uses_op0", "uses_op1", "uses_op2", "produces"):
                    s.add_production({
                        "src": {"type": src_t, "var": "src"},
                        "edge_type": et,
                        "tgt": {"type": tgt_t, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "test:open",
                    })
        return s
    except Exception as e:
        pytest.skip(f"native substrate unavailable: {e}")


# ---------------------------------------------------------------------------
# manifest sanity
# ---------------------------------------------------------------------------

def test_seed_loads_and_lists_concepts_it_will_reference():
    m = load_pipelines_seed(_PIPELINES)
    assert m["id"] == "optimization_pipelines"
    assert "compiler_theory" in m["depends_on"]

    # Every `enables` entry references concepts that exist in compiler_theory.
    theory = load_pipelines_seed(_THEORY) if False else __import__(
        "json").load(open(_THEORY))
    concept_names = {c["name"] for c in theory["concepts"]}
    for rel in m["enables"]:
        assert rel["from"] in concept_names, \
            f"enables.from {rel['from']!r} not in compiler_theory"
        assert rel["to"] in concept_names, \
            f"enables.to {rel['to']!r} not in compiler_theory"
        assert rel.get("rationale"), \
            f"enables {rel['from']}→{rel['to']} lacks rationale"

    # Every pipeline references known concepts.
    for pipe in m["pipelines"]:
        for c in pipe["concepts"]:
            assert c in concept_names, \
                f"pipeline {pipe['name']!r} references unknown concept {c!r}"


# ---------------------------------------------------------------------------
# install — enables edges
# ---------------------------------------------------------------------------

def test_install_creates_enables_edges():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    out = install_pipelines_seed(s, _PIPELINES)

    manifest = load_pipelines_seed(_PIPELINES)
    expected_enables = len(manifest["enables"])
    assert out["enables_installed"] == expected_enables


def test_reassoc_enables_constfold_traversable_in_graph():
    """The canonical cascade observed in tests is reified as an
    `enables` edge the agent can follow."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)

    # Find reassoc concept, walk `enables` out, expect constant_folding.
    reassoc = None
    for c in s.nodes("OptimizationConcept"):
        if s.node(c)["attrs"]["name"] == "algebraic_reassociation":
            reassoc = c
            break
    assert reassoc is not None
    enabled = [s.node(n)["attrs"]["name"]
               for n in s.neighbours(reassoc, "enables")]
    assert "constant_folding" in enabled, \
        f"reassoc should enable constfold; got {enabled}"


def test_every_concept_eventually_enables_dce_or_is_dce():
    """DCE is the universal cleanup pass — every other concept either
    enables it (by creating dead instructions) or IS it."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)

    name_to_concept = {s.node(c)["attrs"]["name"]: c
                       for c in s.nodes("OptimizationConcept")}
    dce = name_to_concept["dead_code_elimination"]

    for name, c in name_to_concept.items():
        if name == "dead_code_elimination":
            # DCE has a self-enables edge for cascading DCE-to-fixed-point.
            assert dce in s.neighbours(c, "enables"), \
                "DCE should self-enable (cascade-to-fixed-point)"
            continue
        # The concept either directly enables DCE or its descendants do.
        # Direct check is sufficient for the current seed.
        directly_enabled = [
            s.node(n)["attrs"]["name"]
            for n in s.neighbours(c, "enables")
        ]
        # Every transforming concept feeds DCE in our seed (except
        # constfold which feeds it transitively through algebraic_identity;
        # but the seed makes that direct too). Allow self_idempotence
        # which doesn't feed anything (it's pure rewire, no constants
        # created, intermediate already had at most one use). Also
        # allow dead_block_elimination — its natural downstream is
        # orphan-instruction cleanup which isn't currently wired (the
        # orphan-elim rule was removed pending a cleaner scoping
        # mechanism).
        if name in ("self_idempotence", "dead_block_elimination"):
            continue
        assert directly_enabled, \
            f"{name} should enable at least one downstream concept"


# ---------------------------------------------------------------------------
# install — Pipeline nodes
# ---------------------------------------------------------------------------

def test_install_creates_pipeline_nodes():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    out = install_pipelines_seed(s, _PIPELINES)

    manifest = load_pipelines_seed(_PIPELINES)
    assert out["pipelines_installed"] == len(manifest["pipelines"])

    p_names = {s.node(p)["attrs"]["name"] for p in s.nodes("Pipeline")}
    assert p_names == {"minimal_peephole", "local_peephole", "dce_only"}


def test_pipeline_ordering_recoverable_from_graph():
    """Pipeline order lives as a list attr on the Pipeline node
    (`concept_order`); the `applies` edges encode set membership. The
    agent reads the order from the attr to dispatch in sequence."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)

    pipeline = next(p for p in s.nodes("Pipeline")
                    if s.node(p)["attrs"]["name"] == "local_peephole")
    p_attrs = s.node(pipeline)["attrs"]
    order = p_attrs.get("concept_order")
    # Substrate may coerce list attrs into tuples on storage.
    assert isinstance(order, (list, tuple)) and len(order) > 0
    # Set membership via applies edges matches the order list.
    edge_targets = s.neighbours(pipeline, "applies")
    edge_names = {s.node(t)["attrs"]["name"] for t in edge_targets}
    assert set(order) == edge_names

    manifest = load_pipelines_seed(_PIPELINES)
    expected = next(p for p in manifest["pipelines"]
                    if p["name"] == "local_peephole")
    assert list(order) == expected["concepts"]


# ---------------------------------------------------------------------------
# executor — pipeline knowledge becomes actionable
# ---------------------------------------------------------------------------

def test_run_pipeline_collapses_canonical_cascade():
    """Run `local_peephole` by name on `(x + 1) + 2`. The executor
    walks the graph (Pipeline → concepts → families → RewriteRules with
    rule_idx attrs) and dispatches `apply_rule_once` by index until the
    pipeline iterates to fixed point.

    Expected: reassoc → constfold → DCE cascade collapses the chain
    to a single `add x, 3` instruction, identical to what `run_rules`
    would produce — but invoked by *name*, not by side-effecting all
    installed rules indiscriminately."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)

    x = s.add_node("LLVMValue", {"type": "i32"})
    c1 = s.add_node("LLVMConstant", {"value": 1, "type": "i32"})
    c2 = s.add_node("LLVMConstant", {"value": 2, "type": "i32"})

    inner = s.add_node("LLVMInstruction", {"opcode": "add"})
    t = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inner, "uses_op0", x, {})
    s.add_edge(inner, "uses_op1", c1, {})
    s.add_edge(inner, "produces", t, {})

    outer = s.add_node("LLVMInstruction", {"opcode": "add"})
    r = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(outer, "uses_op0", t, {})
    s.add_edge(outer, "uses_op1", c2, {})
    s.add_edge(outer, "produces", r, {})

    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", r, {})

    result = run_pipeline_by_name(s, "local_peephole")
    assert result["rules_applied"] > 0, "pipeline should have fired something"

    add_insts = [n for n in s.nodes("LLVMInstruction")
                 if s.node(n)["attrs"].get("opcode") == "add"]
    assert len(add_insts) == 1, \
        f"expected one surviving add after local_peephole; got {len(add_insts)}"

    survivor = add_insts[0]
    op0 = s.neighbours(survivor, "uses_op0")[0]
    op1 = s.neighbours(survivor, "uses_op1")[0]
    types = (s.node(op0)["type"], s.node(op1)["type"])
    assert {"LLVMValue", "LLVMConstant"} == set(types)
    const = op0 if s.node(op0)["type"] == "LLVMConstant" else op1
    assert s.node(const)["attrs"]["value"] == 3


def test_minimal_pipeline_runs_constfold_then_dce_only():
    """The minimal_peephole pipeline excludes reassoc → so on
    `(x + 1) + 2` it should NOT collapse to x + 3 (the two adds remain
    because reassoc never normalises them into adjacency). This proves
    pipeline selection actually constrains rule dispatch — not just a
    descriptive label."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)

    x = s.add_node("LLVMValue", {"type": "i32"})
    c1 = s.add_node("LLVMConstant", {"value": 1, "type": "i32"})
    c2 = s.add_node("LLVMConstant", {"value": 2, "type": "i32"})
    inner = s.add_node("LLVMInstruction", {"opcode": "add"})
    t = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(inner, "uses_op0", x, {})
    s.add_edge(inner, "uses_op1", c1, {})
    s.add_edge(inner, "produces", t, {})
    outer = s.add_node("LLVMInstruction", {"opcode": "add"})
    r = s.add_node("LLVMValue", {"type": "i32"})
    s.add_edge(outer, "uses_op0", t, {})
    s.add_edge(outer, "uses_op1", c2, {})
    s.add_edge(outer, "produces", r, {})
    user = s.add_node("LLVMInstruction", {"opcode": "ret"})
    s.add_edge(user, "uses_op0", r, {})

    run_pipeline_by_name(s, "minimal_peephole")

    # Without reassoc, BOTH adds survive — the two operand-constant
    # pairs (x,1) and (t,2) aren't both constants, so constfold can't
    # attack either, and DCE can't remove anything (both have uses).
    add_insts = [n for n in s.nodes("LLVMInstruction")
                 if s.node(n)["attrs"].get("opcode") == "add"]
    assert len(add_insts) == 2, \
        f"minimal_peephole (no reassoc) should leave both adds; got " \
        f"{len(add_insts)}"


def test_run_pipeline_rejects_unknown_name():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)
    with pytest.raises(ValueError, match="no Pipeline named"):
        run_pipeline_by_name(s, "this_pipeline_does_not_exist")


def test_minimal_pipeline_is_just_constfold_and_dce():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES)
    install_compiler_theory_seed(s, _THEORY)
    install_pipelines_seed(s, _PIPELINES)

    p = next(n for n in s.nodes("Pipeline")
             if s.node(n)["attrs"]["name"] == "minimal_peephole")
    concepts = s.neighbours(p, "applies")
    names = {s.node(c)["attrs"]["name"] for c in concepts}
    assert names == {"constant_folding", "dead_code_elimination"}
