#!/usr/bin/env python3
"""Independent held-out partition, prediction, and outcome analysis."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_geninfer_heldout_relation_v1_20260926.json";LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENINFER_HELDOUT_RELATION_PREREG_20260926.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(row):
 o=row["observation"];m=o["matrix"];preds=[]
 for p,r,q,v in row["heldout_base"]:
  if len(m)!=4:out=None
  else:
   out=[p,m[0]*r+m[1]*q,m[2]*r+m[3]*q,v]
   for t in o["transforms"]:
    if t.get("pred") not in (None,p):continue
    if t.get("kind")=="shift" and t.get("dim") in (1,2):out[t["dim"]]+=t["delta"]
    elif t.get("kind")=="subst" and out[3]==t.get("from"):out[3]=t.get("to")
  preds.append(out)
 return preds
def main():
 d=json.loads(RAW.read_text()); groups=d["inputs"]["groups"]; pts=[tuple(x) for x in d["inputs"]["points"]]; mat=d["inputs"]["matrix"]; cells=defaultdict(list);checks={"raw_lock_hash":d["source_sha256"]["docs/research/engine_substrate/SUBSTRATE_GENINFER_HELDOUT_RELATION_PREREG_20260926.md"]==sha(LOCK),"runner_hash":d["source_sha256"]["scripts/geninfer_heldout_relation_probe_v1.py"]==sha(ROOT/"scripts/geninfer_heldout_relation_probe_v1.py"),"native_hash":d["native"]["sha256"]==sha(Path(d["native"]["path"])),"sample_count":len(d["samples"])==90}
 for x in d["samples"]:
  g=x["group"]; p0=groups[g]["p0"]; h=groups[g]["heldout"]; tr=[i for i in range(8) if i not in h];a,b,c,e=mat; expected_base=[];expected_train=[];expected_hbase=[];expected_htarget=[]
  for i,(r,q) in enumerate(pts):
   pred="p0" if i in p0 else "p1";base=[pred,r,q,"red"];target=[pred,a*r+b*q,c*r+e*q,"red"]
   if i in tr:
    bump=0
    if x["training_condition"]=="uniform_p0_plus1" and pred=="p0":bump=1
    if x["training_condition"]=="inconsistent_p0_plus1_plus2" and pred=="p0":
     pi=[j for j in tr if j in p0]
     if i in pi[:2]:bump=1 if i==pi[0] else 2
    target[1]+=bump;expected_base.append(base);expected_train.append(target)
   else:
    if x["heldout_condition"]=="uniform_p0_plus1" and pred=="p0":target[1]+=1
    expected_hbase.append(base);expected_htarget.append(target)
  key=f"partition_{g}_{x['training_condition']}_{x['heldout_condition']}_{x['repetition']}"
  checks[key]=x["training_indices"]==tr and x["heldout_indices"]==h and x["training_base"]==expected_base and x["training_target"]==expected_train and x["heldout_base"]==expected_hbase and x["heldout_target"]==expected_htarget and len(x["training_base"])==6 and len(x["heldout_base"])==2
  recomputed=score(x);checks[f"score_{g}_{x['training_condition']}_{x['heldout_condition']}_{x['repetition']}"]=x["predictions"]==recomputed and x["heldout_row_correct"]==[a==b for a,b in zip(recomputed,x["heldout_target"])]
  cells[g,x["training_condition"],x["heldout_condition"]].append(x)
 summaries=[]
 for (g,t,h),xs in sorted(cells.items()):
  observations=[x["observation"] for x in xs]; summaries.append({"group":g,"training_condition":t,"heldout_condition":h,"n":len(xs),"train_generator_recovery":sum(o["matrix"]==mat for o in observations),"training_decomposition_accepted":sum(bool(o["explained"]) for o in observations),"heldout_correct_rows":sum(sum(x["heldout_row_correct"]) for x in xs),"heldout_total_rows":2*len(xs),"exact_both_heldout_relations":sum(all(x["heldout_row_correct"]) for x in xs),"matrices":sorted({json.dumps(o["matrix"],separators=(",",":")) for o in observations}),"residuals":sorted({json.dumps(o["transforms"],sort_keys=True,separators=(",",":")) for o in observations}),"deterministic":len({json.dumps(x["observation"],sort_keys=True) for x in xs})==1 and len({json.dumps(x["heldout_row_correct"]) for x in xs})==1})
 checks["balanced_18_cells"]=len(cells)==18 and all(len(xs)==5 for xs in cells.values())
 checks["clean_train_clean_holdout_gate"]=all(s["train_generator_recovery"]==5 and s["heldout_correct_rows"]==10 and s["exact_both_heldout_relations"]==5 for s in summaries if s["training_condition"]=="clean" and s["heldout_condition"]=="clean")
 checks["repeated_outcomes_deterministic"]=all(s["deterministic"] for s in summaries)
 out={"raw_sha256":sha(RAW),"checks":checks,"all_checks_pass":all(checks.values()),"summaries":summaries};path=ROOT/"evaluation/reports/substrate_geninfer_heldout_relation_v1_analysis_20260926.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()
