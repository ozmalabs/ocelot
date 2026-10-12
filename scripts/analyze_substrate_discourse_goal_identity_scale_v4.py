#!/usr/bin/env python3
"""Independent gate and counter reconstruction for v4 goal identity scaling."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_discourse_goal_identity_scale_v4_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/discourse_goal_identity_scale_v4_lock_20260926.json"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_goal_identity_scale_v4_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cost_metrics(run: dict) -> dict:
    counters = {}
    for cp in run["checkpoints"]:
        for key, value in cp["settlement"].get("counters", {}).items():
            counters[key] = counters.get(key, 0) + int(value)
    return {"candidate_pairs": counters.get("cand_tested", 0),
            "term_evaluations": counters.get("term_evals_total", 0),
            "wall_ns": sum(int(cp["settlement"].get("wall_ns", 0)) for cp in run["checkpoints"]),
            "cpu_ns": sum(int(cp["settlement"].get("cpu_ns", 0)) for cp in run["checkpoints"]),
            "peak_rss_kib": run["peak_rss_kib"], "frame_setup_ns": run["frame_setup_ns"]}


def main() -> None:
    raw = json.loads(RAW.read_text())
    fixture = json.loads(FIXTURE.read_text())
    runs = raw["runs"]
    by_key = {(int(r["size"]), r["arm"]): r for r in runs}
    reconstructed = {}; gates = {}
    for size in fixture["goal_counts"]:
        size = int(size)
        temporal = by_key[(size, "temporal_full")]
        recipient = by_key[(size, "recipient_guard_full")]
        explicit = by_key[(size, "explicit_full")]
        owner = by_key[(size, "explicit_owner_queue")]
        omitted = by_key[(size, "explicit_omit_wakeup")]
        expected = {str(i): [size + 3 * i + j for j in range(3)] for i in range(size)}
        path = lambda run: {goal: info["transition_event_indices"]
                            for goal, info in run["final_goals"].items()}
        owner_parity = [a["graph_digest"] == b["graph_digest"]
                        for a, b in zip(explicit["checkpoints"], owner["checkpoints"])]
        omission = [i for i, (a, b) in enumerate(zip(explicit["checkpoints"],
                                                     omitted["checkpoints"]))
                    if a["graph_digest"] != b["graph_digest"]]
        notification_rows = []
        for cp in owner["checkpoints"]:
            for call in cp["settlement"].get("notifications", []):
                notification_rows.extend((cp["event_index"], int(target))
                    for target in call["native_owners"] if int(target) != call["source_frame"])
        omitted_receipts_at_results = all(
            omitted["checkpoints"][size + 3 * i + 2]["origin_receipts"].get(str(i)) == 0.0
            for i in range(size))
        counter = {}
        for cp in owner["checkpoints"]:
            for key, value in cp["settlement"].get("counters", {}).items():
                counter[key] = counter.get(key, 0) + int(value)
        expected_cost = {"candidate_pairs": counter.get("cand_tested", 0),
                         "term_evaluations": counter.get("term_evals_total", 0),
                         "queue_turns": sum(cp["settlement"].get("turns", 0)
                                             for cp in owner["checkpoints"]),
                         "frame_setup_ns": owner["frame_setup_ns"],
                         "peak_rss_kib": owner["peak_rss_kib"],
                         "cpu_ns_total": sum(int(cp["settlement"].get("cpu_ns", 0))
                                              for cp in owner["checkpoints"])}
        reported_cost = raw["summary"][str(size)]["cost_by_arm"]["explicit_owner_queue"]
        gates[str(size)] = {
            "event_and_frame_counts_recompute": len(explicit["checkpoints"]) == 4 * size
                and explicit["frame_count"] == 2 * size and explicit["task_link_edges"] == 3 * size,
            "all_global_arms_fixed_points": all(cp["complete"] for arm in (temporal, recipient, explicit)
                                                 for cp in arm["checkpoints"]),
            "explicit_full_and_owner_match_task_oracle": path(explicit) == expected
                and path(owner) == expected,
            "temporal_and_recipient_controls_fail_task_oracle": path(temporal) != expected
                and path(recipient) != expected,
            "owner_queue_exact_parity_each_checkpoint": all(owner_parity),
            "remote_notification_targets_each_goal_origin": all(
                (size + 3 * i + 2, i) in notification_rows for i in range(size)),
            "omitted_arm_stale_at_all_goal_results": bool(omission)
                and omitted_receipts_at_results,
            "omission_recovery_restores_exact_graph": omitted["final_graph_digest"]
                == explicit["final_graph_digest"],
            "owner_receipts_all_resolved": owner["final_origin_receipts"]
                == {str(i): 1.0 for i in range(size)},
            "owner_counter_and_cost_summary_recompute": all(reported_cost.get(k) == v
                                                               for k, v in expected_cost.items()),
        }
        reconstructed[str(size)] = {"expected_paths": expected,
            "temporal_paths": path(temporal), "recipient_guard_paths": path(recipient),
            "explicit_paths": path(explicit), "owner_parity_checkpoints": sum(owner_parity),
            "checkpoint_count": len(owner_parity), "omission_divergence_indices": omission,
            "omitted_receipts_stale_at_each_task_result": omitted_receipts_at_results,
            "remote_result_owner_notifications": len(notification_rows),
            "owner_queue_candidate_pairs": expected_cost["candidate_pairs"],
            "owner_queue_term_evaluations": expected_cost["term_evaluations"],
            "owner_queue_turns": expected_cost["queue_turns"],
            "full_closure_cost": cost_metrics(explicit),
            "owner_queue_cost": cost_metrics(owner),
            "owner_over_full_candidate_ratio": cost_metrics(owner)["candidate_pairs"] /
                max(1, cost_metrics(explicit)["candidate_pairs"]),
            "owner_over_full_term_ratio": cost_metrics(owner)["term_evaluations"] /
                max(1, cost_metrics(explicit)["term_evaluations"]),
            "owner_over_full_wall_ratio": cost_metrics(owner)["wall_ns"] /
                max(1, cost_metrics(explicit)["wall_ns"])}
    checks = {
        "runner_summary_checks_pass": all(raw["checks"].values()),
        "independent_lock_hash_matches": raw["lock_sha256"] == sha(LOCK),
        "fixture_hash_matches_lock": raw["locked_inputs"]["fixture_sha256"] == sha(FIXTURE),
        "all_fifteen_workers_are_distinct": len(runs) == 15 and len({r["pid"] for r in runs}) == 15,
        "all_sizes_recompute": all(all(row.values()) for row in gates.values()),
    }
    result = {"schema_version": 1,
        "run_id": "substrate-discourse-goal-identity-scale-v4-analysis-20260926",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "fixture_sha256": sha(FIXTURE),
        "checks": checks, "size_gates": gates, "summary": reconstructed,
        "claim_boundary": raw["claim_boundary"],
        "interpretation": "Explicit event-to-goal links disambiguate this generated family. At N<=8, the caller owner queue matches full closure but performs extra candidate, term, and turn work; these measurements are small-instance diagnostics, not asymptotic scaling evidence."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks,
                      "size_gates": gates, "summary": reconstructed}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent goal-identity analysis found a mismatch")


if __name__ == "__main__":
    main()
