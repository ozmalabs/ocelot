"""Numeric, plant-independent checks for the native learned projection."""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter


def _edge(agent, a, edge, b):
    try:
        agent.inner.add_edge_unchecked(a, edge, b, {})
    except TypeError:
        agent.inner.add_edge_unchecked(a, edge, b)


def _term(field, *, addition=False):
    term = {
        "type": "FutureManifoldProjection", "episode": {"type": "Var", "name": "ep"},
        "policy": {"type": "Var", "name": "po"},
        "source": {"type": "Var", "name": "src"}, "field": field,
    }
    if addition:
        term["addition"] = {"type": "Var", "name": "addition"}
    return term


def _bench(*, member_forward=0.0, bound=1.0, neutral_forward=0.0,
           context_delta_forward=0.0, context_gain_forward=0.0,
           member_context_count=2.0, specified_prior=False,
           contextual_prediction=True):
    try:
        agent = WorldAdapter(seeds=("embodied_motor_program",))
    except RuntimeError as exc:
        pytest.skip(str(exc))
    root = agent.agent
    policy = agent.inner.neighbours(root, "has_embodied_motor_program_policy")[0]
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 16.0)
    # Keep the focused fixture's historical horizon bounded; production seed
    # policy defaults to the larger explicit physical horizon.
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 16.0)
    agent.inner.set_attr(policy, "future_manifold_path_fixed_point_run", 1.0)
    agent.inner.set_attr(
        policy, "contextual_effector_prediction_enabled",
        1.0 if contextual_prediction else 0.0,
    )
    for key in ("lateral", "vertical", "roll", "pitch", "turn", "normal_load"):
        agent.inner.set_attr(policy, f"{key}_weight", 0.0)
    agent.inner.set_attr(policy, "forward_weight", 1.0)
    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "target_forward": 0.0, "target_lateral": 0.0, "target_vertical": 0.0,
        "target_roll": 0.0, "target_pitch": 0.0, "target_turn": 0.0,
        "target_normal_load": 0.0, "state_flow_forward": 0.0,
        "state_flow_lateral": 0.0, "state_flow_vertical": 0.0,
        "state_power_state": 0.0, "manifold_bound_forward": bound,
        "manifold_bound_lateral": bound, "manifold_bound_vertical": bound,
        "manifold_bound_roll": bound, "manifold_bound_pitch": bound,
        "manifold_bound_turn": bound, "program_request_seq": 101.0,
    })
    _edge(agent, root, "has_embodied_motor_program_episode", episode)
    source = agent.s.add_node("EmbodiedMotorProgram", {"member_count": 1.0})
    _edge(agent, episode, "has_active_embodied_motor_program", source)
    common = {
        "actuator_group": 0.0, "ordinal": 1.0, "experience_count": 2.0,
        "context_delta_experience_count": member_context_count,
        "activation_magnitude": 1.0,
        "state_effector_position": 0.0, "specified_command_level": 0.0,
        "specified_maximum_position_change_per_action": 1.0,
        "mean_context_delta_flow_forward": context_delta_forward,
        "mean_context_delta_flow_lateral": 0.0,
        "mean_context_delta_flow_vertical": 0.0,
        "mean_context_delta_power_state": 0.0,
    }
    member = agent.s.add_node("EmbodiedEffectorModel", {
        **common, "token": "member", "mean_forward": member_forward,
        "flow_forward_gain_forward": context_gain_forward,
        "specified_actuator_dynamics_enabled": 1.0 if specified_prior else 0.0,
        "specified_effect_prior_confidence": 1.0 if specified_prior else 0.0,
    })
    neutral = agent.s.add_node("EmbodiedEffectorModel", {
        **common, "token": "neutral", "activation_magnitude": 0.0,
        "context_delta_experience_count": 2.0,
        "mean_forward": neutral_forward,
    })
    _edge(agent, source, "includes_embodied_effector_model", member)
    _edge(agent, episode, "has_embodied_effector_model", member)
    _edge(agent, episode, "has_embodied_effector_model", neutral)
    return agent, episode, policy, source


def _value(agent, episode, policy, source, field, *, addition=None):
    try:
        bindings = {
            "ep": episode, "po": policy, "src": source,
        }
        if addition is not None:
            bindings["addition"] = addition
        return agent.inner.evaluate(_term(field, addition=addition is not None), bindings)
    except ValueError as exc:
        if "FutureManifoldProjection" in str(exc):
            pytest.skip("native extension predates FutureManifoldProjection")
        raise


def _learning_safety(agent, episode, **overrides):
    attrs = {
        "verified": 1.0,
        "reset_reachable": 0.0,
        "reset_cost_units": 1000.0,
        "protective_support_available": 0.0,
        "protective_support_effectiveness": 0.0,
        "recovery_path_count": 0.0,
        "required_horizon_units": 4.0,
        "exploration_width_budget": 1.0,
        "exploration_information_budget": 1.0,
    }
    attrs.update(overrides)
    safety = agent.s.add_node("LearningSafetyContext", attrs)
    _edge(agent, episode, "has_learning_safety_context", safety)
    return safety


