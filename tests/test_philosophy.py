"""philosophy Mt + 10 decomposition packs."""
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


def test_phil_installs_with_genlmt():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    assert mt is not None
    assert s.node(mt)["attrs"]["name"] == "philosophy"


def test_phil_carries_epistemology():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("epistemology_definition", "JTB_knowledge",
                     "Gettier_problem", "foundationalism",
                     "coherentism", "reliabilism",
                     "internalism_externalism", "skepticism_global",
                     "a_priori_a_posteriori",
                     "analytic_synthetic_distinction",
                     "Cartesian_doubt", "tabula_rasa"):
        assert required in names


def test_phil_carries_mind():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("mind_body_problem", "substance_dualism",
                     "property_dualism", "physicalism_identity_theory",
                     "functionalism", "computational_theory_of_mind",
                     "qualia_problem", "hard_problem_consciousness",
                     "Chinese_room", "Marys_room",
                     "philosophical_zombie", "intentionality",
                     "extended_mind_thesis", "Nagel_bat"):
        assert required in names


def test_phil_carries_science():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Hume_problem_of_induction", "falsificationism_Popper",
                     "paradigm_Kuhn", "research_programmes_Lakatos",
                     "Feyerabend_anything_goes", "Bayesian_confirmation",
                     "demarcation_problem", "scientific_realism_antirealism",
                     "explanation_DN_model", "causation_counterfactual"):
        assert required in names


def test_phil_carries_language_metaphysics():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("Frege_sense_reference", "Russell_descriptions",
                     "Wittgenstein_language_game", "Grice_implicature",
                     "speech_act_theory", "language_of_thought",
                     "ontology", "universals_particulars",
                     "personal_identity", "possible_worlds",
                     "necessary_a_posteriori", "time_A_B_theory",
                     "free_will_compatibilism", "free_will_libertarianism",
                     "emergence_supervenience", "grounding_metaphysics",
                     "ship_of_Theseus"):
        assert required in names


def test_phil_carries_ethics_logic():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("consequentialism", "deontology_Kant", "virtue_ethics",
                     "contractualism", "metaethics_moral_realism",
                     "moral_anti_realism", "trolley_problem",
                     "naturalistic_fallacy", "propositional_logic",
                     "predicate_logic_FOL", "modal_logic",
                     "Russell_paradox", "liar_paradox", "sorites_paradox",
                     "Godel_incompleteness"):
        assert required in names


def test_phil_carries_continental_eastern_AI():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    names = {s.node(c)["attrs"]["name"]
             for c in s.neighbours(mt, "has_concept")}
    for required in ("phenomenology", "existentialism", "hermeneutics",
                     "structuralism_post", "Buddhism_no_self",
                     "Buddhism_dependent_origination", "Taoism_Tao",
                     "Confucianism_ren", "Turing_test", "Strong_weak_AI",
                     "value_alignment_AI", "intentional_stance",
                     "philosophical_zombie_AI", "extended_cognition_AI",
                     "axiom_zero_substrate", "authored_not_trained",
                     "entity_not_program"):
        assert required in names


def test_phil_rules_carry_soundness_category():
    from substrate.boot_all import load_one_seed
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    valid = {"denotational_equivalence", "algebraic_law",
             "extensional_equivalence", "cost_equivalence",
             "referential_transparency"}
    n_with_cat = 0
    for r in s.neighbours(mt, "has_rule"):
        if s.node(r)["attrs"].get("soundness_category") in valid:
            n_with_cat += 1
    assert n_with_cat >= 18


def test_phil_decomposition_packs_load():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    load_one_seed(s, "philosophy")
    ids = install_all_concept_expansions(s)
    for required in ("epistemology_deep_decomposition",
                     "philosophy_of_mind_deep_decomposition",
                     "philosophy_of_science_deep_decomposition",
                     "ethics_deep_decomposition",
                     "logic_paradoxes_decomposition",
                     "continental_phenomenology_decomposition",
                     "eastern_philosophy_decomposition",
                     "philosophy_of_AI_substrate_positions_decomposition",
                     "political_philosophy_decomposition",
                     "aesthetics_decomposition"):
        assert required in ids, f"phil pack {required!r} not loaded"


def test_total_phil_concept_count():
    from substrate.boot_all import load_one_seed
    from domains.concept_expansions import install_all_concept_expansions
    s = _fresh_substrate()
    mt = load_one_seed(s, "philosophy")
    install_all_concept_expansions(s)
    n_concepts = len(s.neighbours(mt, "has_concept"))
    n_rules = len(s.neighbours(mt, "has_rule"))
    assert n_concepts >= 195, f"only {n_concepts} concepts"
    assert n_rules >= 60, f"only {n_rules} rules"
