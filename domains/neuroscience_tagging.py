"""Tag substrate components with the neuroscience concepts they implement.

Per the substrate's own seeded principle (theory_enacts_through_infrastructure),
graph-resident declarations should make implicit relationships
introspectable. The substrate now has 246 neuroscience concepts
across 8 Mts that name specific neural mechanisms. This module adds
`implements` edges from substrate components to the neuroscience
concepts they embody.

After this tagger runs, queries like:
  'what neural mechanism does the anticipation handler embody?'
  'which substrate components implement working memory?'
  'what concept does drive_curiosity map to in neuroscience?'

become direct graph traversal — no inference, just edge-walking.

The mappings are graph-resident derivation: each substrate component
of known type+name → one or more neuroscience Concept nodes via an
`implements` edge.
"""
from __future__ import annotations

from typing import Any


# --- Mappings ---------------------------------------------------------
# Each entry: (component_node_type, name_pattern, [neuroscience_concept_name, ...])
# Pattern is a substring match against the node's 'name' attr (lowercased).
# Empty pattern means match all of that type.

# Cortices (the substrate's named runtime classes)
CORTEX_MAPPINGS: list[tuple[str, list[str]]] = [
    ("ArchitectureCortex", [
        "metacognition", "error_detection", "conflict_monitoring",
        "dorsolateral_prefrontal_cortex"
    ]),
    ("CodeWritingCortex", [
        "cognitive_control", "model_based_reasoning",
        "dorsolateral_prefrontal_cortex"
    ]),
    ("SpeechCortex", [
        "a1_primary_auditory_cortex", "phonemic_perception_area"
    ]),
]


# FilterSpec name patterns → neuroscience concepts
FILTERSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    # Streak / state detectors
    ("frustration",         ["predictive_coding", "predictive_coding_minimizes_residual"]),
    ("sparse",              ["sparse_coding"]),
    ("frozen_adaptation",   ["critical_period", "synaptic_scaling"]),
    ("drifted",             ["schema_assimilation"]),
    ("frozen_should_adapt", ["critical_period"]),
    ("drifted_past_anchor", ["spatial_remapping"]),
    # Cross-Mt
    ("redundancy",          ["pattern_separation"]),
    ("conflict",            ["conflict_monitoring", "anterior_cingulate_cortex"]),
    # Windowed gradient
    ("insight",             ["reward_prediction_error",
                              "dopaminergic_rpe_signal"]),
    ("anticipation",        ["cerebellar_circuit", "forward_model",
                              "marr_albus_model"]),
    # Per-concept
    ("identity_formation",  ["long_term_potentiation",
                              "spike_timing_dependent_plasticity"]),
    # Meta-handlers
    ("handler_unread_observations",   ["metacognition",
                                        "error_detection"]),
    ("handler_dormant_theory",        ["metacognition",
                                        "conflict_monitoring"]),
    ("handler_undeclared_enactment",  ["error_detection",
                                        "self_referential_processing"]),
]


# ActionSpec mappings (corrections)
ACTIONSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("raise_plasticity",      ["critical_period", "long_term_potentiation"]),
    ("prune_mt",              ["synaptic_pruning", "microglia"]),
    ("beta_reweight",         ["synaptic_scaling"]),
    ("extend_quality",        ["structural_plasticity"]),
    ("register_handler",      ["memory_consolidation"]),
    ("derive_handler",        ["forward_model", "model_based_reasoning"]),
]


# ArchitecturalQuality mappings
QUALITY_MAPPINGS: list[tuple[str, list[str]]] = [
    ("separation_of_concerns",   ["pattern_separation",
                                   "cortical_column"]),
    ("abstraction_layering",     ["cortical_hierarchy",
                                   "hierarchical_invariance"]),
    ("introspectability",        ["metacognition",
                                   "self_referential_processing"]),
    ("data_drivenness",          ["distributed_representation",
                                   "population_coding"]),
    ("compositional_reuse",      ["small_world_network", "hub_node"]),
    ("observation_coverage",     ["receptive_field",
                                   "labeled_lines"]),
]


