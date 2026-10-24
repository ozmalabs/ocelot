from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/research/engine_substrate"


def _read(name):
    return (DOCS / name).read_text()


def test_no_adoption_interval_is_evaluable():
    contract = _read("COGNITION_CUMULATIVE_LEARNING_CONTRACT.md")
    assert "no state changed" in contract
    assert "If search failed, no candidate qualified, or authorization is pending, capture that interval" in contract
    assert "Readiness is triggered by either fixed charged-work or task-access markers" in contract
    assert "never by candidate quality, approval, adoption, or a score" in contract


def test_checkpoints_not_success_selected():
    contract = _read("COGNITION_CUMULATIVE_LEARNING_CONTRACT.md")
    assert "scheduled indices are `g0`, `g1`, `g2`, `g3`" in contract
    assert "never by candidate quality, approval, adoption, or a score" in contract
    assert "all-failure, all-success, missing, invalid, no-change, failed-search and authorization-pending" in contract


def test_pending_approval_not_implicit_permission():
    contract = _read("COGNITION_CUMULATIVE_LEARNING_CONTRACT.md")
    assert "An authorization-pending candidate remains pending" in contract
    assert "never executed, adopted, converted into a receipt" in contract
    assert "Scheduled capture and evaluation confer no action authority" in contract


def test_p22_history_not_reinterpreted():
    p22 = _read("COGNITION_LINEAR_P22_PREREG.md")
    p27 = _read("COGNITION_CUMULATIVE_LEARNING_CONTRACT.md")
    assert "DRAFT — NOT FROZEN" in p22
    assert "No old P22 allocation or outcome is re-entered, rescored" in p27
    assert "P27 is therefore a **separately versioned scheduled-checkpoint successor**" in p27


def test_flat_score_zero_improvement_and_fixed_gate():
    pmb = _read("PMB_V1_SPEC.md")
    contract = _read("COGNITION_CUMULATIVE_LEARNING_CONTRACT.md")
    assert "Ceiling, floor and flat outcomes have exact zero effect" in pmb
    assert "primary final gain at least 0.10 and at least 0.05/checkpoint slope" in contract
    assert "No alternate metric may be selected after results" in contract
