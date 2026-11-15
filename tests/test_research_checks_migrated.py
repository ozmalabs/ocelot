"""Mechanical research workflow gates; passing does not certify truth."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts.ocelot_research_checks import (  # noqa: E402
    check_finite_math,
    check_research_workflow,
)


def _protocol(**overrides):
    value = {
        "hypothesis": "A predicts greater readout than B, or the reverse.",
        "two_sided": True,
        "readout": "mean score by independent run",
        "sample_size_justification": "power calculation, n=40",
        "independent_unit": "seed/run",
        "seed_allocation": "fresh claimed range 900-939",
        "controls": ["positive", "negative"],
        "decision_rule": "compare predeclared interval to zero",
        "fixed_analysis": "analysis-v1",
        "revision": "git:abc123:path/to/prereg@def456",
        "immutable": True,
        "recorded_at": "2026-01-01T12:00:00Z",
    }
    value.update(overrides)
    return value


def test_exploratory_needs_no_prereg_and_is_never_confirmatory():
    result = check_research_workflow({"mode": "exploratory"})
    assert result["label"] == "exploratory"
    assert not result["confirmatory_eligible"]
    assert not result["blockers"]
    assert "exploratory" in result["notices"][0]


def test_confirmatory_requires_complete_immutable_pre_run_protocol_and_receipt():
    run = {
        "protocol_revision": "git:abc123:path/to/prereg@def456",
        "started_at": "2026-01-02T12:00:00Z",
        "receipt_status": "captured",
        "exit_status": 0,
        "controls": {"positive": "passed", "negative": "passed"},
        "engine_status": "current",
    }
    result = check_research_workflow({"mode": "confirmatory"}, _protocol(), run)
    assert result["confirmatory_eligible"]
    assert result["blockers"] == []


def test_post_run_prereg_wrong_revision_and_stale_engine_block_confirmatory_label():
    protocol = _protocol(recorded_at="2026-01-03T12:00:00Z")
    run = {
        "protocol_revision": "other-revision",
        "started_at": "2026-01-02T12:00:00Z",
        "receipt_status": "captured",
        "exit_status": 0,
        "engine_status": "stale",
        "controls": {},
    }
    result = check_research_workflow({"mode": "confirmatory"}, protocol, run)
    assert not result["confirmatory_eligible"]
    assert any("not recorded before" in item for item in result["blockers"])
    assert any("revision" in item for item in result["blockers"])
    assert any("engine provenance" in item for item in result["blockers"])


def test_missing_protocol_control_and_unverified_manual_receipt_are_visible():
    protocol = _protocol(controls=None)
    run = {
        "protocol_revision": protocol["revision"],
        "started_at": "2026-01-02T12:00:00Z",
        "receipt_status": "manual",
        "controls": None,
        "exit_status": 2,
    }
    result = check_research_workflow({"mode": "confirmatory"}, protocol, run)
    assert any("missing controls" in item for item in result["blockers"])
    assert any("control outcomes" in item for item in result["blockers"])
    assert any("receipt is unavailable" in item for item in result["blockers"])
    assert any("manually asserted" in item for item in result["notices"])
    assert any("failed with exit status 2" in item for item in result["notices"])


def test_deductive_and_qualitative_exemptions_require_reason_not_rng_fields():
    missing = check_research_workflow({"mode": "deductive"})
    assert any("exemption reason" in item for item in missing["blockers"])
    valid = check_research_workflow({
        "mode": "qualitative", "empirical_exemption_reason": "interpretive source analysis"
    })
    assert valid["blockers"] == []
    assert "RNG/power exemption" in valid["notices"][0]


def test_finite_math_requires_domain_bounds_and_oracle_accounting_and_never_calls_it_proof():
    incomplete = check_finite_math(
        domain=None, bounds=None, oracle_independent=None,
        verification_label="finite_verification",
    )
    assert not incomplete["complete"]
    assert len(incomplete["blockers"]) == 3

    finite = check_finite_math(
        domain="Boolean assignments", bounds={"variables": 8},
        oracle_independent=True, oracle_description="separate brute-force evaluator",
        verification_label="finite_verification",
    )
    assert finite["complete"]
    assert any("not a universal proof" in item for item in finite["notices"])


def test_failed_finite_run_can_report_nonindependent_oracle_as_limitation():
    result = check_finite_math(
        domain="all 2-bit inputs", bounds="exactly four inputs",
        oracle_independent=False, verification_label="finite_verification",
    )
    assert result["complete"]
    assert any("not independent" in item for item in result["notices"])


def test_timezone_free_prereg_timestamp_compares_safely_and_proof_is_not_verified():
    result = check_research_workflow(
        {"mode": "confirmatory"},
        _protocol(recorded_at="2026-01-01T12:00:00"),
        {"protocol_revision": "git:abc123:path/to/prereg@def456",
         "started_at": "2026-01-02T12:00:00Z", "receipt_status": "captured",
         "exit_status": 0, "controls": {"positive": "passed"}},
    )
    assert result["confirmatory_eligible"]

    proof = check_finite_math(
        domain="all natural numbers", bounds="unbounded",
        oracle_independent=True, oracle_description="not applicable to a proof",
        verification_label="proof",
    )
    assert proof["complete"]
    assert any("does not verify proofs" in item for item in proof["notices"])
