#!/usr/bin/env python3
"""Validate task-oracle and semantic parity for the task-receipt transfer panel."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/thoughtexperiment_task_generated_receipt_transfer_v1_raw_20261001.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_task_generated_receipt_transfer_v1_analysis_20261001.json"
ARMS = ("direct", "eager_receipt", "shared_snapshot_receipt")
EXPECTED_PATHS = {"0": [4, 5, 6], "1": [7, 8, 9]}
EXPECTED_GROUNDS = [["calendar_checked", "location_shared"],
                    ["calendar_request", "calendar_shared"]]


def main() -> int:
    capture = json.loads(RAW.read_text())
    if capture.get("schema") != "ThoughtexperimentTaskReceiptTransferV1Capture":
        raise SystemExit("unexpected capture schema")
    runs = capture["runs"]
    lock = capture["locked_inputs"]
    if len(runs) != 8 or any("worker_error" in row for row in runs):
        raise SystemExit("capture does not contain eight successful workers")
    if len({row["pid"] for row in runs}) != 8:
        raise SystemExit("worker PIDs are not unique")
    if capture["post_run_inputs"] != lock:
        raise SystemExit("input/native fingerprints changed during capture")
    cell_times = {arm: [] for arm in ARMS}
    stage_times = {arm: {key: [] for key in
                         ("adapter_seed_setup_ns", "event_construction_ns", "branch_setup_ns",
                          "rule_closure_ns", "journal_readout_ns", "receipt_adoption_ns",
                          "terminal_probe_ns")} for arm in ARMS}
    order_mismatches = {arm: 0 for arm in ARMS if arm != "direct"}
    order_comparisons = {arm: 0 for arm in ARMS if arm != "direct"}
    nonempty_receipt_counts = {arm: 0 for arm in ARMS if arm != "direct"}
    total_receipt_effects = {arm: 0 for arm in ARMS if arm != "direct"}
    all_event_pairs = 0

    for run in runs:
        if run["before"] != lock or run["after"] != lock:
            raise SystemExit(f"worker source/native fingerprint drift: rep {run['replicate']}")
        episodes = {row["arm"]: row for row in run["episodes"]}
        if set(episodes) != set(ARMS) or run["arm_order"] != [x["arm"] for x in run["episodes"]]:
            raise SystemExit("worker arm order/coverage mismatch")
        direct = episodes["direct"]
        for arm, episode in episodes.items():
            if episode["pid"] != run["pid"] or episode["replicate"] != run["replicate"]:
                raise SystemExit("episode identity does not match worker")
            if episode["loaded_seed_ids"] != direct["loaded_seed_ids"]:
                raise SystemExit("seed identity mismatch across arms")
            if episode["active_lifecycle_rules"] != ["discourse_goal_execute",
                                                       "discourse_goal_resolve",
                                                       "discourse_goal_select"]:
                raise SystemExit(f"active discourse rule gate failed: {episode['active_lifecycle_rules']}")
            if episode["event_ids"] != direct["event_ids"] or len(episode["event_ids"]) != 10:
                raise SystemExit("event identity/coverage mismatch")
            if episode["goal_ids"] != direct["goal_ids"] or len(episode["goal_ids"]) != 2:
                raise SystemExit("goal identity/coverage mismatch")
            if episode["goal_paths"] != EXPECTED_PATHS:
                raise SystemExit(f"task path oracle failed for {arm}: {episode['goal_paths']}")
            if episode["common_grounds"] != EXPECTED_GROUNDS:
                raise SystemExit(f"common-ground oracle failed for {arm}: {episode['common_grounds']}")
            if episode["terminal_progress_steps"] != 0 or not episode["terminal_graph_unchanged"]:
                raise SystemExit(f"terminal fixed-point gate failed for {arm}")
            if len(episode["event_states"]) != 10:
                raise SystemExit("missing per-event canonical state digest")
            if episode["event_progress_steps"] != direct["event_progress_steps"]:
                raise SystemExit(f"per-event closure work diverged for {arm}")
            for left, right in zip(direct["event_states"], episode["event_states"]):
                if left["event_index"] != right["event_index"] or \
                        left["canonical_graph_sha256"] != right["canonical_graph_sha256"]:
                    raise SystemExit(f"per-event canonical graph mismatch: rep={run['replicate']} arm={arm}")
                all_event_pairs += int(arm != "direct")
                if arm != "direct":
                    order_comparisons[arm] += 1
                    order_mismatches[arm] += int(left["wire_graph_sha256"] != right["wire_graph_sha256"])
                    if not right["adopted_primary_matches_branch"]:
                        raise SystemExit(f"receipt adoption failed branch-state parity: rep={run['replicate']} event={right['event_index']}")
            if arm != "direct":
                if len(episode["receipts"]) != 10 or not episode["all_adopted_primaries_match_branch"]:
                    raise SystemExit(f"receipt coverage/adoption gate failed for {arm}")
                effects = [sum(row["effect_counts"].values()) for row in episode["receipts"]]
                nonempty_receipt_counts[arm] += sum(count > 0 for count in effects)
                total_receipt_effects[arm] += sum(effects)
            cell_times[arm].append(episode["measured_route_wall_ns"] / 1e6)
            for key, value in episode["stage_wall_ns"].items():
                stage_times[arm][key].append(value / 1e6)

        for arm in ARMS[1:]:
            if episodes[arm]["final_canonical_graph_sha256"] != direct["final_canonical_graph_sha256"]:
                raise SystemExit(f"final canonical graph mismatch for {arm}")

    medians = {arm: {"measured_route_wall_ms_median": statistics.median(cell_times[arm]),
                     "measured_route_wall_ms_min": min(cell_times[arm]),
                     "measured_route_wall_ms_max": max(cell_times[arm]),
                     "stage_wall_ms_medians": {key: statistics.median(vals)
                                               for key, vals in stage_times[arm].items()}}
               for arm in ARMS}
    result = {
        "schema": "ThoughtexperimentTaskReceiptTransferV1Analysis",
        "raw_capture": str(RAW.relative_to(ROOT)),
        "workers": len(runs), "episodes": len(runs) * len(ARMS),
        "per_event_canonical_comparisons": all_event_pairs,
        "gates": {"unique_fresh_worker_pids": True,
                  "source_native_fingerprints_stable": True,
                  "ten_event_two_goal_task_oracles_all_arms": True,
                  "per_event_closure_and_canonical_state_parity": True,
                  "receipt_primary_matches_producing_branch": True,
                  "terminal_no_progress_and_primary_unchanged": True,
                  "serialized_wire_order_reported_separately": True},
        "timing": medians,
        "wire_order": {arm: {"comparisons": order_comparisons[arm],
                              "mismatches_vs_direct": order_mismatches[arm]}
                       for arm in order_mismatches},
        "receipt_activity": {arm: {"nonempty_event_receipts": nonempty_receipt_counts[arm],
                                    "total_recorded_effects": total_receipt_effects[arm]}
                             for arm in nonempty_receipt_counts},
        "limits": ["one existing authored task fixture", "not a natural-task distribution",
                   "canonical graph facts match; serialized edge order may differ",
                   "does not measure concurrent adoption or serving-runtime compatibility"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "episodes": len(runs) * len(ARMS),
                      "all_gates_pass": True, "wire_order_mismatches": order_mismatches,
                      "analysis": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
