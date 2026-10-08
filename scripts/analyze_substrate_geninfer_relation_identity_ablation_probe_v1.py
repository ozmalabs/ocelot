#!/usr/bin/env python3
"""Independent paired-reference and semantic analysis of the identity ablation."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_20260926.json"
REFERENCE=ROOT/"evaluation/reports/substrate_geninfer_repeat_predicate_robustness_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_analysis_20260926.json"
M=[1,1,0,2];LAYOUTS={"original":[(0,0),(1,0),(2,0),(0,2)],"orthogonal_pairs":[(0,0),(0,1),(1,0),(1,1)],"paired_square":[(0,0),(1,0),(0,1),(1,1)]};PREDS=["p0","p0","p1","p1"];CONDS=["positive","corrupt_p0_r_1","corrupt_p0_r_2","corrupt_p0_r_3"];MODES=["no_identity","stable_identity"]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def input_for(layout,mode,cond):
 a,b,c,d=M;base=[];goal=[]
 for i,(pred,(r,q)) in enumerate(zip(PREDS,LAYOUTS[layout])):
  ident=[] if mode=="no_identity" else [f"rel{i}"];base.append([pred,*ident,r,q,"red"])
  x,y=a*r+b*q,c*r+d*q
  if i==0 and cond!="positive":x+=int(cond.rsplit("_",1)[1])
  goal.append([pred,*ident,x,y,"red"])
 return base,goal,( ["pred","coord:r","coord:c","val"] if mode=="no_identity" else ["pred","id","coord:r","coord:c","val"] )
def main():
 raw=json.loads(SRC.read_text());ref=json.loads(REFERENCE.read_text());ss=raw["samples"];lookup={(s["layout"],s["mode"],s["condition"],s["repetition"]):s for s in ss}
 keys={(l,m,c,r) for l in LAYOUTS for m in MODES for c in CONDS for r in range(1,6)}
 paired=True
 for l in LAYOUTS:
  for c in CONDS:
   for r in range(1,6):
    old=next(x for x in ref["samples"] if x["layout"]==l and x["condition"]==c and x["repetition"]==r)
    new=lookup[l,"no_identity",c,r]
    if old["observation"]!=new["observation"]:paired=False
 checks={"complete_120_paired_observations":len(ss)==120 and set(lookup)==keys,
  "locked_protocol":raw["protocol"]["matrix"]==M and raw["protocol"]["layouts"]=={k:[list(p) for p in v] for k,v in LAYOUTS.items()} and raw["protocol"]["conditions"]==CONDS,
  "generated_signatures_and_identity_fields_match":all((s["base"],s["goal"],s["dim_types"])==input_for(l,m,c) for (l,m,c,r),s in lookup.items()),
  "no_identity_arm_matches_locked_reference":paired and raw["reference"]["sha256"]==sha(REFERENCE),
  "positive_cases_exact_both_modes":all((o:=lookup[l,m,"positive",r]["observation"])["explained"] and o["matrix"]==M and o["residual_dims"]==0 and o["transforms"]==[] for l in LAYOUTS for m in MODES for r in range(1,6)),
  "stable_identity_corruptions_refused":all(not lookup[l,"stable_identity",c,r]["observation"]["explained"] and lookup[l,"stable_identity",c,r]["observation"]["matrix"]==[] for l in LAYOUTS for c in CONDS[1:] for r in range(1,6)),
  "within_cell_outputs_deterministic":all(lookup[l,m,c,r]["observation"]==lookup[l,m,c,1]["observation"] for l in LAYOUTS for m in MODES for c in CONDS for r in range(2,6)),
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in raw["provenance"]["source_sha256"].items())}
 summary={}
 for mode in MODES:
  summary[mode]={}
  for l in LAYOUTS:
   summary[mode][l]={}
   for c in CONDS:
    obs=[lookup[l,mode,c,r]["observation"] for r in range(1,6)];accepted=sum(bool(o["explained"]) for o in obs)
    summary[mode][l][c]={"n":5,"accepted":accepted,"exact_generator":sum(o["matrix"]==M for o in obs),"alternative_matrix":sum(bool(o["explained"]) and o["matrix"]!=M for o in obs),"refused":5-accepted,"candidate_count":obs[0]["checked"],"matrix":obs[0]["matrix"],"transforms":obs[0]["transforms"]}
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"integrity_and_positive_semantics_pass":all(v for k,v in checks.items() if k!="stable_identity_corruptions_refused"),"preregistered_identity_refusal_prediction_supported":checks["stable_identity_corruptions_refused"],"by_mode_layout_condition":summary,"interpretation":"The preregistered prediction that stable IDs eliminate corrupted decompositions is not supported: the stable-identity arm still accepts 15/45 corrupted cases, all with alternative matrices. It preserves all positive cases and reduces aggregate corruption acceptance from 20/45 to 15/45. This is a schema ablation, not proof that the substrate generally supplies relation identities."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"summary":summary},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
