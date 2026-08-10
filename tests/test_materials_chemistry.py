"""materials_chemistry Mt + 9 decomposition packs."""
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


def test_mc_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "materials_chemistry"


def test_mc_carries_atomic_bonding():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("atomic_structure_orbitals", "electron_configuration",
                     "periodic_trends", "ionic_bonding", "covalent_bonding",
                     "metallic_bonding", "hydrogen_bonding", "van_der_Waals",
                     "VSEPR_geometry", "orbital_hybridization"):
        assert required in names


def test_mc_carries_thermo_kinetics_equilibrium():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("stoichiometry", "Avogadros_number",
                     "enthalpy_reaction", "entropy_chemistry",
                     "Gibbs_free_energy", "rate_law", "Arrhenius_equation",
                     "catalysis", "reaction_mechanisms",
                     "equilibrium_constant", "Le_Chatelier_principle",
                     "Ka_Kb_Ksp"):
        assert required in names


def test_mc_carries_acids_bases_electrochem():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("pH_pOH", "Bronsted_acid_base", "Lewis_acid_base",
                     "buffer_solution", "oxidation_reduction",
                     "standard_reduction_potential", "Nernst_equation",
                     "battery_chemistry", "fuel_cell",
                     "corrosion_electrochemistry"):
        assert required in names


def test_mc_carries_organic_biochem():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("functional_groups_organic", "alkanes_alkenes_alkynes",
                     "aromatic_compounds", "stereochemistry",
                     "SN1_SN2_substitution", "polymerization_chain",
                     "amino_acids_proteins", "DNA_RNA_structure",
                     "lipids_membranes", "enzymes", "carbohydrates"):
        assert required in names


def test_mc_carries_materials_science():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("FCC_BCC_HCP_crystals", "Miller_indices",
                     "point_defects", "line_defects_dislocations",
                     "grain_boundaries", "Ficks_diffusion_laws",
                     "diffusion_Arrhenius", "Fe_C_phase_diagram",
                     "lever_rule", "TTT_CCT_diagrams",
                     "annealing_quenching_tempering",
                     "precipitation_hardening", "work_hardening",
                     "solid_solution_strengthening",
                     "grain_refinement_Hall_Petch"):
        assert required in names


def test_mc_carries_polymers_composites_ceramics_semi():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("polymer_glass_transition", "polymer_crystallinity",
                     "polymer_viscoelasticity", "molecular_weight_distribution",
                     "composites_matrix_reinforcement", "composite_lay_up",
                     "ceramic_processing", "band_theory_semiconductors",
                     "doping_p_n", "pn_junction"):
        assert required in names


def test_mc_carries_nano_characterization():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("graphene", "carbon_nanotubes", "quantum_dots",
                     "nanoparticles_synthesis", "XRD_x_ray_diffraction",
                     "SEM_TEM_imaging", "AFM_atomic_force",
                     "NMR_spectroscopy", "IR_spectroscopy",
                     "mass_spectrometry", "chromatography_HPLC_GC"):
        assert required in names


def test_mc_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_mc_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "materials_chemistry")
    ids = install_all_concept_expansions(s)
    for required in ("quantum_atomic_structure_decomposition",
                     "organic_mechanisms_decomposition",
                     "electrochemistry_batteries_decomposition",
                     "crystal_defects_decomposition",
                     "biochemistry_metabolism_decomposition",
                     "polymer_chemistry_decomposition",
                     "semiconductor_physics_decomposition",
                     "nanomaterials_decomposition",
                     "analytical_techniques_decomposition"):
        assert required in ids, f"mc pack {required!r} not loaded"


def test_total_mc_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "materials_chemistry")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 185, f"only {n_concepts} concepts"
    assert n_rules >= 55, f"only {n_rules} rules"
