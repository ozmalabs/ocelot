#!/usr/bin/env python3
"""Analyze Reference-aware semantic structural/output parity for held-topic area-settlement arms."""
from __future__ import annotations
import gzip
import base64
import zlib
import hashlib
import json
import statistics
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/held_topic_area_settlement_parity_v1_2_20261006/capture.json.gz"
LOCK_PATH = ROOT / "evaluation/substrate_capability/held_topic_area_settlement_parity_v1_2_20261006_lock.json"
ANALYZER = Path(__file__).resolve()
OUT = ROOT / "evaluation/reports/held_topic_area_settlement_parity_v1_2_analysis_20261006.json"
ARMS = ("global", "barrier", "async")

def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

RUNNER_PATH = ROOT / "scripts/substrate_held_topic_area_settlement_parity_v1_2.py"
spec = importlib.util.spec_from_file_location("settlement_v12_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

def fixture_fingerprint_checks():
    base = {"nodes": [
        {"id": 1, "type": "Goal", "attrs": {"concept": "copper", "ts": 100}},
        {"id": 2, "type": "ThoughtManifold", "attrs": {"goal_id": {"__nid__": 1}, "manifold_id": "communication-event:#1"}},
        {"id": 3, "type": "SystemModel", "attrs": {"node_count": 2, "ts": 100, "runtime_s": 0.01}}],
        "edges": [{"src": 2, "tgt": 3, "type": "has_model", "attrs": {"w": 1}},
                  {"src": 3, "tgt": 1, "type": "about", "attrs": {}}]}
    permuted = {"nodes": [
        {"id": 90, "type": "SystemModel", "attrs": {"node_count": 2, "ts": 999, "runtime_s": 0.5}},
        {"id": 80, "type": "ThoughtManifold", "attrs": {"goal_id": {"__nid__": 70}, "manifold_id": "communication-event:#70"}},
        {"id": 70, "type": "Goal", "attrs": {"concept": "copper", "ts": 100}}],
        "edges": [{"src": 80, "tgt": 90, "type": "has_model", "attrs": {"w": 1}},
                  {"src": 90, "tgt": 70, "type": "about", "attrs": {}}]}
    def wl(graph): return runner.semantic_graph_fingerprint(graph)[0]
    direction = {"nodes": base["nodes"], "edges": [{**base["edges"][0], "src": 3, "tgt": 2}, base["edges"][1]]}
    edge_attr = {"nodes": base["nodes"], "edges": [{**base["edges"][0], "attrs": {"w": 2}}, base["edges"][1]]}
    node_attr = {"nodes": [{**base["nodes"][0], "attrs": {"concept": "basalt", "ts": 100}}, *base["nodes"][1:]], "edges": base["edges"]}
    duplicate_edge = {"nodes": base["nodes"], "edges": base["edges"] + [base["edges"][0]]}
    edge_type = {"nodes": base["nodes"], "edges": [{**base["edges"][0], "type": "different"}, base["edges"][1]]}
    return wl(base) == wl(permuted) and all(wl(base) != wl(other) for other in
        (direction, edge_attr, node_attr, duplicate_edge, edge_type))


raw = CAPTURE.read_bytes()
capture = json.loads(gzip.decompress(raw))
runs = capture["runs"]
locked = capture["locked_inputs"]
locked_sha = hashlib.sha256(json.dumps(locked, sort_keys=True,
    separators=(",", ":"), default=str).encode()).hexdigest()
checks = {
    "three_arms_nine_workers": len(runs) == 9 and all(sum(r["arm"] == arm for r in runs) == 3 for arm in ARMS),
    "nine_distinct_pids": len({r["pid"] for r in runs}) == 9,
    "capture_lock_file_matches": json.loads(LOCK_PATH.read_text()) == locked,
    "capture_source_stable": capture["post_run_inputs"] == locked and all(
        r["worker_input_sha256"] == locked_sha and r["worker_source_stable"] for r in runs),
    "seven_turns_each": all(len(r["turns"]) == 7 for r in runs),
    "id_independent_fingerprint_fixtures_pass": fixture_fingerprint_checks(),
    "fixed_hash_seed_zero": locked["design"].get("worker_environment", {}).get("PYTHONHASHSEED") == "0",
    "turn_digests_present": all("settlement_parity" in t and
        len(t["settlement_parity"]["graph_semantic_sha256"]) == 64 for r in runs for t in r["turns"]),
    "final_graph_snapshots_present": all(
        bool(r["turns"][-1]["settlement_parity"].get("snapshot_turn")) and
        bool(r["turns"][-1]["settlement_parity"].get("graph_snapshot_zlib_b64")) and
        all(t["settlement_parity"].get("graph_snapshot_zlib_b64") is None for t in r["turns"][:-1])
        for r in runs),
}

prompt_order = [turn["prompt"] for turn in runs[0]["turns"]]
per_prompt = []
for position, prompt in enumerate(prompt_order):
    by_arm = {}
    for arm in ARMS:
        rows = [r["turns"][position] for r in runs if r["arm"] == arm]
        digests = [t["settlement_parity"]["graph_semantic_sha256"] for t in rows]
        replies = [t["reply"] for t in rows]
        checks[f"{arm}_worker_graph_repeat__{position}"] = len(set(digests)) == 1
        checks[f"{arm}_worker_reply_repeat__{position}"] = len(set(replies)) == 1
        by_arm[arm] = {"graph_semantic_sha256": digests[0], "reply": replies[0],
                       "route": rows[0].get("message", {}).get("comp_dispatch_path"),
                       "graph_node_count": rows[0]["settlement_parity"]["node_count"],
                       "graph_edge_count": rows[0]["settlement_parity"]["edge_count"]}
    checks[f"arm_graph_parity__{position}"] = (len({x["graph_semantic_sha256"] for x in by_arm.values()}) == 1 and len({(x["graph_node_count"], x["graph_edge_count"]) for x in by_arm.values()}) == 1)
    checks[f"arm_reply_parity__{position}"] = len({x["reply"] for x in by_arm.values()}) == 1
    per_prompt.append({"prompt": prompt, "arms": by_arm})

for run in runs:
    if run["arm"] == "global":
        expected_areas = {"global": "global"}
    for turn_index, turn in enumerate(run["turns"]):
        calls = turn["settlement_parity"]["settlement_calls"]
        expected_mode = "global" if run["arm"] == "global" else run["arm"]
        checks[f"{run['arm']}_settlement_mode__{run['replicate']}__{turn_index}"] = all(
            call["mode"] == expected_mode for call in calls)
        if run["arm"] != "global":
            checks[f"{run['arm']}_settlement_terminates__{run['replicate']}__{turn_index}"] = all(
                not call["hit_max_rounds"] and call["rounds"] > 0 and
                call["final_residual"] == 0 for call in calls)
            assignment = turn["settlement_parity"]["area_assignments"]
            for name, area in locked["design"]["area_assignments"].items():
                checks[f"{run['arm']}_area_readback__{run['replicate']}__{turn_index}__{name}"] = (
                    assignment.get(name) == area)

graph_signatures = {arm: [] for arm in ARMS}
for arm in ARMS:
    for run in runs:
        if run["arm"] == arm:
            graph_signatures[arm].append(run["final_graph"]["semantic_wl_sha256"])
    checks[f"{arm}_final_graph_repeats"] = len(set(graph_signatures[arm])) == 1
checks["final_graph_parity_all_arms"] = len({rows[0] for rows in graph_signatures.values()}) == 1

# Task utility is a separate baseline property: preserve the known failure rather
# than treating semantic parity as positive capability evidence.
known_honest = [turn for run in runs if run["arm"] == "global" for turn in run["turns"]
                if turn["expected_path"] == "honest_capability"]
checks["known_honest_topic_limitation_reproduced"] = (
    len(known_honest) == 3 and all(turn["reply"] == "What information should I use to answer that?"
                                  for turn in known_honest))

work_summary = {}
for arm in ARMS:
    values = [turn["work"]["elapsed_ns"] for run in runs if run["arm"] == arm for turn in run["turns"]]
    work_summary[arm] = {"turn_count": len(values), "elapsed_ns_median_instrumented": statistics.median(values),
                         "elapsed_ns_min": min(values), "elapsed_ns_max": max(values)}
settlement_summary = {}
for arm in ("barrier", "async"):
    calls = [call for run in runs if run["arm"] == arm for turn in run["turns"]
             for call in turn["settlement_parity"]["settlement_calls"]]
    settlement_summary[arm] = {
        "call_count": len(calls), "rounds_total": sum(call["rounds"] for call in calls),
        "rounds_per_call_median": statistics.median(call["rounds"] for call in calls),
        "steps_total": sum(call["steps"] for call in calls),
        "max_round_count": max(call["rounds"] for call in calls),
        "all_zero_final_residual": all(call["final_residual"] == 0 for call in calls),
        "area_totals": {area: {key: sum(call["area_totals"].get(area, {}).get(key, 0)
                                        for call in calls)
                               for key in ("dirty", "attempted", "steps", "carried")}
                        for area in sorted({area for call in calls for area in call["area_totals"]})},
    }

failed = [key for key, value in checks.items() if not value]
analysis = {
    "schema_version": 2,
    "capture_path": str(CAPTURE.relative_to(ROOT)),
    "capture_sha256": hashlib.sha256(raw).hexdigest(),
    "capture_bytes_gzip": CAPTURE.stat().st_size,
    "capture_lock_sha256": digest_file(LOCK_PATH),
    "analyzer_sha256": digest_file(ANALYZER),
    "checks": checks,
    "semantic_parity_pass": all(value for key, value in checks.items()
                                 if "parity__" in key or "_worker_graph_repeat__" in key
                                 or "_worker_reply_repeat__" in key or key == "final_graph_parity_all_arms"),
    "capture_integrity_pass": all(checks[key] for key in (
        "three_arms_nine_workers", "nine_distinct_pids", "capture_lock_file_matches",
        "capture_source_stable", "seven_turns_each", "turn_digests_present",
        "final_graph_snapshots_present", "id_independent_fingerprint_fixtures_pass")),
    "all_checks_pass": not failed,
    "failed_checks": failed,
    "per_prompt": per_prompt,
    "settlement_summary": settlement_summary,
    "instrumented_turn_wall_time": work_summary,
    "interpretation": "This compares full global closure with two unlimited per-area settlement modes on one authored held-topic family. It does not test finite-budget response release, per-area priority, natural workload prevalence, or a latency claim.",
}
OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                  "capture_integrity_pass": analysis["capture_integrity_pass"],
                  "semantic_parity_pass": analysis["semantic_parity_pass"],
                  "all_checks_pass": analysis["all_checks_pass"],
                  "failed_checks": failed}, indent=2))
