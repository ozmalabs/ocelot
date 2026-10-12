#!/usr/bin/env python3
"""Independent review joins frozen candidate orders to separate utility evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
d=json.loads((ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_raw_20261002.json").read_text())
task=json.loads((ROOT/"evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_raw_20261002.json").read_text())
rec=json.loads((ROOT/"evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json").read_text())
ws=d["workers"];tws=task["workers"];rws=rec["workers"]
utility=[];defaults=[]
for i,w in enumerate(ws):
 score={x["digest"]:all(y["pass"] for y in x["heldout"]) for x in tws[i]["candidate_outcomes"]}
 digest_by_label={x["label"]:x["digest"] for x in w["descriptors"]}
 utility.append({"cold_first":float(score[digest_by_label[w["cold_order"][0]]]),
                 "experience_first":float(score[digest_by_label[w["experience_order"][0]]])})
 defaults.append(float(all(x["pass"] for x in tws[i]["candidate_outcomes"][0]["heldout"])))
checks={
 "three_fresh_workers":len(ws)==3 and len({w["worker"] for w in ws})==3,
 "lock_source_parity":d["source_before"]==d["source_after"]==d["lock"]["sources"],
 "worker_source_stability":all(w["source_before"]==w["source_after"] for w in ws),
 "graph_rank_program_composed":all(w["composer"]["grounded"] and w["composer"]["served_by"]=="graph" and w["composer"]["programs"] for w in ws),
 "same_six_control_descriptors":all([(x["label"],x["digest"]) for x in w["descriptors"]]==[(x["label"],x["digest"]) for x in tws[i]["candidate_descriptors"]] for i,w in enumerate(ws)),
 "complete_recurrence_training_records":all(len(w["prior_records"])==8 and all(x["target_rule"]=="mrl_offer_due_once" for x in w["prior_records"]) for w in ws),
 "records_have_no_control_target_or_class":all(all(x["target_rule"]!="classify_kind_family" and not x["outcome_class"] for x in w["prior_records"]) for w in ws),
 "zero_cross_family_prior_counts":all(all(t["prior_successes"]==0.0 and t["prior_failures"]==0.0 for t in w["experience_traces"].values()) for w in ws),
 "experience_matches_cold_order":all(w["cold_order"]==w["experience_order"] for w in ws),
 "cold_and_experience_first_candidates_fail":all(x["cold_first"]==0.0 and x["experience_first"]==0.0 for x in utility),
 "default_first_candidate_passes":all(defaults),
 "rank_timings_recorded":all(w["timing_ns"]["cold_rank"]>0 and w["timing_ns"]["experience_rank"]>0 for w in ws),
 "orders_precede_heldout_scores":all("heldout_scores" not in w for w in ws),
 "recurrence_training_capture_locked":rec["source_before"]==rec["source_after"]==rec["lock"]["sources"],
}
review={"schema":"CrossFamilyRankerNullTransferV1Review","passed":sum(checks.values()),"total":len(checks),
 "checks":checks,"joined_utility":utility,"default_first_candidate_utility":defaults}
path=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_analysis_review_20261002.json"
path.write_text(json.dumps(review,indent=2,sort_keys=True)+"\n")
print(json.dumps(review,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
