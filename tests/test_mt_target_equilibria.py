"""mt_target_equilibria Mt — Mt's grammar as Hamiltonian."""
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


def test_mte_installs():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "mt_target_equilibria"


def test_mte_carries_foundation():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("target_equilibrium_per_Mt",
                     "Mt_admissibility_grammar_is_H"):
        assert required in names


def test_mte_carries_encoding():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("has_concept_implies_positive_field",
                     "decomposes_implies_positive_coupling",
                     "exclusion_implies_negative_coupling",
                     "genlMt_inherits_couplings",
                     "categorical_clustering_dense_J",
                     "has_rule_implies_constraint_term",
                     "soundness_category_determines_constraint_strength"):
        assert required in names


def test_mte_carries_inter_Mt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("shared_nodes_different_Hs",
                     "conflicting_targets_across_Mts",
                     "effective_H_is_weighted_sum",
                     "no_view_from_nowhere_mechanically"):
        assert required in names


def test_mte_carries_Mt_quality():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Mt_soundness_via_basin_depth",
                     "Mt_coherence_with_parent",
                     "Mt_distinctness_via_basin_separation",
                     "Mt_coverage_via_engaged_nodes"):
        assert required in names


def test_mte_carries_structural_vs_learned():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("structural_target_from_grammar",
                     "learned_target_from_Hebbian",
                     "target_as_structural_anchor_plus_drift",
                     "frozen_vs_adaptive_Mts"):
        assert required in names


def test_mte_carries_substrate_features():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Mt_reflexes_drive_field_toward_target",
                     "Impasse_is_distance_from_target",
                     "active_attention_raises_Mt_beta",
                     "competent_man_threshold_per_Mt",
                     "frame_switch_changes_active_target"):
        assert required in names


def test_mte_carries_operations():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("wrongness_in_Mt_is_distance_to_Mt_target",
                     "per_node_deviation_diagnostic",
                     "drive_toward_Mt_target",
                     "mean_field_marginal_per_Mt"):
        assert required in names


def test_mte_carries_substrate_position():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("substrate_identity_is_target_equilibria",
                     "substrate_targets_are_not_neutral",
                     "substrate_holds_alternatives_with_low_beta",
                     "substrate_self_assessment_via_basin_quality"):
        assert required in names


def test_mte_carries_architecture():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("mt_target_signature_attr",
                     "mt_coupling_seeds_attr",
                     "mt_field_seeds_attr",
                     "compute_Mt_marginal_function",
                     "distance_to_Mt_target_function",
                     "Mt_driving_reflex_pattern",
                     "audit_basin_topology_function",
                     "frame_switch_via_beta_redistribution"):
        assert required in names


def test_mte_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 13


def test_total_mte_count():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mt_target_equilibria")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 40, f"only {n_concepts} concepts"
    assert n_rules >= 13, f"only {n_rules} rules"
