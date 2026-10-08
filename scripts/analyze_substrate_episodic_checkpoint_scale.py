#!/usr/bin/env python3
"""Independent audit and robust summaries for episodic checkpoint scale sweep."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_episodic_checkpoint_scale_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/episodic_checkpoint_scale_lock_20260925.json"


def percentile(values, p):
    return sorted(values)[max(0, math.ceil(p * len(values)) - 1)]


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    hash_match = {key: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == lock["sha256"][key]
                  for key, path in lock["paths"].items()}
    runs = raw["runs"]
    expected = {(n, rep) for n in lock["sizes"] for rep in range(lock["replicates_per_size"])}
    actual = {(r["n"], r["replicate"]) for r in runs}
    checks = {
        "all_locked_inputs_match": all(hash_match.values()),
        "complete_preregistered_size_replicate_grid": actual == expected,
        "all_writer_reader_pids_unique": len({r["writer"]["pid"] for r in runs} |
                                               {r["reader"]["pid"] for r in runs}) == 2 * len(runs),
        "writer_reader_pids_differ_per_pair": all(r["writer"]["pid"] != r["reader"]["pid"] for r in runs),
        "exact_episode_counts_roundtrip": all(r["writer"]["episode_count"] == r["reader"]["episode_count"] == r["n"] for r in runs),
        "all_key_queries_exact_and_provenance_safe": all(
            len(r["reader"]["queries"]) == r["n"] and all(q["candidate_count"] == 1 and
            q["state_summary"] == q["expected_summary"] and q["status"] == "recalled" and
            q["provenance_kind"] == "recalled" and q["observation_status"] == "not_observed"
            for q in r["reader"]["queries"]) for r in runs),
        "all_loaded_readers_close_cleanly": all(r["reader"]["close_status"] == "closed" for r in runs),
    }
    summary = {}
    for n in lock["sizes"]:
        group = [r for r in runs if r["n"] == n]
        all_ticks = [q["tick_ns"] / 1e6 for r in group for q in r["reader"]["queries"]]
        first_ticks = [r["reader"]["queries"][0]["tick_ns"] / 1e6 for r in group]
        last_ticks = [r["reader"]["queries"][-1]["tick_ns"] / 1e6 for r in group]
        summary[str(n)] = {
            "replicates": len(group),
            "exact_recall_rate": sum(q["state_summary"] == q["expected_summary"]
                                      for r in group for q in r["reader"]["queries"]) / sum(len(r["reader"]["queries"]) for r in group),
            "checkpoint_bytes_median": statistics.median(r["writer"]["checkpoint_bytes"] for r in group),
            "save_ms_median": statistics.median(r["writer"]["save_ns"] / 1e6 for r in group),
            "load_ms_median": statistics.median(r["reader"]["load_ns"] / 1e6 for r in group),
            "closure_ms_median": statistics.median(r["writer"]["closure_ns"] / 1e6 for r in group),
            "per_query_tick_ms_median": statistics.median(all_ticks),
            "per_query_tick_ms_p95": percentile(all_ticks, .95),
            "first_query_tick_ms_median": statistics.median(first_ticks),
            "last_query_tick_ms_median": statistics.median(last_ticks),
            "total_query_tick_ms_per_reader_median": statistics.median(
                sum(q["tick_ns"] for q in r["reader"]["queries"]) / 1e6 for r in group),
            "writer_peak_rss_kib_max": max(r["writer"]["rss_peak_kib"] for r in group),
            "reader_peak_rss_kib_max": max(r["reader"]["rss_peak_kib"] for r in group),
        }
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"],
           "input_hash_match": hash_match, "checks": checks, "summary": summary,
           "interpretation": "Synthetic full-graph checkpoint/all-key recall envelope; measurements are descriptive and do not establish asymptotic complexity.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_episodic_checkpoint_scale_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent checkpoint scale audit failed")


if __name__ == "__main__":
    main()
