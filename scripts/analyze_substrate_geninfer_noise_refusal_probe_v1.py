#!/usr/bin/env python3
"""Independent integrity, semantic, and timing analysis for noise refusal."""
from __future__ import annotations
import hashlib,json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_geninfer_noise_refusal_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_noise_refusal_v1_analysis_20260926.json"
MAPS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],"swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}
POINTS=[(0,0),(1,0),(2,0),(0,2)];PREDS=["p0","p1","p2","p3"]
CONDS=["positive","origin_corrupt","predicate_corrupt","missing_origin","extra_origin"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected(fam,cond):
 a,b,c,d=MAPS[fam]; rows=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,POINTS)]
 if cond=="origin_corrupt":rows[0][1]=1
 if cond=="predicate_corrupt":rows[3][0]="corrupt_p3"
 if cond=="missing_origin":rows=rows[1:]
 if cond=="extra_origin":rows=rows+[["extra",0,0,"red"]]
 return rows
def main():
 raw=json.loads(SRC.read_text());samples=raw["samples"];lookup={(s["transform_family"],s["condition"],s["repetition"]):s for s in samples}
 combos=[(f,c) for f in MAPS for c in CONDS];rng=random.Random(20260926);sched={};
 for rep in range(1,6):
  order=combos.copy();rng.shuffle(order);sched[str(rep)]=[[f,c] for f,c in order]
 checks={
  "complete_factorial_five_repeats":len(samples)==100 and len(lookup)==100 and all((f,c,r) in lookup for f,c in combos for r in range(1,6)),
  "locked_protocol_current":raw["protocol"]["transforms"]==MAPS and raw["protocol"]["points"]==[list(x) for x in POINTS] and raw["protocol"]["predicates"]==PREDS and raw["protocol"]["conditions"]==CONDS,
  "generated_signatures_match_locked_conditions":all(s["goal_relation_count"]==len(expected(f,c)) and s["base_relation_count"]==4 for (f,c,r),s in lookup.items()),
  "fixed_bound_candidate_count":raw["protocol"]["bound"]==4 and raw["protocol"]["candidate_count_per_call"]==6560 and all(s["checked"]==6560 for s in samples),
  "positive_cases_recover_exact_matrix":all(lookup[f,"positive",r]["explained"] and lookup[f,"positive",r]["matrix"]==m for f,m in MAPS.items() for r in range(1,6)),
  "all_null_cases_refused":all(not lookup[f,c,r]["explained"] and lookup[f,c,r]["matrix"]==[] for f in MAPS for c in CONDS[1:] for r in range(1,6)),
  "finite_positive_timing":all(math.isfinite(float(s["elapsed_seconds"])) and s["elapsed_seconds"]>0 for s in samples),
  "balanced_deterministic_schedule":raw["protocol"]["schedule_by_repetition"]==sched,
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in raw["provenance"]["source_sha256"].items()),
 }
 by_condition={}
 for cond in CONDS:
  vals=[s["elapsed_seconds"] for s in samples if s["condition"]==cond]
  by_condition[cond]={"n":len(vals),"median_seconds":statistics.median(vals),"min_seconds":min(vals),"max_seconds":max(vals)}
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"by_condition":by_condition,"refusal_rates":{c:sum(not s["explained"] for s in samples if s["condition"]==c)/20 for c in CONDS},"interpretation":"Selected null refusal and positive recovery across four small 2-D transform families; not a calibrated false-positive or natural-noise estimate."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"by_condition":by_condition},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
