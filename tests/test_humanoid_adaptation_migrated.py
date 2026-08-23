from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import math
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "domains" / "pybullet_humanoid_world.py"
GENERATOR = ROOT / "scripts" / "gen_humanoid_adaptation_seed.py"
RUNNER = ROOT / "scripts" / "jabberwock_humanoid_adaptation.py"
SEED = ROOT / "seeds" / "humanoid_adaptation.json"
PROTOCOL = ROOT / "protocols" / "humanoid_balance_adaptation_v1.json"


def _configuration():
    from domains.pybullet_humanoid_world import HumanoidBodyConfiguration

    body = json.loads(PROTOCOL.read_text(encoding="utf-8"))["body"]
    return HumanoidBodyConfiguration(
        time_step=body["time_step_seconds"],
        gravity_acceleration=body["gravity_acceleration"],
        action_frames=body["action_frames"],
        settling_frames=body["initial_settling_frames"],
        joint_twitch_radians=body["joint_twitch_radians"],
        maximum_joint_force=body["maximum_joint_force"],
        position_gain=body["position_gain"],
        velocity_gain=body["velocity_gain"],
    )


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def test_humanoid_seed_owns_learning_and_balance_choice():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    chooser = json.dumps(_rule(seed, "ha_choose_learned_balance_twitch"))
    learner = json.dumps(_rule(seed, "ha_learn_opaque_joint_consequence"))

    assert seed["id"] == "humanoid_adaptation"
    assert seed["version"] == "1.15.0"
    assert '"type": "Argmin"' in chooser
    assert "gravity_acceleration" in chooser
    assert '"type": "Sqrt"' in chooser
    for axis in ("dzx", "dzy", "dwx", "dwy"):
        assert f"mean_{axis}" in chooser
    for axis in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"):
        assert f"observed_{axis}" in learner


def test_all_motor_trial_openers_refuse_duplicate_current_request():
    from scripts.gen_humanoid_adaptation_seed import manifest

    rules = {rule["name"]: rule for rule in manifest()["rules"]}
    for name in (
        "ha_open_receipt_backed_motor_trial",
        "ha_open_synthesized_motor_program_trial",
        "ha_bind_synthesized_structure_to_canonical_memory",
        "ha_open_receipt_advanced_motor_sequence_trial",
        "ha_open_reassociated_motor_memory_trial",
    ):
        condition = json.dumps(rules[name]["where"])
        assert rules[name]["batch"] is False
        assert "has_humanoid_motor_trial" in condition
        assert "current_issued_trial" in condition
        assert "request_seq" in condition

    for name in (
        "ha_open_synthesized_motor_program_trial",
        "ha_bind_synthesized_structure_to_canonical_memory",
    ):
        condition = json.dumps(rules[name]["where"])
        assert "current_ready_program" in condition
        assert '"type": "Argmin"' in condition
    program_opener = rules["ha_open_synthesized_motor_program_trial"]
    assert "generalizes_humanoid_action_model" not in json.dumps(
        program_opener["match"]
    )
    assert "program_action_candidate" in json.dumps(program_opener["where"])
    assert "motor_memory_recalled" in json.dumps(program_opener["effects"])
    text = SEED.read_text(encoding="utf-8").lower()
    for forbidden in (
        "hip",
        "knee",
        "ankle",
        "shoulder",
        "elbow",
        "humanoid_actuator_001",
        "humanoid_actuator_042",
    ):
        assert re.search(rf"\b{re.escape(forbidden)}\b", text) is None


def test_humanoid_python_boundary_contains_no_agent_policy():
    source = ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    public = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }

    assert imported_roots.isdisjoint({"substrate", "substrate_rs"})
    assert public == {
        "actuator_options",
        "apply",
            "apply_force_pulse",
            "body_capability_signature",
            "body_shape_signature",
            "close",
            "hold_tonic",
            "observe",
            "reset",
            "scaffold_body_bounce",
            "scaffold_joint_cycle",
            "step",
        }
    assert not {
        "choose",
        "decide",
        "learn",
        "plan",
        "predict",
        "reward",
        "score",
    } & public


