#!/usr/bin/env python3
"""Post-hoc helper-family attribution from the locked GenInfer lifecycle trace."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/geninfer_scope_index_lifecycle_v1_1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/geninfer_scope_helper_residual_v1_analysis_20261005.json"
HELPERS = {1: "ShapeDecode", 2: "TransformDecode", 3: "DimInfer", 4: "GenInfer"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def work(row: dict) -> tuple[dict[int, Counter], Counter]:
    families: dict[int, Counter] = defaultdict(Counter)
    sched = Counter()
    for event in row["runtime_work_trace"]["rows"]:
        if len(event) != 6:
            raise ValueError(f"malformed work event: {event!r}")
        _, _, _, kind, helper, units = event
        if str(kind).startswith("scheduler_"):
            sched[str(kind)] += int(units)
        elif str(kind).startswith("helper_") and int(helper or 0) in HELPERS:
            families[int(helper)][str(kind)] += int(units)
    return families, sched


def median(values: list[int]) -> int:
    return int(statistics.median(values))


def main() -> int:
    raw = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    errors = []
    if raw.get("source_manifest") != lock.get("sources"):
        errors.append("capture source manifest differs from locked source manifest")
    traces = [row for row in raw["cases"] if row["case"].get("trace")]
    if len(traces) != 18 or len({row["pid"] for row in raw["cases"]}) != 36:
        errors.append("expected 18 traced cases and 36 distinct worker processes")
    if any(row["runtime_work_trace"].get("dropped") != 0 for row in traces):
        errors.append("one or more traces dropped work events")

    grouped = defaultdict(list)
    for row in traces:
        grouped[(row["case"]["decoys"], row["case"]["mode"])].append(row)
    cells = []
    mechanisms_ok = True
    other_helpers_equal = True
    candidate_work_equal = True
    scheduler_equal = True
    replication_ok = True
    for decoys in lock["decoys"]:
        scan_rows = grouped[(decoys, "frame_scoped")]
        indexed_rows = grouped[(decoys, "frame_scoped_indexed")]
        if len(scan_rows) != 3 or len(indexed_rows) != 3:
            errors.append(f"decoys={decoys}: expected three traced workers per arm")
            replication_ok = False
            continue
        scan_families, scan_sched = zip(*(work(row) for row in scan_rows))
        indexed_families, indexed_sched = zip(*(work(row) for row in indexed_rows))
        summary = {}
        family_counts = {}
        for helper_id, helper_name in HELPERS.items():
            kinds = sorted({kind for maps in (*scan_families, *indexed_families)
                            for kind in maps[helper_id]})
            arm_summary = {}
            for arm, maps in (("scan", scan_families), ("indexed", indexed_families)):
                arm_summary[arm] = {
                    kind: median([m[helper_id].get(kind, 0) for m in maps])
                    for kind in kinds
                }
            family_counts[helper_name] = arm_summary
            summary[helper_name] = {
                "scan_population_nodes": arm_summary["scan"].get("helper_codebook_population_node", 0),
                "indexed_population_nodes": arm_summary["indexed"].get("helper_codebook_population_node", 0),
                "scan_parsed_parts": arm_summary["scan"].get("helper_codebook_part_parsed", 0),
                "indexed_parsed_parts": arm_summary["indexed"].get("helper_codebook_part_parsed", 0),
                "scan_candidates": arm_summary["scan"].get("helper_search_candidate", 0),
                "indexed_candidates": arm_summary["indexed"].get("helper_search_candidate", 0),
            }
            if helper_id != 4:
                other_helpers_equal &= arm_summary["scan"] == arm_summary["indexed"]
            candidate_work_equal &= summary[helper_name]["scan_candidates"] == summary[helper_name]["indexed_candidates"]
        scheduler_equal &= all(scan_sched[i] == indexed_sched[i] for i in range(3))
        scan_population = sum(item["scan_population_nodes"] for item in summary.values())
        indexed_population = sum(item["indexed_population_nodes"] for item in summary.values())
        population_reduction = scan_population - indexed_population
        geninfer_index_queries = [m[4].get("helper_scope_population_index_query", 0)
                                  for m in indexed_families]
        geninfer_index_members = [m[4].get("helper_scope_population_index_member", 0)
                                  for m in indexed_families]
        mechanisms_ok &= (summary["GenInfer"]["indexed_population_nodes"] == 0
                          and summary["GenInfer"]["scan_population_nodes"] > 0
                          and geninfer_index_queries == [4, 4, 4]
                          and geninfer_index_members == [4, 4, 4])
        cells.append({
            "decoys": decoys,
            "shape_signature_population": statistics.median(
                row["shape_signature_population"] for row in scan_rows),
            "helper_work": family_counts,
            "total_helper_population_visits_scan": scan_population,
            "total_helper_population_visits_indexed": indexed_population,
            "total_helper_population_visits_removed": population_reduction,
            "fraction_of_population_visits_removed": population_reduction / scan_population if scan_population else 0,
            "geninfer_index_queries_by_replicate": geninfer_index_queries,
            "geninfer_index_members_by_replicate": geninfer_index_members,
            "scheduler_work": {
                "scan": {k: median([m[k] for m in scan_sched]) for k in sorted(scan_sched[0])},
                "indexed": {k: median([m[k] for m in indexed_sched]) for k in sorted(indexed_sched[0])},
            },
        })
        signatures = []
        for rows in (scan_families, indexed_families):
            signatures.append({json.dumps({h: dict(m[h]) for h in HELPERS}, sort_keys=True)
                               for m in rows})
        replication_ok &= all(len(items) == 1 for items in signatures)

    checks = {
        "capture_matches_source_lock": raw.get("source_manifest") == lock.get("sources"),
        "fresh_traced_processes_and_no_drops": len(traces) == 18
            and len({row["pid"] for row in raw["cases"]}) == 36
            and all(row["runtime_work_trace"].get("dropped") == 0 for row in traces),
        "work_reproduces_within_each_cell": replication_ok,
        "index_removes_geninfer_population_visits": mechanisms_ok,
        "other_helper_work_unchanged": other_helpers_equal,
        "candidate_work_unchanged": candidate_work_equal,
        "scheduler_work_unchanged": scheduler_equal,
    }
    result = {
        "schema": "GenInferScopeHelperResidualV1Analysis",
        "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
        "analyzer_sha256": sha(Path(__file__)),
        "helper_subject_mapping": HELPERS,
        "checks": checks, "passed": all(checks.values()), "errors": errors,
        "cells": cells,
        "interpretation": "The GenInfer index removes its own typed-population traversal, but ShapeDecode, TransformDecode, and DimInfer still enumerate the complete ShapeSignature population. GenInfer candidate-search work is unchanged. This attributes residual dynamic-helper work, not wall-time causality; the untraced lifecycle result remains near parity.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
                      "passed": sum(checks.values()), "total": len(checks),
                      "all_passed": result["passed"]}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
