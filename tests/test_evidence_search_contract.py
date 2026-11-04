from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "docs/research/engine_substrate/"
            "COGNITION_EVIDENCE_SEARCH_CONTRACT.md")


def test_contract_selects_only_p23_measured_remedies():
    text = CONTRACT.read_text()
    assert "exact native effect digest" in text
    assert "10,000 ordinary discovery attempts" in text
    assert "5,000 independent-goal qualification attempts" in text
    assert "Keep the existing global search ceiling at 120,000 attempts." in text
    assert "explicit CLI flag" in text
    assert "defaults off" in text


def test_all_selectors_receive_the_same_task_pool_and_budget():
    text = CONTRACT.read_text()
    assert "same finite, learner-accessible training opportunity pool" in text
    assert "same tasks, initial held processes, work ceiling" in text
    assert "random selector" in text and "fixed selector" in text


def test_exact_effect_identity_is_context_bound_and_preserves_attempts():
    text = CONTRACT.read_text()
    assert "same domain and probe context" in text
    assert "Keep partial, stochastic, unknown, and non-comparable effects distinct." in text
    assert "Preserve syntax attempts and their provenance" in text
    assert "Identity, active, adopted, and duplicate effects" in text


def test_contract_carries_forward_p25_transfer_floor():
    text = CONTRACT.read_text()
    assert "all arms scored zero on its unseen ButtonWidget transfer task" in text
    assert "A zero loss between floor-level arms is not positive transfer evidence." in text


def test_no_gain_and_failure_denominators_remain_reportable():
    text = CONTRACT.read_text()
    assert "A structurally valid null or negative result remains reportable." in text
    assert "missing, pending, failed, floor, and ceiling outcomes without exclusion" in text
    assert "without changed learned state and subsequent behavior fails" in text
