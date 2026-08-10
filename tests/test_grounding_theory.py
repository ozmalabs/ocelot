"""grounding_theory Mt — vector grounding as Axiom 0's consequence."""
from __future__ import annotations

import pytest
from substrate_rs import _native


_NODE_TYPES = (
    "Microtheory", "Concept", "Rule",
    "DesignPattern", "ProgrammingLanguage", "CodeTarget",
    "DesignExclusion", "LanguageExclusion", "LanguageScoringConfig",
    "CodeWritingCortex", "CodeAuthoringRoot", "Reflex",
    "ReplacementTarget", "CodeDraft", "ValidationResult",
    "CodeInstallation",
)
_EDGE_TYPES = (
    "genlMt", "has_concept", "has_rule", "owns_microtheory",
    "owns_root", "has_reflex", "current_target", "has_draft",
    "validated_by", "installed_as", "authored_in", "uses_pattern",
    "subClassOf", "in_category", "decomposes",
)


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et, "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    s.add_node("Microtheory", {"name": "compiler_theory"})
    return s


def test_gt_installs():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "grounding_theory"


def test_gt_carries_foundation_axiom0_link():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("axiom_zero_implies_vector_grounding",
                     "grounding_vector_definition",
                     "axiom_zero_no_view_from_nowhere"):
        assert required in names


def test_gt_carries_dimensions():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("frame_dimensions", "modality_dimensions",
                     "aspect_dimensions"):
        assert required in names


def test_gt_carries_interpretation_of_existing():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("binary_grounding_is_residue",
                     "phonology_divergence_already_vectoral",
                     "Unknown_as_zero_vector",
                     "ist_formula_as_projection"):
        assert required in names


def test_gt_carries_operations():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("wrongness_as_vector_displacement",
                     "how_wrong_per_dimension",
                     "conviction_as_magnitude",
                     "coherence_as_alignment",
                     "multiple_inconsistent_views_simultaneously"):
        assert required in names


def test_gt_carries_stance():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("frame_relativity_not_relativism",
                     "vector_grounding_extends_substrate_features",
                     "competent_man_sufficiency_thresholded_magnitude",
                     "babble_extends_to_vector_sampling",
                     "structural_constraint_not_anything_goes"):
        assert required in names


def test_gt_carries_comparisons():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("embedding_spaces_partial_vector_grounding",
                     "Dempster_Shafer_evidence_partial_match",
                     "fuzzy_logic_per_dimension_partial",
                     "paraconsistent_logic_alignment"):
        assert required in names


def test_gt_carries_architecture():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Concept_grounding_vector_attr",
                     "refers_to_edge_becomes_weighted",
                     "Unknown_node_collapses_to_zero_vector_Concept",
                     "Impasse_vector_valued",
                     "operations_on_grounding_vectors",
                     "migration_strategy_thresholded_readout"):
        assert required in names


def test_gt_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 10


def test_gt_total_count():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "grounding_theory")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 28, f"only {n_concepts} concepts"
    assert n_rules >= 10, f"only {n_rules} rules"
