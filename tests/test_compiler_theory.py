"""Compiler-theory seed — names + validity arguments attached to the
families that the rule-inference layer discovered structurally.

After loading both seeds, an agent traversing from any installed
RewriteRule reaches:
  rule → member_of → RuleFamily ← instantiates ← OptimizationConcept

The concept carries the *why*: definition, validity argument, and a
category (denotational_equivalence vs algebraic_law) that links to
the underlying soundness principle.
"""
from __future__ import annotations

import pytest

from domains.llvm_pass_compiler import install_passes_seed
from domains.compiler_theory_seed import (
    install_compiler_theory_seed, load_compiler_theory_seed,
)


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_PASSES_SEED = f"{_REPO_ROOT}/seeds/llvm_passes.json"
_THEORY_SEED = f"{_REPO_ROOT}/seeds/compiler_theory.json"


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

def test_seed_loads_with_expected_concepts():
    m = load_compiler_theory_seed(_THEORY_SEED)
    assert m["id"] == "compiler_theory"
    assert "llvm_passes" in m["depends_on"]
    names = {c["name"] for c in m["concepts"]}
    assert names == {
        "constant_folding",
        "algebraic_identity_elimination",
        "self_idempotence",
        "self_annihilation",
        "dead_code_elimination",
        "strength_reduction",
        "common_subexpression_elimination",
        "algebraic_reassociation",
        "select_constant_condition",
        "select_equal_branches",
        "control_flow_constant_folding",
        "dead_block_elimination",
    }


def test_every_concept_has_validity_argument():
    m = load_compiler_theory_seed(_THEORY_SEED)
    for c in m["concepts"]:
        assert isinstance(c.get("validity_argument"), str)
        assert len(c["validity_argument"]) > 80, \
            f"{c['name']} has no real validity argument"


def test_categories_define_soundness_principles():
    m = load_compiler_theory_seed(_THEORY_SEED)
    cats = m.get("categories", {})
    assert {"denotational_equivalence", "algebraic_law",
            "extensional_equivalence", "cost_equivalence",
            "referential_transparency", "ub_preservation"} <= cats.keys()
    for name, cat in cats.items():
        assert cat.get("soundness_principle"), \
            f"category {name} has no soundness_principle"


# ---------------------------------------------------------------------------
# install: concepts → families
# ---------------------------------------------------------------------------

def test_install_creates_concept_nodes():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES_SEED)
    out = install_compiler_theory_seed(s, _THEORY_SEED)
    assert out["concepts_installed"] == 12
    assert out["categories_installed"] == 6
    concepts = s.nodes("OptimizationConcept")
    assert len(concepts) == 12


def test_every_concept_wires_to_a_family():
    """All seeded fingerprints exist in the discovered family set —
    the theory seed and the inference layer are mutually grounded."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES_SEED)
    out = install_compiler_theory_seed(s, _THEORY_SEED)
    assert out["concepts_wired"] == 12, \
        f"every concept should bind to a discovered family; got " \
        f"{out['concepts_wired']}"


def test_rule_traversal_reaches_named_concept():
    """The canonical query: from any constfold_* RewriteRule, walk
    `member_of` to its family, then walk back `instantiates` to the
    named OptimizationConcept. The agent's "why is this folding a
    constant?" question is answered by graph traversal."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES_SEED)
    install_compiler_theory_seed(s, _THEORY_SEED)

    constfold_rule = None
    for r in s.nodes("RewriteRule"):
        if s.node(r)["attrs"].get("name") == "constfold_and":
            constfold_rule = r
            break
    assert constfold_rule is not None

    fams = s.neighbours(constfold_rule, "member_of")
    assert len(fams) == 1
    family = fams[0]

    concepts = s.in_neighbours(family, "instantiates")
    assert len(concepts) == 1, \
        f"family should have exactly one named concept; got {concepts}"
    concept_attrs = s.node(concepts[0])["attrs"]
    assert concept_attrs["name"] == "constant_folding"
    assert "validity_argument" in concept_attrs


def test_concept_is_categorised():
    """Each concept has an `in_category` edge to a Category node
    carrying the underlying soundness principle."""
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES_SEED)
    install_compiler_theory_seed(s, _THEORY_SEED)

    for c in s.nodes("OptimizationConcept"):
        cats = s.neighbours(c, "in_category")
        assert len(cats) == 1, \
            f"concept {s.node(c)['attrs']['name']} should be in one category"
        cat_attrs = s.node(cats[0])["attrs"]
        assert cat_attrs.get("soundness_principle"), \
            f"category {cat_attrs.get('name')} has no soundness_principle"


def test_constant_folding_is_denotational_other_three_are_algebraic():
    s = _native_substrate_or_skip()
    install_passes_seed(s, _PASSES_SEED)
    install_compiler_theory_seed(s, _THEORY_SEED)

    name_to_cat = {}
    for c in s.nodes("OptimizationConcept"):
        attrs = s.node(c)["attrs"]
        cats = s.neighbours(c, "in_category")
        cat_name = s.node(cats[0])["attrs"]["name"]
        name_to_cat[attrs["name"]] = cat_name

    assert name_to_cat == {
        "constant_folding": "denotational_equivalence",
        "algebraic_identity_elimination": "algebraic_law",
        "self_idempotence": "algebraic_law",
        "self_annihilation": "algebraic_law",
        "dead_code_elimination": "extensional_equivalence",
        "strength_reduction": "cost_equivalence",
        "common_subexpression_elimination": "referential_transparency",
        "algebraic_reassociation": "algebraic_law",
        "select_constant_condition": "denotational_equivalence",
        "select_equal_branches": "algebraic_law",
        "control_flow_constant_folding": "denotational_equivalence",
        "dead_block_elimination": "extensional_equivalence",
    }
