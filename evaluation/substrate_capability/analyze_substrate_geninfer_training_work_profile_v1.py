#!/usr/bin/env python3
"""Validate GenInfer candidate-work reconciliation and summarize by input size."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/substrate_geninfer_training_work_profile_v1_20261006.json"
OUT = ROOT / "evaluation/reports/substrate_geninfer_training_work_profile_v1_analysis_20261006.json"
RUNNER = ROOT / "evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py"
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_TRAINING_WORK_PROFILE_V1_PREREG_20261006.md"
V1 = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    data = json.loads(CAPTURE.read_text())
    rows = data.get("cases", [])
    errors = []
    for key, path in (("runner_sha256", RUNNER), ("analyzer_sha256", ANALYZER),
                      ("protocol_sha256", PROTOCOL), ("v1_runner_sha256", V1)):
        if data.get(key) != sha(path):
            errors.append(f"{key} differs from captured source")
    if len(rows) != 9 or data.get("worker_count") != 9 or not data.get("source_stable"):
        errors.append("expected nine source-stable fresh workers")
    source_maps = data.get("source_sha256_by_worker", [])
    if len(source_maps) != 9 or any(x != source_maps[0] for x in source_maps[1:]):
        errors.append("worker source manifests differ or are incomplete")
    if len({row.get("pid") for row in rows}) != 9:
        errors.append("workers did not run in distinct processes")

    by_size = {}
    for n in (4, 16, 64):
        cell = [row for row in rows if row.get("case", {}).get("n") == n]
        if len(cell) != 3:
            errors.append(f"n={n}: expected three repetitions")
        for row in cell:
            case = row["case"]
            if case != {"id": f"positive_n{n}_b5_r{case['repeat']}", "kind": "positive", "n": n, "bound": 5, "repeat": case["repeat"]}:
                errors.append(f"n={n}: unexpected case")
            if not row.get("source_stable") or row["source_before"] != row["source_after"]:
                errors.append(f"{case['id']}: source drift")
            if not row.get("target_acquired_during_training") or not row.get("training_oracle_exact_match"):
                errors.append(f"{case['id']}: training acquisition or oracle failed")
            if not row.get("heldout_exact_match") or row.get("corrupted_heldout_exact_match"):
                errors.append(f"{case['id']}: held-out semantic gate failed")
            counters = row.get("train", {}).get("gen_infer_counters", {})
            required = ("gen_infer_requests", "gen_infer_cache_hits", "gen_infer_kernel_calls",
                        "gen_infer_eligible_bases", "gen_infer_matrix_attempts", "gen_infer_apply_rejects",
                        "gen_infer_candidate_rejects", "gen_infer_residual_rejects", "gen_infer_candidate_survivors")
            if any(key not in counters for key in required):
                errors.append(f"{case['id']}: missing native GenInfer work counters")
            bases_by_bound = {int(k.split(":", 1)[1]): int(v) for k, v in counters.items()
                              if k.startswith("gen_infer_bases_by_bound:")}
            attempts = sum(((2 * bound + 1) ** 4 - 1) * count for bound, count in bases_by_bound.items())
            partition = sum(counters.get(key, 0) for key in (
                "gen_infer_apply_rejects", "gen_infer_candidate_rejects",
                "gen_infer_residual_rejects", "gen_infer_candidate_survivors"))
            if counters.get("gen_infer_requests") != counters.get("gen_infer_cache_hits", 0) + counters.get("gen_infer_kernel_calls", 0):
                errors.append(f"{case['id']}: request/cache/kernel counts do not reconcile")
            if counters.get("gen_infer_eligible_bases") != sum(bases_by_bound.values()):
                errors.append(f"{case['id']}: eligible bases do not reconcile")
            if counters.get("gen_infer_matrix_attempts") != attempts or attempts != partition:
                errors.append(f"{case['id']}: matrix attempt count or rejection partition does not reconcile")
        if cell:
            fields = ("gen_infer_requests", "gen_infer_kernel_calls", "gen_infer_eligible_bases",
                      "gen_infer_matrix_attempts", "gen_infer_apply_rejects", "gen_infer_candidate_rejects",
                      "gen_infer_residual_rejects", "gen_infer_candidate_survivors")
            by_size[str(n)] = {
                "runs": len(cell),
                "median_audit_enabled_train_wall_ms": statistics.median(r["train"]["closure_wall_ns"] for r in cell) / 1e6,
                "median_train_cpu_ms": statistics.median(r["train"]["closure_cpu_ns"] for r in cell) / 1e6,
                "median_closure_work": statistics.median(r["train"]["closure_work"] for r in cell),
                "median_bound_counts": {
                    key: statistics.median(
                        sum(int(v) for k, v in r["train"]["gen_infer_counters"].items()
                            if k == "gen_infer_bases_by_bound:" + key)
                        for r in cell)
                    for key in sorted({k.split(":", 1)[1] for r in cell
                                       for k in r["train"]["gen_infer_counters"]
                                       if k.startswith("gen_infer_bases_by_bound:")})
                },
                "median_gen_infer": {
                    field.removeprefix("gen_infer_"): statistics.median(r["train"]["gen_infer_counters"].get(field, 0) for r in cell)
                    for field in fields
                },
            }
    report = {
        "schema": "GenInferTrainingWorkProfileV1Analysis",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gates_pass": not errors, "errors": errors, "capture_sha256": sha(CAPTURE),
        "interpretation_limit": "Scale-audit counters attribute discrete candidate work, not time per candidate phase. Timings include enabled audit instrumentation and are diagnostic only.",
        "summary": {"workers": len(rows), "by_relation_count": by_size},
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "gates_pass": report["gates_pass"],
                      "errors": errors, "summary": report["summary"]}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
