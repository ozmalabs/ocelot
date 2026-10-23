import importlib.util
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest
from evaluation.process_mastery.checkpoint_world_adapter import CheckpointExpression

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p22_development_probe.py"
BINDING = ROOT / "docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_D4_0406_0407.json"
SPEC = importlib.util.spec_from_file_location("p22_development_probe_cli", SCRIPT)
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)
DIGEST = "badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255"


def _command(output: Path, binding: Path, *extra: str) -> list[str]:
    return [sys.executable, str(SCRIPT), "--family", "d4", "--training-draws",
        "406", "407", "--training-goal-relation", "distinct",
        "--validation-start", "0", "--validation-count", "0",
        "--approved-candidate-binding", str(binding), "--approve-digest", DIGEST,
        "--review-seconds", "0.5", "--output", str(output), *extra]


def _temporary_binding(output: Path, binding_path: Path) -> Path:
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    binding["output_path"] = str(output)
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    return binding_path


def test_approval_cli_requires_explicit_execution_flag(tmp_path):
    output = tmp_path / "candidate.json"
    binding = _temporary_binding(output, tmp_path / "binding.json")
    result = subprocess.run(_command(output, binding), cwd=ROOT, capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "--execute-approved-adoption" in result.stderr
    assert not output.exists()


def test_approval_cli_rejects_digest_mismatch_before_probe_or_output(tmp_path):
    output = tmp_path / "candidate.json"
    binding = _temporary_binding(output, tmp_path / "binding.json")
    command = _command(output, binding, "--execute-approved-adoption")
    command[command.index("--approve-digest") + 1] = "0" * 64
    result = subprocess.run(command, cwd=ROOT, capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "approved digest/family does not match" in result.stderr
    assert not output.exists()


def test_approval_cli_rejects_superseded_request_before_claiming_output(tmp_path):
    output = tmp_path / "candidate.json"
    binding_path = _temporary_binding(output, tmp_path / "binding.json")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["status"] = "superseded"
    binding_path.write_text(json.dumps(binding), encoding="utf-8")

    result = subprocess.run(_command(output, binding_path,
        "--execute-approved-adoption"), cwd=ROOT, capture_output=True,
        text=True, check=False)

    assert result.returncode != 0
    assert "candidate binding document does not match" in result.stderr
    assert not output.exists()


def test_approval_cli_rejects_claimed_output_path_without_overwriting(tmp_path):
    output = tmp_path / "candidate.json"
    output.write_text("consumed-result\n", encoding="utf-8")
    binding = _temporary_binding(output, tmp_path / "binding.json")

    result = subprocess.run(_command(output, binding,
        "--execute-approved-adoption"), cwd=ROOT, capture_output=True,
        text=True, check=False)

    assert result.returncode != 0
    assert "requires a new --output path" in result.stderr
    assert output.read_text(encoding="utf-8") == "consumed-result\n"


def test_parent_checkpoint_binding_hash_is_checked_before_one_shot_claim(tmp_path):
    output = tmp_path / "candidate.json"
    binding_path = _temporary_binding(output, tmp_path / "binding.json")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["parent_checkpoint"] = {
        "artifact_path": "missing-parent.json",
        "artifact_sha256": "0" * 64,
        "record_path": ["simulated_adoption", "generation_one_checkpoint"],
        "checkpoint_digest": "1" * 64,
    }
    binding["approval_binding"]["parent_checkpoint_digest"] = "1" * 64
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    command = _command(output, binding_path, "--execute-approved-adoption")
    result = subprocess.run(command, cwd=ROOT, capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "invalid parent checkpoint binding" in result.stderr
    assert not output.exists()


def test_approval_cli_rejects_candidate_transfer_depth_mismatch(tmp_path):
    output = tmp_path / "candidate.json"
    binding_path = _temporary_binding(output, tmp_path / "binding.json")
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    binding["candidate_transfer_depth"] = 3
    binding["approval_binding"]["candidate_transfer_depth"] = 3
    binding_path.write_text(json.dumps(binding), encoding="utf-8")
    command = _command(output, binding_path,
        "--candidate-transfer-depth", "2", "--execute-approved-adoption")
    result = subprocess.run(command, cwd=ROOT, capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "candidate_transfer_depth differs" in result.stderr
    assert not output.exists()


def test_parent_checkpoint_binding_resolves_exact_record_and_digest(tmp_path,
                                                                    monkeypatch):
    monkeypatch.setattr(CLI, "ROOT", tmp_path)
    checkpoint = CheckpointExpression("parent-g1", "root-digest", "expr-digest",
        (0, 1, 2, 3), 0, generation=1, checkpoint_digest="parent-digest",
        approval_id="approval", receipt_id="receipt", cumulative_primitive_work=0,
        resource_snapshot_json="{}", native_graph_snapshot_json="{}")
    source = {"simulated_adoption": {
        "generation_one_checkpoint": asdict(checkpoint)}}
    raw = json.dumps(source, sort_keys=True).encode()
    (tmp_path / "parent.json").write_bytes(raw)
    spec = {"parent_checkpoint": {
        "artifact_path": "parent.json",
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "record_path": ["simulated_adoption", "generation_one_checkpoint"],
        "checkpoint_digest": "parent-digest"}}
    monkeypatch.setattr(CLI.CheckpointWorldAdapter,
        "_checkpoint_digest_valid", staticmethod(lambda value: value is not None))
    loaded = CLI._parent_checkpoint_from_binding(spec)
    assert loaded.checkpoint_id == "parent-g1"
    assert loaded.generation == 1
    assert loaded.params == (0, 1, 2, 3)

    spec["parent_checkpoint"]["checkpoint_digest"] = "other-digest"
    with pytest.raises(ValueError, match="parent checkpoint digest"):
        CLI._parent_checkpoint_from_binding(spec)


def test_training_continuation_parent_is_bound_to_artifact_and_record(tmp_path,
                                                                      monkeypatch):
    monkeypatch.setattr(CLI, "ROOT", tmp_path)
    checkpoint = CheckpointExpression("parent-g2", "root-digest", "expr-digest",
        (0, 1, 2, 3), 0, generation=2, checkpoint_digest="parent-digest",
        approval_id="approval", receipt_id="receipt", cumulative_primitive_work=10,
        resource_snapshot_json="{}", native_graph_snapshot_json="{}")
    artifact = tmp_path / "continuation.json"
    artifact.write_text(json.dumps({"parent_checkpoint": asdict(checkpoint)}),
                        encoding="utf-8")
    monkeypatch.setattr(CLI.CheckpointWorldAdapter,
        "_checkpoint_digest_valid", staticmethod(lambda value: value is not None))

    loaded, binding = CLI._continuation_parent_from_artifact(
        artifact, ["parent_checkpoint"], "parent-digest")

    assert loaded.checkpoint_id == "parent-g2"
    assert loaded.generation == 2
    assert binding["artifact_path"] == "continuation.json"
    assert binding["record_path"] == ["parent_checkpoint"]
    assert binding["checkpoint_digest"] == "parent-digest"

    with pytest.raises(ValueError, match="parent checkpoint digest"):
        CLI._continuation_parent_from_artifact(
            artifact, ["parent_checkpoint"], "wrong-digest")


def test_approved_adoption_attempt_output_is_durable_one_shot_claim(tmp_path):
    output = tmp_path / "attempt.json"
    CLI._claim_approval_output(output, approved_digest=DIGEST,
        review_seconds=0.5, binding_document_sha256="a" * 64)
    before = output.read_bytes()
    assert json.loads(before)["status"] == "attempt_started"
    with pytest.raises(FileExistsError):
        CLI._claim_approval_output(output, approved_digest=DIGEST,
            review_seconds=0.5, binding_document_sha256="a" * 64)
    assert output.read_bytes() == before


def test_registered_full_root_request_binds_measured_replay_and_novel_child():
    request_path = ROOT / (
        "docs/research/engine_substrate/"
        "COGNITION_P22_APPROVAL_REQUEST_D4_FULL_0985_0986.json")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["status"] == "awaiting_exact_user_approval"
    assert request["training_draws"] == [985, 986, 987, 988]
    assert request["validation_draws"] == []
    assert request["candidate_transfer_depth"] == 3
    assert not (ROOT / request["output_path"]).exists()

    parent = CLI._parent_checkpoint_from_binding(request)
    binding = request["approval_binding"]
    assert parent.checkpoint_id == "p22-d4-full-g0"
    assert parent.checkpoint_digest == binding["parent_checkpoint_digest"]
    graph = json.loads(parent.native_graph_snapshot_json)
    active_effects = set()
    for node in graph["nodes"]:
        attrs = node.get("attrs", {})
        if (node.get("type") == "ProcessSchema"
                and attrs.get("status") == "active"
                and attrs.get("provenance") == "world_affordance"):
            params = attrs.get("params", [])
            if isinstance(params, dict):
                params = params["__list__"]
            active_effects.add(tuple(params))
    assert active_effects == {(1, 3, 0, 2), (2, 3, 0, 1)}
    assert binding["expression_digest"] == (
        "15ab127dc160101ea078c7eea5b91b5339bc4ca6a73a20048c5facb27656b651")
    assert binding["qualification_id"] == "#12259"
    assert binding["training_trial_keys"] == [
        "p22:d4-v2:train:0985", "p22:d4-v2:train:0986"]

    artifacts = {}
    for prefix in ("source", "replay"):
        artifact_path = ROOT / request[f"{prefix}_artifact_path"]
        raw = artifact_path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == request[
            f"{prefix}_artifact_sha256"]
        artifacts[prefix] = json.loads(raw)
    assert artifacts["replay"]["native_rule_work"][
        "rule_identity_coverage"] == "COMPLETE"
    for artifact in artifacts.values():
        candidate = next(row for row in artifact["candidates"]
            if row["expression_digest"] == binding["expression_digest"])
        qualification = next(row for row in candidate["qualifications"]
            if row["qualification_id"] == binding["qualification_id"])
        assert qualification["training_trial_keys"] == binding[
            "training_trial_keys"]
        child_trial = next(row for row in candidate["independent_goal_trials"]
            if row["attempt_id"] == qualification["attempt_ids"][1])
        child = next(row for row in artifact["candidates"]
            if row["candidate_id"] == child_trial["derived_candidate_ids"][0])
        assert tuple(child["approval_binding"]["params"]) not in active_effects
        assert tuple(candidate["approval_binding"]["params"]) not in active_effects
        assert artifact["approval_count"] == 0
        assert artifact["world_receipt_count"] == 0
        assert artifact["validation_world_ids"] == []


@pytest.mark.parametrize("request_name", [
    "COGNITION_P22_APPROVAL_REQUEST_D4_0962_0972.json",
    "COGNITION_P22_APPROVAL_REQUEST_LOOPOVER_0951_0954.json",
    "COGNITION_P22_APPROVAL_REQUEST_D4_FULL_0985_0986.json",
])
def test_current_registered_root_approval_packets_are_bound_and_unclaimed(
        request_name):
    request_path = ROOT / "docs/research/engine_substrate" / request_name
    request = json.loads(request_path.read_text(encoding="utf-8"))
    binding = request["approval_binding"]

    assert request["status"] == "awaiting_exact_user_approval"
    assert request["training_goal_relation"] == "distinct"
    assert request["validation_draws"] == []
    assert not (ROOT / request["output_path"]).exists()
    parent = CLI._parent_checkpoint_from_binding(request)
    assert parent.generation == 0
    assert parent.checkpoint_digest == binding["parent_checkpoint_digest"]
    assert binding["status"] == "unapproved_candidate"
    assert binding["expression_digest"]
    assert binding["qualification_id"]
    assert len(set(binding["training_trial_keys"])) == 2

    for prefix in ("source", "replay"):
        raw = (ROOT / request[f"{prefix}_artifact_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == request[
            f"{prefix}_artifact_sha256"]
        artifact = json.loads(raw)
        assert artifact["status"] == "COMPLETED"
        assert artifact["approval_count"] == 0
        assert artifact["world_receipt_count"] == 0
        assert artifact["validation_world_ids"] == []
        candidate = next(row for row in artifact["candidates"]
            if row["expression_digest"] == binding["expression_digest"])
        qualification = next(row for row in candidate["qualifications"]
            if row["qualification_id"] == binding["qualification_id"])
        assert qualification["training_trial_keys"] == binding[
            "training_trial_keys"]