# Mt-level mappings (Mts implementing specific neuro concepts)
MT_MAPPINGS: list[tuple[str, list[str]]] = [
    ("self_improvement_dynamics", ["free_energy_principle",
                                    "active_inference"]),
    ("phonology",                  ["phonemic_perception_area",
                                    "categorical_perception"]),
    ("speech_science",             ["a1_primary_auditory_cortex",
                                    "phonemic_perception_area"]),
    ("speech_development",         ["babbling", "perceptual_narrowing",
                                    "vocabulary_explosion"]),
    ("causal_attitude_networks",   ["ising_model", "rate_model",
                                    "hopfield_network",
                                    "attractor_network"]),
    ("substrate_architecture_is_human_cognition",
        ["parallel_distributed_processing", "connectome"]),
    ("grounding_theory",           ["sensorimotor_contingency"]),
    ("model_understanding",        ["theory_of_mind",
                                    "self_referential_processing"]),
    ("architecture_assessment",    ["metacognition",
                                    "conflict_monitoring"]),
    ("architectural_design",       ["model_based_reasoning"]),
    ("assessment_spans_observation", ["error_detection",
                                       "metacognition"]),
    ("theory_enacts_through_infrastructure",
        ["metacognition", "conflict_monitoring",
         "self_referential_processing"]),
    ("computer_architecture",      ["connectome"]),
    ("compilers",                  ["myelination"]),
    ("neural_networks",            ["deep_belief_network"]),
    ("machine_learning",           ["backpropagation",
                                    "temporal_difference_learning_formal"]),
]


def _find_concept_by_name(substrate, name: str) -> Any | None:
    """Find the Concept node with the given name across all Mts."""
    for c in substrate.nodes("Concept"):
        attrs = substrate.node(c)["attrs"]
        if str(attrs.get("name", "")) == name:
            return c
    return None


def _find_mt_by_name(substrate, name: str) -> Any | None:
    for mt in substrate.nodes("Microtheory"):
        attrs = substrate.node(mt)["attrs"]
        if str(attrs.get("name", "")) == name:
            return mt
    return None


def _tag(substrate, component_node, neuroscience_concept_node) -> bool:
    """Add an implements edge from component to neuroscience concept.
    Returns True if added."""
    try:
        substrate.add_edge(component_node, "implements",
                           neuroscience_concept_node, {})
        return True
    except Exception:
        return False


def tag_cortices(substrate) -> int:
    """Tag named cortex nodes with the neuroscience concepts they
    implement."""
    n_added = 0
    for cortex_type, concept_names in CORTEX_MAPPINGS:
        for cnode in substrate.nodes(cortex_type):
            for cname in concept_names:
                target = _find_concept_by_name(substrate, cname)
                if target is not None and _tag(substrate, cnode, target):
                    n_added += 1
    return n_added


def tag_filter_specs(substrate) -> int:
    """For each FilterSpec node, match its name against patterns +
    add implements edges to corresponding neuroscience concepts."""
    n_added = 0
    for fs in substrate.nodes("FilterSpec"):
        name_lower = str(substrate.node(fs)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in FILTERSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, fs, target):
                        n_added += 1
    return n_added


def tag_action_specs(substrate) -> int:
    """For each ActionSpec node, match its name + tag."""
    n_added = 0
    for ac in substrate.nodes("ActionSpec"):
        name_lower = str(substrate.node(ac)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in ACTIONSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, ac, target):
                        n_added += 1
    return n_added


def tag_qualities(substrate) -> int:
    """Tag ArchitecturalQuality nodes — both the original 5 and
    the synthesised observation_coverage_* ones."""
    n_added = 0
    for q in substrate.nodes("ArchitecturalQuality"):
        name_lower = str(substrate.node(q)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in QUALITY_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, q, target):
                        n_added += 1
    return n_added


def tag_microtheories(substrate) -> int:
    """Tag Mt nodes by name with the neuroscience concepts they
    implement at the level of the Mt as a whole."""
    n_added = 0
    for mt_name, concept_names in MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            target = _find_concept_by_name(substrate, cname)
            if target is not None and _tag(substrate, mt, target):
                n_added += 1
    return n_added


