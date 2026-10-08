#!/usr/bin/env python3
"""Independent integrity and descriptive scaling analysis for fanout node sweep."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_analysis_20261004.json"
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def runner_module():
    spec = importlib.util.spec_from_file_location("fanout_node_scale_runner", RUNNER)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod


def med(xs): return statistics.median(xs) if xs else None


def main():
    capture = json.loads(CAPTURE.read_text()); lock = json.loads(LOCK.read_text()); runner = runner_module()
    rows = capture.get("runs", []); configs = runner.configurations(); current = runner.locked_inputs()
    expected = {(c["noise_nodes"], c["backend"], c["replicate"]) for c in configs}
    observed = {(r["configuration"]["noise_nodes"], r["configuration"]["backend"], r["configuration"]["replicate"]) for r in rows}
    component_remainders = []
    for r in rows:
        named = sum(r["phase_ns"].values())
        comp = r["cost_breakdown_in_lifecycle"]
        component_remainders.append(r["lifecycle_wall_ns"] - named - comp["graph_export_ns"] - comp["canonical_digest_ns"])
    checks = {
        "source_lock_matches_and_recomputes": capture.get("locked_inputs") == lock.get("locked_inputs") == current,
        "source_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == current,
        "fixed_randomized_18_cell_matrix": capture.get("configs") == configs and len(rows) == 18 and observed == expected,
        "no_failures_unique_workers": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 18,
        "semantic_oracle_isolation_revision_gates": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["primary_unchanged_before_return"] and r["stale_residual_rejected"]
            and r["stale_retry_left_primary_unchanged"] and r["all_primary_rules_preserved"]
            and r["oracle_grounded_frame_count"] == 4 and r["oracle_grounded_evidence_exact"] for r in rows),
        "only_correct_candidate_grounded": all(sum(x["grounding_status"] == "candidate_grounded" and x["evidence"] == EVIDENCE
            for x in r["candidate_outcomes"]) == 1 and all(x["grounding_status"] == "unresolved"
            for x in r["candidate_outcomes"] if x["candidate_id"] != r["correct_candidate_position"]) for r in rows),
        "all_candidates_quiescent": all(len(r["candidate_outcomes"]) == 4 and all(x["quiescent"] and x["terminal_zero_progress_sweep"]
            for x in r["candidate_outcomes"]) for r in rows),
        "five_exports_and_digests_per_worker": all(r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 5
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 5 for r in rows),
        "expected_node_and_edge_counts": all(r["node_count"] == r["configuration"]["noise_nodes"] + 511
            and r["edge_count"] == 467 for r in rows),
        "phase_export_digest_components_fit_lifecycle": all(x >= 0 for x in component_remainders),
    }
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        by_size = {}
        for size in (10_000, 100_000, 200_000):
            group = [r for r in rows if r["configuration"]["backend"] == backend and r["configuration"]["noise_nodes"] == size]
            if len(group) != 3:
                checks[f"{backend}_{size}_three_replicates"] = False
            life = [r["lifecycle_wall_ns"] for r in group]
            export = [r["cost_breakdown_in_lifecycle"]["graph_export_ns"] for r in group]
            digest = [r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in group]
            fork = [r["phase_ns"]["candidate_forks_total"] for r in group]
            phase = [sum(r["phase_ns"].values()) for r in group]
            remainder = [r["lifecycle_wall_ns"] - sum(r["phase_ns"].values())
                - r["cost_breakdown_in_lifecycle"]["graph_export_ns"]
                - r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in group]
            by_size[size] = {"workers": len(group), "median_nodes": med([r["node_count"] for r in group]),
                "median_edges": med([r["edge_count"] for r in group]),
                "median_lifecycle_ms": med(life) / 1e6 if life else None,
                "median_graph_export_ms": med(export) / 1e6 if export else None,
                "median_canonical_digest_ms": med(digest) / 1e6 if digest else None,
                "median_candidate_forks_ms": med(fork) / 1e6 if fork else None,
                "median_named_phases_ms": med(phase) / 1e6 if phase else None,
                "median_unattributed_remainder_ms": med(remainder) / 1e6 if remainder else None,
                "median_baseline_pss_mib": med([r["memory_kib"]["baseline_pss"] for r in group]) / 1024,
                "median_retained_pss_delta_mib": med([r["memory_kib"]["retained_fanout_pss"] - r["memory_kib"]["baseline_pss"] for r in group]) / 1024,
                "median_peak_rss_mib": med([r["memory_kib"]["peak_rss_after_drop"] for r in group]) / 1024}
        ratios = {}
        for metric in ("median_lifecycle_ms", "median_graph_export_ms", "median_canonical_digest_ms", "median_candidate_forks_ms"):
            ratios[metric] = {"10k_to_100k": by_size[100_000][metric] / by_size[10_000][metric],
                "100k_to_200k": by_size[200_000][metric] / by_size[100_000][metric]}
        summaries[backend] = {"by_noise_nodes": by_size, "scale_ratios": ratios}
    result = {"schema": "ThoughtexperimentFanoutNodeScaleV1Analysis", "capture_sha256": sha(CAPTURE),
        "checks": checks, "summaries": summaries,
        "interpretation": "Descriptive scaling for isolated unrelated nodes in a fixed authored task. Instrumented export/digest times retain the broad on/off overhead uncertainty from the preceding eight-pair control; no corrected cost is claimed.",
        "claim_boundary": "Three fresh workers per cell, one host, constant 467-edge task structure; no natural task prevalence, edge-density scaling, or general complexity law."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries}, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
