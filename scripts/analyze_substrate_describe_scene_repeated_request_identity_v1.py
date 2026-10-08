#!/usr/bin/env python3
"""Independent structural analysis for the describe-scene repeated-request capture."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_describe_scene_repeated_request_identity_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_repeated_request_identity_v1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_describe_scene_repeated_request_identity_v1_analysis_20260926.json"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def shape(run):
    return [{
        "turn": t["turn"], "route": t["route"], "reply_nonempty": t["reply_nonempty"],
        "origin_event_kind": t["origin_event_kind"], "state_event_kinds": t["state_event_kinds"],
        "new_goal_count": len(t["new_goal_ids"]), "matching_goal_count": len(t["matching_goal_ids"]),
        "scene_parent_count": len(t["scene_parent_ids"]), "lifecycle_event_count": t["lifecycle_event_count"],
        "matching_goal_shapes": [{
            "kind": g["attrs"].get("kind"), "comprehended_message_count": len(g["comprehended_message_ids"]),
            "origin_event_count": len(g["origin_event_ids"]), "subgoal_count": len(g["subgoal_ids"]),
        } for g in t["matching_goals"]],
    } for t in run["turns"]]

def main():
    raw = json.loads(RAW.read_text()); lock = json.loads(LOCK.read_text())
    gate_details = []
    for run in raw["runs"]:
        turns = run["turns"]
        reused_parent = (len(turns) == 2 and turns[0]["matching_goal_ids"] == turns[1]["matching_goal_ids"]
                         and len(turns[0]["matching_goal_ids"]) == 1)
        shared_comprehension = (len(turns) == 2 and len(turns[1]["matching_goals"]) == 1
            and len(turns[1]["matching_goals"][0]["comprehended_message_ids"]) == 2)
        missing_origin = all(not g["origin_event_ids"] for t in turns for g in t["matching_goals"])
        gate_details.append({"pid": run["pid"], "distinct_parent_identity": run["distinct_parent_identity"],
            "reused_same_parent_goal": reused_parent, "second_goal_comprehends_both_messages": shared_comprehension,
            "parent_originated_in_no_event": missing_origin,
            "no_lifecycle_events": all(t["lifecycle_event_count"] == 0 for t in turns),
            "two_replies_nonempty": run["both_replies_nonempty"]})
    stable = len({json.dumps(shape(r), sort_keys=True) for r in raw["runs"]}) == 1
    checks = {
        "raw_capture_lock_sha256_matches": raw["lock_sha256"] == sha(LOCK),
        "raw_lock_equals_lock_file": raw["locked_inputs"] == lock.get("locked_inputs"),
        "three_distinct_fresh_processes": len(raw["runs"]) == 3 and len({r["pid"] for r in raw["runs"]}) == 3,
        "source_stable_all_workers_and_postrun": raw["post_run_inputs"] == raw["locked_inputs"] and all(
            r["worker_started_inputs"] == raw["locked_inputs"] and r["worker_finished_inputs"] == raw["locked_inputs"] for r in raw["runs"]),
        "two_replies_nonempty_each_worker": all(x["two_replies_nonempty"] for x in gate_details),
        "replicated_identity_failure_shape": all(x["reused_same_parent_goal"] and
            x["second_goal_comprehends_both_messages"] and x["parent_originated_in_no_event"] for x in gate_details),
        "no_goal_bound_lifecycle_events": all(x["no_lifecycle_events"] for x in gate_details),
        "normalized_graph_shape_repeats": stable,
    }
    analysis = {"schema_version": 1, "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "checks": checks, "replicates": gate_details,
        "normalized_shape": shape(raw["runs"][0]) if raw["runs"] else [],
        "summary": raw.get("summary", {}),
        "interpretation": "The attached-scene describe route returns replies but reuses one scene-level parent Goal for both sequential requests. The Goal comprehends both Messages, has no originated_in event edge, and receives no Goal-bound lifecycle events. This is a replicated identity failure for this route and fixture; it does not establish concurrent behavior."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks}, indent=2))
    if not all(checks.values()): raise SystemExit("independent analysis validity check failed")

if __name__ == "__main__": main()
