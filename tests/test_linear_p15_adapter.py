"""Development-only integration checks for the frozen P15 native adapter."""
from __future__ import annotations

import pytest
pytest.importorskip("substrate_rs")

from evaluation.process_mastery.linear_p15_v1 import run
from evaluation.process_mastery.analyze_linear_p15_v1 import analyze, _integrity_controls


def test_self_check_runs_three_approved_generations():
    payload = run(n=2, self_check=True)
    result = analyze(payload)
    assert result["integrity_status"] == "PASS"
    assert result["paired_tasks"] == 6
    assert result["paired_bootstrap_cost_latency"]["resamples"] == 10_000
    assert (result["trend"].get("estimable") is True or
            isinstance(result["trend"].get("reason"), str))
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
    assert third["candidate_status"] == "promoted"
    assert third["generation_status"] == "active"
    assert third["approval_event"] == {"status": "approved",
        "candidate_name": "commutator_fourth_v3", "criteria_digest": "pmb-v1-frozen-criteria"}
    assert payload["metadata"]["completed_generations"] == [1, 2, 3]


def test_analyzer_fails_on_unmatched_worlds():
    payload = run(n=2, self_check=True)
    payload["records"][-1]["world_sha256"] = "tampered"
    result = analyze(payload)
    assert result["integrity_status"] == "FAIL"
    assert result["integrity_failures"]["world"] > 0


def test_heldout_is_fixed_at_200_and_development_is_disjoint():
    with pytest.raises(ValueError, match="200-task"):
        run(n=2, split="heldout")
    payload = run(n=2, self_check=True)
    assert payload["metadata"]["task_control_block"] == 1
    controls = _integrity_controls(payload)
    assert controls["n"] == controls["passed"] == 100
    assert controls["failed"] == 0