def _humanoid_path_bench(effects, *, bound=1.0):
    """Build a graph-only learned program chain; no world is stepped."""
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(str(exc))
    root = agent.agent
    policy = agent.inner.neighbours(root, "has_humanoid_policy")[0]
    for key, value in {
        "future_manifold_enabled": 1.0,
        "future_manifold_temporal_anchors_enabled": 1.0,
        "future_manifold_projection_budget": 16.0,
        "gravity_acceleration": 9.81,
    }.items():
        agent.inner.set_attr(policy, key, value)
    episode = agent.s.add_node("HumanoidEpisode", {
        "request_seq": 1.0, "state_seq": 1.0,
        "current_support_phase": 0.0, "response_frames": 1.0,
        "manifold_bounds_ready": 1.0,
        **{f"manifold_bound_{key}": bound for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
    })
    _edge(agent, root, "has_humanoid_episode", episode)
    programs = [agent.s.add_node("HumanoidMotorProgram", {
        "status": "grounded", "memory_eligible": 1.0,
    })]
    common = {
        "support_phase": 0.0, "context_id": 0.0, "initialized": 1.0,
        "mean_input_energy_joules": 1.0,
        **{f"mean_{key}": 0.0 for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
        **{f"anchor_{key}": 0.0 for key in (
            "z_x", "z_y", "wx", "wy", "vx", "vy", "vz",
        )},
        "anchor_lateral_offset": 0.0,
    }
    for ordinal, effect in enumerate(effects, start=1):
        model = agent.s.add_node("HumanoidPhaseActionModel", {
            **common, "token": f"path-{ordinal}",
            "ordinal": float(ordinal), "actuator_group": float(ordinal),
            "mean_dvx": float(effect),
        })
        _edge(agent, episode, "has_humanoid_phase_action_model", model)
        program = agent.s.add_node("HumanoidMotorProgram", {
            "status": "grounded", "memory_eligible": 1.0,
        })
        _edge(agent, program, "includes_humanoid_phase_action_model", model)
        programs.append(program)
    transitions = []
    for ordinal in range(len(effects)):
        transition = agent.s.add_node("EmbodiedProgramTransition", {
            "verified": 1.0, "response_frames": 1.0,
        })
        _edge(
            agent, transition, "starts_from_embodied_program",
            programs[ordinal],
        )
        _edge(
            agent, transition, "continues_with_embodied_program",
            programs[ordinal + 1],
        )
        transitions.append(transition)
    path = agent.s.add_node("ParetoCandidate", {
        "kind": "embodied_program_path", "depth": float(len(transitions)),
    })
    _edge(agent, path, "starts_from_embodied_program", programs[0])
    _edge(agent, path, "continues_with_embodied_program", programs[-1])
    for transition in transitions:
        _edge(agent, path, "contains_embodied_program_transition", transition)
    return agent, episode, policy, path, transitions


def test_generic_projection_exposes_dimension_local_narrativium():
    agent, ep, policy, source = _bench()
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 2.0)
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 2.0)
    agent.inner.set_attr(ep, "future_manifold_target", [[0.0], [0.0]])
    agent.inner.set_attr(ep, "future_manifold_bounds", [[1.0], [1.0]])
    agent.inner.set_attr(source, "future_manifold_values", [[0.0], [0.5]])

    assert _value(agent, ep, policy, source, "narrativium_reachable_0") == 1.0
    assert _value(agent, ep, policy, source, "narrativium_retained_0") == 1.0
    agent.inner.set_attr(source, "future_manifold_values", [[0.0], [2.0]])
    assert _value(agent, ep, policy, source, "narrativium_reachable_0") == 1.0
    assert _value(agent, ep, policy, source, "narrativium_retained_0") == 0.0


def test_humanoid_projection_exposes_narrativium_by_humanoid_axis():
    agent, ep, policy, path, _ = _humanoid_path_bench([0.1], bound=1.0)
    assert _value(agent, ep, policy, path, "narrativium_reachable_dvx") == 1.0
    assert _value(agent, ep, policy, path, "narrativium_retained_dvx") == 1.0


def test_ideal_effort_allows_excess_only_for_manifold_compression():
    agent, ep, policy, source = _bench()
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 2.0)
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 2.0)
    for key, value in {
        "future_manifold_target": [[0.0], [0.0]],
        "future_manifold_bounds": [[1.0], [1.0]],
        "future_manifold_ideal_effort": 10.0,
        "future_manifold_ideal_completion_time": 2.0,
        "future_manifold_ideal_width": 0.0,
        "future_manifold_ideal_information_loss": 0.0,
    }.items():
        agent.inner.set_attr(ep, key, value)
    for key, value in {
        "future_manifold_values": [[0.0], [0.0]],
        "future_manifold_widths": [[0.0], [0.0]],
        "future_manifold_effort": 12.0,
        "future_manifold_completion_time": 2.0,
    }.items():
        agent.inner.set_attr(source, key, value)

    assert _value(agent, ep, policy, source, "effort_supported") == 1.0
    assert _value(agent, ep, policy, source, "effort_residual") == 2.0
    assert _value(agent, ep, policy, source, "manifold_compression") == 0.0
    assert _value(agent, ep, policy, source, "compression_dimension_count") == 0.0
    assert _value(agent, ep, policy, source, "effort_authorized") == 0.0

    # A receipt-grounded compound can explicitly carry the exact number of
    # unresolved interaction dimensions its whole response collapsed. This is
    # a compression ratio/count, not an effort-tolerance percentage.
    agent.inner.set_attr(
        source, "future_manifold_information_compression", 2.0
    )
    assert _value(agent, ep, policy, source, "information_compression") == 2.0
    assert _value(agent, ep, policy, source, "effort_authorized") == 1.0
    agent.inner.set_attr(
        source, "future_manifold_information_compression", 0.0
    )

    # More-than-normal effort becomes admissible when it shortens the
    # represented completion time; this is compression, not a reward for burn.
    agent.inner.set_attr(source, "future_manifold_completion_time", 1.0)
    assert _value(agent, ep, policy, source, "time_compression") == 1.0
    assert _value(agent, ep, policy, source, "manifold_compression") == 1.0
    assert _value(agent, ep, policy, source, "compression_dimension_count") == 1.0
    assert _value(agent, ep, policy, source, "effort_authorized") == 1.0

    # Width and information remain independent authorization dimensions; no
    # cross-unit scalar trade is required or exposed.
    agent.inner.set_attr(source, "future_manifold_completion_time", 2.0)
    agent.inner.set_attr(ep, "future_manifold_ideal_width", 1.0)
    assert _value(agent, ep, policy, source, "width_compression") == 1.0
    assert _value(agent, ep, policy, source, "compression_dimension_count") == 1.0
    assert _value(agent, ep, policy, source, "effort_authorized") == 1.0

    agent.inner.set_attr(ep, "future_manifold_ideal_width", 0.0)
    agent.inner.set_attr(ep, "future_manifold_ideal_information_loss", 1.0)
    assert _value(agent, ep, policy, source, "information_compression") == 1.0
    assert _value(agent, ep, policy, source, "compression_dimension_count") == 1.0
    assert _value(agent, ep, policy, source, "effort_authorized") == 1.0

    # Normal-or-lower effort remains admissible without inventing compression.
    agent.inner.set_attr(source, "future_manifold_completion_time", 2.0)
    agent.inner.set_attr(ep, "future_manifold_ideal_information_loss", 0.0)
    agent.inner.set_attr(source, "future_manifold_effort", 8.0)
    assert _value(agent, ep, policy, source, "effort_residual") == 0.0
    assert _value(agent, ep, policy, source, "effort_authorized") == 1.0

    # Before a domain has adapted an episode-local value, a policy can supply
    # a weak general prior without making zero action the reference.
    agent.inner.set_attr(ep, "future_manifold_ideal_effort", 0.0)
    agent.inner.set_attr(policy, "future_manifold_ideal_effort_prior", 9.0)
    assert _value(agent, ep, policy, source, "ideal_effort") == 9.0
    assert _value(agent, ep, policy, source, "effort_supported") == 1.0


