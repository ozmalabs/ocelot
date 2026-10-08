#!/usr/bin/env python3
"""Analyze repeated-predicate GenInfer robustness without assuming null outcomes."""
from __future__ import annotations
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_analysis_20260926.json"
M=[1,1,0,2];LAYOUTS={"original":[(0,0),(1,0),(2,0),(0,2)],"orthogonal_pairs":[(0,0),(0,1),(1,0),(1,1)],"paired_square":[(0,0),(1,0),(0,1),(1,1)]};PREDS=["p0","p0","p1","p1"];CONDS=["positive","corrupt_p0_r_1","corrupt_p0_r_2","corrupt_p0_r_3"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs(layout,condition):
 pts=LAYOUTS[layout];base=[[p,r,q,"red"] for p,(r,q) in zip(PREDS,pts)];a,b,c,d=M;goal=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,pts)]
 if condition!="positive":goal[0][1]+=int(condition.rsplit("_",1)[1])
 return base,goal
def bound_from_count(count):
 for b in range(1,1000):
  if (2*b+1)**4-1==count:return b
 return None
def main():
 raw=json.loads(SRC.read_text());ss=raw["samples"];lookup={(s["layout"],s["condition"],s["repetition"]):s for s in ss};expected={(l,c,r) for l in LAYOUTS for c in CONDS for r in range(1,6)}
 checks={"complete_60_cell_repeats":len(ss)==60 and set(lookup)==expected,
  "locked_design_current":raw["protocol"]["matrix"]==M and raw["protocol"]["predicates"]==PREDS and raw["protocol"]["corruption_magnitudes"]==[1,2,3] and raw["protocol"]["repetitions"]==5,
  "generated_signatures_match_protocol":all((s["base"],s["goal"])==inputs(l,c) and s["base_relation_count"]==4 and s["goal_relation_count"]==4 for (l,c,r),s in lookup.items()),
  "positive_cases_recover_generator":all((o:=lookup[l,"positive",r]["observation"])["explained"] and o["matrix"]==M and o["residual_dims"]==0 and o["transforms"]==[] for l in LAYOUTS for r in range(1,6)),
  "within_cell_outputs_deterministic":all(all(lookup[l,c,r]["observation"]==lookup[l,c,1]["observation"] for r in range(2,6)) for l in LAYOUTS for c in CONDS),
  "candidate_counts_stable_within_cells":all(len({lookup[l,c,r]["observation"]["checked"] for r in range(1,6)})==1 for l in LAYOUTS for c in CONDS),
  "generating_matrix_inside_every_enumerated_bound":all((b:=bound_from_count(lookup[l,c,r]["observation"]["checked"])) is not None and max(abs(x) for x in M)<=b for l in LAYOUTS for c in CONDS for r in range(1,6)),
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in raw["provenance"]["source_sha256"].items())}
 summaries={}
 for l in LAYOUTS:
  summaries[l]={}
  for c in CONDS:
   obs=[lookup[l,c,r]["observation"] for r in range(1,6)];accepted=sum(bool(o["explained"]) for o in obs);exact=sum(o["matrix"]==M for o in obs if o["explained"]);alt=sum(bool(o["explained"]) and o["matrix"]!=M for o in obs);refused=len(obs)-accepted
   transforms=Counter(json.dumps(o["transforms"],sort_keys=True) for o in obs)
   summaries[l][c]={"n":len(obs),"accepted":accepted,"acceptance_rate":accepted/len(obs),"exact_generating_matrix":exact,"exact_recovery_rate_all_cases":exact/len(obs),"alternative_matrix":alt,"refused":refused,"candidate_count":obs[0]["checked"],"derived_matrix_entry_bound":bound_from_count(obs[0]["checked"]),"residual_forms":dict(transforms),"example_matrix":obs[0]["matrix"]}
 corrupted=[x for l in LAYOUTS for c in CONDS[1:] for x in [summaries[l][c]]]
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"by_layout_and_condition":summaries,"corrupted_case_totals":{"n":sum(x["n"] for x in corrupted),"accepted":sum(x["accepted"] for x in corrupted),"exact_generating_matrix":sum(x["exact_generating_matrix"] for x in corrupted),"alternative_matrix":sum(x["alternative_matrix"] for x in corrupted),"refused":sum(x["refused"] for x in corrupted)},"interpretation":"The generating matrix's coefficients are within every enumerated bound; failures and alternatives arise within the searched coefficient domain. Source inspection implicates canonical sorted positional alignment and residual/Occam ranking, not a bound that excluded the generating map. This is a descriptive synthetic surface, not a natural-noise error-rate claim."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"corrupted_case_totals":result["corrupted_case_totals"],"by_layout_and_condition":summaries},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
