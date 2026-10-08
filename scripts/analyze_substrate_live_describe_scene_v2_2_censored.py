#!/usr/bin/env python3
"""Independent integrity analysis for the censored v2.2 conversation replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_2_workers_raw_20260927.json"
SUMMARY = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_2_20260927.json"
LOCK = ROOT / "evaluation/substrate_capability/live_describe_scene_access_trace_v2_2_lock_20260927.json"
PRIOR = ROOT / "evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_2_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_2_censored_analysis_20260927.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze() -> dict:
    raw, summary, lock, prior = (json.loads(p.read_text()) for p in (RAW, SUMMARY, LOCK, PRIOR))
    runs = raw["runs"]
    locked = lock["locked_inputs"]
    pairs = {rep: {r["trace_enabled"]: r for r in runs if r["replicate"] == rep}
             for rep in (0, 1, 2)}
    reply_surfaces = sorted({surface for r in runs for surface in r["replies"].values()})
    prior_surfaces = sorted({turn["reply"] for run in prior["runs"] for turn in run["turns"]})
    changed_prior_sources = sorted(
        key for key in set(prior["locked_inputs"]["source_sha256"]) & set(locked["source_sha256"])
        if prior["locked_inputs"]["source_sha256"][key] != locked["source_sha256"][key]
    )
    checks = {
        "snapshot_lock_matches_driver_and_raw": (
            summary["locked_inputs"] == locked == raw["locked_inputs"]
        ),
        "snapshot_stable_through_all_workers": (
            summary["post_run_inputs"] == locked
            and all(r["worker_started_inputs"] == locked == r["worker_finished_inputs"] for r in runs)
        ),
        "six_workers_and_three_pairs": (
            len(runs) == 6 and len({r["pid"] for r in runs}) == 6
            and all(set(pairs[rep]) == {True, False} for rep in pairs)
        ),
        "paired_semantic_graph_parity": all(
            pairs[rep][True]["whole_graph_semantic_sha256"]
            == pairs[rep][False]["whole_graph_semantic_sha256"]
            and pairs[rep][True]["task_boundaries"] == pairs[rep][False]["task_boundaries"]
            for rep in pairs
        ),
        "shared_scene_input_shape_reconciles": all(
            r["task_boundaries"]["shared_scene_input_node_types"] == {"Percept": 3, "Scene": 1}
            and r["task_boundaries"]["shared_scene_input"]["owned_node_count"] == 4
            for r in runs
        ),
        "worker_threads_joined": all(r["threads_joined"] for r in runs),
        "all_workers_censored_before_selection": all(
            "A selection timeout" in r["errors"]
            and not r["identity_gate"] and not r["lifecycle_gate"]
            for r in runs
        ),
        "same_unknown_command_reply_in_all_workers": (
            reply_surfaces == ["I don't know 'describe' — what does it mean?"]
        ),
        "no_goal_producer_events": all(not r["producer_work"] and not r["final"]["a"] and not r["final"]["b"] for r in runs),
        "prior_same_prompt_capture_was_successful": (
            all(prior["checks"].values())
            and prior_surfaces == ["I see the grey thing stays, the yellow counter, and the blue thing moves."]
        ),
        "prior_and_current_source_locks_differ": bool(changed_prior_sources),
        "driver_failed_expected_behavior_gates": (
            not summary["checks"]["schedule_and_lifecycle_gates_both_arms"]
            and not summary["checks"]["all_threads_joined_without_errors"]
        ),
    }
    report = {
        "schema_version": 1,
        "run_id": "substrate-live-describe-scene-v2-2-censored-analysis-20260927",
        "status": "censored_behavioral_gate_failure",
        "claim_boundary": (
            "An isolated, source-stable snapshot completed all six processes and preserved paired final graph "
            "parity, but every worker timed out before request A emitted selection. The scene input projection "
            "is structurally present, but no successful conversation lifecycle was measured. This analysis "
            "does not treat event counts, timing, or the fixture as a valid locality result."
        ),
        "input_sha256": {"raw": sha(RAW), "summary": sha(SUMMARY), "lock": sha(LOCK)},
        "checks": checks,
        "shared_scene_input_types": runs[0]["task_boundaries"]["shared_scene_input_node_types"],
        "workers": len(runs),
        "selection_timeouts": sum("A selection timeout" in r["errors"] for r in runs),
        "reply_surfaces": reply_surfaces,
        "prior_successful_reply_surfaces": prior_surfaces,
        "prior_capture_run_id": prior["run_id"],
        "changed_shared_source_lock_keys_vs_prior": changed_prior_sources,
        "cross_version_interpretation": "same prompt succeeded in the earlier locked state; the later locked state fails it, but multiple source inputs differ, so this is an observed state-dependent capability discrepancy, not causal attribution to any one edit",
        "goal_producer_events": sum(len(r["producer_work"]) for r in runs),
        "semantic_parity_pairs": sum(
            pairs[rep][True]["whole_graph_semantic_sha256"] == pairs[rep][False]["whole_graph_semantic_sha256"]
            for rep in pairs
        ),
        "trace_event_counts_are_not_reported": True,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


if __name__ == "__main__":
    result = analyze()
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "status": result["status"],
                      "checks": result["checks"], "selection_timeouts": result["selection_timeouts"]}, indent=2))
    if not all(result["checks"].values()):
        raise SystemExit("censored-run integrity analysis failed")