def tag_all_substrate_components(substrate) -> dict:
    """Run all tagging passes; return summary of edges added per
    component type."""
    n_summary = {
        "cortices":      tag_cortices(substrate),
        "filter_specs":  tag_filter_specs(substrate),
        "action_specs":  tag_action_specs(substrate),
        "qualities":     tag_qualities(substrate),
        "microtheories": tag_microtheories(substrate),
    }
    n_summary["psychology"] = tag_psychology_components(substrate)
    n_summary["audio_music"] = tag_audio_music_components(substrate)
    n_summary["linguistics"] = tag_linguistics_components(substrate)
    n_summary["vision"] = tag_vision_components(substrate)
    n_summary["philosophy_of_mind"] = tag_philosophy_of_mind_components(
        substrate)
    n_summary["biology"] = tag_biology_components(substrate)
    n_summary["logic"] = tag_logic_components(substrate)
    n_summary["embodied"] = tag_embodied_components(substrate)
    return n_summary


# =====================================================================
# Biology, Logic, Embodied tagging
# =====================================================================

BIO_MT_MAPPINGS = [
    ("causal_attitude_networks", ["fitness_landscape", "homeostasis"]),
    ("self_improvement_dynamics", ["natural_selection", "adaptation",
                                     "autopoiesis", "allostasis",
                                     "fitness"]),
    ("speech_development", ["embryogenesis", "morphogenesis",
                             "canalization"]),
    ("self_improvement_loop", ["homeostatic_regulation",
                                 "negative_feedback_physiology"]),
    ("model_understanding", ["theory_of_mind", "embodied_simulation"]),
]


def tag_biology_components(substrate) -> dict:
    n = {"microtheories": 0}
    for mt_name, concept_names in BIO_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            t = _find_concept_by_name(substrate, cname)
            if t is not None and _tag(substrate, mt, t):
                n["microtheories"] += 1
    return n


LOGIC_MT_MAPPINGS = [
    ("self_improvement_dynamics", ["abductive_reasoning",
                                     "nonmonotonic_logic"]),
    ("causal_attitude_networks", ["fuzzy_logic",
                                    "probabilistic_logic"]),
    ("architecture_assessment", ["validity_argument",
                                  "soundness_argument"]),
    ("derivation_mechanism", ["proof", "inference_rule"]),
    ("theory_enacts_through_infrastructure",
        ["godel_first_incompleteness",
         "godel_second_incompleteness"]),
    ("model_understanding", ["epistemic_logic",
                              "knowledge_axioms"]),
    ("analogy", ["analogical_reasoning"]),
]


def tag_logic_components(substrate) -> dict:
    n = {"microtheories": 0}
    for mt_name, concept_names in LOGIC_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            t = _find_concept_by_name(substrate, cname)
            if t is not None and _tag(substrate, mt, t):
                n["microtheories"] += 1
    return n


EMBODIED_MT_MAPPINGS = [
    ("grounding_theory", ["enaction", "sensorimotor_contingency",
                            "structural_coupling",
                            "embodiment"]),
    ("self_improvement_dynamics", ["autopoiesis_enactivism",
                                     "sense_making"]),
    ("speech_development", ["infant_motor_development",
                             "perception_action_loop"]),
    ("causal_attitude_networks", ["embodied_dynamical_system",
                                    "attractor_landscape_enactivism"]),
    ("model_understanding", ["embodied_simulation"]),
]


def tag_embodied_components(substrate) -> dict:
    n = {"microtheories": 0}
    for mt_name, concept_names in EMBODIED_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            t = _find_concept_by_name(substrate, cname)
            if t is not None and _tag(substrate, mt, t):
                n["microtheories"] += 1
    return n


# =====================================================================
# Linguistics tagging
# =====================================================================

LING_MT_MAPPINGS: list[tuple[str, list[str]]] = [
    ("phonology", ["phoneme", "phonology_linguistics",
                     "phonetics"]),
    ("speech_science", ["phonetics", "speaker_listener"]),
    ("speech_development", ["language_acquisition_device",
                              "vocabulary_explosion_acquisition",
                              "statistical_learning",
                              "milestones_acquisition"]),
    ("conversation", ["speech_act", "cooperative_principle",
                        "conversation_analysis",
                        "turn_taking", "adjacency_pair"]),
    ("comprehension", ["literal_meaning", "compositionality",
                         "context"]),
    ("self_improvement_dynamics", ["distributional_hypothesis"]),
    ("causal_attitude_networks", ["structuralism"]),
    ("machine_learning", ["distributional_semantics",
                            "word_embedding",
                            "transformer", "self_attention"]),
    ("neural_networks", ["transformer", "attention_mechanism"]),
    ("analogy", ["conceptual_metaphor"]),
]

