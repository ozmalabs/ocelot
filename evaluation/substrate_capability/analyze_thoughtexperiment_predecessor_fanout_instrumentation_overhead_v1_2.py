#!/usr/bin/env python3
"""Independent analysis of the eight-pair instrumentation overhead follow-up."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_2_analysis_20261004.json"
SEMANTIC_FIELDS = ("candidate_id", "head", "grounding_status", "evidence", "grounded_frame_count",
    "grounded_evidence_exact", "sweeps", "scope_calls", "work_steps", "quiescent",
    "terminal_zero_progress_sweep", "residual_total_counts", "residual_derived_counts")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("fanout_overhead_v1_1_runner", RUNNER)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module); return module


def project(row): return [{k: item[k] for k in SEMANTIC_FIELDS} for item in row["candidate_outcomes"]]


def mean_t_interval(values):
    n = len(values); mean = statistics.mean(values); se = statistics.stdev(values) / n ** 0.5 if n > 1 else 0
    return {"mean_ms": mean, "stddev_ms": statistics.stdev(values) if n > 1 else 0,
            "standard_error_ms": se, "ci95_t_df7_ms": [mean - 2.365 * se, mean + 2.365 * se] if n == 8 else None}


def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text()); runner = load_runner()
    current = runner.locked_inputs(); configs = runner.configurations(); schedule = runner.schedule(); rows = capture.get("runs", [])
    grouped = {}
    for row in rows:
        c = row["configuration"]
        grouped.setdefault((c["backend"], c["replicate"]), {})[row["instrumentation_arm"]] = row
    checks = {
        "lock_matches_and_recomputes": capture.get("locked_inputs") == lock.get("locked_inputs") == current,
        "postrun_sources_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == current,
        "fixed_schedule_and_32_rows": capture.get("configs") == configs and capture.get("schedule") == schedule and len(rows) == 32,
        "no_worker_failures_and_unique_pids": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 32,
        "16_complete_pairs": len(grouped) == 16 and all(set(g) == {"off", "on"} for g in grouped.values()),
        "eight_pairs_per_backend": all(sum(b == backend for b, _ in grouped) == 8 for backend in ("full_copy", "shared_graph_pages")),
        "semantic_gates_each_arm": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"])
            for r in rows),
        "exact_pairwise_semantic_projection": all(g["on"]["baseline_primary_digest"] == g["off"]["baseline_primary_digest"]
            and g["on"]["valid_candidate_ids"] == g["off"]["valid_candidate_ids"]
            and project(g["on"]) == project(g["off"]) for g in grouped.values() if set(g) == {"on", "off"}),
        "five_exports_and_digests_per_on_worker": all(
            r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 5
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 5
            for r in rows if r["instrumentation_arm"] == "on"),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        pairs = []
        for (b, rep), arms in sorted(grouped.items()):
            if b != backend or set(arms) != {"off", "on"}: continue
            off, on = arms["off"]["lifecycle_wall_ns"] / 1e6, arms["on"]["lifecycle_wall_ns"] / 1e6
            pairs.append({"replicate": rep, "off_ms": off, "on_ms": on, "delta_ms": on - off, "ratio_on_off": on / off,
                "export_ms_on": arms["on"]["cost_breakdown_in_lifecycle"]["graph_export_ns"] / 1e6,
                "digest_ms_on": arms["on"]["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] / 1e6})
        deltas = [p["delta_ms"] for p in pairs]
        summaries[backend] = {"pairs": pairs, "median_off_ms": statistics.median([p["off_ms"] for p in pairs]),
            "median_on_ms": statistics.median([p["on_ms"] for p in pairs]),
            "median_delta_ms": statistics.median(deltas), "median_ratio_on_off": statistics.median([p["ratio_on_off"] for p in pairs]),
            "paired_delta_summary": mean_t_interval(deltas), "paired_delta_range_ms": [min(deltas), max(deltas)],
            "median_export_ms_on": statistics.median([p["export_ms_on"] for p in pairs]),
            "median_digest_ms_on": statistics.median([p["digest_ms_on"] for p in pairs])}
    result = {"schema": "ThoughtexperimentFanoutInstrumentationOverheadV1_2Analysis", "capture_sha256": sha(CAPTURE),
        "analysis_script_sha256": sha(Path(__file__)), "checks": checks, "summaries": summaries,
        "interval_method": "paired mean delta ± 2.365 standard errors (two-sided 95% t critical, df=7)",
        "interpretation": "Eight pairs improve precision over v1 but remain one workload/host. The interval estimates combined clock-call and Python-wrapper dispatch impact; it does not isolate those sources or prove universal negligible overhead.",
        "claim_boundary": "One authored 100k-node workload with fixed frame/fanout shape; no scale law."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
        "summaries": {k: {n: v for n, v in x.items() if n != "pairs"} for k, x in summaries.items()}}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
