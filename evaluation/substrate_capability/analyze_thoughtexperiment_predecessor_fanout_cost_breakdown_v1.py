#!/usr/bin/env python3
"""Independent source/semantic and timer-conservation analysis for cost breakdown."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_cost_breakdown_v1_analysis_20261004.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs():
    spec = importlib.util.spec_from_file_location("fanout_cost_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.locked_inputs()


def median(values):
    return statistics.median(values) if values else None


def main():
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    rows = capture.get("runs", [])
    expected = {(b, r) for b in ("full_copy", "shared_graph_pages") for r in range(3)}
    observed = {(r["configuration"]["backend"], r["configuration"]["replicate"]) for r in rows}
    checks = {
        "lock_matches_capture": capture.get("locked_inputs") == lock.get("locked_inputs"),
        "lock_recomputes": current_inputs() == lock.get("locked_inputs"),
        "post_run_source_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == lock.get("locked_inputs"),
        "complete_six_worker_matrix": len(rows) == 6 and len({r["pid"] for r in rows}) == 6 and observed == expected,
        "no_worker_failures": capture.get("worker_failures") == [],
        "semantic_gates_pass": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"])
            for r in rows),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        group = [r for r in rows if r["configuration"]["backend"] == backend]
        named = [sum(r["phase_ns"].values()) for r in group]
        export = [r["cost_breakdown_in_lifecycle"]["graph_export_ns"] for r in group]
        digest = [r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in group]
        life = [r["lifecycle_wall_ns"] for r in group]
        remainder = [t - n - e - d for t, n, e, d in zip(life, named, export, digest)]
        checks[f"{backend}_component_sum_within_lifecycle"] = all(x >= 0 for x in remainder)
        checks[f"{backend}_instrumentation_nonempty"] = all(
            r["cost_breakdown_in_lifecycle"]["graph_export_calls"] > 0
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] > 0 for r in group)
        summaries[backend] = {
            "workers": len(group),
            "median_lifecycle_ms": median(life) / 1e6 if life else None,
            "median_named_phases_ms": median(named) / 1e6 if named else None,
            "median_graph_export_ms": median(export) / 1e6 if export else None,
            "median_graph_export_calls": median([r["cost_breakdown_in_lifecycle"]["graph_export_calls"] for r in group]),
            "median_canonical_digest_ms": median(digest) / 1e6 if digest else None,
            "median_canonical_digest_calls": median([r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] for r in group]),
            "median_residual_unattributed_ms": median(remainder) / 1e6 if remainder else None,
            "median_named_phase_fraction": median([n / t for n, t in zip(named, life) if t]),
            "median_export_fraction": median([e / t for e, t in zip(export, life) if t]),
            "median_digest_fraction": median([d / t for d, t in zip(digest, life) if t]),
            "per_worker_components_ms": [{"replicate": r["configuration"]["replicate"],
                "lifecycle": r["lifecycle_wall_ns"] / 1e6,
                "named_phases": sum(r["phase_ns"].values()) / 1e6,
                "graph_export": r["cost_breakdown_in_lifecycle"]["graph_export_ns"] / 1e6,
                "canonical_digest": r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] / 1e6,
                "remainder": (r["lifecycle_wall_ns"] - sum(r["phase_ns"].values())
                    - r["cost_breakdown_in_lifecycle"]["graph_export_ns"]
                    - r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"]) / 1e6} for r in group],
        }
    result = {"schema": "ThoughtexperimentPredecessorFanoutCostBreakdownV1Analysis",
        "capture_sha256": sha(CAPTURE), "locked_inputs": lock.get("locked_inputs"),
        "checks": checks, "summaries": summaries,
        "interpretation": "Graph export and canonical digest are directly timed inside the lifecycle boundary. Named phase timers and these new timers are disjoint in this workload. The final remainder includes other uninstrumented audits, validation, wrapper operations, and timer overhead; it is not causally attributed.",
        "claim_boundary": "Six source-locked runs of one authored 100k-node workload on one host; not a natural workload estimate or scaling law."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
        "summaries": {k: {n: v for n, v in x.items() if n != "per_worker_components_ms"} for k, x in summaries.items()}}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
