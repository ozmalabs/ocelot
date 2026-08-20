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
    for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"):
        agent.inner.set_attr(ep, f"manifold_bound_{key}", 1.0)

    assert float(_value(agent, ep, policy, source, "support")) == 1.0
    assert float(_value(agent, ep, policy, source, "resolved")) == 1.0
    assert float(_value(agent, ep, policy, source, "loss")) == 0.0

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


def test_humanoid_risk_gate_stops_at_least_admissible_intervention():
    """Task improvement cannot widen an already-preserved future path."""
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
    assert _humanoid_motor_members(agent, episode, policy) == {"primary"}
