"""mathematics Mt + 6 decomposition packs."""
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


def test_math_installs():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "mathematics"


def test_math_carries_foundation_number_algebra():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("ZFC_axioms", "set_operations", "function_definition",
                     "equivalence_relation", "proof_methods",
                     "mathematical_induction", "natural_numbers_Peano",
                     "integer_construction", "rational_real_complex",
                     "prime_numbers", "fundamental_theorem_arithmetic",
                     "Euclidean_algorithm", "modular_arithmetic",
                     "Riemann_hypothesis", "vector_space",
                     "linear_transformation", "matrix_multiplication",
                     "determinant", "eigenvalues_eigenvectors",
                     "singular_value_decomposition", "inner_product_norm",
                     "Gram_Schmidt", "group_definition", "ring_field",
                     "homomorphism_isomorphism", "Galois_theory"):
        assert required in names


def test_math_carries_calculus_analysis():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("limit_definition", "derivative_definition",
                     "chain_rule", "integral_Riemann",
                     "fundamental_theorem_calculus", "Taylor_series",
                     "multivariable_calculus", "vector_calculus",
                     "differential_equations",
                     "real_analysis_completeness",
                     "uniform_convergence",
                     "complex_analysis_holomorphic", "measure_theory",
                     "functional_analysis", "Hilbert_space"):
        assert required in names


def test_math_carries_topology_geometry_probability():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("topology_open_sets", "metric_space", "compactness",
                     "connectedness", "fundamental_group", "manifold",
                     "Euclidean_axioms", "non_Euclidean_geometry",
                     "Riemannian_metric", "projective_geometry",
                     "algebraic_geometry", "probability_space",
                     "random_variable", "expectation_variance",
                     "common_distributions", "central_limit_theorem",
                     "law_of_large_numbers", "Bayes_theorem_math",
                     "Markov_chain", "stochastic_process",
                     "hypothesis_testing", "confidence_intervals",
                     "regression_analysis", "Bayesian_inference",
                     "MCMC_sampling"):
        assert required in names


def test_math_carries_discrete_numerical_optimization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("combinatorics_counting", "graph_theory_math",
                     "generating_functions", "recurrence_relations",
                     "Ramsey_theory", "numerical_root_finding",
                     "numerical_integration", "numerical_ODE",
                     "PDE_solvers", "numerical_stability",
                     "linear_programming", "convex_optimization",
                     "gradient_descent_math", "Newton_method_optimization",
                     "KKT_conditions", "integer_programming",
                     "dynamic_programming_math"):
        assert required in names


def test_math_carries_category_type_info_game():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("category_definition", "functor",
                     "natural_transformation", "monad", "adjunction",
                     "Yoneda_lemma", "lambda_calculus_math",
                     "simply_typed_lambda", "dependent_types",
                     "Curry_Howard_correspondence",
                     "homotopy_type_theory", "Shannon_entropy",
                     "mutual_information", "KL_divergence_math",
                     "channel_capacity", "Shannon_source_coding",
                     "Nash_equilibrium", "zero_sum_game",
                     "mechanism_design", "evolutionary_game_theory"):
        assert required in names


def test_math_carries_dynamical_logic():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("dynamical_system", "fixed_point_stability",
                     "bifurcation", "strange_attractor",
                     "Lyapunov_exponent", "fractal_dimension",
                     "model_theory", "computability_theory",
                     "complexity_theory_math", "Godel_completeness",
                     "axiom_of_choice", "continuum_hypothesis"):
        assert required in names


def test_math_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_math_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "mathematics")
    ids = install_all_concept_expansions(s)
    for required in ("linear_algebra_deep_decomposition",
                     "probability_statistics_deep_decomposition",
                     "calculus_analysis_deep_decomposition",
                     "category_type_theory_decomposition",
                     "optimization_deep_decomposition",
                     "information_theory_deep_decomposition"):
        assert required in ids, f"math pack {required!r} not loaded"


def test_total_math_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "mathematics")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 175, f"only {n_concepts} concepts"
    assert n_rules >= 45, f"only {n_rules} rules"
