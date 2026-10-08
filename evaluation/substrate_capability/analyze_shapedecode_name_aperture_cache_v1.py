#!/usr/bin/env python3
"""Independent parity and cost analysis for ShapeDecode cache v1."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/shapedecode_name_aperture_cache_v1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_cache_v1_lock_20261005.json"
BASELINE = ROOT / "evaluation/reports/shapedecode_name_aperture_baseline_v1_analysis_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_name_aperture_cache_v1_analysis_20261005.json"
KINDS = {
    "dynamic_helper_invocation", "helper_codebook_population_node",
    "helper_node_attribute_examined", "helper_codebook_part_parsed",
    "helper_search_candidate", "helper_candidate_part_scored",
    "helper_codebook_cache_miss", "helper_codebook_cache_hit",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def project(row: dict) -> dict:
    r = row.get("result", {})
    readback = dict(r.get("readback", {}))
    readback.pop("tag", None)
    return {"identified_as": r.get("identified_as"), "readback": readback,
            "closure_work": r.get("closure_work"),
            "shape_signature_count": r.get("shape_signature_count")}


def counts(row: dict) -> dict[str, int]:
    trace = row.get("result", {}).get("runtime_work_trace", {})
    out = {kind: 0 for kind in KINDS}
    for event in trace.get("rows", []):
        if len(event) == 6 and str(event[3]) in KINDS and int(event[4] or 0) == 1:
            out[str(event[3])] += int(event[5])
    return out


def main() -> int:
    cap, lock, baseline = (json.loads(p.read_text()) for p in (CAPTURE, LOCK, BASELINE))
    rows = cap.get("rows", [])
    expected = {c["id"] for c in lock["cases"]}
    actual = {r.get("case", {}).get("id") for r in rows}
    checks = {
        "locked_80_case_panel": len(rows) == 80 and actual == expected,
        "capture_references_lock": cap.get("lock_sha256") == sha(LOCK),
        "fresh_process_per_case": len({r.get("pid") for r in rows}) == 80,
        "worker_source_manifests_stable": all(r.get("source_stable") and
            r.get("source_before") == lock["manifest"] == r.get("source_after") for r in rows),
        "no_worker_failures": not cap.get("process_failures") and all("worker_error" not in r for r in rows),
        "all_workers_select_exact_target": all(r.get("result", {}).get("identified_as") == "r00" and
            r.get("result", {}).get("readback", {}).get("status") == "xf_done" for r in rows),
        "traces_complete": all(not r["case"]["trace"] or
            r.get("result", {}).get("runtime_work_trace", {}).get("dropped") == 0 for r in rows),
    }
    base_visits = {c["size"]: c["traced_shape_decode_work_counts"][
        "helper_codebook_population_node"]["median"] for c in baseline["cells"]}
    base_calls = {c["size"]: c["traced_shape_decode_work_counts"][
        "dynamic_helper_invocation"]["median"] for c in baseline["cells"]}
    scan_baseline_ok = True
    trace_parity_ok = True
    pair_parity_ok = True
    cells = []
    paired = []
    for size in (16, 32, 64, 128):
        size_rows = [r for r in rows if r.get("case", {}).get("size") == size]
        for rep in range(5):
            variants = {(r["case"]["cache_mode"], bool(r["case"]["trace"])): r
                        for r in size_rows if r["case"]["replicate"] == rep}
            scan_plain, scan_trace = variants.get(("scan", False)), variants.get(("scan", True))
            cache_plain, cache_trace = variants.get(("cached", False)), variants.get(("cached", True))
            if not all((scan_plain, scan_trace, cache_plain, cache_trace)):
                pair_parity_ok = trace_parity_ok = scan_baseline_ok = False
                continue
            ps = [project(x) for x in (scan_plain, cache_plain)]
            same = ps[0] == ps[1]
            pair_parity_ok &= same
            trace_parity_ok &= (project(scan_plain) == project(scan_trace) ==
                                project(cache_plain) == project(cache_trace))
            cs, cc = counts(scan_trace), counts(cache_trace)
            scan_baseline_ok &= (cs["helper_codebook_population_node"] == base_visits[size]
                                 and cs["dynamic_helper_invocation"] == base_calls[size])
            paired.append({"size": size, "effective_population": size + 17,
                           "replicate": rep, "outputs_and_work_match": same,
                           "scan_untraced_wall_ns": scan_plain["result"]["closure_wall_ns"],
                           "cached_untraced_wall_ns": cache_plain["result"]["closure_wall_ns"],
                           "scan_untraced_cpu_ns": scan_plain["result"]["closure_cpu_ns"],
                           "cached_untraced_cpu_ns": cache_plain["result"]["closure_cpu_ns"],
                           "scan_trace": cs, "cached_trace": cc,
                           "scan_trace_dropped": scan_trace["result"]["runtime_work_trace"]["dropped"],
                           "cached_trace_dropped": cache_trace["result"]["runtime_work_trace"]["dropped"]})
        cell = {}
        for mode in ("scan", "cached"):
            arm = [r for r in size_rows if r["case"]["cache_mode"] == mode]
            plain = [r["result"] for r in arm if not r["case"]["trace"]]
            traced = [counts(r) for r in arm if r["case"]["trace"]]
            summaries = {}
            for kind in sorted(KINDS):
                vals = [x[kind] for x in traced]
                summaries[kind] = {"median": int(statistics.median(vals)), "min": min(vals), "max": max(vals)}
            cell[mode] = {
                "untraced_wall_ns": {"median": int(statistics.median(x["closure_wall_ns"] for x in plain)),
                                     "min": min(x["closure_wall_ns"] for x in plain),
                                     "max": max(x["closure_wall_ns"] for x in plain)},
                "untraced_cpu_ns": {"median": int(statistics.median(x["closure_cpu_ns"] for x in plain)),
                                    "min": min(x["closure_cpu_ns"] for x in plain),
                                    "max": max(x["closure_cpu_ns"] for x in plain)},
                "peak_rss_kib": {"median": int(statistics.median(x["peak_rss_kib"] for x in plain)),
                                 "min": min(x["peak_rss_kib"] for x in plain),
                                 "max": max(x["peak_rss_kib"] for x in plain)},
                "traced_work": summaries,
            }
        scan_work = cell["scan"]["traced_work"]["helper_codebook_population_node"]["median"]
        cached_work = cell["cached"]["traced_work"]["helper_codebook_population_node"]["median"]
        cell["effective_population"] = size + 17
        cell["population_visit_reduction_fraction"] = 1.0 - cached_work / scan_work if scan_work else None
        cell["median_wall_speedup"] = (cell["scan"]["untraced_wall_ns"]["median"] /
                                      cell["cached"]["untraced_wall_ns"]["median"])
        cell["median_cpu_speedup"] = (cell["scan"]["untraced_cpu_ns"]["median"] /
                                     cell["cached"]["untraced_cpu_ns"]["median"])
        cells.append({"authored_size": size, **cell})
    checks["scan_arm_matches_v1_work_baseline"] = scan_baseline_ok
    checks["paired_scan_cache_output_and_work_parity"] = pair_parity_ok
    checks["traced_untraced_semantic_parity"] = trace_parity_ok
    checks["cache_work_reduces_population_visits_every_size"] = all(
        c["cached"]["traced_work"]["helper_codebook_population_node"]["median"] <
        c["scan"]["traced_work"]["helper_codebook_population_node"]["median"] for c in cells)
    checks["cache_reports_hits_and_misses"] = all(
        c["cached"]["traced_work"]["helper_codebook_cache_hit"]["median"] > 0 and
        c["cached"]["traced_work"]["helper_codebook_cache_miss"]["median"] > 0 for c in cells)
    result = {"schema": "ShapeDecodeNameApertureCacheV1Analysis",
              "run_id": "shapedecode-name-aperture-cache-v1-analysis-20261005",
              "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
              "checks": checks, "passed": all(checks.values()),
              "worker_count": len(rows), "cells": cells, "paired_rows": paired,
              "interpretation": "Paired one-host cache-vs-scan result for a single authored ShapeDecode name-aperture route. No natural task prevalence or general tractability claim follows."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "passed": result["passed"],
                      "checks": sum(checks.values()), "check_count": len(checks),
                      "reductions": [c["population_visit_reduction_fraction"] for c in cells],
                      "speedups": [c["median_wall_speedup"] for c in cells]}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
