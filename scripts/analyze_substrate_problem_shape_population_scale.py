#!/usr/bin/env python3
"""Independent checks and summaries for the ProblemShape population sweep."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def analyze(raw: dict) -> dict:
    workers = raw["records"]
    by_key = {(r["population_size"], r["task_mix"], r["codebook_mode"]): r for r in workers}
    checks: dict[str, bool] = {
        "all_worker_checks_pass": all(r["all_checks_pass"] for r in workers),
        "12_worker_matrix_complete": len(workers) == 12 and len(by_key) == 12,
        "12_distinct_process_ids": len({r["process_id"] for r in workers}) == 12,
        "aggregate_records_unique_processes": raw.get("unique_worker_processes") is True,
    }
    rows = []
    for n in (2, 4, 8):
        dyn = by_key[(n, "recognition", "dynamic")]
        frozen = by_key[(n, "recognition", "frozen")]
        ps_mint_candidates = sum(z["count"] for x in dyn["records"]
                                 for z in x["problem_shape_rule_scale_audit"]
                                 if z["rule_name"] == "ps_mint" and z["metric"] == "candidate_pairs")
        ps_mint_candidate_sequence = [sum(z["count"] for z in x["problem_shape_rule_scale_audit"]
                                          if z["rule_name"] == "ps_mint" and z["metric"] == "candidate_pairs")
                                      for x in dyn["records"]]
        ps_mint_terms = sum(z["count"] for x in dyn["records"]
                            for z in x["problem_shape_rule_scale_audit"]
                            if z["rule_name"] == "ps_mint" and z["metric"] == "term_evaluations")
        expected_triangular = n * (n + 1) // 2
        frozen_mint_candidates = sum(z["count"] for x in frozen["records"]
                                     for z in x["problem_shape_rule_scale_audit"]
                                     if z["rule_name"] == "ps_mint" and z["metric"] == "candidate_pairs")
        frozen_mint_terms = sum(z["count"] for x in frozen["records"]
                                for z in x["problem_shape_rule_scale_audit"]
                                if z["rule_name"] == "ps_mint" and z["metric"] == "term_evaluations")
        candidate_delta = dyn["problem_shape_candidate_pairs_total"] - frozen["problem_shape_candidate_pairs_total"]
        term_delta = dyn["problem_shape_term_evaluations_total"] - frozen["problem_shape_term_evaluations_total"]
        per_rule_totals = {}
        for rule_name in ("ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"):
            pairs = sum(z["count"] for x in dyn["records"] for z in x["problem_shape_rule_scale_audit"]
                        if z["rule_name"] == rule_name and z["metric"] == "candidate_pairs")
            terms = sum(z["count"] for x in dyn["records"] for z in x["problem_shape_rule_scale_audit"]
                        if z["rule_name"] == rule_name and z["metric"] == "term_evaluations")
            per_rule_totals[rule_name] = {"candidate_pairs": pairs, "term_evaluations": terms}
        row = {
            "N": n,
            "recognition_dynamic_total_candidate_pairs": dyn["problem_shape_candidate_pairs_total"],
            "recognition_frozen_total_candidate_pairs": frozen["problem_shape_candidate_pairs_total"],
            "recognition_dynamic_total_term_evaluations": dyn["problem_shape_term_evaluations_total"],
            "recognition_frozen_total_term_evaluations": frozen["problem_shape_term_evaluations_total"],
            "ps_mint_candidate_pairs_dynamic": ps_mint_candidates,
            "ps_mint_candidate_sequence_dynamic": ps_mint_candidate_sequence,
            "ps_mint_term_evaluations_dynamic": ps_mint_terms,
            "ps_mint_candidate_pairs_frozen": frozen_mint_candidates,
            "ps_mint_term_evaluations_frozen": frozen_mint_terms,
            "dynamic_minus_frozen_candidate_pairs": candidate_delta,
            "dynamic_minus_frozen_term_evaluations": term_delta,
            "recognition_dynamic_per_rule_totals": per_rule_totals,
            "ps_mint_candidate_pair_share": ps_mint_candidates / dyn["problem_shape_candidate_pairs_total"],
            "ps_mint_term_evaluation_share": ps_mint_terms / dyn["problem_shape_term_evaluations_total"],
            "expected_triangular_sum": expected_triangular,
            "expected_five_term_evaluations_per_pair": 5 * expected_triangular,
            "recurrent_dynamic_total_candidate_pairs": by_key[(n, "recurrent_residual", "dynamic")]["problem_shape_candidate_pairs_total"],
            "recurrent_frozen_total_candidate_pairs": by_key[(n, "recurrent_residual", "frozen")]["problem_shape_candidate_pairs_total"],
            "recurrent_dynamic_total_term_evaluations": by_key[(n, "recurrent_residual", "dynamic")]["problem_shape_term_evaluations_total"],
            "recurrent_frozen_total_term_evaluations": by_key[(n, "recurrent_residual", "frozen")]["problem_shape_term_evaluations_total"],
            "dynamic_mint_count": by_key[(n, "recurrent_residual", "dynamic")]["total_mints"],
            "frozen_mint_count": by_key[(n, "recurrent_residual", "frozen")]["total_mints"],
            "worker_observe_wall_ns": {
                f"{mix}_{mode}": [x["wall_time_ns"] for x in by_key[(n, mix, mode)]["records"]]
                for mix in ("recognition", "recurrent_residual") for mode in ("dynamic", "frozen")
            },
        }
        rows.append(row)
        checks[f"N{n}_recognition_ps_mint_triangular"] = ps_mint_candidates == expected_triangular
        checks[f"N{n}_recognition_ps_mint_per_observation_sequence"] = ps_mint_candidate_sequence == list(range(1, n + 1))
        checks[f"N{n}_recognition_ps_mint_five_term_evals"] = ps_mint_terms == 5 * expected_triangular
        checks[f"N{n}_frozen_ps_mint_counters_zero"] = frozen_mint_candidates == 0 and frozen_mint_terms == 0
        checks[f"N{n}_recognition_arm_state_and_work_delta"] = (
            dyn["total_mints"] == frozen["total_mints"] == 0
            and dyn["problem_shape_candidate_pairs_total"] - frozen["problem_shape_candidate_pairs_total"] == ps_mint_candidates
            and dyn["problem_shape_term_evaluations_total"] - frozen["problem_shape_term_evaluations_total"] == ps_mint_terms
        )
        checks[f"N{n}_recurrent_dynamic_vs_frozen"] = (
            by_key[(n, "recurrent_residual", "dynamic")]["total_mints"] == 1
            and by_key[(n, "recurrent_residual", "frozen")]["total_mints"] == 0
            and all(x["observation_status_final"] == "recognized"
                    for x in by_key[(n, "recurrent_residual", "dynamic")]["records"])
            and all(x["observation_status_final"] == "residual"
                    for x in by_key[(n, "recurrent_residual", "frozen")]["records"])
        )
    return {"schema_version": 1, "analysis_id": raw["run_id"] + "-analysis",
            "raw_report_path": "evaluation/reports/substrate_problem_shape_population_scale_20260925.json",
            "raw_report_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
            "checks": checks, "all_checks_pass": all(checks.values()), "by_size": rows,
            "interpretation": {
                "recognition_only": "The dynamic ps_mint rule examines a triangular number N(N+1)/2 of candidate pairs across N sequential observations. The frozen control removes exactly these candidate pairs and five term evaluations per pair in these cells; no mints occur in either arm.",
                "recurrent_residual": "Dynamic recurrence mints exactly once and re-decodes all same-shape residuals; the frozen codebook leaves them residual. Cost totals include the extra work of mint/redecode and subsequent recognition.",
                "scope": "Six population sizes per task mix across a small authored suite; this is mechanism-level evidence, not a natural-task frequency estimate or a general asymptotic theorem."
            }}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("raw", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = analyze(json.loads(args.raw.read_text()))
    result["raw_report_sha256"] = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "checks": result["checks"]}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
