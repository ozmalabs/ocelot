import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

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
