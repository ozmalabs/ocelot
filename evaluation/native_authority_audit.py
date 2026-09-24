"""Static audit of Python cognitive branches against native-cycle authority.

This is an audit aid, not a semantic gate.  Python modules may still contain
legacy orchestration or compatibility paths.  The important property is that
those paths are visible as migration findings rather than being mistaken for
native outcome authority.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


# This is intentionally an exact, small exception list.  A binding is valid
# only when the named function records native trace/rule-readback provenance
# and does not choose a cognitive outcome in Python.  New entries require a
# focused provenance test.
NATIVE_BOUNDARY_BINDINGS = {
    ("domains/achieve_world.py", "decide", "run_rules"):
        {
            "cluster": "achieve_world.decide",
            "provenance": "native_rule_readback:achieve_world",
            "rule": "achieve_world_native_rules",
            "boundary": "native_achieve_decision_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/agnosia_world.py", "name_percept", "run_rules"):
        {
            "cluster": "agnosia_world.percept_decode",
            "provenance": "native_rule_readback:agnosia",
            "rule": "agnosia_native_rules",
            "boundary": "native_agnosia_decode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/allocentric_world_view_ingest.py", "ingest_current_optic_evidence", "run_rules"):
        {
            "cluster": "allocentric_world_view.ingress",
            "provenance": "native_rule_readback:allocentric_view",
            "rule": "allocentric_world_view_native_rules",
            "boundary": "native_allocentric_view_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/bigville_disposition_apply.py", "apply_resident_dispositions", "run_rules"):
        {
            "cluster": "bigville_disposition_apply.settlement",
            "provenance": "native_rule_readback:bigville_dispositions",
            "rule": "bigville_dispositions_native_rules",
            "boundary": "native_bigville_disposition_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/bigville_register_backend.py", "decode_band", "run_rules"):
        {
            "cluster": "bigville_register.decode_band",
            "provenance": "native_rule_readback:bigville_register",
            "rule": "bigville_register_native_rules",
            "boundary": "native_bigville_register_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/marshmallow_world.py", "_chosen_at", "run_rules"):
        {
            "cluster": "marshmallow_world.delay_decision",
            "provenance": "native_rule_readback:marshmallow_delay",
            "rule": "marshmallow_delay_native_rules",
            "boundary": "native_marshmallow_delay_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/falling_world.py", "discover_order", "run_rules"):
        {
            "cluster": "falling_world.order_discovery",
            "provenance": "native_rule_readback:falling_order",
            "rule": "falling_world_native_order_rules",
            "boundary": "native_falling_order_discovery_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/galileo_world.py", "watch_falls", "run_rules"):
        {
            "cluster": "galileo_world.fall_discovery",
            "provenance": "native_rule_readback:galileo_falls",
            "rule": "galileo_fall_native_rules",
            "boundary": "native_galileo_discovery_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/push_world.py", "discover_masses", "run_rules"):
        {
            "cluster": "push_world.mass_discovery",
            "provenance": "native_rule_readback:push_mass",
            "rule": "push_world_native_mass_rules",
            "boundary": "native_push_mass_discovery_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/physics_world.py", "run_world", "run_rules"):
        {
            "cluster": "physics_world.simulation_settlement",
            "provenance": "native_rule_readback:physics_world",
            "rule": "physics_world_native_rules",
            "boundary": "native_physics_simulation_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/physics_world.py", "run_lever", "run_rules"):
        {
            "cluster": "physics_world.simulation_settlement",
            "provenance": "native_rule_readback:physics_world",
            "rule": "physics_world_native_rules",
            "boundary": "native_physics_lever_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/frustration_world.py", "observe", "run_rules"):
        {
            "cluster": "frustration_world.observe",
            "provenance": "native_rule_readback:frustration",
            "rule": "frustration_native_rules",
            "boundary": "native_frustration_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/mood_r1_world.py", "step", "run_rules"):
        {
            "cluster": "mood_r1.step",
            "provenance": "native_rule_readback:mood_r1",
            "rule": "mood_r1_native_rules",
            "boundary": "native_mood_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/harvest_spite_world.py", "step", "run_rules"):
        {
            "cluster": "harvest_spite.decision_settlement",
            "provenance": "native_rule_readback:harvest_spite",
            "rule": "harvest_spite_native_rules",
            "boundary": "native_harvest_spite_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/control_bundle.py", "enact", "run_rules"):
        {
            "cluster": "control_bundle.enactment_settlement",
            "provenance": "native_rule_readback:control_bundle",
            "rule": "control_bundle_native_rules",
            "boundary": "native_control_bundle_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/crossframe_world.py", "run", "run_rules"):
        {
            "cluster": "crossframe_world.identity_settlement",
            "provenance": "native_rule_readback:crossframe_identity",
            "rule": "crossframe_identity_native_rules",
            "boundary": "native_crossframe_identity_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/identity_seam_world.py", "run", "run_rules"):
        {
            "cluster": "identity_seam_world.identity_growth",
            "provenance": "native_rule_readback:identity_seam",
            "rule": "identity_seam_native_rules",
            "boundary": "native_identity_seam_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/verdict_comparator_world.py", "run", "run_rules"):
        {
            "cluster": "verdict_comparator.settlement",
            "provenance": "native_rule_readback:verdict_comparator",
            "rule": "verdict_comparator_native_rules",
            "boundary": "native_verdict_comparator_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/rule_lifter.py", "fire_lifted_rule", "run_rules"):
        {
            "cluster": "rule_lifter.fixpoint_execution",
            "provenance": "native_rule_readback:lifted_rule",
            "rule": "lifted_rule_native_fixpoint",
            "boundary": "native_lifted_rule_fixpoint_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/substrate_extension.py", "_run_item", "run_rules"):
        {
            "cluster": "substrate_extension.pipeline_verification",
            "provenance": "native_rule_readback:substrate_extension_pipeline",
            "rule": "substrate_extension_native_pipeline_rules",
            "boundary": "native_extension_pipeline_verification_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/salient_cache.py", "tick", "run_rules"):
        {
            "cluster": "salient_cache.tick_settlement",
            "provenance": "native_rule_readback:salience_cache",
            "rule": "salience_cache_native_rules",
            "boundary": "native_salience_cache_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/whisper_grounding_guard.py", "infer_embedding", "run_rules"):
        {
            "cluster": "whisper_grounding_guard.inference",
            "provenance": "native_rule_readback:whisper_grounding",
            "rule": "whisper_grounding_native_rules",
            "boundary": "native_whisper_grounding_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_anxiety_world.py", "classify", "run_rules"):
        {
            "cluster": "trait_anxiety.classification",
            "provenance": "native_rule_readback:trait_anxiety",
            "rule": "trait_anxiety_native_rules",
            "boundary": "native_trait_anxiety_classification_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/enigma_solver.py", "graph_crib_admissibility", "run_rules"):
        {
            "cluster": "enigma_solver.crib_admissibility",
            "provenance": "native_rule_readback:enigma_scan",
            "rule": "enigma_crib_admissibility_native_rules",
            "boundary": "native_enigma_admissibility_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/prog_chunk_growth.py", "chunk_pump", "run_rules"):
        {
            "cluster": "prog_chunk_growth.native_pump",
            "provenance": "native_rule_readback:program_chunk_growth",
            "rule": "program_chunk_growth_native_rules",
            "boundary": "native_program_chunk_pump_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "_update_vision_photon_sheet", "run_cognitive_tasks"):
        {
            "cluster": "world_adapter.vision_photon_settlement",
            "provenance": "native_cycle_readback:vision_photon_sheet",
            "rule": "vision_photon_native_task_rules",
            "boundary": "native_vision_photon_task_execution_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "_update_vision_photon_sheet", "run_rules"):
        {
            "cluster": "world_adapter.vision_photon_settlement",
            "provenance": "native_cycle_readback:vision_photon_sheet",
            "rule": "vision_photon_native_task_rules",
            "boundary": "native_vision_photon_rule_settlement_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/two_eye_superres_2d.py", "sample_eye_2d", "run_cognitive_tasks"):
        {
            "cluster": "two_eye_superres_2d.sample_settlement",
            "provenance": "native_cycle_readback:two_eye_superres_2d",
            "rule": "two_eye_superres_2d_native_sampling_rules",
            "boundary": "native_two_eye_2d_sampling_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/two_eye_superres_2d.py", "sample_eye_2d", "run_rules"):
        {
            "cluster": "two_eye_superres_2d.sample_settlement",
            "provenance": "native_cycle_readback:two_eye_superres_2d",
            "rule": "two_eye_superres_2d_native_sampling_rules",
            "boundary": "native_two_eye_2d_sampling_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/vision_graph.py", "_convolve_pair_tasks", "run_cognitive_tasks"):
        {
            "cluster": "vision_graph.convolution_tasks",
            "provenance": "native_cycle_readback:vision_convolution",
            "rule": "vision_convolution_native_tasks",
            "boundary": "native_vision_convolution_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/sensory_field.py", "select_kernels", "run_rules"):
        {
            "cluster": "sensory_field.kernel_selection",
            "provenance": "native_rule_readback:sensory_kernel_selection",
            "rule": "keep_discriminative_kernel",
            "boundary": "native_sensory_kernel_selection_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/sensory_field.py", "sense_discrimination", "run_rules"):
        {
            "cluster": "sensory_field.discrimination",
            "provenance": "native_rule_readback:sensory_discrimination",
            "rule": "keep_discriminative_kernel",
            "boundary": "native_sensory_discrimination_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/feature_field.py", "select_cues", "run_rules"):
        {
            "cluster": "feature_field.cue_selection",
            "provenance": "native_rule_readback:feature_cue_selection",
            "rule": "keep_discriminative_cue",
            "boundary": "native_feature_cue_selection_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/modality_reflex.py", "train", "run_rules"):
        {
            "cluster": "modality_reflex.native_training",
            "provenance": "native_rule_readback:modality_reflex_training",
            "rule": "modality_net_collapse",
            "boundary": "native_modality_training_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/resident_trust.py", "mint_trust_beliefs", "run_rules"):
        {
            "cluster": "resident_trust.belief_settlement",
            "provenance": "native_rule_readback:resident_trust",
            "rule": "resident_trust_native_rules",
            "boundary": "native_trust_belief_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/resident_trust.py", "record_trust_incident", "run_rules"):
        {
            "cluster": "resident_trust.belief_settlement",
            "provenance": "native_rule_readback:resident_trust",
            "rule": "resident_trust_native_rules",
            "boundary": "native_trust_incident_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/self_efficacy.py", "record_self_efficacy_incident", "run_rules"):
        {
            "cluster": "self_efficacy.incident_settlement",
            "provenance": "native_rule_readback:self_efficacy",
            "rule": "self_efficacy_native_rules",
            "boundary": "native_self_efficacy_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/shared_arousal.py", "record_targeted_incident", "run_rules"):
        {
            "cluster": "shared_arousal.target_incident",
            "provenance": "native_rule_readback:shared_arousal",
            "rule": "shared_arousal_native_rules",
            "boundary": "native_shared_arousal_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/envy.py", "record_deservingness_incident", "run_rules"):
        {
            "cluster": "envy.deservingness_settlement",
            "provenance": "native_rule_readback:envy_deservingness",
            "rule": "envy_native_rules",
            "boundary": "native_envy_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/two_eye_superres.py", "sample_eye", "run_cognitive_tasks"):
        {
            "cluster": "two_eye_superres.sample_settlement",
            "provenance": "native_cycle_readback:two_eye_superres",
            "rule": "two_eye_superres_native_sampling_rules",
            "boundary": "native_two_eye_sampling_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/two_eye_superres.py", "sample_eye", "run_rules"):
        {
            "cluster": "two_eye_superres.sample_settlement",
            "provenance": "native_cycle_readback:two_eye_superres",
            "rule": "two_eye_superres_native_sampling_rules",
            "boundary": "native_two_eye_sampling_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/two_eye_superres.py", "fuse", "run_cognitive_tasks"):
        {
            "cluster": "two_eye_superres.fusion_settlement",
            "provenance": "native_rule_readback:two_eye_superres_fusion",
            "rule": "two_eye_superres_native_fusion_rules",
            "boundary": "native_two_eye_fusion_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/two_eye_superres.py", "fuse", "run_rules"):
        {
            "cluster": "two_eye_superres.fusion_settlement",
            "provenance": "native_rule_readback:two_eye_superres_fusion",
            "rule": "two_eye_superres_native_fusion_rules",
            "boundary": "native_two_eye_fusion_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/prog_synthesis.py", "_decode_order", "run_rules"):
        {
            "cluster": "prog_synthesis.order_decode",
            "provenance": "native_rule_readback:program_lattice",
            "rule": "program_synthesis_native_lattice_rules",
            "boundary": "native_program_order_decode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/prog_synthesis.py", "pump", "run_rules"):
        {
            "cluster": "prog_synthesis.fixpoint_pump",
            "provenance": "native_rule_readback:program_synthesis_pump",
            "rule": "program_synthesis_native_rules",
            "boundary": "native_program_synthesis_pump_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/ink_decode.py", "_lattice_partition", "run_rules"):
        {
            "cluster": "ink_decode.lattice_settlement",
            "provenance": "native_rule_readback:ink_lattice",
            "rule": "ink_lattice_native_rules",
            "boundary": "native_ink_lattice_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/ink_decode.py", "_refine_or_note", "run_rules"):
        {
            "cluster": "ink_decode.refinement_settlement",
            "provenance": "native_rule_readback:ink_refinement",
            "rule": "ink_refinement_native_rules",
            "boundary": "native_ink_refinement_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/ink_decode.py", "decode_ink", "run_rules"):
        {
            "cluster": "ink_decode.writer_settlement",
            "provenance": "native_rule_readback:ink_writer",
            "rule": "ink_writer_native_rules",
            "boundary": "native_ink_writer_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/spatial_sense.py", "quanta_flood_step", "run_rules"):
        {
            "cluster": "spatial_sense.quanta_flood",
            "provenance": "native_rule_readback:spatial_sense_flood",
            "rule": "spatial_sense_quanta_flood_rules",
            "boundary": "native_quanta_flood_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/spatial_sense.py", "spatial_sense_step", "run_rules"):
        {
            "cluster": "spatial_sense.navigation_settlement",
            "provenance": "native_rule_readback:spatial_navigation",
            "rule": "spatial_sense_navigation_rules",
            "boundary": "native_spatial_navigation_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/hate_attribution.py", "record_understanding_incident", "run_rules"):
        {
            "cluster": "hate_attribution.understanding_settlement",
            "provenance": "native_rule_readback:hate_understanding",
            "rule": "hate_understanding_native_rules",
            "boundary": "native_hate_understanding_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/hate_attribution.py", "record_hate_incident", "run_rules"):
        {
            "cluster": "hate_attribution.incident_settlement",
            "provenance": "native_rule_readback:hate_attribution_native_rules",
            "rule": "hate_attribution_native_rules",
            "boundary": "native_hate_incident_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/read_method_draft.py", "validate_by_running", "run_rules"):
        {
            "cluster": "read_method_draft.native_validation",
            "provenance": "native_rule_readback:read_method_validation",
            "rule": "read_method_draft_synthesized_rule",
            "boundary": "native_draft_validation_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/can_self_worth_bridge.py", "find_or_build_resident_can", "run_rules"):
        {
            "cluster": "can_self_worth_bridge.resident_settlement",
            "provenance": "native_rule_readback:self_worth_can",
            "rule": "self_worth_can_native_rules",
            "boundary": "native_self_worth_resident_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/can_self_worth_bridge.py", "record_incident_outcome", "run_rules"):
        {
            "cluster": "can_self_worth_bridge.incident_settlement",
            "provenance": "native_rule_readback:self_worth_incident",
            "rule": "self_worth_can_native_rules",
            "boundary": "native_self_worth_incident_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/can_self_worth_bridge.py", "mint_domain_self_worth", "run_rules"):
        {
            "cluster": "can_self_worth_bridge.domain_projection",
            "provenance": "native_rule_readback:self_worth_domain_projection",
            "rule": "self_worth_can_native_rules",
            "boundary": "native_self_worth_domain_projection_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/can_self_worth_bridge.py", "record_self_conscious_consequence", "run_rules"):
        {
            "cluster": "can_self_worth_bridge.consequence_settlement",
            "provenance": "native_rule_readback:self_worth_consequence",
            "rule": "self_worth_can_native_rules",
            "boundary": "native_self_worth_consequence_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/can_self_worth_bridge.py", "record_peer_observation", "run_rules"):
        {
            "cluster": "can_self_worth_bridge.peer_comparison",
            "provenance": "native_rule_readback:self_worth_peer_comparison",
            "rule": "self_worth_peer_comparison_native_rules",
            "boundary": "native_self_worth_peer_comparison_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_modulator_bridge.py", "ensure_modulator_state", "run_rules"):
        {
            "cluster": "trait_modulator_bridge.state_initialization",
            "provenance": "native_rule_readback:trait_modulator_state",
            "rule": "trait_modulator_native_initialization_rules",
            "boundary": "native_trait_modulator_initialization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_modulator_bridge.py", "sync_traits_to_modulator", "run_rules"):
        {
            "cluster": "trait_modulator_bridge.trait_to_modulator",
            "provenance": "native_rule_readback:trait_modulator_bias",
            "rule": "trait_modulator_native_bias_rules",
            "boundary": "native_trait_bias_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_modulator_bridge.py", "crystallise_traits_from_modulator", "run_rules"):
        {
            "cluster": "trait_modulator_bridge.modulator_to_trait",
            "provenance": "native_rule_readback:trait_modulator_trait_crystallization",
            "rule": "trait_modulator_native_trait_rules",
            "boundary": "native_trait_crystallization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_modulator_bridge.py", "_batched_relax", "run_rules"):
        {
            "cluster": "trait_modulator_bridge.batched_relaxation",
            "provenance": "native_rule_readback:trait_modulator_batched_relaxation",
            "rule": "trait_modulator_native_trait_rules",
            "boundary": "native_batched_trait_relaxation_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_modulator_bridge.py", "drive_homeostasis_step", "run_rules"):
        {
            "cluster": "trait_modulator_bridge.drive_homeostasis",
            "provenance": "native_rule_readback:trait_modulator_homeostasis",
            "rule": "trait_modulator_native_homeostasis_rules",
            "boundary": "native_drive_homeostasis_refresh_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/trait_modulator_bridge.py", "personality_homeostasis_step", "run_rules"):
        {
            "cluster": "trait_modulator_bridge.personality_homeostasis",
            "provenance": "native_rule_readback:trait_modulator_homeostasis",
            "rule": "trait_modulator_native_homeostasis_rules",
            "boundary": "native_personality_homeostasis_refresh_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/frame_weights.py", "update_quantum_frame", "run_rules"):
        {
            "cluster": "frame_weights.quantum_update",
            "provenance": "native_rule_readback:frame_weights",
            "rule": "frame_weights_native_update_rules",
            "boundary": "native_frame_weight_update_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/frame_weights.py", "pooled_reliability", "run_rules"):
        {
            "cluster": "frame_weights.pooled_update",
            "provenance": "native_rule_readback:frame_weights_pool",
            "rule": "frame_weights_native_pool_rules",
            "boundary": "native_frame_pool_update_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/disposition.py", "relax_trait", "run_rules"):
        {
            "cluster": "disposition.trait_settlement",
            "provenance": "native_rule_readback:trait_dynamics",
            "rule": "disposition_trait_native_rules",
            "boundary": "native_trait_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/disposition.py", "pull_trait", "run_rules"):
        {
            "cluster": "disposition.trait_settlement",
            "provenance": "native_rule_readback:trait_dynamics",
            "rule": "disposition_trait_native_rules",
            "boundary": "native_trait_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/disposition.py", "crystallize_trait", "run_rules"):
        {
            "cluster": "disposition.trait_settlement",
            "provenance": "native_rule_readback:trait_dynamics",
            "rule": "disposition_trait_native_rules",
            "boundary": "native_trait_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/spatial_belief.py", "ingest", "run_rules"):
        {
            "cluster": "spatial_belief.observation_settlement",
            "provenance": "native_rule_readback:spatial_belief",
            "rule": "spatial_belief_native_settlement_rules",
            "boundary": "native_spatial_belief_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/equation.py", "solve_for", "run_rules"):
        {
            "cluster": "equation.solve_for",
            "provenance": "native_rule_readback:equation_isolation",
            "rule": "equation_isolation_native_rules",
            "boundary": "native_equation_isolation_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/rule_dispute_full_pipeline.py", "run_rule_dispute", "run_rules"):
        {
            "cluster": "rule_dispute_full_pipeline.dispute_settlement",
            "provenance": "native_rule_readback:rule_dispute_pipeline",
            "rule": "rule_dispute_full_pipeline_native_rules",
            "boundary": "native_dispute_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/meta_shape.py", "observe", "run_rules"):
        {
            "cluster": "meta_shape.observation_growth",
            "provenance": "native_rule_readback:meta_shape_growth",
            "rule": "meta_shape_growth_native_rules",
            "boundary": "native_meta_shape_growth_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/problem_shape.py", "observe", "run_rules"):
        {
            "cluster": "problem_shape.observation_decode",
            "provenance": "native_rule_readback:problem_shape",
            "rule": "problem_shape_growth_native_decode",
            "boundary": "native_problem_shape_decode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/fovea_bridge.py", "resolve_fovea", "run_rules"):
        {
            "cluster": "fovea_bridge.salience_selection",
            "provenance": "native_rule_readback:fovea_salience",
            "rule": "fovea_salience_argmin_unique",
            "boundary": "native_fovea_selection_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/upload_text_read.py", "pump_upload_text_read", "cognitive_tick"):
        {
            "cluster": "upload_text_read.native_cognitive_pump",
            "provenance": "native_cycle_readback:cognitive_legacy",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "delegation_to_bound_native_cycle_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/prosody_generation.py", "substrate_affect_coord", "run_rules"):
        {
            "cluster": "prosody_generation.affect_coordinate",
            "provenance": "native_rule_readback:modulator_affect",
            "rule": "mod_valence_mod_arousal_mod_arousal_phasic",
            "boundary": "native_affect_coordinate_readback_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/fallback_readout.py", "mint_report", "run_rules"):
        {
            "cluster": "fallback_readout.report_classification",
            "provenance": "native_rule_readback:fallback_vocabulary",
            "rule": "fallback_vocabulary_native_classification",
            "boundary": "native_fallback_classification_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/solver_dispatch.py", "grow_can_network_from_text", "run_rules"):
        {
            "cluster": "solver_dispatch.can_network_settlement",
            "provenance": "native_rule_readback:solver_can_network",
            "rule": "solver_can_native_rules",
            "boundary": "native_can_network_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/solver_dispatch.py", "_drive_to_resolution", "run_rules"):
        {
            "cluster": "solver_dispatch.goal_resolution_settlement",
            "provenance": "native_rule_readback:solver_dispatch_resolution",
            "rule": "solver_dispatch_native_resolution_rules",
            "boundary": "native_goal_resolution_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "_bind_live_goals_and_deliberation", "run_rules"):
        {
            "cluster": "world_adapter.live_deliberation_bridge",
            "provenance": "native_rule_readback:phase4a_live_deliberation",
            "rule": "conversation_deliberation_phase4a_native_settlement_v1",
            "boundary": "graph_evidence_materialization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "comprehend", "run_rules"):
        {
            "cluster": "world_adapter.comprehension_rule_execution",
            "provenance": "native_rule_readback:communication_comprehension",
            "rule": "communication_comprehension_native_rule_set_v1",
            "boundary": "graph_rule_execution_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "tick", "run_cycle"):
        {
            "cluster": "world_adapter.native_default_cycle",
            "provenance": "native_cycle_readback:default_schedule",
            "rule": "native_cycle_plan_default_v1",
            "boundary": "native_schedule_execution_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "dual_process_tick", "run_cycle"):
        {
            "cluster": "world_adapter.native_dual_process_cycle",
            "provenance": "native_cycle_readback:dual_process_schedule",
            "rule": "native_cycle_plan_dual_process_v1",
            "boundary": "native_schedule_execution_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/question_driver.py", "_native_deliberation_cycle", "run_cycle"):
        {
            "cluster": "question_driver.deliberation_pump",
            "provenance": "native_trace:question_driver_deliberation",
            "rule": "question_driver_deliberation_native_trace_v1",
        },
    ("domains/comprehend_text.py", "_classify_kind_rules", "run_rules"):
        {
            "cluster": "comprehend_text.speech_act_classification",
            "provenance": "native_rule_readback:speech_act_classification",
            "rule": "comprehend_text_speech_act_native_readback_v1",
        },
    ("domains/conversation_action.py", "attach_scene", "run_rules"):
        {
            "cluster": "conversation_action.scene_materialization",
            "provenance": "native_rule_readback:scene_percept_materialization",
            "rule": "conversation_action_scene_percept_materialization_v1",
        },
    ("domains/conversation_action.py", "_act_describe_scene", "run_rules"):
        {
            "cluster": "conversation_action.describe_scene_goal_readback",
            "provenance": "native_rule_readback:describe_scene_goal",
            "rule": "conversation_action_describe_scene_goal_v1",
            "boundary": "graph_evidence_materialization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/actor_goals.py", "annotate_utterance_phrases", "run_rules"):
        {
            "cluster": "actor_goals.utterance_phrase_annotation",
            "provenance": "native_rule_readback:utterance_phrase_annotation",
            "rule": "actor_goals_utterance_phrase_annotation_v1",
        },
    ("substrate/world_adapter.py", "ingest_semantic_event", "run_rules"):
        {
            "cluster": "world_adapter.neutral_semantic_event_ingress",
            "provenance": "native_rule_readback:semantic_event_arbitration",
            "rule": "communication_intent_arbitration",
            "boundary": "mechanical_evidence_materialization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/conceptualizer.py", "run_pipeline", "run_rules"):
        {
            "cluster": "conceptualizer.native_pipeline",
            "provenance": "native_rule_readback:conceptualizer_pipeline",
            "rule": "conceptualizer_authored_rule_set",
            "boundary": "native_rule_execution_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/curiosity_topic_ingest.py", "maintain_topic_interest", "run_rules"):
        {
            "cluster": "curiosity_topic_selection.native_settlement",
            "provenance": "native_rule_readback:curiosity_topic_selection",
            "rule": "learning_progress_curiosity_and_topic_selection",
            "boundary": "native_gap_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "cognitive_tick", "run_cycle"):
        {
            "cluster": "world_adapter.cognitive_cycle",
            "provenance": "native_cycle_readback:cognitive_legacy",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "native_schedule_execution_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "master_tick", "run_cycle"):
        {
            "cluster": "world_adapter.master_cycle",
            "provenance": "native_cycle_readback:master_legacy",
            "rule": "master_legacy_native_schedule",
            "boundary": "native_schedule_execution_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "live_examined", "cognitive_tick"):
        {
            "cluster": "world_adapter.live_examined_native_cycle_delegation",
            "provenance": "native_cycle_readback:cognitive_legacy",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "delegation_to_bound_native_cycle_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("substrate/world_adapter.py", "live", "cognitive_tick"):
        {
            "cluster": "world_adapter.live_native_cycle_delegation",
            "provenance": "native_cycle_readback:cognitive_legacy",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "delegation_to_bound_native_cycle_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/actor_goals.py", "annotate_actor_action", "run_rules"):
        {
            "cluster": "actor_goals.actor_action_settlement",
            "provenance": "native_rule_readback:actor_goal_settlement",
            "rule": "actor_goals_native_rule_set",
            "boundary": "native_actor_goal_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/actor_goals.py", "annotate_disclaimer_candidates", "run_rules"):
        {
            "cluster": "actor_goals.disclaimer_settlement",
            "provenance": "native_rule_readback:disclaimer_codebook",
            "rule": "actor_goals_disclaimer_codebook_rules",
            "boundary": "native_disclaimer_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/actor_goals.py", "annotate_action_pairs", "run_rules"):
        {
            "cluster": "actor_goals.action_pair_settlement",
            "provenance": "native_rule_readback:action_pair_codebook",
            "rule": "actor_goals_action_pair_codebook_rules",
            "boundary": "native_action_pair_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/actor_goals.py", "assess_epistemic_lean", "run_rules"):
        {
            "cluster": "actor_goals.epistemic_assessment",
            "provenance": "native_rule_readback:epistemic_assessment",
            "rule": "epistemic_detection_and_combine_rule_set",
            "boundary": "native_epistemic_assessment_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/actor_goals.py", "_author_layer_rule", "run_rules"):
        {
            "cluster": "actor_goals.authored_rule_execution",
            "provenance": "native_rule_readback:actor_goal_authored_rule",
            "rule": "agent_authored_actor_goal_rule",
            "boundary": "native_authored_rule_execution_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/meaning_inference.py", "annotate_predication_slots", "run_rules"):
        {
            "cluster": "meaning_inference.predication_slot_settlement",
            "provenance": "native_rule_readback:selectional_inference",
            "rule": "meaning_inference_selectional_rules",
            "boundary": "native_selectional_inference_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/meaning_inference.py", "annotate_predication_facts", "run_rules"):
        {
            "cluster": "meaning_inference.predication_fact_settlement",
            "provenance": "native_rule_readback:definitional_inference",
            "rule": "meaning_inference_definitional_rules",
            "boundary": "native_definitional_inference_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/meaning_inference.py", "annotate_affix_candidates", "run_rules"):
        {
            "cluster": "meaning_inference.morphology_settlement",
            "provenance": "native_rule_readback:morphological_inference",
            "rule": "meaning_inference_morphology_rules",
            "boundary": "native_morphological_inference_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/meaning_inference.py", "annotate_relational_signatures", "run_rules"):
        {
            "cluster": "meaning_inference.relational_signature_settlement",
            "provenance": "native_rule_readback:structural_analogy",
            "rule": "meaning_inference_structural_analogy_rules",
            "boundary": "native_structural_analogy_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/recount_faculty.py", "project_read_scene", "run_rules"):
        {
            "cluster": "recount_faculty.read_scene_settlement",
            "provenance": "native_rule_readback:recount_realization",
            "rule": "recount_realization_and_fluency_rules",
            "boundary": "native_recount_realization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/media_analysis.py", "annotate_passive_predication", "run_rules"):
        {
            "cluster": "media_analysis.passive_settlement",
            "provenance": "native_rule_readback:passive_analysis",
            "rule": "media_analysis_passive_rules",
            "boundary": "native_passive_analysis_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/media_analysis.py", "annotate_intent_signals", "run_rules"):
        {
            "cluster": "media_analysis.intent_signal_settlement",
            "provenance": "native_rule_readback:intent_signal_analysis",
            "rule": "media_analysis_intent_signal_rules",
            "boundary": "native_intent_signal_analysis_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/media_analysis.py", "annotate_relational_noun", "run_rules"):
        {
            "cluster": "media_analysis.relational_noun_settlement",
            "provenance": "native_rule_readback:relational_noun_analysis",
            "rule": "media_analysis_relational_noun_rules",
            "boundary": "native_relational_noun_analysis_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/recount_faculty.py", "recount_what_read", "run_rules"):
        {
            "cluster": "recount_faculty.recount_reasoning_settlement",
            "provenance": "native_rule_readback:recount_reasoning",
            "rule": "recount_faculty_reasoning_rules",
            "boundary": "native_recount_reasoning_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/recount_faculty.py", "analyse_what_read", "run_rules"):
        {
            "cluster": "recount_faculty.analysis_reasoning_settlement",
            "provenance": "native_rule_readback:recount_analysis_reasoning",
            "rule": "recount_analysis_reasoning_rules",
            "boundary": "native_recount_analysis_reasoning_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/recount_faculty.py", "project_analysis_scene", "run_rules"):
        {
            "cluster": "recount_faculty.analysis_scene_settlement",
            "provenance": "native_rule_readback:recount_analysis_scene",
            "rule": "recount_analysis_realization_rules",
            "boundary": "native_recount_analysis_scene_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/conceptualizer.py", "scan_and_monitor", "run_rules"):
        {
            "cluster": "conceptualizer.monitor_candidate_settlement",
            "provenance": "native_rule_readback:conceptualizer_candidate_commit",
            "rule": "conceptualizer_output_candidate_commit",
            "boundary": "native_output_candidate_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/information_commitment.py", "assess", "run_rules"):
        {
            "cluster": "information_commitment.native_decision_settlement",
            "provenance": "native_rule_readback:information_commitment",
            "rule": "ic_gate_manifold_projection",
            "boundary": "native_commitment_decision_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/situation_model_reader.py", "ingest_predication", "run_rules"):
        {
            "cluster": "situation_model_reader.predication_settlement",
            "provenance": "native_rule_readback:situation_model",
            "rule": "situation_model_native_fixpoint",
            "boundary": "native_situation_model_fixpoint_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/inference_generation.py", "_mint_part_of", "run_rules"):
        {
            "cluster": "inference_generation.part_of_settlement",
            "provenance": "native_rule_readback:inference_generation",
            "rule": "inference_generation_native_fixpoint",
            "boundary": "native_inference_fixpoint_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/cognitive_disambiguation.py", "coherence_check", "run_rules"):
        {
            "cluster": "cognitive_disambiguation.coherence_settlement",
            "provenance": "native_rule_readback:coherence_check",
            "rule": "coerce_role_named_after",
            "boundary": "native_coherence_redecode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/cognitive_disambiguation.py", "metonymic_redecode", "run_rules"):
        {
            "cluster": "cognitive_disambiguation.metonymic_settlement",
            "provenance": "native_rule_readback:metonymic_redecode",
            "rule": "coerce_theme_and_agent",
            "boundary": "native_metonymic_redecode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/reflective_faculty.py", "induce_concern", "run_rules"):
        {
            "cluster": "reflective_faculty.concern_decode_settlement",
            "provenance": "native_rule_readback:shape_decode_loop",
            "rule": "shape_decode_loop",
            "boundary": "native_concern_decode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/reflective_faculty.py", "check_new_relation_cue_roles", "run_rules"):
        {
            "cluster": "reflective_faculty.relation_cue_settlement",
            "provenance": "native_rule_readback:argument_role_vocabulary",
            "rule": "argument_role_vocabulary",
            "boundary": "native_relation_role_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/reflective_faculty.py", "record_correspondence", "run_rules"):
        {
            "cluster": "reflective_faculty.correspondence_settlement",
            "provenance": "native_rule_readback:blob_edge_correspondence",
            "rule": "blob_edge_correspondence",
            "boundary": "native_correspondence_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/reading_drive.py", "_tick_reading", "cognitive_tick"):
        {
            "cluster": "reading_drive.native_cognitive_tick_delegation",
            "provenance": "native_cycle_readback:reading_drive",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "delegation_to_bound_native_cycle_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/cognitive_rule_frames.py", "read_rule_document", "run_rules"):
        {
            "cluster": "cognitive_rule_frames.document_settlement",
            "provenance": "native_rule_readback:cognitive_rule_frames",
            "rule": "cognitive_rule_frames_document_rules",
            "boundary": "native_rule_frame_document_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/cognitive_rule_frames.py", "observe_situation", "run_rules"):
        {
            "cluster": "cognitive_rule_frames.observation_settlement",
            "provenance": "native_rule_readback:cognitive_rule_frames",
            "rule": "cognitive_rule_frames_observation_rules",
            "boundary": "native_rule_frame_observation_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/cognitive_rule_frames.py", "commit_prediction", "run_rules"):
        {
            "cluster": "cognitive_rule_frames.commitment_settlement",
            "provenance": "native_rule_readback:cognitive_rule_frames",
            "rule": "cognitive_rule_frames_commitment_rules",
            "boundary": "native_rule_frame_commitment_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/cognitive_rule_frames.py", "draft_document", "run_rules"):
        {
            "cluster": "cognitive_rule_frames.draft_settlement",
            "provenance": "native_rule_readback:cognitive_rule_frames",
            "rule": "cognitive_rule_frames_draft_rules",
            "boundary": "native_rule_frame_draft_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/capability_graph.py", "settle", "run_rules"):
        {
            "cluster": "capability_graph.fixpoint_settlement",
            "provenance": "native_rule_readback:capability_graph",
            "rule": "capability_graph_native_fixpoint",
            "boundary": "native_capability_fixpoint_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/autonomous_discovery.py", "settle_native", "run_rules"):
        {
            "cluster": "autonomous_discovery.native_settlement",
            "provenance": "native_rule_readback:autonomous_discovery",
            "rule": "autonomous_discovery_native_rules",
            "boundary": "native_discovery_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/analogical_thinking.py", "record_pair_correspondence", "run_rules"):
        {
            "cluster": "analogical_thinking.pair_settlement",
            "provenance": "native_rule_readback:analogical_pair",
            "rule": "blob_mint_blob_recognize_blob_no_collapse",
            "boundary": "native_analogical_pair_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/analogical_thinking.py", "record_directional_correspondence", "run_rules"):
        {
            "cluster": "analogical_thinking.directional_settlement",
            "provenance": "native_rule_readback:directional_correspondence",
            "rule": "directional_correspondence_rules",
            "boundary": "native_directional_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/analogical_thinking.py", "_legacy_find_analogies", "run_rules"):
        {
            "cluster": "analogical_thinking.legacy_safety_settlement",
            "provenance": "native_rule_readback:analogical_legacy_safety",
            "rule": "analogical_native_rules",
            "boundary": "native_idempotent_safety_pass_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/procedural_reader.py", "_referent_crosscheck", "run_rules"):
        {
            "cluster": "procedural_reader.referent_crosscheck",
            "provenance": "native_rule_readback:procedural_referent",
            "rule": "procedural_referent_rules",
            "boundary": "native_procedural_referent_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/analogy_search.py", "observe", "run_rules"):
        {
            "cluster": "analogy_search.observe_settlement",
            "provenance": "native_rule_readback:analogy_search",
            "rule": "analogy_search_rules",
            "boundary": "native_analogy_observation_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/analogy_search.py", "crystallize", "run_rules"):
        {
            "cluster": "analogy_search.crystallize_settlement",
            "provenance": "native_rule_readback:analogy_crystallization",
            "rule": "can_native_identity_field_feedback",
            "boundary": "native_analogy_crystallization_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/predictive_reading.py", "read_arc_predictively", "cognitive_tick"):
        {
            "cluster": "predictive_reading.predictive_cycle_delegation",
            "provenance": "native_cycle_readback:predictive_reading",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "delegation_to_bound_native_cycle_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/predictive_reading.py", "read_arc_with_dwell", "cognitive_tick"):
        {
            "cluster": "predictive_reading.dwell_cycle_delegation",
            "provenance": "native_cycle_readback:predictive_reading_dwell",
            "rule": "cognitive_legacy_native_schedule",
            "boundary": "delegation_to_bound_native_cycle_only",
            "outcome_source": "native_cycle_readback",
            "python_outcome_selection": False,
        },
    ("domains/cross_text_prior.py", "extend_on_residual", "run_rules"):
        {
            "cluster": "cross_text_prior.residual_redecode_settlement",
            "provenance": "native_rule_readback:cross_text_prior",
            "rule": "sd_redecode",
            "boundary": "native_residual_redecode_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/reasoning_can_bridge.py", "_run_correspondence", "run_rules"):
        {
            "cluster": "reasoning_can_bridge.correspondence_settlement",
            "provenance": "native_rule_readback:reasoning_can_bridge",
            "rule": "reasoning_can_correspondence_rules",
            "boundary": "native_reasoning_correspondence_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/ast_to_rule.py", "expr_term", "run_rules"):
        {
            "cluster": "ast_to_rule.expression_settlement",
            "provenance": "native_rule_readback:ast_to_term",
            "rule": "ast_to_term_rules",
            "boundary": "native_ast_expression_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/ast_to_rule.py", "body_term", "run_rules"):
        {
            "cluster": "ast_to_rule.body_settlement",
            "provenance": "native_rule_readback:ast_to_term",
            "rule": "ast_to_term_rules",
            "boundary": "native_ast_body_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/faculty_autogenesis.py", "pump", "run_rules"):
        {
            "cluster": "faculty_autogenesis.discovery_settlement",
            "provenance": "native_rule_readback:faculty_autogenesis",
            "rule": "faculty_autogenesis_rules",
            "boundary": "native_faculty_autogenesis_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/minting_train_of_thought.py", "run_minting_train_of_thought", "run_rules"):
        {
            "cluster": "minting_train_of_thought.segment_settlement",
            "provenance": "native_rule_readback:minting_train",
            "rule": "minting_train_native_rules",
            "boundary": "native_minting_segment_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/harvest_world.py", "__init__", "run_rules"):
        {
            "cluster": "harvest_world.initial_native_settlement",
            "provenance": "native_rule_readback:harvest_world_init",
            "rule": "harvest_commons_native_rules",
            "boundary": "delegation_to_native_harvest_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/harvest_world.py", "step", "run_rules"):
        {
            "cluster": "harvest_world.tick_settlement",
            "provenance": "native_rule_readback:harvest_world_step",
            "rule": "harvest_commons_native_rules",
            "boundary": "delegation_to_native_harvest_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/invariant_comparator_world.py", "run", "run_rules"):
        {
            "cluster": "invariant_comparator.settlement",
            "provenance": "native_rule_readback:invariant_comparator",
            "rule": "vision_invariant_comparator_native_rules",
            "boundary": "delegation_to_native_invariant_comparison_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_allo_surface_ingest.py", "accumulate", "run_rules"):
        {
            "cluster": "doom_allocentric_surface.accumulation",
            "provenance": "native_rule_readback:doom_allocentric_surface",
            "rule": "doom_allocentric_surface_native_rules",
            "boundary": "delegation_to_native_allocentric_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_dual_process_ingest.py", "deliberate", "run_rules"):
        {
            "cluster": "doom_dual_process.deliberation_settlement",
            "provenance": "native_rule_readback:doom_dual_process",
            "rule": "doom_dual_process_native_rules",
            "boundary": "delegation_to_native_dual_process_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_emotion_narration_ingest.py", "feed_and_settle", "run_rules"):
        {
            "cluster": "doom_emotion_narration.settlement",
            "provenance": "native_rule_readback:doom_emotion_narration",
            "rule": "doom_emotion_narration_native_rules",
            "boundary": "delegation_to_native_emotion_narration_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_map_ingest.py", "accumulate", "run_rules"):
        {
            "cluster": "doom_map.accumulation_and_typing",
            "provenance": "native_rule_readback:doom_map",
            "rule": "doom_map_native_rules",
            "boundary": "delegation_to_native_map_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_operate.py", "step", "run_rules"):
        {
            "cluster": "doom_operate.motor_settlement",
            "provenance": "native_rule_readback:doom_operate",
            "rule": "doom_operate_native_rules",
            "boundary": "delegation_to_native_motor_settlement_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_pattern_eye.py", "recognise", "run_rules"):
        {
            "cluster": "doom_pattern_eye.recognition",
            "provenance": "native_rule_readback:doom_pattern_eye",
            "rule": "doom_pattern_eye_native_rules",
            "boundary": "delegation_to_native_pattern_recognition_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
    ("domains/doom_pattern_eye.py", "recognise_texture", "run_rules"):
        {
            "cluster": "doom_pattern_eye.texture_recognition",
            "provenance": "native_rule_readback:doom_pattern_eye_texture",
            "rule": "doom_pattern_eye_texture_native_rules",
            "boundary": "delegation_to_native_texture_recognition_only",
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        },
}


class _CognitiveCallVisitor(ast.NodeVisitor):
    """Collect only unbound calls; retain exact native-bound calls separately."""

    _CALL_NAMES = {"run_cycle", "run_rules", "cognitive_tick", "run_cognitive_tasks"}

    def __init__(self, *, relative_file: str):
        self.relative_file = relative_file
        self.findings: list[dict[str, Any]] = []
        self.bound_calls: list[dict[str, Any]] = []
        self._functions: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._functions.append(node.name)
        self.generic_visit(node)
        self._functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        target = node.func
        name = target.attr if isinstance(target, ast.Attribute) else (
            target.id if isinstance(target, ast.Name) else ""
        )
        if name in self._CALL_NAMES:
            function = self._functions[-1] if self._functions else "<module>"
            binding = NATIVE_BOUNDARY_BINDINGS.get(
                (self.relative_file, function, name))
            record = {
                "file": self.relative_file,
                "line": int(getattr(node, "lineno", 0)),
                "kind": "python_cycle_or_task_call",
                "call": name,
                "function": function,
            }
            if binding is None:
                record["authority"] = "requires_native_boundary_review"
                self.findings.append(record)
            else:
                record.update({
                    "authority": "native_graph_bound",
                    "cluster": binding["cluster"],
                    "provenance": binding["provenance"],
                    "exception_rule": binding["rule"],
                })
                for key in (
                    "boundary", "outcome_source", "python_outcome_selection",
                ):
                    if key in binding:
                        record[key] = binding[key]
                self.bound_calls.append(record)
        self.generic_visit(node)


def audit_python_cognitive_branches(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root)
    findings: list[dict[str, Any]] = []
    bound_calls: list[dict[str, Any]] = []
    files_scanned = 0
    # The live adapter is part of this authority surface, but unrelated
    # substrate implementation files remain outside this Python-branch debt
    # report.  The exact binding above keeps this reviewed native boundary
    # visible as provenance rather than silently treating it as Python policy.
    paths = list((base / "domains").glob("*.py"))
    world_adapter = base / "substrate" / "world_adapter.py"
    if world_adapter.exists():
        paths.append(world_adapter)
    for path in sorted(paths):
        files_scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            findings.append({"file": str(path), "line": 0, "kind": "unreadable", "detail": str(exc)})
            continue
        relative_file = path.relative_to(base).as_posix()
        visitor = _CognitiveCallVisitor(relative_file=relative_file)
        visitor.visit(tree)
        findings.extend(visitor.findings)
        bound_calls.extend(visitor.bound_calls)
    return {
        "schema": "native-authority-python-branch-audit-v2",
        "files_scanned": files_scanned,
        "findings": findings,
        "finding_count": len(findings),
        "bound_calls": bound_calls,
        "bound_count": len(bound_calls),
        "total_call_count": len(findings) + len(bound_calls),
        "status": "review_required" if findings else "clean",
        "interpretation": (
            "Findings identify Python orchestration/cycle calls for migration review; "
            "exactly listed native-bound calls carry trace provenance and are not "
            "treated as unreviewed debt."
        ),
    }
