#!/usr/bin/env python3
"""Independent semantic and provenance gates for the residual envelope."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_geninfer_residual_envelope_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_residual_envelope_v1_analysis_20260926.json"
MAPS={"asymmetric_scale_shear":[1,1,0,2],"anisotropic_scale":[2,0,0,1],"swap_scale":[0,2,1,0],"coupled_shear":[2,0,1,1]}
PTS=[(0,0),(1,0),(2,0),(0,2)];PREDS=["p0","p1","p2","p3"]
UC=["positive","global_shift_r","two_slot_shifts_max2","two_slot_shifts_max1","global_substitution"]
RC=["repeated_predicate_nonuniform_numeric","repeated_predicate_symbolic_conflict"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def generated(m,cond):
 a,b,c,d=m;base=[[p,r,q,"red"] for p,(r,q) in zip(PREDS,PTS)];goal=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(PREDS,PTS)]
 if cond in ("global_shift_r","two_slot_shifts_max2","two_slot_shifts_max1"):goal=[[p,r+1,q+(2 if cond.startswith("two_slot") else 0),v] for p,r,q,v in goal]
 if cond=="global_substitution":goal=[[p,r,q,"blue"] for p,r,q,v in goal]
 return base,goal
def repeated(cond):
 a,b,c,d=MAPS["asymmetric_scale_shear"];preds=["p0","p0","p1","p1"]
 base=[[p,r,q,"red"] for p,(r,q) in zip(preds,PTS)];goal=[[p,a*r+b*q,c*r+d*q,"red"] for p,(r,q) in zip(preds,PTS)]
 if cond=="repeated_predicate_nonuniform_numeric":goal[0][1]+=1;goal[1][1]+=2
 else:goal[0][3]="blue";goal[1][3]="green"
 return base,goal
def main():
 raw=json.loads(SRC.read_text());samples=raw["samples"];lookup={(s["family"],s["condition"],s["repetition"]):s for s in samples}
 expected_keys={(fam,c,r) for fam in MAPS for c in UC for r in range(1,6)}|{("asymmetric_scale_shear",c,r) for c in RC for r in range(1,6)}
 keys=set(lookup)
 checks={"complete_110_observations":len(samples)==110 and keys==expected_keys,
  "locked_protocol_current":raw["protocol"]["maps"]==MAPS and raw["protocol"]["unique_conditions"]==UC and raw["protocol"]["repeated_conditions"]==RC and raw["protocol"]["repetitions"]==5,
  "generated_inputs_match_lock":all((s["base"],s["goal"])==(repeated(c) if c in RC else generated(MAPS[f],c)) for (f,c,r),s in lookup.items()),
  "candidate_search_count_fixed":all(s["observation"]["checked"]==6560 for s in samples),
  "positive_exact_fit":all((o:=lookup[f,"positive",r]["observation"])["explained"] and o["matrix"]==m and o["residual_dims"]==0 and o["transforms"]==[] and o["dims"]==[] for f,m in MAPS.items() for r in range(1,6)),
  "global_numeric_residuals":all((o:=lookup[f,"global_shift_r",r]["observation"])["explained"] and o["matrix"]==m and o["transforms"]==[{"dim":1,"kind":"shift","delta":1}] for f,m in MAPS.items() for r in range(1,6)),
  "two_residual_dimensions_respect_budget":all((o:=lookup[f,"two_slot_shifts_max2",r]["observation"])["explained"] and o["matrix"]==m and o["residual_dims"]==2 and o["transforms"]==[{"dim":1,"kind":"shift","delta":1},{"dim":2,"kind":"shift","delta":2}] for f,m in MAPS.items() for r in range(1,6)) and all(not lookup[f,"two_slot_shifts_max1",r]["observation"]["explained"] and lookup[f,"two_slot_shifts_max1",r]["observation"]["matrix"]==[] for f in MAPS for r in range(1,6)),
  "global_symbolic_substitution":all((o:=lookup[f,"global_substitution",r]["observation"])["explained"] and o["matrix"]==m and o["transforms"]==[{"dim":3,"kind":"subst","delta":[["red","blue"]]}] for f,m in MAPS.items() for r in range(1,6)),
  "repeated_predicate_numeric_decomposition_stable":all((o:=lookup["asymmetric_scale_shear","repeated_predicate_nonuniform_numeric",r]["observation"])["explained"] and o["matrix"]==[-2,-2,0,2] and o["transforms"]==[{"dim":1,"kind":"shift","delta":3,"pred":"p0"},{"dim":1,"kind":"shift","delta":6,"pred":"p1"}] for r in range(1,6)),
  "cross_predicate_symbolic_conflict_refused":all(not (o:=lookup["asymmetric_scale_shear","repeated_predicate_symbolic_conflict",r]["observation"])["explained"] and o["matrix"]==[] and o["transforms"]==[] for r in range(1,6)),
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in raw["provenance"]["source_sha256"].items())}
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"observations":len(samples),"interpretation":"The evaluator accepts bounded numeric and symbolic residual decomposition, enforces the tested transform-entry budget, and refuses this conflicting symbolic mapping. Repeated-predicate numeric data can select a materially different matrix with predicate-local residuals, indicating decomposition non-identifiability in this fixture."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"interpretation":result["interpretation"]},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
