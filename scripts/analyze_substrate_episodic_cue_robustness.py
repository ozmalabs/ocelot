#!/usr/bin/env python3
"""Independent audit for the preregistered episodic cue robustness run."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_episodic_cue_robustness_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/episodic_cue_robustness_lock_20260925.json"


def main():
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    hashes = {key: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == lock["sha256"][key]
              for key, path in lock["paths"].items()}
    arms = {r["condition"]: r for r in raw["runs"]}
    exact = [q for r in raw["runs"] for q in r["queries"] if q["form"] == "exact"]
    transformed = [q for r in raw["runs"] for q in r["queries"] if q["form"] != "exact"]
    checks = {
        "all_locked_hashes_match": all(hashes.values()),
        "expected_arms_and_query_count": set(arms) == {"clean", "near_neighbor"} and all(len(r["queries"]) == 18 for r in arms.values()),
        "all_exact_keys_reconstruct_the_target": len(exact) == 12 and all(
            q["candidate_count"] == 1 and q.get("state_summary") == q["expected_summary"] and
            q["provenance_kind"] == "recalled" and q["observation_status"] == "not_observed"
            for q in exact),
        "all_nonexact_forms_explicitly_miss": len(transformed) == 24 and all(
            q["candidate_count"] == 0 and q["status"] == "insufficient_information"
            for q in transformed),
        "neighbor_arm_keeps_exact_target_identity": all(
            q.get("state_summary") == q["expected_summary"]
            for q in arms["near_neighbor"]["queries"] if q["form"] == "exact"),
        "unique_task_ids_per_arm": all(len({q["task_id"] for q in r["queries"]}) == 18 for r in arms.values()),
        "episode_counts_match": arms["clean"]["episode_count"] == 6 and arms["near_neighbor"]["episode_count"] == 12,
    }
    stats = {}
    for arm, run in arms.items():
        stats[arm] = {}
        for form in ("exact", "truncated", "paraphrase"):
            rows = [q for q in run["queries"] if q["form"] == form]
            times = [q["tick_ns"] / 1e6 for q in rows]
            stats[arm][form] = {
                "n": len(rows),
                "candidate_count_positive": sum(q["candidate_count"] > 0 for q in rows),
                "exact_target_reconstruction": sum(q.get("state_summary") == q["expected_summary"] for q in rows),
                "insufficient_information": sum(q["status"] == "insufficient_information" for q in rows),
                "median_tick_ms": statistics.median(times),
            }
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"],
           "input_hash_match": hashes, "checks": checks, "summary": stats,
           "interpretation": "Current symbolic cue path is exact-key at this interface; truncated/paraphrase forms miss. Synthetic six-item probe only.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_episodic_cue_robustness_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": stats, "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent cue robustness audit failed")


if __name__ == "__main__":
    main()
