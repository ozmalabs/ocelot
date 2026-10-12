#!/usr/bin/env python3
"""Independent review of the two-stage null-transfer capture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
orders_path=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_orders_20261002.json"
scores_path=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_scores_20261002.json"
o=json.loads(orders_path.read_text());s=json.loads(scores_path.read_text());ws=o["workers"];ss=s["workers"]
score_maps=[{x["label"]:x for x in w["scores"]} for w in ss]
checks={
 "three_fresh_rank_workers":len(ws)==3 and len({x["worker"] for x in ws})==3,
 "three_fresh_scoring_workers":len(ss)==3 and len({x["worker"] for x in ss})==3,
 "order_source_lock_parity":o["source_before"]==o["source_after"]==o["lock"]["sources"],
 "score_source_lock_parity":s["source_before"]==s["source_after"]==o["lock"]["sources"],
 "order_stability":all(w["source_before"]==w["source_after"] for w in ws),
 "score_stability":all(w["source_before"]==w["source_after"] for w in ss),
 "production_rank_program_composed":all(w["composer"]["grounded"] and w["composer"]["served_by"]=="graph" and w["composer"]["programs"] for w in ws),
 "six_unique_candidates_per_worker":all(len(w["descriptors"])==6 and len({x["digest"] for x in w["descriptors"]})==6 for w in ws),
 "stable_candidate_descriptors_across_rank_workers":all([x["digest"] for x in w["descriptors"]]==[x["digest"] for x in ws[0]["descriptors"]] for w in ws),
 "all_candidate_bundles_scored":all(set(score_maps[i])=={c["label"] for c in w["candidates"]} for i,(w,_) in enumerate(zip(ws,ss))),
 "complete_recurrence_training_records":all(len(w["prior_records"])==8 and all(x["target_rule"]=="mrl_offer_due_once" for x in w["prior_records"]) for w in ws),
 "zero_cross_family_ranker_counts":all(all(t["prior_successes"]==0.0 and t["prior_failures"]==0.0 for t in w["experience_traces"].values()) for w in ws),
 "experience_order_equals_cold":all(w["cold_order"]==w["experience_order"] for w in ws),
 "default_order_first_candidate_passes":all(w["default_order"][0]=="flip_comparison" and score_maps[i][w["default_order"][0]]["utility"]==1.0 for i,w in enumerate(ws)),
 "order_stage_contains_no_heldout_outcomes":all("scores" not in w and "heldout" not in w for w in ws),
 "scores_follow_exact_order_artifact":s["orders_sha256"]==hashlib.sha256(orders_path.read_bytes()).hexdigest(),
 "cold_and_experience_first_candidate_fail":all(score_maps[i][w["cold_order"][0]]["utility"]==0.0 and score_maps[i][w["experience_order"][0]]["utility"]==0.0 for i,w in enumerate(ws)),
 "only_flip_passes_heldout":all([x["label"] for x in row.values() if x["utility"]==1.0]==["flip_comparison"] for row in score_maps),
 "heldout_score_matrix_repeats":all([(x["label"],x["utility"],[y["actual"] for y in x["outcomes"]]) for x in row["scores"]]==[(x["label"],x["utility"],[y["actual"] for y in x["outcomes"]]) for x in ss[0]["scores"]] for row in ss),
 "rank_timings_recorded":all(w["timing_ns"]["cold_rank"]>0 and w["timing_ns"]["experience_rank"]>0 for w in ws),
}
review={"schema":"CrossFamilyRankerNullTransferV1_2Review","passed":sum(checks.values()),"total":len(checks),"checks":checks,
 "per_worker":{"first_candidate_utility":[{"cold":score_maps[i][w["cold_order"][0]]["utility"],"experience":score_maps[i][w["experience_order"][0]]["utility"]} for i,w in enumerate(ws)],
  "rank_time_ns":[w["timing_ns"] for w in ws]}}
out=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_2_analysis_review_20261002.json"
out.write_text(json.dumps(review,indent=2,sort_keys=True)+"\n")
print(json.dumps(review,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
