#!/usr/bin/env python3
"""Independent parity and semantic-gap audit for the interleaved task probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_conversation_scoped_owner_wakeup_v2_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/conversation_scoped_owner_wakeup_v2_lock_20260926.json"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_common_ground_stress.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_scoped_owner_wakeup_v2_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    fixture = json.loads(FIXTURE.read_text())
    full, owner, omitted = raw["runs"]
    fc, oc, xc = (r["checkpoints"] for r in (full, owner, omitted))
    parity = [a["graph_digest"] == b["graph_digest"] for a, b in zip(fc, oc)]
    stale = [a["graph_digest"] != b["graph_digest"] for a, b in zip(fc, xc)]
    receipt_stale = [a["origin_resolution_receipts"] != b["origin_resolution_receipts"]
                     for a, b in zip(fc, xc)]
    remote = []
    for cp in oc:
        for call in cp["settlement"].get("notifications", []):
            remote += [(cp["event_index"], call["source_frame"], int(target))
                       for target in call["native_owners"]
                       if int(target) != int(call["source_frame"])]
    expected_fixture_pairing = {0: [4, 5, 6], 3: [7, 8, 9]}
    actual = {int(origin): values["transition_event_indices"]
              for origin, values in full["final_goals"].items()}
    checks = {
        "runner_checks_all_pass": all(raw["checks"].values()),
        "lock_digest_matches": raw["lock_sha256"] == sha(LOCK),
        "fixture_and_checkpoint_shape": fixture["event_count"] == len(fc) == 10,
        "three_fresh_processes": len({r["pid"] for r in raw["runs"]}) == 3,
        "full_arm_reaches_fixed_points": all(x["complete"] for x in fc),
        "owner_queue_exact_graph_parity": all(parity),
        "remote_result_notifies_both_origin_frames": any(x[0] == 6 and x[2] == 0 for x in remote)
            and any(x[0] == 6 and x[2] == 1 for x in remote),
        "omission_stale_on_receipt_checkpoint": stale[6] and receipt_stale[6],
        "global_recovery_exact": omitted["final_graph_digest"] == full["final_graph_digest"],
        "fixture_intended_goal_pairing_not_realized_by_rules": actual != expected_fixture_pairing,
        "observed_rule_pairing_recomputed": actual == {0: [4, 5, 6], 3: [4, 5, 6]},
        "owner_goal_state_and_common_ground_match_full": owner["final_goals"] == full["final_goals"]
            and owner["final_origin_receipts"] == full["final_origin_receipts"]
            and owner["final_common_grounds"] == full["final_common_grounds"],
    }
    result = {
        "schema_version": 1,
        "run_id": "substrate-conversation-scoped-owner-wakeup-v2-analysis-20260926",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "fixture_sha256": sha(FIXTURE), "checks": checks,
        "summary": {"owner_queue_equal_checkpoints": sum(parity), "checkpoint_count": len(parity),
                    "omission_divergence_event_indices": [i for i, x in enumerate(stale) if x],
                    "receipt_divergence_event_indices": [i for i, x in enumerate(receipt_stale) if x],
                    "remote_notifications": [list(x) for x in remote],
                    "fixture_pairing_by_origin": expected_fixture_pairing,
                    "native_rule_pairing_by_origin": actual,
                    "semantic_gap": "The benchmark-loaded experimental seed rules transition both open Goals on events 4, 5, and 6 because their guards use temporal order rather than task identity/addressee. The domain contains an explicit host transition_goal(agent, goal, ...) helper, but source audit found no domain-module call sites; this probe does not establish a production task misassignment. See the v3 candidate guard diagnostic."},
        "claim_boundary": raw["claim_boundary"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": result["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent v2 owner-wakeup analysis found a mismatch")


if __name__ == "__main__":
    main()
