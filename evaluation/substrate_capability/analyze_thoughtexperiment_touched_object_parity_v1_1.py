#!/usr/bin/env python3
"""Independently score exact full-state and touched-object parity measurements."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_touched_object_parity_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_touched_object_parity_v1_1_lock_20261004.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_touched_object_parity_v1_1_20261004.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_touched_object_parity_v1_1_analysis_20261004.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_1_analysis_20261004.json"
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def load_runner():
    spec = importlib.util.spec_from_file_location("touched_object_parity_runner_analysis", RUNNER)
    mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod); return mod


def median(xs): return statistics.median(xs) if xs else None


def main():
    capture, lock, runner = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text()), load_runner()
    rows, configs, current = capture.get("runs", []), runner.configurations(), runner.locked_inputs()
    expected = {(c["noise_nodes"], c["backend"], c["replicate"]) for c in configs}
    observed = {(r["configuration"]["noise_nodes"], r["configuration"]["backend"], r["configuration"]["replicate"]) for r in rows}
    checks = {
        "lock_matches_recomputed_sources": lock.get("locked_inputs") == capture.get("locked_inputs") == current,
        "postrun_sources_stable": capture.get("source_stable") is True and capture.get("post_run_locked_inputs") == current,
        "exact_18_cell_schedule": capture.get("configurations") == configs and len(rows) == 18 and observed == expected,
        "no_failures_unique_pids": capture.get("worker_failures") == [] and len({r["pid"] for r in rows}) == 18,
        "exact_node_edge_counts": all(r["node_count"] == r["configuration"]["noise_nodes"] + 511 and r["edge_count"] == 467 for r in rows),
        "one_correct_candidate_and_oracle_parity": all(len(r["valid_candidate_ids"]) == 1
            and r["selected_candidate_id"] == r["correct_candidate_position"]
            and r["selected_branch_matches_monolithic_oracle"] and r["primary_matches_monolithic_oracle"]
            and r["oracle_grounded_frame_count"] == 4 and r["oracle_grounded_evidence_exact"] for r in rows),
        "primary_isolation_rules_and_stale_retry": all(r["primary_unchanged_before_return"]
            and r["returned_branch_matches"] and r["all_primary_rules_preserved"]
            and r["stale_residual_rejected"] and r["stale_retry_left_primary_unchanged"] for r in rows),
        "all_candidate_semantics_and_quiescence": all(len(r["candidate_outcomes"]) == 4
            and sum(c["grounding_status"] == "candidate_grounded" and c["evidence"] == EVIDENCE for c in r["candidate_outcomes"]) == 1
            and all(c["quiescent"] and c["terminal_zero_progress_sweep"] for c in r["candidate_outcomes"])
            and all(c["grounding_status"] == "unresolved" for c in r["candidate_outcomes"]
                    if c["candidate_id"] != r["correct_candidate_position"]) for r in rows),
        "touched_reconstruction_matches_every_worker": all(r["audit_measurements"]["touched_projection"]["supported"]
            and r["audit_measurements"]["touched_projection"]["matched"]
            and not r["audit_measurements"]["touched_projection"]["unsupported"]
            and r["audit_measurements"]["touched_projection"]["changed_nodes"] == 1 for r in rows),
        "all_delta_rows_are_node_change_only": all(all(c["residual_total_counts"][key] == 0
            for key in ("nodes_added", "nodes_removed", "edges_added", "edges_changed", "edges_removed"))
            and c["residual_total_counts"]["nodes_changed"] == 1 for r in rows for c in r["candidate_outcomes"]),
        "six_untracked_mutation_falsifiers": sum(r["audit_measurements"]["untracked_mutation_falsifier"] is not None
            for r in rows) == 6 and all(r["audit_measurements"]["untracked_mutation_falsifier"]["touched_projection_passes"]
            and r["audit_measurements"]["untracked_mutation_falsifier"]["exact_global_digest_detects_mutation"]
            for r in rows if r["audit_measurements"]["untracked_mutation_falsifier"] is not None),
        "original_five_export_digest_lifecycle_and_conservation": all(
            r["cost_breakdown_in_lifecycle"]["graph_export_calls"] == 5
            and r["cost_breakdown_in_lifecycle"]["canonical_digest_calls"] == 5
            and r["lifecycle_wall_ns"] >= sum(r["phase_ns"].values())
                + r["cost_breakdown_in_lifecycle"]["graph_export_ns"]
                + r["cost_breakdown_in_lifecycle"]["canonical_digest_ns"] for r in rows),
        "exact_audit_call_indices_recorded": all(len(r["audit_measurements"]["all_graph_export_ns"]) in (8, 10)
            and len(r["audit_measurements"]["all_digest_ns"]) in (8, 10)
            and all(r["audit_measurements"]["exact_full_parity_audit"][key] >= 0 for key in (
                "selected_branch_export_ns", "returned_primary_export_ns", "selected_branch_digest_ns", "returned_primary_digest_ns"))
            for r in rows),
    }
    base = json.loads(BASE_ANALYSIS.read_text())["summaries"]
    summaries = {}
    for backend in ("full_copy", "shared_graph_pages"):
        summaries[backend] = {}
        for size in (10_000, 100_000, 200_000):
            group = [r for r in rows if r["configuration"]["backend"] == backend and r["configuration"]["noise_nodes"] == size]
            checks[f"{backend}_{size}_three_replicates"] = len(group) == 3
            full = lambda r: sum(r["audit_measurements"]["exact_full_parity_audit"].values()) / 1e6
            touched = lambda r: (r["audit_measurements"]["touched_preimage_capture_ns"]
                                 + r["audit_measurements"]["touched_projection_validation_ns"]) / 1e6
            values = {"workers": len(group), "nodes": median([r["node_count"] for r in group]),
                "edges": median([r["edge_count"] for r in group]), "full_exact_parity_audit_ms": median([full(r) for r in group]),
                "touched_preimage_ms": median([r["audit_measurements"]["touched_preimage_capture_ns"] / 1e6 for r in group]),
                "touched_projection_ms": median([r["audit_measurements"]["touched_projection_validation_ns"] / 1e6 for r in group]),
                "touched_total_ms": median([touched(r) for r in group]),
                "full_to_touched_ratio": median([full(r) / max(touched(r), 1e-9) for r in group]),
                "full_copy_fork_ms": median([r["phase_ns"]["candidate_forks_total"] / 1e6 for r in group]),
                "full_graph_exports_ms": median([r["audit_measurements"]["exact_full_parity_audit"]["selected_branch_export_ns"] / 1e6
                    + r["audit_measurements"]["exact_full_parity_audit"]["returned_primary_export_ns"] / 1e6 for r in group]),
                "full_graph_digests_ms": median([r["audit_measurements"]["exact_full_parity_audit"]["selected_branch_digest_ns"] / 1e6
                    + r["audit_measurements"]["exact_full_parity_audit"]["returned_primary_digest_ns"] / 1e6 for r in group]),
                "median_lifecycle_ms": median([r["lifecycle_wall_ns"] / 1e6 for r in group])}
            old = base[backend]["by_noise_nodes"][str(size)]
            values["baseline_lifecycle_ms"] = old["median_lifecycle_ms"]
            summaries[backend][size] = values
    result = {"schema": "ThoughtexperimentTouchedObjectParityV1_1Analysis", "capture_sha256": sha(CAPTURE),
        "analysis_script_sha256": sha(Path(__file__)), "checks": checks, "summaries": summaries,
        "interpretation": "On the current one-node-change residual, reconstruction and equality of the complete touched node state can be checked from its before-image plus journal patch at cost dependent on that touched object, while exact branch-primary parity exports and hashes the whole graph. The untracked-mutation controls are required to interpret this as a local consistency check: the touched projection passes despite unrelated corruption that the full digest detects.",
        "claim_boundary": "One current predecessor-fanout task, node changes only, 10k/100k/200k unrelated nodes, two snapshot backends, and three fresh workers per cell. This is not a general replacement for exact graph parity; adds/removes and edge mutations are deliberately rejected as unsupported."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "summaries": summaries}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__": raise SystemExit(main())
