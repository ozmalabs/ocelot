"""causal_attitude_networks Mt — CAN as grounding mechanism."""
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


def test_can_installs():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "causal_attitude_networks"


def test_can_carries_foundation_and_ising():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("CAN_Borsboom_Dalege",
                     "attitudes_not_latent_variables",
                     "evaluations_beliefs_behaviours_as_nodes",
                     "node_state_sigma", "coupling_J_ij",
                     "external_field_h_i", "inverse_temperature_beta",
                     "Hamiltonian_H", "Boltzmann_distribution",
                     "free_energy_F"):
        assert required in names


def test_can_carries_dynamics():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Metropolis_Hastings_update", "Glauber_dynamics",
                     "mean_field_approximation",
                     "evidence_shifts_field",
                     "basin_hopping_belief_revision"):
        assert required in names


def test_can_carries_attitude_properties():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("stability_local_minimum",
                     "attitude_strength_is_connectivity",
                     "ambivalence_spin_glass_frustration",
                     "polarisation_phase_transition",
                     "attention_modulates_beta",
                     "multiple_basins_multiple_views"):
        assert required in names


def test_can_carries_mapping_to_grounding():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("marginal_expectation_is_grounding",
                     "Mt_is_subnetwork_with_signature_couplings",
                     "multiple_Mts_multiple_Hamiltonians",
                     "frame_switch_changes_active_Hamiltonian",
                     "wrongness_is_distance_to_target_marginal",
                     "diagnostic_per_node_deviation"):
        assert required in names


def test_can_carries_substrate_features():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("info_gain_drives_curiosity",
                     "babble_is_MCMC_sampling",
                     "predicate_churn_is_bistability",
                     "conviction_is_J_times_beta",
                     "coherence_is_negative_free_energy"):
        assert required in names


def test_can_carries_learning():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("coupling_learning_Hebbian",
                     "field_calibration_from_world",
                     "network_size_grows_with_learning"):
        assert required in names


def test_can_carries_lineage_and_comparisons():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Ising_model_history",
                     "Hopfield_network_associative_memory",
                     "Boltzmann_machine_learning",
                     "psychopathology_network_Cramer_Borsboom",
                     "frequentist_vs_thermal_sampling",
                     "CAN_vs_predictive_processing",
                     "CAN_vs_Bayesian_network"):
        assert required in names


def test_can_carries_architecture():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("concept_state_attr_substrate",
                     "causal_influence_edge_type",
                     "external_field_attr_substrate",
                     "Mt_temperature_attr",
                     "dynamics_module_metropolis_glauber",
                     "Impasse_becomes_network_diagnosis",
                     "migration_from_binary_to_CAN"):
        assert required in names


def test_can_rules_carry_soundness_category():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 12


def test_total_can_count():
    s = _fresh_substrate()
    mt = load_one_seed(s, "causal_attitude_networks")
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 48, f"only {n_concepts} concepts"
    assert n_rules >= 14, f"only {n_rules} rules"