def test_learning_exploration_is_situated_by_support_and_projected_time():
    """A declaration supplies a budget; the current recovery field spends it."""
    agent, ep, policy, source = _bench(member_forward=1.2, bound=1.0)
    safety = _learning_safety(agent, ep)
    for key, value in {
        "body_mass": 10.0,
        "state_qx": 0.0,
        "state_qy": 0.0,
        "support_sensor_count": 1.0,
        "active_support_count": 1.0,
        "state_support_0_force": 100.0,
        "state_contact_force_newtons": 100.0,
    }.items():
        agent.inner.set_attr(ep, key, value)
    agent.inner.set_attr(policy, "gravity_acceleration", 10.0)
    agent.inner.set_attr(policy, "future_manifold_path_fixed_point_run", 15.0)

    near_authority = float(_value(
        agent, ep, policy, source, "exploration_authority"
    ))
    near_bound = float(_value(agent, ep, policy, source, "applied_bound_0"))
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0
    assert near_authority > 0.2
    assert near_bound > 1.2

    # The same contact observation cannot license an arbitrarily distant
    # future: outside the declared near horizon its contribution decays.
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 64.0)
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 64.0)
    agent.inner.set_attr(policy, "future_manifold_path_fixed_point_run", 63.0)
    assert float(_value(agent, ep, policy, source, "loss")) == 1.0

    # Removing actual support tightens immediately even though the declared
    # safe-learning context and its budgets are unchanged.
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 16.0)
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 16.0)
    agent.inner.set_attr(policy, "future_manifold_path_fixed_point_run", 15.0)
    agent.inner.set_attr(ep, "active_support_count", 0.0)
    agent.inner.set_attr(ep, "state_support_0_force", 0.0)
    agent.inner.set_attr(ep, "state_contact_force_newtons", 0.0)
    unsupported_bound = float(_value(
        agent, ep, policy, source, "applied_bound_0"
    ))
    assert unsupported_bound < near_bound
    assert float(_value(agent, ep, policy, source, "loss")) == 1.0
    assert unsupported_bound == float(_value(
        agent, ep, policy, source, "applied_bound_0"
    ))

    # Availability is not engagement. A declared caregiver contributes only
    # when the graph requests that support for this situated attempt.
    agent.inner.set_attr(safety, "protective_support_available", 1.0)
    agent.inner.set_attr(safety, "protective_support_effectiveness", 1.0)
    assert float(_value(
        agent, ep, policy, source, "applied_bound_0"
    )) == unsupported_bound
    agent.inner.set_attr(ep, "caregiver_protective_support_requested", 1.0)
    assert float(_value(agent, ep, policy, source, "applied_bound_0")) == 2.0
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0


def _motor_members(agent, episode, policy):
    chosen = set()
    for candidate in agent.inner.neighbours(episode, "has_embodied_effector_model"):
        verdict = agent.inner.evaluate({
            "type": "MotorCompose",
            "episode": {"type": "Var", "name": "ep"},
            "policy": {"type": "Var", "name": "po"},
            "candidate": {"type": "Var", "name": "candidate"},
        }, {"ep": episode, "po": policy, "candidate": candidate})
        if verdict:
            chosen.add(str(agent.s.node(candidate)["attrs"].get("token")))
    return chosen


def _humanoid_motor_members(agent, episode, policy):
    chosen = set()
    for candidate in agent.inner.neighbours(
        episode, "has_humanoid_phase_action_model"
    ):
        verdict = agent.inner.evaluate({
            "type": "MotorCompose",
            "episode": {"type": "Var", "name": "ep"},
            "policy": {"type": "Var", "name": "po"},
            "candidate": {"type": "Var", "name": "candidate"},
        }, {"ep": episode, "po": policy, "candidate": candidate})
        if verdict:
            chosen.add(str(agent.s.node(candidate)["attrs"].get("token")))
    return chosen


def test_projection_reports_horizon_loss_and_retention():
    agent, ep, policy, source = _bench(member_forward=2.0, bound=1.0)
    assert float(_value(agent, ep, policy, source, "loss")) > 0.0
    assert float(_value(agent, ep, policy, source, "horizon")) == 1.0
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0)
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0
    assert float(_value(agent, ep, policy, source, "horizon")) == 1.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 2.0


def test_projection_snapshot_is_the_same_atomic_six_field_report():
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0)
    snapshot = tuple(_value(agent, ep, policy, source, "snapshot"))
    fields = (
        "support", "resolved", "loss", "information_loss",
        "effort_supported", "effort_authorized",
    )
    assert snapshot == tuple(
        _value(agent, ep, policy, source, field) for field in fields
    )


def test_projection_shape_snapshot_is_the_same_atomic_manifold_report():
    agent, ep, policy, source = _bench(member_forward=2.0, bound=1.0)
    snapshot = tuple(_value(agent, ep, policy, source, "shape_snapshot"))
    fields = (
        "support", "resolved", "loss", "information_loss", "horizon",
        "earliest_decisive_tick", "minimum_exafferent_scale",
        *(f"residual_{index}" for index in range(7)),
        *(f"applied_bound_{index}" for index in range(7)),
    )
    assert len(snapshot) == 21
    assert snapshot == tuple(
        _value(agent, ep, policy, source, field) for field in fields
    )


def test_projection_audit_snapshot_matches_every_selected_path_field():
    agent, ep, policy, source = _bench(member_forward=2.0, bound=1.0)
    snapshot = tuple(_value(agent, ep, policy, source, "audit_snapshot"))
    fields = (
        "support", "resolved", "loss", "information_loss", "horizon",
        "anchor_count", "refinement_count", "termination_code",
        "exploration_authority", "effort_supported", "projected_effort",
        "ideal_effort", "effort_scale", "effort_residual",
        "time_compression", "width_compression", "information_compression",
        "compression_dimension_count", "manifold_compression",
        "effort_authorized",
        *(f"situated_support_{index}" for index in range(7)),
        *(f"applied_bound_{index}" for index in range(7)),
    )
    assert len(snapshot) == 34
    assert snapshot == tuple(
        _value(agent, ep, policy, source, field) for field in fields
    )


