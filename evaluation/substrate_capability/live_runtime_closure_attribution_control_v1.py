#!/usr/bin/env python3
"""Locked native binding control for store-qualified rule audit identities."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_CLOSURE_ATTRIBUTION_CONTROL_V1_PREREG_20261004.md"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_closure_attribution_control_v1_lock_20261004.json"
RESULT = ROOT / "evaluation/reports/live_runtime_closure_attribution_control_v1_20261004.json"
SOURCES = [
    ROOT / "runners/dsl/src/scale_audit.rs",
    ROOT / "runners/dsl/src/substrate.rs",
    ROOT / "runners/dsl/src/rewrite.rs",
    ROOT / "runners/dsl/src/py.rs",
    ROOT / "runners/dsl/Cargo.lock",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs() -> dict:
    from substrate_rs import _native

    return {
        "preregistration_sha256": sha(PREREG),
        "runner_sha256": sha(Path(__file__).resolve()),
        "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in SOURCES},
        "native_path": str(Path(_native.__file__).resolve()),
        "native_sha256": sha(Path(_native.__file__).resolve()),
    }


def run_control() -> dict:
    from domains.engine_provenance import assert_measuring_engine
    from substrate_rs import _native

    assert_measuring_engine()
    N = _native.Substrate
    N.scale_audit_set_enabled(False)
    N.scale_audit_set_per_rule_enabled(False)
    N.scale_audit_reset()
    N.scale_audit_per_rule_reset()
    N.scale_audit_set_per_rule_enabled(True)
    N.scale_audit_set_enabled(True)

    substrates = [N(), N()]
    applications = []
    for substrate in substrates:
        src = substrate.add_node("Node")
        tgt = substrate.add_node("Node")
        substrate.add_edge_unchecked(src, "link", tgt)
        rule_index = substrate.add_rule(
            {
                "name": "shared_rule",
                "match": [["src", "link", "tgt"]],
                "where": None,
                "effects": [],
            }
        )
        applications.append(
            {"rule_index": rule_index, "matched": bool(substrate.apply_rule_once(rule_index))}
        )

    on = {
        "global": [list(row) for row in N.scale_audit_snapshot()],
        "per_rule": [list(row) for row in N.scale_audit_per_rule_snapshot()],
        "clauses": [list(row) for row in N.scale_audit_match_clause_snapshot()],
        "metadata": [list(row) for row in N.scale_audit_rule_metadata_snapshot()],
        "identities": [list(row) for row in N.scale_audit_rule_identity_snapshot()],
    }
    global_counts = dict(on["global"])
    identity_rows = on["identities"]
    target_identities = [row for row in identity_rows if row[2] == 0]
    audit_ids = {row[0] for row in target_identities}
    stores = {row[1] for row in target_identities}
    per_candidate = {
        row[0]: row[2] for row in on["per_rule"] if row[1] == "candidate_tests"
    }
    clause_by_id: dict[int, int] = {}
    for audit_id, position, count in on["clauses"]:
        if position == 0:
            clause_by_id[audit_id] = clause_by_id.get(audit_id, 0) + count

    N.scale_audit_set_enabled(False)
    N.scale_audit_reset()
    N.scale_audit_per_rule_reset()
    audit_off_application = bool(substrates[0].apply_rule_once(0))
    off = {
        "global": [list(row) for row in N.scale_audit_snapshot()],
        "per_rule": [list(row) for row in N.scale_audit_per_rule_snapshot()],
        "clauses": [list(row) for row in N.scale_audit_match_clause_snapshot()],
        "metadata": [list(row) for row in N.scale_audit_rule_metadata_snapshot()],
        "identities": [list(row) for row in N.scale_audit_rule_identity_snapshot()],
    }

    checks = {
        "two_local_zero_rules_matched": applications == [
            {"rule_index": 0, "matched": True}, {"rule_index": 0, "matched": True}
        ],
        "two_distinct_audit_ids_and_stores": len(target_identities) == 2
        and len(audit_ids) == 2
        and len(stores) == 2,
        "metadata_valid_nonambiguous": len(on["metadata"]) == 2
        and all(row[2] == "shared_rule" and row[3] == 1 and not row[4] for row in on["metadata"]),
        "per_rule_and_clause_split": len(per_candidate) == 2
        and set(per_candidate) == audit_ids
        and set(clause_by_id) == audit_ids
        and all(value == 1 for value in per_candidate.values())
        and all(value == 1 for value in clause_by_id.values()),
        "candidate_conservation": global_counts.get("cand_tested_unattributed") == 0
        and sum(per_candidate.values()) == global_counts.get("cand_tested")
        and sum(clause_by_id.values()) == global_counts.get("cand_tested"),
        "audit_off_isolation": audit_off_application
        and all(value == 0 for _, value in off["global"])
        and all(not off[key] for key in ("per_rule", "clauses", "metadata", "identities")),
    }
    N.scale_audit_set_per_rule_enabled(False)
    N.scale_audit_reset()
    return {"applications": applications, "audit_on": on, "audit_off": off, "checks": checks}


def write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        if RESULT.exists() or LOCK.exists():
            raise SystemExit("refusing to replace an existing control result or lock")
        write_json(LOCK, {"schema": "LiveRuntimeClosureAttributionControlV1Lock", "inputs": inputs()})
        print(LOCK.relative_to(ROOT))
        return 0
    if not LOCK.exists() or RESULT.exists():
        raise SystemExit("expected fresh lock and absent result; use --lock first")
    locked = json.loads(LOCK.read_text())["inputs"]
    started = inputs()
    if started != locked:
        raise SystemExit("source/native inputs do not match saved lock")
    capture = run_control()
    finished = inputs()
    result = {
        "schema": "LiveRuntimeClosureAttributionControlV1",
        "locked_inputs": locked,
        "worker_started_inputs": started,
        "worker_finished_inputs": finished,
        "source_stable": started == finished,
        **capture,
    }
    result["all_checks_pass"] = result["source_stable"] and all(capture["checks"].values())
    write_json(RESULT, result)
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "checks": result["checks"], "result": str(RESULT.relative_to(ROOT))}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
