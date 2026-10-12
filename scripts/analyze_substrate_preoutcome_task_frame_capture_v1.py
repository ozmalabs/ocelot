#!/usr/bin/env python3
"""Independent summary and gate analysis for pre-outcome frame capture v1."""
from __future__ import annotations
import gzip
import json
import statistics
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/preoutcome_task_frame_capture_v1_20261005/capture.json.gz"
OUT = ROOT / "evaluation/reports/preoutcome_task_frame_capture_v1_analysis_20261005.json"
BASE_PATH = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"

spec = importlib.util.spec_from_file_location("held_topic_base_v1_6", BASE_PATH)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
data = json.loads(gzip.decompress(CAPTURE.read_bytes()))
runs = data["runs"]
checks = {}
checks["three_workers"] = len(runs) == 3
checks["three_fresh_pids"] = len({run["pid"] for run in runs}) == 3
checks["source_lock_stable"] = data["locked_inputs"] == data["post_run_inputs"]
checks["all_capture_trace_gates"] = all(run["preoutcome_capture_gate"] for run in runs)
checks["seven_turns_each"] = all(len(run["turns"]) == 7 for run in runs)
checks["checkpoint_turn_trace_alignment"] = all(
    len(run["turns"]) == 7 and all("preoutcome_frame" in t and "postcheckpoint_rule_access" in t
                                     for t in run["turns"]) for run in runs)

prompt_summaries = []
for turn0 in runs[0]["turns"]:
    prompt = turn0["prompt"]
    rows = [turn for run in runs for turn in run["turns"] if turn["prompt"] == prompt]
    frames = [turn["preoutcome_frame"] for turn in rows]
    traces = [turn["postcheckpoint_rule_access"] for turn in rows]
    structural_signatures = {
        json.dumps({key: frame[key] for key in (
            "owned_node_count", "owned_type_counts", "boundary_unique_external_node_count",
            "boundary_external_type_counts", "boundary_incidence_count",
            "boundary_edge_type_counts", "internal_edge_count",
            "owned_induced_state_treewidth_upper_bound")}, sort_keys=True)
        for frame in frames}
    checks[f"frame_structure_repeats__{prompt}"] = len(structural_signatures) == 1
    prompt_summaries.append({
        "prompt": prompt,
        "replicate_count": len(rows),
        "owned_nodes": [f["owned_node_count"] for f in frames],
        "owned_induced_state_treewidth_upper_bound": [
            f["owned_induced_state_treewidth_upper_bound"]["value"] for f in frames],
        "boundary_incidences": [f["boundary_incidence_count"] for f in frames],
        "distinct_external_boundary_nodes": [f["boundary_unique_external_node_count"] for f in frames],
        "postcheckpoint_native_access_events": [t["event_count"] for t in traces],
        "touched_frame_nodes": [t["touched_nodes_by_scope"]["frame"] for t in traces],
        "touched_direct_boundary_nodes": [t["touched_nodes_by_scope"]["boundary_external"] for t in traces],
        "touched_outside_cut_nodes": [t["touched_nodes_by_scope"]["outside_cut"] for t in traces],
        "dropped_trace_rows": [t["dropped"] for t in traces],
        "unmapped_rule_uids": [t["unmapped_rule_uids"] for t in traces],
        "reply_signatures": sorted({turn["reply"] for turn in rows}),
        "structural_signature_repeats": len(structural_signatures) == 1,
    })

for run in runs:
    for teach in run["teaching"]:
        checks[f"worker{run['replicate']}_teaching_{teach['topic']}"] = (
            teach["returned_answer"] == teach["expected_answer"])
    for turn in run["turns"]:
        topic = turn["expected_topic"]
        prefix = f"worker{run['replicate']}__{turn['prompt']}"
        dispatch = (turn["comprehension"] or {}).get("dispatch", {})
        if topic not in {"unobtainium", "localhitium"}:
            held = turn["held_answers"]
            goal_ok = (len(turn["answer_topic_goal_ids"]) == 1 and len(turn["goals"]) == 1
                       and turn["goals"][0]["attrs"].get("concept") == topic)
            receipt_ok = any(receipt["attrs"].get("status") == "released"
                             and receipt["attrs"].get("surface") == turn["reply"]
                             and any(node in receipt["released_ids"] for node in
                                     turn["answer_topic_goal_ids"] + turn["held_answer_ids"])
                             for receipt in turn["receipts"])
            checks[prefix + "__supported_answer_released"] = (
                turn["reply"] == base.FACTS[topic] and len(held) == 1
                and held[0]["attrs"].get("text") == base.FACTS[topic]
                and held[0]["attrs"].get("grounding_referent") == topic
                and held[0]["attrs"].get("grounding_status") == "supported"
                and len(turn["evidence"]) >= 1 and goal_ok and receipt_ok
                and dispatch.get("path") == turn["expected_path"])
        elif topic == "unobtainium":
            checks[prefix + "__unknown_topic_unresolved"] = (
                len(turn["answer_topic_goal_ids"]) == 1 and len(turn["grounder_calls"]) >= 1
                and turn["grounder_calls"][0]["phrase"].lower() == topic
                and turn["goals"][0]["attrs"].get("outcome") == "unresolved"
                and topic in turn["reply"].lower() and dispatch.get("path") == turn["expected_path"])
        else:
            expected = base.LOCAL_HIT_ANSWER
            checks[prefix + "__injected_local_hit_released"] = (
                turn["reply"] == expected and len(turn["grounder_calls"]) == 1
                and turn["grounder_calls"][0].get("injected_local_hit") is True
                and len(turn["held_answers"]) == 1
                and turn["held_answers"][0]["attrs"].get("text") == expected
                and turn["held_answers"][0]["attrs"].get("grounding_status") == "supported"
                and len(turn["evidence"]) >= 1 and turn["goals"][0]["attrs"].get("outcome") == "resolved"
                and any(receipt["attrs"].get("status") == "released"
                        and receipt["attrs"].get("surface") == expected for receipt in turn["receipts"])
                and dispatch.get("path") == turn["expected_path"])

trace_counts = [turn["postcheckpoint_rule_access"]["event_count"]
                for run in runs for turn in run["turns"]]
summary = {
    "schema_version": 1,
    "capture_path": str(CAPTURE.relative_to(ROOT)),
    "capture_bytes_gzip": CAPTURE.stat().st_size,
    "workers": len(runs),
    "turns": sum(len(run["turns"]) for run in runs),
    "checks": checks,
    "capture_integrity_pass": all(checks[k] for k in (
        "three_workers", "three_fresh_pids", "source_lock_stable", "all_capture_trace_gates",
        "seven_turns_each", "checkpoint_turn_trace_alignment")),
    "utility_gate_pass": all(value for key, value in checks.items()
                              if "supported_answer_released" in key or "unknown_topic_unresolved" in key
                              or "injected_local_hit_released" in key),
    "prompt_summaries": prompt_summaries,
    "postcheckpoint_native_access_event_count": {
        "min": min(trace_counts), "median": statistics.median(trace_counts),
        "max": max(trace_counts), "total": sum(trace_counts)},
    "interpretation": "Prospective ingress-frame and native access-trace capture on one authored held-topic family; does not establish natural prevalence, factor interfaces, or partitioned execution parity.",
}
OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                  "capture_integrity_pass": summary["capture_integrity_pass"],
                  "utility_gate_pass": summary["utility_gate_pass"],
                  "failed_checks": [key for key, value in checks.items() if not value]}, indent=2))
