#!/usr/bin/env python3
"""Independent audit of native per-rule episodic query attribution."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_episodic_query_attribution_20260925.json"
LOCK = ROOT / "evaluation/substrate_capability/episodic_query_attribution_lock_20260925.json"
PAIR_RULE = "episodic_mark_overlapping_cues_for_conservative_completion"


def main():
    raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
    hashes = {key: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == lock["sha256"][key]
              for key, path in lock["paths"].items()}
    runs = raw["runs"]
    expected_pairs = {(n, rep) for n in lock["sizes"] for rep in range(lock["replicates_per_size"])}
    actual_pairs = {(r["n"], r["replicate"]) for r in runs}
    by_size = {}
    per_run_pair_counts = []
    for n in lock["sizes"]:
        group = [r for r in runs if r["n"] == n]
        controls = [r["readers"]["control"] for r in group]
        audits = [r["readers"]["audit"] for r in group]
        counters_by_reader = []
        for r in audits:
            counts = {}
            for row in r["per_rule_counters"]:
                key = (row["rule_name"], row["metric"])
                counts[key] = counts.get(key, 0) + row["count"]
            pair = counts.get((PAIR_RULE, "candidate_tests"), 0)
            per_run_pair_counts.append({"n": n, "replicate": r["pid"], "candidate_tests": pair})
            counters_by_reader.append(counts)
        mean_counters = {}
        for counters in counters_by_reader:
            for key, count in counters.items():
                mean_counters[key] = mean_counters.get(key, 0) + count / len(group)
        global_mean = {key: statistics.mean(r["global_counters"].get(key, 0) for r in audits)
                       for key in audits[0]["global_counters"]}
        control_median = statistics.median(r["tick_ns"] / 1e6 for r in controls)
        audit_median = statistics.median(r["tick_ns"] / 1e6 for r in audits)
        by_size[str(n)] = {
            "replicates": len(group), "control_tick_ms_median": control_median,
            "audit_tick_ms_median": audit_median,
            "audit_wall_overhead_ratio": audit_median / control_median if control_median else None,
            "pair_rule_candidate_tests_per_query": mean_counters.get((PAIR_RULE, "candidate_tests"), 0),
            "pair_rule_where_evaluations_per_query": mean_counters.get((PAIR_RULE, "where_evaluations"), 0),
            "pair_rule_term_evaluations_per_query": mean_counters.get((PAIR_RULE, "term_evaluations"), 0),
            "all_rules_candidate_tests_per_query": global_mean.get("cand_tested", 0),
            "all_rules_where_evaluations_per_query": global_mean.get("where_evals", 0),
            "all_rules_term_evaluations_per_query": global_mean.get("term_evals_total", 0),
            "all_rules_rule_enumerations_per_query": global_mean.get("rule_enumerations", 0),
            "all_rules_effect_nodes_per_query": global_mean.get("rule_effect_node_inserts", 0),
            "all_rules_effect_attr_sets_per_query": global_mean.get("rule_effect_attr_set_attempts", 0),
            "candidate_tests_by_rule_per_query": [
                {"rule_name": rule, "candidate_tests": count}
                for (rule, metric), count in sorted(mean_counters.items()) if metric == "candidate_tests" and count],
        }
    checks = {
        "all_locked_hashes_match": all(hashes.values()),
        "complete_size_replicate_grid": actual_pairs == expected_pairs,
        "paired_answers_and_provenance_match": all(
            r["readers"]["control"]["state_summary"] == r["readers"]["audit"]["state_summary"] == r["readers"]["control"]["expected_summary"] and
            r["readers"]["control"]["candidate_count"] == r["readers"]["audit"]["candidate_count"] == 1 and
            r["readers"]["control"]["provenance_kind"] == r["readers"]["audit"]["provenance_kind"] == "recalled"
            for r in runs),
        "per_rule_overlap_counter_matches_exact_pair_envelope": all(
            x["candidate_tests"] == 2 * x["n"] * (x["n"] + 1) for x in per_run_pair_counts),
        "overlap_rule_is_dominant_candidate_test_source": all(
            by_size[str(n)]["pair_rule_candidate_tests_per_query"] >
            .9 * by_size[str(n)]["all_rules_candidate_tests_per_query"] for n in lock["sizes"] if n >= 78),
    }
    n_lo, n_hi = lock["sizes"][0], lock["sizes"][-1]
    pair_lo = by_size[str(n_lo)]["pair_rule_candidate_tests_per_query"]
    pair_hi = by_size[str(n_hi)]["pair_rule_candidate_tests_per_query"]
    out = {"run_id": raw["run_id"], "lock_run_id": lock["run_id"], "input_hash_match": hashes,
           "checks": checks, "summary": by_size,
           "candidate_test_endpoint_exponent": math.log(pair_hi / pair_lo) / math.log(n_hi / n_lo),
           "candidate_test_exact_identity": "2*N*(N+1) per exact retrieval tick for episodic_mark_overlapping_cues_for_conservative_completion on this all-unique-cue workload",
           "interpretation": "The current seed spends a quadratic number of candidate tests in an all-pairs overlapping-cue rule on this measured workload; this is an exact operation-count result for these graph sizes and source, not a general runtime complexity theorem.",
           "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    dest = ROOT / "evaluation/reports/substrate_episodic_query_attribution_analysis_20260925.json"
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": by_size,
                      "candidate_test_endpoint_exponent": out["candidate_test_endpoint_exponent"],
                      "output": str(dest)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("episodic query attribution audit failed")


if __name__ == "__main__":
    main()
