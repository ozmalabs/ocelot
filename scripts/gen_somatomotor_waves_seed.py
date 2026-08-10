#!/usr/bin/env python3
"""Generate integer-native spontaneous activity over an arbitrary body graph."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (  # noqa: E402
    A,
    AO,
    And,
    Argmin,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    If,
    L,
    Lt,
    Max,
    Minus,
    Neg,
    Neighbours,
    Not,
    Or,
    PI0,
    Plus,
    SetT,
    T,
    V,
)
from scripts.gen_embodied_development_seed import (  # noqa: E402
    capability_success,
)


P0 = PI0


def Argmax(source, var_name, value, default):
    return {
        "type": "Argmax",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def cells(field="field"):
    return Neighbours(field, "has_somatomotor_wave_cell")


def current_active_cells(field="field"):
    return Filter(
        cells(field),
        "active_cell",
        And(
            Eq(A("active_cell", "state"), L("active")),
            Not(Lt(
                P0("active_cell", "active_until"),
                P0(field, "current_epoch"),
            )),
        ),
    )


def rested_cells(field="field"):
    return Filter(
        cells(field),
        "rested_cell",
        Eq(A("rested_cell", "state"), L("rested")),
    )


def cell_for_effector(effector_var: str, field="field"):
    return Filter(
        cells(field),
        "candidate_cell",
        Exists(
            Neighbours("candidate_cell", "represents_embodied_effector"),
            "represented_effector",
            Eq(V("represented_effector"), V(effector_var)),
        ),
    )


def channel_effectors(effector="effector", topology="topology"):
    return Filter(
        Neighbours(topology, "has_embodied_effector"),
        "channel_peer",
        Eq(
            P0("channel_peer", "channel_ordinal"),
            P0(effector, "channel_ordinal"),
        ),
    )


def known_coupling(source="source_cell", target="target_cell"):
    return Filter(
        Neighbours(source, "has_somatomotor_wave_coupling"),
        "known_coupling",
        Exists(
            Neighbours("known_coupling", "targets_somatomotor_wave_cell"),
            "known_target",
            Eq(V("known_target"), V(target)),
        ),
    )


def coupling_rank(coupling="coupling"):
    return Plus(
        P0(coupling, "strength"),
        P0(coupling, "warm_prior_rank"),
    )


def cell_warm_ignition_rank(cell="cell"):
    warm = Filter(
        Neighbours(cell, "has_somatomotor_wave_coupling"),
        "warm_ignition_coupling",
        Gt(P0("warm_ignition_coupling", "warm_prior_rank"), L(0)),
    )
    winner = Argmax(
        warm,
        "ranked_ignition_coupling",
        P0("ranked_ignition_coupling", "warm_prior_rank"),
        V(cell),
    )
    return If(
        Gt(Count(warm), L(0)),
        AO(winner, "warm_prior_rank"),
        L(0),
    )


def stronger_available_coupling():
    return Filter(
        Neighbours("source", "has_somatomotor_wave_coupling"),
        "stronger_coupling",
        And(
            Gt(coupling_rank("stronger_coupling"), coupling_rank()),
            Gt(P0("stronger_coupling", "strength"), L(0)),
            Exists(
                Neighbours(
                    "stronger_coupling",
                    "targets_somatomotor_wave_cell",
                ),
                "stronger_target",
                Eq(A("stronger_target", "state"), L("rested")),
            ),
        ),
    )


def coupling_memory_shape(memory="memory", field="covered_count"):
    return {
        "type": "ShapeDecode",
        "goal": A("development", "body_capability_signature"),
        "codebook_type": "SomatomotorCouplingMemory",
        "codebook_scope": SetT(A(memory, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def coupling_memory_matches_relation(memory="memory"):
    relation_matches = tuple(
        Eq(P0(memory, field), P0("relation", field))
        for field in (
            "same_command_channel",
            "declared_hard_coupling",
            "mechanical_path_known",
            "mechanical_path_length",
            "same_mount",
            "command_polarity_product",
        )
    )
    effector_matches = tuple(
        Eq(
            P0(memory, f"{role}_{field}"),
            P0(f"{role}_effector", field),
        )
        for role in ("source", "target")
        for field in (
            "mount_depth",
            "mount_degree",
            "axis_x_class",
            "axis_y_class",
            "axis_z_class",
        )
    )
    return And(*(relation_matches + effector_matches))


def coupling_memory_candidates():
    return Filter(
        Neighbours("agent", "has_somatomotor_coupling_memory"),
        "memory_candidate",
        And(
            coupling_memory_matches_relation("memory_candidate"),
            Gt(
                Minus(
                    P0("memory_candidate", "productive_count"),
                    P0("memory_candidate", "unproductive_count"),
                ),
                L(0),
            ),
            Gt(
                coupling_memory_shape("memory_candidate", "covered_count"),
                Count(coupling_memory_shape("memory_candidate", "residual")),
            ),
            Not(Eq(
                A("memory_candidate", "signature"),
                A("development", "body_capability_signature"),
            )),
        ),
    )


def floor_development_active():
    return And(
        Eq(P0("episode", "somatomotor_wave_enabled"), L(1)),
        Eq(P0("development", "development_learning_active"), L(1)),
        Eq(A("capability", "developmental_ecology"), L("floor")),
        Eq(P0("episode", "sensorimotor_interrupt_required"), L(0)),
        Eq(P0("episode", "reset_requested"), L(0)),
    )


def unexposed_scaffold_cells():
    return Filter(
        cells(),
        "unexposed_scaffold_cell",
        Eq(P0("unexposed_scaffold_cell", "passive_contingent_count"), L(0)),
    )


def Abs(value):
    return Max(value, Neg(value))


def productive_receipt(receipt="receipt"):
    return Or(
        Eq(P0(receipt, "development_configuration_changed"), L(1)),
        Eq(P0(receipt, "development_support_topology_changed"), L(1)),
        Gt(P0(receipt, "development_orientation_units"), L(0)),
        Gt(P0(receipt, "development_translation_units"), L(0)),
    )


def instantiate_field_rule():
    return {
        "name": "smw_instantiate_situated_somatomotor_wave_field",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -120,
        "batch": False,
        "comment": "The body topology, not anatomy or a canonical pose, is "
        "the excitable sheet. The field has no action until development opens "
        "a situated floor ecology.",
        "match": [["episode", "has_embodied_effector_topology", "topology"]],
        "where": Eq(
            Count(Neighbours("episode", "has_somatomotor_wave_field")),
            L(0),
        ),
        "effects": [
            ["add_node", "field", "SomatomotorWaveField", {
                "current_epoch": 0,
                "last_clock_epoch": 0,
                "last_ignition_epoch": 0,
                "last_collapse_epoch": 0,
                "ignition_count": 0,
                "collapse_count": 0,
                "verified_reafference_count": 0,
                "warm_coupling_hint_count": 0,
                "warm_coupling_reverification_count": 0,
                "passive_scaffold_receipt_count": 0,
                "vestibular_scaffold_receipt_count": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "episode", "has_somatomotor_wave_field", "field"],
            ["add_edge", "field", "uses_embodied_effector_topology", "topology"],
        ],
    }


def instantiate_cell_rule():
    representative = Argmin(
        channel_effectors(),
        "channel_option",
        P0("channel_option", "ordinal"),
        V("effector"),
    )
    return {
        "name": "smw_instantiate_excitable_cell_for_each_effector_channel",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -119,
        "batch": True,
        "comment": "One excitable cell per mechanically discovered command "
        "channel, not per opposing command polarity. Its ordinal is identity "
        "only; wave dynamics determine recruitment.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "uses_embodied_effector_topology", "topology"],
            ["topology", "has_embodied_effector", "effector"],
        ],
        "where": And(
            Gt(P0("effector", "channel_ordinal"), L(-1)),
            Eq(V("effector"), representative),
            Eq(Count(cell_for_effector("effector")), L(0)),
        ),
        "effects": [
            ["add_node", "cell", "SomatomotorWaveCell", {
                "ordinal": T(P0("effector", "ordinal")),
                "state": "rested",
                "excitability": 1,
                "activated_at": 0,
                "active_until": 0,
                "refractory_until": 0,
                "last_recovery_epoch": 0,
                "activation_count": 0,
                "verified_consequence_count": 0,
                "productive_consequence_count": 0,
                "passive_exposure_count": 0,
                "passive_contingent_count": 0,
                "passive_mismatch_count": 0,
                "passive_consequence_count": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "field", "has_somatomotor_wave_cell", "cell"],
            ["add_edge", "cell", "represents_embodied_effector", "effector"],
        ],
    }


def instantiate_passive_body_model_rule():
    return {
        "name": "smw_instantiate_passive_body_model_per_effector_channel",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -118,
        "batch": True,
        "comment": "Exafferent motion gets its own predictive model. It is "
        "not an action model and never receives output authority.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": Eq(Count(Neighbours(
            "cell", "has_somatomotor_passive_body_model"
        )), L(0)),
        "effects": [
            ["add_node", "passive_model", "SomatomotorPassiveBodyModel", {
                "exposure_count": 0,
                "contingent_count": 0,
                "mismatch_count": 0,
                "positive_extent_units": 0,
                "negative_extent_units": 0,
                "return_residual_sum_units": 0,
                "coupled_channel_observation_count": 0,
                "passive_prediction_error_units": 0,
                "repeatable_count": 0,
                "active_reverification_count": 0,
                "agency_disambiguated_count": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            [
                "add_edge", "cell", "has_somatomotor_passive_body_model",
                "passive_model",
            ],
        ],
    }


def request_passive_effector_scaffold_rule():
    unexposed = unexposed_scaffold_cells()
    winner = Argmin(
        unexposed,
        "scaffold_candidate",
        P0("scaffold_candidate", "ordinal"),
        V("field"),
    )
    return {
        "name": "smw_request_least_exposed_passive_effector_cycle",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -116,
        "batch": False,
        "comment": "A caregiver opportunity is exafferent calibration, not "
        "an action. The graph requests the least-exposed situated channel.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": And(
            Eq(P0("episode", "caregiver_scaffold_session_active"), L(1)),
            Eq(P0("episode", "caregiver_scaffold_handoff_ready"), L(0)),
            Gt(Count(unexposed), L(0)),
            Eq(Count(Neighbours(
                "episode", "requests_passive_somatomotor_scaffold"
            )), L(0)),
            Eq(V("cell"), winner),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "requests_passive_somatomotor_scaffold",
                "cell",
            ],
            ["set_attr", "episode", "caregiver_scaffold_request_count", T(
                Plus(
                    P0("episode", "caregiver_scaffold_request_count"),
                    L(1),
                )
            )],
        ],
    }


def learn_passive_effector_scaffold_rule():
    return {
        "name": "smw_learn_exafferent_effector_cycle_without_agency_credit",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -115,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_somatomotor_scaffold_receipt", "receipt"],
            ["receipt", "scaffolds_somatomotor_wave_cell", "cell"],
            ["episode", "requests_passive_somatomotor_scaffold", "cell"],
            ["cell", "has_somatomotor_passive_body_model", "passive_model"],
        ],
        "where": And(
            Eq(A("receipt", "scaffold_kind"), L("passive_effector_cycle")),
            Eq(P0("receipt", "exafferent"), L(1)),
            Eq(P0("receipt", "efference_copy_present"), L(0)),
            Eq(P0("receipt", "receipt_processed"), L(0)),
        ),
        "effects": [
            ["set_attr", "cell", "passive_exposure_count", T(Plus(
                P0("cell", "passive_exposure_count"), L(1)
            ))],
            ["set_attr", "cell", "passive_contingent_count", T(Plus(
                P0("cell", "passive_contingent_count"), L(1)
            ))],
            ["set_attr", "cell", "passive_consequence_count", T(Plus(
                P0("cell", "passive_consequence_count"),
                P0("receipt", "configuration_changed"),
            ))],
            ["set_attr", "cell", "excitability", T(Plus(
                P0("cell", "excitability"),
                P0("receipt", "configuration_changed"),
            ))],
            ["set_attr", "field", "passive_scaffold_receipt_count", T(Plus(
                P0("field", "passive_scaffold_receipt_count"), L(1)
            ))],
            ["set_attr", "passive_model", "exposure_count", T(Plus(
                P0("passive_model", "exposure_count"), L(1)
            ))],
            ["set_attr", "passive_model", "contingent_count", T(Plus(
                P0("passive_model", "contingent_count"), L(1)
            ))],
            ["set_attr", "passive_model", "positive_extent_units", T(Max(
                P0("passive_model", "positive_extent_units"),
                P0("receipt", "positive_excursion_units"),
            ))],
            ["set_attr", "passive_model", "negative_extent_units", T(Max(
                P0("passive_model", "negative_extent_units"),
                Neg(P0("receipt", "negative_excursion_units")),
            ))],
            ["set_attr", "passive_model", "return_residual_sum_units", T(
                Plus(
                    P0("passive_model", "return_residual_sum_units"),
                    Abs(P0("receipt", "return_residual_units")),
                )
            )],
            ["set_attr", "passive_model", "coupled_channel_observation_count", T(
                Plus(
                    P0("passive_model", "coupled_channel_observation_count"),
                    P0("receipt", "coupled_channel_count"),
                )
            )],
            ["set_attr", "passive_model", "passive_prediction_error_units", T(
                Plus(
                    Abs(Minus(
                        P0("receipt", "positive_excursion_units"),
                        P0("passive_model", "positive_extent_units"),
                    )),
                    Plus(
                        Abs(Minus(
                            Neg(P0("receipt", "negative_excursion_units")),
                            P0("passive_model", "negative_extent_units"),
                        )),
                        Abs(P0("receipt", "return_residual_units")),
                    ),
                )
            )],
            ["set_attr", "passive_model", "repeatable_count", T(Plus(
                P0("passive_model", "repeatable_count"),
                If(
                    And(
                        Gt(P0("passive_model", "exposure_count"), L(0)),
                        Eq(
                            P0("passive_model", "passive_prediction_error_units"),
                            L(0),
                        ),
                    ),
                    L(1),
                    L(0),
                ),
            ))],
            ["set_attr", "episode", "caregiver_scaffold_receipt_count", T(
                Plus(
                    P0("episode", "caregiver_scaffold_receipt_count"),
                    L(1),
                )
            )],
            ["set_attr", "receipt", "receipt_processed", 1],
            [
                "del_edge",
                "episode",
                "requests_passive_somatomotor_scaffold",
                "cell",
            ],
        ],
    }


def reject_noncontingent_effector_scaffold_rule():
    return {
        "name": "smw_record_noncontingent_passive_motion_without_handoff_credit",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -115,
        "batch": False,
        "comment": "Motion of a different channel is real exafference, but it "
        "does not answer the graph's request and cannot unlock active control.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_somatomotor_scaffold_receipt", "receipt"],
            ["receipt", "scaffolds_somatomotor_wave_cell", "actual_cell"],
            ["actual_cell", "has_somatomotor_passive_body_model", "actual_model"],
            ["episode", "requests_passive_somatomotor_scaffold", "requested_cell"],
            ["requested_cell", "has_somatomotor_passive_body_model", "requested_model"],
        ],
        "where": And(
            Not(Eq(V("actual_cell"), V("requested_cell"))),
            Eq(A("receipt", "scaffold_kind"), L("passive_effector_cycle")),
            Eq(P0("receipt", "exafferent"), L(1)),
            Eq(P0("receipt", "efference_copy_present"), L(0)),
            Eq(P0("receipt", "receipt_processed"), L(0)),
        ),
        "effects": [
            ["set_attr", "actual_cell", "passive_exposure_count", T(Plus(
                P0("actual_cell", "passive_exposure_count"), L(1)
            ))],
            ["set_attr", "actual_model", "exposure_count", T(Plus(
                P0("actual_model", "exposure_count"), L(1)
            ))],
            ["set_attr", "requested_cell", "passive_mismatch_count", T(Plus(
                P0("requested_cell", "passive_mismatch_count"), L(1)
            ))],
            ["set_attr", "requested_model", "mismatch_count", T(Plus(
                P0("requested_model", "mismatch_count"), L(1)
            ))],
            ["set_attr", "episode", "caregiver_scaffold_mismatch_count", T(
                Plus(P0("episode", "caregiver_scaffold_mismatch_count"), L(1))
            )],
            ["set_attr", "receipt", "receipt_processed", 1],
            [
                "del_edge", "episode",
                "requests_passive_somatomotor_scaffold", "requested_cell",
            ],
        ],
    }


def request_passive_vestibular_scaffold_rule():
    return {
        "name": "smw_request_passive_whole_body_load_wave_after_limb_survey",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -114,
        "batch": False,
        "match": [["episode", "has_somatomotor_wave_field", "field"]],
        "where": And(
            Eq(P0("episode", "caregiver_scaffold_session_active"), L(1)),
            Eq(Count(unexposed_scaffold_cells()), L(0)),
            Eq(P0("episode", "caregiver_bounce_requested"), L(0)),
            Eq(P0("episode", "caregiver_bounce_completed"), L(0)),
        ),
        "effects": [
            ["set_attr", "episode", "caregiver_bounce_requested", 1],
        ],
    }


def learn_passive_vestibular_scaffold_rule():
    return {
        "name": "smw_learn_exafferent_whole_body_load_wave",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -113,
        "batch": False,
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_somatomotor_scaffold_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("receipt", "scaffold_kind"), L("passive_body_bounce")),
            Eq(P0("receipt", "exafferent"), L(1)),
            Eq(P0("receipt", "efference_copy_present"), L(0)),
            Eq(P0("receipt", "receipt_processed"), L(0)),
        ),
        "effects": [
            [
                "set_attr",
                "field",
                "vestibular_scaffold_receipt_count",
                T(Plus(
                    P0("field", "vestibular_scaffold_receipt_count"),
                    L(1),
                )),
            ],
            ["set_attr", "episode", "caregiver_bounce_requested", 0],
            ["set_attr", "episode", "caregiver_bounce_completed", 1],
            ["set_attr", "receipt", "receipt_processed", 1],
        ],
    }


def close_passive_scaffold_handoff_rule():
    return {
        "name": "smw_close_passive_scaffold_before_self_authored_attempt",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -112,
        "batch": False,
        "match": [["episode", "has_somatomotor_wave_field", "field"]],
        "where": And(
            Eq(P0("episode", "caregiver_scaffold_session_active"), L(1)),
            Eq(Count(unexposed_scaffold_cells()), L(0)),
            Eq(P0("episode", "caregiver_bounce_completed"), L(1)),
            Eq(P0("episode", "caregiver_scaffold_handoff_ready"), L(0)),
        ),
        "effects": [
            ["set_attr", "episode", "caregiver_scaffold_handoff_ready", 1],
            ["set_attr", "episode", "caregiver_scaffold_session_active", 0],
            ["set_attr", "episode", "caregiver_passive_scaffold_withdrawn", 1],
            ["set_attr", "episode", "caregiver_scaffold_withdrawn", 1],
        ],
    }


def bind_coupling_rule(direction: str):
    source_effector = "source_effector" if direction == "forward" else "target_effector"
    target_effector = "target_effector" if direction == "forward" else "source_effector"
    return {
        "name": f"smw_bind_{direction}_topological_wave_coupling",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -118,
        "batch": True,
        "comment": "Mechanical adjacency supplies only a possible propagation "
        "path. Receipt-grounded use changes its integer strength.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "uses_embodied_effector_topology", "topology"],
            ["topology", "has_embodied_effector_relation", "relation"],
            ["relation", "has_embodied_effector_source", "source_effector"],
            ["relation", "has_embodied_effector_target", "target_effector"],
            ["field", "has_somatomotor_wave_cell", "source_cell"],
            ["source_cell", "represents_embodied_effector", source_effector],
            ["field", "has_somatomotor_wave_cell", "target_cell"],
            ["target_cell", "represents_embodied_effector", target_effector],
        ],
        "where": Eq(Count(known_coupling()), L(0)),
        "effects": [
            ["add_node", "coupling", "SomatomotorWaveCoupling", {
                "strength": 1,
                "coactivation_count": 0,
                "productive_count": 0,
                "unproductive_count": 0,
                "warm_prior_rank": 0,
                "warm_prior_reverified": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "source_cell", "has_somatomotor_wave_coupling", "coupling"],
            ["add_edge", "coupling", "targets_somatomotor_wave_cell", "target_cell"],
            ["add_edge", "coupling", "grounds_in_embodied_effector_relation", "relation"],
        ],
    }


def warm_start_coupling_rule():
    candidates = coupling_memory_candidates()
    winner = Argmax(
        candidates,
        "ranked_memory",
        Minus(
            P0("ranked_memory", "productive_count"),
            P0("ranked_memory", "unproductive_count"),
        ),
        V("memory"),
    )
    return {
        "name": "smw_warm_start_structurally_matching_coupling_hint",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -117,
        "batch": False,
        "comment": "A source-body coupling supplies only a one-shot rank "
        "hint when body ShapeDecode coverage exceeds residual and the local "
        "mechanical relation motif matches. The target receipt immediately "
        "clears the hint; actuator choice remains in the local wave collapse.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "source"],
            ["source", "has_somatomotor_wave_coupling", "coupling"],
            ["source", "represents_embodied_effector", "source_effector"],
            ["coupling", "grounds_in_embodied_effector_relation", "relation"],
            ["coupling", "targets_somatomotor_wave_cell", "target"],
            ["target", "represents_embodied_effector", "target_effector"],
            ["agent", "has_somatomotor_coupling_memory", "memory"],
        ],
        "where": And(
            Eq(P0("coupling", "warm_prior_rank"), L(0)),
            Eq(Count(Neighbours(
                "coupling", "warm_starts_from_somatomotor_coupling_memory"
            )), L(0)),
            Gt(Count(candidates), L(0)),
            Eq(V("memory"), winner),
        ),
        "effects": [
            ["set_attr", "coupling", "warm_prior_rank", T(Max(
                L(1),
                Minus(
                    P0("memory", "productive_count"),
                    P0("memory", "unproductive_count"),
                ),
            ))],
            [
                "add_edge",
                "coupling",
                "warm_starts_from_somatomotor_coupling_memory",
                "memory",
            ],
            ["set_attr", "field", "warm_coupling_hint_count", T(Plus(
                P0("field", "warm_coupling_hint_count"), L(1)
            ))],
        ],
    }


def advance_clock_rule():
    return {
        "name": "smw_advance_from_situated_motor_epoch",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -110,
        "batch": False,
        "comment": "The boundary publishes a clock only. All structured "
        "activity is generated by the graph.",
        "match": [["episode", "has_somatomotor_wave_field", "field"]],
        "where": Gt(P0("episode", "request_seq"), P0("field", "last_clock_epoch")),
        "effects": [
            ["set_attr", "field", "current_epoch", T(P0("episode", "request_seq"))],
            ["set_attr", "field", "last_clock_epoch", T(P0("episode", "request_seq"))],
        ],
    }


def recover_and_charge_rule():
    return {
        "name": "smw_recover_and_homeostatically_charge_cells",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -109,
        "batch": True,
        "comment": "Unused cells become more likely to ignite. Refractory "
        "cells recover from a topology-derived interval, preventing fixation.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": And(
            Gt(P0("field", "current_epoch"), P0("cell", "last_recovery_epoch")),
            Or(
                Eq(A("cell", "state"), L("rested")),
                And(
                    Eq(A("cell", "state"), L("refractory")),
                    Not(Lt(
                        P0("field", "current_epoch"),
                        P0("cell", "refractory_until"),
                    )),
                ),
            ),
        ),
        "effects": [
            ["set_attr", "cell", "state", "rested"],
            ["set_attr", "cell", "excitability", T(Plus(
                P0("cell", "excitability"), L(1)
            ))],
            ["set_attr", "cell", "last_recovery_epoch", T(
                P0("field", "current_epoch")
            )],
        ],
    }


def activate_recruited_rule():
    local_span = Max(
        L(1),
        Count(Neighbours("cell", "has_somatomotor_wave_coupling")),
    )
    return {
        "name": "smw_activate_recruited_next_wavefront",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -108,
        "batch": True,
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": And(
            Eq(A("cell", "state"), L("recruited")),
            Eq(P0("cell", "activated_at"), P0("field", "current_epoch")),
        ),
        "effects": [
            ["set_attr", "cell", "state", "active"],
            ["set_attr", "cell", "active_until", T(Plus(
                P0("field", "current_epoch"), local_span
            ))],
            ["set_attr", "cell", "excitability", 0],
            ["set_attr", "cell", "activation_count", T(Plus(
                P0("cell", "activation_count"), L(1)
            ))],
        ],
    }


def refract_previous_wavefront_rule():
    neighbour_count = Count(Neighbours("cell", "has_somatomotor_wave_coupling"))
    return {
        "name": "smw_refract_consumed_wavefront",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -107,
        "batch": True,
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": And(
            Eq(A("cell", "state"), L("active")),
            Lt(P0("cell", "active_until"), P0("field", "current_epoch")),
        ),
        "effects": [
            ["set_attr", "cell", "state", "refractory"],
            ["set_attr", "cell", "refractory_until", T(Plus(
                P0("field", "current_epoch"), Max(L(1), neighbour_count)
            ))],
        ],
    }


def ignite_rule():
    eligible = rested_cells()
    winner = Argmin(
        eligible,
        "ignition_candidate",
        Neg(Plus(
            P0("ignition_candidate", "excitability"),
            cell_warm_ignition_rank("ignition_candidate"),
        )),
        V("field"),
    )
    local_span = Max(
        L(1),
        Count(Neighbours("cell", "has_somatomotor_wave_coupling")),
    )
    return {
        "name": "smw_homeostatic_ignition",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -106,
        "batch": False,
        "comment": "Ignition is endogenous: the most deprived rested cell "
        "wins. No desired pose, limb name, random motor command or reward enters.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": And(
            floor_development_active(),
            Gt(P0("field", "current_epoch"), P0("field", "last_ignition_epoch")),
            Eq(Count(current_active_cells()), L(0)),
            Gt(Count(eligible), L(0)),
            Eq(V("cell"), winner),
        ),
        "effects": [
            ["set_attr", "cell", "state", "active"],
            ["set_attr", "cell", "activated_at", T(P0("field", "current_epoch"))],
            ["set_attr", "cell", "active_until", T(Plus(
                P0("field", "current_epoch"), local_span
            ))],
            ["set_attr", "cell", "excitability", 0],
            ["set_attr", "cell", "activation_count", T(Plus(
                P0("cell", "activation_count"), L(1)
            ))],
            ["set_attr", "field", "last_ignition_epoch", T(
                P0("field", "current_epoch")
            )],
            ["set_attr", "field", "ignition_count", T(Plus(
                P0("field", "ignition_count"), L(1)
            ))],
        ],
    }


def propagate_rule():
    return {
        "name": "smw_propagate_one_topological_hop",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -105,
        "batch": True,
        "comment": "A current wavefront recruits adjacent rested cells for "
        "the next motor epoch. The one-epoch delay prevents fixpoint flooding.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "source"],
            ["source", "has_somatomotor_wave_coupling", "coupling"],
            ["coupling", "targets_somatomotor_wave_cell", "target"],
        ],
        "where": And(
            Eq(A("source", "state"), L("active")),
            Eq(P0("source", "activated_at"), P0("field", "current_epoch")),
            Eq(A("target", "state"), L("rested")),
            Gt(P0("coupling", "strength"), L(0)),
            Eq(Count(stronger_available_coupling()), L(0)),
        ),
        "effects": [
            ["set_attr", "target", "state", "recruited"],
            ["set_attr", "target", "activated_at", T(Plus(
                P0("field", "current_epoch"), L(1)
            ))],
            ["set_attr", "coupling", "coactivation_count", T(Plus(
                P0("coupling", "coactivation_count"), L(1)
            ))],
        ],
    }


def open_wave_program_rule():
    active = current_active_cells()
    return {
        "name": "smw_collapse_current_wavefront_to_single_program",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -104,
        "batch": False,
        "comment": "Massively parallel activity becomes one program which "
        "may control many effectors; there is never one decision per effector.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": And(
            floor_development_active(),
            Gt(Count(active), L(0)),
            Gt(P0("field", "current_epoch"), P0("field", "last_collapse_epoch")),
        ),
        "effects": [
            ["add_node", "program", "SomatomotorWaveProgram", {
                "epoch": T(P0("field", "current_epoch")),
                "status": "open",
                "wavefront_width": T(Count(active)),
                "receipt_processed": 0,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "field", "has_somatomotor_wave_program", "program"],
            [
                "add_edge",
                "program",
                "tests_embodied_developmental_capability",
                "capability",
            ],
            ["set_attr", "field", "last_collapse_epoch", T(P0("field", "current_epoch"))],
            ["set_attr", "field", "collapse_count", T(Plus(
                P0("field", "collapse_count"), L(1)
            ))],
        ],
    }


def bind_wavefront_members_rule():
    return {
        "name": "smw_bind_parallel_wavefront_members_to_program",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -103,
        "batch": True,
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_program", "program"],
            ["field", "has_somatomotor_wave_cell", "cell"],
        ],
        "where": And(
            Eq(A("program", "status"), L("open")),
            Eq(P0("program", "epoch"), P0("field", "current_epoch")),
            Eq(A("cell", "state"), L("active")),
            Not(Gt(P0("cell", "activated_at"), P0("program", "epoch"))),
            Not(Lt(P0("cell", "active_until"), P0("program", "epoch"))),
            Not(Exists(
                Neighbours("program", "includes_somatomotor_wave_cell"),
                "known_member",
                Eq(V("known_member"), V("cell")),
            )),
        ),
        "effects": [[
            "add_edge", "program", "includes_somatomotor_wave_cell", "cell",
        ]],
    }


def close_wave_program_rule():
    return {
        "name": "smw_close_complete_wavefront_program",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": -102,
        "batch": False,
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_program", "program"],
        ],
        "where": And(
            Eq(A("program", "status"), L("open")),
            Eq(
                Count(Neighbours("program", "includes_somatomotor_wave_cell")),
                P0("program", "wavefront_width"),
            ),
        ),
        "effects": [["set_attr", "program", "status", "ready"]],
    }


def learn_reafference_rule():
    productive = productive_receipt()
    return {
        "name": "smw_learn_wave_cell_from_verified_reafference",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": 80,
        "batch": True,
        "comment": "The body teaches the generator. A wave is productive if "
        "its verified receipt changes configuration, contact or orientation; "
        "no external reward or preferred pose is required.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "projects_embodied_development", "development"],
            ["field", "has_somatomotor_wave_program", "program"],
            ["program", "includes_somatomotor_wave_cell", "cell"],
            ["development", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("program", "status"), L("ready")),
            Eq(P0("program", "receipt_processed"), L(0)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_receipt_seq"), P0("program", "epoch")),
        ),
        "effects": [
            ["set_attr", "cell", "verified_consequence_count", T(Plus(
                P0("cell", "verified_consequence_count"), L(1)
            ))],
            ["set_attr", "cell", "productive_consequence_count", T(Plus(
                P0("cell", "productive_consequence_count"),
                If(productive, L(1), L(0)),
            ))],
        ],
    }


def learn_coupling_reafference_rule():
    productive = capability_success("instance", "receipt")
    return {
        "name": "smw_reinforce_or_fractionate_coactive_wave_coupling",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": 81,
        "batch": True,
        "comment": "Only a verified receipt can change propagation. A "
        "productive coactivation strengthens the directed topological path; "
        "an unproductive one weakens it to zero, allowing assemblies to "
        "fractionate without inventing a fault class or host reward.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "projects_embodied_development", "development"],
            ["field", "has_somatomotor_wave_program", "program"],
            [
                "program",
                "tests_embodied_developmental_capability",
                "instance",
            ],
            ["program", "includes_somatomotor_wave_cell", "source"],
            ["source", "has_somatomotor_wave_coupling", "coupling"],
            ["coupling", "targets_somatomotor_wave_cell", "target"],
            ["program", "includes_somatomotor_wave_cell", "target"],
            ["development", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("program", "status"), L("ready")),
            Eq(P0("program", "receipt_processed"), L(0)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_receipt_seq"), P0("program", "epoch")),
            Not(Exists(
                Neighbours(
                    "program", "processed_somatomotor_wave_coupling"
                ),
                "processed_coupling",
                Eq(V("processed_coupling"), V("coupling")),
            )),
        ),
        "effects": [
            ["set_attr", "coupling", "strength", T(If(
                productive,
                Plus(P0("coupling", "strength"), L(1)),
                Max(L(0), Minus(P0("coupling", "strength"), L(1))),
            ))],
            ["set_attr", "coupling", "productive_count", T(Plus(
                P0("coupling", "productive_count"),
                If(productive, L(1), L(0)),
            ))],
            ["set_attr", "coupling", "unproductive_count", T(Plus(
                P0("coupling", "unproductive_count"),
                If(productive, L(0), L(1)),
            ))],
            ["set_attr", "field", "warm_coupling_reverification_count", T(
                Plus(
                    P0("field", "warm_coupling_reverification_count"),
                    If(
                        Gt(P0("coupling", "warm_prior_rank"), L(0)),
                        L(1),
                        L(0),
                    ),
                )
            )],
            ["set_attr", "coupling", "warm_prior_reverified", T(If(
                Gt(P0("coupling", "warm_prior_rank"), L(0)),
                L(1),
                P0("coupling", "warm_prior_reverified"),
            ))],
            ["set_attr", "coupling", "warm_prior_rank", 0],
            [
                "add_edge",
                "program",
                "processed_somatomotor_wave_coupling",
                "coupling",
            ],
        ],
    }


def close_reafference_rule():
    return {
        "name": "smw_close_verified_reafference_episode",
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "order": 82,
        "batch": False,
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "projects_embodied_development", "development"],
            ["field", "has_somatomotor_wave_program", "program"],
            ["development", "has_embodied_development_receipt", "receipt"],
        ],
        "where": And(
            Eq(A("program", "status"), L("ready")),
            Eq(P0("program", "receipt_processed"), L(0)),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Eq(P0("receipt", "development_receipt_seq"), P0("program", "epoch")),
        ),
        "effects": [
            ["set_attr", "program", "receipt_processed", 1],
            ["set_attr", "program", "status", "experienced"],
            ["set_attr", "field", "verified_reafference_count", T(Plus(
                P0("field", "verified_reafference_count"), L(1)
            ))],
        ],
    }


def manifest() -> dict:
    return {
        "id": "somatomotor_waves",
        "version": "1.6.0",
        "depends_on": ["embodied_development"],
        "area": "embodied_somatomotor_waves",
        "latency_class": "hard_realtime",
        "description": "Integer-native endogenous spontaneous activity over "
            "a discovered effector topology: homeostatic ignition, one-hop wave "
            "propagation, refractoriness, single compound collapse and verified "
            "reafferent learning, with one-shot structural ignition priors.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "somatomotor_waves:field",
                "src": {"type": "Unknown", "var": "episode"},
                "edge_type": "has_somatomotor_wave_field",
                "tgt": {"type": "SomatomotorWaveField", "var": "field"},
            },
            {
                "provenance": "somatomotor_waves:cell",
                "src": {"type": "SomatomotorWaveField", "var": "field"},
                "edge_type": "has_somatomotor_wave_cell",
                "tgt": {"type": "SomatomotorWaveCell", "var": "cell"},
            },
            {
                "provenance": "somatomotor_waves:program",
                "src": {"type": "SomatomotorWaveField", "var": "field"},
                "edge_type": "has_somatomotor_wave_program",
                "tgt": {"type": "SomatomotorWaveProgram", "var": "program"},
            },
            {
                "provenance": "somatomotor_waves:coupling_memory",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_somatomotor_coupling_memory",
                "tgt": {"type": "SomatomotorCouplingMemory", "var": "memory"},
            },
        ],
        "rules": [
            instantiate_field_rule(),
            instantiate_cell_rule(),
            instantiate_passive_body_model_rule(),
            bind_coupling_rule("forward"),
            bind_coupling_rule("reverse"),
            warm_start_coupling_rule(),
            request_passive_effector_scaffold_rule(),
            learn_passive_effector_scaffold_rule(),
            reject_noncontingent_effector_scaffold_rule(),
            request_passive_vestibular_scaffold_rule(),
            learn_passive_vestibular_scaffold_rule(),
            close_passive_scaffold_handoff_rule(),
            advance_clock_rule(),
            recover_and_charge_rule(),
            activate_recruited_rule(),
            refract_previous_wavefront_rule(),
            ignite_rule(),
            propagate_rule(),
            open_wave_program_rule(),
            bind_wavefront_members_rule(),
            close_wave_program_rule(),
            learn_reafference_rule(),
            learn_coupling_reafference_rule(),
            close_reafference_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "somatomotor_waves.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
