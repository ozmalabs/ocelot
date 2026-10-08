#!/usr/bin/env python3
"""Independent analysis of the fixed-size edge-topology fanout replay."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_edge_topology_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_edge_topology_v1_1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_edge_topology_v1_1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_edge_topology_v1_1_analysis_20261004.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_1_analysis_20261004.json"
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("fanout_edge_topology_runner_analysis", RUNNER)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod


def median(xs): return statistics.median(xs) if xs else None


def main():
    from substrate_rs import _native
    capture, lock, runner = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text()), load_runner()
    rows = capture.get("runs", [])
    configs = runner.configurations()
    current = runner.locked_inputs()
    expected = {(c["noise_edge_topology"], c["backend"], c["replicate"]) for c in configs}
    observed = {(r["configuration"]["noise_edge_topology"], r["configuration"]["backend"],
                 r["configuration"]["replicate"]) for r in rows}
    checks = {
        "lock_matches_recomputed_sources": lock.get("locked_inputs") == capture.get("locked_inputs") == current,
        "postrun_sources_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == current,
        "native_build_identity_present": bool(_native.__file__) and Path(_native.__file__).is_file(),
        "exact_24_cell_schedule": capture.get("configurations") == configs and len(rows) == 24 and observed == expected,
        "no_worker_failures_unique_processes": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 24,
        "exact_graph_size_and_edge_count": all(r["node_count"] == 100_511 and r["edge_count"] == 100_466
            and r["configuration"]["noise_edge_count"] == 99_999 for r in rows),
        "correct_candidate_and_oracle_parity": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["oracle_grounded_frame_count"] == 4 and r["oracle_grounded_evidence_exact"] for r in rows),
        "isolation_revision_and_rule_gates": all(r["primary_unchanged_before_return"]
            and r["returned_branch_matches"] and r["all_primary_rules_preserved"]
            and r["stale_residual_rejected"] and r["stale_retry_left_primary_unchanged"] for r in rows),
        "candidate_semantics_and_quiescence": all(len(r["candidate_outcomes"]) == 4
            and sum(x["grounding_status"] == "candidate_grounded" and x["evidence"] == EVIDENCE
                    for x in r["candidate_outcomes"]) == 1
            and all(x["quiescent"] and x["terminal_zero_progress_sweep"] for x in r["candidate_outcomes"])
            and all(x["grounding_status"] == "unresolved" for x in r["candidate_outcomes"]
                    if x["candidate_id"] != r["correct_candidate_position"]) for r in rows),
        "lifecycle_instrumentation_and_conservation": all(
            r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 5
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 5
            and r["lifecycle_wall_ns"] >= sum(r["phase_ns"].values())
                + r["cost_breakdown_in_lifecycle"]["graph_export_ns"]
                + r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in rows),
        "topology_setup_cost_recorded_outside_lifecycle": all(r["noise_topology_setup_calls"] == 2
            and len(r["noise_topology_setup_ns"]) == 2 and all(x >= 0 for x in r["noise_topology_setup_ns"])
            for r in rows),
    }
    summaries = {}
    base = json.loads(BASE_ANALYSIS.read_text())["summaries"]
    for topology in ("path", "star", "cluster_star", "random_recursive_tree"):
        summaries[topology] = {}
        for backend in ("full_copy", "shared_graph_pages"):
            group = [r for r in rows if r["configuration"]["noise_edge_topology"] == topology
                     and r["configuration"]["backend"] == backend]
            checks[f"{topology}_{backend}_three_replicates"] = len(group) == 3
            names = {
                "lifecycle_ms": lambda r: r["lifecycle_wall_ns"] / 1e6,
                "graph_export_ms": lambda r: r["cost_breakdown_in_lifecycle"]["graph_export_ns"] / 1e6,
                "digest_ms": lambda r: r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] / 1e6,
                "candidate_forks_ms": lambda r: r["phase_ns"]["candidate_forks_total"] / 1e6,
                "topology_setup_ms_two_graphs": lambda r: sum(r["noise_topology_setup_ns"]) / 1e6,
                "allocator_retained_delta_mib": lambda r: (r["allocator_bytes"]["retained_fanout"]["in_use"]
                    - r["allocator_bytes"]["baseline"]["in_use"]) / 1048576,
                "baseline_pss_mib": lambda r: r["memory_kib"]["baseline_pss"] / 1024,
                "peak_rss_mib": lambda r: r["memory_kib"]["peak_rss_after_drop"] / 1024,
            }
            values = {key: median([fn(r) for r in group]) for key, fn in names.items()}
            sparse = base[backend]["by_noise_nodes"][100_000]
            baseline = {"lifecycle_ms": sparse["median_lifecycle_ms"],
                        "graph_export_ms": sparse["median_graph_export_ms"],
                        "digest_ms": sparse["median_digest_ms"],
                        "candidate_forks_ms": sparse["median_candidate_forks_ms"],
                        "allocator_retained_delta_mib": sparse["median_allocator_retained_delta_mib"]}
            values["ratio_to_100k_sparse_baseline"] = {key: values[key] / base_value
                for key, base_value in baseline.items() if base_value not in (0, None)}
            summaries[topology][backend] = {"workers": len(group), **values}
    result = {"schema": "ThoughtexperimentFanoutEdgeTopologyV1_1Analysis", "capture_sha256": sha(CAPTURE),
        "analysis_script_sha256": sha(Path(__file__)), "checks": checks, "summaries": summaries,
        "interpretation": "Equal node/edge counts hold graph size and mean sparsity approximately fixed while varying degree distribution and component layout. Any timing differences are descriptive for this one host and unrelated background graph; candidate semantics must still pass independently in every cell.",
        "claim_boundary": "100k unrelated nodes plus 99,999 background edges, four prescribed tree layouts, four frames, four supplied candidates, two snapshot backends, and three fresh workers per cell. This does not establish natural task topology prevalence, learned cuts, concurrent throughput, or a complexity law."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