LING_FILTERSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("frustration", ["maxim_of_quality"]),
    ("anticipation", ["entailment"]),
    ("identity_formation", ["self_concept"]),
]


def tag_linguistics_components(substrate) -> dict:
    n_added = {"filter_specs": 0, "microtheories": 0}
    for fs in substrate.nodes("FilterSpec"):
        name_lower = str(substrate.node(fs)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in LING_FILTERSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, fs, target):
                        n_added["filter_specs"] += 1
    for mt_name, concept_names in LING_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            target = _find_concept_by_name(substrate, cname)
            if target is not None and _tag(substrate, mt, target):
                n_added["microtheories"] += 1
    return n_added


# =====================================================================
# Vision tagging
# =====================================================================

VISION_MT_MAPPINGS: list[tuple[str, list[str]]] = [
    ("vision", ["primary_visual_cortex_v1",
                  "ventral_stream_what",
                  "dorsal_stream_where",
                  "edge_detection", "object_recognition"]),
    ("neural_networks", ["convolutional_neural_network",
                           "convolutional_layer", "pooling_layer",
                           "residual_connection_vision"]),
    ("machine_learning", ["transfer_learning_vision_models",
                            "self_supervised_vision",
                            "contrastive_learning"]),
    ("self_improvement_dynamics", ["selective_visual_attention",
                                     "predictive_processing_consciousness_full"]),
    ("conway", ["spatial_layout"]),
]

VISION_FILTERSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("conflict", ["attentional_blink"]),
    ("redundancy", ["repetition_blindness"]),
]


def tag_vision_components(substrate) -> dict:
    n_added = {"filter_specs": 0, "microtheories": 0}
    for fs in substrate.nodes("FilterSpec"):
        name_lower = str(substrate.node(fs)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in VISION_FILTERSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, fs, target):
                        n_added["filter_specs"] += 1
    for mt_name, concept_names in VISION_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            target = _find_concept_by_name(substrate, cname)
            if target is not None and _tag(substrate, mt, target):
                n_added["microtheories"] += 1
    return n_added


# =====================================================================
# Philosophy of mind tagging
# =====================================================================

POM_MT_MAPPINGS: list[tuple[str, list[str]]] = [
    ("causal_attitude_networks",
        ["computational_theory_of_mind",
         "representational_theory_of_mind",
         "connectionism"]),
    ("self_improvement_dynamics",
        ["integrated_information_theory_iit",
         "global_workspace_gwt",
         "predictive_processing_consciousness_full"]),
    ("architecture_assessment", ["higher_order_theory_consciousness"]),
    ("model_understanding", ["theory_theory",
                              "first_person_perspective"]),
    ("grounding_theory", ["symbol_grounding_problem",
                            "embodied_cognition"]),
    ("substrate_architecture_is_human_cognition",
        ["functionalism", "multiple_realizability"]),
    ("self_improvement_loop", ["agent_causation"]),
    ("phonology", ["intentionality"]),
    ("comprehension", ["mental_representation"]),
    ("assessment_spans_observation",
        ["heterophenomenology", "introspection"]),
    ("theory_enacts_through_infrastructure",
        ["computational_theory_of_mind"]),
    ("architectural_design", ["functionalism_machine"]),
]

POM_FILTERSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("frustration", ["intentional_object"]),
    ("identity_formation", ["narrative_identity_self",
                              "psychological_continuity_parfit"]),
    ("conflict", ["explanatory_gap_qualia"]),
]


def tag_philosophy_of_mind_components(substrate) -> dict:
    n_added = {"filter_specs": 0, "microtheories": 0}
    for fs in substrate.nodes("FilterSpec"):
        name_lower = str(substrate.node(fs)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in POM_FILTERSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, fs, target):
                        n_added["filter_specs"] += 1
    for mt_name, concept_names in POM_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            target = _find_concept_by_name(substrate, cname)
            if target is not None and _tag(substrate, mt, target):
                n_added["microtheories"] += 1
    return n_added


