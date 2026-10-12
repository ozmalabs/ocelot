#!/usr/bin/env python3
"""Validate bound × relation factorial and reconcile GenInfer native work."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/substrate_geninfer_training_work_profile_v2_20261006.json"
OUT = ROOT / "evaluation/reports/substrate_geninfer_training_work_profile_v2_analysis_20261006.json"
RUNNER = ROOT / "evaluation/substrate_capability/substrate_geninfer_training_work_profile_v2.py"
ANALYZER = Path(__file__).resolve()
BASE_PROFILE = ROOT / "evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_TRAINING_WORK_PROFILE_V2_PREREG_20261006.md"
V1 = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expected_cases():
    return [
        {"id": f"positive_n{n}_b{bound}_r{rep}", "kind": "positive", "n": n,
         "bound": bound, "repeat": rep}
        for n in (4, 16, 64) for bound in (3, 5, 7) for rep in (1, 2, 3)
    ]


def main():
    data = json.loads(CAPTURE.read_text())
    rows = data.get("cases", [])
    errors = []
    file_hashes = {"runner_sha256": RUNNER, "protocol_sha256": PROTOCOL,
                   "analyzer_sha256": ANALYZER, "base_profile_sha256": BASE_PROFILE,
                   "v1_runner_sha256": V1}
    for key, path in file_hashes.items():
        if data.get(key) != sha(path):
            errors.append(f"{key} differs from current source")
    if data.get("case_spec") != expected_cases() or len(rows) != 27 or data.get("worker_count") != 27:
        errors.append("capture does not contain the preregistered 27-cell factorial")
    if not data.get("source_stable"):
        errors.append("capture reports source drift")
    source_maps = data.get("source_sha256_by_worker", [])
    if len(source_maps) != 27 or any(x != source_maps[0] for x in source_maps[1:]):
        errors.append("worker source maps differ or are incomplete")
    if len({row.get("pid") for row in rows}) != 27:
        errors.append("workers did not execute in distinct processes")

    indexed = {(row.get("case", {}).get("id"), row.get("variant", "64")): row for row in rows}
    if len(indexed) != 27:
        errors.append("duplicate or missing case IDs")
    hashes = {row.get("source_before", {}).get("native_sha256") for row in rows}
    if len(hashes) != 1:
        errors.append("native artifact hash varies across profile workers")

    by_cell = {}
    for case in expected_cases():
        row = indexed.get((case["id"], "64"))
        if row is None:
            errors.append(f"missing {case['id']}")
            continue
        if row.get("case") != case:
            errors.append(f"{case['id']}: locked case mismatch")
        if not row.get("source_stable") or row["source_before"] != row["source_after"]:
            errors.append(f"{case['id']}: worker source drift")
        if row.get("expected_bound") != case["bound"] or row.get("matrix") != [case["bound"]-1, 1, 1, 1]:
            errors.append(f"{case['id']}: transformation matrix/bound mismatch")
        if not row.get("target_acquired_during_training") or not row.get("training_oracle_exact_match"):
            errors.append(f"{case['id']}: training semantic gate failed")
        if not row.get("heldout_exact_match") or row.get("corrupted_heldout_exact_match"):
            errors.append(f"{case['id']}: held-out semantic gate failed")
        counters = row.get("train", {}).get("gen_infer_counters", {})
        required = ("gen_infer_requests", "gen_infer_cache_hits", "gen_infer_kernel_calls",
                    "gen_infer_eligible_bases", "gen_infer_matrix_attempts", "gen_infer_apply_rejects",
                    "gen_infer_candidate_rejects", "gen_infer_residual_rejects", "gen_infer_candidate_survivors")
        if any(key not in counters for key in required):
            errors.append(f"{case['id']}: missing GenInfer counters")
        bound_counts = {int(k.split(":", 1)[1]): int(v) for k, v in counters.items()
                        if k.startswith("gen_infer_bases_by_bound:")}
        attempts_expected = sum(((2*b+1)**4-1)*count for b, count in bound_counts.items())
        attempts_outcomes = sum(counters.get(k, 0) for k in (
            "gen_infer_apply_rejects", "gen_infer_candidate_rejects",
            "gen_infer_residual_rejects", "gen_infer_candidate_survivors"))
        if counters.get("gen_infer_requests") != counters.get("gen_infer_cache_hits", 0)+counters.get("gen_infer_kernel_calls", 0):
            errors.append(f"{case['id']}: request/cache/kernel reconciliation failed")
        if counters.get("gen_infer_eligible_bases") != sum(bound_counts.values()):
            errors.append(f"{case['id']}: eligible-base reconciliation failed")
        if counters.get("gen_infer_matrix_attempts") != attempts_expected or attempts_expected != attempts_outcomes:
            errors.append(f"{case['id']}: matrix-attempt reconciliation failed")
        if set(bound_counts) != {case["bound"]}:
            errors.append(f"{case['id']}: observed bound set {bound_counts} differs from treatment")
        term_counters = row.get("train", {}).get("term_audit_counters", {})
        if any(key not in term_counters for key in ("term_units_total", "term_evals_total",
                                                    "term_unit:GenInfer", "term_eval:GenInfer")):
            errors.append(f"{case['id']}: missing GenInfer term-work audit counters")
        elif term_counters["term_unit:GenInfer"] <= 0:
            errors.append(f"{case['id']}: GenInfer interior work units were not observed")

    cells = {}
    for n in (4, 16, 64):
        for bound in (3, 5, 7):
            cell = [indexed.get((f"positive_n{n}_b{bound}_r{rep}", "64")) for rep in (1, 2, 3)]
            cell = [row for row in cell if row]
            if cell:
                vals = [r["train"]["gen_infer_counters"] for r in cell]
                cells[f"n{n}_b{bound}"] = {
                    "runs": len(cell),
                    "median_audit_enabled_train_wall_ms": statistics.median(r["train"]["closure_wall_ns"] for r in cell)/1e6,
                    "median_train_cpu_ms": statistics.median(r["train"]["closure_cpu_ns"] for r in cell)/1e6,
                    "median_eligible_bases": statistics.median(c["gen_infer_eligible_bases"] for c in vals),
                    "median_matrix_attempts": statistics.median(c["gen_infer_matrix_attempts"] for c in vals),
                    "median_apply_rejects": statistics.median(c["gen_infer_apply_rejects"] for c in vals),
                    "median_candidate_rejects": statistics.median(c["gen_infer_candidate_rejects"] for c in vals),
                    "median_residual_rejects": statistics.median(c["gen_infer_residual_rejects"] for c in vals),
                    "median_candidate_survivors": statistics.median(c["gen_infer_candidate_survivors"] for c in vals),
                    "median_geninfer_term_evaluations": statistics.median(r["train"]["term_audit_counters"]["term_eval:GenInfer"] for r in cell),
                    "median_geninfer_term_units": statistics.median(r["train"]["term_audit_counters"]["term_unit:GenInfer"] for r in cell),
                    "median_all_term_units": statistics.median(r["train"]["term_audit_counters"]["term_units_total"] for r in cell),
                    "median_geninfer_units_per_matrix_attempt": statistics.median(
                        r["train"]["term_audit_counters"]["term_unit:GenInfer"] /
                        r["train"]["gen_infer_counters"]["gen_infer_matrix_attempts"] for r in cell),
                }
    report = {
        "schema": "GenInferTrainingWorkProfileV2Analysis",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gates_pass": not errors, "errors": errors, "capture_sha256": sha(CAPTURE),
        "interpretation_limit": "Three sizes and three bounds characterize this authored 2D family only. Audit-enabled timing is diagnostic; formula-reconciled counters are the primary result.",
        "summary": {"workers": len(rows), "cells": cells},
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "gates_pass": report["gates_pass"],
                      "errors": errors, "summary": report["summary"]}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
