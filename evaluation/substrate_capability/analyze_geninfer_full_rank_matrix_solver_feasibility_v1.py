#!/usr/bin/env python3
"""Independent integrity and exact-output analysis for the full-rank probe."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/geninfer_full_rank_matrix_solver_feasibility_v1.py"
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FULL_RANK_MATRIX_SOLVER_FEASIBILITY_V1_PREREG_20261006.md"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply(matrix, point):
    return [sum(v * point[j] for j, v in enumerate(row)) for row in matrix]


def rank(rows):
    a = [list(map(float, row)) for row in rows]
    r = 0
    for c in range(len(a[0]) if a else 0):
        pivot = next((i for i in range(r, len(a)) if a[i][c] != 0), None)
        if pivot is None:
            continue
        a[r], a[pivot] = a[pivot], a[r]
        scale = a[r][c]
        a[r] = [x / scale for x in a[r]]
        for i in range(len(a)):
            if i != r and a[i][c]:
                k = a[i][c]
                a[i] = [x - k * y for x, y in zip(a[i], a[r])]
        r += 1
    return r


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "evaluation/reports/geninfer_full_rank_matrix_solver_feasibility_v1_20261006.json"
    payload = json.loads(path.read_text())
    errors = []
    if payload.get("runner_sha256") != sha(RUNNER):
        errors.append("runner hash mismatch")
    if payload.get("analyzer_sha256") != sha(ANALYZER):
        errors.append("analyzer hash mismatch")
    if payload.get("protocol_sha256") != sha(PROTOCOL):
        errors.append("protocol hash mismatch")
    if [case.get("dimension") for case in payload.get("cases", [])] != [1, 2, 3]:
        errors.append("dimension coverage mismatch")
    for case in payload.get("cases", []):
        d = case["dimension"]
        matrix = case["recovered_matrix"]
        if len(matrix) != d or any(len(row) != d for row in matrix):
            errors.append(f"d={d}: recovered matrix shape mismatch")
            continue
        if any(apply(matrix, x) != y for x, y in zip(case["training_source"], case["training_target"])):
            errors.append(f"d={d}: training exactness failed")
        if any(apply(matrix, x) != y for x, y in zip(case["heldout_source"], case["heldout_target"])):
            errors.append(f"d={d}: held-out exactness failed")
        diff = [[x[j] - case["training_source"][0][j]
                 for j in range(d)] for x in case["rank_deficient_source"][1:]]
        if rank(diff) >= d or not case.get("rank_deficient_abstained") or case.get("rank_deficient_result") is not None:
            errors.append(f"d={d}: rank-deficient abstention gate failed")
        bound = case["matrix_bound"]
        expected = (2 * bound + 1) ** (d * d) - 1
        if case.get("exhaustive_candidate_count") != expected:
            errors.append(f"d={d}: exhaustive candidate formula mismatch")
        if case.get("solver_wall_ns", 0) <= 0:
            errors.append(f"d={d}: missing solver timing")
    report = {"schema": "GenInferFullRankMatrixSolverFeasibilityV1Analysis",
              "capture_sha256": sha(path), "errors": errors, "gates_pass": not errors,
              "cases": len(payload.get("cases", [])),
              "interpretation_limit": payload.get("interpretation_limit")}
    out = path.with_name(path.stem.replace("_20261006", "_analysis_20261006") + ".json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(out.relative_to(ROOT)), "errors": errors,
                      "gates_pass": not errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