# =====================================================================
# Audio/music mappings — mapping substrate audio infrastructure to
# audio concepts.
# =====================================================================

AUDIO_MT_MAPPINGS: list[tuple[str, list[str]]] = [
    ("phonology", ["formant", "pitch_perception_models",
                     "vocal_tract_resonance_formants",
                     "categorical_perception"]),
    ("speech_science", ["pitch", "timbre", "formant",
                         "missing_fundamental"]),
    ("speech_development", ["beat_induction",
                             "infant_musicality",
                             "perceptual_narrowing_music"]),
    ("audio_coding_theory", ["sampling", "nyquist_shannon_theorem",
                               "perceptual_coding",
                               "discrete_fourier_transform"]),
    ("causal_attitude_networks", ["tonal_hierarchy",
                                    "consonance",
                                    "dissonance"]),
    ("self_improvement_dynamics", ["musical_expectation",
                                     "tension_resolution_cycle"]),
]

AUDIO_FILTERSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("anticipation",       ["musical_expectation",
                             "huron_itpra"]),
    ("identity_formation", ["rhythmic_entrainment"]),
    ("conflict",           ["dissonance"]),
    ("redundancy",         ["consonance"]),
]


def tag_audio_music_components(substrate) -> dict:
    """Tag substrate components with audio/music concepts."""
    n_added = {"filter_specs": 0, "microtheories": 0}

    for fs in substrate.nodes("FilterSpec"):
        name_lower = str(substrate.node(fs)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in AUDIO_FILTERSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, fs, target):
                        n_added["filter_specs"] += 1

    for mt_name, concept_names in AUDIO_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            target = _find_concept_by_name(substrate, cname)
            if target is not None and _tag(substrate, mt, target):
                n_added["microtheories"] += 1

    return n_added


# =====================================================================
# Psychology mappings — same pattern, different concept space
# =====================================================================

PSY_FILTERSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("frustration",       ["cognitive_dissonance",
                            "expectation_violation"]),
    ("sparse",             ["overgeneralisation"]),
    ("frozen_should_adapt", ["confirmation_bias"]),
    ("drifted_past_anchor", ["accommodation"]),
    ("redundancy",         ["mental_filter"]),
    ("conflict",           ["cognitive_dissonance",
                            "automatic_thoughts"]),
    ("insight",            ["surprise", "expectation_violation"]),
    ("anticipation",       ["catastrophising", "fortune_telling"]),
    ("identity_formation", ["self_concept", "narrative_identity"]),
    ("handler_unread_observations",   ["metacognition_psychological"]),
    ("handler_dormant_theory",        ["metacognition_psychological"]),
    ("handler_undeclared_enactment",  ["metacognition_psychological"]),
]

PSY_ACTIONSPEC_MAPPINGS: list[tuple[str, list[str]]] = [
    ("raise_plasticity",   ["growth_mindset",
                             "critical_period_psychological"]),
    ("prune_mt",            ["extinction_behavioural"]),
    ("beta_reweight",       ["accommodation"]),
    ("extend_quality",      ["cognitive_restructuring"]),
    ("register_handler",    ["assimilation"]),
    ("derive_handler",      ["behavioral_experiments"]),
]

PSY_QUALITY_MAPPINGS: list[tuple[str, list[str]]] = [
    ("separation_of_concerns",   ["categorisation",
                                   "stimulus_discrimination"]),
    ("abstraction_layering",     ["schema",
                                   "concept_formation"]),
    ("introspectability",        ["metacognition_psychological",
                                   "self_concept_clarity"]),
    ("data_drivenness",          ["empiricism"]),
    ("compositional_reuse",      ["schema",
                                   "transfer_of_learning"]),
    ("observation_coverage",     ["selective_attention"]),
]

