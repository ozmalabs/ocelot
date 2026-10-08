#!/usr/bin/env python3
"""Independent review of the control-kind candidate-admission capture."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
d=json.loads((ROOT/"evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_raw_20261002.json").read_text())
ws=d["workers"]
descs=[w["candidate_descriptors"] for w in ws]
outs=[w["candidate_outcomes"] for w in ws]
checks={
 "three_fresh_workers":len(ws)==3 and len({w["worker"] for w in ws})==3,
 "source_lock_parity":d["source_before"]==d["source_after"]==d["lock"]["sources"],
 "stable_worker_source":all(w["source_before"]==w["source_after"] for w in ws),
 "six_applicable_candidates":all(len(x)==6 for x in descs),
 "six_unique_descriptors":all(len({c["digest"] for c in x})==6 for x in descs),
 "same_descriptors_across_workers":all({c["digest"] for c in x}=={c["digest"] for c in descs[0]} for x in descs),
 "all_candidates_scored_on_both_splits":all(len(x)==6 and all(len(c["training"])==2 and len(c["heldout"])==2 for c in x) for x in outs),
 "source_rule_passes_all_cases":all(all(x["pass"] for x in w["controls"]["source"]) for w in ws),
 "fault_fails_all_cases":all(not any(x["pass"] for x in w["controls"]["fault"]) for w in ws),
 "training_heldout_names_disjoint":all({x["name"] for x in w["candidate_outcomes"][0]["training"]}.isdisjoint({x["name"] for x in w["candidate_outcomes"][0]["heldout"]}) for w in ws),
 "one_heldout_repair":all([c["label"] for c in w["candidate_outcomes"] if all(x["pass"] for x in c["heldout"]) ]==["flip_comparison"] for w in ws),
 "at_least_one_heldout_failure":all(any(not all(x["pass"] for x in c["heldout"]) for c in w["candidate_outcomes"]) for w in ws),
 "stable_outcome_matrix":all([(c["digest"],[x["actual"] for x in c["training"]],[x["actual"] for x in c["heldout"]]) for c in row]==[(c["digest"],[x["actual"] for x in c["training"]],[x["actual"] for x in c["heldout"]]) for c in outs[0]] for row in outs[1:]),
 "all_labels_reconcile_to_expected":all(x["pass"]==(x["actual"]==x["expected"] and x["family_set"]==1.0) for w in ws for c in w["candidate_outcomes"] for split in ("training","heldout") for x in c[split]),
}
review={"schema":"ControlKindClassificationRepairV1Review","passed":sum(checks.values()),"total":len(checks),"checks":checks}
path=ROOT/"evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_analysis_review_20261002.json"
path.write_text(json.dumps(review,indent=2,sort_keys=True)+"\n")
print(json.dumps(review,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