@pytest.mark.parametrize(
    ("member_forward", "expected_residual"),
    ((2.0, 1.0), (-2.0, -1.0)),
)
def test_projection_reports_signed_time_addressed_shape_residual(
    member_forward, expected_residual
):
    """Escapes retain direction and excess, not merely a scalar loss count."""
    agent, ep, policy, source = _bench(
        member_forward=member_forward, bound=1.0
    )
    assert float(_value(agent, ep, policy, source, "loss")) == 1.0
    assert float(_value(
        agent, ep, policy, source, "residual_0"
    )) == expected_residual
    assert float(_value(
        agent, ep, policy, source, "shape_residual_1_0"
    )) == expected_residual
    assert float(_value(
        agent, ep, policy, source, "shape_residual_1_1"
    )) == 0.0


def test_projection_accepts_grounded_humanoid_phase_program_membership():
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0)
    member = agent.inner.neighbours(
        source, "includes_embodied_effector_model"
    )[0]
    agent.inner.remove_edge(
        source, "includes_embodied_effector_model", member
    )
    _edge(
        agent, source, "includes_humanoid_phase_action_model", member
    )
    assert float(_value(agent, ep, policy, source, "support")) == 1.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0

    assert float(_value(agent, ep, policy, source, "loss")) == 0.0


def test_humanoid_path_projection_carries_shape_across_program_boundaries():
    agent, ep, policy, path, transitions = _humanoid_path_bench((0.5, 1.0))
    assert float(_value(agent, ep, policy, path, "support")) == 1.0
    assert float(_value(agent, ep, policy, path, "resolved")) == 1.0
    assert float(_value(agent, ep, policy, path, "loss")) == 1.0
    assert float(_value(agent, ep, policy, path, "horizon")) == 2.0
    assert float(_value(agent, ep, policy, path, "residual_4")) == 0.5
    assert float(
        _value(agent, ep, policy, path, "narrativium_retained_dvx")
    ) == 0.0
    assert float(
        _value(agent, ep, policy, path, "narrativium_retained_dvz")
    ) == 1.0
    assert float(_value(agent, ep, policy, path, "retained_width")) == 6.0

    # Once the first action has a real receipt, prediction is re-anchored to
    # that state and only the still-unexecuted suffix is synthesized.
    assert float(_value(
        agent, ep, policy, path, "loss", addition=transitions[1]
    )) == 0.0
    assert float(_value(
        agent, ep, policy, path, "horizon", addition=transitions[1]
    )) == 1.0


def test_humanoid_path_projection_respects_transition_order():
    unsafe = _humanoid_path_bench((1.5, -1.0))
    safe = _humanoid_path_bench((-1.0, 1.5))
    assert float(_value(*unsafe[:4], "loss")) == 1.0
    assert float(_value(*safe[:4], "loss")) == 0.0
    assert float(_value(*safe[:4], "horizon")) == 2.0


def test_humanoid_path_projection_fails_closed_on_disconnected_chain():
    agent, ep, policy, path, transitions = _humanoid_path_bench((0.25, 0.25))
    origin = agent.inner.neighbours(
        transitions[1], "starts_from_embodied_program"
    )[0]
    agent.inner.remove_edge(
        transitions[1], "starts_from_embodied_program", origin
    )
    disconnected = agent.s.add_node("HumanoidMotorProgram", {})
    _edge(
        agent, transitions[1], "starts_from_embodied_program", disconnected
    )
    assert float(_value(agent, ep, policy, path, "support")) == 0.0
    assert float(_value(agent, ep, policy, path, "resolved")) == 0.0


def test_humanoid_path_escape_cannot_pose_as_effort_time_compression():
    agent, ep, policy, path, _ = _humanoid_path_bench((1.5, -1.0))
    agent.inner.set_attr(ep, "future_manifold_ideal_effort", 1.0)
    agent.inner.set_attr(ep, "future_manifold_ideal_completion_time", 4.0)
    agent.inner.set_attr(path, "future_manifold_effort", 2.0)
    assert float(_value(agent, ep, policy, path, "loss")) == 1.0
    assert float(_value(agent, ep, policy, path, "time_compression")) == 0.0
    assert float(_value(agent, ep, policy, path, "effort_authorized")) == 0.0


def test_humanoid_path_effort_ratio_uses_matching_temporal_exposure():
    agent, ep, policy, path, _ = _humanoid_path_bench((0.25, -0.25))
    agent.inner.set_attr(ep, "future_manifold_ideal_effort", 0.5)
    agent.inner.set_attr(ep, "future_manifold_effort_scale_joules", 2.0)
    # Two one-joule programs consume two ordinary action exposures. Their
    # mean situated ratio is therefore 2 J / (2 J/action * 2 actions) = 0.5.
    assert float(_value(agent, ep, policy, path, "projected_effort")) == 0.5
    assert float(_value(agent, ep, policy, path, "effort_scale")) == 4.0
    assert float(_value(agent, ep, policy, path, "effort_residual")) == 0.0
    assert float(_value(agent, ep, policy, path, "effort_authorized")) == 1.0

