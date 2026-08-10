"""Morphology-neutral motor-plan hints distilled from biology and robotics.

These are relation systems for search initialization.  They contain no joint
identity, command value, timing constant, or output authority.
"""
from __future__ import annotations

from typing import Any


_STAGE_PHASES = {
    "accept_load": "preparation",
    "propel": "launch",
    "clear_limb": "flight",
    "place_limb": "landing",
    "weight_supported_explore": "preparation",
    "hand_supported_coordinate": "preparation",
    "independent_variable_steps": "launch",
    "symmetrize_without_freezing": "landing",
    "predict": "preparation",
    "exploit_passive_dynamics": "launch",
    "correct_from_receipt": "landing",
    "update_structure": "recovery",
    "declare_contact_stage": "preparation",
    "approach_contact_basin": "launch",
    "establish_contact": "landing",
    "stabilize_then_advance": "recovery",
    "forecast_mass_state": "preparation",
    "choose_contact_forces": "launch",
    "realize_task_hierarchy": "flight",
    "verify_load_envelope": "landing",
    "locate_affordance": "preparation",
    "select_maneuver_basin": "preparation",
    "shape_takeoff": "launch",
    "prepare_landing": "landing",
    "enter_with_directed_momentum": "preparation",
    "lower_and_round": "launch",
    "progress_contact_chain": "flight",
    "redirect_to_support": "landing",
    "verify_entry_envelope": "preparation",
    "command_dynamic_pitch_up": "launch",
    "hold_coupled_axes": "flight",
    "unload_and_recover": "recovery",
}


def _hint(
    name: str,
    context: str,
    provenance: str,
    evidence_url: str,
    stages: tuple[tuple[str, tuple[tuple[Any, ...], ...]], ...],
) -> dict[str, Any]:
    return {
        "attrs": {
            "name": name,
            "signature": (("motor_task", context),),
            "motor_task_context": context,
            "output_authority": 0.0,
            "knowledge_kind": "search_basin_hint",
            "provenance": provenance,
            "evidence_url": evidence_url,
            "stage_count": float(len(stages)),
        },
        "stages": [
            {
                "attrs": {
                    "name": f"{name}:stage:{ordinal}",
                    "ordinal": float(ordinal),
                    "stage_role": role,
                    "signature": signature,
                    "routing_signature": (
                        ("motor_task_context", context),
                        ("motor_task_phase", _STAGE_PHASES[role]),
                    ),
                    "output_authority": 0.0,
                },
            }
            for ordinal, (role, signature) in enumerate(stages)
        ],
    }


def seeded_motor_plan_hints() -> list[dict[str, Any]]:
    """Return abstract priors; graph matching decides applicability and use."""
    return [
        _hint(
            "prior:biology:spinal_phase_synergies",
            "locomotion",
            "biological_motor_infrastructure_and_muscle_synergies",
            "https://doi.org/10.1038/nrn1137",
            (
                ("accept_load", (("support", "load_acceptance"),)),
                ("propel", (("support", "stance"), ("function", "propulsion"))),
                ("clear_limb", (("support", "swing"), ("function", "clearance"))),
                ("place_limb", (("support", "contact_transition"),)),
            ),
        ),
        _hint(
            "prior:biology:developmental_symmetrization",
            "locomotion",
            "infant_supported_to_independent_locomotor_development",
            "https://doi.org/10.1038/s42003-025-09198-y",
            (
                ("weight_supported_explore", (("development", "supported"),)),
                ("hand_supported_coordinate", (("development", "assisted"),)),
                ("independent_variable_steps", (("development", "independent_early"),)),
                ("symmetrize_without_freezing", (("development", "independent_late"),)),
            ),
        ),
        _hint(
            "prior:biology:predictive_reactive_biomechanical",
            "locomotion",
            "human_sensorimotor_learning_control_classes",
            "https://doi.org/10.1038/nrn3112",
            (
                ("predict", (("control", "predictive"),)),
                ("exploit_passive_dynamics", (("control", "biomechanical"),)),
                ("correct_from_receipt", (("control", "reactive"),)),
                ("update_structure", (("learning", "error_and_use_dependent"),)),
            ),
        ),
        _hint(
            "prior:robotics:wococo_sequential_contacts",
            "parkour",
            "WoCoCo_whole_body_sequential_contact_control",
            "https://arxiv.org/abs/2406.06005",
            (
                ("declare_contact_stage", (("contact", "desired_set"),)),
                ("approach_contact_basin", (("contact", "precondition"),)),
                ("establish_contact", (("contact", "transition"),)),
                ("stabilize_then_advance", (("contact", "stage_receipt"),)),
            ),
        ),
        _hint(
            "prior:robotics:centroidal_mpc_whole_body",
            "locomotion",
            "centroidal_MPC_and_hierarchical_whole_body_control",
            "https://arxiv.org/abs/2506.14278",
            (
                ("forecast_mass_state", (("model", "centroidal_dynamics"),)),
                ("choose_contact_forces", (("constraint", "contact_feasibility"),)),
                ("realize_task_hierarchy", (("control", "whole_body_hierarchy"),)),
                ("verify_load_envelope", (("receipt", "structural_and_balance"),)),
            ),
        ),
        _hint(
            "prior:robotics:vision_conditioned_parkour",
            "parkour",
            "vision_conditioned_whole_body_humanoid_parkour",
            "https://arxiv.org/abs/2406.10759",
            (
                ("locate_affordance", (("perception", "terrain_affordance"),)),
                ("select_maneuver_basin", (("planning", "skill_basin"),)),
                ("shape_takeoff", (("flight", "takeoff_condition"),)),
                ("prepare_landing", (("flight", "landing_condition"),)),
            ),
        ),
        _hint(
            "prior:maneuver:forward_roll",
            "parkour",
            "biological_and_gymnastic_forward_roll_topology",
            "https://doi.org/10.1080/02701367.2012.10599865",
            (
                ("enter_with_directed_momentum", (
                    ("precondition", "forward_momentum"),
                    ("constraint", "head_contact_excluded"),
                )),
                ("lower_and_round", (
                    ("shape", "rounded_body"),
                    ("energy", "lower_center_of_mass"),
                )),
                ("progress_contact_chain", (
                    ("contact_order", "hands_upper_back_trunk"),
                    ("function", "distribute_impulse"),
                )),
                ("redirect_to_support", (
                    ("energy", "rotation_to_translation"),
                    ("exit", "support_reacquired"),
                )),
            ),
        ),
        _hint(
            "prior:maneuver:dynamic_high_alpha_cobra",
            "flight_maneuver",
            "high_alpha_dynamic_deceleration_maneuver",
            "https://www.nasa.gov/wp-content/uploads/2023/03/88314main_h-2399.pdf",
            (
                ("verify_entry_envelope", (
                    ("precondition", "control_authority_and_energy"),
                    ("constraint", "structural_envelope"),
                )),
                ("command_dynamic_pitch_up", (
                    ("aerodynamics", "rapid_angle_of_attack_increase"),
                    ("objective", "retain_attitude_authority"),
                )),
                ("hold_coupled_axes", (
                    ("constraint", "bound_sideslip_and_departure"),
                    ("energy", "exchange_speed_for_drag_and_attitude"),
                )),
                ("unload_and_recover", (
                    ("exit", "attached_or_controllable_flow"),
                    ("constraint", "recover_before_energy_floor"),
                )),
            ),
        ),
    ]


__all__ = ["seeded_motor_plan_hints"]
