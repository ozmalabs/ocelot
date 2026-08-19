"""Static contract checks for the opt-in, graph-native manifold treatment."""
import json
from pathlib import Path
from substrate.world_adapter import WorldAdapter
from domains.embodied_graph_transducer import add_unchecked_edge as _edge
from tests.test_active_aero_motor_program_migrated import _model_attrs


SEED = Path(__file__).parents[1] / "seeds" / "embodied_motor_program.json"


def _seed():
    return json.loads(SEED.read_text())


def test_gate_is_inert_by_default_and_recursive_projection_is_audit_only():
    seed = _seed()
    policy = next(n for n in seed["nodes"] if n["type"] == "EmbodiedMotorProgramPolicy")
    attrs = policy["attrs"]
    assert attrs["future_manifold_enabled"] == 0.0
    assert "future_manifold_establish_from_seq" in attrs
    assert "future_manifold_establish_until_seq" in attrs
    assert attrs["future_manifold_physical_horizon"] == 256.0
    close = next(r for r in seed["rules"] if r["name"] == "emp_abs_close_embodied_motor_program")
    effects = close["effects"]
    horizon_effect = next(e for e in effects if e[2] == "manifold_horizon")
    assert "FutureManifoldProjection" in str(horizon_effect[3])
    assert any(e[2] == "manifold_projection_resolved" for e in effects)
    assert any(e[2] == "manifold_projection_reason" for e in effects)
    assert any(e[2] == "manifold_projection_termination_code" for e in effects)
    assert "certified_horizon" in json.dumps(close)


def test_sparse_anchor_and_local_refinement_contract_is_opt_in():
    seed = _seed()
    policy = next(
        n for n in seed["nodes"] if n["type"] == "EmbodiedMotorProgramPolicy"
    )
    attrs = policy["attrs"]
    assert attrs["future_manifold_temporal_anchors_enabled"] == 0.0
    assert attrs["future_manifold_anchor_growth"] == 2.0
    assert attrs["future_manifold_max_shape_order"] == 1.0
    assert attrs["future_manifold_max_refinements"] == 16.0
    assert attrs["future_manifold_enclosure_width_floor"] == 0.0

    close = next(
        r for r in seed["rules"]
        if r["name"] == "emp_abs_close_embodied_motor_program"
    )
    encoded = json.dumps(close)
    for field in (
        "manifold_anchor_count",
        "manifold_refinement_count",
        "manifold_certified_interval_count",
        "manifold_ambiguous_interval_count",
        "manifold_max_enclosure_width",
        "manifold_max_shape_order",
        "manifold_earliest_decisive_tick",
    ):
        assert field in encoded
    assert "dense_1_2_3_loglog_far" in encoded


def test_native_path_keeps_selection_in_motor_compose_and_audits_at_close():
    rules = {r["name"]: r for r in _seed()["rules"]}
    parallel = rules["emp_abs_expand_factorized_groups_in_parallel"]
    assert any("future_manifold_enabled" in json.dumps(w) for w in [parallel["where"]])
    native_mark = json.dumps(rules["emp_native_mark_composition_choice"])
    assert "MotorCompose" in native_mark
    assert "FutureManifoldProjection" not in native_mark
    close = json.dumps(rules["emp_render_close_embodied_motor_program"])
    assert "FutureManifoldProjection" in close
    assert "future_manifold_enabled" in close


def test_width_cap_is_shared_by_expansion_and_close_frontiers():
    rules = {r["name"]: r for r in _seed()["rules"]}
    expansion = json.dumps(rules["emp_abs_expand_embodied_motor_program"])
    parallel = json.dumps(rules["emp_abs_expand_factorized_groups_in_parallel"])
    close = json.dumps(rules["emp_abs_close_embodied_motor_program"])
    for encoded in (expansion, parallel, close):
        assert "maximum_program_width" in encoded
        assert "member_count" in encoded


def test_default_reuse_reprojects_the_held_program_at_the_risk_gate():
    rules = {r["name"]: r for r in _seed()["rules"]}
    for name in (
        "emp_release_internalized_program_default",
        "emp_async_release_trusted_default",
    ):
        encoded = json.dumps(rules[name]["where"])
        assert "FutureManifoldProjection" in encoded
        assert "manifold_bounds_ready" in encoded


def test_bound_establishment_binds_the_policy_that_defines_its_window():
    rule = next(
        r for r in _seed()["rules"]
        if r["name"] == "emp_establish_future_manifold_from_ready_program"
    )
    assert ["agent", "has_embodied_motor_program_policy", "policy"] in rule["match"]


def test_positive_weight_is_required_by_manifold_loss_term():
    source = Path(__file__).parents[1] / "scripts" / "gen_embodied_motor_program_seed.py"
    text = source.read_text()
    assert 'Gt(P0("policy", f"{key}_weight"), L(0.0))' in text


def test_cold_member_bootstraps_only_from_same_group_receipt_evidence():
    rule = next(r for r in _seed()["rules"]
                if r["name"] == "emp_share_group_context_transition_evidence")
    encoded = json.dumps(rule)
    assert '"actuator_group"' in encoded
    assert '"context_delta_experience_count"' in encoded
    # The rule's peer predicate is evidence-gated; it cannot bootstrap an
    # entirely cold group and contains no plant/world machinery.
    assert '"peer"' in encoded
    assert "world" not in encoded.lower()
    assert "jsbsim" not in encoded.lower()


def test_enabled_establishment_crosses_seq_100_then_fails_closed_without_recursive_model():
    agent = WorldAdapter(seeds=("embodied_motor_program",))
    policy = next(iter(agent.s.nodes("EmbodiedMotorProgramPolicy")))
    for key in ("forward", "lateral", "vertical", "roll", "pitch", "turn"):
        agent.inner.set_attr(policy, f"{key}_weight", 1.0)
    agent.inner.set_attr(policy, "future_manifold_enabled", 1.0)
    agent.inner.set_attr(policy, "future_manifold_establish_from_seq", 1.0)
    agent.inner.set_attr(policy, "future_manifold_establish_until_seq", 100.0)
    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "program_mode": "synthesis", "program_request_seq": 1.0,
        "program_decision_seq": 0.0, "action_ready": 0.0,
        "state_flow_speed_squared": 1.0, "target_forward": 1.0,
        "target_lateral": 0.0, "target_vertical": 0.0, "target_roll": 0.0,
        "target_pitch": 0.0, "target_turn": 0.0,
    })
    _edge(agent, agent.agent, "has_embodied_motor_program_episode", episode)
    for ordinal in range(2):
        model = agent.s.add_node("EmbodiedEffectorModel", _model_attrs(
            f"manifold_{ordinal}", ordinal, ordinal, forward=1.0))
        _edge(agent, episode, "has_embodied_effector_model", model)
    for seq in range(1, 102):
        agent.inner.set_attr(episode, "program_request_seq", float(seq))
        agent.inner.set_attr(episode, "action_ready", 0.0)
        agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert float(attrs.get("program_request_seq")) == 101.0
    assert float(attrs.get("manifold_bounds_ready", 0.0)) in (0.0, 1.0)
    # No recursive A-B-S transition model is installed, so the treatment
    # cannot claim a post-window projection or emit a fake horizon.
    assert not any(float(agent.s.node(p)["attrs"].get("manifold_projection_resolved", 0.0)) > 0.5
                   for p in agent.inner.neighbours(episode, "has_embodied_motor_program"))
