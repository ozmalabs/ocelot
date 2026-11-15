import pytest

from evaluation.research_assistant.harness import EvaluationError
from evaluation.research_assistant.heldout_runner import (
    attach_outputs, freeze_assignments, prepare_packets, score_blind_sheets,
)


TASKS = [
    {"task_id": "T1", "prompt": "Question one", "source_access": ["S1"]},
    {"task_id": "T2", "prompt": "Question two"},
]


def test_frozen_packets_are_reproducible_and_blind():
    frozen = freeze_assignments(TASKS, seed=27)
    assert frozen == freeze_assignments(TASKS, seed=27)
    packets = prepare_packets(TASKS, frozen)
    assert len(packets["prompts"]) == 6
    assert all("arm" not in row for row in packets["prompts"])
    assert all("answer_key" not in row for row in packets["prompts"])
    assert len({r["blind_label"] for r in packets["prompts"]}) == 6
    assert "arm" not in str(packets["blind_sheets"])


def test_output_hash_and_unknown_operations_stay_null():
    packets = prepare_packets(TASKS, freeze_assignments(TASKS, seed=3))
    label = packets["prompts"][0]["blind_label"]
    record = attach_outputs(packets, {label: {"answer": "Answer"}})
    row = next(r for r in record["blind_sheets"] if r["blind_label"] == label)
    assert row["output_sha256"]
    assert row["tokens"] is row["latency_ms"] is row["tool_cost"] is None


def test_blind_scores_join_to_key_only_after_scoring():
    frozen = freeze_assignments(TASKS, seed=9)
    packets = prepare_packets(TASKS, frozen)
    outputs = {r["blind_label"]: {"answer": "ok", "latency_ms": 12}
               for r in packets["prompts"]}
    record = attach_outputs(packets, outputs)
    for sheet in record["blind_sheets"]:
        sheet["scores"] = {k: 2 for k in sheet["scores"]}
        sheet["rationales"] = {k: "supported" for k in sheet["scores"]}
    joined = score_blind_sheets(record, frozen["assignments"], grader_id="G1")
    assert len(joined["runs"]) == 6
    assert all(r["arm"] in {"source_only", "generic_ledger", "research_helper"}
               for r in joined["runs"])
    assert all(r["latency_ms"] == 12 and r["tokens"] is None for r in joined["runs"])


def test_tampered_key_output_and_invalid_scores_fail_closed():
    frozen = freeze_assignments(TASKS, seed=11)
    packets = prepare_packets(TASKS, frozen)
    with pytest.raises(EvaluationError, match="digest"):
        prepare_packets(TASKS, {**frozen, "assignments": []})
    label = packets["prompts"][0]["blind_label"]
    with pytest.raises(EvaluationError, match="nonnegative"):
        attach_outputs(packets, {label: {"answer": "x", "tokens": -1}})
    record = attach_outputs(packets, {label: {"answer": "x"}})
    record["blind_sheets"][0]["scores"]["completion"] = 3
    with pytest.raises(EvaluationError, match="score"):
        score_blind_sheets(record, frozen["assignments"], grader_id="G")
