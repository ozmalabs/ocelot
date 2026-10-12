#!/usr/bin/env python3
"""Independent parity and pairing checks for GenInfer scope-index lifecycle v1."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_1_lock_20261005.json"
CAPTURE = ROOT / "evaluation/reports/geninfer_scope_index_lifecycle_v1_1_20261005.json"
OUT = ROOT / "evaluation/reports/geninfer_scope_index_lifecycle_v1_1_analysis_20261005.json"


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
    gate("locked_case_set", len(rows) == 36 and observed_ids == case_ids,
         f"expected {len(case_ids)} locked cases; observed {len(rows)} rows")
    gate("capture_lock_hash", capture.get("lock_sha256") ==
         hashlib.sha256(LOCK.read_bytes()).hexdigest(),
         "capture references current lock bytes")
    gate("source_manifest_matches", capture.get("source_manifest") == lock.get("sources") and
         all(row.get("source_before") == lock["sources"] == row.get("source_after")
             and row.get("source_stable") for row in rows),
         "top-level and all worker source/build manifests match the lock")
    gate("fresh_worker_processes", len({row.get("pid") for row in rows}) == 36,
         "each locked traced/untraced condition ran in its own process")
    gate("scope_and_task_membership", all(row.get("task_membership_parity") for row in rows),
         "indexed task parts resolve to the exact scan-derived member IDs")
    gate("fork_and_branch_isolation", all(row.get("fork_matches") and row.get("branch_isolated")
         for row in rows), "fork graph equals parent at creation; branch writes leave parent unchanged")
    indexed_rows = [row for row in rows if row.get("case", {}).get("mode") == "frame_scoped_indexed"]
    gate("branch_index_mutation", len(indexed_rows) == 18 and all(
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
    trace_rows_by_case = {}
    helper_kinds = {
        "dynamic_helper_invocation", "helper_codebook_population_node",
        "helper_node_attribute_examined", "helper_codebook_part_parsed",
        "helper_relation_cue_population_node", "helper_search_candidate",
        "helper_candidate_part_scored", "helper_graph_term_node_decoded",
        "helper_render_rule_candidate", "helper_auxiliary_population_node",
        "helper_scope_population_index_query", "helper_scope_population_index_member",
    }
    for row in rows:
        trace = row.get("runtime_work_trace", {})
        if row.get("case", {}).get("trace"):
            counts = {}
            for event in trace.get("rows", []):
                if len(event) != 6:
                    continue
                kind = str(event[3])
                # The work-event subject is the dynamic-helper enum. GenInfer
                # is helper 4 on this source-locked route, as in scope trace v2.1.
                if kind in helper_kinds and int(event[4] or 0) == 4:
                    counts[kind] = counts.get(kind, 0) + int(event[5])
            trace_rows_by_case[row["case"]["id"]] = (counts, trace.get("dropped"))

    trace_replay_ok = True
    for decoys in lock["decoys"]:
        for rep in lock["replicates"]:
            arm_pair = {}
            for mode in ("frame_scoped", "frame_scoped_indexed"):
                arm_pair[mode] = {bool(row["case"]["trace"]): row for row in rows
                                  if row["case"]["decoys"] == decoys
                                  and row["case"]["replicate"] == rep
                                  and row["case"]["mode"] == mode}
            if any(set(arm_pair[mode]) != {False, True} for mode in arm_pair):
                trace_replay_ok = pairing_ok = False
                continue
            for mode in arm_pair:
                plain, traced = arm_pair[mode][False], arm_pair[mode][True]
                same = canonical(plain["outputs"]) == canonical(traced["outputs"])
                same_work = plain["closure_work"] == traced["closure_work"]
                trace_replay_ok &= same and same_work and traced["runtime_work_trace"]["dropped"] == 0
            scan, indexed = arm_pair["frame_scoped"][False], arm_pair["frame_scoped_indexed"][False]
            same_output = canonical(scan["outputs"]) == canonical(indexed["outputs"])
            same_work = scan["closure_work"] == indexed["closure_work"]
            pairing_ok &= same_output and same_work
            pairs.append({"decoys": decoys, "replicate": rep,
                          "outputs_match": same_output, "closure_work_match": same_work,
                          "scan_wall_ns": scan["closure_wall_ns"],
                          "indexed_wall_ns": indexed["closure_wall_ns"],
                          "scan_cpu_ns": scan["closure_cpu_ns"],
                          "indexed_cpu_ns": indexed["closure_cpu_ns"]})
    gate("paired_output_and_coarse_work", pairing_ok and len(pairs) == 9,
         f"exact output and run_rules return-count parity across {len(pairs)} untraced scan/index pairs")
    gate("traced_untraced_outcome_parity", trace_replay_ok,
         "traced workers match the separate untraced result and coarse work count; no trace drops")

    helper_parity = True
    population_reduced = True
    index_events_present = True
    for decoys in lock["decoys"]:
        for rep in lock["replicates"]:
            scan_case = f"frame_scoped_d{decoys}_r{rep}_trace1"
            idx_case = f"frame_scoped_indexed_d{decoys}_r{rep}_trace1"
            scan_counts, scan_drops = trace_rows_by_case.get(scan_case, ({}, 1))
            idx_counts, idx_drops = trace_rows_by_case.get(idx_case, ({}, 1))
            population_reduced &= idx_counts.get("helper_codebook_population_node", 0) < scan_counts.get("helper_codebook_population_node", 0)
            helper_parity &= idx_counts.get("helper_codebook_part_parsed", -1) == scan_counts.get("helper_codebook_part_parsed", -2)
            helper_parity &= idx_counts.get("helper_search_candidate", -1) == scan_counts.get("helper_search_candidate", -2)
            index_events_present &= idx_counts.get("helper_scope_population_index_query", 0) > 0
            index_events_present &= idx_counts.get("helper_scope_population_index_member", 0) > 0
            index_events_present &= scan_drops == idx_drops == 0
    gate("indexed_trace_avoids_population_scan", population_reduced,
         "traced indexed closure records fewer codebook population node visits in every cell")
    gate("traced_parse_and_candidate_parity", helper_parity,
         "indexed and scan closures parse equal parts and enumerate equal search candidates")
    gate("indexed_scope_query_events", index_events_present,
         "indexed path records scope-index queries and returned members without trace drops")
    gate("lifecycle_measurements_present", all(
        row["index_build_ns"] >= 0 and row["task_insert_ns"] > 0 and row["fork_ns"] > 0 and
        row["branch_mutation_ns"] >= 0 and row["serialize_ns"] > 0 and row["restore_ns"] > 0
        for row in rows), "all lifecycle phases were recorded")
    scan_rows = [row for row in rows if row.get("case", {}).get("mode") == "frame_scoped"]
    gate("index_toggle_and_phase_rss", len(indexed_rows) == 18 and all(
         row["index_build_ns"] > 0 and row["restore_redeclare_ns"] > 0
         and row["hwm_by_phase_kib"].keys() >= {
             "after_boot_kib", "after_decoys_kib", "after_index_kib",
             "after_fork_kib", "after_restore_kib", "after_closure_kib"}
         for row in indexed_rows) and all(
         row["index_build_ns"] == 0 and row["restore_redeclare_ns"] == 0
         for row in scan_rows),
         "index phases are present only in indexed arms and RSS high-water checkpoints are recorded")

    analysis = {"schema": "GenInferScopeIndexLifecycleV1_1Analysis",
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
