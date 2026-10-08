#!/usr/bin/env python3
"""Independent audit of the frozen episodic-memory task pilot raw record."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_episodic_memory_task_pilot_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/episodic_memory_task_pilot_lock_20260925.json"


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    hash_match = {
        label: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == lock["sha256"][label]
        for label, path in lock["paths"].items()
    }
    runs = {row["condition"]: row for row in raw["runs"]}
    unique = [q for name in ("memory_small", "memory_medium", "memory_large")
              for q in runs[name]["queries"] if q["task_kind"] == "unique"]
    collisions = [q for q in runs["memory_collision"]["queries"]
                  if q["task_kind"] == "ambiguous"]
    controls = [q for name in ("reset_memory", "no_memory") for q in runs[name]["queries"]]
    checks = {
        "all_locked_inputs_match": all(hash_match.values()),
        "six_expected_arms": set(runs) == set(lock["conditions"]),
        "18_unique_exact_answers_with_recall_provenance": len(unique) == 18 and all(
            q["task_correct"] and q["confidence"] >= lock["confidence_threshold"] and
            q["provenance_kind"] == "recalled" and
            q["observation_status"] == "not_observed" and q["candidate_count"] == 1
            for q in unique),
        "six_collision_cases_abstain_at_half_confidence": len(collisions) == 6 and all(
            q["task_correct"] and q["evaluator_action"] == "abstain" and
            q["confidence"] == q["uncertainty"] == 0.5 and
            q.get("state_summary") in q["expected_summary"] for q in collisions),
        "unknown_cue_abstains_in_each_arm": all(
            row["queries"][-1]["task_kind"] == "unknown" and
            row["queries"][-1]["evaluator_action"] == "abstain" and
            row["queries"][-1]["task_correct"] for row in runs.values()),
        "reset_explicitly_reports_insufficient_information": all(
            q["candidate_count"] == 0 and q["status"] == "insufficient_information" and
            q["evaluator_action"] == "abstain" for q in runs["reset_memory"]["queries"]),
        "no_memory_emits_no_candidate": all(
            q["candidate_count"] == 0 and q["evaluator_action"] == "abstain"
            for q in runs["no_memory"]["queries"]),
        "query_ids_unique_in_each_arm": all(
            len({q["query_id"] for q in r["queries"]}) == len(r["queries"])
            for r in runs.values()),
        "episode_counts_match_declared_sizes": all(
            runs[name]["acquisition_episode_count"] == count
            for name, count in {"memory_small": 6, "memory_medium": 24,
                                "memory_large": 78, "memory_collision": 30,
                                "reset_memory": 0, "no_memory": 0}.items()),
    }
    summary = {}
    for name, row in runs.items():
        task = [q for q in row["queries"] if q["task_kind"] != "unknown"]
        lat = [q["tick_ns"] / 1e6 for q in task]
        summary[name] = {
            "episode_count": row["acquisition_episode_count"],
            "queries": len(row["queries"]),
            "answer_count": sum(q["evaluator_action"] == "answer" for q in row["queries"]),
            "correct_count": sum(q["task_correct"] for q in task),
            "task_count": len(task),
            "median_query_tick_ms": statistics.median(lat),
            "max_query_tick_ms": max(lat),
            "acquisition_tick_ms": row["acquisition_tick_ns"] / 1e6,
            "boot_ms": row["boot_ns"] / 1e6,
            "rss_peak_kib": row["rss_peak_kib"],
        }
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"],
           "input_hash_match": hash_match, "checks": checks, "summary": summary,
           "interpretation": "Independent raw-record audit; synthetic authored task only; timing descriptive.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_episodic_memory_task_pilot_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent episodic-memory audit failed")


if __name__ == "__main__":
    main()
