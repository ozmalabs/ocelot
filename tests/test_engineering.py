"""engineering Mt + 9 decomposition packs."""
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


def test_eng_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "engineering"


def test_eng_carries_foundation():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("engineering_method", "factor_of_safety",
                     "design_constraints", "tradeoff_analysis",
                     "iterative_design"):
        assert required in names


def test_eng_carries_mechanics():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("statics_equilibrium", "free_body_diagram",
                     "moment_force_about_point", "centroid_centre_of_mass",
                     "moment_of_inertia_area", "moment_of_inertia_mass",
                     "kinematics_translation", "kinematics_rotation",
                     "Newton_second_law", "energy_conservation",
                     "work_energy_theorem", "impulse_momentum"):
        assert required in names


def test_eng_carries_strength_materials():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("stress_strain", "Youngs_modulus", "yield_strength",
                     "ultimate_tensile_strength", "ductile_vs_brittle",
                     "fatigue_SN_curve", "fracture_mechanics", "creep",
                     "bending_stress_formula", "shear_stress", "torsion"):
        assert required in names


def test_eng_carries_materials():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("carbon_steel", "alloy_steel", "aluminum_alloys",
                     "polymers_thermoplastics", "polymers_thermosets",
                     "composites_fiber_reinforced", "ceramics_engineering",
                     "phase_diagram", "heat_treatment", "corrosion"):
        assert required in names


def test_eng_carries_thermo_fluids_heat():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("first_law_thermodynamics", "second_law_thermodynamics",
                     "Carnot_cycle", "Rankine_cycle", "Brayton_cycle",
                     "Otto_cycle", "Diesel_cycle", "refrigeration_cycle",
                     "conduction_Fourier", "convection_Newton_cooling",
                     "radiation_Stefan_Boltzmann", "heat_exchanger_LMTD",
                     "Bernoulli_equation", "Reynolds_number",
                     "Navier_Stokes_equations", "pipe_flow_friction",
                     "pump_centrifugal", "cavitation"):
        assert required in names


def test_eng_carries_electrical_em_control():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("ohms_law", "Kirchhoff_laws", "Thevenin_equivalent",
                     "RC_RL_RLC_circuits", "op_amp_ideal",
                     "AC_phasor_analysis", "three_phase_power",
                     "transformer", "induction_motor", "Maxwell_equations",
                     "impedance_matching", "antenna_dipole",
                     "PID_controller", "transfer_function",
                     "stability_root_locus", "Bode_plot",
                     "state_space_representation", "model_predictive_control",
                     "Fourier_transform", "Laplace_transform",
                     "z_transform", "sampling_Nyquist", "filter_design"):
        assert required in names


def test_eng_carries_structural_chemical_aero():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("truss_analysis", "beam_bending", "column_buckling",
                     "reinforced_concrete", "steel_structure_design",
                     "seismic_design", "finite_element_method",
                     "Reynolds_transport_theorem", "mass_energy_balance",
                     "reactor_CSTR_PFR", "distillation",
                     "aerodynamics_lift_drag", "Mach_number",
                     "rocket_equation", "orbital_mechanics_Kepler"):
        assert required in names


def test_eng_carries_manufacturing_machine_design():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("gear_train", "bearing_selection", "fasteners_threaded",
                     "shaft_design", "spring_design", "belt_chain_drive",
                     "machining_turning", "machining_milling",
                     "additive_manufacturing", "injection_molding",
                     "casting", "forging", "welding", "GD_T",
                     "six_sigma", "statistical_process_control"):
        assert required in names


def test_eng_carries_systems_economics_standards():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("MTBF_reliability", "Weibull_distribution",
                     "redundancy_design", "FMEA_engineering",
                     "systems_engineering_V_model",
                     "requirements_engineering", "trade_study",
                     "lifecycle_cost", "engineering_economics_NPV",
                     "engineering_economics_IRR", "payback_period",
                     "ASME_codes", "ISO_standards", "IEEE_standards",
                     "ASTM_materials", "CAD_parametric", "FEA_workflow",
                     "CFD_workflow", "CAM_toolpaths"):
        assert required in names


def test_eng_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_eng_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "engineering")
    ids = install_all_concept_expansions(s)
    for required in ("statics_dynamics_detailed_decomposition",
                     "materials_failure_modes_decomposition",
                     "control_systems_design_decomposition",
                     "signal_processing_engineering_decomposition",
                     "thermo_cycles_decomposition",
                     "structural_analysis_design_decomposition",
                     "manufacturing_processes_decomposition",
                     "fluid_mechanics_decomposition",
                     "systems_engineering_methodology_decomposition"):
        assert required in ids, f"eng pack {required!r} not loaded"


def test_total_eng_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "engineering")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 230, f"only {n_concepts} concepts"
    assert n_rules >= 60, f"only {n_rules} rules"
