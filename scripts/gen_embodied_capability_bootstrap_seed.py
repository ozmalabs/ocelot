#!/usr/bin/env python3
"""Author morphology-neutral, integer-native embodied bootstrap hints.

The authored nodes are output-null relation systems.  They narrow an
analysis-by-synthesis search to useful basin topologies without supplying a
joint identity, a command, a duration, a global home, or actuator authority.
Python only serialises the graph seed; matching and use happen in Rust.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


# A stage phase is a topological role in a contact/energy cycle, not a clock.
BOOTSTRAPS = (
    {
        "name": "bootstrap:development:supported_range_discovery",
        "context": "locomotion",
        "family": "embodiment_calibration",
        "provenance": "developmental_motor_learning_and_body_babbling",
        "evidence_url": "https://doi.org/10.3389/fpsyg.2018.01939",
        "situations": ("broad_support", "unknown_effector_map"),
        "invariants": ("viability", "reversible_exploration"),
        "stages": (
            ("preparation", "find_broad_support", "support_before_exploration"),
            ("launch", "vary_one_relation", "local_controllability_probe"),
            ("landing", "observe_displacement", "situated_effect_receipt"),
            ("recovery", "compose_correlated_effectors", "shape_indexed_chunk"),
        ),
    },
    {
        "name": "bootstrap:development:righting_support_reacquisition",
        "context": "locomotion",
        "family": "righting_and_get_up",
        "provenance": "developmental_righting_and_postural_reactions",
        "evidence_url": "https://doi.org/10.1016/0378-3782(90)90140-E",
        "situations": ("low_height", "support_not_under_mass"),
        "invariants": ("protect_sensors", "reacquire_support"),
        "stages": (
            ("preparation", "locate_current_support", "no_assumed_home"),
            ("launch", "create_roll_or_push", "exchange_internal_momentum"),
            ("landing", "place_new_support", "increase_support_dimension"),
            ("recovery", "raise_mass_inside_support", "righting_receipt"),
        ),
    },
    {
        "name": "bootstrap:biology:protected_descent_and_roll",
        "context": "locomotion",
        "family": "fall_management",
        "provenance": "human_protective_stepping_reaching_and_rolling",
        "evidence_url": "https://doi.org/10.1016/j.humov.2013.12.010",
        "situations": ("support_loss", "unavoidable_descent"),
        "invariants": ("protect_sensors", "distribute_impulse"),
        "stages": (
            ("preparation", "choose_reachable_contact", "trade_step_reach_or_roll"),
            ("launch", "redirect_angular_momentum", "avoid_direct_sensor_impact"),
            ("flight", "shape_contact_sequence", "spread_impulse_over_time"),
            ("landing", "accept_load_progressively", "retain_recovery_options"),
        ),
    },
    {
        "name": "bootstrap:biology:balance_strategy_ladder",
        "context": "locomotion",
        "family": "disturbance_rejection",
        "provenance": "ankle_hip_step_and_reach_postural_strategies",
        "evidence_url": "https://doi.org/10.1152/jn.1986.55.6.1369",
        "situations": ("supported", "external_disturbance"),
        "invariants": ("viability", "bounded_load"),
        "stages": (
            ("preparation", "estimate_support_margin", "disturbance_relative_to_capability"),
            ("launch", "counter_within_support", "small_coupled_response"),
            ("flight", "change_support_if_needed", "step_or_reach_is_tradeoff"),
            ("landing", "dissipate_residual", "verify_new_support"),
        ),
    },
    {
        "name": "bootstrap:biology:cyclic_contact_locomotion",
        "context": "locomotion",
        "family": "locomotion",
        "provenance": "phase_dependent_spinal_and_supraspinal_locomotor_control",
        "evidence_url": "https://doi.org/10.1038/nrn1137",
        "situations": ("alternating_support_available", "displacement_available"),
        "invariants": ("viability", "controllability"),
        "stages": (
            ("preparation", "accept_load", "support_receipt"),
            ("launch", "redirect_and_propel", "momentum_exchange"),
            ("flight", "clear_free_effector", "predict_next_contact"),
            ("landing", "place_support", "close_contact_cycle"),
        ),
    },
    {
        "name": "bootstrap:frames:translation_without_canonical_forward",
        "context": "locomotion",
        "family": "frame_discovery",
        "provenance": "situated_sensorimotor_coordinate_frame_learning",
        "evidence_url": "https://doi.org/10.1523/ENEURO.0070-16.2016",
        "situations": ("repeatable_translation", "unknown_task_frame_alignment"),
        "invariants": ("controllability", "viability"),
        "stages": (
            ("preparation", "observe_translation_from_current_pose", "no_canonical_forward"),
            ("launch", "find_opposed_or_reversible_effect", "direction_is_a_relation"),
            ("flight", "bind_body_world_and_task_frames", "preserve_gait_basin"),
            ("landing", "align_capability_to_situated_goal", "goal_error_is_not_gait_error"),
        ),
    },
    {
        "name": "bootstrap:whole_body:compound_task_residual",
        "context": "locomotion",
        "family": "whole_body_composition",
        "provenance": "motor_abundance_and_uncontrolled_manifold_control",
        "evidence_url": "https://doi.org/10.1123/mcj.14.1.83",
        "situations": ("multiple_effectors", "multiple_open_residuals"),
        "invariants": ("task_progress", "viability"),
        "stages": (
            ("preparation", "identify_shared_effect", "coupling_is_observed_not_named"),
            ("launch", "hold_one_combined_outcome", "single_collapse_many_effectors"),
            ("flight", "leave_nullspace_variable", "do_not_freeze_irrelevant_axes"),
            ("landing", "mint_combination_on_receipt", "practice_becomes_metaprogram"),
        ),
    },
    {
        "name": "bootstrap:development:reach_contact_release",
        "context": "manipulation",
        "family": "contact_manipulation",
        "provenance": "infant_reaching_and_grasp_development",
        "evidence_url": "https://doi.org/10.1111/desc.12370",
        "situations": ("reachable_affordance", "free_effector"),
        "invariants": ("viability", "bounded_contact_force"),
        "stages": (
            ("preparation", "orient_to_affordance", "task_relative_preshape"),
            ("launch", "transport_effector", "redundant_path_is_free"),
            ("landing", "close_contact_chain", "force_closure_receipt"),
            ("recovery", "release_or_manipulate", "contact_is_reversible"),
        ),
    },
    {
        "name": "bootstrap:hybrid:effector_regime_transition",
        "context": "hybrid_mobility",
        "family": "hybrid_locomotion",
        "provenance": "hybrid_contact_aerodynamic_and_thrust_control",
        "evidence_url": "https://doi.org/10.1109/TMECH.2022.3164929",
        "situations": ("changing_effector_authority", "energy_transition"),
        "invariants": ("material_envelope", "controllability"),
        "stages": (
            ("preparation", "estimate_authority_envelope", "observe_load_and_deformation"),
            ("launch", "overlap_effector_regimes", "avoid_authority_gap"),
            ("flight", "trade_energy_and_control", "pareto_profile_stays_open"),
            ("landing", "retire_spent_effector", "verify_new_regime"),
        ),
    },
    {
        "name": "bootstrap:ballistic:takeoff_and_landing",
        "context": "self_takeoff",
        "family": "ballistic_transition",
        "provenance": "human_jump_takeoff_flight_and_landing_phases",
        "evidence_url": "https://doi.org/10.1519/JSC.0000000000004700",
        "situations": ("support_to_flight", "flight_to_support"),
        "invariants": ("material_envelope", "landing_options"),
        "stages": (
            ("preparation", "store_recoverable_energy", "load_within_envelope"),
            ("launch", "coordinate_impulse", "one_outcome_many_effectors"),
            ("flight", "shape_landing_state", "angular_momentum_is_conserved"),
            ("landing", "accept_and_redirect_load", "progressive_support_receipt"),
        ),
    },
)


def build() -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    local_id = 1

    invariant_ids: dict[str, int] = {}
    for invariant in sorted({
        value for row in BOOTSTRAPS for value in row["invariants"]
    }):
        invariant_ids[invariant] = local_id
        nodes.append({
            "local_id": local_id,
            "type": "CapabilityInvariant",
            "attrs": {
                "name": f"embodied_invariant:{invariant}",
                "invariant_kind": invariant,
                "integer_native": 1,
            },
        })
        local_id += 1

    routing_shape_ids: dict[tuple[str, str], int] = {}
    routing_shapes = sorted({
        (row["context"], phase)
        for row in BOOTSTRAPS
        for phase, _, _ in row["stages"]
    })
    for context, phase in routing_shapes:
        routing_shape_ids[(context, phase)] = local_id
        nodes.append({
            "local_id": local_id,
            "type": "EmbodiedMotorRoutingShape",
            "attrs": {
                "name": f"motor_routing_shape:{context}:{phase}",
                "motor_task_context": context,
                "motor_task_phase": phase,
                "signature": [
                    ["motor_task_context", context],
                    ["motor_task_phase", phase],
                ],
                "integer_native": 1,
            },
        })
        edges.append({
            "src": {"role": "agent_root"},
            "type": "has_embodied_motor_routing_shape",
            "tgt": {"local": local_id},
            "attrs": {},
        })
        local_id += 1

    for ordinal, row in enumerate(BOOTSTRAPS):
        situation_id = local_id
        hint_id = local_id + 1
        local_id += 2
        nodes.extend((
            {
                "local_id": situation_id,
                "type": "EmbodiedBootstrapSituation",
                "attrs": {
                    "name": f"situation:{row['name']}",
                    "ordinal": ordinal,
                    "family": row["family"],
                    "context": row["context"],
                    "signature": [
                        ["situation", value]
                        for value in row["situations"]
                    ],
                    "output_authority": 0,
                },
            },
            {
                "local_id": hint_id,
                "type": "EmbodiedMotorPlanHint",
                "attrs": {
                    "name": row["name"],
                    "ordinal": ordinal,
                    "signature": [["motor_task", row["context"]]],
                    "motor_task_context": row["context"],
                    "bootstrap_family": row["family"],
                    "knowledge_kind": "analysis_by_synthesis_basin_hint",
                    "provenance": row["provenance"],
                    "evidence_url": row["evidence_url"],
                    "stage_count": len(row["stages"]),
                    "output_authority": 0,
                    "integer_native": 1,
                },
            },
        ))
        edges.extend((
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_bootstrap_situation",
                "tgt": {"local": situation_id},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_motor_plan_hint_library",
                "tgt": {"local": hint_id},
                "attrs": {},
            },
            {
                "src": {"local": situation_id},
                "type": "suggests_embodied_motor_plan_hint",
                "tgt": {"local": hint_id},
                "attrs": {},
            },
        ))
        for invariant in row["invariants"]:
            edges.append({
                "src": {"local": situation_id},
                "type": "requires_capability_invariant",
                "tgt": {"local": invariant_ids[invariant]},
                "attrs": {},
            })
        for stage_ordinal, (phase, role, relation) in enumerate(row["stages"]):
            stage_id = local_id
            local_id += 1
            nodes.append({
                "local_id": stage_id,
                "type": "EmbodiedMotorPlanHintStage",
                "attrs": {
                    "name": f"{row['name']}:stage:{stage_ordinal}",
                    "ordinal": stage_ordinal,
                    "stage_role": role,
                    "signature": [
                        ["bootstrap_role", role],
                        ["bootstrap_relation", relation],
                    ],
                    "routing_signature": [
                        ["motor_task_context", row["context"]],
                        ["motor_task_phase", phase],
                    ],
                    "output_authority": 0,
                    "integer_native": 1,
                },
            })
            edges.append({
                "src": {"local": hint_id},
                "type": "has_embodied_motor_plan_hint_stage",
                "tgt": {"local": stage_id},
                "attrs": {},
            })
            edges.append({
                "src": {"local": stage_id},
                "type": "routes_through_embodied_motor_routing_shape",
                "tgt": {"local": routing_shape_ids[(row["context"], phase)]},
                "attrs": {},
            })

    productions = [
        ("Agent", "has_embodied_bootstrap_situation", "EmbodiedBootstrapSituation"),
        ("Agent", "has_embodied_motor_plan_hint_library", "EmbodiedMotorPlanHint"),
        ("EmbodiedBootstrapSituation", "suggests_embodied_motor_plan_hint", "EmbodiedMotorPlanHint"),
        ("EmbodiedBootstrapSituation", "requires_capability_invariant", "CapabilityInvariant"),
        ("EmbodiedMotorPlanHint", "has_embodied_motor_plan_hint_stage", "EmbodiedMotorPlanHintStage"),
        ("Agent", "has_embodied_motor_routing_shape", "EmbodiedMotorRoutingShape"),
        ("EmbodiedMotorPlanHintStage", "routes_through_embodied_motor_routing_shape", "EmbodiedMotorRoutingShape"),
    ]
    return {
        "id": "embodied_capability_bootstrap",
        "version": "1.0.0",
        "depends_on": ["capability_collapse"],
        "self_load_only": True,
        "area": "general_cognition",
        "latency_class": "background",
        "description": "Output-null, morphology-neutral situation and motor-plan basin hints for situated analysis-by-synthesis.",
        "nodes": nodes,
        "edges": edges,
        "productions": [
            {
                "provenance": f"seed:embodied_capability_bootstrap:{edge_type}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge_type,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for src, edge_type, tgt in productions
        ],
        "rules": [],
    }


def main() -> None:
    output = ROOT / "seeds" / "embodied_capability_bootstrap.json"
    payload = build()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output.relative_to(ROOT)} ({len(payload['nodes'])} nodes)")


if __name__ == "__main__":
    main()
