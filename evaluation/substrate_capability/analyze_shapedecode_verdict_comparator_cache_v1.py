#!/usr/bin/env python3
"""Independent paired parity and cost analysis for verdict comparator replay."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/shapedecode_verdict_comparator_cache_v1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_verdict_comparator_cache_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_verdict_comparator_cache_v1_analysis_20261005.json"
KINDS = {"dynamic_helper_invocation", "helper_codebook_population_node",
         "helper_node_attribute_examined", "helper_codebook_part_parsed",
         "helper_search_candidate", "helper_candidate_part_scored",
         "helper_codebook_cache_hit", "helper_codebook_cache_miss"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def work_counts(row: dict) -> dict[str, int]:
    out = {kind: 0 for kind in KINDS}
    for event in row.get("trace", {}).get("rows", []):
        if len(event) == 6 and str(event[3]) in KINDS and int(event[4] or 0) == 1:
            out[str(event[3])] += int(event[5])
    return out


def semantic_projection(row: dict) -> dict:
    readback = dict(row.get("readback", {}))
    readback.pop("tag", None)
    return {"readback": readback, "closure_work": row.get("closure_work"),
            "vdsignature_count": row.get("vdsignature_count")}


def main() -> int:
    capture, lock = (json.loads(path.read_text()) for path in (CAPTURE, LOCK))
    rows = capture.get("rows", [])
    expected = {case["id"] for case in lock["cases"]}
    actual = {row.get("case", {}).get("id") for row in rows}
    checks = {
        "locked_80_case_panel": len(rows) == 80 and actual == expected,
        "capture_lock_hash_matches": capture.get("lock_sha256") == sha(LOCK),
        "fresh_process_per_case": len({row.get("pid") for row in rows}) == 80,
        "source_manifests_stable": all(row.get("source_stable") and
            row.get("source_before") == lock["manifest"] == row.get("source_after") for row in rows),
        "no_worker_failures": not capture.get("process_failures") and
            all("worker_error" not in row for row in rows),
        "all_workers_choose_r00": all(row.get("readback", {}).get("said") == "r00" for row in rows),
        "traces_have_no_drops": all(not row["case"]["trace"] or row.get("trace", {}).get("dropped") == 0 for row in rows),
    }
    paired, cells = [], []
    parity = traced_parity = True
    for size in (16, 32, 64, 128):
        plain_scan, plain_cached, traced_scan, traced_cached = [], [], [], []
        for rep in range(5):
            items = {(r["case"]["mode"], bool(r["case"]["trace"])): r for r in rows
                     if r.get("case", {}).get("size") == size and
                     r.get("case", {}).get("replicate") == rep}
            sp, cp, st, ct = (items.get(("scan", False)), items.get(("cached", False)),
                              items.get(("scan", True)), items.get(("cached", True)))
            if not all((sp, cp, st, ct)):
                parity = traced_parity = False
                continue
            paired_equal = semantic_projection(sp) == semantic_projection(cp)
            all_trace_equal = len({json.dumps(semantic_projection(r), sort_keys=True)
                                   for r in (sp, cp, st, ct)}) == 1
            parity &= paired_equal
            traced_parity &= all_trace_equal
            plain_scan.append(sp); plain_cached.append(cp)
            traced_scan.append(st); traced_cached.append(ct)
            paired.append({"size": size, "replicate": rep,
                           "semantic_parity": paired_equal, "trace_arm_parity": all_trace_equal,
                           "scan_work": work_counts(st), "cached_work": work_counts(ct),
                           "scan_wall_ns": sp["closure_wall_ns"],
                           "cached_wall_ns": cp["closure_wall_ns"],
                           "scan_cpu_ns": sp["closure_cpu_ns"],
                           "cached_cpu_ns": cp["closure_cpu_ns"]})
        med_scan = statistics.median(r["closure_wall_ns"] for r in plain_scan) if plain_scan else 0
        med_cached = statistics.median(r["closure_wall_ns"] for r in plain_cached) if plain_cached else 0
        s_counts = [work_counts(r) for r in traced_scan]
        c_counts = [work_counts(r) for r in traced_cached]
        med = lambda seq, key: int(statistics.median(d[key] for d in seq)) if seq else 0
        cells.append({"authored_size": size,
                      "effective_vdsignature_population": statistics.median(r["vdsignature_count"] for r in plain_scan) if plain_scan else 0,
                      "scan_population_visits": med(s_counts, "helper_codebook_population_node"),
                      "cached_population_visits": med(c_counts, "helper_codebook_population_node"),
                      "cached_hits": med(c_counts, "helper_codebook_cache_hit"),
                      "cached_misses": med(c_counts, "helper_codebook_cache_miss"),
                      "scan_wall_median_ns": int(med_scan), "cached_wall_median_ns": int(med_cached),
                      "wall_speedup": med_scan / med_cached if med_cached else None,
                      "scan_cpu_median_ns": med(plain_scan, "closure_cpu_ns"),
                      "cached_cpu_median_ns": med(plain_cached, "closure_cpu_ns"),
                      "scan_rss_median_kib": med(plain_scan, "peak_rss_kib"),
                      "cached_rss_median_kib": med(plain_cached, "peak_rss_kib")})
    checks["paired_output_and_closure_work_parity"] = parity
    checks["traced_untraced_semantic_parity"] = traced_parity
    checks["cache_reduces_population_visits_all_sizes"] = all(c["cached_population_visits"] < c["scan_population_visits"] for c in cells)
    checks["cache_records_reuse_all_sizes"] = all(c["cached_hits"] > 0 and c["cached_misses"] > 0 for c in cells)
    result = {"schema": "ShapeDecodeVerdictComparatorCacheV1Analysis",
              "run_id": "shapedecode-verdict-comparator-cache-v1-analysis-20261005",
              "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
              "checks": checks, "passed": all(checks.values()), "worker_count": len(rows),
              "cells": cells, "paired_rows": paired,
              "interpretation": "Current-source end-to-end replay of the existing V0 verdict-comparator seed on one authored one-observation workload; no natural-task prevalence claim."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(), "passed": result["passed"],
                      "checks": sum(checks.values()), "check_count": len(checks),
                      "cells": cells}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
