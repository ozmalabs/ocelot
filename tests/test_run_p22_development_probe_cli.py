import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_p22_development_probe.py"
BINDING = ROOT / "docs/research/engine_substrate/COGNITION_P22_APPROVAL_REQUEST_D4_0406_0407.json"
DIGEST = "badd1251ee4eb9c779233a3631b307d68ec6e34da40daeb993f8c0be0641d255"


def _command(output: Path, *extra: str) -> list[str]:
    return [sys.executable, str(SCRIPT), "--family", "d4", "--training-draws",
        "406", "407", "--training-goal-relation", "distinct",
        "--validation-start", "0", "--validation-count", "0",
        "--approved-candidate-binding", str(BINDING), "--approve-digest", DIGEST,
        "--review-seconds", "0.5", "--output", str(output), *extra]


def test_approval_cli_requires_explicit_execution_flag():
    output = ROOT / "evaluation/process_mastery/results/p22_approved_candidate_d4_0406_0407.json"
    result = subprocess.run(_command(output), cwd=ROOT, capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "--execute-approved-adoption" in result.stderr
    assert not output.exists()


def test_approval_cli_rejects_digest_mismatch_before_probe_or_output():
    output = ROOT / "evaluation/process_mastery/results/p22_approved_candidate_d4_0406_0407.json"
    command = _command(output, "--execute-approved-adoption")
    command[command.index("--approve-digest") + 1] = "0" * 64
    result = subprocess.run(command, cwd=ROOT, capture_output=True,
                            text=True, check=False)
    assert result.returncode != 0
    assert "approved digest/family does not match" in result.stderr
    assert not output.exists()
