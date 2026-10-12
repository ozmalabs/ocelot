#!/usr/bin/env python3
"""Independent integrity summary for the exploratory 100k fanout capture."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_100k_exploratory_20261003.json"
OUTPUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_100k_exploratory_analysis_20261003.json"


def main() -> int:
    capture = json.loads(CAPTURE.read_text())
    rows = capture["runs"]
    expected = {
        (rep, backend)
        for rep in range(3)
        for backend in ("full_copy", "shared_graph_pages")
    }
    observed = {
        (row["configuration"]["replicate"], row["configuration"]["backend"])
        for row in rows
    }
    checks = {
        "six_unique_paired_rows": len(rows) == 6 and observed == expected,
        "all_rows_at_100k_scale": all(
            row["configuration"]["noise_nodes"] == 100_000
            and row["node_count"] >= 100_000
            for row in rows
        ),
        "one_candidate_selected_each": all(
            len(row["valid_candidate_ids"]) == 1
            and row["selected_candidate_id"] == row["correct_candidate_position"]
            for row in rows
        ),
        "branch_and_primary_match_monolithic": all(
            row["selected_branch_matches_monolithic_oracle"]
            and row["primary_matches_monolithic_oracle"]
            for row in rows
        ),
        "primary_isolation_and_stale_rejection": all(
            row["primary_unchanged_before_return"]
            and row["stale_residual_rejected"]
            and row["stale_retry_left_primary_unchanged"]
            for row in rows
        ),
        "quiescent_scoped_closure": all(
            len(row["candidate_outcomes"]) == row["configuration"]["fanout"]
            and all(
                outcome["quiescent"] and outcome["terminal_zero_progress_sweep"]
                for outcome in row["candidate_outcomes"]
            )
            for row in rows
        ),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        subset = [row for row in rows if row["configuration"]["backend"] == backend]
        summaries[backend] = {
            "replicates": len(subset),
            "median_lifecycle_ms": statistics.median(
                row["lifecycle_wall_ns"] / 1e6 for row in subset
            ),
            "median_snapshot_ms": statistics.median(
                row["phase_ns"]["snapshot_create"] / 1e6 for row in subset
            ),
            "median_candidate_forks_ms": statistics.median(
                row["phase_ns"]["candidate_forks_total"] / 1e6 for row in subset
            ),
            "median_retained_allocator_delta_mib": statistics.median(
                (row["allocator_bytes"]["retained_fanout"]["in_use"]
                 - row["allocator_bytes"]["baseline"]["in_use"]) / 1048576
                for row in subset
            ),
            "median_post_drop_allocator_delta_mib": statistics.median(
                (row["allocator_bytes"]["after_drop"]["in_use"]
                 - row["allocator_bytes"]["baseline"]["in_use"]) / 1048576
                for row in subset
            ),
            "median_sampled_peak_rss_delta_mib": statistics.median(
                (row["memory_kib"]["peak_rss_after_drop"]
                 - row["memory_kib"]["baseline_rss"]) / 1024
                for row in subset
            ),
        }
    checks["shared_snapshot_forks_faster"] = (
        summaries["shared_graph_pages"]["median_candidate_forks_ms"]
        < summaries["full_copy"]["median_candidate_forks_ms"]
    )
    checks["shared_snapshot_retains_less_allocator_memory"] = (
        summaries["shared_graph_pages"]["median_retained_allocator_delta_mib"]
        < summaries["full_copy"]["median_retained_allocator_delta_mib"]
    )
    result = {
        "schema": "ThoughtexperimentPredecessorFanout100kExploratoryAnalysis",
        "capture": CAPTURE.relative_to(ROOT).as_posix(),
        "checks": checks,
        "summaries": summaries,
        "interpretation_boundary": (
            "Unpreregistered exploratory checkpoint, three replicates per backend, "
            "one host and one 100k-node synthetic noise graph; not a scaling law."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
