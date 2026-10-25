"""Development gates for paired native goal action and transfer curves."""
from evaluation.ousiometrics.behavior_panel import (
    CONTROL_ARMS, LEARNING_HORIZONS, PRIMARY_ARMS, development_panel, run_tool_trial,
)
from evaluation.ousiometrics.worlds import FactorProfile


def test_same_learning_horizon_and_worlds():
    panel = development_panel(seeds=(28091,), frames=PRIMARY_ARMS,
                              families=("tool_intervention",))
    rows = panel["rows"]
    assert len(rows) == 2
    for row in rows:
        assert row["learning_horizons"] == list(LEARNING_HORIZONS)
        assert len(row["checkpoints"]) == len(LEARNING_HORIZONS)
    paired = [row["checkpoints"] for row in rows]
    assert [[c["horizon"] for c in curve] for curve in paired] == [
        list(LEARNING_HORIZONS), list(LEARNING_HORIZONS)]
    for left, right in zip(*paired):
        assert left["source_contexts"] == right["source_contexts"]
        assert left["target_calibration_context"] == right["target_calibration_context"]
        assert left["score_context"] == right["score_context"]
        assert left["target_binding"] == right["target_binding"]
        assert left["decision"] is None or left["decision"]["status"] == "consumed"


def test_full_reference_no_false_advantage():
    profile = FactorProfile(.8, 0.0, 0.0, 0.0, 0.0)
    rows = [run_tool_trial(frame, profile=profile, seed=28101) for frame in (
        "shared_basis_64bit_transported_l1", "eq4_rotation_64bit_transported_l1",
        "random_rotation_dev_64bit_transported_l1")]
    for checkpoint_set in zip(*(row["checkpoints"] for row in rows)):
        assert len({checkpoint["action"] for checkpoint in checkpoint_set}) == 1
        assert len({checkpoint["goal_satisfied"] for checkpoint in checkpoint_set}) == 1
        errors = [checkpoint["goal_error"] for checkpoint in checkpoint_set
                  if checkpoint["goal_error"] is not None]
        if errors:
            assert max(errors) - min(errors) < 1e-8


def test_work_includes_mapping_and_failed_proposals():
    row = run_tool_trial(PRIMARY_ARMS[0], profile=FactorProfile(.2, 0, 0, 0, 0),
                         seed=28102)
    assert len(row["learning_curve"]) == len(LEARNING_HORIZONS)
    assert 0.0 <= row["learning_auc"] <= 1.0
    for checkpoint in row["checkpoints"]:
        assert checkpoint["native_steps"] > 0
        assert checkpoint["decoder_graph_bytes"] > 0
        assert checkpoint["exact_checks"] == checkpoint["horizon"] + 1 + int(
            checkpoint["receipt_verified"])
        assert checkpoint["query_count"] == 1
        assert checkpoint["frame_mapping_bits"] == 1152.0
        assert checkpoint["metric_policy_bits"] == 64.0
        assert checkpoint["total_representation_bits"] == 1408.0
        assert checkpoint["failed_proposals"] in (0, 1)
        assert checkpoint["heldout_used_for_selection"] is False


def test_transfer_requires_new_target_verification():
    row = run_tool_trial(PRIMARY_ARMS[0], profile=FactorProfile(.8, .1, 0, 0, 0),
                         seed=28103)
    for checkpoint in row["checkpoints"]:
        assert checkpoint["target_changed_from_source"] is True
        assert checkpoint["target_calibration_context"] not in checkpoint["source_contexts"]
        assert checkpoint["score_context"] != checkpoint["target_calibration_context"]
        assert checkpoint["target_calibration_binding"] != "standard-tool"
        assert checkpoint["target_binding"] != checkpoint["target_calibration_binding"]
        assert checkpoint["target_verification_before_score"] is True
        assert checkpoint["target_calibration"]["verified"] is True
        assert checkpoint["target_calibration"]["projection_verified"] is True
        assert checkpoint["evidence_events"] == checkpoint["horizon"] + 1 + int(
            checkpoint["receipt_verified"])


def test_social_repair_family_has_paired_horizons_and_verified_calibration():
    panel = development_panel(seeds=(28105,), frames=PRIMARY_ARMS,
                              families=("social_request_repair",))
    assert len(panel["rows"]) == len(PRIMARY_ARMS)
    paired = [row["checkpoints"] for row in panel["rows"]]
    for left, right in zip(*paired):
        assert left["world_family"] == right["world_family"] == "social_request_repair"
        assert left["horizon"] == right["horizon"]
        assert left["target_calibration_context"] == right["target_calibration_context"]
        assert left["score_context"] == right["score_context"]
        assert left["target_verification_before_score"] is True
        assert left["target_calibration"]["projection_verified"] is True
        assert left["total_representation_bits"] > 0


def test_no_success_conditioned_primary():
    panel = development_panel(seeds=(28111, 28112), frames=PRIMARY_ARMS + CONTROL_ARMS)
    assert panel["primary_arms"] == list(PRIMARY_ARMS)
    assert panel["control_arms"] == list(CONTROL_ARMS)
    assert panel["primary_status"] == "development_only_no_preregistered_inference"
    assert len(panel["rows"]) == 2 * 2 * (len(PRIMARY_ARMS) + len(CONTROL_ARMS))
    assert panel["host_selects_action"] is False
    assert panel["all_failures_retained"] is True
    assert all(len(row["learning_curve"]) == len(LEARNING_HORIZONS)
               for row in panel["rows"])
    assert all(len(row["checkpoints"]) == len(LEARNING_HORIZONS)
               for row in panel["rows"])
    assert {row["world_family"] for row in panel["rows"]} == {
        "tool_intervention", "social_request_repair"}
    assert all("goal_satisfied" in checkpoint
               and "failed_or_abstained_actions" in checkpoint
               for row in panel["rows"] for checkpoint in row["checkpoints"])
