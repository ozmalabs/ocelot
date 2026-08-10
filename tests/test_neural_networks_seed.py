"""neural_networks seed — verifying the cortex's NN-authoring vocabulary.

The seed is graph data. These tests verify the loader installs the
vocabulary in the right shape and that the existing
`pick_design_pattern` selector ranks NN patterns correctly without any
NN-specific Python logic.
"""
from __future__ import annotations

import pytest
from substrate_rs import _native
from substrate.boot_all import load_one_seed


_NODE_TYPES = (
    "Microtheory", "Concept", "DesignPattern", "DesignExclusion",
    "CodeTarget", "ProgrammingLanguage", "LanguageExclusion",
    "LanguageScoringConfig", "CodeWritingCortex", "CodeAuthoringRoot",
    "Reflex", "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "owns_microtheory", "owns_root",
    "has_reflex", "current_target", "has_draft", "validated_by",
    "installed_as", "authored_in", "uses_pattern", "subClassOf",
    "in_category",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


def _seed_compiler_theory_and_code_authoring(substrate):
    """Both parent Mts the neural_networks Mt declares as parents.
    Bare nodes are fine — we only need the names so the genlMt lookup
    finds them.
    """
    substrate.add_node("Microtheory", {"name": "compiler_theory"})
    substrate.add_node("Microtheory", {"name": "code_authoring"})


# ---------------------------------------------------------------------------
# loader shape
# ---------------------------------------------------------------------------

def test_seed_installs_microtheory_with_genlMt_to_both_parents():
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)

    mt = load_one_seed(s, "neural_networks")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "neural_networks"

    parents = {s.node(p)["attrs"]["name"]
               for p in s.neighbours(mt, "genlMt")}
    assert "compiler_theory" in parents
    assert "code_authoring" in parents


def test_seed_installs_at_least_fifteen_concepts_each_with_has_concept():
    """Every NN Concept must be reachable from the Mt via `has_concept`
    so the architecture cortex doesn't surface them as orphaned."""
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)

    mt = load_one_seed(s, "neural_networks")

    concept_names = {s.node(c)["attrs"]["name"]
                     for c in s.neighbours(mt, "has_concept")}
    # Must include the headline NN building-block vocabulary.
    for required in ("tensor", "weight", "layer", "gradient", "loss",
                     "optimizer", "embedding", "softmax",
                     "nonlinearity", "training_loop"):
        assert required in concept_names, f"missing concept {required!r}"
    assert len(concept_names) >= 15


def test_seed_installs_design_patterns_with_origin_neural_networks():
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    load_one_seed(s, "neural_networks")

    nn_patterns = [
        s.node(n)["attrs"]
        for n in s.nodes("DesignPattern")
        if s.node(n)["attrs"].get("origin") == "neural_networks"
    ]
    names = {p["name"] for p in nn_patterns}
    for required in ("linear_layer", "softmax_classifier", "mlp_block",
                     "embedding_table", "attention_block",
                     "gradient_descent", "cross_entropy_loss"):
        assert required in names, f"missing NN pattern {required!r}"


def test_seed_installs_nn_shaped_code_targets():
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    load_one_seed(s, "neural_networks")

    op_names = {s.node(n)["attrs"].get("op_name")
                for n in s.nodes("CodeTarget")}
    assert "classify_word_signature" in op_names
    assert "score_substrate_match" in op_names
    assert "embed_concept" in op_names


def test_seed_installs_exclusions():
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    load_one_seed(s, "neural_networks")

    pairs = {(s.node(n)["attrs"].get("pattern_tag"),
              s.node(n)["attrs"].get("target_anti_tag"))
             for n in s.nodes("DesignExclusion")}
    assert ("softmax_classifier", "regression_target") in pairs
    assert ("mse_loss", "discrete_target") in pairs


