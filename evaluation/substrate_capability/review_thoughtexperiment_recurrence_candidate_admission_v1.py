#!/usr/bin/env python3
"""Independent review of recurrence candidate-admission outcomes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json"
d=json.loads(RAW.read_text()); ws=d["workers"]
descriptors=[w["candidate_descriptors"] for w in ws]
all_outcomes=[w["candidate_outcomes"] for w in ws]
expected={x["digest"] for x in descriptors[0]}
checks={
 "three_fresh_workers":len(ws)==3 and len({w["worker"] for w in ws})==3,
 "locked_source_parity":d["source_before"]==d["source_after"]==d["lock"]["sources"],
 "worker_source_stability":all(w["source_before"]==w["source_after"] for w in ws),
 "eight_generated_candidates":len(descriptors[0])==8,
 "unique_candidate_descriptors":len(expected)==len(descriptors[0]),
 "same_descriptor_set_each_worker":all({x["digest"] for x in row}==expected for row in descriptors),
 "all_candidates_scored_both_splits":all(len(rows)==8 and all("training" in x and "heldout" in x for x in rows) for rows in all_outcomes),
 "training_and_heldout_keys_disjoint":all(set(x["training"]["recurrence_keys"]).isdisjoint(x["heldout"]["recurrence_keys"]) for rows in all_outcomes for x in rows),
 "independent_pass_failure_present":all(any(x["heldout"]["pass"] for x in rows) and any(not x["heldout"]["pass"] for x in rows) for rows in all_outcomes),
 "only_repair_passes_heldout":all([x["label"] for x in rows if x["heldout"]["pass"]]==["dedup_identity_fix"] for rows in all_outcomes),
 "heldout_oracle_matches_counts":all(x["heldout"]["pass"]==(x["heldout"]["offer_counts"]==[1,1] and x["heldout"]["fixedpoint_progress"]==0) for rows in all_outcomes for x in rows),
 "repeatable_outcome_matrix":all([(x["digest"],x["training"]["pass"],x["heldout"]["pass"]) for x in rows]==[(x["digest"],x["training"]["pass"],x["heldout"]["pass"]) for x in all_outcomes[0]] for rows in all_outcomes[1:]),
}
out={"schema":"RecurrenceCandidateAdmissionV1Review","passed":sum(checks.values()),"total":len(checks),"checks":checks}
path=ROOT/"evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_analysis_review_20261002.json"
path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
