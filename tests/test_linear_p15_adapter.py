"""Development-only integration checks for the frozen P15 native adapter."""
from __future__ import annotations

import pytest
pytest.importorskip("substrate_rs")

from evaluation.process_mastery.linear_p15_v1 import run
from evaluation.process_mastery.analyze_linear_p15_v1 import analyze


def test_self_check_runs_real_matched_outcomes_and_leaves_next_gate_pending():
    payload = run(n=2, self_check=True)
    result = analyze(payload)
    assert result["integrity_status"] == "PASS"
    assert result["paired_tasks"] == 4
    assert payload["metadata"]["candidate_development"]["candidate_status"] == "promoted"
    successor = payload["metadata"]["successor_development"]
    assert successor["candidate_name"] == "commutator_cube_v2"
    assert successor["approval_event"] == {"status": "approved",
        "candidate_name": "commutator_cube_v2", "criteria_digest": "pmb-v1-frozen-criteria"}
    assert successor["generation_status"] == "active"
    assert successor["candidate_yield"] > successor["parent_yield"]
    assert payload["metadata"]["candidate_selection_draws"] == {
        "generation_1": [800, 801], "generation_2": [800, 801],
        "generation_3": [800, 801]}
    third = payload["metadata"]["third_generation_development"]
    assert third["candidate_status"] == "awaiting_human"
    assert third["approval_required"] is True


def test_analyzer_fails_on_unmatched_worlds():
    payload = run(n=2, self_check=True)
    payload["records"][-1]["world_sha256"] = "tampered"
    result = analyze(payload)
    assert result["integrity_status"] == "FAIL"
    assert result["integrity_failures"]["world"] > 0
