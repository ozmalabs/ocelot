"""Run six-axis graph-native control of a factorized fixed-wing jet plant.

Python copies raw sensors and exact simulator receipts.  The Rust graph
calibrates opaque effectors, synthesizes simultaneous programs, learns vector
airflow/power-conditioned consequences, and reacts to hidden authority loss.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.embodied_graph_transducer import (  # noqa: E402
    add_unchecked_edge as _edge,
    pose_attrs,
    stamp_attrs,
    unique_neighbour,
    unique_node,
)
from domains.fixed_wing_jet_world import (  # noqa: E402
    EFFECTOR_GROUP_COUNT,
    FixedWingDamageCondition,
    FixedWingJetWorld,
    FixedWingParameters,
)
from scripts.gen_embodied_motor_program_seed import (  # noqa: E402
    COMPONENTS,
    FLOW_FEATURES,
)
from scripts.gen_embodied_structural_limits_seed import (  # noqa: E402
    STRUCTURAL_LOADS,
)
from scripts.jabberwock_active_aero import (  # noqa: E402
    _settle_graph_request,
    _trial_tokens,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


CONSEQUENCES = tuple(dict.fromkeys(
    (*COMPONENTS, "drag", "energy", *STRUCTURAL_LOADS)
))

# Opt-in regime-monitor diagnostics (GAMMA_REGIME_DIAGNOSTICS=1): the
# escalation contract's own attrs, copied verbatim into each trace row.
_REGIME_DIAGNOSTICS = bool(os.environ.get("GAMMA_REGIME_DIAGNOSTICS"))
_REGIME_DIAGNOSTIC_ATTRS = (
    "regime_absence_integral",
    "regime_evidence_seq",
    "regime_evidence_horizon_actions",
    "regime_best_error",
    "regime_error_ema",
    "regime_previous_error",
    "regime_deliberating",
    "regime_deliberation_integral",
    "regime_deliberation_opened_seq",
    "regime_pareto_minted_seq",
    "regime_policy_priority_axis_ordinal",
    "regime_escalation_requested",
    "regime_last_verdict",
    "regime_terminal",
    "f16_sink_rate_ema",
    "f16_yaw_rate_ema",
    # v5.0.0 order-N axis projection: the deadline each axis's own margin
    # stream projects, and the ORDER the held finite-difference recursion
    # measured on it (1 = velocity, 2 = acceleration, 3 = jerk, 0 = the
    # stream is incompressible at every order).  Both are read once per
    # deliberation opening, so a trace row carries the projection the
    # candidates were actually scored on.
    "f16_axis_clock_altitude",
    "f16_axis_clock_altitude_kept",
    "f16_axis_clock_altitude_order1",
    "f16_axis_clock_attitude",
    "f16_axis_clock_attitude_kept",
    "f16_roll_rate_measured",
    "f16_roll_authority_measured",
    "f16_axis_clock_heading",
    "f16_axis_clock_sideslip",
    "f16_axis_order_altitude",
    "f16_axis_order_altitude_kept",
    "f16_axis_order_attitude",
    "f16_axis_order_heading",
    "f16_axis_order_sideslip",
    # control_regime_escalation v6.0.0: the two projected clocks per channel
    # (actions until this channel's objective is unattainable; actions until
    # the escape it funds expires), their regime-level minima, and the
    # general contract attrs the gate acts on.
    "f16_axis_clock_option_altitude",
    "f16_axis_order_option_altitude",
    "f16_actions_to_transition_altitude",
    "f16_actions_to_transition_attitude",
    "f16_actions_to_transition_heading",
    "f16_actions_to_transition_sideslip",
    "f16_actions_to_option_loss",
    "regime_actions_to_transition",
    "regime_actions_to_option_loss",
    "regime_actions_to_act",
    "regime_class_gate_enabled",
    "regime_recalibration_requested",
    # control_regime_escalation v7.0.0 / f16_flight_path_control v8.0.0 --
    # THE TWO-COLUMN LEDGER.  What the plant published about its propulsion
    # stock and rate ceiling (with the `_measured` tokens that say whether it
    # published anything at all), the reserve the general seed holds against
    # it, and the two energy columns whose SUM is the quantity the monotonicity
    # prediction is about.
    "state_remaining_fuel_kg",
    "state_remaining_fuel_kg_measured",
    "state_maximum_thrust_n",
    "state_maximum_thrust_n_measured",
    "state_vehicle_mass_kg",
    "state_fuel_specific_energy_j_kg",
    "state_engine_thrust_n",
    "state_fuel_flow_kg_s",
    "f16_axis_clock_fuel",
    "f16_axis_order_fuel",
    "f16_reserve_actions",
    "regime_reserve_actions",
    "f16_energy_mechanical_m",
    "f16_energy_convertible_m",
    "f16_energy_total_m",
    # WHICH CORNERS WERE EVEN PROPOSED.  Each minting rule stamps the
    # deliberation opening it last minted for, so comparing these against
    # `regime_deliberation_opened_seq` says whether a corner was on the
    # frontier at all -- which is a different question from whether it lost,
    # and block H could not tell them apart without these.
    "f16_pareto_minted_seq_hold",
    "f16_pareto_minted_seq_trim",
    "f16_pareto_minted_seq_orbit",
    "f16_pareto_minted_seq_speed_priority",
    "f16_pareto_minted_seq_roll_priority",
    "regime_max_ordinal",
    # The INTERVENTIONAL authority instrument (f16_flight_path_control
    # v8.4.0): per actuator group, the mean prediction error over the actions
    # where that group was the SOLE commanded effector, and how many such
    # actions there were.  A count of zero means no evidence, not no error.
    *(
        f"f16_authority_{field}_g{group}"
        for group in range(4)
        for field in ("error_mean", "error_count", "log_mean",
                      "order", "samples")
    ),
    *(
        f"f16_track_{field}_g{group}"
        for group in range(4)
        for field in ("fail", "ok")
    ),
    # THE DIFFERENCE SHAPE: how far the learned effector map has moved from the
    # one held after calibration, against that map's own magnitude.  Healthy
    # flight holds it at ~0.04x; a fault exceeds 1x within 25 actions.
    "f16_shape_difference_sq",
    "f16_shape_reference_sq",
    "f16_shape_changed",
    # GOAL CONTAINMENT: how far each declared objective can still be driven
    # over the horizon by the best effector measured to affect it, how far it
    # must be driven to meet the want, and whether the want is outside reach.
    *(
        f"f16_{field}_{name}"
        for name in ("altitude", "heading", "speed")
        for field in ("manifold_reach", "goal_gap", "goal_margin",
                      "goal_outside")
    ),
    # decision_making_spike.md §103 rung: the budget/floor contract
    # (control_regime_escalation v7.12.0) and the two new leg-specific
    # measurements (resource-currency sunk cost; the declared threat region).
    "regime_viability_rung",
    "regime_rung_high_water",
    "regime_spend_floor",
    "regime_info_spend_floor",
    "regime_budget_exhausted",
    "regime_info_budget_exhausted",
    "regime_worth_in_rungs",
    "regime_info_worth_in_rungs",
    "regime_resource_spent_in_rungs",
    "regime_resource_spent_log",
    "regime_resource_decade",
    "f16_initial_fuel_kg",
    "f16_resource_fraction_remaining",
    "f16_threat_enabled",
    "f16_threat_initial_range_m",
    "f16_threat_closing_rate_m_s",
    "f16_threat_region_actions",
    "f16_threat_region_inside",
    "f16_probe_stopped",
    "f16_probe_stopped_seq",
)


def _state_attrs(observation: dict[str, Any]) -> dict[str, float]:
    flow = tuple(float(value) for value in observation["body_air_velocity"])
    velocity = tuple(float(value) for value in observation["linear_velocity"])
    rates = tuple(float(value) for value in observation["body_angular_velocity"])
    power_state = sum(observation["engine_power_state"]) / len(
        observation["engine_power_state"]
    )
    qx, qy, qz, qw = (
        float(value) for value in observation["orientation_xyzw"]
    )
    roll_angle = math.atan2(
        2.0 * (qw * qx + qy * qz),
        1.0 - 2.0 * (qx * qx + qy * qy),
    )
    pitch_angle = math.asin(max(
        -1.0,
        min(1.0, 2.0 * (qw * qy - qz * qx)),
    ))
    yaw_angle = math.atan2(
        2.0 * (qw * qz + qx * qy),
        1.0 - 2.0 * (qy * qy + qz * qz),
    )
    attrs = {
        "state_vx": velocity[0],
        "state_vy": velocity[1],
        "state_vz": velocity[2],
        "state_body_vx": flow[0],
        "state_body_vy": flow[1],
        "state_body_vz": flow[2],
        "state_body_wx": rates[0],
        "state_body_wy": rates[1],
        "state_body_wz": rates[2],
        "state_flow_speed_squared": sum(value * value for value in flow),
        "state_flow_forward": flow[0],
        "state_flow_lateral": flow[1],
        "state_flow_vertical": flow[2],
        "state_power_state": float(power_state),
        "state_roll_angle": roll_angle,
        "state_pitch_angle": pitch_angle,
        "state_yaw_angle": yaw_angle,
        "state_angle_of_attack": float(
            observation.get("angle_of_attack_radians", 0.0)
        ),
        "state_sideslip": float(
            observation.get("sideslip_radians", 0.0)
        ),
        "state_altitude_m": float(observation["position"][2]),
        "state_gravity_m_s2": float(observation.get("gravity_m_s2", 0.0)),
        "state_true_airspeed_m_s": float(
            observation.get(
                "true_airspeed_m_s",
                math.sqrt(sum(value * value for value in flow)),
            )
        ),
    }
    # THE PROPULSION LEDGER, copied only where the plant publishes it.
    #
    # Every key here is a plain copy of a number the world adapter already
    # produced -- no decision, no derivation.  The one conditional is the
    # first-class-absence token: a plant that does not publish a column leaves
    # BOTH its value and its `_measured` flag at zero, and the consumer seed
    # reads that flag rather than guessing from a magnitude.  An unpublished
    # tank must not read as an empty one, and must not read as an infinite one
    # either; what it reads as is UNKNOWN, and the general seed's own finite
    # non-increasing bound is what stands in for it.
    for observed_key, attr in (
        ("remaining_fuel_kg", "state_remaining_fuel_kg"),
        ("fuel_specific_energy_j_per_kg", "state_fuel_specific_energy_j_kg"),
        ("maximum_engine_thrust_newtons", "state_maximum_thrust_n"),
        ("vehicle_mass_kg", "state_vehicle_mass_kg"),
        ("engine_thrust_newtons", "state_engine_thrust_n"),
        ("fuel_flow_kg_s", "state_fuel_flow_kg_s"),
    ):
        value = observation.get(observed_key)
        attrs[f"{attr}_measured"] = 0.0 if value is None else 1.0
        attrs[attr] = 0.0 if value is None else float(value)
    current_structural_loads = {
        "normal_load": abs(float(observation["normal_load_factor"])),
        "peak_force": float(observation["peak_force_newtons"]),
        "impulse": float(observation["impulse_newton_seconds"]),
        "impact_energy": float(observation["impact_energy_joules"]),
        "thermal_load": float(observation["thermal_load_joules"]),
        "dynamic_pressure": float(observation["dynamic_pressure_pascals"]),
        "roll_moment": float(observation["roll_moment_newton_metres"]),
        "pitch_moment": float(observation["pitch_moment_newton_metres"]),
        "yaw_moment": float(observation["yaw_moment_newton_metres"]),
        "heat_flux": float(observation["heat_flux_watts_per_square_metre"]),
        "skin_temperature": float(observation["skin_temperature_kelvin"]),
    }
    attrs.update({
        f"state_current_{key}": value
        for key, value in current_structural_loads.items()
    })
    return attrs


# The airframe's own group, numbered above the commandable surfaces.
_PLANT_EFFECTOR_GROUP = 4


def _model_attrs(option: dict[str, Any], ordinal: int) -> dict[str, Any]:
    specified_effect_samples = float(
        option.get("specified_effect_equivalent_samples", 0.0)
    )
    vector_norm = math.sqrt(sum(
        float(option.get(f"specified_mean_{key}", 0.0)) ** 2
        for key in COMPONENTS
    ))
    attrs: dict[str, Any] = {
        "token": option["token"],
        "ordinal": float(ordinal),
        "actuator_group": float(option["group_ordinal"]),
        "activation_magnitude": float(option["activation_magnitude"]),
        # These are offline design-analysis bounds, not limits inferred by
        # risking the airframe during calibration.
        "structural_certified_default": 1.0,
        "available": 1.0,
        "log_authority": 0.0,
        # Log magnitude of the effect vector.  Candidate admissibility uses
        # this together with log_authority, so weak/uncertain vectors do not
        # compete as if they had the same control leverage as other surfaces.
        "log_vector_weight": math.log(max(vector_norm, 1.0e-6)),
        "experience_count": specified_effect_samples,
        "specified_effect_prior_confidence": float(
            option.get("specified_effect_prior_confidence", 0.0)
        ),
        "specified_actuator_dynamics_enabled": float(
            option.get("specified_actuator_dynamics_enabled", 0.0)
        ),
        "specified_command_level": float(
            option.get("specified_command_level", 0.0)
        ),
        "specified_maximum_position_change_per_action": float(
            option.get(
                "specified_maximum_position_change_per_action",
                0.0,
            )
        ),
        "state_effector_position": 0.0,
        "last_learning_seq": 0.0,
        "render_choice_seq": 0.0,
        "recalibration_required": 0.0,
        "mean_flow_speed_squared": 0.0,
        "flow_variance_sum": 0.0,
        "semantics": "unknown",
    }
    for feature in FLOW_FEATURES:
        attrs[f"mean_{feature}"] = 0.0
        attrs[f"{feature}_variance_sum"] = 0.0
    for key in CONSEQUENCES:
        attrs[f"mean_{key}"] = float(
            option.get(f"specified_mean_{key}", 0.0)
        )
        attrs[f"specified_passive_mean_{key}"] = float(
            option.get(f"specified_passive_mean_{key}", 0.0)
        )
        attrs[f"specified_position_gain_{key}"] = float(
            option.get(f"specified_position_gain_{key}", 0.0)
        )
        attrs[f"flow_gain_{key}"] = 0.0
        attrs[f"flow_covariance_{key}"] = 0.0
        for feature in FLOW_FEATURES:
            attrs[f"{feature}_gain_{key}"] = 0.0
            attrs[f"{feature}_covariance_{key}"] = 0.0
    for key in STRUCTURAL_LOADS:
        attrs[f"specified_{key}"] = float(option[f"specified_{key}"])
    return attrs


def _outcome_attrs(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    request_seq: int,
) -> dict[str, Any]:
    pre_velocity = tuple(float(value) for value in before["linear_velocity"])
    post_velocity = tuple(float(value) for value in after["linear_velocity"])
    pre_body = tuple(float(value) for value in before["body_air_velocity"])
    post_body = tuple(float(value) for value in after["body_air_velocity"])
    pre_rates = tuple(float(value) for value in before["body_angular_velocity"])
    post_rates = tuple(float(value) for value in after["body_angular_velocity"])
    pre_power = sum(before["engine_power_state"]) / len(
        before["engine_power_state"]
    )
    observed = {
        "forward": abs(post_body[0] - pre_body[0]),
        "lateral": abs(post_body[1] - pre_body[1]),
        "vertical": abs(post_body[2] - pre_body[2]),
        # Direction is indispensable to closed-loop stabilization.  Loads are
        # magnitudes below, but angular consequences remain signed so the graph
        # can synthesize an opposing effector combination.
        "roll": post_rates[0] - pre_rates[0],
        "pitch": post_rates[1] - pre_rates[1],
        "turn": post_rates[2] - pre_rates[2],
        "normal_load": abs(float(after["normal_load_factor"])),
        "peak_force": float(after["peak_force_newtons"]),
        "impulse": float(after["impulse_newton_seconds"]),
        "impact_energy": float(after["impact_energy_joules"]),
        "thermal_load": float(after["thermal_load_joules"]),
        "dynamic_pressure": float(after["dynamic_pressure_pascals"]),
        "roll_moment": float(after["roll_moment_newton_metres"]),
        "pitch_moment": float(after["pitch_moment_newton_metres"]),
        "yaw_moment": float(after["yaw_moment_newton_metres"]),
        "heat_flux": float(after["heat_flux_watts_per_square_metre"]),
        "skin_temperature": float(after["skin_temperature_kelvin"]),
    }
    return {
        **pose_attrs(before, "pre"),
        **pose_attrs(after, "post"),
        **{
            f"pre_v{axis}": value
            for axis, value in zip(("x", "y", "z"), pre_velocity)
        },
        **{
            f"post_v{axis}": value
            for axis, value in zip(("x", "y", "z"), post_velocity)
        },
        **{
            f"pre_body_v{axis}": value
            for axis, value in zip(("x", "y", "z"), pre_body)
        },
        **{
            f"post_body_v{axis}": value
            for axis, value in zip(("x", "y", "z"), post_body)
        },
        **{
            f"pre_body_w{axis}": value
            for axis, value in zip(("x", "y", "z"), pre_rates)
        },
        **{
            f"post_body_w{axis}": value
            for axis, value in zip(("x", "y", "z"), post_rates)
        },
        "pre_flow_forward": pre_body[0],
        "pre_flow_lateral": pre_body[1],
        "pre_flow_vertical": pre_body[2],
        "pre_power_state": float(pre_power),
        **{f"observed_{key}": value for key, value in observed.items()},
        "observed_damage_fraction": float(
            after["observed_damage_fraction"]
        ),
        "action_duration_seconds": (
            float(after["sim_time_seconds"])
            - float(before["sim_time_seconds"])
        ),
        "normal_load_factor": float(after["normal_load_factor"]),
        "aerodynamic_dissipation_joules": float(
            after["aerodynamic_dissipation_joules"]
        ),
        "input_energy_joules": float(after["input_energy_joules"]),
        "external_normal_force_newtons": 0.0,
        "body_weight_newtons": 1.0,
        "request_seq": float(request_seq),
        "receipt_verified": 1.0,
        "processed": 0.0,
        "surprise_processed": 0.0,
        "provenance_kind": "raw_six_axis_fixed_wing_receipt",
    }


def _run(
    *,
    steps: int,
    parameters: FixedWingParameters | None,
    wind_velocity: tuple[float, float, float],
    damage: FixedWingDamageCondition | None,
    world_adapter: Any | None = None,
    target_overrides: dict[str, float] | None = None,
    policy_overrides: dict[str, float] | None = None,
    episode_overrides: dict[str, float] | None = None,
    reference_schedule: Sequence[
        tuple[int, dict[str, float]]
    ] | None = None,
    seeds: tuple[str, ...] = ("embodied_motor_program",),
    capture_plant_failure: bool = False,
) -> dict[str, Any]:
    agent = WorldAdapter(seeds=seeds)
    policy = unique_node(agent, "EmbodiedMotorProgramPolicy")
    policy_attrs = {
        "calibration_samples": 2.0,
        "minimum_calibration_flow_speed_squared": 0.0,
        "compound_surprise_threshold": 10.0,
        "relative_normal_load_surprise": 0.75,
        "maximum_recalibration_cycles": 1.0,
        "maximum_default_program_reuse_cycles": 4.0,
        "contextual_effector_prediction_enabled": 1.0,
        "parallel_factorized_composition_enabled": 0.0,
        "forward_weight": 12.0,
        "lateral_weight": 10.0,
        "vertical_weight": 10.0,
        "roll_weight": 35.0,
        "pitch_weight": 45.0,
        "turn_weight": 25.0,
        "normal_load_weight": 6.0,
        "drag_weight": 0.00000002,
        "energy_weight": 0.000000002,
        "activation_weight": 0.002,
    }
    policy_attrs.update(policy_overrides or {})
    stamp_attrs(agent, policy, policy_attrs)
    world_context = world_adapter or FixedWingJetWorld(
        parameters=parameters,
        wind_velocity=wind_velocity,
        damage=damage,
    )
    with world_context as world:
        observation = world.reset()
        targets = {
            "target_forward": 0.025,
            "target_lateral": 0.0,
            "target_vertical": 0.0,
            "target_roll": 0.012,
            "target_pitch": 0.010,
            "target_turn": 0.006,
            "target_normal_load": 1.0,
        }
        targets.update(target_overrides or {})
        episode_attrs = {
            "program_mode": "calibration",
            "six_axis_receipts": 1.0,
            "program_request_seq": 0.0,
            "program_decision_seq": 0.0,
            "action_ready": 0.0,
            "calibration_complete": 0.0,
            "recalibration_count": 0.0,
            "default_program_reuse_count": 0.0,
            "structural_limits_enabled": 1.0,
            "structural_specification_seq": 1.0,
            "state_structural_capacity_fraction": 1.0,
            "structural_interrupt_required": 0.0,
            "authority_escape_mode": 0.0,
            "authority_escape_reason": "none",
            "maximum_program_width": float(world.effector_group_count),
            "decision_armed": 0.0,
            "decision_request_epoch": 0.0,
            "last_opened_decision_epoch": 0.0,
            "last_published_decision_epoch": 0.0,
            "last_program_trial_epoch": 0.0,
            "receipt_boundary_seq": 0.0,
            **targets,
            **_state_attrs(observation),
        }
        episode_attrs.update(episode_overrides or {})
        episode = agent.s.add_node(
            "EmbodiedMotorProgramEpisode",
            episode_attrs,
        )
        _edge(agent, agent.agent, "has_embodied_motor_program_episode", episode)
        _edge(agent, agent.agent, "has_embodied_motor_episode", episode)
        # The episode doubles as the control-regime holder for the general
        # control_regime_escalation seed; its rules are opt-in via the
        # regime_monitor_enabled episode attr.
        _edge(agent, agent.agent, "holds_control_regime", episode)
        options = list(world.actuator_options())
        for ordinal, option in enumerate(options):
            model = agent.s.add_node(
                "EmbodiedEffectorModel",
                _model_attrs(option, ordinal),
            )
            _edge(agent, episode, "has_embodied_effector_model", model)
        # THE PLANT, DECLARED AS A CONTRIBUTOR.
        #
        # The airframe was commanded once, at construction, to have a
        # particular response, and has been executing that command ever since.
        # Its deviation from that command is a deviation from command in
        # exactly the sense every other effector already uses -- which is why
        # it needs no new machinery, only a node.
        #
        # `never_commanded` is the effector contract's flag for a contributor
        # that is OBSERVED and LEARNED but never selected into a motor program
        # (embodied_motor_program v1.9.0).  Without it the composer issues this
        # model's token and the world is asked to fly the airframe as if it
        # were a surface.
        #
        # ONE contributor, not one per wing: which part changed is not
        # something the frame should be told.
        plant = agent.s.add_node("EmbodiedEffectorModel", {
            "token": "plant",
            "ordinal": float(len(options)),
            "actuator_group": float(_PLANT_EFFECTOR_GROUP),
            "activation_magnitude": 1.0,
            "structural_certified_default": 1.0,
            # An ORDINARY effector with zero authority -- no special class.
            # The probe ladder will discover it never answers, exactly as it
            # discovers a jammed rudder, and the authority machinery will price
            # it accordingly.  Nothing here declares that; it is measured.
            "available": 1.0,
            "log_authority": 0.0,
            "log_vector_weight": math.log(1.0e-6),
            "experience_count": 0.0,
            "specified_effect_prior_confidence": 0.0,
            "specified_actuator_dynamics_enabled": 0.0,
            "specified_command_level": 1.0,
            "specified_maximum_position_change_per_action": 0.0,
            "state_effector_position": 1.0,
            "last_learning_seq": 0.0,
        })
        _edge(agent, episode, "has_embodied_effector_model", plant)
        effector_models = agent.inner.neighbours(
            episode, "has_embodied_effector_model"
        )

        def stamp_effector_positions(state: dict[str, Any]) -> None:
            positions = state.get("effector_position")
            if positions is None:
                return
            for model in effector_models:
                group = int(
                    agent.s.node(model)["attrs"]["actuator_group"]
                )
                agent.inner.set_attr(
                    model,
                    "state_effector_position",
                    float(positions[group])
                    if group < len(positions)
                    # The plant's position is not an actuator position: a rule
                    # moves it from measured conformance to construction.
                    else float(agent.s.node(model)["attrs"]
                               .get("state_effector_position", 1.0)),
                )

        stamp_effector_positions(observation)
        structural_nodes = []
        for component in world.structural_components():
            node = agent.s.add_node("StructuralBodyComponent", component)
            _edge(agent, episode, "has_structural_body_component", node)
            structural_nodes.append(node)
        for source, target in zip(structural_nodes, structural_nodes[1:]):
            _edge(agent, source, "transfers_structural_load_to", target)
        agent.tick()

        trace = []
        graph_latencies_ns = []
        reuse_latencies_ns = []
        synthesis_latencies_ns = []
        plant_failure: str | None = None
        previous_airspeed_fps: float | None = None
        for request_seq in range(1, steps + 1):
            scheduled_reference: dict[str, float] = {}
            for onset_action, reference_attrs in reference_schedule or ():
                if request_seq - 1 >= onset_action:
                    scheduled_reference = reference_attrs
            stamp_effector_positions(observation)
            altitude_m = float(observation["position"][2])
            altitude_rate_m_s = float(observation["linear_velocity"][2])
            airspeed_fps = (
                sum(value * value for value in observation["body_air_velocity"])
                ** 0.5
                / 0.3048
            )
            airspeed_rate_fps_s = (
                0.0
                if previous_airspeed_fps is None
                else (
                    airspeed_fps - previous_airspeed_fps
                ) / max(world.action_duration_seconds, 1.0e-9)
            )
            recovery_horizon_s = max(
                world.action_duration_seconds,
                world.effector_group_count * world.action_duration_seconds,
            )
            predicted_altitude_m = (
                altitude_m + altitude_rate_m_s * recovery_horizon_s
            )
            predicted_airspeed_fps = (
                airspeed_fps + airspeed_rate_fps_s * recovery_horizon_s
            )
            escape_mode = (
                predicted_altitude_m <= 0.0
                or predicted_airspeed_fps <= 0.0
            )
            previous_airspeed_fps = airspeed_fps
            stamp_attrs(agent, episode, {
                **_state_attrs(observation),
                **scheduled_reference,
                "program_request_seq": float(request_seq),
                "regime_clock_seq": float(request_seq),
                "action_ready": 0.0,
                "authority_escape_mode": 1.0 if escape_mode else 0.0,
                "authority_escape_reason": (
                    "low_altitude_or_airspeed" if escape_mode else "none"
                ),
            })
            before_request_attrs = dict(agent.s.node(episode)["attrs"])
            reuse_count_before = float(
                before_request_attrs.get("default_program_reuse_count", 0.0)
            )
            mode_before = str(before_request_attrs["program_mode"])
            started = time.perf_counter_ns()
            _settle_graph_request(agent, episode, request_seq)
            request_latency_ns = time.perf_counter_ns() - started
            graph_latencies_ns.append(request_latency_ns)
            released_attrs = dict(agent.s.node(episode)["attrs"])
            default_reused = (
                mode_before == "synthesis"
                and float(
                    released_attrs.get("default_program_reuse_count", 0.0)
                ) > reuse_count_before
            )
            if default_reused:
                reuse_latencies_ns.append(request_latency_ns)
            elif mode_before == "synthesis":
                synthesis_latencies_ns.append(request_latency_ns)
            trial = unique_neighbour(
                agent,
                episode,
                "has_embodied_motor_program_trial",
                attrs={"status": "issued", "request_seq": float(request_seq)},
                description=f"fixed-wing trial {request_seq}",
            )
            tokens = _trial_tokens(agent, trial)
            before = observation
            try:
                observation = world.step_program(tokens)
            except (ArithmeticError, RuntimeError) as exc:
                if not capture_plant_failure:
                    raise
                plant_failure = f"{type(exc).__name__}: {exc}"
                break
            if tuple(observation["last_motor_program_tokens"]) != tokens:
                raise RuntimeError("plant receipt does not match graph program")
            outcome = agent.s.add_node(
                "EmbodiedMotorProgramOutcome",
                _outcome_attrs(before, observation, request_seq=request_seq),
            )
            _edge(agent, trial, "has_embodied_motor_program_outcome", outcome)
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            agent.inner.set_attr(episode, "receipt_boundary_seq", float(request_seq))
            agent.tick()
            program = agent.inner.neighbours(
                trial, "enacts_embodied_motor_program"
            )[0]
            episode_attrs = agent.s.node(episode)["attrs"]
            trace.append({
                "request_seq": request_seq,
                "tokens": list(tokens),
                "groups": [
                    int(agent.s.node(model)["attrs"]["actuator_group"])
                    for model in agent.inner.neighbours(
                        trial, "commands_embodied_effector_model"
                    )
                ],
                "member_count": len(tokens),
                "default_reused": default_reused,
                "program_mode": episode_attrs["program_mode"],
                "recalibration_count": episode_attrs["recalibration_count"],
                "regime_ordinal": float(
                    episode_attrs.get("regime_ordinal", 0.0)
                ),
                "regime_escalation_count": float(
                    episode_attrs.get("regime_escalation_count", 0.0)
                ),
                "flight_path_trim_active": float(
                    episode_attrs.get("flight_path_trim_active", 0.0)
                ),
                "flight_path_orbit_active": float(
                    episode_attrs.get("flight_path_orbit_active", 0.0)
                ),
                "flight_path_speed_priority_active": float(
                    episode_attrs.get("flight_path_speed_priority_active", 0.0)
                ),
                "flight_path_roll_priority_active": float(
                    episode_attrs.get("flight_path_roll_priority_active", 0.0)
                ),
                "flight_path_trim_body_vy": float(
                    episode_attrs.get("flight_path_trim_body_vy", 0.0)
                ),
                "prediction_error_energy": agent.s.node(program)["attrs"].get(
                    "prediction_error_energy", 0.0
                ),
                # Published for the descent probe: the budget the composer
                # prices, and the ladder rung that names why.
                "margin_actions": float(
                    episode_attrs.get("margin_actions", -1.0)
                ),
                "f16_viability_rung": float(
                    episode_attrs.get("f16_viability_rung", -1.0)
                ),
                "altitude_m": observation["position"][2],
                "airspeed_m_s": sum(
                    value * value for value in observation["body_air_velocity"]
                ) ** 0.5,
                "normal_load_factor": observation["normal_load_factor"],
                "angle_of_attack_radians": observation[
                    "angle_of_attack_radians"
                ],
                "sideslip_radians": float(
                    observation.get("sideslip_radians", 0.0)
                ),
                "body_rates": list(observation["body_angular_velocity"]),
                "attitude_angles": [
                    _state_attrs(observation)["state_roll_angle"],
                    _state_attrs(observation)["state_pitch_angle"],
                    _state_attrs(observation)["state_yaw_angle"],
                ],
                "target_body_rate_delta": [
                    float(released_attrs["target_roll"]),
                    float(released_attrs["target_pitch"]),
                    float(released_attrs["target_turn"]),
                ],
                "target_consequence_delta": {
                    key: float(released_attrs[f"target_{key}"])
                    for key in (
                        "forward",
                        "lateral",
                        "vertical",
                        "roll",
                        "pitch",
                        "turn",
                        "normal_load",
                    )
                },
                "reference_altitude_m": float(
                    episode_attrs.get("reference_altitude_m", 0.0)
                ),
                "reference_heading_rad": float(
                    episode_attrs.get("reference_heading_rad", 0.0)
                ),
                "reference_true_airspeed_m_s": float(
                    episode_attrs.get("reference_true_airspeed_m_s", 0.0)
                ),
                "flight_path_errors": [
                    float(episode_attrs.get(
                        "flight_path_altitude_error_m", 0.0
                    )),
                    float(episode_attrs.get(
                        "flight_path_heading_error_rad", 0.0
                    )),
                    float(episode_attrs.get(
                        "flight_path_airspeed_error_m_s", 0.0
                    )),
                ],
                "effector_position": list(
                    observation.get("effector_position", ())
                ),
                "ground_contact": bool(
                    observation.get("ground_contact", False)
                ),
                "gust_ned_fps": list(
                    observation.get("gust_ned_fps", ())
                ),
                "damage_active": bool(
                    observation.get(
                        "failure_active",
                        damage is not None
                        and request_seq - 1 >= damage.onset_action,
                    )
                ),
                **(
                    {"mach": float(observation["mach"])}
                    if "mach" in observation else {}
                ),
                # Regime-monitor diagnostics: mechanical read-back of the
                # escalation contract's own attrs, opt-in via
                # GAMMA_REGIME_DIAGNOSTICS so ordinary runs keep their
                # trace shape.  Diagnosing why a deliberation opened
                # requires the integrator's own state, not just the
                # regime it published.
                **(
                    {
                        key: float(episode_attrs.get(key, 0.0))
                        for key in _REGIME_DIAGNOSTIC_ATTRS
                    }
                    if _REGIME_DIAGNOSTICS else {}
                ),
                **(
                    {
                        "dynamic_pressure_pascals": float(
                            observation["dynamic_pressure_pascals"]
                        ),
                        "skin_temperature_kelvin": float(
                            observation["skin_temperature_kelvin"]
                        ),
                        "heat_flux_watts_per_square_metre": float(
                            observation[
                                "heat_flux_watts_per_square_metre"
                            ]
                        ),
                    }
                    if "mach" in observation else {}
                ),
            })
        ordered = sorted(graph_latencies_ns)
        ordered_reuse = sorted(reuse_latencies_ns)
        ordered_synthesis = sorted(synthesis_latencies_ns)

        def latency_summary(samples: list[int]) -> dict[str, float]:
            if not samples:
                return {"count": 0.0}
            return {
                "count": float(len(samples)),
                "median_microseconds": samples[len(samples) // 2] / 1_000.0,
                "p99_microseconds": (
                    samples[round((len(samples) - 1) * 0.99)] / 1_000.0
                ),
            }

        structural_envelope = unique_neighbour(
            agent,
            episode,
            "has_structural_body_envelope",
            attrs={},
            description="fixed-wing structural envelope",
        )
        structural_attrs = agent.s.node(structural_envelope)["attrs"]
        return {
            "steps": steps,
            "pareto_profile_core": "embodied_pareto_profile",
            "control_objectives_scalarized": False,
            "completed_steps": len(trace),
            "plant_failure": plant_failure,
            "effector_groups": world.effector_group_count,
            "primitive_options": len(world.actuator_options()),
            "materialized_compound_lattice": False,
            "wind_velocity": list(wind_velocity),
            "damage_onset": None if damage is None else damage.onset_action,
            "recalibration_count": agent.s.node(episode)["attrs"][
                "recalibration_count"
            ],
            "maximum_program_width": max(
                (row["member_count"] for row in trace),
                default=0,
            ),
            "minimum_altitude_m": min(
                (row["altitude_m"] for row in trace),
                default=float(observation["position"][2]),
            ),
            "maximum_absolute_body_rate": max(
                (
                    abs(value)
                    for row in trace
                    for value in row["body_rates"]
                ),
                default=0.0,
            ),
            "graph_request_latency_median_microseconds": (
                ordered[len(ordered) // 2] / 1_000.0
            ),
            "graph_request_latency_p99_microseconds": (
                ordered[round((len(ordered) - 1) * 0.99)] / 1_000.0
            ),
            "internalized_reuse_latency": latency_summary(ordered_reuse),
            "fresh_synthesis_latency": latency_summary(ordered_synthesis),
            "structural_capacity_fraction": structural_attrs[
                "capacity_fraction"
            ],
            "maximum_structural_utilization": structural_attrs[
                "maximum_observed_utilization"
            ],
            "structural_failure": structural_attrs["failure"],
            "safe_normal_load_factor": structural_attrs[
                "safe_normal_load"
            ],
            "maximum_mach": max(
                (row.get("mach", 0.0) for row in trace),
                default=0.0,
            ),
            "structural_utilization_by_load": {
                key: structural_attrs[f"maximum_{key}_utilization"]
                for key in STRUCTURAL_LOADS
            },
            "trace": trace,
        }


def run_fixed_wing_experiment(
    *,
    steps: int = 190,
    damage_onset: int | None = 70,
    broken_group: int = 2,
) -> dict[str, Any]:
    if steps < 1:
        raise ValueError("steps must be positive")
    if broken_group not in range(EFFECTOR_GROUP_COUNT):
        raise ValueError("broken_group must identify an effector group")
    damage = None
    if damage_onset is not None:
        retained = [1.0] * EFFECTOR_GROUP_COUNT
        retained[broken_group] = 0.0
        damage = FixedWingDamageCondition(
            onset_action=damage_onset,
            retained_authority=tuple(retained),
        )
    primary = _run(
        steps=steps,
        parameters=FixedWingParameters(),
        wind_velocity=(0.0, 5.0, 0.0),
        damage=damage,
    )
    transfer = _run(
        steps=min(90, steps),
        parameters=FixedWingParameters(
            mass_kg=8_450.0,
            wing_area_m2=31.0,
            span_m=11.2,
            chord_m=3.4,
            roll_inertia_kg_m2=17_000.0,
            pitch_inertia_kg_m2=57_000.0,
            yaw_inertia_kg_m2=65_000.0,
            maximum_engine_thrust_newtons=13_500.0,
            engine_spool_seconds=1.15,
        ),
        wind_velocity=(2.0, -7.0, 0.5),
        damage=None,
    )
    return {"primary": primary, "unfamiliar_airframe": transfer}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=190)
    parser.add_argument("--damage-onset", type=int, default=70)
    parser.add_argument("--broken-group", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_fixed_wing_experiment(
        steps=args.steps,
        damage_onset=args.damage_onset,
        broken_group=args.broken_group,
    )
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
