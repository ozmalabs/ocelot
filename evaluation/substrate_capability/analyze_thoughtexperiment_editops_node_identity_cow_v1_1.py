#!/usr/bin/env python3
"""Independent integrity analysis for node-identity CoW integration."""
from __future__ import annotations
import hashlib, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_editops_node_identity_cow_v1_1_lock_20261003.json"
ORDERS = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_orders_20261003.json"
SCORES = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_scores_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_editops_node_identity_cow_v1_1_analysis_20261003.json"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    lock, orders, scores = (json.loads(p.read_text()) for p in (LOCK, ORDERS, SCORES))
    os, ss = orders["workers"], scores["workers"]
    score_by_worker = {x["worker"]: x for x in ss}
    checks = {
        "capture_lock_binding": orders["lock_sha256"] == sha(LOCK) and scores["lock_sha256"] == sha(LOCK)
            and scores["orders_sha256"] == sha(ORDERS),
        "four_unique_workers_each_stage": len(os) == len(ss) == 4
            and {x["worker"] for x in os} == {0,1,2,3}
            and {x["worker"] for x in ss} == {0,1,2,3},
        "source_hashes_stable": all(x["source_stable"] and x["source_before"] == x["source_after"] == lock["sources"] for x in os + ss),
        "eight_candidates_and_frozen_order": all(len(x["descriptors"]) == 8 and len(x["candidate_rules"]) == 8
            and len(x["candidate_order"]) == 8 and set(x["candidate_order"]) == set(range(8)) for x in os),
        "paired_backend_semantic_parity": all(
            [r["candidate_id"] for r in x["training"]["full_copy"]] == [r["candidate_id"] for r in x["training"]["shared_graph_pages"]]
            and all(a["branch_result"]["correct"] == b["branch_result"]["correct"]
                and a["branch_result"]["counts"] == b["branch_result"]["counts"]
                and a["branch_result"]["work_steps"] == b["branch_result"]["work_steps"]
                and a["primary_unchanged_before_return"] and b["primary_unchanged_before_return"]
                for a,b in zip(x["training"]["full_copy"],x["training"]["shared_graph_pages"])) for x in os),
        "unique_training_winner_selected": all(
            sum(r["branch_result"]["correct"] for r in x["training"]["shared_graph_pages"]) == 1
            and x["selected_label"] == "node_attrs:out:agent:has_actor_goal:actor+verb"
            and x["decision"].get("proposal_id") == next(d["proposal_id"] for d in x["descriptors"] if d["label"] == x["selected_label"])
            for x in os),
        "abstention_controls": all(not x["controls"][c].get("ok") for x in os for c in ("all_wrong","tie")),
        "source_controls_pass": all(all(row["branch_result"]["correct"] and row["primary_unchanged_before_return"]
            for row in x["source_controls"].values()) for x in os),
        "heldout_all_candidates_scored_and_isolated": all(all(len(x["heldout"][b]) == 8
            and all(r["primary_unchanged_before_return"] for r in x["heldout"][b]) for b in ("full_copy","shared_graph_pages")) for x in ss),
        "selected_repair_passes_both_heldouts": all(all(next(r for r in x["heldout"][b] if r["candidate_id"] == x["selected_id"])["branch_result"]["correct"]
            for b in ("full_copy","shared_graph_pages")) for x in ss),
        "selected_residual_receipt_returned_safely": all(
            x["adoption_branch"]["primary_unchanged_before_return"]
            and x["adoption_branch"]["receipt_return"]["receipt_parity"]
            and x["adoption_branch"]["receipt_return"]["stale_retry_rejected"]
            and x["adoption_branch"]["receipt_return"]["stale_retry_unchanged"]
            and x["adoption_branch"]["receipt_return"]["primary_rules_preserved"]
            and len(x["adoption_branch"]["receipt_return"]["delta"].get("nodes_changed",[])) == 1
            and not any(x["adoption_branch"]["receipt_return"]["delta"].get(k,[]) for k in ("nodes_added","edges_added","edges_changed","nodes_removed","edges_removed"))
            for x in ss),
    }
    summary = {"backend_training_lifecycle_median_ms": {}, "backend_heldout_lifecycle_median_ms": {},
               "backend_candidate_snapshot_median_ms": {}, "receipt_adoption_median_ms": 0.0}
    for backend in ("full_copy","shared_graph_pages"):
        summary["backend_training_lifecycle_median_ms"][backend] = statistics.median(
            sum(x["snapshot_ns"] + x["rule_patch_ns"] + x["branch_result"]["input_and_closure_ns"] for x in w["training"][backend]) / 1e6 for w in os)
        summary["backend_heldout_lifecycle_median_ms"][backend] = statistics.median(
            sum(x["snapshot_ns"] + x["rule_patch_ns"] + x["branch_result"]["input_and_closure_ns"] for x in w["heldout"][backend]) / 1e6 for w in ss)
        summary["backend_candidate_snapshot_median_ms"][backend] = statistics.median(
            statistics.median(x["snapshot_ns"] for x in w["training"][backend]) / 1e6 for w in os)
    summary["receipt_adoption_median_ms"] = statistics.median(x["adoption_branch"]["receipt_return"]["timing_ns"]["adopt"] / 1e6 for x in ss)
    result = {"schema":"ThoughtexperimentEditOpsNodeIdentityCowV1_1Analysis", "checks":checks,
        "summary":summary, "interpretation_boundary":"One authored actor/verb family; branches return selected proposal evidence, not an active production rule. Task, fault, examples, and oracle remain harness supplied."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if all(checks.values()) else 1

if __name__ == "__main__": raise SystemExit(main())
