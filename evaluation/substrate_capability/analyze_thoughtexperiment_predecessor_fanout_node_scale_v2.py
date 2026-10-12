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
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v2.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v2_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v2_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v2_analysis_20261004.json"
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values): return statistics.median(values) if values else None


def load_runner():
    spec = importlib.util.spec_from_file_location("fanout_node_scale_runner_v2", RUNNER)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod


def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text()); runner = load_runner()
    rows = capture.get("runs", []); current = runner.locked_inputs(); configs = runner.configurations()
    expected = {(c["noise_nodes"], c["backend"], c["replicate"]) for c in configs}
    observed = {(r["configuration"]["noise_nodes"], r["configuration"]["backend"], r["configuration"]["replicate"]) for r in rows}
    checks = {
        "prelock_recomputes_and_matches": capture.get("locked_inputs") == lock.get("locked_inputs") == current,
        "postrun_sources_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == current,
        "exact_12_cell_schedule": capture.get("configs") == configs and len(rows) == 12 and observed == expected,
        "no_failures_unique_pids": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 12,
        "oracle_isolation_revision_and_correct_selection": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            and r["oracle_grounded_frame_count"] == 4 and r["oracle_grounded_evidence_exact"] for r in rows),
        "only_correct_candidate_grounded": all(sum(x["grounding_status"] == "candidate_grounded" and x["evidence"] == EVIDENCE
            for x in r["candidate_outcomes"]) == 1 and all(x["grounding_status"] == "unresolved"
            for x in r["candidate_outcomes"] if x["candidate_id"] != r["correct_candidate_position"]) for r in rows),
        "quiescence_and_instrumentation_counts": all(len(r["candidate_outcomes"]) == 4
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"])
            and r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 5
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 5 for r in rows),
        "known_graph_size_and_component_conservation": all(r["node_count"] == r["configuration"]["noise_nodes"] + 511
            and r["edge_count"] == 467 and r["lifecycle_wall_ns"] >= sum(r["phase_ns"].values())
            + r["cost_breakdown_in_lifecycle"]["graph_export_ns"]
            + r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in rows),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        by_size = {}
        for size in (200_000, 400_000, 1_000_000):
            group = [r for r in rows if r["configuration"]["backend"] == backend and r["configuration"]["noise_nodes"] == size]
            checks[f"{backend}_{size}_two_replicates"] = len(group) == 2
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
        scale = {}
        for metric in ("median_lifecycle_ms", "median_graph_export_ms", "median_digest_ms", "median_candidate_forks_ms",
                       "median_allocator_retained_delta_mib"):
            scale[metric] = {"200k_to_400k": by_size[400_000][metric] / by_size[200_000][metric],
                "400k_to_1m": by_size[1_000_000][metric] / by_size[400_000][metric]}
        summaries[backend] = {"by_noise_nodes": by_size, "scale_ratios": scale}
    result = {"schema": "ThoughtexperimentFanoutNodeScaleV2Analysis",
        "analysis_amendment": "Extends the current-source node scale to one million unrelated nodes, retaining allocator and release summaries.",
        "capture_sha256": sha(CAPTURE), "analysis_script_sha256": sha(Path(__file__)),
        "checks": checks, "summaries": summaries,
        "interpretation": "In this fixed sparse-edge workload, graph export, canonical digest, and full-copy branch allocation rise approximately in proportion to node count over the sampled range; shared-page fork time and retained allocator growth are much smaller. Instrumentation effects remain uncertain from the prior paired control. This is descriptive for one host/workload.",
        "claim_boundary": "200k/400k/1m isolated unrelated-node scale, four frames, four candidate branches, two workers per cell; no natural workload or general complexity law."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
