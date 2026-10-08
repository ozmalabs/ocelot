#!/usr/bin/env python3
"""Independent paired analysis for instrumentation overhead capture."""
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
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_instrumentation_overhead_v1_analysis_20261004.json"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs():
    spec = importlib.util.spec_from_file_location("fanout_overhead_runner", RUNNER)
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
    return module.locked_inputs(), module.configurations(), module.schedule()


def median(xs): return statistics.median(xs) if xs else None


def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text()); rows = capture["runs"]
    inputs, configs, schedule = current_inputs()
    grouped = {}
    for row in rows:
        c = row["configuration"]
        grouped.setdefault((c["backend"], c["replicate"]), {})[row["instrumentation_arm"]] = row
    checks = {
        "lock_matches_and_recomputes": capture["locked_inputs"] == lock["locked_inputs"] == inputs,
        "sources_stable": capture["source_stable"] and capture["post_run_locked_inputs"] == inputs,
        "exact_schedule_and_matrix": capture["configs"] == configs and capture["schedule"] == schedule and len(rows) == 12,
        "no_failures_and_unique_processes": capture["worker_failures"] == [] and len({r["pid"] for r in rows}) == 12,
        "six_complete_pairs": len(grouped) == 6 and all(set(g) == {"off", "on"} for g in grouped.values()),
        "semantic_parity_each_arm": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            for r in rows),
        "instrumentation_arm_presence": all(
            (r["cost_breakdown_in_lifecycle"]["graph_export_calls"] > 0
             and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] > 0)
            if r["instrumentation_arm"] == "on" else
            (r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 0
             and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 0)
            for r in rows),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        pairs = []
        for (b, rep), group in sorted(grouped.items()):
            if b != backend: continue
            off, on = group["off"], group["on"]
            pairs.append({"replicate": rep, "off_ms": off["lifecycle_wall_ns"] / 1e6,
                "on_ms": on["lifecycle_wall_ns"] / 1e6,
                "delta_ms": (on["lifecycle_wall_ns"] - off["lifecycle_wall_ns"]) / 1e6,
                "ratio_on_off": on["lifecycle_wall_ns"] / off["lifecycle_wall_ns"],
                "graph_digest_equal": on["primary_matches_monolithic_oracle"] == off["primary_matches_monolithic_oracle"],
                "on_export_ms": on["cost_breakdown_in_lifecycle"]["graph_export_ns"] / 1e6,
                "on_digest_ms": on["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] / 1e6})
        summaries[backend] = {"pairs": pairs, "median_off_ms": median([p["off_ms"] for p in pairs]),
            "median_on_ms": median([p["on_ms"] for p in pairs]),
            "median_paired_delta_ms": median([p["delta_ms"] for p in pairs]),
            "median_paired_ratio_on_off": median([p["ratio_on_off"] for p in pairs]),
            "median_export_ms_on": median([p["on_export_ms"] for p in pairs]),
            "median_digest_ms_on": median([p["on_digest_ms"] for p in pairs])}
    result = {"schema": "ThoughtexperimentFanoutInstrumentationOverheadV1Analysis",
        "capture_sha256": sha(CAPTURE), "checks": checks, "summaries": summaries,
        "interpretation": "Paired on/off differences estimate the combined effect of clock calls and Python wrapper dispatch for this workload. They do not separately estimate those two effects or generalize beyond the six pairs.",
        "claim_boundary": "One host and one authored 100k-node workload, with three pairs per backend."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
