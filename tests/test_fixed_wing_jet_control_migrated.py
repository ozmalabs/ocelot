from __future__ import annotations

import json
from pathlib import Path

from domains.fixed_wing_jet_world import (
    EFFECTOR_GROUP_COUNT,
    FixedWingDamageCondition,
    FixedWingJetWorld,
)
from domains.hidden_goal_landscape_world import HiddenGoalLandscapeWorld
from scripts import (
    gen_embodied_motor_program_seed,
    gen_embodied_structural_limits_seed,
    gen_hidden_goal_aerial_mission_seed,
)
from scripts.jabberwock_active_aero import (
    _settle_graph_request,
    _trial_tokens,
)
from scripts.jabberwock_fixed_wing_jet import _model_attrs
from domains.embodied_graph_transducer import add_unchecked_edge as _edge
from substrate.world_adapter import WorldAdapter
from scripts.jabberwock_hidden_goal_aerial_mission import (
    run_hidden_goal_mission,
)


ROOT = Path(__file__).resolve().parents[1]


def test_shared_motor_program_is_six_axis_vector_flow_and_default_capable():
    payload = gen_embodied_motor_program_seed.manifest()
    assert payload == json.loads(
        (ROOT / "seeds" / "embodied_motor_program.json").read_text()
    )
    assert "embodied_pareto_profile" in payload["depends_on"]
    assert gen_embodied_motor_program_seed.COMPONENTS == (
        "forward", "lateral", "vertical", "roll", "pitch", "turn", "normal_load"
    )
    serialized = json.dumps(payload)
    for feature in (
        "state_flow_forward",
        "state_flow_lateral",
        "state_flow_vertical",
        "state_power_state",
    ):
        assert feature in serialized
    names = {rule["name"] for rule in payload["rules"]}
    assert {
        "emp_release_internalized_program_default",
        "emp_internalize_receipt_grounded_program_default",
        "emp_retire_superseded_program_default",
    } <= names


def test_fixed_wing_plant_is_factorized_spooled_and_damageable():
    retained = [1.0] * EFFECTOR_GROUP_COUNT
    retained[0] = 0.0
    with FixedWingJetWorld(
        damage=FixedWingDamageCondition(1, tuple(retained))
    ) as world:
        options = world.actuator_options()
        assert len(options) == EFFECTOR_GROUP_COUNT * 3
        assert {row["group_ordinal"] for row in options} == {
            float(index) for index in range(EFFECTOR_GROUP_COUNT)
        }
        before = world.observe()["engine_power_state"][0]
        first = world.step_program(("jet_effector_002",))
        assert first["engine_power_state"][0] > before
        second = world.step_program(("jet_effector_002",))
        assert second["engine_power_state"][0] < first["engine_power_state"][0]
        assert second["position"][2] > 0.0


