#!/usr/bin/env python3
"""Independent task-oracle and owner-queue audit for v3 goal association."""
from __future__ import annotations

import hashlib
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_discourse_goal_association_v3_20260926.json"
FAILED = ROOT / "evaluation/reports/substrate_discourse_goal_association_v3_attempt1_gatefail_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/discourse_goal_association_v3_lock_20260926.json"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_common_ground_stress.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_goal_association_v3_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transition_goal_callsites() -> list[dict]:
    found = []
    for path in sorted((ROOT / "domains").rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if name == "transition_goal":
                found.append({"path": str(path.relative_to(ROOT)), "line": node.lineno})
    return found


def main() -> None:
    raw = json.loads(RAW.read_text())
    failed = json.loads(FAILED.read_text())
    fixture = json.loads(FIXTURE.read_text())
    baseline, full, owner, omitted = raw["runs"]
    fc, oc, xc = (x["checkpoints"] for x in (full, owner, omitted))
    parity = [a["graph_digest"] == b["graph_digest"] for a, b in zip(fc, oc)]
    stale = [a["graph_digest"] != b["graph_digest"] for a, b in zip(fc, xc)]
    receipts_stale = [a["origin_resolution_receipts"] != b["origin_resolution_receipts"]
                      for a, b in zip(fc, xc)]
    remote = []
    for cp in oc:
        for report in cp["settlement"].get("notifications", []):
            remote.extend((cp["event_index"], report["source_frame"], int(target))
                          for target in report["native_owners"]
                          if int(target) != int(report["source_frame"]))
    intended = {"0": [4, 5, 6], "3": [7, 8, 9]}
    production_calls = transition_goal_callsites()
    baseline_paths = {k: v["transition_event_indices"] for k, v in baseline["final_goals"].items()}
    guarded_paths = {k: v["transition_event_indices"] for k, v in full["final_goals"].items()}
    checks = {
        "corrected_runner_all_gates_pass": all(raw["checks"].values()),
        "lock_digest_matches": raw["lock_sha256"] == sha(LOCK),
        "fixture_shape_matches_ten_event_contract": fixture["event_count"] == len(fc) == 10,
        "four_fresh_processes": len({r["pid"] for r in raw["runs"]}) == 4,
        "all_full_arms_fixed_point": all(cp["complete"] for arm in (baseline, full)
                                          for cp in arm["checkpoints"]),
        "guarded_owner_queue_exact_state_each_checkpoint": all(parity),
        "guarded_rules_installed_only_in_treatment_arms": baseline["guarded_rule_indices"] == []
            and all(len(r["guarded_rule_indices"]) == 3 for r in (full, owner, omitted)),
        "baseline_temporal_rule_failure_reproduced": baseline_paths == {"0": [4, 5, 6], "3": [4, 5, 6]},
        "candidate_addressee_guard_matches_task_oracle": guarded_paths == intended,
        "both_origin_frames_notified_at_their_result_events": any(x == (6, 2, 0) for x in remote)
            and any(x == (9, 3, 1) for x in remote),
        "omission_stales_each_receipt_at_its_result_checkpoint": stale[6] and stale[9]
            and receipts_stale[6] and receipts_stale[9]
            and xc[6]["origin_resolution_receipts"].get("0") == 0.0
            and xc[9]["origin_resolution_receipts"].get("3") == 0.0,
        "final_full_recovery_restores_exact_graph": omitted["final_graph_digest"] == full["final_graph_digest"],
        "first_capture_gate_failure_preserved": not all(failed["checks"].values())
            and failed["checks"].get("guarded_queue_notifies_both_origin_frames_at_results") is False,
        "guarded_semantics_and_common_ground_match_across_schedules": owner["final_goals"] == full["final_goals"]
            and owner["final_origin_receipts"] == full["final_origin_receipts"]
            and owner["final_common_grounds"] == full["final_common_grounds"],
        "domain_modules_do_not_call_host_transition_helper": production_calls == [],
    }
    result = {
        "schema_version": 1,
        "run_id": "substrate-discourse-goal-association-v3-analysis-20260926",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "fixture_sha256": sha(FIXTURE),
        "preserved_gate_failure_sha256": sha(FAILED), "checks": checks,
        "summary": {"owner_queue_equal_checkpoints": sum(parity), "checkpoint_count": len(parity),
                    "omission_divergence_event_indices": [i for i, x in enumerate(stale) if x],
                    "baseline_goal_paths": baseline_paths, "guarded_goal_paths": guarded_paths,
                    "intended_goal_paths": intended,
                    "remote_notifications": [list(x) for x in remote],
                    "domain_transition_goal_callsites": production_calls,
                    "wall_time_claim": "single capture; descriptive only; no speed claim",
                    "semantic_limit": "The temporal-only behavior is in the experimental native seed; domains contain a host helper with no call sites. Addressee equality repairs this fixture only; concurrent same-addressee goals remain unresolved."},
        "claim_boundary": raw["claim_boundary"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": result["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent goal-association analysis found a mismatch")


if __name__ == "__main__":
    main()