PSY_MT_MAPPINGS: list[tuple[str, list[str]]] = [
    ("self_improvement_dynamics", ["self_determination_theory",
                                    "intrinsic_motivation",
                                    "growth_mindset"]),
    ("causal_attitude_networks",   ["cognitive_consistency",
                                    "cognitive_dissonance"]),
    ("substrate_architecture_is_human_cognition",
        ["cognitive_architecture", "cognitive_revolution"]),
    ("grounding_theory",           ["piaget_sensorimotor_stage",
                                    "embodied_cognition"]),
    ("model_understanding",        ["theory_of_mind",
                                    "social_cognition"]),
    ("architecture_assessment",    ["metacognition_psychological"]),
    ("architectural_design",       ["problem_solving",
                                    "decision_making"]),
    ("assessment_spans_observation", ["metacognition_psychological",
                                       "feeling_of_knowing"]),
    ("theory_enacts_through_infrastructure",
        ["metacognition_psychological",
         "self_concept_clarity"]),
    ("phonology",                  ["categorical_perception",
                                    "perceptual_narrowing_psychological"]),
    ("speech_science",             ["language", "perception"]),
    ("speech_development",         ["piaget_sensorimotor_stage",
                                    "joint_attention", "fast_mapping"]),
    ("machine_learning",           ["conditioning",
                                    "rescorla_wagner_model"]),
    ("compilers",                  ["chunking", "expertise"]),
    ("self_improvement_loop",      ["self_determination_theory"]),
]


def tag_psychology_components(substrate) -> dict:
    """Tag substrate components with psychology concepts, mirroring
    the neuroscience tagging pattern."""
    n_added = {"filter_specs": 0, "action_specs": 0,
               "qualities": 0, "microtheories": 0}

    # FilterSpecs
    for fs in substrate.nodes("FilterSpec"):
        name_lower = str(substrate.node(fs)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in PSY_FILTERSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, fs, target):
                        n_added["filter_specs"] += 1

    # ActionSpecs
    for ac in substrate.nodes("ActionSpec"):
        name_lower = str(substrate.node(ac)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in PSY_ACTIONSPEC_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, ac, target):
                        n_added["action_specs"] += 1

    # Qualities
    for q in substrate.nodes("ArchitecturalQuality"):
        name_lower = str(substrate.node(q)["attrs"]
                         .get("name", "")).lower()
        for pattern, concept_names in PSY_QUALITY_MAPPINGS:
            if pattern in name_lower:
                for cname in concept_names:
                    target = _find_concept_by_name(substrate, cname)
                    if target is not None \
                            and _tag(substrate, q, target):
                        n_added["qualities"] += 1

    # Microtheories
    for mt_name, concept_names in PSY_MT_MAPPINGS:
        mt = _find_mt_by_name(substrate, mt_name)
        if mt is None:
            continue
        for cname in concept_names:
            target = _find_concept_by_name(substrate, cname)
            if target is not None and _tag(substrate, mt, target):
                n_added["microtheories"] += 1

    return n_added


# --- Query helpers --------------------------------------------------------

def what_does_this_implement(substrate, node) -> list[str]:
    """Walk implements edges from this node; return concept names."""
    out = []
    for target in substrate.neighbours(node, "implements"):
        attrs = substrate.node(target)["attrs"]
        name = str(attrs.get("name", ""))
        if name:
            out.append(name)
    return out


def list_implements_edges(substrate) -> list[dict]:
    """Walk all implements edges; return [(component_type, component_name,
    concept_name)]. Useful for inspection."""
    out = []
    # Walk every node type that could be tagged; check its implements.
    for ntype in ("ArchitectureCortex", "CodeWritingCortex",
                  "SpeechCortex", "FilterSpec", "ActionSpec",
                  "ArchitecturalQuality", "Microtheory"):
        for n in substrate.nodes(ntype):
            n_attrs = substrate.node(n)["attrs"]
            n_name = str(n_attrs.get("name", "")) or ntype
            for target in substrate.neighbours(n, "implements"):
                t_attrs = substrate.node(target)["attrs"]
                concept_name = str(t_attrs.get("name", ""))
                if concept_name:
                    out.append({
                        "component_type": ntype,
                        "component_name": n_name,
                        "neuroscience_concept": concept_name,
                    })
    return out


__all__ = [
    "tag_cortices", "tag_filter_specs", "tag_action_specs",
    "tag_qualities", "tag_microtheories",
    "tag_all_substrate_components",
    "what_does_this_implement", "list_implements_edges",
    "CORTEX_MAPPINGS", "FILTERSPEC_MAPPINGS", "ACTIONSPEC_MAPPINGS",
    "QUALITY_MAPPINGS", "MT_MAPPINGS",
]
