#!/usr/bin/env python3
"""Amended paired-outcome audit for instrumentation overhead v1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_1_analysis_20261004.json"
SEMANTIC_FIELDS = ("candidate_id", "head", "grounding_status", "evidence", "grounded_frame_count",
    "grounded_evidence_exact", "sweeps", "scope_calls", "work_steps", "quiescent",
    "terminal_zero_progress_sweep", "residual_total_counts", "residual_derived_counts")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs():
    spec = importlib.util.spec_from_file_location("fanout_overhead_runner_v1_1", RUNNER)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
    return module.locked_inputs(), module.configurations(), module.schedule()


def project_outcomes(row):
    return [{key: item[key] for key in SEMANTIC_FIELDS} for item in row["candidate_outcomes"]]


def median(values): return statistics.median(values) if values else None


def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text())
    rows = capture.get("runs", []); inputs, configs, schedule = current_inputs()
    grouped = {}
    for row in rows:
        c = row["configuration"]
        grouped.setdefault((c["backend"], c["replicate"]), {})[row["instrumentation_arm"]] = row
    checks = {
        "prelocked_inputs_match_and_recompute": capture.get("locked_inputs") == lock.get("locked_inputs") == inputs,
        "postrun_sources_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == inputs,
        "exact_schedule_and_12_rows": capture.get("configs") == configs and capture.get("schedule") == schedule and len(rows) == 12,
        "no_worker_failures_and_unique_pids": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 12,
        "all_six_pairs_complete": len(grouped) == 6 and all(set(g) == {"off", "on"} for g in grouped.values()),
        "both_arms_pass_individual_semantic_gates": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"])
            for r in rows),
        "instrumentation_only_in_on_arm": all(
            (r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 5
             and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 5)
            if r["instrumentation_arm"] == "on" else
            (r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 0
             and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 0)
            for r in rows),
        "exact_pairwise_semantic_outcome_parity": all(
            g["on"]["baseline_primary_digest"] == g["off"]["baseline_primary_digest"]
            and g["on"]["valid_candidate_ids"] == g["off"]["valid_candidate_ids"]
            and g["on"]["selected_candidate_id"] == g["off"]["selected_candidate_id"]
            and project_outcomes(g["on"]) == project_outcomes(g["off"])
            and g["on"]["returned_branch_matches"] == g["off"]["returned_branch_matches"]
            for g in grouped.values() if set(g) == {"on", "off"}),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        pairs = []
        for (b, replicate), arms in sorted(grouped.items()):
            if b != backend or set(arms) != {"off", "on"}: continue
            off, on = arms["off"], arms["on"]
            off_ms, on_ms = off["lifecycle_wall_ns"] / 1e6, on["lifecycle_wall_ns"] / 1e6
            pairs.append({"replicate": replicate, "off_ms": off_ms, "on_ms": on_ms,
                "delta_ms": on_ms - off_ms, "ratio_on_off": on_ms / off_ms,
                "on_graph_export_ms": on["cost_breakdown_in_lifecycle"]["graph_export_ns"] / 1e6,
                "on_canonical_digest_ms": on["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] / 1e6})
        summaries[backend] = {"pairs": pairs, "median_off_ms": median([p["off_ms"] for p in pairs]),
            "median_on_ms": median([p["on_ms"] for p in pairs]),
            "median_paired_delta_ms": median([p["delta_ms"] for p in pairs]),
            "median_paired_ratio_on_off": median([p["ratio_on_off"] for p in pairs]),
            "paired_delta_range_ms": [min(p["delta_ms"] for p in pairs), max(p["delta_ms"] for p in pairs)] if pairs else None,
            "median_instrumented_export_ms": median([p["on_graph_export_ms"] for p in pairs]),
            "median_instrumented_digest_ms": median([p["on_canonical_digest_ms"] for p in pairs])}
    result = {"schema": "ThoughtexperimentFanoutInstrumentationOverheadV1_1Analysis",
        "analysis_revision": "Post-capture amendment: adds exact pairwise semantic outcome projection; capture and pre-run lock unchanged.",
        "capture_sha256": sha(CAPTURE), "analysis_script_sha256": sha(Path(__file__)),
        "checks": checks, "summaries": summaries,
        "interpretation": "Three pairs per backend show variable paired timing deltas; medians near zero do not establish zero overhead. The combined clock-wrapper and Python dispatch effect is small relative to multi-second lifecycle here, but the sample is too small to estimate a general overhead factor.",
        "claim_boundary": "One host and one authored 100k-node workload; no general runtime-overhead or scaling claim."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
        "summaries": {k: {n: v for n, v in x.items() if n != "pairs"} for k, x in summaries.items()}}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
