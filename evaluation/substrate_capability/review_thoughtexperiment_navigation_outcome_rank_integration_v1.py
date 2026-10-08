#!/usr/bin/env python3
"""Independent structural review of the navigation rank-integration capture."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_raw_20261002.json"
data = json.loads(RAW.read_text())
workers = data["workers"]
checks = {
    "three_fresh_workers": len(workers) == 3 and len({w["worker"] for w in workers}) == 3,
    "source_lock_parity": data["source_before"] == data["source_after"] == data["lock"]["sources"],
    "three_policy_arms": all(set(w["arms"]) == {"default_order", "cold_graph_rank", "experience_graph_rank"} for w in workers),
    "graph_rank_composed": all(bool(w["rank_program_names"]) for w in workers),
    "train_holdout_disjoint": all(set(w["train_case_ids"]).isdisjoint(w["heldout_case_ids"]) for w in workers),
    "at_least_three_candidates": all(len(w["default_order"]) >= 3 for w in workers),
    "all_candidates_scored": all(len(w["training_scores"]) == len(w["default_order"]) == len(w["heldout_scores_all_candidates"]) for w in workers),
    "cold_rank_has_first_candidate_error": all(w["arms"]["cold_graph_rank"]["first_candidate_utility"] == 0.0 for w in workers),
    "experience_and_default_first_candidate_pass": all(w["arms"][a]["first_candidate_utility"] == 1.0 for w in workers for a in ("default_order", "experience_graph_rank")),
    "experience_reduces_trials_vs_cold": all(len(w["arms"]["experience_graph_rank"]["attempts_until_success"]) < len(w["arms"]["cold_graph_rank"]["attempts_until_success"]) for w in workers),
    "no_experience_gain_vs_default": all(w["arms"]["experience_graph_rank"]["attempts_until_success"] == w["arms"]["default_order"]["attempts_until_success"] for w in workers),
    "candidate_specific_training_counts": all(
        w["rank_traces"]["flip_comparison"]["prior_successes"] == 1.0
        and w["rank_traces"]["flip_comparison"]["prior_failures"] == 0.0
        and all(trace["prior_successes"] == 0.0 and trace["prior_failures"] == 1.0
                for label, trace in w["rank_traces"].items() if label != "flip_comparison")
        for w in workers),
    "all_arms_succeed": all(w["arms"][a]["success"] for w in workers for a in w["arms"]),
}
out = {"schema":"NavigationOutcomeRankIntegrationV1Review","passed":sum(checks.values()),"total":len(checks),"checks":checks}
out["protocol_deviations"] = ["per-policy ordering latency required by preregistration is absent; see capture amendment"]
path = ROOT / "evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_analysis_review_20261002.json"
path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
if not all(checks.values()): raise SystemExit(1)
