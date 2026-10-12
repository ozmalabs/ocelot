"""End-to-end acceptance assertions for the supplemental memory/learning probe."""
from evaluation.phase8_memory_learning_probe import run_probe


def test_multi_topic_learning_and_interference_recall_have_graph_receipts():
    report = run_probe()

    assert report["status"] == "measured"
    assert report["controls"] == {
        "prelearning_answers_absent": True,
        "teacher_payloads_match": True,
        "typed_grounding_evidence_present": True,
        "distinct_held_answers": True,
    }
    assert report["scores"]["learning"] == {
        "successes": 5, "n": 5, "mean": 1.0,
    }
    assert report["scores"]["memory"] == {
        "successes": 5, "n": 5, "mean": 1.0,
    }

    assert len(report["cases"]) == 5
    held_ids = set()
    for case in report["cases"].values():
        first = case["first_answer"]
        repeated = case["delayed_repeat"]
        assert first["answer_commitment_kind"] == \
            "supported_event_bound_topic_answer"
        assert repeated["answer_commitment_kind"] == \
            "supported_event_bound_topic_answer"
        assert first["receipt_id"] != repeated["receipt_id"]
        assert first["held_answer_id"] == repeated["held_answer_id"]
        assert first["grounding_evidence_id"] == \
            repeated["grounding_evidence_id"]
        held_ids.add(first["held_answer_id"])
    assert len(held_ids) == 5
    assert len(report["intervening_turns"]) == 2
