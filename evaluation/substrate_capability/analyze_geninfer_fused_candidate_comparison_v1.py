#!/usr/bin/env python3
"""Independent semantic/work gate and audit-off timing analysis."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/geninfer_fused_candidate_comparison_v1_20261006.json"
OUT = ROOT / "evaluation/reports/geninfer_fused_candidate_comparison_v1_analysis_20261006.json"
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_geninfer_fused_candidate_comparison_v1.py"
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FUSED_CANDIDATE_COMPARISON_V1_PREREG_20261006.md"
FULLSEED = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"
BASE_PROFILE = ROOT / "evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py"
NONLINEAR = ROOT / "scripts/substrate_nonlinear_dimension_induction_v1_5.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic_phase(row, phase):
    fields = ("status", "covered_by", "residual", "transform_receipts", "closure_work")
    return {field: row.get("phases", {}).get(phase, {}).get(field) for field in fields}


def source_key(row):
    return row["task"]["id"], row["audit_enabled"]


def main():
    data = json.loads(CAPTURE.read_text())
    rows = data.get("workers", [])
    errors = []
    file_hashes = {"runner_sha256": RUNNER, "analyzer_sha256": ANALYZER,
                   "protocol_sha256": PROTOCOL, "fullseed_runner_sha256": FULLSEED,
                   "base_profile_sha256": BASE_PROFILE, "nonlinear_runner_sha256": NONLINEAR}
    for key, path in file_hashes.items():
        if data.get(key) != sha(path):
            errors.append(f"{key} mismatch")
    tasks = data.get("case_spec", [])
    expected_count = len(tasks) * 4
    if len(rows) != expected_count or data.get("worker_count") != expected_count:
        errors.append(f"expected {expected_count} workers from task × variant × audit design")
    if not data.get("source_stable"):
        errors.append("capture reports worker source drift")
    if len({row.get("pid") for row in rows}) != len(rows):
        errors.append("worker processes are not unique")

    indexed = {(row["task"]["id"], row["audit_enabled"], row["variant"]): row for row in rows}
    if len(indexed) != len(rows):
        errors.append("duplicate task/audit/variant workers")
    binary_hashes = {variant: {row["native_sha256"] for row in rows if row["variant"] == variant}
                     for variant in ("baseline", "fused")}
    if any(len(hashes) != 1 for hashes in binary_hashes.values()) or binary_hashes["baseline"] == binary_hashes["fused"]:
        errors.append("engine hashes are inconsistent within or across variants")

    timing_by_cell = defaultdict(lambda: {"baseline": defaultdict(list), "fused": defaultdict(list)})
    term_by_cell = defaultdict(lambda: {"baseline": [], "fused": []})
    search_fields = ("gen_infer_requests", "gen_infer_cache_hits", "gen_infer_kernel_calls",
                     "gen_infer_eligible_bases", "gen_infer_matrix_attempts", "gen_infer_apply_rejects",
                     "gen_infer_candidate_rejects", "gen_infer_residual_rejects", "gen_infer_candidate_survivors")
    for task in tasks:
        ident = task["id"]
        for audit in (False, True):
            pair = {variant: indexed.get((ident, audit, variant)) for variant in ("baseline", "fused")}
            if any(row is None for row in pair.values()):
                errors.append(f"{ident}/audit={audit}: missing paired variant")
                continue
            baseline, fused = pair["baseline"], pair["fused"]
            for row in pair.values():
                if not row.get("source_stable") or row["source_before"] != row["source_after"]:
                    errors.append(f"{ident}/{row['variant']}: source drift")
                if row["native_sha256"] != next(iter(binary_hashes[row["variant"]])):
                    errors.append(f"{ident}/{row['variant']}: binary hash mismatch")
            if baseline["source_before"]["source_sha256"] != fused["source_before"]["source_sha256"]:
                errors.append(f"{ident}/audit={audit}: source hashes differ across variants")
            if baseline["semantic"] != fused["semantic"]:
                errors.append(f"{ident}/audit={audit}: semantic result mismatch")

            phases = ("train", "heldout", "corrupted_heldout") if task["kind"] == "positive" else ("train", "transfer")
            for phase in phases:
                if semantic_phase(baseline, phase) != semantic_phase(fused, phase):
                    errors.append(f"{ident}/audit={audit}/{phase}: semantic phase mismatch")
                for row in pair.values():
                    out = row["phases"].get(phase, {})
                    if not isinstance(out.get("closure_wall_ns"), int) or out["closure_wall_ns"] <= 0:
                        errors.append(f"{ident}/{row['variant']}/{phase}: invalid timing")
                    if audit:
                        counters = out.get("gen_infer_counters", {})
                        if any(field not in counters for field in search_fields):
                            errors.append(f"{ident}/{row['variant']}/{phase}: missing GenInfer counters")
                        bound_counts = {int(k.split(":", 1)[1]): int(v) for k, v in counters.items()
                                        if k.startswith("gen_infer_bases_by_bound:")}
                        expected_attempts = sum(((2*b+1)**4-1)*count for b, count in bound_counts.items())
                        outcome_sum = sum(counters.get(k, 0) for k in (
                            "gen_infer_apply_rejects", "gen_infer_candidate_rejects",
                            "gen_infer_residual_rejects", "gen_infer_candidate_survivors"))
                        if counters.get("gen_infer_eligible_bases") != sum(bound_counts.values()):
                            errors.append(f"{ident}/{row['variant']}/{phase}: eligible-base reconciliation failed")
                        if counters.get("gen_infer_matrix_attempts") != expected_attempts or expected_attempts != outcome_sum:
                            errors.append(f"{ident}/{row['variant']}/{phase}: candidate-work reconciliation failed")
                if audit:
                    ca = baseline["phases"][phase]["gen_infer_counters"]
                    cb = fused["phases"][phase]["gen_infer_counters"]
                    if any(ca.get(field) != cb.get(field) for field in search_fields):
                        errors.append(f"{ident}/{phase}: GenInfer search accounting changed")
                else:
                    key = ident
                    timing_by_cell[key]["baseline"][phase].append(baseline["phases"][phase])
                    timing_by_cell[key]["fused"][phase].append(fused["phases"][phase])
            if audit:
                for phase in phases:
                    a = baseline["phases"][phase].get("term_audit_counters", {})
                    b = fused["phases"][phase].get("term_audit_counters", {})
                    term_by_cell[(ident, phase)]["baseline"].append(a.get("term_unit:GenInfer", 0))
                    term_by_cell[(ident, phase)]["fused"].append(b.get("term_unit:GenInfer", 0))

            if task["kind"] == "positive":
                for row in pair.values():
                    if not row["semantic"].get("target_acquired_during_training"):
                        errors.append(f"{ident}/{row['variant']}: positive training failed")
                    if not row["semantic"].get("heldout_exact_match") or row["semantic"].get("corrupted_heldout_exact_match"):
                        errors.append(f"{ident}/{row['variant']}: fullseed exact/corrupt oracle failed")
            elif task["case"]["family"] == "linear":
                if baseline["semantic"].get("training_expected_matrix") != [1, 1, 0, 2]:
                    errors.append(f"{ident}: linear fixture positive control changed")
            else:
                if task["case"].get("any_exact_linear_fit"):
                    errors.append(f"{ident}: nonlinear fixture unexpectedly has exact linear fit")

    timing_summary = {}
    for task in tasks:
        if task["kind"] != "positive":
            continue
        ident = task["id"]
        timing_summary[ident] = {}
        for phase in ("train", "heldout", "corrupted_heldout"):
            baseline = timing_by_cell[ident]["baseline"][phase]
            fused = timing_by_cell[ident]["fused"][phase]
            if baseline and fused:
                timing_summary[ident][phase] = {
                    "baseline_median_ms": statistics.median(r["closure_wall_ns"] for r in baseline)/1e6,
                    "fused_median_ms": statistics.median(r["closure_wall_ns"] for r in fused)/1e6,
                    "fused_over_baseline": statistics.median(r["closure_wall_ns"] for r in fused)/statistics.median(r["closure_wall_ns"] for r in baseline),
                    "baseline_median_cpu_ms": statistics.median(r["closure_cpu_ns"] for r in baseline)/1e6,
                    "fused_median_cpu_ms": statistics.median(r["closure_cpu_ns"] for r in fused)/1e6,
                    "baseline_median_hwm_delta_kib": statistics.median(r.get("hwm_delta_kib", 0) for r in baseline),
                    "fused_median_hwm_delta_kib": statistics.median(r.get("hwm_delta_kib", 0) for r in fused),
                }

    term_summary = {}
    for (ident, phase), variants in term_by_cell.items():
        if variants["baseline"]:
            term_summary[f"{ident}/{phase}"] = {
                "baseline_median_GenInfer_units": statistics.median(variants["baseline"]),
                "fused_median_GenInfer_units": statistics.median(variants["fused"]),
            }

    report = {"schema": "GenInferFusedCandidateComparisonV1Analysis",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gates_pass": not errors, "errors": errors, "capture_sha256": sha(CAPTURE),
        "timing_summary_audit_off": timing_summary, "term_work_summary_audit_on": term_summary,
        "interpretation_limit": "Exact behavioral parity on the registered families is a bounded gate. Audit-off timings on one host do not establish production speedup or natural-task prevalence."}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "gates_pass": report["gates_pass"],
                      "errors": errors, "timing_summary_audit_off": timing_summary,
                      "term_work_summary_audit_on": term_summary}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