def test_full_humanoid_exposes_opaque_dynamic_joint_alphabet():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    import pybullet
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld

    with PyBulletHumanoidWorld(_configuration()) as world:
        initial = world.observe()
        options = world.actuator_options()
        after = world.step(
            ("humanoid_actuator_001", "humanoid_actuator_003"),
            frames=5,
        )
        caregiver_buffered = world.step(
            "humanoid_actuator_001",
            frames=5,
            caregiver_protective_support=True,
        )
        caregiver_half_buffered = world.step(
            "humanoid_actuator_001",
            frames=5,
            caregiver_protective_support=True,
            caregiver_support_scale=0.5,
        )
        caregiver_directional = world.step(
            "humanoid_actuator_001",
            frames=5,
            caregiver_protective_support=True,
            caregiver_manifold_residual=(0.1, -0.2, 0.0, 0.0, 0.3, -0.4, 0.0),
        )
        with pytest.raises(ValueError, match="requires authorization"):
            world.step(
                "humanoid_actuator_001",
                caregiver_support_scale=0.5,
            )
        with pytest.raises(ValueError, match="conflicting joint group"):
            world.step(
                ("humanoid_actuator_001", "humanoid_actuator_002")
            )

        assert (
            pybullet.getConnectionInfo(world._client)["connectionMethod"]
            == pybullet.DIRECT
        )

    assert len(initial["joints"]) == 21
    assert initial["supplied_energy_joules"] == 0.0
    assert after["supplied_energy_joules"] >= 0.0
    assert after["absorbed_energy_joules"] >= 0.0
    assert after["peak_actuator_power_watts"] >= 0.0
    assert len(options) == 43
    assert sum(option["tonic_default"] for option in options) == 1.0
    assert tuple(option["token"] for option in options) == tuple(
        f"humanoid_actuator_{index:03d}" for index in range(43)
    )
    assert not any(
        anatomical_word in option["token"]
        for option in options
        for anatomical_word in (
            "hip",
            "knee",
            "ankle",
            "shoulder",
            "elbow",
            "left",
            "right",
        )
    )
    assert after["step_index"] == 5
    assert after["last_actuator_token"] is None
    assert after["last_actuator_tokens"] == (
        "humanoid_actuator_001",
        "humanoid_actuator_003",
    )
    assert caregiver_buffered["caregiver_protective_support_applied"] == 1
    assert caregiver_buffered["caregiver_support_scale"] == 1.0
    assert (
        caregiver_buffered["caregiver_support_impulse_newton_seconds"] > 0.0
    )
    assert caregiver_half_buffered["caregiver_support_scale"] == 0.5
    assert caregiver_half_buffered[
        "caregiver_support_impulse_newton_seconds"
    ] == pytest.approx(
        caregiver_buffered["caregiver_support_impulse_newton_seconds"] * 0.5
    )
    assert caregiver_directional["caregiver_support_force_world"][0] < 0.0
    assert caregiver_directional["caregiver_support_force_world"][1] > 0.0
    assert caregiver_directional["caregiver_support_torque_world"][0] < 0.0
    assert caregiver_directional["caregiver_support_torque_world"][1] < 0.0
    assert options[1]["actuator_group"] != options[3]["actuator_group"]
    assert all(
        math.isfinite(value)
        for value in (
            *after["base_position"],
            *after["base_orientation_xyzw"],
        )
    )


def test_reset_can_enact_graph_selected_integer_orientation_fixture():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld

    with PyBulletHumanoidWorld(_configuration()) as world:
        selected = world.reset(initial_base_quarter_turns=(1, 0, 0))
        with pytest.raises(ValueError, match="three integers"):
            world.reset(initial_base_quarter_turns=(1, 0))

    assert len(selected["joints"]) == 21
    assert all(math.isfinite(value) for value in (
        *selected["base_position"],
        *selected["base_orientation_xyzw"],
    ))


def test_motor_targets_are_situated_in_the_current_sensed_configuration():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld

    with PyBulletHumanoidWorld(_configuration()) as world:
        initial = world.observe()
        first = world.step("humanoid_actuator_001", frames=5)
        second = world.step("humanoid_actuator_001", frames=5)
        held = world.hold_tonic(1)

    initial_positions = tuple(
        joint["position"] for joint in initial["joints"]
    )
    first_positions = tuple(joint["position"] for joint in first["joints"])
    second_positions = tuple(joint["position"] for joint in second["joints"])
    assert first["motor_reference_positions"] == pytest.approx(
        initial_positions
    )
    assert second["motor_reference_positions"] == pytest.approx(
        first_positions
    )
    assert held["motor_reference_positions"] == pytest.approx(
        second_positions
    )
    assert held["motor_target_positions"] == pytest.approx(second_positions)
    assert held["motor_command_displacements"] == pytest.approx(
        (0.0,) * len(second_positions)
    )
    assert held["motor_reference_kind"] == "current_sensed_configuration"
    assert "home" not in inspect.getsource(
        PyBulletHumanoidWorld._write_twitches
    ).lower()


