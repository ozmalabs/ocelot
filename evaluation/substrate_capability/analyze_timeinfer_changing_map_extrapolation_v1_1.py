#!/usr/bin/env python3
"""Independent outcome checks for TimeInfer changing-map baseline v1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "evaluation/reports/timeinfer_changing_map_extrapolation_v1_1_20261006.json"
LOCK = ROOT / "evaluation/substrate_capability/timeinfer_changing_map_extrapolation_v1_1_lock_20261006.json"
RUNNER = ROOT / "evaluation/substrate_capability/timeinfer_changing_map_extrapolation_v1_1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/TIMEINFER_CHANGING_MAP_EXTRAPOLATION_V1_1_PREREG_20261006.md"
CASES = ("translate_order2", "changing_linear_shear", "changing_quadratic_shear",
         "static_quadratic_shear", "random_translation")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity_view(row: dict) -> dict:
    return {key: row[key] for key in ("frame_count", "frames", "withheld_next_frame",
            "direct_fields", "exact_heldout_transfer", "rule_observation_status", "time_mints")}


def main() -> int:
    report = json.loads(REPORT.read_text())
    lock = json.loads(LOCK.read_text())
    if report.get("locked_inputs") != lock.get("inputs") or report.get("post_run_inputs") != lock.get("inputs"):
        raise SystemExit("capture did not preserve the locked inputs")
    if report.get("source_stable") is not True:
        raise SystemExit("capture source stability failed")
    expected = [(case, rep) for case in CASES for rep in range(3)]
    workers = report.get("workers", [])
    actual = [(row.get("case"), row.get("replicate")) for row in workers]
    if actual != expected or len(workers) != 15:
        raise SystemExit("worker schedule mismatch")
    grouped: dict[str, list[dict]] = {}
    for row in workers:
        if row.get("source_stable") is not True or row.get("direct_elapsed_ns", 0) <= 0:
            raise SystemExit("worker source/timing gate failed")
        if not row.get("engine_provenance"):
            raise SystemExit("missing engine provenance")
        grouped.setdefault(row["case"], []).append(row)
    parity = {case: all(parity_view(pair[0]) == parity_view(row) for row in pair[1:])
              for case, pair in grouped.items()}
    if not all(parity.values()):
        raise SystemExit("paired repeat semantic parity failed")
    summaries = {}
    for case, rows in grouped.items():
        first = rows[0]
        fields = first["direct_fields"]
        explained = fields.get("explained") is True
        predicted = fields.get("predicted")
        transfer = isinstance(predicted, (list, tuple)) and sorted(map(tuple, predicted)) == sorted(map(tuple, first["withheld_next_frame"]))
        mints = bool(first.get("time_mints"))
        summaries[case] = {"replicate_count": len(rows), "repeat_parity": parity[case],
            "direct_explained": [r["direct_fields"].get("explained") for r in rows],
            "direct_kind": [r["direct_fields"].get("kind") for r in rows],
            "direct_order": [r["direct_fields"].get("order") for r in rows],
            "exact_heldout_transfer": [isinstance(r["direct_fields"].get("predicted"), (list, tuple)) and sorted(map(tuple, r["direct_fields"]["predicted"])) == sorted(map(tuple, r["withheld_next_frame"])) for r in rows],
            "rule_status": [r.get("rule_observation_status") for r in rows],
            "time_mint_count": [len(r.get("time_mints", [])) for r in rows],
            "median_direct_elapsed_ns": sorted(r["direct_elapsed_ns"] for r in rows)[1],
            "consistent_acceptance": bool(explained and transfer),
            "explained_without_exact_transfer": bool(explained and not transfer),
            "mint_without_exact_transfer": bool(mints and not transfer)}
    if summaries["translate_order2"]["direct_order"] != [2, 2, 2] or \
            summaries["translate_order2"]["exact_heldout_transfer"] != [True, True, True]:
        raise SystemExit("order-2 translation positive control failed")
    if summaries["random_translation"]["exact_heldout_transfer"] != [False, False, False] or \
            summaries["random_translation"]["time_mint_count"] != [0, 0, 0]:
        raise SystemExit("random-trajectory refusal control failed")
    result = {"schema": "TimeInferChangingMapV1_1Analysis", "passed": True,
              "worker_count": len(workers), "repeat_parity": parity,
              "per_case": summaries,
              "source_lock_sha256": sha(LOCK), "capture_sha256": sha(REPORT),
              "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(RUNNER),
              "interpretation_limit": "authored finite sequences; direct-Term baseline only; not natural prevalence or general nonlinear capability"}
    out = ROOT / "evaluation/reports/timeinfer_changing_map_extrapolation_v1_1_analysis_20261006.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": out.relative_to(ROOT).as_posix(), "passed": True,
                      "worker_count": len(workers), "per_case": summaries}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