def test_projection_uses_humanoid_phase_models_as_reference_population():
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0)
    models = list(agent.inner.neighbours(ep, "has_embodied_effector_model"))
    for ordinal, model in enumerate(models):
        agent.inner.remove_edge(ep, "has_embodied_effector_model", model)
        _edge(agent, ep, "has_humanoid_phase_action_model", model)
        for key, value in {
            "token": f"phase-{ordinal}",
            "ordinal": float(ordinal),
            "actuator_group": float(ordinal),
            "support_phase": 0.0,
            "context_id": 0.0,
            "initialized": 1.0,
            "mean_input_energy_joules": 0.0,
            "context_grounded": 1.0,
            **{f"mean_{key}": 0.0 for key in (
                "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
            )},
            **{f"anchor_{key}": 0.0 for key in (
                "z_x", "z_y", "wx", "wy", "vx", "vy", "vz",
            )},
            "anchor_lateral_offset": 0.0,
        }.items():
            agent.inner.set_attr(model, key, value)
    member = agent.inner.neighbours(
        source, "includes_embodied_effector_model"
    )[0]
    agent.inner.remove_edge(
        source, "includes_embodied_effector_model", member
    )
    _edge(agent, source, "includes_humanoid_phase_action_model", member)
    agent.inner.set_attr(ep, "current_support_phase", 0.0)
    agent.inner.set_attr(ep, "response_frames", 2.0)
    agent.inner.set_attr(ep, "manifold_bounds_ready", 1.0)
    agent.inner.set_attr(ep, "caregiver_support_counterfactual_authority", 1.0)
    agent.inner.set_attr(ep, "caregiver_support_counterfactual_loss_floor", 1.0)
    for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"):
        agent.inner.set_attr(ep, f"manifold_bound_{key}", 1.0)

    assert float(_value(agent, ep, policy, source, "support")) == 1.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0

    # The endogenous program escapes by one unit. Learned exafference of -2
    # restores the path, with one-half being the least tested intervention
    # that reaches the bound. This is a risk-gate decision; when endogenous
    # motion is already safe, the correct minimum is zero.
    agent.inner.set_attr(member, "mean_dvx", 2.0)
    fractional_support = agent.s.add_node(
        "CaregiverSupportScaleCandidate",
        {
            **dict(agent.s.node(member)["attrs"]),
            "token": "fractional_support",
            "exafferent": 1.0,
            "counterfactual_scale_numerator": 1.0,
            "counterfactual_scale_denominator": 4.0,
            "mean_dvx": -2.0,
        },
    )
    assert float(_value(
        agent, ep, policy, source, "loss", addition=fractional_support
    )) == 1.0
    agent.inner.set_attr(
        fractional_support, "counterfactual_scale_numerator", 4.0
    )
    assert float(_value(
        agent, ep, policy, source, "loss", addition=fractional_support
    )) == 0.0
    assert float(_value(
        agent, ep, policy, source, "minimum_exafferent_scale",
        addition=fractional_support,
    )) == 0.5
    assert float(_value(agent, ep, policy, source, "loss")) == 1.0

    historical_attrs = dict(agent.s.node(member)["attrs"])
    historical_attrs["context_id"] = 99.0
    historical = agent.s.add_node(
        "HumanoidPhaseActionModel", historical_attrs
    )
    agent.inner.remove_edge(
        source, "includes_humanoid_phase_action_model", member
    )
    _edge(
        agent, source, "includes_humanoid_phase_action_model", historical
    )
    assert float(_value(agent, ep, policy, source, "support")) == 1.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0


def test_projection_changes_with_learned_member_delta_and_neutral_reference():
    agent, ep, policy, source = _bench(member_forward=2.0, bound=1.0, neutral_forward=0.0)
    assert float(_value(agent, ep, policy, source, "loss")) > 0.0
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0, neutral_forward=2.0)
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0


def test_projection_extends_until_learned_shape_becomes_decisive():
    agent, ep, policy, source = _bench(
        bound=1.0, context_delta_forward=0.75, context_gain_forward=1.0,
    )
    assert float(_value(agent, ep, policy, source, "loss")) == 1.0
    assert float(_value(agent, ep, policy, source, "horizon")) == 2.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 1.0


def test_projection_budget_exhaustion_is_unresolved_not_retained():
    agent, ep, policy, source = _bench(
        bound=10.0, context_delta_forward=0.1, context_gain_forward=1.0,
    )
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 3.0)
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 0.0
    assert float(_value(agent, ep, policy, source, "horizon")) == 3.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 3.0


def test_sparse_anchor_report_is_bounded_and_first_order_certified():
    """Enabled projection reports sparse-anchor work under one budget."""
    agent, ep, policy, source = _bench(
        bound=1.0, context_delta_forward=0.75, context_gain_forward=1.0,
    )
    for key, value in {
        "future_manifold_temporal_anchors_enabled": 1.0,
        "future_manifold_max_shape_order": 1.0,
        "future_manifold_max_refinements": 16.0,
    }.items():
        agent.inner.set_attr(policy, key, value)
    values = {
        field: float(_value(agent, ep, policy, source, field))
        for field in (
            "anchor_count", "refinement_count", "certified_interval_count",
            "ambiguous_interval_count", "max_enclosure_width",
            "max_shape_order", "earliest_decisive_tick", "budget",
        )
    }
    assert values["anchor_count"] >= 1.0
    assert values["anchor_count"] <= values["budget"]
    assert values["max_shape_order"] == 0.0
    # The first dense interval is certified, while the learned context
    # delta crosses the bound at the next anchor; a dense-only implementation
    # would miss this explicit intermediate decision boundary.
    assert values["earliest_decisive_tick"] == 2.0
    assert values["certified_interval_count"] + values["ambiguous_interval_count"] >= 1.0
    assert values["refinement_count"] >= 0.0


def test_sparse_certified_span_reports_runtime_shape_order_one():
    agent, ep, policy, source = _bench(
        bound=100.0, context_delta_forward=0.01, context_gain_forward=1.0,
    )
    agent.inner.set_attr(policy, "future_manifold_temporal_anchors_enabled", 1.0)
    agent.inner.set_attr(policy, "future_manifold_max_shape_order", 1.0)
    assert float(_value(agent, ep, policy, source, "max_shape_order")) == 1.0


def test_explicit_physical_horizon_certifies_without_fixed_point():
    agent, ep, policy, source = _bench(
        bound=100.0, context_delta_forward=0.01, context_gain_forward=1.0,
    )
    agent.inner.set_attr(policy, "future_manifold_temporal_anchors_enabled", 1.0)
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 64.0)
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 64.0)
    agent.inner.set_attr(policy, "future_manifold_max_refinements", 16.0)
    agent.inner.set_attr(policy, "future_manifold_path_fixed_point_run", 63.0)
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 6.0
    assert float(_value(agent, ep, policy, source, "horizon")) == 64.0
    anchors = float(_value(agent, ep, policy, source, "anchor_count"))
    assert anchors < 32.0


