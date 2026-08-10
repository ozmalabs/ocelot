import json
import subprocess
import sys
from pathlib import Path

import pytest

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "gen_embodied_capability_bootstrap_seed.py"
SEED = ROOT / "seeds" / "embodied_capability_bootstrap.json"


def _assert_no_float(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_float(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_float(nested)


def test_seed_is_reproducible_integer_native_and_output_null(tmp_path):
    before = SEED.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    assert SEED.read_text(encoding="utf-8") == before

    seed = json.loads(before)
    _assert_no_float(seed)
    source = GENERATOR.read_text(encoding="utf-8")
    assert "float(" not in source
    assert seed["depends_on"] == ["capability_collapse"]
    assert seed["rules"] == []
    for node in seed["nodes"]:
        if node["type"] in {
            "EmbodiedBootstrapSituation",
            "EmbodiedMotorPlanHint",
            "EmbodiedMotorPlanHintStage",
        }:
            assert node["attrs"]["output_authority"] == 0


def test_bootstraps_cover_development_recovery_composition_and_future_hands():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    hints = {
        node["attrs"]["bootstrap_family"]: node
        for node in seed["nodes"]
        if node["type"] == "EmbodiedMotorPlanHint"
    }
    assert {
        "embodiment_calibration",
        "righting_and_get_up",
        "fall_management",
        "disturbance_rejection",
        "locomotion",
        "frame_discovery",
        "whole_body_composition",
        "contact_manipulation",
        "hybrid_locomotion",
        "ballistic_transition",
    }.issubset(hints)
    assert all(hint["attrs"]["stage_count"] == 4 for hint in hints.values())


def test_humanoid_loads_bootstraps_through_normal_hint_shape_pipeline():
    humanoid = json.loads(
        (ROOT / "seeds" / "humanoid_adaptation.json").read_text(encoding="utf-8")
    )
    assert "embodied_capability_bootstrap" in humanoid["depends_on"]
    rule_names = {rule["name"] for rule in humanoid["rules"]}
    assert "ha_consider_shape_matched_motor_plan_hint" in rule_names
    assert "ha_route_abstract_motor_plan_hint_stage_basin" in rule_names
    assert "ha_classify_grounded_program_routing_shape" in rule_names
    assert "ha_bind_indexed_bootstrap_stage_basin" in rule_names
    rules = {rule["name"]: rule for rule in humanoid["rules"]}
    for name in (
        "ha_consider_shape_matched_motor_plan_hint",
        "ha_classify_grounded_program_routing_shape",
        "ha_bind_indexed_bootstrap_stage_basin",
    ):
        assert rules[name]["latency_class"] == "hard_realtime"
        assert rules[name]["area"] == "humanoid_sensorimotor_adaptation"
        assert rules[name]["batch"] is True
        _assert_no_float(rules[name])
    for name in (
        "ha_bind_motor_plan_hint_stage_search_basin",
        "ha_route_abstract_motor_plan_hint_stage_basin",
    ):
        assert rules[name]["latency_class"] == "background"
        assert rules[name]["area"] == "embodied_sensorimotor"
        _assert_no_float(rules[name])
    grounding = next(
        rule for rule in humanoid["rules"]
        if rule["name"] == "ha_ground_synthesized_motor_program_from_receipt"
    )
    encoded = json.dumps(grounding)
    assert '["set_attr", "plan", "name"' in encoded
    assert '["set_attr", "plan", "signature"' in encoded
    assert "FromJsonString" in encoded
    assert "motor_task_context" in encoded
    assert "motor_task_phase" in encoded


def test_no_seed_contains_commands_joint_identity_or_global_home():
    text = SEED.read_text(encoding="utf-8").lower()
    for forbidden in (
        "humanoid_actuator_",
        "joint_angle",
        "target_torque",
        "global_home",
        "fixed_trajectory",
    ):
        assert forbidden not in text


def test_humanoid_dependency_materializes_bootstraps_in_the_graph():
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    hints = agent.inner.neighbours(
        agent.agent, "has_embodied_motor_plan_hint_library"
    )
    names = {
        agent.s.node(hint)["attrs"].get("name")
        for hint in hints
    }
    assert "bootstrap:development:supported_range_discovery" in names
    assert "bootstrap:development:righting_support_reacquisition" in names
    assert "bootstrap:whole_body:compound_task_residual" in names
    stages = [
        stage for stage in agent.s.nodes("EmbodiedMotorPlanHintStage")
        if agent.s.node(stage)["attrs"].get("name", "").startswith(
            "bootstrap:"
        )
    ]
    assert stages
    assert all(agent.inner.neighbours(
        stage, "routes_through_embodied_motor_routing_shape"
    ) for stage in stages)


def test_cold_grounded_program_enters_search_and_consequence_indexes_without_system_two():
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    episode = agent.s.add_node("HumanoidEpisode", {
        "motor_plan_query_signature": (("motor_task", "locomotion"),),
        "motor_plan_hint_count": 0.0,
        "motor_plan_hint_escalation_count": 0.0,
        "motor_plan_basin_seed_count": 0.0,
        "state_seq": 1.0,
        "action_ready": 0.0,
    })
    agent.inner.add_edge(agent.agent, "has_humanoid_episode", episode)
    program = agent.s.add_node("HumanoidMotorProgram", {
        "name": "situated_motor_program:test",
        "signature": (
            ("motor_task_context", "locomotion"),
            ("motor_task_phase", "preparation"),
        ),
        "motor_task_context": "locomotion",
        "motor_task_phase": "preparation",
        "observed_height_energy_relation": "held",
        "status": "grounded",
    })
    agent.inner.add_edge(episode, "has_humanoid_motor_program", program)
    work_bound = len(agent.inner.neighbours(
        agent.agent, "has_embodied_motor_plan_hint_library"
    )) + len(agent.inner.neighbours(
        agent.agent, "has_embodied_motor_routing_shape"
    )) + len(agent.inner.neighbours(
        agent.agent, "has_embodied_motor_consequence_routing_shape"
    ))
    for _ in range(work_bound):
        agent.tick()
        if (
            program in agent.inner.neighbours(
                episode, "has_humanoid_motor_program_search_index"
            )
            and agent.inner.neighbours(
                program, "realizes_embodied_motor_consequence_shape"
            )
        ):
            break
    assert len(agent.inner.neighbours(
        program, "realizes_embodied_motor_routing_shape"
    )) == 1
    assert len(agent.inner.neighbours(
        program, "realizes_embodied_motor_consequence_shape"
    )) == 1
    assert program in agent.inner.neighbours(
        episode, "has_humanoid_motor_program_search_index"
    )
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["motor_plan_hint_count"] > 0.0
    assert attrs["motor_plan_hint_escalation_count"] == 0.0
