from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from domains.embodied_graph_transducer import add_unchecked_edge as _edge
from scripts import gen_embodied_motor_program_seed
from scripts.jabberwock_active_aero import (
    CONSEQUENCES,
    _settle_graph_request,
    run_active_aero,
)
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "embodied_motor_program.json"
GENERATOR = ROOT / "scripts" / "gen_embodied_motor_program_seed.py"
WORLD = ROOT / "domains" / "pybullet_robot_world.py"
PROTOCOL = ROOT / "protocols" / "active_aero_wheeled_v1.json"
RESULT = ROOT / "results" / "active_aero_wheeled_v1.json"


def _model_attrs(
    token: str,
    ordinal: int,
    group: int,
    *,
    forward: float = 0.0,
    turn: float = 0.0,
    normal_load: float = 0.0,
) -> dict[str, float | str]:
    attrs: dict[str, float | str] = {
        "token": token,
        "ordinal": float(ordinal),
        "actuator_group": float(group),
        "activation_magnitude": 1.0,
        "available": 1.0,
        "experience_count": 1.0,
        "last_learning_seq": 0.0,
        "recalibration_required": 0.0,
        "mean_flow_speed_squared": 0.0,
        "flow_variance_sum": 0.0,
    }
    observations = {
        "forward": forward,
        "lateral": 0.0,
        "vertical": 0.0,
        "roll": 0.0,
        "pitch": 0.0,
        "turn": turn,
        "normal_load": normal_load,
        "drag": 0.0,
        "energy": 0.0,
    }
    for key in CONSEQUENCES:
        attrs[f"mean_{key}"] = observations[key]
        attrs[f"flow_gain_{key}"] = 0.0
        attrs[f"flow_covariance_{key}"] = 0.0
    return attrs


def test_shared_seed_is_factorized_morphology_neutral_and_collapse_backed():
    payload = json.loads(SEED.read_text(encoding="utf-8"))
    assert payload == gen_embodied_motor_program_seed.manifest()
    names = {rule["name"] for rule in payload["rules"]}
    assert payload["depends_on"] == [
        "embodied_pareto_profile",
        "motor_decision_collapse",
        "embodied_structural_limits",
    ]
    assert {
        "emp_abs_open_embodied_motor_program",
        "emp_abs_expand_embodied_motor_program",
        "emp_abs_close_embodied_motor_program",
        "emp_open_selected_motor_program_trial",
        "emp_learn_factorized_effector_from_exact_receipt",
        "emp_learn_compound_program_interaction_residual",
        # v1.18.0: restored.  The shape trigger that briefly replaced this
        # measured three episodes worse and was not rescued by credit
        # assignment or the adaptation rate (block DC).
        "emp_reopen_factorized_calibration_on_compound_surprise",
    } <= names
    serialized = json.dumps(payload).lower()
    for forbidden in ("racecar", "spoiler", "wing", "wheel", "rotor"):
        assert forbidden not in serialized
    assert "includes_embodied_effector_model" in serialized
    assert "actuator_group" in serialized
    assert "activation_magnitude" in serialized
    assert "baseline_prediction" not in serialized


