#!/usr/bin/env python3
"""Amended node-scale analysis adding allocator retention to original gates."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_revision_receipt_validation_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_revision_receipt_validation_v1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_revision_receipt_validation_v1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_revision_receipt_validation_v1_analysis_20261004.json"
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values): return statistics.median(values) if values else None


def load_runner():
    spec = importlib.util.spec_from_file_location("revision_receipt_validation_runner_v1", RUNNER)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod


def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text()); runner = load_runner()
    rows = capture.get("runs", []); current = runner.locked_inputs(); configs = runner.configurations()
    expected = {(c["noise_nodes"], c["backend"], c["replicate"], c["validation_mode"]) for c in configs}
    observed = {(r["configuration"]["noise_nodes"], r["configuration"]["backend"], r["configuration"]["replicate"], r["configuration"]["validation_mode"]) for r in rows}
    checks = {
        "prelock_recomputes_and_matches": capture.get("locked_inputs") == lock.get("locked_inputs") == current,
        "postrun_sources_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == current,
        "exact_16_cell_paired_schedule": capture.get("configs") == configs and len(rows) == 16 and observed == expected,
        "no_failures_unique_pids": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 16,
        "oracle_isolation_revision_and_correct_selection": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            and r["oracle_grounded_frame_count"] == 4 and r["oracle_grounded_evidence_exact"] for r in rows),
        "only_correct_candidate_grounded": all(sum(x["grounding_status"] == "candidate_grounded" and x["evidence"] == EVIDENCE
            for x in r["candidate_outcomes"]) == 1 and all(x["grounding_status"] == "unresolved"
            for x in r["candidate_outcomes"] if x["candidate_id"] != r["correct_candidate_position"]) for r in rows),
        "quiescence_and_mode_specific_instrumentation": all(len(r["candidate_outcomes"]) == 4
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"])
            and r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == (5 if r["configuration"]["validation_mode"] == "full_digest" else 0)
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == (5 if r["configuration"]["validation_mode"] == "full_digest" else 0)
            and (r["returned_branch_matches"] is True)
            and (r["exact_post_lifecycle_audit_ns"] > 0 if r["configuration"]["validation_mode"] == "revision_receipt" else r["exact_post_lifecycle_audit_ns"] == 0) for r in rows),
        "known_graph_size_and_component_conservation": all(r["node_count"] == r["configuration"]["noise_nodes"] + 511
            and r["edge_count"] == 467 and r["lifecycle_wall_ns"] >= sum(r["phase_ns"].values())
            + r["cost_breakdown_in_lifecycle"]["graph_export_ns"]
            + r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in rows),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
      for mode in ("full_digest", "revision_receipt"):
        by_size = {}
        for size in (200_000, 1_000_000):
            group = [r for r in rows if r["configuration"]["backend"] == backend and r["configuration"]["validation_mode"] == mode and r["configuration"]["noise_nodes"] == size]
            checks[f"{backend}_{mode}_{size}_two_replicates"] = len(group) == 2
            get = lambda fn: [fn(r) for r in group]
            by_size[size] = {"workers": len(group), "median_nodes": median(get(lambda r: r["node_count"])),
                "median_edges": median(get(lambda r: r["edge_count"])),
                "median_lifecycle_ms": median(get(lambda r: r["lifecycle_wall_ns"])) / 1e6,
                "median_graph_export_ms": median(get(lambda r: r["cost_breakdown_in_lifecycle"]["graph_export_ns"])) / 1e6,
                "median_digest_ms": median(get(lambda r: r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"])) / 1e6,
                "median_candidate_forks_ms": median(get(lambda r: r["phase_ns"]["candidate_forks_total"])) / 1e6,
                "median_named_phases_ms": median(get(lambda r: sum(r["phase_ns"].values()))) / 1e6,
                "median_unattributed_remainder_ms": median(get(lambda r: r["lifecycle_wall_ns"] - sum(r["phase_ns"].values())
                    - r["cost_breakdown_in_lifecycle"]["graph_export_ns"] - r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"])) / 1e6,
                "median_baseline_pss_mib": median(get(lambda r: r["memory_kib"]["baseline_pss"])) / 1024,
                "median_peak_rss_mib": median(get(lambda r: r["memory_kib"]["peak_rss_after_drop"])) / 1024,
                "median_retained_pss_delta_mib": median(get(lambda r: r["memory_kib"]["retained_fanout_pss"] - r["memory_kib"]["baseline_pss"])) / 1024,
                "median_allocator_baseline_mib": median(get(lambda r: r["allocator_bytes"]["baseline"]["in_use"])) / 1048576,
                "median_allocator_retained_delta_mib": median(get(lambda r: r["allocator_bytes"]["retained_fanout"]["in_use"] - r["allocator_bytes"]["baseline"]["in_use"])) / 1048576,
                "median_allocator_after_drop_delta_mib": median(get(lambda r: r["allocator_bytes"]["after_drop"]["in_use"] - r["allocator_bytes"]["baseline"]["in_use"])) / 1048576}
        scale = {metric: {"200k_to_1m": (by_size[1_000_000][metric] / by_size[200_000][metric]
                if by_size[200_000][metric] not in (0, None) else None)}
            for metric in ("median_lifecycle_ms", "median_graph_export_ms", "median_digest_ms", "median_candidate_forks_ms", "median_allocator_retained_delta_mib")}
        summaries[f"{backend}_{mode}"] = {"by_noise_nodes": by_size, "scale_ratios": scale}
    speedups = {}
    for backend in ("full_copy", "shared_graph_pages"):
        speedups[backend] = {}
        for size in (200_000, 1_000_000):
            full = summaries[f"{backend}_full_digest"]["by_noise_nodes"][size]
            fast = summaries[f"{backend}_revision_receipt"]["by_noise_nodes"][size]
            full_life, fast_life = full["median_lifecycle_ms"], fast["median_lifecycle_ms"]
            full_inclusive = full_life
            fast_inclusive = fast_life + median([r["exact_post_lifecycle_audit_ns"] for r in rows
                if r["configuration"]["backend"] == backend and r["configuration"]["noise_nodes"] == size
                and r["configuration"]["validation_mode"] == "revision_receipt"]) / 1e6
            reps = (0, 1)
            per_rep = []
            for rep in reps:
                f = next(r for r in rows if r["configuration"]["backend"] == backend and r["configuration"]["noise_nodes"] == size and r["configuration"]["replicate"] == rep and r["configuration"]["validation_mode"] == "full_digest")
                q = next(r for r in rows if r["configuration"]["backend"] == backend and r["configuration"]["noise_nodes"] == size and r["configuration"]["replicate"] == rep and r["configuration"]["validation_mode"] == "revision_receipt")
                per_rep.append({"replicate": rep,
                    "lifecycle_speedup": f["lifecycle_wall_ns"] / q["lifecycle_wall_ns"],
                    "audit_inclusive_speedup": f["lifecycle_wall_ns"] / (q["lifecycle_wall_ns"] + q["exact_post_lifecycle_audit_ns"]),
                    "fast_exact_audit_ms": q["exact_post_lifecycle_audit_ns"] / 1e6})
            lifecycle_pairs = [x["lifecycle_speedup"] for x in per_rep]
            inclusive_pairs = [x["audit_inclusive_speedup"] for x in per_rep]
            speedups[backend][str(size)] = {"lifecycle_speedup_ratio_of_medians": full_life / fast_life,
                "median_paired_lifecycle_speedup": median(lifecycle_pairs), "paired_lifecycle_speedups": lifecycle_pairs,
                "full_digest_lifecycle_ms": full_life, "revision_receipt_lifecycle_ms": fast_life,
                "revision_receipt_exact_audit_inclusive_ms": fast_inclusive,
                "median_paired_audit_inclusive_speedup": median(inclusive_pairs), "paired_audit_inclusive_speedups": inclusive_pairs,
                "revision_receipt_audit_ms": fast_inclusive - fast_life, "per_replicate": per_rep}
    result = {"schema": "ThoughtexperimentRevisionReceiptValidationV1Analysis",
        "analysis_amendment": "Paired source-locked comparison of full graph digests and O(1) revision/journal checks, with exact full-state audit retained outside the fast lifecycle.",
        "capture_sha256": sha(CAPTURE), "analysis_script_sha256": sha(Path(__file__)),
        "checks": checks, "summaries": summaries, "paired_speedups": speedups,
        "interpretation": "The revision/receipt mode removes five full graph exports/digests from the timed lifecycle and preserves full branch/primary parity immediately afterward. Report operational lifecycle time separately from exact-audit time; speedup is conditional on the tracked-writer and complete-journal contract.",
        "claim_boundary": "200k/1m isolated unrelated-node scale; both validation modes and both fork backends; two paired replicates per cell. The revision/receipt arm uses full exact digest parity immediately after its timed lifecycle; no general complexity or natural-task claim."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries, "paired_speedups": speedups}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
