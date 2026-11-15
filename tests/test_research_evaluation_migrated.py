import unittest
from pathlib import Path

from evaluation.research_assistant.harness import (
    ARMS,
    EvaluationError,
    load_fixtures,
    summarize,
    validate_fixtures,
)


ROOT = Path(__file__).resolve().parents[1]


def score_data(fixtures):
    runs = []
    for task in fixtures["tasks"]:
        for arm in ARMS:
            runs.append({
                "task_id": task["task_id"], "arm": arm,
                "status": "completed", "grader_id": "grader-A",
                "blind_label": f"blind-{len(runs)}",
                "scores": {
                    "source_claim_accuracy": 2,
                    "unsupported_assertions": 2,
                    "contradiction_recall": 2,
                    "limitation_recall": 2,
                    "citation_reopenability": 2,
                    "citation_hash_match": 2,
                    "completion": 2,
                },
                "tokens": 100, "latency_ms": 1000, "tool_cost": 0,
            })
    return {"fixture_set_id": fixtures["fixture_set_id"],
            "preregistration_id": "pilot-prereg-001", "grading_blinded": True,
            "runs": runs}


class ResearchEvaluationTests(unittest.TestCase):
    def test_fixture_contract_and_source_hashes(self):
        fixtures = load_fixtures()
        result = validate_fixtures(fixtures, ROOT, ROOT.parent / "graphic-equalisation")
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["task_count"], 5)
        self.assertEqual(fixtures["status"], "pilot_only_burned_not_held_out")

    def test_summarize_keeps_arm_denominators_and_no_inference(self):
        fixtures = load_fixtures()
        result = summarize(score_data(fixtures), fixtures)
        self.assertEqual(result["expected_runs"], 15)
        self.assertEqual(result["complete_paired_task_count"], 5)
        self.assertEqual(result["arms"]["research_helper"]["task_denominator"], 5)
        self.assertEqual(result["arms"]["research_helper"]["completed"], 5)
        self.assertEqual(result["arms"]["research_helper"]["mean_scores_0_to_2"]["completion"], 2)
        self.assertIn("No benefit claim", result["inference_note"])

    def test_failed_runs_remain_in_denominator(self):
        fixtures = load_fixtures()
        data = score_data(fixtures)
        row = next(r for r in data["runs"] if r["arm"] == "generic_ledger")
        row["status"] = "failed"
        row["failure_reason"] = "fixture source retrieval failure"
        row.pop("scores")
        result = summarize(data, fixtures)
        arm = result["arms"]["generic_ledger"]
        self.assertEqual(arm["task_denominator"], 5)
        self.assertEqual(arm["completed"], 4)
        self.assertEqual(arm["missing_or_failed"], 1)

    def test_rejects_unblinded_or_unpreregistered_scores(self):
        fixtures = load_fixtures()
        data = score_data(fixtures)
        data["grading_blinded"] = False
        with self.assertRaises(EvaluationError):
            summarize(data, fixtures)

    def test_rejects_missing_key_dimension(self):
        fixtures = load_fixtures()
        data = score_data(fixtures)
        del data["runs"][0]["scores"]["limitation_recall"]
        with self.assertRaises(EvaluationError):
            summarize(data, fixtures)


if __name__ == "__main__":
    unittest.main()
