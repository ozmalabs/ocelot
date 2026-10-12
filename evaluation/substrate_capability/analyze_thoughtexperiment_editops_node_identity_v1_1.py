#!/usr/bin/env python3
"""Independent integrity and outcome analysis for node-identity hypotheses."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_editops_node_identity_v1_1_lock_20261003.json"
ORDERS = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_orders_20261003.json"
SCORES = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_scores_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_v1_1_analysis_20261003.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    lock = json.loads(LOCK.read_text())
    orders = json.loads(ORDERS.read_text())
    scores = json.loads(SCORES.read_text())
    order_rows, score_rows = orders["workers"], scores["workers"]
    expected_ids = {0, 1, 2, 3}
    by_score = {row["worker"]: row for row in score_rows}
    checks = {
        "capture_lock_binding": orders["lock_sha256"] == sha(LOCK)
        and scores["lock_sha256"] == sha(LOCK)
        and scores["orders_sha256"] == sha(ORDERS),
        "four_workers_each_stage": len(order_rows) == 4 and set(by_score) == expected_ids
        and {row["worker"] for row in order_rows} == expected_ids,
        "stable_sources_each_stage": all(row["source_stable"]
            and row["source_before"] == row["source_after"] == lock["sources"]
            for row in order_rows + score_rows),
        "eight_unique_candidates_per_worker": all(len(row["descriptors"]) == 8
            and len({d["proposal_id"] for d in row["descriptors"]}) == 8
            and len(row["candidate_rules"]) == 8 for row in order_rows),
        "permutation_and_candidate_score_binding": all(
            len(row["candidate_order"]) == 8
            and set(row["candidate_order"]) == set(range(8))
            and [d["proposal_id"] for d in row["descriptors"]]
                == ["sha256:" + hashlib.sha256(json.dumps(rule, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest()
                    for rule in row["candidate_rules"]]
            and [d["proposal_id"] for d in row["descriptors"]]
                == [d["proposal_id"] for d in by_score[row["worker"]]["heldout"]]
            for row in order_rows),
        "all_site_scopes_in_pool": all(
            any(d["site"].get("scope") == "edge" for d in row["descriptors"])
            and {tuple(d["site"].get("identity_keys") or ()) for d in row["descriptors"]
                 if d["site"].get("scope") == "node_attrs"}
                == {("actor",), ("object",), ("verb",), ("actor", "object"),
                    ("actor", "verb"), ("object", "verb"), ("actor", "object", "verb")}
            for row in order_rows),
        "unique_training_winner_selected": all(
            sum(bool(x["correct"]) for x in row["training"]) == 1
            and row["selected_label"] == "node_attrs:out:agent:has_actor_goal:actor+verb"
            and row["decision"].get("proposal_id") == next(
                d["proposal_id"] for d in row["descriptors"]
                if d["label"] == "node_attrs:out:agent:has_actor_goal:actor+verb")
            for row in order_rows),
        "abstention_controls": all(not row["controls"][arm].get("ok")
            for row in order_rows for arm in ("all_wrong", "tie")),
        "heldout_selected_and_source_pass": all(
            next(x for x in by_score[row["worker"]]["heldout"]
                 if x["proposal_id"] == row["decision"].get("proposal_id"))["correct"]
            and row["training_source_control"]["correct"]
            and by_score[row["worker"]]["heldout_source_control"]["correct"]
            for row in order_rows),
        "all_heldout_candidates_scored": all(len(row["heldout"]) == 8
            and all(x["rule_store_stable"] and x["fixedpoint_progress"] == 0
                    for x in row["heldout"])
            for row in score_rows),
    }
    label_rates = {}
    for descriptor in order_rows[0]["descriptors"]:
        label = descriptor["label"]
        wins = sum(next(x for x in row["training"]
                        if x["proposal_id"] == descriptor["proposal_id"])["correct"]
                   for row in order_rows)
        heldout = sum(next(x for x in by_score[row["worker"]]["heldout"]
                           if x["proposal_id"] == descriptor["proposal_id"])["correct"]
                      for row in order_rows)
        label_rates[label] = {"training_correct_workers": wins,
                              "heldout_correct_workers": heldout}
    costs = {
        "generation_median_ms": statistics.median(x["generation_ns"] for x in order_rows) / 1e6,
        "training_scoring_median_ms": statistics.median(x["training_scoring_ns"] for x in order_rows) / 1e6,
        "selector_median_ms": statistics.median(x["selector_ns"] for x in order_rows) / 1e6,
        "heldout_all_candidate_scoring_median_ms": statistics.median(
            x["heldout_scoring_ns"] for x in score_rows) / 1e6,
    }
    result = {"schema": "ThoughtexperimentEditOpsNodeIdentityV1_1Analysis",
        "checks": checks, "candidate_outcomes": label_rates, "costs": costs,
        "interpretation_boundary": "One synthetic actor-recipient rule family; does not establish autonomous residual diagnosis or general self-improvement."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