def test_analysis_by_synthesis_constructs_arbitrary_four_group_program():
    agent = WorldAdapter(seeds=("embodied_motor_program",))
    policy = next(iter(agent.s.nodes("EmbodiedMotorProgramPolicy")))
    for key, value in {
        "forward_weight": 1.0,
        "turn_weight": 1.0,
        "normal_load_weight": 1.0,
        "lateral_weight": 1.0,
        "drag_weight": 0.0,
        "energy_weight": 0.0,
        "activation_weight": 0.0,
    }.items():
        agent.inner.set_attr(policy, key, value)
    episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
        "program_mode": "synthesis",
        "program_request_seq": 1.0,
        "program_decision_seq": 0.0,
        "action_ready": 0.0,
        "decision_armed": 0.0,
        "decision_request_epoch": 0.0,
        "last_opened_decision_epoch": 0.0,
        "last_published_decision_epoch": 0.0,
        "last_program_trial_epoch": 0.0,
        "recalibration_count": 0.0,
        "state_flow_speed_squared": 0.0,
        "target_forward": 1.0,
        "target_lateral": 0.0,
        "target_turn": 1.0,
        "target_normal_load": 2.0,
    })
    _edge(agent, agent.agent, "has_embodied_motor_program_episode", episode)
    _edge(agent, agent.agent, "has_embodied_motor_episode", episode)
    consequences = (
        {"forward": 1.0},
        {"turn": 1.0},
        {"normal_load": 1.0},
        {"normal_load": 1.0},
        {},
    )
    for ordinal, consequence in enumerate(consequences):
        model = agent.s.add_node(
            "EmbodiedEffectorModel",
            _model_attrs(
                f"opaque_{ordinal}",
                ordinal,
                ordinal,
                **consequence,
            ),
        )
        _edge(agent, episode, "has_embodied_effector_model", model)

    _settle_graph_request(agent, episode, 1)
    trial = agent.inner.neighbours(
        episode,
        "has_embodied_motor_program_trial",
    )[0]
    program = agent.inner.neighbours(
        trial,
        "enacts_embodied_motor_program",
    )[0]
    members = agent.inner.neighbours(
        program,
        "includes_embodied_effector_model",
    )
    assert agent.s.node(program)["attrs"]["source"] == "analysis_by_synthesis"
    assert agent.s.node(program)["attrs"]["member_count"] == 4.0
    assert {
        agent.s.node(member)["attrs"]["actuator_group"]
        for member in members
    } == {0.0, 1.0, 2.0, 3.0}
    assert agent.s.node(episode)["attrs"]["selected_option_ref"] == program


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet robot extra is not installed",
)
def test_factorized_plant_applies_concurrent_aero_and_rejects_group_conflicts():
    from domains.pybullet_robot_world import PyBulletRobotWorld

    with PyBulletRobotWorld(
        "racecar_active_aero",
        control_steps=12,
    ) as world:
        options = world.actuator_options()
        assert len(options) == 18
        assert {
            option["group_ordinal"] for option in options
        } == {0.0, 1.0, 2.0, 3.0, 4.0, 5.0}
        for _ in range(20):
            world.step_program(("effector_002", "effector_004"))
        baseline = world.step_program(("effector_002", "effector_004"))
        active = world.step_program((
            "effector_002",
            "effector_004",
            "effector_008",
            "effector_011",
            "effector_014",
            "effector_017",
        ))
        assert active["external_normal_force_newtons"] > 0.0
        assert active["aerodynamic_dissipation_joules"] > 0.0
        assert sum(active["wheel_normal_loads"]) > 0.0
        assert baseline["external_normal_force_newtons"] == 0.0
        with pytest.raises(ValueError, match="must contain"):
            world.step_program(())
        with pytest.raises(ValueError, match="must contain"):
            world.step_program("effector_002")
        with pytest.raises(ValueError, match="at most once"):
            world.step_program(("effector_006", "effector_008"))


@pytest.mark.skipif(
    importlib.util.find_spec("pybullet") is None,
    reason="PyBullet robot extra is not installed",
)
def test_hidden_broken_surface_reopens_calibration_and_changes_program():
    result = run_active_aero(
        steps=110,
        damage_onset=60,
        broken_surface=2,
    )
    group_four_tokens = {
        row["token"]
        for row in result["models"]
        if row["actuator_group"] == 4.0
    }
    positive_broken_token = next(
        row["token"]
        for row in result["models"]
        if row["ordinal"] == 14.0
    )
    before_damage = result["trace"][52:62]
    after_recalibration = result["trace"][97:]

    assert any(
        positive_broken_token in row["tokens"]
        for row in before_damage
    )
    assert result["recalibration_count"] == 1.0
    assert result["final_program_mode"] == "synthesis"
    assert all(
        group_four_tokens.isdisjoint(row["tokens"])
        for row in after_recalibration
    )
    assert any(row["member_count"] > 1 for row in after_recalibration)
    broken_model = result["models"][14]
    assert broken_model["mean_normal_load"] == 0.0
    assert broken_model["flow_gain_normal_load"] == 0.0


def test_generator_and_world_do_not_materialize_a_compound_cartesian_lattice():
    generator = GENERATOR.read_text(encoding="utf-8")
    world = WORLD.read_text(encoding="utf-8")
    assert "includes_embodied_effector_model" in generator
    assert "Cartesian product" in world
    assert "_factorized_token_map" in world
    assert "range(group_count)" in world
    assert "range(6)" not in world
    assert "for command in (-1.0, 0.0, 1.0)" in world
    assert "step_program" in world


def test_checked_result_satisfies_the_declared_damage_gates():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    run = protocol["run"]
    assert result["steps"] == run["steps"]
    assert result["damage_onset"] == run["damage_onset_action"]
    assert result["broken_surface"] == run["broken_surface_index"]
    assert result["recalibration_count"] == 1.0
    assert result["maximum_program_width"] >= (
        protocol["gates"]["minimum_observed_program_width"]
    )
    assert result["final_program_mode"] == "synthesis"
