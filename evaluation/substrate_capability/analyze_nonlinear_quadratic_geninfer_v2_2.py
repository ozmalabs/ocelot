#!/usr/bin/env python3
"""Independent adjudicator for the locked v2.1 quadratic GenInfer run."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/nonlinear_quadratic_geninfer_v2_2_lock_20261006.json"
RAW = ROOT / "evaluation/reports/nonlinear_quadratic_geninfer_v2_2_raw_20261006.json"
OUT = ROOT / "evaluation/reports/nonlinear_quadratic_geninfer_v2_2_analysis_20261006.json"


def sha(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def oracle(family: str, x: int, y: int) -> tuple[int, int]:
    if family == "linear":
        return x + y, 2 * y
    if family == "coupled":
        return x + x * y, y + x * x
    if family == "cross":
        return x, y + x * y
    if family == "cubic":
        return x, y + x ** 3
    raise ValueError(family)


def payload_projection(row: dict) -> dict:
    return {key: row.get(key) for key in (
        "status", "residual", "dim_infer", "transform_receipts",
        "generator_payloads", "base", "observed_target")}


def normalize(value):
    if isinstance(value, tuple):
        return [normalize(x) for x in value]
    if isinstance(value, list):
        return [normalize(x) for x in value]
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    return value


def main() -> int:
    if not LOCK.is_file() or not RAW.is_file():
        raise SystemExit("missing v2.1 lock or raw capture")
    lock, raw = json.loads(LOCK.read_text()), json.loads(RAW.read_text())
    checks: dict[str, bool] = {}
    checks["raw_schema"] = raw.get("schema") == "NonlinearQuadraticGenInferV2_2Raw"
    checks["lock_hash"] = raw.get("lock_sha256") == sha(LOCK)
    checks["source_stability"] = raw.get("source_and_binaries_stable") is True
    checks["source_hashes_unchanged"] = raw.get("locked_sources_sha256") == raw.get("post_run_sources_sha256") == lock.get("sources_sha256")
    checks["worker_total"] = len(raw.get("workers", [])) == lock.get("worker_count") == 320
    checks["worker_failures_empty"] = raw.get("failures") == []
    checks["capture_complete"] = raw.get("capture_complete") is True and raw.get("completed_count") == lock.get("worker_count")
    schedule = {(r["worker_id"]): r for r in lock["schedule"]}
    workers = {r.get("worker_id"): r for r in raw.get("workers", [])}
    checks["unique_workers"] = len(workers) == len(raw.get("workers", []))
    checks["schedule_exact"] = set(workers) == set(schedule)

    by_key: dict[tuple, dict] = {}
    wrong_binary = []
    oracle_errors = []
    semantic_errors = []
    false_mints = []
    control_errors = []
    counter_errors = []
    for wid, row in workers.items():
        expected = schedule.get(wid)
        if expected is None:
            continue
        key = (expected["condition"], expected["repeat"], expected["feature"], expected["audit"])
        by_key[key] = row
        arm = expected["feature"]
        if row.get("feature") != arm or row.get("audit") != expected["audit"] or row.get("native_sha256") != lock["native_binaries"][arm]["sha256"]:
            wrong_binary.append(wid)
        held = row.get("heldout", {})
        family = {"linear_positive": "linear", "coupled_quadratic": "coupled",
                  "quadratic_cross_term": "cross", "rank_deficient": "coupled",
                  "corrupted_training": "coupled", "duplicate_identity": "coupled",
                  "missing_identity": "coupled", "cubic_out_of_family": "cubic"}[expected["condition"]]
        target = held.get("observed_target", [])
        base_by_id = {r[1]: r[2:4] for r in held.get("base", [])}
        min_x = min((xy[0] for xy in base_by_id.values()), default=0)
        min_y = min((xy[1] for xy in base_by_id.values()), default=0)
        if len(target) != 6 or any(
            r[1] not in base_by_id or r[2:4] != list(oracle(family, base_by_id[r[1]][0] - min_x, base_by_id[r[1]][1] - min_y))
            for r in target
        ):
            oracle_errors.append(wid)
        dim = normalize(held.get("dim_infer"))
        if not isinstance(dim, dict):
            semantic_errors.append({"worker_id": wid, "reason": "missing_dim_infer"})
            continue
        q_train = [g for g in row.get("training", {}).get("generator_payloads", []) if g.get("kind") == "quadratic2"]
        q_after = [g for g in held.get("generator_payloads", []) if g.get("kind") == "quadratic2"]
        positive_q = expected["feature"] == "on" and expected["condition"] in ("coupled_quadratic", "quadratic_cross_term")
        positive_linear = expected["condition"] == "linear_positive"
        if positive_q:
            expected_coeffs = ([1, 0, 0, 1, 0, 0, 1, 1, 0, 0]
                               if expected["condition"] == "coupled_quadratic"
                               else [1, 0, 0, 0, 0, 0, 1, 0, 1, 0])
            if len(q_train) != 1 or q_train[0].get("coefficients") != expected_coeffs:
                control_errors.append({"worker_id": wid, "reason": "quadratic_acquisition_or_coefficients"})
            if row.get("reload", {}).get("generator_payloads") != row.get("training", {}).get("generator_payloads"):
                control_errors.append({"worker_id": wid, "reason": "generator_payload_changed_on_reload"})
            if not row.get("reload", {}).get("agent_node_id_preserved"):
                control_errors.append({"worker_id": wid, "reason": "agent_id_not_preserved"})
            q_name = q_train[0].get("name") if q_train else None
            exact_reuse = (dim.get("explained") is True and dim.get("generator") == q_name
                and dim.get("generators", [None])[0] == q_name
                and not dim.get("transforms") and held.get("status") == "recognized_transformed")
            if not exact_reuse or q_after != q_train:
                control_errors.append({"worker_id": wid, "reason": "quadratic_diminfer_reuse_not_exact"})
        else:
            if q_train or q_after:
                false_mints.append(wid)
        if expected["feature"] == "off" and (q_train or q_after):
            false_mints.append(wid)
        if expected["condition"] == "linear_positive":
            linear_train = [g for g in row.get("training", {}).get("generator_payloads", []) if g.get("kind") == "linear"]
            if not linear_train or (expected["feature"] == "on" and q_train):
                control_errors.append({"worker_id": wid, "reason": "linear_positive_kind_or_mint"})
            if not (dim.get("explained") is True and not dim.get("transforms") and held.get("status") == "recognized_transformed"):
                control_errors.append({"worker_id": wid, "reason": "linear_heldout_not_exact"})
        if expected["condition"] in ("rank_deficient", "corrupted_training", "duplicate_identity", "missing_identity", "cubic_out_of_family"):
            if q_train != q_after:
                control_errors.append({"worker_id": wid, "reason": "negative_control_changed_quadratic_codebook"})
        if expected["audit"]:
            counters = row.get("training", {}).get("counters", {})
            if arm == "on":
                attempts = counters.get("gen_infer_quadratic_attempts", 0)
                rejected = counters.get("gen_infer_quadratic_validation_rejects", 0)
                survivors = counters.get("gen_infer_quadratic_survivors", 0)
                refusal = sum(v for k, v in counters.items() if k.startswith("gen_infer_quadratic_refusal:"))
                if attempts != rejected + survivors + refusal:
                    counter_errors.append({"worker_id": wid, "attempts": attempts,
                        "validation_rejects": rejected, "survivors": survivors, "refusals": refusal})
                if positive_q and (attempts <= 0 or survivors <= 0):
                    counter_errors.append({"worker_id": wid, "reason": "positive_quadratic_missing_solver_work"})
                refusal_reason = {
                    "rank_deficient": "rank_deficient",
                    "corrupted_training": "residual_mismatch",
                    "duplicate_identity": "identity_ambiguous",
                    "missing_identity": "identity_incomplete",
                    "cubic_out_of_family": "residual_mismatch",
                }.get(expected["condition"])
                if refusal_reason and counters.get(f"gen_infer_quadratic_refusal:{refusal_reason}", 0) <= 0:
                    counter_errors.append({"worker_id": wid, "reason": "expected_refusal_reason_missing",
                        "expected": refusal_reason, "observed": counters})

    checks["native_binary_assignment"] = not wrong_binary
    checks["heldout_oracle_rows"] = not oracle_errors
    checks["quadratic_false_mints"] = not false_mints
    checks["acquisition_reuse_and_refusal_controls"] = not control_errors
    checks["quadratic_counter_conservation"] = not counter_errors

    # Clean and audit-on runs are paired by condition/repeat/feature; compare
    # semantic fields while leaving timings and counter payloads out of parity.
    parity_errors = []
    for condition in (c["condition"] for c in lock["cells"]):
        for repeat in range(1, 11):
            for feature in ("off", "on"):
                clean = by_key.get((condition, repeat, feature, False))
                audited = by_key.get((condition, repeat, feature, True))
                if clean is None or audited is None:
                    parity_errors.append({"condition": condition, "repeat": repeat, "feature": feature, "reason": "missing_pair"})
                    continue
                for phase in ("training", "reload", "heldout"):
                    left = clean.get(phase, {})
                    right = audited.get(phase, {})
                    sem_keys = ("status", "residual", "generator_payloads", "dim_infer", "transform_receipts", "agent_node_id_preserved")
                    if normalize({k: left.get(k) for k in sem_keys}) != normalize({k: right.get(k) for k in sem_keys}):
                        parity_errors.append({"condition": condition, "repeat": repeat,
                            "feature": feature, "phase": phase, "reason": "semantic_difference"})
    checks["audit_semantic_parity"] = not parity_errors

    perf = {}
    for condition in (c["condition"] for c in lock["cells"]):
        for feature in ("off", "on"):
            selected = [row for (cond, _, feat, audit), row in by_key.items()
                        if cond == condition and feat == feature and audit is False]
            vals = sorted(row.get("training", {}).get("closure_ns", 0)
                          + row.get("heldout", {}).get("closure_ns", 0) for row in selected)
            rss = sorted(row.get("process_peak_rss_kib", 0) for row in selected)
            if selected:
                perf[f"{condition}:{feature}"] = {
                    "clean_worker_n": len(selected),
                    "closure_total_ns_median": vals[len(vals) // 2],
                    "worker_wall_ns_median": sorted(r.get("worker_wall_ns", 0) for r in selected)[len(selected) // 2],
                    "process_peak_rss_kib_median": rss[len(rss) // 2],
                    "process_peak_rss_kib_p95": rss[min(len(rss) - 1, int(0.95 * len(rss)))],
                }

    gates = {"worker_total", "worker_failures_empty", "capture_complete", "unique_workers", "schedule_exact",
             "source_stability", "source_hashes_unchanged", "native_binary_assignment",
             "heldout_oracle_rows", "quadratic_false_mints", "acquisition_reuse_and_refusal_controls",
             "quadratic_counter_conservation", "audit_semantic_parity"}
    result = {"schema": "NonlinearQuadraticGenInferV2_2Analysis", "lock_sha256": sha(LOCK),
        "raw_sha256": sha(RAW), "checks": checks, "passed": all(checks.get(k, False) for k in gates),
        "worker_count": len(workers), "worker_failures": raw.get("failures", []),
        "native_assignment_errors": wrong_binary, "oracle_errors": oracle_errors,
        "false_quadratic_mints": false_mints, "semantic_errors": control_errors,
        "counter_errors": counter_errors, "audit_parity_errors": parity_errors,
        "clean_performance_summary": perf,
        "performance_admissible": all(checks.get(k, False) for k in gates),
        "limits": "bounded integer 2-D quadratic family and registered fixtures only; no general nonlinear or natural-task tractability claim"}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "passed": result["passed"],
        "checks": checks, "worker_count": len(workers)}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
