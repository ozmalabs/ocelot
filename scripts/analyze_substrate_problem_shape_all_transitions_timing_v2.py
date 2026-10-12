#!/usr/bin/env python3
"""Independent V2 timing/counter readback; baseline ps_mint comes from locked audit rows."""
from __future__ import annotations

import hashlib
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_20260925.json"
BASELINE = ROOT / "evaluation/reports/substrate_problem_shape_population_scale_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/problem_shape_all_transitions_timing_v2_lock_20260925.json"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_2_AMENDMENT_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_analysis_20260925.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(xs, p):
    vals = sorted(xs)
    return vals[min(len(vals) - 1, int(p * len(vals)))]


def main():
    raw = json.loads(RAW.read_text())
    baseline = json.loads(BASELINE.read_text())
    cells = [r for r in baseline["records"] if r.get("population_size") == 8
             and r.get("task_mix") == "recurrent_residual"
             and r.get("codebook_mode") == "dynamic"]
    if len(cells) != 1:
        raise SystemExit(f"expected one locked N=8 recurrent dynamic baseline cell, got {len(cells)}")
    baseline_cell = cells[0]

    base_ps_mint = {"candidate_pairs": 0, "term_evaluations": 0}
    for record in baseline_cell["records"]:
        for item in record["problem_shape_rule_scale_audit"]:
            if item["rule_name"] == "ps_mint" and item["metric"] in base_ps_mint:
                base_ps_mint[item["metric"]] += int(item["count"])

    pairs = raw["pairs"]
    expected_order_counts = {"baseline_first": 6, "candidate_first": 6}
    order_counts = {
        "baseline_first": sum(p["execution_order"][0] == "baseline" for p in pairs),
        "candidate_first": sum(p["execution_order"][0] == "candidate" for p in pairs),
    }
    pids = [p["arms"][arm]["process_id"] for p in pairs for arm in ("baseline", "candidate")]
    ratios = [float(p["wall_ratio_candidate_over_baseline"]) for p in pairs]
    deltas = [int(p["wall_delta_ns_candidate_minus_baseline"]) for p in pairs]
    cpu_ratios = [float(p["cpu_ratio_candidate_over_baseline"]) for p in pairs]
    candidate_counts = {p["arms"]["candidate"]["problem_shape_candidate_pairs_total"] for p in pairs}
    candidate_terms = {p["arms"]["candidate"]["problem_shape_term_evaluations_total"] for p in pairs}
    candidate_mint_pairs = {p["arms"]["candidate"]["ps_mint_candidate_pairs_total"] for p in pairs}
    candidate_mint_terms = {p["arms"]["candidate"]["ps_mint_term_evaluations_total"] for p in pairs}
    baseline_counts = {p["arms"]["baseline"]["problem_shape_candidate_pairs_total"] for p in pairs}
    baseline_terms = {p["arms"]["baseline"]["problem_shape_term_evaluations_total"] for p in pairs}
    semantic = len(pairs) == 12 and all(p["semantic_parity"]
        and p["arms"]["baseline"]["all_checks_pass"]
        and p["arms"]["candidate"]["all_checks_pass"] for p in pairs)
    unique = len(pids) == len(set(pids)) == 24
    balanced = order_counts == expected_order_counts
    stable_counts = all(len(x) == 1 for x in (candidate_counts, candidate_terms,
        candidate_mint_pairs, candidate_mint_terms, baseline_counts, baseline_terms))

    # Paired bootstrap of the median wall ratio; resample complete process pairs.
    rng = random.Random(20260925)
    boot = []
    for _ in range(20000):
        boot.append(statistics.median(rng.choice(ratios) for _ in ratios))
    boot.sort()
    base_candidate_pairs = next(iter(baseline_counts))
    cand_candidate_pairs = next(iter(candidate_counts))
    base_term_evals = next(iter(baseline_terms))
    cand_term_evals = next(iter(candidate_terms))
    cand_mint_pair_count = next(iter(candidate_mint_pairs))
    cand_mint_term_count = next(iter(candidate_mint_terms))
    result = {
        "schema_version": 1,
        "analysis": "problem-shape-all-transitions-timing-v2-independent-readback",
        "raw_sha256": sha(RAW), "baseline_raw_sha256": sha(BASELINE),
        "lock_sha256": sha(LOCK), "amendment_sha256": sha(AMENDMENT),
        "pair_count": len(pairs), "process_count": len(pids),
        "semantic_gates_pass": semantic, "unique_process_ids": unique,
        "order_counts": order_counts, "order_balance_pass": balanced,
        "pair_counter_values_stable": stable_counts,
        "timing": {
            "candidate_faster_pairs": sum(x < 1.0 for x in ratios),
            "wall_ratio_median": statistics.median(ratios),
            "wall_ratio_mean": statistics.mean(ratios),
            "wall_ratio_range": [min(ratios), max(ratios)],
            "paired_median_ratio_bootstrap_95": [percentile(boot, .025), percentile(boot, .975)],
            "median_wall_delta_ns": statistics.median(deltas),
            "cpu_ratio_median": statistics.median(cpu_ratios),
        },
        "work_counters": {
            "problem_shape_candidate_pairs": {"baseline": base_candidate_pairs, "candidate": cand_candidate_pairs,
                                              "relative_reduction": 1 - cand_candidate_pairs / base_candidate_pairs},
            "problem_shape_term_evaluations": {"baseline": base_term_evals, "candidate": cand_term_evals,
                                               "relative_reduction": 1 - cand_term_evals / base_term_evals},
            "ps_mint_candidate_pairs": {"baseline": base_ps_mint["candidate_pairs"],
                                         "candidate": cand_mint_pair_count,
                                         "baseline_source": "hash-locked population-scale baseline worker per-rule audit rows; same N=8 recurrent-residual dynamic cell"},
            "ps_mint_term_evaluations": {"baseline": base_ps_mint["term_evaluations"],
                                          "candidate": cand_mint_term_count,
                                          "baseline_source": "hash-locked population-scale baseline worker per-rule audit rows; same N=8 recurrent-residual dynamic cell"},
            "candidate_host_index_maintenance_ns_median": statistics.median(
                p["arms"]["candidate"]["host_index_maintenance_ns_total"] for p in pairs),
        },
        "raw_field_correction": {
            "baseline_ps_mint_summary_fields_in_raw": "zero values are missing-field defaults, not measurements",
            "correction": "Use source-linked per-rule audit rows in the locked baseline raw artifact; preserve V2 raw unchanged.",
        },
        "all_gates_pass": semantic and unique and balanced and stable_counts,
        "interpretation_limit": "Repeated timing and work counts for one authored N=8 recurrent-residual ProblemShape sequence; not a natural-task or substrate-wide result.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_gates_pass": result["all_gates_pass"],
                      "timing": result["timing"], "work_counters": result["work_counters"]}, sort_keys=True))
    return 0 if result["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
