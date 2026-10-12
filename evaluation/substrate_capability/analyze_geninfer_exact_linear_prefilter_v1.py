#!/usr/bin/env python3
"""Independent adjudicator for the source-locked three-arm GenInfer panel."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/geninfer_exact_linear_prefilter_v1_lock_20261006.json"
RAW = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_v1_raw_20261006.json"
OUT = ROOT / "evaluation/reports/geninfer_exact_linear_prefilter_v1_analysis_20261006.json"
ARMS = ("off", "quadratic", "prefilter")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value):
    if isinstance(value, (tuple, list)):
        return [normalize(x) for x in value]
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    return value


def oracle(family: str, x: int, y: int) -> tuple[int, int]:
    if family == "linear": return x + y, 2 * y
    if family == "coupled": return x + x * y, y + x * x
    if family == "cross": return x, y + x * y
    if family == "centered_cubic": return x, y + (x - 2) ** 3
    raise ValueError(family)


def semantic_projection(row: dict) -> dict:
    return {phase: {k: row.get(phase, {}).get(k) for k in (
        "status", "residual", "generator_payloads", "dim_infer", "transform_receipts",
        "agent_node_id_preserved")} for phase in ("training", "reload", "heldout")}


def main() -> int:
    lock, raw = json.loads(LOCK.read_text()), json.loads(RAW.read_text())
    schedule = {r["worker_id"]: r for r in lock["schedule"]}
    workers = {r.get("worker_id"): r for r in raw.get("workers", [])}
    checks: dict[str, bool] = {
        "raw_schema": raw.get("schema") == "GenInferExactLinearPrefilterV1Raw",
        "lock_hash": raw.get("lock_sha256") == sha(LOCK),
        "source_stability": raw.get("source_and_binaries_stable") is True,
        "source_hashes_unchanged": raw.get("locked_sources_sha256") == raw.get("post_run_sources_sha256") == lock.get("sources_sha256"),
        "worker_total": len(workers) == lock.get("worker_count") == 480,
        "worker_failures_empty": raw.get("failures") == [],
        "capture_complete": raw.get("capture_complete") is True and raw.get("completed_count") == lock.get("worker_count"),
        "unique_workers": len(workers) == len(raw.get("workers", [])),
        "schedule_exact": set(workers) == set(schedule),
    }
    binary_errors, oracle_errors, semantic_errors, counter_errors, false_mints = [], [], [], [], []
    by_key: dict[tuple, dict] = {}
    for wid, row in workers.items():
        exp = schedule.get(wid)
        if exp is None: continue
        arm = exp["feature"]
        by_key[(exp["condition"], exp["repeat"], arm, exp["audit"])] = row
        if row.get("feature") != arm or row.get("audit") != exp["audit"] or row.get("native_sha256") != lock["native_binaries"][arm]["sha256"]:
            binary_errors.append(wid)
        family = next(c["family"] for c in lock["cells"] if c["condition"] == exp["condition"])
        held = row.get("heldout", {})
        targets, base = held.get("observed_target", []), held.get("base", [])
        base_by_id = {r[1]: r[2:4] for r in base}
        min_x = min((v[0] for v in base_by_id.values()), default=0)
        min_y = min((v[1] for v in base_by_id.values()), default=0)
        if len(targets) != 6 or any(r[1] not in base_by_id or r[2:4] != list(oracle(family, base_by_id[r[1]][0]-min_x, base_by_id[r[1]][1]-min_y)) for r in targets):
            oracle_errors.append(wid)

        q_train = [g for g in row.get("training", {}).get("generator_payloads", []) if g.get("kind") == "quadratic2"]
        q_after = [g for g in held.get("generator_payloads", []) if g.get("kind") == "quadratic2"]
        q_capable = arm in ("quadratic", "prefilter")
        positive_q = q_capable and exp["condition"] in ("coupled_quadratic", "quadratic_cross_term")
        if positive_q:
            expected_coeffs = ([1,0,0,1,0,0,1,1,0,0] if exp["condition"] == "coupled_quadratic"
                               else [1,0,0,0,0,0,1,0,1,0])
            if len(q_train) != 1 or q_train[0].get("coefficients") != expected_coeffs:
                semantic_errors.append({"worker_id": wid, "reason": "quadratic_acquisition_or_coefficients"})
            if row.get("reload", {}).get("generator_payloads") != row.get("training", {}).get("generator_payloads") or not row.get("reload", {}).get("agent_node_id_preserved"):
                semantic_errors.append({"worker_id": wid, "reason": "reload_changed_codebook_or_agent"})
            q_name = q_train[0].get("name") if q_train else None
            dim = held.get("dim_infer", {})
            if not (dim.get("explained") is True and dim.get("generator") == q_name and dim.get("generators", [None])[0] == q_name and not dim.get("transforms") and held.get("status") == "recognized_transformed" and q_after == q_train):
                semantic_errors.append({"worker_id": wid, "reason": "quadratic_transfer_not_reused"})
        elif q_train or q_after:
            false_mints.append(wid)

        if exp["condition"] == "linear_positive":
            linear = [g for g in row.get("training", {}).get("generator_payloads", []) if g.get("kind") == "linear"]
            dim = held.get("dim_infer", {})
            if not linear or q_train or not (dim.get("explained") is True and not dim.get("transforms") and held.get("status") == "recognized_transformed"):
                semantic_errors.append({"worker_id": wid, "reason": "linear_positive_not_acquired_and_transferred"})
        if exp["condition"] in ("rank_deficient", "corrupted_training", "duplicate_identity", "missing_identity", "cubic_out_of_family") and q_train != q_after:
            semantic_errors.append({"worker_id": wid, "reason": "negative_control_quadratic_codebook_changed"})

        counters = row.get("training", {}).get("counters", {})
        if exp["audit"]:
            if q_capable:
                attempts = counters.get("gen_infer_quadratic_attempts", 0)
                rejected = counters.get("gen_infer_quadratic_validation_rejects", 0)
                survivors = counters.get("gen_infer_quadratic_survivors", 0)
                refusals = sum(v for k,v in counters.items() if k.startswith("gen_infer_quadratic_refusal:"))
                if attempts != rejected + survivors + refusals:
                    counter_errors.append({"worker_id":wid,"reason":"quadratic_counter_conservation"})
                if positive_q and survivors <= 0:
                    counter_errors.append({"worker_id":wid,"reason":"positive_quadratic_solver_not_admitted"})
            if arm == "prefilter":
                attempts = counters.get("gen_infer_prefilter_attempts", 0)
                outcomes = sum(counters.get(k,0) for k in ("gen_infer_prefilter_solved","gen_infer_prefilter_proven_no_fit","gen_infer_prefilter_fallback"))
                if attempts != outcomes:
                    counter_errors.append({"worker_id":wid,"reason":"prefilter_outcome_conservation","attempts":attempts,"outcomes":outcomes})
                no_fit = counters.get("gen_infer_prefilter_proven_no_fit", 0)
                fallback = counters.get("gen_infer_prefilter_fallback", 0)
                no_fit_reasons = sum(v for k,v in counters.items() if k.startswith("gen_infer_prefilter_proven_no_fit_reason:"))
                fallback_reasons = sum(v for k,v in counters.items() if k.startswith("gen_infer_prefilter_fallback_reason:"))
                if no_fit != no_fit_reasons or fallback != fallback_reasons:
                    counter_errors.append({"worker_id":wid,"reason":"prefilter_reason_conservation","no_fit":no_fit,"no_fit_reasons":no_fit_reasons,"fallback":fallback,"fallback_reasons":fallback_reasons})
                if counters.get("gen_infer_prefilter_solved", 0) and (counters.get("gen_infer_prefilter_identity_value_comparisons", 0) <= 0 or counters.get("gen_infer_prefilter_exact_arithmetic_checks", 0) <= 0):
                    counter_errors.append({"worker_id":wid,"reason":"prefilter_work_counters_missing_on_solve"})
            elif counters.get("gen_infer_prefilter_attempts", 0):
                counter_errors.append({"worker_id":wid,"reason":"prefilter_ran_in_control_arm"})
        elif arm == "prefilter" and any(counters.get(k,0) for k in (
            "gen_infer_prefilter_attempts", "gen_infer_prefilter_identity_value_comparisons",
            "gen_infer_prefilter_exact_arithmetic_checks")):
            counter_errors.append({"worker_id":wid,"reason":"prefilter_counters_nonzero_with_audit_off"})

    checks["native_binary_assignment"] = not binary_errors
    checks["heldout_oracle_rows"] = not oracle_errors
    checks["no_quadratic_false_mints"] = not false_mints
    checks["acquisition_transfer_and_refusal_controls"] = not semantic_errors
    checks["counter_conservation"] = not counter_errors

    parity_errors=[]
    for cond in (c["condition"] for c in lock["cells"]):
        for repeat in range(1,11):
            for arm in ARMS:
                a=by_key.get((cond,repeat,arm,False)); b=by_key.get((cond,repeat,arm,True))
                if a is None or b is None or normalize(semantic_projection(a)) != normalize(semantic_projection(b)):
                    parity_errors.append({"condition":cond,"repeat":repeat,"arm":arm,"reason":"audit_semantic_parity"})
            q=by_key.get((cond,repeat,"quadratic",False)); p=by_key.get((cond,repeat,"prefilter",False))
            if q is None or p is None or normalize(semantic_projection(q)) != normalize(semantic_projection(p)):
                parity_errors.append({"condition":cond,"repeat":repeat,"arms":["quadratic","prefilter"],"reason":"prefilter_semantic_parity"})
            if cond not in ("coupled_quadratic","quadratic_cross_term"):
                off=by_key.get((cond,repeat,"off",False))
                if off is None or q is None or normalize(semantic_projection(off)) != normalize(semantic_projection(q)):
                    parity_errors.append({"condition":cond,"repeat":repeat,"arms":["off","quadratic"],"reason":"control_arm_semantic_parity"})
    checks["audit_and_build_semantic_parity"] = not parity_errors

    perf={}
    for cond in (c["condition"] for c in lock["cells"]):
        for arm in ARMS:
            selected=[r for (c,_,a,audit),r in by_key.items() if c==cond and a==arm and not audit]
            if selected:
                closure=sorted(r["training"]["closure_ns"]+r["heldout"]["closure_ns"] for r in selected)
                perf[f"{cond}:{arm}"]={"n":len(selected),"closure_total_ns_median":closure[len(closure)//2],
                    "worker_wall_ns_median":sorted(r["worker_wall_ns"] for r in selected)[len(selected)//2],
                    "peak_rss_kib_median":sorted(r["process_peak_rss_kib"] for r in selected)[len(selected)//2]}
    gates=list(checks)
    result={"schema":"GenInferExactLinearPrefilterV1Analysis","lock_sha256":sha(LOCK),"raw_sha256":sha(RAW),
        "checks":checks,"passed":all(checks.values()),"worker_count":len(workers),"worker_failures":raw.get("failures",[]),
        "native_binary_errors":binary_errors,"heldout_oracle_errors":oracle_errors,"false_quadratic_mints":false_mints,
        "semantic_errors":semantic_errors,"counter_errors":counter_errors,"parity_errors":parity_errors,
        "clean_performance_summary":perf,"performance_admissible":all(checks.values()),
        "limits":"Finite registered 2-D integer-map and bounded quadratic fixtures only; no natural-task prevalence or general learning tractability claim."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"passed":result["passed"],"checks":checks,"worker_count":len(workers)},sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