def test_graph_owns_local_motor_fixations_and_efference_receipts():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    names = {rule["name"] for rule in seed["rules"]}
    assert {
        "ha_mint_situated_motor_fixation",
            "ha_refresh_situated_motor_fixation",
            "ha_propose_situated_motor_fixation",
            "ha_refresh_candidate_motor_fixation",
            "ha_reject_stale_candidate_motor_fixation",
            "ha_transition_situated_motor_fixation",
            "ha_bind_situated_motor_reference",
        "ha_issue_situated_motor_efference_copy",
        "ha_confirm_situated_motor_efference_copy",
    } <= names

    fixation_text = json.dumps(
        _rule(seed, "ha_mint_situated_motor_fixation")
    ).lower()
    transition_text = json.dumps(
        _rule(seed, "ha_transition_situated_motor_fixation")
    ).lower()
    copy_text = json.dumps(
        _rule(seed, "ha_confirm_situated_motor_efference_copy")
    ).lower()
    assert "current_sensed_configuration" in fixation_text
    assert "gravity_acceleration" in fixation_text
    assert "physics_time_step" in fixation_text
    assert "configuration_shape" in transition_text
    assert "gait_surprise_confirmation_receipts" in transition_text
    assert "motor_reference_error_energy" in copy_text
    assert "home" not in fixation_text + transition_text + copy_text


@pytest.mark.parametrize(
    "field,value",
    (
        ("time_step", 0.0),
        ("gravity_acceleration", -9.81),
        ("action_frames", 0),
        ("settling_frames", True),
        ("joint_twitch_radians", -0.1),
        ("maximum_joint_force", float("nan")),
    ),
)
def test_invalid_humanoid_body_configuration_is_rejected(field, value):
    from domains.pybullet_humanoid_world import HumanoidBodyConfiguration

    kwargs = {
        "time_step": 1.0 / 240.0,
        "gravity_acceleration": 9.81,
        "action_frames": 2,
        "settling_frames": 10,
        "joint_twitch_radians": 0.1,
        "maximum_joint_force": 50.0,
        "position_gain": 0.3,
        "velocity_gain": 1.0,
    }
    kwargs[field] = value
    with pytest.raises(ValueError):
        HumanoidBodyConfiguration(**kwargs)


def test_runner_only_enacts_graph_authored_tokens():
    source = RUNNER.read_text(encoding="utf-8")
    run_arm = inspect.getsource(
        __import__(
            "scripts.jabberwock_humanoid_adaptation",
            fromlist=["_run_arm"],
        )._run_arm
    )

    assert 'WorldAdapter(seeds=("humanoid_adaptation",))' in run_arm
    assert "token, trial, decision = _request_action" in run_arm
    assert "after = _enact_graph_command(world, token, decision)" in run_arm
    enactor = inspect.getsource(
        __import__(
            "scripts.jabberwock_humanoid_adaptation",
            fromlist=["_enact_graph_command"],
        )._enact_graph_command
    )
    assert 'decision["selected_motor_tokens"]' in enactor
    assert 'decision["selected_response_frames"]' in enactor
    assert "min(effects" not in source
    assert "choose_action" not in source
    assert "correction_cost" not in source
    assert '"semantics": "unknown"' in run_arm
    assert '"policy_owner": "rust_graph"' in run_arm
    generator = GENERATOR.read_text(encoding="utf-8")
    assert "def correction_cost" in generator
    assert '"type": "Argmin"' in generator


