#!/usr/bin/env python3
"""Independent analyzer for the CAN-to-deduction bridge oracle capture."""
import itertools, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evaluation/reports/can_deduction_bridge_oracle_v1_20260927.json"
TOPICS = ["trust_mayor", "claim_credible", "world_safe", "self_worth", "debtor_trustworthy"]

def expected_from_input(states, entity):
    # Separate, small truth-table implementation over the captured input vector.
    facts = set()
    for topic in TOPICS:
        value = states[topic]
        if value == 1: facts.add((entity, topic))
        elif value == -1: facts.add((entity, "not_" + topic))
        elif value != 0: raise ValueError("unexpected state value")
    return facts

def analyze(report):
    checks = {}
    all_rows = []
    run_sets = []
    for run in report.get("runs", []):
        rows = run.get("cases", [])
        checks[f"rep{run.get('replicate')}_243_rows"] = len(rows) == 243
        ids = [r.get("case_id") for r in rows]
        checks[f"rep{run.get('replicate')}_unique_complete_ids"] = sorted(ids) == list(range(243))
        mismatches = []
        null_fp = 0
        for row in rows:
            exp = expected_from_input(row["states"], row["entity"])
            obs = {tuple(x) for x in row.get("observed", [])}
            if obs != exp:
                mismatches.append({"case_id": row.get("case_id"), "expected": sorted(exp), "observed": sorted(obs)})
            if any(state == 0 and ((row["entity"], topic) in obs or
                                   (row["entity"], "not_" + topic) in obs)
                   for topic, state in row["states"].items()):
                null_fp += 1
            all_rows.append((row, exp, obs))
        checks[f"rep{run.get('replicate')}_exact_truth_table"] = not mismatches
        checks[f"rep{run.get('replicate')}_no_null_false_positive"] = null_fp == 0
        aggregate_expected = sorted(tuple(x) for x in run.get("aggregate_expected", []))
        aggregate_observed = sorted(tuple(x) for x in run.get("aggregate_observed", []))
        checks[f"rep{run.get('replicate')}_global_entity_attribution"] = aggregate_expected == aggregate_observed
        controls = run.get("controls", {})
        checks[f"rep{run.get('replicate')}_duplicate_semantics_stable"] = controls.get("duplicate_invocation", {}).get("semantic_delta_empty") is True
        checks[f"rep{run.get('replicate')}_unrelated_target_isolated"] = controls.get("unrelated_target", {}).get("no_cross_target_facts") is True
        checks[f"rep{run.get('replicate')}_missing_state_is_null"] = controls.get("missing_state", {}).get("no_fact_for_missing_state") is True
        amb = controls.get("ambiguous_tokens", {})
        checks[f"rep{run.get('replicate')}_ambiguity_does_not_mint_denotes"] = amb.get("expected_no_denotes") is True and not amb.get("ambiguous_denotes_edges")
        checks[f"rep{run.get('replicate')}_legacy_owner_fallback_recorded"] = amb.get("legacy_owner_fallback") is True
        run_sets.append({r["case_id"]: (r["expected"], r["observed"]) for r in rows})
    checks["replicates_agree"] = len(run_sets) == 2 and run_sets[0] == run_sets[1]
    tp = fp = fn = 0
    state_counts = {"positive": {"tp": 0, "fp": 0, "fn": 0}, "negative": {"tp": 0, "fp": 0, "fn": 0}}
    for row, exp, obs in all_rows:
        for expected_fact in exp:
            bucket = "negative" if expected_fact[1].startswith("not_") else "positive"
            if expected_fact in obs: state_counts[bucket]["tp"] += 1
            else: state_counts[bucket]["fn"] += 1
        for observed_fact in obs - exp:
            bucket = "negative" if observed_fact[1].startswith("not_") else "positive"
            state_counts[bucket]["fp"] += 1
    for b in state_counts.values(): tp += b["tp"]; fp += b["fp"]; fn += b["fn"]
    return {"checks": checks, "pass": all(checks.values()),
            "metrics": {"cases_across_workers": len(all_rows), "exact_case_accuracy": (sum(r[1] == r[2] for r in all_rows) / len(all_rows) if all_rows else None),
                        "fact_precision": (tp / (tp + fp) if tp + fp else 1.0),
                        "fact_recall": (tp / (tp + fn) if tp + fn else 1.0),
                        "positive": state_counts["positive"], "negative": state_counts["negative"],
                        "all_ambivalent_case_count": sum(1 for row, exp, obs in all_rows if not exp),
                        "null_topic_decisions": sum(1 for row, exp, obs in all_rows
                                                     for state in row["states"].values() if state == 0),
                        "null_false_positive_count": sum(1 for row, exp, obs in all_rows
                                                         for topic, state in row["states"].items()
                                                         if state == 0 and ((row["entity"], topic) in obs or
                                                                            (row["entity"], "not_" + topic) in obs)),
                        "native_audit_counters_by_replicate": [run.get("native_audit_counters", {}) for run in report.get("runs", [])],
                        "mismatch_count": sum(r[1] != r[2] for r in all_rows)}}

if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORT
    result = analyze(json.loads(path.read_text()))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]: raise SystemExit(1)