def test_ground_impact_limit_blocks_destructive_probe_and_external_overload_interrupts():
    structural = gen_embodied_structural_limits_seed.manifest()
    assert structural == json.loads(
        (ROOT / "seeds" / "embodied_structural_limits.json").read_text()
    )
    agent = WorldAdapter(seeds=("embodied_motor_program",))
    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "program_mode": "calibration",
        "program_request_seq": 0.0,
        "program_decision_seq": 0.0,
        "action_ready": 0.0,
        "decision_armed": 0.0,
        "decision_request_epoch": 0.0,
        "last_opened_decision_epoch": 0.0,
        "last_published_decision_epoch": 0.0,
        "last_program_trial_epoch": 0.0,
        "receipt_boundary_seq": 0.0,
        "recalibration_count": 0.0,
        "structural_limits_enabled": 1.0,
        "structural_specification_seq": 1.0,
        "state_structural_capacity_fraction": 1.0,
        "state_flow_speed_squared": 0.0,
        "state_flow_forward": 0.0,
        "state_flow_lateral": 0.0,
        "state_flow_vertical": 0.0,
        "state_power_state": 0.0,
        "target_forward": 1.0,
        "target_lateral": 0.0,
        "target_vertical": 0.0,
        "target_roll": 0.0,
        "target_pitch": 0.0,
        "target_turn": 0.0,
        "target_normal_load": 1.0,
    })
    _edge(agent, agent.agent, "has_embodied_motor_program_episode", episode)
    _edge(agent, agent.agent, "has_embodied_motor_episode", episode)
    component = {
        "component_code": "ground_structure_000",
        "material_code": "ground_material_000",
        "specification_confidence": 1.0,
        "fatigue_damage_per_second_at_limit": 0.0001,
    }
    for key in gen_embodied_structural_limits_seed.STRUCTURAL_LOADS:
        component[f"allowable_{key}"] = (
            300.0 if key == "impact_energy" else 100.0
        )
        component[f"load_fraction_{key}"] = 1.0
    component_node = agent.s.add_node("StructuralBodyComponent", component)
    _edge(agent, episode, "has_structural_body_component", component_node)

    base_spec = {
        key: 0.0
        for key in gen_embodied_structural_limits_seed.STRUCTURAL_LOADS
    }
    unsafe_spec = {**base_spec, "forward": 1.0, "impact_energy": 1_000.0}
    safe_spec = {**base_spec, "forward": 0.4, "impact_energy": 100.0}
    for ordinal, (token, spec) in enumerate((
        ("opaque_destructive_probe", unsafe_spec),
        ("opaque_safe_probe", safe_spec),
    )):
        option = {
            "token": token,
            "group_ordinal": 0.0,
            "activation_magnitude": 1.0,
            **{f"specified_{key}": value for key, value in spec.items()},
        }
        model = agent.s.add_node(
            "EmbodiedEffectorModel",
            _model_attrs(option, ordinal),
        )
        _edge(agent, episode, "has_embodied_effector_model", model)
    agent.tick()
    assert agent.s.node(episode)["attrs"]["state_safe_impact_energy"] == 200.0
    agent.inner.set_attr(episode, "program_request_seq", 1.0)
    _settle_graph_request(agent, episode, 1)
    trial = agent.inner.neighbours(
        episode, "has_embodied_motor_program_trial"
    )[0]
    assert _trial_tokens(agent, trial) == ("opaque_safe_probe",)

    outcome_attrs = {
        "request_seq": 1.0,
        "receipt_verified": 1.0,
        "processed": 0.0,
        "surprise_processed": 0.0,
        "action_duration_seconds": 0.1,
        "observed_damage_fraction": 0.0,
        **{
            f"observed_{key}": 250.0 if key == "impact_energy" else 0.0
            for key in gen_embodied_structural_limits_seed.STRUCTURAL_LOADS
        },
    }
    outcome = agent.s.add_node(
        "EmbodiedMotorProgramOutcome", outcome_attrs
    )
    _edge(agent, trial, "has_embodied_motor_program_outcome", outcome)
    agent.tick()
    envelope = agent.inner.neighbours(
        episode, "has_structural_body_envelope"
    )[0]
    assert agent.s.node(envelope)["attrs"]["failure"] == 0.0
    assert agent.s.node(envelope)["attrs"]["capacity_fraction"] > 0.0
    assert agent.s.node(episode)["attrs"]["structural_interrupt_required"] == 1.0

    overload = agent.s.add_node("EmbodiedMotorProgramOutcome", {
        **outcome_attrs,
        "request_seq": 2.0,
        "observed_impact_energy": 500.0,
    })
    _edge(agent, trial, "has_embodied_motor_program_outcome", overload)
    agent.tick()
    assert agent.s.node(envelope)["attrs"]["failure"] == 1.0
    assert agent.s.node(envelope)["attrs"]["capacity_fraction"] == 0.0
    assert agent.s.node(episode)["attrs"]["structural_interrupt_required"] == 1.0


def test_graph_infers_dynamic_mass_stiffness_and_nondestructive_limit_bounds():
    agent = WorldAdapter(seeds=("embodied_structural_limits",))
    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "structural_specification_seq": 0.0,
        "program_request_seq": 0.0,
        "state_fatigue_damage_per_second_at_limit": 0.0,
    })
    _edge(agent, agent.agent, "has_embodied_motor_program_episode", episode)
    agent.tick()
    envelope = agent.inner.neighbours(
        episode, "has_structural_body_envelope"
    )[0]

    def observe(
        seq: int,
        *,
        mass_kg: float,
        load: float,
        strain: float,
        residual_strain: float,
    ) -> None:
        trial = agent.s.add_node("EmbodiedMotorProgramTrial", {})
        outcome = agent.s.add_node("EmbodiedMotorProgramOutcome", {
            "request_seq": float(seq),
            "receipt_verified": 1.0,
            "structural_response_observed": 1.0,
            "observed_effective_mass_kg": mass_kg,
            "observed_gravity_m_s2": 9.80665,
            "observed_support_force_newtons": mass_kg * 9.80665,
            "observed_normal_load": load,
            "observed_strain_normal_load": strain,
            "observed_residual_strain_normal_load": residual_strain,
            "action_duration_seconds": 0.1,
            "observed_damage_fraction": 0.0,
            **{
                f"observed_{key}": 0.0
                for key in gen_embodied_structural_limits_seed.STRUCTURAL_LOADS
                if key != "normal_load"
            },
        })
        _edge(agent, episode, "has_embodied_motor_program_trial", trial)
        _edge(agent, trial, "has_embodied_motor_program_outcome", outcome)
        agent.tick()

    observe(1, mass_kg=70.0, load=2.0, strain=0.001, residual_strain=0.0)
    attrs = agent.s.node(envelope)["attrs"]
    assert attrs["baseline_mass_kg"] == 70.0
    assert attrs["reversible_limit_lower_normal_load"] == 2.0
    assert attrs["reference_stiffness_normal_load"] == 2_000.0

    observe(2, mass_kg=85.0, load=2.0, strain=0.002, residual_strain=0.0)
    attrs = agent.s.node(envelope)["attrs"]
    assert attrs["effective_mass_kg"] == 85.0
    assert attrs["payload_mass_delta_kg"] == 15.0
    assert attrs["stiffness_ratio_normal_load"] == 0.5
    assert attrs["safe_normal_load"] < attrs["rated_normal_load"]

    observe(3, mass_kg=85.0, load=3.0, strain=0.003, residual_strain=0.003)
    attrs = agent.s.node(envelope)["attrs"]
    assert attrs["reversible_limit_lower_normal_load"] == 2.0
    assert attrs["plastic_limit_upper_normal_load"] == 3.0
    assert attrs["inferred_rated_normal_load"] == 2.0


