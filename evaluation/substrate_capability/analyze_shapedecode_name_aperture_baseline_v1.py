#!/usr/bin/env python3
"""Independent analysis of the ShapeDecode name-aperture scan baseline."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/shapedecode_name_aperture_baseline_v1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_name_aperture_baseline_v1_analysis_20261005.json"
HELPER_KINDS = {
    "dynamic_helper_invocation", "helper_codebook_population_node",
    "helper_node_attribute_examined", "helper_codebook_part_parsed",
    "helper_search_candidate", "helper_candidate_part_scored",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    capture, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    rows = capture.get("rows", [])
    checks = {
        "locked_cases_complete": len(rows) == len(lock["cases"]) == 24 and
            {r.get("case", {}).get("id") for r in rows} == {c["id"] for c in lock["cases"]},
        "capture_references_lock": capture.get("lock_sha256") == sha(LOCK),
        "fresh_process_per_case": len({r.get("pid") for r in rows}) == len(rows),
        "source_lock_stable_each_worker": all(r.get("source_stable") and
            r.get("source_before") == lock["source_manifest"] == r.get("source_after") for r in rows),
        "no_worker_failures": not capture.get("process_failures") and all("worker_error" not in r for r in rows),
        "all_cases_select_exact_target": all(r.get("identified_as") == "r00" and
            r.get("readback", {}).get("said") == "r00" and
            r.get("readback", {}).get("status") == "xf_done" for r in rows),
        "effective_codebook_population_includes_boot_parts": all(
            r.get("shape_signature_count") == r.get("case", {}).get("size", -17) + 17 for r in rows),
        "trace_rows_present_and_complete": all(
            (not r["case"]["trace"] and not r["runtime_work_trace"]["rows"]) or
            (r["case"]["trace"] and r["runtime_work_trace"]["dropped"] == 0 and
             r["runtime_work_trace"]["shape_decode_counts"].get("helper_codebook_population_node", 0) > 0)
            for r in rows),
    }
    paired = []
    cells = []
    for size in (16, 32, 64, 128):
        size_rows = [r for r in rows if r.get("case", {}).get("size") == size]
        cell_pairs = []
        for rep in (0, 1, 2):
            plain = next((r for r in size_rows if r["case"]["replicate"] == rep and not r["case"]["trace"]), None)
            traced = next((r for r in size_rows if r["case"]["replicate"] == rep and r["case"]["trace"]), None)
            same = bool(plain and traced and plain.get("identified_as") == traced.get("identified_as")
                        and plain.get("closure_work") == traced.get("closure_work"))
            cell_pairs.append(same)
            paired.append({"size": size, "replicate": rep, "same_winner_and_closure_work": same,
                           "untraced_wall_ns": plain.get("closure_wall_ns") if plain else None,
                           "untraced_cpu_ns": plain.get("closure_cpu_ns") if plain else None,
                           "traced_helper_work": traced.get("runtime_work_trace", {}).get("shape_decode_counts", {}) if traced else {}})
        checks[f"trace_timing_pair_parity_n{size}"] = all(cell_pairs)
        plain_times = [r["closure_wall_ns"] for r in size_rows if not r["case"]["trace"] and "closure_wall_ns" in r]
        plain_cpu = [r["closure_cpu_ns"] for r in size_rows if not r["case"]["trace"] and "closure_cpu_ns" in r]
        trace_counts = {}
        for kind in HELPER_KINDS:
            trace_counts[kind] = [r.get("runtime_work_trace", {}).get("shape_decode_counts", {}).get(kind, 0)
                                  for r in size_rows if r["case"]["trace"]]
        med = lambda xs: int(statistics.median(xs)) if xs else None
        cells.append({"size": size, "replicates_per_trace_state": 3,
                      "effective_shape_signature_population": sorted({r["shape_signature_count"] for r in size_rows}),
                      "untraced_closure_wall_ns": {"median": med(plain_times), "min": min(plain_times), "max": max(plain_times)},
                      "untraced_closure_cpu_ns": {"median": med(plain_cpu), "min": min(plain_cpu), "max": max(plain_cpu)},
                      "traced_shape_decode_work_counts": {
                          kind: {"median": med(vals), "min": min(vals), "max": max(vals)}
                          for kind, vals in trace_counts.items() if vals}})
    visits = [c["traced_shape_decode_work_counts"].get("helper_codebook_population_node", {}).get("median", 0)
              for c in cells]
    checks["population_visit_medians_increase_with_codebook_size"] = all(a < b for a, b in zip(visits, visits[1:]))
    checks["one_observation_one_target_per_worker"] = all(
        r.get("readback", {}).get("truth") == 0 and r.get("readback", {}).get("said_idx") == 0
        for r in rows)
    result = {
        "schema": "ShapeDecodeNameApertureBaselineV1Analysis",
        "run_id": "shapedecode-name-aperture-baseline-v1-analysis-20261005",
        "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
        "checks": checks, "passed": all(checks.values()),
        "worker_count": len(rows), "cells": cells, "paired_rows": paired,
        "interpretation": (
            "Current scan-path baseline for one authored candidate-at-a-time ShapeDecode route. "
            "The work counters count operations, not CPU share. Synthetic codebook scaling does not "
            "establish natural workload prevalence or an index speedup."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "passed": result["passed"],
                      "checks": sum(checks.values()), "check_count": len(checks),
                      "population_visit_medians": visits}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
