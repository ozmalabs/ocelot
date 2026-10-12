#!/usr/bin/env python3
"""Independent full-seed held-out generator/residual scoring."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_genmint_heldout_transfer_v1_20260926.json";LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_PREREG_20260926.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(x):
 rec=next((t for t in x["heldout"]["transforms"] if t.get("generator")),None)
 if rec is None:return None
 gen=next((g for g in x["final_linear_generators"] if g["name"]==rec["generator"]),None)
 if not gen or len(gen["matrix"])!=4:return None
 m=gen["matrix"];base=x["heldout_base"];mins=[min(r[j] for r in base) for j in (1,2)];pred=[]
 for p,r,c,v in base:
  u=r-mins[0];w=c-mins[1];out=[p,m[0]*u+m[1]*w,m[2]*u+m[3]*w,v]
  k=rec.get("k",1)
  # Reapply the matrix k-1 more times, preserving the local origin convention.
  for _ in range(max(0,int(k)-1)):
   mm=m;rr=out[1];cc=out[2];out[1]=mm[0]*rr+mm[1]*cc;out[2]=mm[2]*rr+mm[3]*cc
  for t in rec.get("transforms") or []:
   dim=t.get("dim")
   if t.get("kind")=="shift" and dim in (1,2):out[dim]+=t.get("delta",0)
   elif t.get("kind")=="subst" and out[3]==t.get("from"):out[3]=t.get("to")
  pred.append(out)
 return {"generator_name":gen["name"],"matrix":m,"predictions":pred,"correct":[a==b for a,b in zip(pred,x["heldout_target"])]}
def main():
 d=json.loads(RAW.read_text());checks={"lock_hash":d["source_sha256"]["docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_PREREG_20260926.md"]==sha(LOCK),"runner_hash":d["source_sha256"]["scripts/genmint_heldout_transfer_probe_v1.py"]==sha(ROOT/"scripts/genmint_heldout_transfer_probe_v1.py"),"native_hash":d["native"]["sha256"]==sha(Path(d["native"]["path"])),"sample_count":len(d["samples"])==180};cells=defaultdict(list)
 for x in d["samples"]:
  p0=d["inputs"]["groups"][x["group"]]["p0"];held=d["inputs"]["groups"][x["group"]]["heldout"];train=[i for i in range(8) if i not in held];checks[f"input_{len(checks)}"]=len(x["training_base"])==6 and len(x["heldout_base"])==2 and x["training_indices"]==train and x["heldout_indices"]==held and all((r[0]==("p0" if i in p0 else "p1")) for r,i in zip(x["training_base"],train))
  pred=score(x);x["independent_heldout_score"]=pred;cells[x["group"],x["training_condition"],x["heldout_condition"],x["gen_infer_enabled"]].append(x)
 summaries=[]
 for (g,t,h,en),xs in sorted(cells.items()):
  scr=[x["independent_heldout_score"] for x in xs];valid=[z for z in scr if z is not None]
  summaries.append({"group":g,"training_condition":t,"heldout_condition":h,"gen_infer_enabled":en,"n":len(xs),"train_statuses":sorted({str(x["train"]["status"]) for x in xs}),"heldout_statuses":sorted({str(x["heldout"]["status"]) for x in xs}),"linear_matrices":sorted({json.dumps(y["matrix"],separators=(",",":")) for x in xs for y in x["final_linear_generators"]}),"expected_generator_acquired":sum(any(y["matrix"]==[1,1,0,2] for y in x["final_linear_generators"]) for x in xs),"heldout_transform_present":sum(z is not None for z in scr),"heldout_correct_rows":sum(sum(z["correct"]) for z in valid),"heldout_total_rows":2*len(xs),"exact_both_rows":sum(all(z["correct"]) for z in valid),"quanta_added_train":sorted({x["train"]["quanta_added"] for x in xs}),"quanta_added_heldout":sorted({x["heldout"]["quanta_added"] for x in xs}),"deterministic":len({json.dumps((x["train"]["status"],x["train"]["linear_generators"],x["heldout"]["status"],x["heldout"]["transforms"],x["independent_heldout_score"]),sort_keys=True) for x in xs})==1})
 checks["balanced_36_cells"]=len(cells)==36 and all(len(x)==5 for x in cells.values());checks["clean_enabled_positive_gate"]=all(s["expected_generator_acquired"]==5 and s["heldout_statuses"]==["recognized_transformed"] and s["exact_both_rows"]==5 for s in summaries if s["gen_infer_enabled"] and s["training_condition"]=="clean" and s["heldout_condition"]=="clean");checks["repeat_determinism"]=all(s["deterministic"] for s in summaries)
 out={"raw_sha256":sha(RAW),"checks":checks,"all_integrity_and_positive_gates_pass":all(checks.values()),"summaries":summaries};path=ROOT/"evaluation/reports/substrate_genmint_heldout_transfer_v1_analysis_20260926.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()
