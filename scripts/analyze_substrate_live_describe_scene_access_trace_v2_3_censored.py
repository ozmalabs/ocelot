#!/usr/bin/env python3
"""Independent integrity summary for the censored live conversation v2.3 run."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_3_workers_raw_20260927.json"
OUT = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_3_censored_analysis_20260927.json"

raw = json.loads(RAW.read_text())
runs = raw["runs"]
checks = {
    "six_workers": len(runs) == 6,
    "three_replicates_each_arm": sum(not r["trace_enabled"] for r in runs) == 3 and sum(bool(r["trace_enabled"]) for r in runs) == 3,
    "all_source_locks_match": all(r.get("worker_started_inputs") == raw["locked_inputs"] == r.get("worker_finished_inputs") for r in runs),
    "paired_graph_semantic_parity": all(next(x for x in runs if x["replicate"] == r["replicate"] and x["trace_enabled"] != r["trace_enabled"])["whole_graph_semantic_sha256"] == r["whole_graph_semantic_sha256"] for r in runs),
    "all_workers_joined": all(r.get("threads_joined") for r in runs),
    "all_lifecycle_gates_failed": all(not r.get("lifecycle_gate") for r in runs),
    "no_goal_producer_work": all(not r.get("producer_work") for r in runs),
    "all_workers_selection_timeout": all("A selection timeout" in r.get("errors", []) for r in runs),
    "no_request_bound_goals": all(not r.get("final", {}).get("goals") for r in runs),
}
out = {
    "schema_version": 1,
    "run_id": "substrate-live-describe-scene-access-trace-v2-3-censored-analysis-20260927",
    "source_raw": str(RAW.relative_to(ROOT)),
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "classification": "censored_driver_failure_no_locality_or_timing_claim",
    "worker_count": len(runs),
    "errors": [r.get("errors", []) for r in runs],
    "reply_pairs": [r.get("replies") for r in runs],
    "graph_semantic_hashes": [r.get("whole_graph_semantic_sha256") for r in runs],
    "interpretation": "The six-worker run retained source locks and paired final graph semantic parity, but every worker failed before request A selection, recorded no goal-producer callback work, and had no final request-bound goals. Instrumented timing and access rows are therefore driver artifacts and are excluded from substrate performance/locality evidence.",
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({"output": str(OUT), "checks": checks, "all_checks_pass": out["all_checks_pass"]}, indent=2))