def test_oscillatory_affine_box_refines_then_certifies():
    """A rotational context stays safe exactly while its box needs splitting."""
    agent, ep, policy, source = _bench(bound=1.5)
    agent.inner.set_attr(ep, "state_flow_forward", 1.0)
    agent.inner.set_attr(ep, "state_flow_lateral", 0.0)
    member = next(
        model for model in agent.inner.neighbours(source, "includes_embodied_effector_model")
        if agent.s.node(model)["attrs"].get("token") == "member"
    )
    for key, value in {
        "context_delta_gain_flow_forward_flow_forward": -1.0,
        "context_delta_gain_flow_forward_flow_lateral": -1.0,
        "context_delta_gain_flow_lateral_flow_forward": 1.0,
        "context_delta_gain_flow_lateral_flow_lateral": -1.0,
        "flow_forward_gain_forward": 1.0,
        "flow_lateral_gain_forward": 1.0,
    }.items():
        agent.inner.set_attr(member, key, value)
    agent.inner.set_attr(policy, "future_manifold_temporal_anchors_enabled", 1.0)
    agent.inner.set_attr(policy, "future_manifold_physical_horizon", 8.0)
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 64.0)
    agent.inner.set_attr(policy, "future_manifold_max_refinements", 32.0)
    agent.inner.set_attr(policy, "future_manifold_path_fixed_point_run", 63.0)
    assert float(_value(agent, ep, policy, source, "refinement_count")) > 0.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0


def test_sparse_anchor_budget_exhaustion_remains_fail_closed():
    agent, ep, policy, source = _bench(
        bound=10.0, context_delta_forward=0.1, context_gain_forward=1.0,
    )
    agent.inner.set_attr(policy, "future_manifold_temporal_anchors_enabled", 1.0)
    agent.inner.set_attr(policy, "future_manifold_max_refinements", 1.0)
    agent.inner.set_attr(policy, "future_manifold_projection_budget", 3.0)
    assert float(_value(agent, ep, policy, source, "resolved")) == 0.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 3.0
    assert float(_value(agent, ep, policy, source, "anchor_count")) <= 3.0


def test_latent_context_motion_does_not_block_a_shape_fixed_point():
    agent, ep, policy, source = _bench(
        bound=10.0, context_delta_forward=0.1, context_gain_forward=1.0,
        contextual_prediction=False,
    )
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 2.0


def test_epistemic_probe_certificate_ends_at_its_receipt_boundary():
    agent, ep, policy, source = _bench(
        bound=10.0, context_delta_forward=0.1, context_gain_forward=1.0,
        contextual_prediction=True,
    )
    agent.inner.set_attr(source, "source", "factorized_calibration")
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0
    assert float(_value(agent, ep, policy, source, "horizon")) == 1.0
    assert float(_value(agent, ep, policy, source, "termination_code")) == 5.0


def test_optional_candidate_is_projected_exactly_once():
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0)
    common = {
        "experience_count": 2.0, "context_delta_experience_count": 2.0,
        "activation_magnitude": 1.0, "state_effector_position": 0.0,
        "specified_command_level": 0.0,
        "specified_maximum_position_change_per_action": 1.0,
        "mean_forward": 0.75,
    }
    addition = agent.s.add_node("EmbodiedEffectorModel", common)
    assert float(_value(agent, ep, policy, source, "loss", addition=addition)) == 0.0
    agent.inner.set_attr(addition, "mean_forward", 1.25)
    assert float(_value(agent, ep, policy, source, "loss", addition=addition)) == 1.0


def test_optional_program_expands_its_grounded_models_before_projection():
    agent, ep, policy, source = _bench(member_forward=0.0, bound=1.0)
    addition = agent.s.add_node("EmbodiedMotorProgram", {"member_count": 1.0})
    addition_model = agent.s.add_node("EmbodiedEffectorModel", {
        "experience_count": 2.0,
        "context_delta_experience_count": 2.0,
        "activation_magnitude": 1.0,
        "state_effector_position": 0.0,
        "specified_command_level": 0.0,
        "specified_maximum_position_change_per_action": 1.0,
        "mean_forward": 0.75,
    })
    _edge(
        agent, addition, "includes_embodied_effector_model", addition_model
    )
    assert float(
        _value(agent, ep, policy, source, "support", addition=addition)
    ) == 1.0
    assert float(
        _value(agent, ep, policy, source, "loss", addition=addition)
    ) == 0.0
    agent.inner.set_attr(addition_model, "mean_forward", 1.25)
    assert float(
        _value(agent, ep, policy, source, "loss", addition=addition)
    ) == 1.0


def test_specified_effect_can_inherit_learned_neutral_context_transition():
    agent, ep, policy, source = _bench(
        member_context_count=0.0, specified_prior=True,
    )
    assert float(_value(agent, ep, policy, source, "support")) == 1.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0


def test_native_composer_projects_complete_candidates_only_when_gate_is_active():
    """A currently optimal action drifts outside the tube on its second tick.

    Gate-off must retain the legacy choice.  Gate-on must prefer the slightly
    worse immediate action whose complete held path reaches a fixed point
    inside the bound.  No simulator or world step participates.
    """
    try:
        agent = WorldAdapter(seeds=("embodied_motor_program",))
    except RuntimeError as exc:
        pytest.skip(str(exc))
    root = agent.agent
    policy = agent.inner.neighbours(root, "has_embodied_motor_program_policy")[0]
    for key in ("lateral", "vertical", "roll", "pitch", "turn", "normal_load"):
        agent.inner.set_attr(policy, f"{key}_weight", 0.0)
    for key, value in {
        "forward_weight": 1.0,
        "future_manifold_projection_budget": 16.0,
        "future_manifold_path_fixed_point_run": 1.0,
        "native_composition_enabled": 1.0,
    }.items():
        agent.inner.set_attr(policy, key, value)
    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "target_forward": 0.0, "target_lateral": 0.0,
        "target_vertical": 0.0, "target_roll": 0.0, "target_pitch": 0.0,
        "target_turn": 0.0, "target_normal_load": 0.0,
        "state_flow_forward": 0.0, "state_flow_lateral": 0.0,
        "state_flow_vertical": 0.0, "state_power_state": 0.0,
        "manifold_bound_forward": 1.0, "manifold_bounds_ready": 1.0,
        "program_request_seq": 101.0,
    })
    _edge(agent, root, "has_embodied_motor_program_episode", episode)
    common = {
        "experience_count": 2.0, "available": 1.0,
        "context_delta_experience_count": 2.0,
        "state_effector_position": 0.0, "specified_command_level": 0.0,
        "specified_maximum_position_change_per_action": 1.0,
        "activation_magnitude": 1.0, "log_authority": 0.0,
    }
    drifting = agent.s.add_node("EmbodiedEffectorModel", {
        **common, "token": "drifting", "ordinal": 1.0, "actuator_group": 0.0,
        "mean_forward": 0.0, "mean_context_delta_flow_forward": 0.75,
        "flow_forward_gain_forward": 1.0,
    })
    retained = agent.s.add_node("EmbodiedEffectorModel", {
        **common, "token": "retained", "ordinal": 2.0, "actuator_group": 1.0,
        "mean_forward": 0.25, "mean_context_delta_flow_forward": 0.0,
    })
    reference = agent.s.add_node("EmbodiedEffectorModel", {
        **common, "token": "reference", "ordinal": 3.0, "actuator_group": 2.0,
        "available": 0.0, "activation_magnitude": 0.0,
        "mean_forward": 0.0, "mean_context_delta_flow_forward": 0.0,
    })
    for model in (drifting, retained, reference):
        _edge(agent, episode, "has_embodied_effector_model", model)

    agent.inner.set_attr(policy, "future_manifold_enabled", 0.0)
    assert _motor_members(agent, episode, policy) == {"drifting"}
    agent.inner.set_attr(policy, "future_manifold_enabled", 1.0)
    assert _motor_members(agent, episode, policy) == {"retained"}