def test_hidden_goal_is_not_observed_and_graph_locates_then_marks_it():
    world = HiddenGoalLandscapeWorld()
    assert all("target" not in key for key in world.observe())
    payload = gen_hidden_goal_aerial_mission_seed.manifest()
    assert payload == json.loads(
        (ROOT / "seeds" / "hidden_goal_aerial_mission.json").read_text()
    )
    result = run_hidden_goal_mission()
    assert result["target_location_exposed_to_graph"] is False
    assert result["goal_marked"] == 1.0
    assert result["flare_count"] == 1.0
    first_flare = next(row for row in result["trace"] if row["flare_count"])
    assert first_flare["goal_located"] == 1.0
    assert all(row["flare_count"] == 0.0 for row in result["trace"][:-1])
    assert {row["semantics"] for row in result["models"]} == {"unknown"}


def test_checked_results_satisfy_preregistered_gates():
    aircraft = json.loads(
        (ROOT / "results" / "fixed_wing_jet_control_v1.json").read_text()
    )
    mission = json.loads(
        (ROOT / "results" / "hidden_goal_aerial_mission_v1.json").read_text()
    )
    primary = aircraft["primary"]
    assert primary["minimum_altitude_m"] > 0.0
    assert primary["recalibration_count"] == 1.0
    assert primary["maximum_program_width"] >= 2
    assert primary["internalized_reuse_latency"]["median_microseconds"] < 1_000.0
    assert (
        primary["fresh_synthesis_latency"]["median_microseconds"]
        > primary["internalized_reuse_latency"]["median_microseconds"]
    )
    assert all(
        2 not in row["groups"] for row in primary["trace"][-20:]
    )
    assert primary["structural_failure"] == 0.0
    assert primary["structural_capacity_fraction"] > 0.0
    assert primary["maximum_structural_utilization"] < 1.0
    assert set(primary["structural_utilization_by_load"]) == set(
        gen_embodied_structural_limits_seed.STRUCTURAL_LOADS
    )
    assert aircraft["unfamiliar_airframe"]["minimum_altitude_m"] > 0.0
    assert aircraft["unfamiliar_airframe"]["structural_failure"] == 0.0
    assert mission["goal_marked"] == 1.0
    assert mission["flare_count"] == 1.0


def test_the_plant_publishes_its_rate_ceiling_and_declares_no_stock():
    """THRUST IS NOT FREE ENERGY, and this plant now says half of why.

    `maximum_engine_thrust_newtons` and `mass_kg` were declared by
    `FixedWingParameters` from the day it was written and were never handed to
    the graph, so every consumer of this plant was free to read thrust as
    unbounded power.  They are published now.

    The other half is the one that matters more: this plant models NO FUEL, so
    it publishes no stock at all — and the adapter's translation of that
    absence is a `_measured` token set to zero, NOT a value of zero and NOT a
    missing key that reads as unbounded.  An unmeasured tank must not read as
    an empty one and must not read as an infinite one; what stands in for it is
    the general seed's own finite, non-increasing reserve
    (`control_regime_escalation` v7.0.0).
    """
    from scripts.jabberwock_fixed_wing_jet import _state_attrs

    world = FixedWingJetWorld()
    observation = world.observe()
    assert observation["maximum_engine_thrust_newtons"] > 0.0
    assert observation["vehicle_mass_kg"] > 0.0
    assert "remaining_fuel_kg" not in observation

    attrs = _state_attrs(observation)
    # the RATE ceiling is a measurement …
    assert attrs["state_maximum_thrust_n_measured"] == 1.0
    assert attrs["state_maximum_thrust_n"] == (
        observation["maximum_engine_thrust_newtons"]
    )
    assert attrs["state_vehicle_mass_kg_measured"] == 1.0
    # … and the AMOUNT ceiling is an honest absence, not a zero stock.
    assert attrs["state_remaining_fuel_kg_measured"] == 0.0
    assert attrs["state_fuel_specific_energy_j_kg_measured"] == 0.0
