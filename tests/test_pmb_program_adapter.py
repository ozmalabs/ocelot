from __future__ import annotations

import json

from evaluation.process_mastery import harness, program_adapter as adapter
from scripts import mbpp_zero_shot_baseline as mbpp


def test_existing_synthesis_outcome_preserved():
    # Task 14 is a frozen accepted candidate with a held-out disagreement.
    frozen = json.loads(open(mbpp.OUT_PATH, encoding="utf-8").read())
    expected = next(r for r in frozen["runnable_rows"] if r["task_id"] == 14)
    bundle = adapter.load_task(14)
    harness_result = adapter.run_task(14, track_i=False)
    assert harness_result["solver_status"] == expected["status"]
    assert harness_result["external_outcome"]["all_ok"] is False
    assert harness_result["candidate_program"]
    assert bundle["task"]["prompt"] == expected["prompt"]
    legacy_task = next(t for t in mbpp.split_tasks(
        json.loads(open(mbpp.FIXTURE_PATH, encoding="utf-8").read()))["test"]
                       if t["task_id"] == 14)
    spec, report = mbpp.build_task_rows(legacy_task)
    legacy = mbpp.run_task(legacy_task, spec, report)
    assert legacy["status"] == harness_result["solver_status"]
    assert legacy["outcome"] == "accepted_holdout_fail"


def test_hidden_tests_not_agent_input():
    bundle = adapter.load_task(14)
    assert "code" not in bundle["task"]
    assert "test_list" not in bundle["task"]
    assert "held_out_rows" not in bundle["task"]
    assert bundle["scorer"]["held_out_rows"]
    # Running performs an additional graph audit after synthesis.
    result = adapter.run_task(14, track_i=False)
    assert result["evidence_boundary"].startswith("held-out rows remain")
    assert result["heldout_rows_scored"] == len(bundle["scorer"]["held_out_rows"])


def test_program_arm_not_dummy_baseline():
    baseline = harness.Agent(track_i=False)
    treatment = harness.Agent(track_i=True)
    baseline.register_program_adapter()
    treatment.register_program_adapter()
    assert "program" in baseline.adapters and "program" in treatment.adapters
    b = baseline.request_action(None, {"task_id": 14}, adapter="program")
    t = treatment.request_action(None, {"task_id": 14}, adapter="program")
    assert b["status"] in {"COMPLETED", "FAILED", "UNSUPPORTED"}
    assert t["status"] in {"COMPLETED", "FAILED", "UNSUPPORTED"}
    assert b["profile"] == "baseline" and t["profile"] == "track-i"
    assert b["dataset"]["fixture_sha256"] == t["dataset"]["fixture_sha256"]
    assert b["compute"]["attempts"] is not None or b["status"] == "UNSUPPORTED"


def test_dataset_split_provenance_recorded():
    p = adapter.dataset_provenance()
    assert p["n_tasks"] == 427
    assert p["split"] == "test task_id 11..510 (vendored subset)"
    assert len(p["fixture_sha256"]) == 64
    assert p["contamination_rule"]