def test_gaits_are_graph_held_contact_attractors_not_speed_bands():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    gaits = [
        node
        for node in seed["nodes"]
        if node["type"] == "HumanoidGaitAttractor"
    ]
    regimes = [
        node
        for node in seed["nodes"]
        if node["type"] == "HumanoidResidualRegime"
    ]

    # The attractors are identified by ORDINAL, not by a name.  Rung 4
    # (2026-08-10) removed `name` / `gait_name` / `coordination_family` and
    # every one of the 15 recorded metrics came back byte-identical, so the
    # taxonomy was decoration for the decision path.  Asserting the ordinal
    # spine is the stronger form of this test's own claim: what makes these
    # contact attractors rather than speed bands is the ordinal and its
    # arithmetic derivatives, which is all any rule ever read.
    assert [node["attrs"]["ordinal"] for node in gaits] == [0.0, 1.0, 2.0, 3.0]
    assert not any(
        key in node["attrs"]
        for node in gaits + regimes
        for key in ("name", "gait_name", "coordination_family")
    )
    assert len(regimes) == len(gaits) * 9
    assert {
        node["attrs"]["gait_ordinal"] for node in regimes
    } == {node["attrs"]["ordinal"] for node in gaits}
    assert all(
        "target_speed" not in key
        for node in gaits
        for key in node["attrs"]
    )
    assert [
        node["attrs"]["flight_phase_authority"] for node in gaits
    ] == [0.0, 1.0, 1.0, 1.0]
    assert len([
        edge
        for edge in seed["edges"]
        if edge["type"] == "realizes_humanoid_gait_with_regime"
    ]) == len(regimes)


def test_every_motor_trial_captures_action_time_gait_eligibility():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    trial_rules = [
        rule
        for rule in seed["rules"]
        if any(
            effect[0] == "add_node"
            and effect[2] == "HumanoidMotorTrial"
            for effect in rule.get("effects", [])
        )
    ]

    assert len(trial_rules) == 5
    for rule in trial_rules:
        trial_attrs = next(
            effect[3]
            for effect in rule["effects"]
            if effect[0] == "add_node"
            and effect[2] == "HumanoidMotorTrial"
        )
        regime_term = json.dumps(trial_attrs["residual_regime_ordinal"])
        gait_term = json.dumps(trial_attrs["gait_attractor_ordinal"])
        assert "active_residual_regime_ordinal" in regime_term
        assert "active_gait_attractor_ordinal" in gait_term


def test_closed_residual_window_advances_graph_sweep_on_action_sheet():
    from domains.embodied_graph_transducer import add_unchecked_edge
    from substrate.world_adapter import WorldAdapter

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    sweep = _rule(seed, "ha_curiosity_selects_coordination_experiment")
    learner = _rule(seed, "ha_learn_persistent_residual_regime")
    assert sweep["latency_class"] == "hard_realtime"
    sweep_text = json.dumps(sweep)
    assert "EvalSubgraph" in sweep_text
    assert "action_score_term" in sweep_text
    assert "decision_core" in seed["depends_on"]
    assert learner["latency_class"] == "hard_realtime"
    learner_where = json.dumps(learner["where"])
    assert "residual_regime_ordinal" in learner_where
    assert "active_residual_regime_ordinal" not in learner_where
    assert '"status"' not in learner_where

    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    policy = agent.s.nodes("HumanoidPolicy")[0]
    agent.inner.set_attr(
        policy,
        "persistent_task_residual_authority",
        1.0,
    )
    regimes = sorted(
        agent.s.nodes("HumanoidResidualRegime"),
        key=lambda node: agent.s.node(node)["attrs"]["ordinal"],
    )
    agent.inner.set_attr(regimes[0], "sample_count", 9.0)
    agent.inner.set_attr(regimes[0], "asym_count", 0.0)
    agent.inner.set_attr(regimes[0], "q", 1.0)
    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "locomotion",
        "mode": "directed_walk",
        "active_gait_attractor_ordinal": 0.0,
        "active_residual_regime_ordinal": 0.0,
        "residual_regime_window_complete": 1.0,
        "residual_regime_window_sample_count": 9.0,
        "residual_regime_selection_count": 0.0,
    })
    add_unchecked_edge(
        agent,
        agent.agent,
        "has_humanoid_episode",
        episode,
    )

    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["active_residual_regime_ordinal"] == 1.0
    assert attrs["active_gait_attractor_ordinal"] == 0.0
    assert attrs["residual_regime_window_complete"] == 0.0
    assert attrs["residual_regime_window_sample_count"] == 0.0
    assert attrs["residual_regime_selection_count"] == 1.0
    assert agent.s.node(regimes[0])["attrs"]["completed_windows"] == 1.0

    for regime in regimes[1:9]:
        agent.inner.set_attr(regime, "sample_count", 9.0)
        agent.inner.set_attr(regime, "asym_count", 0.0)
        agent.inner.set_attr(regime, "q", 1.0)
    agent.inner.remove_edge(
        episode,
        "evaluates_humanoid_residual_regime",
        regimes[1],
    )
    add_unchecked_edge(
        agent,
        episode,
        "evaluates_humanoid_residual_regime",
        regimes[8],
    )
    agent.inner.set_attr(episode, "active_residual_regime_ordinal", 8.0)
    agent.inner.set_attr(episode, "residual_regime_window_complete", 1.0)
    agent.inner.set_attr(
        episode,
        "residual_regime_window_sample_count",
        9.0,
    )
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["active_residual_regime_ordinal"] == 9.0
    assert attrs["active_gait_attractor_ordinal"] == 1.0


