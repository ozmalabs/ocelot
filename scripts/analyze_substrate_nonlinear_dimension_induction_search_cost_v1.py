#!/usr/bin/env python3
"""Derive exact GenInfer matrix-loop lower bounds from the locked v1.3 fixtures."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "evaluation/substrate_capability/nonlinear_dimension_induction_v1_3_lock_20261005.json"
RAW = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_v1_3_20261005.json"
OUT = ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_search_cost_v1_20261005.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_extent(rows: list[list[object]], slot: int) -> int:
    vals = [int(row[slot]) for row in rows]
    return max(vals) - min(vals) if vals else 0


def main() -> int:
    lock = json.loads(LOCK.read_text())
    raw = json.loads(RAW.read_text())
    if raw.get("lock_sha256") != digest(LOCK):
        raise SystemExit("capture does not match the locked v1.3 protocol")
    if not raw.get("source_native_stable"):
        raise SystemExit("capture did not preserve its source/native lock")

    cases = [c for c in lock["inputs"]["cases"] if c["family"] == "coupled_quadratic"]
    rows = []
    for case in cases:
        for stage, target_key, base_key in (
            ("train", "training_target", "training_base"),
            ("transfer", "transfer_target", "transfer_base"),
        ):
            target, bases = case[target_key], [case[base_key]]
            # The harness adds both named ShapeSignatures to the codebook.
            # Both have the locked coord:r/coord:c type labels and are eligible
            # for GenInfer; additional boot-core parts can only increase work.
            if stage == "train":
                bases.append(case["transfer_base"])
            else:
                bases.append(case["training_base"])
            goal_bound = max(normalized_extent(target, 2), normalized_extent(target, 3))
            per_base = []
            for base in bases:
                base_bound = max(normalized_extent(base, 2), normalized_extent(base, 3))
                bound = max(goal_bound, base_bound)
                per_base.append({
                    "bound": bound,
                    "matrix_candidates": (2 * bound + 1) ** 4 - 1,
                })
            rows.append({
                "replicate": case["replicate"],
                "stage": stage,
                "goal_bound": goal_bound,
                "explicit_eligible_base_count": len(per_base),
                "explicit_bases": per_base,
                "minimum_matrix_attempts_per_geninfer": sum(x["matrix_candidates"] for x in per_base),
            })

    transfer = [r["minimum_matrix_attempts_per_geninfer"] for r in rows if r["stage"] == "transfer"]
    train = [r["minimum_matrix_attempts_per_geninfer"] for r in rows if r["stage"] == "train"]
    samples = [s for s in raw["samples"] if s["family"] == "coupled_quadratic" and s["enabled"]]
    analysis = json.loads((ROOT / "evaluation/reports/substrate_nonlinear_dimension_induction_v1_3_analysis_20261005.json").read_text())
    outcomes = {
        "n": len(samples),
        "all_train_and_transfer_statuses_minted": all(all(e["status"] == "minted" for e in s["events"]) for s in samples),
        "capability_axes_added_per_event": sorted({e["quanta_added"] for s in samples for e in s["events"]}),
        "dimension_generator_counts_before_after": sorted({(len(s["initial_generators"]), len(s["final_generators"])) for s in samples}),
        "exact_new_linear_transfer_count": sum(
            bool(analysis.get("independent_transfer_scoring", {}).get(f"coupled_quadratic:enabled:{s['replicate']}", {}).get("exact_transfer_prediction"))
            for s in samples
        ),
    }
    result = {
        "schema_version": 1,
        "run_id": raw["run_id"],
        "lock_sha256": digest(LOCK),
        "derived_from": [str(LOCK.relative_to(ROOT)), str(RAW.relative_to(ROOT))],
        "source_formula": "GenInfer loops m00,m01,m10,m11 over [-B,B], excluding identity; candidates per eligible base = (2B+1)^4 - 1.",
        "scope_note": "Counts are an exact lower bound from the two harness-supplied typed bases only. Unscoped eligible boot-core ShapeSignatures, if any, add attempts. This is per GenInfer evaluation, not a claim that one evaluation occurred per whole rule closure.",
        "train_attempts_per_geninfer": {"min": min(train), "max": max(train)},
        "transfer_attempts_per_geninfer": {"min": min(transfer), "max": max(transfer)},
        "transfer_to_train_candidate_ratio": round(min(transfer) / min(train), 3),
        "enabled_outcomes": outcomes,
        "cells": rows,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("train_attempts_per_geninfer", "transfer_attempts_per_geninfer", "transfer_to_train_candidate_ratio", "enabled_outcomes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