def test_idempotent_install():
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)

    load_one_seed(s, "neural_networks")
    counts_first = {
        t: len(s.nodes(t))
        for t in ("Microtheory", "Concept", "DesignPattern",
                  "CodeTarget", "DesignExclusion")
    }

    load_one_seed(s, "neural_networks")
    counts_second = {
        t: len(s.nodes(t))
        for t in ("Microtheory", "Concept", "DesignPattern",
                  "CodeTarget", "DesignExclusion")
    }

    assert counts_first == counts_second


# ---------------------------------------------------------------------------
# selector behaviour — the existing pick_design_pattern with NN data
# ---------------------------------------------------------------------------

def test_pick_picks_nn_pattern_for_fuzzy_classification_target():
    """No NN-specific logic in pick_design_pattern. It just ranks by
    tag match + expected_speedup over all DesignPattern nodes. With
    NN data installed, an NN-shaped target should select an NN
    pattern."""
    from domains.design_patterns import (
        install_design_patterns_mt, pick_design_pattern,
    )
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    install_design_patterns_mt(s)        # 8 compiler patterns
    load_one_seed(s, "neural_networks")      # 13 NN patterns

    # NN-shaped target tags.
    picked = pick_design_pattern(s, [
        "fuzzy_classification", "n_classes_known", "function_approximation",
    ])
    assert picked is not None
    assert picked["name"] in ("softmax_classifier", "mlp_block"), (
        f"expected softmax_classifier or mlp_block, got {picked['name']!r}")
    assert picked["origin"] == "neural_networks"


def test_pick_still_picks_compiler_pattern_for_compiler_target():
    """No regression: compiler-shaped tags must still pick a compiler
    pattern, not an NN one."""
    from domains.design_patterns import (
        install_design_patterns_mt, pick_design_pattern,
    )
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    install_design_patterns_mt(s)
    load_one_seed(s, "neural_networks")

    picked = pick_design_pattern(s, [
        "hot_loop", "math_heavy", "expensive_inner_op",
        "pure_function", "small_input_domain", "precomputable",
    ])
    assert picked is not None
    assert picked["origin"] == "design_patterns", (
        f"compiler tags should pick a compiler pattern, got "
        f"{picked['name']!r} origin={picked.get('origin')!r}")


def test_survey_pattern_opportunities_reports_all_targets():
    """The cortex's own self-introspection. Runs pick_design_pattern
    over every CodeTarget; each NN-shaped target should resolve to a
    pattern with origin=neural_networks, each compiler-shaped target
    to origin=design_patterns. No filter in the survey — output is
    whatever the selector picks."""
    from domains.code_writing_cortex import CodeWritingCortex

    class _A:
        def op_stats(self):
            return {}

    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    cortex = CodeWritingCortex(s, agent=_A()).install()
    rows = cortex.survey_pattern_opportunities()

    by_op = {r["op_name"]: r for r in rows}
    # Compiler target with rich design_tags.
    assert "evaluate_polynomial" in by_op
    assert by_op["evaluate_polynomial"]["pattern_origin"] == "design_patterns"
    # NN-shaped targets resolved to NN-origin patterns.
    assert "classify_word_signature" in by_op
    assert by_op["classify_word_signature"]["pattern_origin"] == "neural_networks"
    assert "embed_concept" in by_op
    assert by_op["embed_concept"]["pattern_origin"] == "neural_networks"


def test_pick_picks_embedding_table_for_discrete_to_continuous():
    from domains.design_patterns import (
        install_design_patterns_mt, pick_design_pattern,
    )
    s = _fresh_substrate()
    _seed_compiler_theory_and_code_authoring(s)
    install_design_patterns_mt(s)
    load_one_seed(s, "neural_networks")

    picked = pick_design_pattern(s, [
        "discrete_to_continuous", "vocabulary_lookup", "lookup_or_learned",
    ])
    assert picked is not None
    # Both embedding_table and lookup_table can match — embedding_table
    # gets 3 matches, lookup_table 1 (small_input_domain is the only
    # overlap and we didn't pass it). embedding_table should win.
    assert picked["name"] == "embedding_table"