def test_core_curiosity_can_choose_nonordinal_coordination_probe():
    from domains.embodied_graph_transducer import add_unchecked_edge
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    policy = agent.s.nodes("HumanoidPolicy")[0]
    agent.inner.set_attr(
        policy,
        "persistent_task_residual_authority",
        1.0,
    )
    regimes = sorted(
        agent.s.nodes("HumanoidResidualRegime"),
        key=lambda node: agent.s.node(node)["attrs"]["ordinal"],
    )
    agent.inner.set_attr(regimes[0], "sample_count", 9.0)
    agent.inner.set_attr(regimes[0], "asym_count", 0.0)
    agent.inner.set_attr(regimes[0], "q", 1.0)
    agent.inner.set_attr(regimes[17], "asym_count", 100.0)
    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "locomotion",
        "mode": "directed_walk",
        "active_gait_attractor_ordinal": 0.0,
        "active_residual_regime_ordinal": 0.0,
        "residual_regime_window_complete": 0.0,
        "residual_regime_window_sample_count": 9.0,
        "residual_regime_selection_count": 0.0,
    })
    add_unchecked_edge(
        agent,
        agent.agent,
        "has_humanoid_episode",
        episode,
    )

    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["active_residual_regime_ordinal"] == 17.0
    assert attrs["active_gait_attractor_ordinal"] == 1.0


def test_graph_learns_full_humanoid_and_survives_matched_impulse():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    from scripts.jabberwock_humanoid_adaptation import run_experiment

    result = run_experiment(PROTOCOL)
    adaptive = result["adaptive"]
    tonic = result["tonic_control"]

    assert result["joint_count"] == 21
    assert result["opaque_actuator_count"] == 43
    assert result["policy_owner"] == "rust_graph"
    assert result["pre_recovery_trajectories_identical"] is True
    assert "world_frame_force_newtons" not in result["perturbation"]
    assert result["perturbation"]["world_frame_force_body_weights"] == [
        9.0,
        2.25,
        0.0,
    ]
    expected_body_weight = (
        adaptive["body_mass"] * _configuration().gravity_acceleration
    )
    assert result["perturbation"][
        "resolved_world_frame_force_newtons"
    ] == pytest.approx([
        9.0 * expected_body_weight,
        2.25 * expected_body_weight,
        0.0,
    ])
    assert all(
        row["experience_count"] == 1.0
        for row in adaptive["models"]
        if row["tonic_default"] == 0.0
    )
    assert adaptive["first_fall_action"] is None
    assert adaptive["nominal_response_frames"] == 12
    assert adaptive["minimum_recovery_response_frames"] == 2
    assert adaptive["maximum_recovery_response_frames"] == 2
    assert adaptive["minimum_height"] > adaptive["height_floor"]
    assert adaptive["upright_at_end_graph_assessment"] == 1.0
    assert adaptive["recovery_action_diversity"] > 20
    assert tonic["first_fall_action"] is None
    assert tonic["minimum_recovery_response_frames"] == 2
    assert tonic["minimum_height"] > tonic["height_floor"]
    assert tonic["upright_at_end_graph_assessment"] == 1.0
    assert result["paired_effect"]["minimum_height_advantage"] > 0.0
    assert result["paired_effect"]["tilt_integral_reduction"] > 0.0
    assert adaptive["motor_fixation_count"] >= 1.0
    assert adaptive["motor_efference_copy_count"] >= 42.0
    assert adaptive["minimum_height_graph_assessment"] == pytest.approx(
        adaptive["minimum_height"]
    )
    assert adaptive["peak_tilt_graph_assessment"] == pytest.approx(
        adaptive["peak_tilt"]
    )
