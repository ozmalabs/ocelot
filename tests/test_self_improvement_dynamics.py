"""self_improvement_dynamics Mt — basin evolution rules."""
from __future__ import annotations

import pytest
from substrate_rs import _native
from substrate.boot_all import load_one_seed


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


def test_sid_installs():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "self_improvement_dynamics"


def test_sid_carries_foundation():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("basin_topology_evolves",
                     "substrate_is_own_architect",
                     "improvement_is_not_arbitrary_drift"):
        assert required in names


def test_sid_carries_drives():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("drive_curiosity_high_entropy",
                     "drive_coherence_reduce_frustration",
                     "drive_stability_deepen_confirmed",
                     "drive_discrimination_separate_basins",
                     "drive_coverage_extend_important",
                     "drive_parsimony_prune_dead",
                     "improvement_drives_compose_into_objective"):
        assert required in names


def test_sid_carries_when_to_modify():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("when_to_deepen_basin", "when_to_flatten_basin",
                     "when_to_add_Mt", "when_to_merge_Mts",
                     "when_to_split_Mt"):
        assert required in names


def test_sid_carries_update_mechanisms():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Hebbian_J_update", "anti_Hebbian_J_decay",
                     "J_pruning_below_threshold",
                     "h_evidence_update", "h_default_decay",
                     "beta_attention_boost",
                     "structural_rewrite_via_grammar"):
        assert required in names


def test_sid_carries_identity_protection():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("foundational_Mts_are_frozen",
                     "domain_Mts_are_adaptive", "Mt_freeze_flag",
                     "alignment_under_self_modification"):
        assert required in names


def test_sid_carries_failure_modes():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("fail_mode_frozen_should_adapt",
                     "fail_mode_drifted_past_anchor",
                     "fail_mode_frustrated_Mt",
                     "fail_mode_redundant_Mt",
                     "fail_mode_sparse_Mt",
                     "fail_mode_conflicting_reflexes"):
        assert required in names


def test_sid_carries_corrections():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("correction_raise_plasticity",
                     "correction_re_anchor", "correction_split_Mt",
                     "correction_merge_Mts", "correction_prune_Mt",
                     "correction_beta_reweight"):
        assert required in names


def test_sid_carries_loop():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("self_improvement_loop", "monitor_basin_topology",
                     "detect_failure_mode", "apply_correction_per_mode",
                     "verify_improvement", "track_substrate_metrics"):
        assert required in names


def test_sid_carries_connections_to_existing():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("meta_monitor_is_self_improvement_loop",
                     "architecture_cortex_is_quality_audit",
                     "DevelopmentCortex_is_strategy_layer",
                     "feature_invention_is_Mt_birth",
                     "substrate_meta_capabilities_compose"):
        assert required in names


def test_sid_carries_architecture():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Mt_update_policy_attr",
                     "Mt_basin_quality_metrics_attr",
                     "self_improvement_loop_reflex",
                     "failure_mode_detector_rule_set",
                     "correction_operations_module"):
        assert required in names


def test_sid_rules_carry_soundness_category():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 14


def test_total_sid_count():
    s = _fresh_substrate()
    mt = load_one_seed(s, "self_improvement_dynamics")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 50, f"only {n_concepts} concepts"
    assert n_rules >= 14, f"only {n_rules} rules"
