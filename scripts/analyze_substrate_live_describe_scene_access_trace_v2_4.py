#!/usr/bin/env python3
"""Independent integrity and compact metric audit for live trace v2.4."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json"
SUMMARY = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_20260927.json"
OUT = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_analysis_20260927.json"
raw, summary = json.loads(RAW.read_text()), json.loads(SUMMARY.read_text())
runs = raw["runs"]
pairs = {rep: {bool(r["trace_enabled"]): r for r in runs if r["replicate"] == rep}
         for rep in {r["replicate"] for r in runs}}
semantic_keys = ("replies", "event_rows", "final", "event_order_gate", "identity_gate", "lifecycle_gate",
                 "pause_gate", "reply_parity", "whole_graph_semantic_sha256", "task_boundaries", "turn_output_evidence")
checks = {
    "six_distinct_workers_three_pairs": len(runs) == 6 and len({r["pid"] for r in runs}) == 6 and all(set(p) == {False, True} for p in pairs.values()),
    "locked_sources_stable": all(r["worker_started_inputs"] == raw["locked_inputs"] == r["worker_finished_inputs"] for r in runs) and summary["post_run_inputs"] == raw["locked_inputs"],
    "all_workers_joined_without_errors": all(r["threads_joined"] and not r["errors"] for r in runs),
    "schedule_and_request_lifecycle": all(r["b_was_serialized"] and r["pause_gate"] and not r["b_completed_while_a_blocked"] and r["event_order_gate"] and r["identity_gate"] and r["lifecycle_gate"] and r["reply_parity"] for r in runs),
    "exact_semantic_parity_within_pairs": all(all(pairs[i][True][k] == pairs[i][False][k] for k in semantic_keys) for i in pairs),
    "trace_intervals_complete_and_no_drops": all(set(r["request_traces"]) == ({"request-A", "request-B"} if r["trace_enabled"] else set()) and (not r["trace_enabled"] or all(x["event_count"] > 0 and x["dropped"] == 0 for x in r["request_traces"].values())) for r in runs),
    "trace_event_totals_reconcile": all(r["access_trace"]["event_count"] == sum(x["event_count"] for x in r["request_traces"].values()) for r in runs if r["trace_enabled"]),
    "untraced_arms_have_no_access_events": all(not r["access_trace"]["event_rows"] and r["access_trace"]["event_count"] == 0 for r in runs if not r["trace_enabled"]),
}
traced = [r for r in runs if r["trace_enabled"]]
metrics = {}
for key, name in (("a", "request-A"), ("b", "request-B")):
    metrics[name] = {
        "trace_event_counts": [r["request_traces"][name]["event_count"] for r in traced],
        "owned_node_counts": [r["task_boundaries"][key]["owned_node_count"] for r in traced],
        "owned_induced_width_upper_bounds": [r["task_boundaries"][key]["owned_induced_treewidth_upper_bound"]["value"] for r in traced],
        "boundary_incidence_counts": [r["task_boundaries"][key]["boundary_incidence_count"] for r in traced],
        "unique_external_boundary_node_counts": [r["task_boundaries"][key]["boundary_unique_external_node_count"] for r in traced],
        "public_surface_matches_graph_outbound": [r["turn_output_evidence"][name]["any_outbound_matches_public_surface"] for r in traced],
    }
scene = [r["task_boundaries"]["shared_scene_input"] for r in traced]
all_checks = all(checks.values())
out = {
    "schema_version": 1,
    "run_id": "substrate-live-describe-scene-access-trace-v2-4-independent-analysis-20260927",
    "source_raw": str(RAW.relative_to(ROOT)),
    "checks": checks,
    "all_checks_pass": all_checks,
    "classification": "valid_single_fixture_access_capture" if all_checks else "censored_or_integrity_failure",
    "per_request_metrics": metrics,
    "shared_scene_input": {
        "node_counts": [x["owned_node_count"] for x in scene],
        "boundary_incidence_counts": [x["boundary_incidence_count"] for x in scene],
        "induced_width_upper_bounds": [x["owned_induced_treewidth_upper_bound"]["value"] for x in scene],
    },
    "public_graph_output_alignment": {
        "all_traced_requests_match": all(all(v) for v in (m["public_surface_matches_graph_outbound"] for m in metrics.values())),
        "interpretation": "Public replies describe the scene and request Goals resolve, but the captured unsuppressed graph outbound Message does not match the public surface; request B has no matching outbound Message. Treat output-channel alignment as a separate capability gap.",
    },
    "timing_claim_boundary": "Do not interpret v2.4 timings as uninstrumented commodity-CPU cost: the full driver enables per-rule audit around producer callbacks and performs graph readback. The paired timings are retained only as instrumentation-context data.",
    "locality_claim_boundary": "Selected native access events and graph cut metrics cover this authored scene fixture only. Request lifecycle projections have induced-width upper bound 2 but expose 18–20 external nodes across 32–35 boundary incidences. These structural cuts do not prove dynamic computation factorizes across boundaries or that natural tasks have this distribution.",
}
OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks, "all_checks_pass": all_checks, "per_request_metrics": metrics}, indent=2))
if not all_checks:
    raise SystemExit("v2.4 independent integrity audit failed")
