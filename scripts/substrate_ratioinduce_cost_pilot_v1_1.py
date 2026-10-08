#!/usr/bin/env python3
"""Direct-call cost pilot for native RatioInduce; emits immutable raw samples."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate_rs import _native  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_ratioinduce_cost_pilot_v1_1_20260926.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_RATIOINDUCE_COST_PILOT_PREREG_20260926.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_RATIOINDUCE_COST_PILOT_V1_1_AMENDMENT_20260926.md"
RUNNER = Path(__file__).resolve()
REPEATS = 7
RATIOS = (2, 3, 5, 7)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(scale: int, points: int, dims: int) -> list[list[object]]:
    if points < 2:
        raise ValueError("fixture needs at least two relations")
    rows = []
    for i in range(points):
        coords = [int(round(i * (RATIOS[d] * scale) / (points - 1)))
                  for d in range(dims)]
        rows.append(["cell", *coords, i])
    return rows


def population(n: int, points: int, dims: int) -> list[list[list[object]]]:
    return [frame(i + 1, points, dims) for i in range(n)]


def case(sub, n: int, points: int, dims: int, factor: str, level: int) -> dict:
    pop = population(n, points, dims)
    term = {"type": "RatioInduce",
            "population": {"type": "Lit", "value": pop},
            "resolution": 0, "field": ""}
    wall, cpu, output = [], [], None
    for repetition in range(1, REPEATS + 1):
        cpu0, wall0 = time.process_time_ns(), time.perf_counter_ns()
        output = sub.evaluate(term, {})
        wall.append(time.perf_counter_ns() - wall0)
        cpu.append(time.process_time_ns() - cpu0)
    expected_ratios = []
    ref = RATIOS[0]
    for slot in range(1, dims):
        from math import gcd
        g = gcd(RATIOS[slot], ref)
        expected_ratios.extend([slot + 1, RATIOS[slot] // g, ref // g])
    expected_checked = n * (dims - 1)
    passed = (output.get("explained") is True
              and int(output.get("n_frames") or 0) == n
              and list(output.get("ratios") or []) == expected_ratios
              and int(output.get("checked") or 0) == expected_checked)
    return {
        "factor": factor, "level": level, "frames": n,
        "relations_per_frame": points, "coord_dimensions": dims,
        "input_relations": n * points, "expected_checked": expected_checked,
        "observed_checked": int(output.get("checked") or 0),
        "explained": output.get("explained"),
        "observed_ratio_triples": list(output.get("ratios") or []),
        "expected_ratio_triples": expected_ratios,
        "success": passed,
        "wall_time_ns": wall, "cpu_time_ns": cpu,
        "median_wall_time_ns": int(statistics.median(wall)),
        "median_cpu_time_ns": int(statistics.median(cpu)),
    }


def main() -> int:
    sub = _native.Substrate()
    # A single empty-signature part supplies typed coordinate slots; RatioInduce
    # reads dim_types but derives all extents from the supplied population.
    sub.add_node("ShapeSignature", {
        "name": "ratio_cost_probe", "signature": json.dumps([["cell", 0, 0, 0, 0, 0]]),
        "kind": "faculty", "faculty": "ratio_cost_probe",
        "dim_types": ["pred", "coord:0", "coord:1", "coord:2", "coord:3", "val"],
    })

    cells = []
    for i, n in enumerate((2, 8, 32, 128), 1):
        cells.append(case(sub, n, 16, 2, "frames", i))
    for i, p in enumerate((4, 16, 64, 256), 1):
        cells.append(case(sub, 16, p, 2, "relations_per_frame", i))
    for i, d in enumerate((2, 3, 4), 1):
        cells.append(case(sub, 16, 16, d, "coord_dimensions", i))

    extension = Path(_native.__file__).resolve()
    source_paths = [
        str(RUNNER.relative_to(ROOT)),
        str(PREREG.relative_to(ROOT)),
        str(AMENDMENT.relative_to(ROOT)),
        "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
        "runners/dsl/src/jsonio.rs", "runners/dsl/python/substrate_rs/_native.build.json",
    ]
    report = {
        "schema_version": 1,
        "run_id": "substrate-ratioinduce-cost-pilot-v1.1-20260926",
        "status": "pilot",
        "engine": provenance_line(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_tree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "processor": platform.processor(), "cpu_count": os.cpu_count(),
                        "peak_rss_process_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)},
        "protocol": {"amendment": str(AMENDMENT.relative_to(ROOT)),
                     "repeats": REPEATS, "warmup": "none beyond engine_preamble/module boot",
                     "factor_levels": {"frames": [2, 8, 32, 128],
                                       "relations_per_frame": [4, 16, 64, 256],
                                       "coord_dimensions": [2, 3, 4]},
                     "timed_region": "native Substrate.evaluate of RatioInduce; population built before timer",
                     "resolution": 0},
        "provenance": {
            "sha256": {rel: sha(ROOT / rel) for rel in source_paths},
            "native_extension": str(extension), "native_sha256": sha(extension),
        },
        "cells": cells,
        "failed_cells": [c for c in cells if not c["success"]],
        "claim_boundary": "One exact positive family; fixed D/P/N sweeps. Direct operator only; no closure, extraction, mint/redecode, natural workload, or general asymptotic claim.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": report["run_id"], "engine": report["engine"],
                      "cells": len(cells), "failed_cells": len(report["failed_cells"]),
                      "output": str(OUT)}, indent=2))
    return 0 if not report["failed_cells"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
