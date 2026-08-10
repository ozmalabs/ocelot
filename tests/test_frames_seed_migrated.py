"""Frame / Microtheory register layer — the SEED, migrated to the seed-booted
WorldAdapter (no CuriousAgent).

Slice 1 of the Frame-layer migration: the graph-data FOUNDATION. The Microtheory
tree (3 roots + genlMt sub-Mts), the agent's operates_in scope, and the inquiry
Frame library are a graph-data MANIFEST (seeds/frames.json) the Rust seed loader
installs at boot — the adapter does NOT construct them. These tests assert the
loaded structure via pure graph queries (microtheory/frame/_agent_scope_mts).

Covers the structural subset of tests/test_frames.py (the recognition decision +
answer_within routing + teach-loop are subsequent slices). Vocabulary: FrameNet
(Frame/evokes/frame-elements) + CYC (Microtheory/genlMt scope).
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

_FRAMES = CORE_SEEDS + ("frames",)


def _agent():
    return WorldAdapter(seeds=_FRAMES)


def _genl_parents(wa, mt_id):
    return set(wa.inner.neighbours(mt_id, "genlMt"))


def _out(wa, nid, edge):
    return set(wa.inner.neighbours(nid, edge))


# --- the Microtheory tree ------------------------------------------------

def test_seeded_microtheories_live_in_the_graph():
    a = _agent()
    for root in ("mathematics", "computer_science", "computer_architecture"):
        rid = a.microtheory(root)
        assert rid is not None, f"missing root Mt: {root}"
        assert a.s.node(rid)["type"] == "Microtheory"
    arith = a.microtheory("elementary_arithmetic")
    assert a.microtheory("mathematics") in _genl_parents(a, arith)


def test_cs_and_architecture_sub_microtheories_inherit_correctly():
    a = _agent()
    cs, arch = a.microtheory("computer_science"), a.microtheory("computer_architecture")
    for sub in ("data_structures", "algorithms", "complexity_theory",
                "systems_programming", "programming_languages", "compilers",
                "concurrency"):
        sid = a.microtheory(sub)
        assert sid is not None, f"missing CS sub-Mt: {sub}"
        assert cs in _genl_parents(a, sid), f"{sub} should genlMt computer_science"
    for sub in ("instruction_set_architecture", "microarchitecture",
                "memory_hierarchy", "vector_processing", "concurrency_primitives",
                "performance_analysis"):
        sid = a.microtheory(sub)
        assert sid is not None, f"missing arch sub-Mt: {sub}"
        assert arch in _genl_parents(a, sid), f"{sub} should genlMt computer_architecture"


def test_agent_operates_in_all_three_root_microtheories():
    a = _agent()
    targets = _out(a, a.agent, "operates_in")
    for root in ("mathematics", "computer_science", "computer_architecture"):
        assert a.microtheory(root) in targets, f"agent should operates_in {root}"


def test_agent_operates_in_root_mathematics_by_default():
    a = _agent()
    assert a.microtheory("mathematics") in _out(a, a.agent, "operates_in")


def test_cs_and_architecture_scopes_have_no_frames_at_seed():
    a = _agent()
    for sub in ("data_structures", "algorithms", "microarchitecture",
                "memory_hierarchy"):
        sid = a.microtheory(sub)
        held = [f for f in a.frames() if sid in _out(a, f, "holds_in")]
        assert held == [], f"{sub} should have no frames at seed (got {len(held)})"


# --- the Frame library ---------------------------------------------------

def test_each_capability_concept_holds_in_a_microtheory():
    a = _agent()
    for concept_name, mt_name in [
        ("largest_prime_factor", "elementary_arithmetic"),
        ("det", "linear_algebra"),
        ("order", "finitely_presented_groups"),
        ("expectation", "continuous_probability"),
        ("next_term", "sequence_inference"),
        ("solution", "equation_solving"),
    ]:
        c_id = a._concept_by_name(concept_name)
        assert c_id is not None, f"{concept_name} concept missing"
        assert a.microtheory(mt_name) in _out(a, c_id, "holds_in"), (
            f"{concept_name} should hold_in {mt_name}")


def test_seeded_frames_live_in_the_graph_and_route_to_capabilities():
    a = _agent()
    f = a.frame("largest_prime_factor_inquiry")
    assert f is not None
    assert a.s.node(f)["type"] == "Frame"
    attrs = a.s.node(f)["attrs"]
    assert "largest prime divisor" in attrs["evoked_by"]
    assert "largest prime factor" in attrs["evoked_by"]
    assert a._concept_by_name("largest_prime_factor") in _out(a, f, "realised_by")
    assert a.microtheory("elementary_arithmetic") in _out(a, f, "holds_in")


def test_frame_library_covers_every_seeded_capability():
    a = _agent()
    expected = {
        "largest_prime_factor_inquiry", "prime_factors_inquiry",
        "primality_inquiry", "evenness_inquiry", "oddness_inquiry",
        "gcd_inquiry", "lcm_inquiry", "divides_inquiry",
        "determinant_inquiry", "rank_inquiry", "trace_inquiry",
        "invertibility_inquiry", "order_inquiry", "index_inquiry",
        "expectation_inquiry", "variance_inquiry", "next_term_inquiry",
        "wolfram_code_inquiry", "solution_inquiry",
    }
    present = {a.s.node(f)["attrs"].get("name") for f in a.frames()}
    assert not (expected - present), f"missing seeded frames: {expected - present}"


def test_predicate_frame_has_predicate_binding_attr():
    a = _agent()
    f = a.frame("primality_inquiry")
    assert f is not None
    assert a.s.node(f)["attrs"].get("binding_pattern") == "predicate_of_subject"
    g = a.frame("determinant_inquiry")
    assert a.s.node(g)["attrs"].get("binding_pattern") == "function_of_subject"


def test_introspection_frames_live_in_performance_analysis_mt():
    a = _agent()
    perf = a.microtheory("performance_analysis")
    for f_name in ("op_mean_cost_inquiry", "op_count_inquiry", "op_total_cost_inquiry"):
        fid = a.frame(f_name)
        assert fid is not None, f"missing {f_name}"
        assert perf in _out(a, fid, "holds_in"), f"{f_name} should hold_in performance_analysis"


# --- scope inheritance ---------------------------------------------------

def test_genlMt_inheritance_brings_specialised_mts_into_scope():
    a = _agent()
    scope = a._agent_scope_mts()
    assert a.microtheory("mathematics") in scope
    assert a.microtheory("elementary_arithmetic") in scope
    assert a.microtheory("linear_algebra") in scope
