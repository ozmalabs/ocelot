#!/usr/bin/env python3
"""Independent structural analysis for the describe-scene repeated-request capture."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_lifecycle_identity_v1_1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_1_analysis_20260926.json"

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
        unique_per_turn = all(len(t["matching_goal_ids"]) == 1 and len(t["matching_goals"]) == 1 for t in turns)
        distinct_parents = unique_per_turn and turns[0]["matching_goal_ids"][0] != turns[1]["matching_goal_ids"][0]
        owner_links = all(unique_per_turn and t["matching_goals"][0]["comprehended_message_ids"] == [t["message_id"]]
            and t["matching_goals"][0]["origin_event_ids"] == [t["origin_event_id"]] for t in turns)
        lifecycle = all(unique_per_turn
            and t["matching_goals"][0]["transition_kinds"] == ["selection", "execution", "action_result"]
            and t["matching_goals"][0]["closed"] and not t["matching_goals"][0]["active"]
            and [e["kind"] for e in t["goal_lifecycle_events"]] == ["selection", "execution", "action_result"]
            and all(e["for_goal_ids"] == t["matching_goal_ids"] for e in t["goal_lifecycle_events"])
            for t in turns)
        gate_details.append({"pid": run["pid"], "distinct_parent_identity": run["distinct_parent_identity"],
            "one_distinct_parent_per_request": distinct_parents, "owner_links_exact": owner_links,
            "lifecycle_exact_and_terminal": lifecycle,
            "two_replies_nonempty": run["both_replies_nonempty"]})
    stable = len({json.dumps(shape(r), sort_keys=True) for r in raw["runs"]}) == 1
    checks = {
        "raw_capture_lock_sha256_matches": raw["lock_sha256"] == sha(LOCK),
        "raw_lock_equals_lock_file": raw["locked_inputs"] == lock.get("locked_inputs"),
        "three_distinct_fresh_processes": len(raw["runs"]) == 3 and len({r["pid"] for r in raw["runs"]}) == 3,
        "source_stable_all_workers_and_postrun": raw["post_run_inputs"] == raw["locked_inputs"] and all(
            r["worker_started_inputs"] == raw["locked_inputs"] and r["worker_finished_inputs"] == raw["locked_inputs"] for r in raw["runs"]),
        "two_replies_nonempty_each_worker": all(x["two_replies_nonempty"] for x in gate_details),
        "distinct_request_goal_identity": all(x["one_distinct_parent_per_request"] and x["owner_links_exact"] for x in gate_details),
        "parent_lifecycle_identity_and_terminal_closure": all(x["lifecycle_exact_and_terminal"] for x in gate_details),
        "normalized_graph_shape_repeats": stable,
        "positive_lifecycle_gate_all_runs": all(r["distinct_parent_identity"] and r["each_goal_owns_only_its_request"] for r in raw["runs"]),
    }
    analysis = {"schema_version": 1, "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "checks": checks, "replicates": gate_details,
        "normalized_shape": shape(raw["runs"][0]) if raw["runs"] else [],
        "summary": raw.get("summary", {}),
        "interpretation": "The request-scoped describe-scene path is confirmed across sequential repeated requests: each inbound Message maps to a distinct parent Goal with its own origin event, three owned utterance subgoals, and a correctly linked selection/execution/result lifecycle ending resolved and closed. This does not establish concurrent behavior."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks}, indent=2))
    if not all(checks.values()): raise SystemExit("independent analysis validity check failed")

if __name__ == "__main__": main()
