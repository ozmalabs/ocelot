"""P14.01 contract guards. These tests pin the frozen boundary before P14.02 implementation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/research/engine_substrate/COGNITION_PROOF_OPERATOR_CONTRACT.md"


def _contract():
    return CONTRACT.read_text()


def test_empirical_invariant_not_theorem():
    text = _contract()
    empirical = text.split("An **empirical invariant**", 1)[1].split("A **conjecture**", 1)[0]
    assert "not a theorem" in empirical
    assert "cannot satisfy a proof obligation" in empirical


def test_proof_assumptions_bound():
    text = _contract()
    assert "assumption digest" in text
    assert "family/model digest" in text
    assert "Any change to a bound input invalidates the proof reference" in text
    assert "missing assumptions" in text


def test_operator_cannot_edit_verifier():
    text = _contract()
    boundaries = text.split("An authored invention operator", 1)[1].split("Candidate selection", 1)[0]
    for protected in ("verifier", "checker", "evaluation harness", "held-out allocation", "criteria"):
        assert protected in boundaries


def test_human_gate_not_bypassed():
    text = _contract()
    assert "requires the existing human approval gate" in text
    assert "policies remain disabled by default" in text
    assert "held-out results remain untouched" in text