def test_humanoid_risk_gate_keeps_normal_task_momentum_inside_manifold():
    """Preserving the future path does not collapse normal effort to zero."""
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(str(exc))
    root = agent.agent
    policy = agent.inner.neighbours(root, "has_humanoid_policy")[0]
    for key, value in {
        "native_humanoid_composition_enabled": 1.0,
        "future_manifold_temporal_anchors_enabled": 1.0,
        "target_froude_speed": 0.0,
        "persistent_task_residual_authority": 0.0,
        "support_geometry_preview_authority": 0.0,
        "takeoff_motor_compression_authority": 0.0,
        "gravity_acceleration": 9.81,
        "support_phase_prior_strength": 1.0,
    }.items():
        agent.inner.set_attr(policy, key, value)
    episode_attrs = {
        "request_seq": 1.0, "state_seq": 1.0,
        "selected_primary_token": "primary",
        "selected_primary_context_id": 0.0,
        "current_support_phase": 0.0,
        "response_frames": 2.0,
        "manifold_bounds_ready": 1.0,
        "standing_reference_z": 1.0,
        "state_qx": 0.0, "state_qy": 0.0,
        "state_qz": 0.0, "state_qw": 1.0,
        "locomotion_drive_active": 1.0,
        "heading_x": 1.0,
        **{f"manifold_bound_{key}": 2.0 for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
    }
    episode = agent.s.add_node("HumanoidEpisode", episode_attrs)
    _edge(agent, root, "has_humanoid_episode", episode)
    common = {
        "support_phase": 0.0, "context_id": 0.0,
        "initialized": 1.0, "mean_input_energy_joules": 0.0,
        **{f"mean_{key}": 0.0 for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
        **{f"anchor_{key}": 0.0 for key in (
            "z_x", "z_y", "wx", "wy", "vx", "vy", "vz",
        )},
        "anchor_lateral_offset": 0.0,
    }
    primary = agent.s.add_node("HumanoidPhaseActionModel", {
        **common, "token": "primary", "ordinal": 1.0,
        "actuator_group": 1.0, "mean_dvx": 1.0,
    })
    cancellation = agent.s.add_node("HumanoidPhaseActionModel", {
        **common, "token": "cancellation", "ordinal": 2.0,
        "actuator_group": 2.0, "mean_dvx": -1.0,
    })
    for model in (primary, cancellation):
        _edge(agent, episode, "has_humanoid_phase_action_model", model)
    synergy = agent.s.add_node("HumanoidSynergyModel", {
        "token_a": "primary", "token_b": "cancellation",
        "ordinal": 1.0, "approved": 1.0,
        **{f"residual_{key}": 0.0 for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
    })
    _edge(agent, episode, "has_humanoid_synergy_model", synergy)
    plan = agent.s.add_node("HumanoidMotorProgram", {
        "request_seq": 1.0, "allow_expansion": 1.0,
    })
    _edge(agent, episode, "has_active_humanoid_motor_program", plan)

    agent.inner.set_attr(policy, "future_manifold_enabled", 0.0)
    assert _humanoid_motor_members(agent, episode, policy) == {
        "primary", "cancellation",
    }
    agent.inner.set_attr(policy, "future_manifold_enabled", 1.0)
    assert _humanoid_motor_members(agent, episode, policy) == {
        "primary", "cancellation",
    }


def test_humanoid_takeoff_projects_flat_intermediate_actions_to_improving_order_n_shape():
    """A higher-order receipt model may justify crossing a flat local step."""
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(str(exc))
    root = agent.agent
    policy = agent.inner.neighbours(root, "has_humanoid_policy")[0]
    for key, value in {
        "native_humanoid_composition_enabled": 1.0,
        "future_manifold_enabled": 1.0,
        "future_manifold_temporal_anchors_enabled": 1.0,
        "persistent_task_residual_authority": 1.0,
        "support_geometry_preview_authority": 0.0,
        "takeoff_motor_compression_authority": 0.0,
        "gravity_acceleration": 9.0,
        "support_phase_prior_strength": 1.0,
        "target_froude_speed": 0.0,
    }.items():
        agent.inner.set_attr(policy, key, value)
    episode = agent.s.add_node("HumanoidEpisode", {
        "request_seq": 1.0, "state_seq": 1.0,
        "selected_primary_token": "primary",
        "selected_primary_context_id": 0.0,
        "current_support_phase": 0.0,
        "response_frames": 2.0,
        "physics_time_step": 0.01,
        "manifold_bounds_ready": 1.0,
        "standing_reference_z": 1.0,
        "state_qx": 0.0, "state_qy": 0.0,
        "state_qz": 0.0, "state_qw": 1.0,
        "state_vz": 0.0,
        "motor_task_context": "self_takeoff",
        "state_gravity_relative_orientation_class": 3.0,
        "self_takeoff_drive_active": 1.0,
        "self_takeoff_target_velocity_scale": 1.0,
        "heading_x": 1.0,
        **{f"manifold_bound_{key}": (5.0 if key == "dvz" else 10.0) for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
    })
    _edge(agent, root, "has_humanoid_episode", episode)
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4.0,
    })
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "evidence_kind": "support_reducing_elevation",
        "failure_count": 16.0,
    })
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    safety = agent.s.add_node("LearningSafetyContext", {
        "verified": 1.0,
        "reset_reachable": 1.0,
        "reset_cost_units": 1.0,
        "required_horizon_units": 1.0,
        "protective_support_available": 1.0,
    })
    _edge(agent, episode, "has_learning_safety_context", safety)
    common = {
        "support_phase": 0.0, "context_id": 0.0,
        "initialized": 1.0, "mean_input_energy_joules": 0.0,
        **{f"mean_{key}": 0.0 for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
        **{f"anchor_{key}": 0.0 for key in (
            "z_x", "z_y", "wx", "wy", "vx", "vy", "vz",
        )},
        "anchor_lateral_offset": 0.0,
    }
    models = []
    for ordinal, token in enumerate(("primary", "flat_a", "flat_b")):
        model = agent.s.add_node("HumanoidPhaseActionModel", {
            **common, "token": token, "ordinal": float(ordinal),
            "actuator_group": float(ordinal),
        })
        _edge(agent, episode, "has_humanoid_phase_action_model", model)
        models.append(model)
    ungrounded = None
    for ordinal, (left, right) in enumerate((
        ("primary", "flat_a"),
        ("primary", "flat_b"),
        ("flat_a", "flat_b"),
    )):
        synergy = agent.s.add_node("HumanoidSynergyModel", {
            "token_a": left, "token_b": right,
            "ordinal": float(ordinal), "approved": 1.0,
            "experience_count": (
                0.0 if (left, right) == ("primary", "flat_a") else 1.0
            ),
            **{f"residual_{key}": (
                3.0 if key == "dvz" and left == "flat_a" else 0.0
            ) for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")},
        })
        _edge(agent, episode, "has_humanoid_synergy_model", synergy)
        if (left, right) == ("primary", "flat_a"):
            ungrounded = synergy
    plan = agent.s.add_node("HumanoidMotorProgram", {
        "request_seq": 1.0, "allow_expansion": 1.0,
    })
    _edge(agent, episode, "has_active_humanoid_motor_program", plan)
    for model in models:
        _edge(agent, plan, "includes_humanoid_phase_action_model", model)

    # The unknown pair is the only information-gaining probe. Its receipt is
    # identifiable, so the composer stops at width two even though evidence
    # permits order three.
    assert _humanoid_motor_members(agent, episode, policy) == {
        "primary", "flat_a",
    }
    assert ungrounded is not None
    agent.inner.remove_edge(
        episode, "has_humanoid_synergy_model", ungrounded
    )
    # A supported learning projection preserves the additive path and carries
    # the one unobserved pair in the information-loss dimension. It does not
    # invent a synergy or collapse the complete order-three program to
    # unsupported merely because this action is the experiment that learns it.
    assert float(_value(agent, episode, policy, plan, "support")) == 1.0
    unobserved_information_loss = float(
        _value(agent, episode, policy, plan, "information_loss")
    )
    assert 0.0 < unobserved_information_loss <= 1.0

    # A physical receipt for the complete compound supersedes its incomplete
    # pairwise decomposition.  The whole-program response is analysis by
    # synthesis evidence in its own right: replaying it must not recreate the
    # unknown interaction as information loss.
    for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"):
        agent.inner.set_attr(plan, f"mean_{key}", 3.0 if key == "dvz" else 0.0)
    agent.inner.set_attr(plan, "member_count", 3.0)
    agent.inner.set_attr(plan, "experience_count", 1.0)
    agent.inner.set_attr(plan, "receipt_learned", 1.0)
    agent.inner.set_attr(plan, "whole_program_projection_authority", 1.0)
    agent.inner.set_attr(plan, "motor_task_context", "self_takeoff")
    agent.inner.set_attr(plan, "receipt_support_phase", 0.0)
    agent.inner.set_attr(plan, "receipt_orientation_class", 3.0)
    agent.inner.set_attr(plan, "receipt_response_frames", 2.0)
    agent.inner.set_attr(plan, "response_frames", 2.0)
    assert float(_value(agent, episode, policy, plan, "support")) == 1.0
    assert float(
        _value(agent, episode, policy, plan, "information_loss")
    ) == 0.0
    agent.inner.set_attr(
        episode, "state_gravity_relative_orientation_class", 2.0
    )
    assert float(
        _value(agent, episode, policy, plan, "information_loss")
    ) == unobserved_information_loss
    agent.inner.set_attr(
        episode, "state_gravity_relative_orientation_class", 3.0
    )
    agent.inner.set_attr(plan, "response_frames", 3.0)
    assert float(
        _value(agent, episode, policy, plan, "information_loss")
    ) == unobserved_information_loss
    agent.inner.set_attr(plan, "response_frames", 2.0)

    _edge(agent, episode, "has_humanoid_synergy_model", ungrounded)
    agent.inner.set_attr(ungrounded, "experience_count", 1.0)

    # Once the lower-order basis is grounded, the terminal order-three shape
    # can justify crossing the locally flat intermediate step.
    assert _humanoid_motor_members(agent, episode, policy) == {
        "primary", "flat_a", "flat_b",
    }

    # Infer recruitment from the outstanding takeoff residual, then authorize
    # it only when the exact scaled order-N shape stays inside every bound.
    agent.inner.set_attr(episode, "self_takeoff_target_velocity_scale", 2.0)
    effort = _value(
        agent, episode, policy, plan, "takeoff_effort_snapshot",
    )
    safe_boundary = (5.0 / 3.0) ** 0.5
    assert tuple(float(value) for value in effort[:5]) == pytest.approx((
        1.0,
        2.0 ** 0.5,
        safe_boundary,
        2.0 ** 0.5 - safe_boundary,
        1.0,
    ))
    assert float(effort[11]) == pytest.approx(5.0)

    agent.inner.set_attr(episode, "manifold_bound_dvz", 10.0)
    effort = _value(
        agent, episode, policy, plan, "takeoff_effort_snapshot",
    )
    assert tuple(float(value) for value in effort[:5]) == pytest.approx(
        (1.0, 2.0 ** 0.5, 2.0 ** 0.5, 0.0, 1.0),
    )
    # Pairwise synergy scales with both uniformly recruited members.
    assert float(effort[11]) == pytest.approx(6.0)
