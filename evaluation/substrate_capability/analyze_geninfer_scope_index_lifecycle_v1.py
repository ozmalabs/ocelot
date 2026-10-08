#!/usr/bin/env python3
"""Independent parity and pairing checks for GenInfer scope-index lifecycle v1."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_lock_20261005.json"
CAPTURE = ROOT / "evaluation/reports/geninfer_scope_index_lifecycle_v1_20261005.json"
OUT = ROOT / "evaluation/reports/geninfer_scope_index_lifecycle_v1_analysis_20261005.json"


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def main() -> int:
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    gates: list[dict] = []

    def gate(name: str, ok: bool, detail: str) -> None:
        gates.append({"name": name, "passed": bool(ok), "detail": detail})

    case_ids = {case["id"] for case in lock["cases"]}
    rows = capture.get("cases", [])
    observed_ids = {row.get("case", {}).get("id") for row in rows}
    gate("locked_case_set", len(rows) == 18 and observed_ids == case_ids,
         f"expected {len(case_ids)} locked cases; observed {len(rows)} rows")
    gate("capture_lock_hash", capture.get("lock_sha256") ==
         hashlib.sha256(LOCK.read_bytes()).hexdigest(),
         "capture references current lock bytes")
    gate("source_manifest_matches", capture.get("source_manifest") == lock.get("sources") and
         all(row.get("source_before") == lock["sources"] == row.get("source_after")
             and row.get("source_stable") for row in rows),
         "top-level and all worker source/build manifests match the lock")
    gate("scope_and_task_membership", all(row.get("task_membership_parity") for row in rows),
         "indexed task parts resolve to the exact scan-derived member IDs")
    gate("fork_and_branch_isolation", all(row.get("fork_matches") and row.get("branch_isolated")
         for row in rows), "fork graph equals parent at creation; branch writes leave parent unchanged")
    indexed_rows = [row for row in rows if row.get("case", {}).get("mode") == "frame_scoped_indexed"]
    gate("branch_index_mutation", len(indexed_rows) == 9 and all(
         row.get("branch_mutation_parity") and row.get("decoy_index_parity")
         for row in indexed_rows),
         "indexed branch scope buckets and decoy bucket agree with full-scan oracle")
    gate("restore_parity", all(row.get("restore_matches") and row.get("restore_index_matches")
         for row in rows), "restored graph and re-declared indexed membership match")
    gate("output_oracles", all(len(row.get("outputs", [])) == 2 and all(
         output.get("oracle_exact") and output.get("target_generator_present") and
         output.get("status") == "recognized_transformed" and bool(output.get("receipts"))
         for output in row["outputs"]) for row in rows),
         "each target frame has exact oracle, decoded status, receipt, and acquired generator")

    pairs = []
    pairing_ok = True
    for decoys in lock["decoys"]:
        for rep in lock["replicates"]:
            pair = {row["case"]["mode"]: row for row in rows
                    if row["case"]["decoys"] == decoys and row["case"]["replicate"] == rep}
            if set(pair) != {"frame_scoped", "frame_scoped_indexed"}:
                pairing_ok = False
                continue
            scan, indexed = pair["frame_scoped"], pair["frame_scoped_indexed"]
            same_output = canonical(scan["outputs"]) == canonical(indexed["outputs"])
            same_work = scan["closure_work"] == indexed["closure_work"]
            pairing_ok &= same_output and same_work
            pairs.append({"decoys": decoys, "replicate": rep,
                          "outputs_match": same_output, "closure_work_match": same_work,
                          "scan_wall_ns": scan["closure_wall_ns"],
                          "indexed_wall_ns": indexed["closure_wall_ns"],
                          "scan_cpu_ns": scan["closure_cpu_ns"],
                          "indexed_cpu_ns": indexed["closure_cpu_ns"]})
    gate("paired_output_and_work", pairing_ok and len(pairs) == 9,
         f"exact output and work parity across {len(pairs)} scan/index pairs")
    gate("lifecycle_measurements_present", all(
        row["index_build_ns"] >= 0 and row["task_insert_ns"] > 0 and row["fork_ns"] > 0 and
        row["branch_mutation_ns"] >= 0 and row["serialize_ns"] > 0 and row["restore_ns"] > 0
        for row in rows), "all lifecycle phases were recorded")
    gate("index_toggle_and_phase_rss", len(indexed_rows) == 9 and all(
         row["index_build_ns"] > 0 and row["restore_redeclare_ns"] > 0
         and row["hwm_by_phase_kib"].keys() >= {
             "after_boot_kib", "after_decoys_kib", "after_index_kib",
             "after_fork_kib", "after_restore_kib", "after_closure_kib"}
         for row in indexed_rows) and all(
         row["index_build_ns"] == 0 and row["restore_redeclare_ns"] == 0
         for row in rows if row not in indexed_rows),
         "index phases are present only in indexed arms and RSS high-water checkpoints are recorded")

    analysis = {"schema": "GenInferScopeIndexLifecycleV1Analysis",
                "capture_sha256": "sha256:" + hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
                "lock_sha256": "sha256:" + hashlib.sha256(LOCK.read_bytes()).hexdigest(),
                "gate_count": len(gates), "passed_count": sum(g["passed"] for g in gates),
                "all_gates_passed": all(g["passed"] for g in gates),
                "gates": gates, "paired_rows": pairs}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
                      "passed": analysis["passed_count"], "total": len(gates),
                      "all_gates_passed": analysis["all_gates_passed"]}, sort_keys=True))
    return 0 if analysis["all_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
