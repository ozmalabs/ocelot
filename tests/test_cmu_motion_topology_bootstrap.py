import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cmu_mocap"
TOPOLOGY = DATA / "topology.json"
SEED = ROOT / "seeds" / "cmu_motion_topology_bootstrap.json"
GENERATOR = ROOT / "scripts" / "gen_cmu_motion_topology_seed.py"
HARVESTER = ROOT / "scripts" / "harvest_cmu_motion_topology.py"


def _assert_no_float(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_float(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_float(nested)


def test_checked_in_topology_is_categorical_integer_and_pose_free():
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    _assert_no_float(topology)
    assert topology["raw_data_redistributed"] is False
    assert topology["raw_pose_values_retained"] is False
    assert topology["numeric_kinematic_values_retained"] is False
    assert len(topology["clips"]) == 9
    encoded = json.dumps(topology)
    for forbidden in ("joint_angles", "root_position", "command", "torque"):
        assert forbidden not in encoded
    assert sum(clip["frame_count"] for clip in topology["clips"]) == 6800


def test_manifest_checksums_match_held_subset_when_downloaded():
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    raw = DATA / "raw"
    if not raw.exists():
        pytest.skip("raw CMU subset is intentionally not redistributed")
    for row in manifest["clips"]:
        subject = int(row["subject"])
        trial = int(row["trial"])
        for filename, expected in (
            (f"{subject}.asf", row["asf_sha256"]),
            (f"{subject}_{trial:02d}.amc", row["amc_sha256"]),
        ):
            assert hashlib.sha256((raw / filename).read_bytes()).hexdigest() == expected


def test_topology_reproduces_from_checksum_pinned_raw_subset_when_held():
    if not (DATA / "raw").exists():
        pytest.skip("raw CMU subset is intentionally not redistributed")
    before = TOPOLOGY.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(HARVESTER)], cwd=ROOT, check=True)
    assert TOPOLOGY.read_text(encoding="utf-8") == before


def test_seed_reproduces_offline_and_contains_only_output_null_topology(tmp_path):
    before = SEED.read_text(encoding="utf-8")
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    assert SEED.read_text(encoding="utf-8") == before
    seed = json.loads(before)
    _assert_no_float(seed)
    assert seed["depends_on"] == ["embodied_capability_bootstrap"]
    assert seed["rules"] == []
    assert len([
        node for node in seed["nodes"]
        if node["type"] == "EmbodiedMotorPlanHint"
    ]) == 9
    assert len([
        node for node in seed["nodes"]
        if node["type"] == "EmbodiedMotorPlanHintStage"
    ]) == 73
    assert all(
        node["attrs"].get("output_authority") == 0
        for node in seed["nodes"]
    )
    assert all(
        node["attrs"]["requires_observed_consequence_shape"] == 1
        for node in seed["nodes"]
        if node["type"] == "EmbodiedMotorPlanHintStage"
    )
    assert any(
        node["type"] == "EmbodiedMotorConsequenceRoutingShape"
        for node in seed["nodes"]
    )


def test_translation_is_a_relation_not_a_privileged_direction():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    stages = [
        node for node in seed["nodes"]
        if node["type"] == "EmbodiedMotorPlanHintStage"
    ]
    signatures = json.dumps([
        stage["attrs"]["signature"] for stage in stages
    ])
    assert "translation_relation" in signatures
    assert "increasing" in signatures
    assert "decreasing" in signatures
    assert "forward" not in signatures
    assert "backward" not in signatures
    evidence = [
        node for node in seed["nodes"]
        if node["type"] == "ObservedMotionTopologyEvidence"
        and node["attrs"]["source"] == "cmu:47:01"
    ]
    assert evidence[0]["attrs"]["opposed_translation_observed"] == 1


def test_transition_graph_preserves_recurrence_without_unrolled_trajectory():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    transition_edges = [
        edge for edge in seed["edges"]
        if edge["type"] == "can_transition_to_embodied_motor_plan_hint_stage"
    ]
    assert len(transition_edges) == 178
    assert all(edge["attrs"]["observation_count"] > 0 for edge in transition_edges)
    pairs = {
        (edge["src"]["local"], edge["tgt"]["local"])
        for edge in transition_edges
    }
    assert any((target, source) in pairs for source, target in pairs)


def test_contact_topology_recovers_expected_regime_changes():
    topology = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    clips = {clip["source"]: clip for clip in topology["clips"]}

    walk_support = {
        state["support_topology"] for state in clips["cmu:47:01"]["states"]
    }
    assert walk_support == {"single_lower_support", "paired_lower_support"}

    jump_support = {
        state["support_topology"] for state in clips["cmu:118:01"]["states"]
    }
    assert jump_support == {"paired_lower_support", "unsupported"}

    roll_and_get_up_support = {
        state["support_topology"]
        for source in ("cmu:128:10", "cmu:140:01", "cmu:140:03")
        for state in clips[source]["states"]
    }
    assert "upper_support" in roll_and_get_up_support
    assert "distributed_support" in roll_and_get_up_support


def test_humanoid_loads_observed_topology_through_graph_dependency():
    humanoid = json.loads(
        (ROOT / "seeds" / "humanoid_adaptation.json").read_text(encoding="utf-8")
    )
    assert "cmu_motion_topology_bootstrap" in humanoid["depends_on"]
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    evidence = agent.inner.neighbours(
        agent.agent, "has_observed_motion_topology_evidence"
    )
    assert len(evidence) == 9
    assert all(
        agent.s.node(node)["attrs"]["output_authority"] == 0
        for node in evidence
    )


def test_observed_states_do_not_enter_generic_cartesian_program_matcher():
    humanoid = json.loads(
        (ROOT / "seeds" / "humanoid_adaptation.json").read_text(encoding="utf-8")
    )
    rules = {rule["name"]: rule for rule in humanoid["rules"]}
    assert "ha_classify_grounded_program_consequence_shape" in rules
    for name in (
        "ha_bind_motor_plan_hint_stage_search_basin",
        "ha_route_abstract_motor_plan_hint_stage_basin",
    ):
        encoded = json.dumps(rules[name])
        assert "requires_observed_consequence_shape" in encoded
