#!/usr/bin/env python3
"""Independent parity and wakeup checks for the scoped conversation probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_conversation_scoped_owner_wakeup_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/conversation_scoped_owner_wakeup_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_scoped_owner_wakeup_v1_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    full, owner, omitted = raw["runs"]
    full_cp, owner_cp, omitted_cp = (x["checkpoints"] for x in (full, owner, omitted))
    parity = [a["graph_digest"] == b["graph_digest"] for a, b in zip(full_cp, owner_cp)]
    stale = [a["graph_digest"] != b["graph_digest"] for a, b in zip(full_cp, omitted_cp)]
    receipt_stale = [a["origin_resolution_receipts"] != b["origin_resolution_receipts"]
                     for a, b in zip(full_cp, omitted_cp)]
    remote = []
    for cp in owner_cp:
        for notification in cp["settlement"].get("notifications", []):
            remote.extend((cp["event_index"], notification["source_frame"], target)
                          for target in notification["native_owners"]
                          if target != notification["source_frame"])
    expected_receipts = {"0": 1.0, "5": 1.0}
    checks = {
        "runner_checks_all_pass": all(raw["checks"].values()),
        "independent_lock_digest_matches": raw["lock_sha256"] == sha(LOCK),
        "three_distinct_processes": len({r["pid"] for r in raw["runs"]}) == 3,
        "ten_checkpoints_and_full_fixed_points": len(full_cp) == 10 and all(x["complete"] for x in full_cp),
        "owner_queue_exact_parity_at_every_checkpoint": all(parity),
        "remote_owner_wakeup_crosses_both_goal_boundaries": any(x[2] == 0 and x[0] in {1, 2, 3}
            for x in remote) and any(x[2] == 2 and x[0] in {6, 7, 8} for x in remote),
        "omission_stale_after_remote_resolution": all(stale[i] and receipt_stale[i]
            for i in (3, 8)),
        "omission_recovery_restores_final_graph": omitted["final_graph_digest"] == full["final_graph_digest"],
        "owner_task_and_receipt_oracles_match": owner["final_goals"] == full["final_goals"]
            and owner["final_origin_receipts"] == expected_receipts
            and owner["final_common_grounds"] == full["final_common_grounds"],
    }
    result = {
        "schema_version": 1,
        "run_id": "substrate-conversation-scoped-owner-wakeup-v1-analysis-20260926",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "checks": checks,
        "summary": {"owner_queue_equal_checkpoints": sum(parity),
                    "checkpoint_count": len(parity),
                    "omitted_equal_checkpoints": len(stale) - sum(stale),
                    "omission_divergence_event_indices": [i for i, x in enumerate(stale) if x],
                    "origin_receipt_divergence_event_indices": [i for i, x in enumerate(receipt_stale) if x],
                    "remote_notifications": [list(x) for x in remote]},
        "claim_boundary": raw["claim_boundary"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": result["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent owner-wakeup analysis found a mismatch")


if __name__ == "__main__":
    main()
