#!/usr/bin/env python3
"""Route-aware v1.1 reanalysis: score only reuse of the acquired linear map."""
import hashlib,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/substrate_genmint_heldout_transfer_v1_20260926.json";LOCK=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_PREREG_20260926.md";AMEND=ROOT/"docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_V1_1_AMENDMENT_20260926.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(x):
 ts=x["heldout"]["transforms"]; rec=next((t for t in ts if t.get("generator")),None)
 if rec is None:return {"route":"no_generator_transform","correct":None}
 gen=next((g for g in x["final_linear_generators"] if g["name"]==rec["generator"]),None)
 if gen is None:return {"route":"other_held_generator","selected_generator":rec["generator"],"correct":None}
 initial_names={g["name"] for g in x["initial_linear_generators"]};train_names={g["name"] for g in x["train"]["linear_generators"]}; newly_minted=rec["generator"] in train_names-initial_names
 m=gen["matrix"]
 if len(m)!=4:return {"route":"unsupported_linear_map","selected_generator":rec["generator"],"correct":None}
 base=x["heldout_base"];mins=[min(r[j] for r in base) for j in (1,2)];pred=[]
 for p,r,c,v in base:
  u=r-mins[0];w=c-mins[1];out=[p,m[0]*u+m[1]*w,m[2]*u+m[3]*w,v]
  for t in rec.get("transforms") or []:
   dim=t.get("dim")
   if t.get("kind")=="shift" and dim in (1,2):out[dim]+=t.get("delta",0)
   elif t.get("kind")=="subst" and out[3]==t.get("from"):out[3]=t.get("to")
  pred.append(out)
 return {"route":"acquired_linear" if newly_minted and m==[1,1,0,2] else "other_linear_generator","selected_generator":rec["generator"],"matrix":m,"predictions":pred,"correct":[a==b for a,b in zip(pred,x["heldout_target"])]}
def main():
 d=json.loads(RAW.read_text());rows=[];checks={"lock_hash":d["source_sha256"]["docs/research/engine_substrate/SUBSTRATE_GENMINT_HELDOUT_TRANSFER_PREREG_20260926.md"]==sha(LOCK),"runner_hash":d["source_sha256"]["scripts/genmint_heldout_transfer_probe_v1.py"]==sha(ROOT/"scripts/genmint_heldout_transfer_probe_v1.py"),"native_hash":d["native"]["sha256"]==sha(Path(d["native"]["path"])),"sample_count":len(d["samples"])==180};cells=defaultdict(list)
 for x in d["samples"]:
  p0=d["inputs"]["groups"][x["group"]]["p0"];held=d["inputs"]["groups"][x["group"]]["heldout"];train=[i for i in range(8) if i not in held]
  rows.append((x,score(x)));cells[x["group"],x["training_condition"],x["heldout_condition"],x["gen_infer_enabled"]].append((x,rows[-1][1]))
  checks[f"partition_{len(checks)}"]=x["training_indices"]==train and x["heldout_indices"]==held and len(x["training_base"])==6 and len(x["heldout_base"])==2 and [r[0] for r in x["training_base"]]==["p0" if i in p0 else "p1" for i in train]
 summaries=[]
 for (g,t,h,en),items in sorted(cells.items()):
  scored=[z for _,z in items if z["route"]=="acquired_linear"];other=sum(z["route"]=="other_held_generator" for _,z in items);none=sum(z["route"]=="no_generator_transform" for _,z in items)
  summaries.append({"group":g,"training_condition":t,"heldout_condition":h,"gen_infer_enabled":en,"n":len(items),"training_statuses":sorted({str(x["train"]["status"]) for x,_ in items}),"heldout_statuses":sorted({str(x["heldout"]["status"]) for x,_ in items}),"acquired_matrix_present":sum(any(q["matrix"]==[1,1,0,2] for q in x["final_linear_generators"]) for x,_ in items),"route_acquired_linear":len(scored),"route_other_held_generator":other,"route_no_transform":none,"acquired_linear_rows_correct":sum(sum(z["correct"]) for z in scored),"acquired_linear_rows_scored":2*len(scored),"exact_acquired_linear_holdout_pairs":sum(all(z["correct"]) for z in scored),"acquired_linear_quanta_train":sorted({x["train"]["quanta_added"] for x,_ in items}),"acquired_linear_quanta_holdout":sorted({x["heldout"]["quanta_added"] for x,_ in items}),"deterministic":len({json.dumps((x["train"]["status"],x["train"]["linear_generators"],x["heldout"]["status"],z),sort_keys=True) for x,z in items})==1})
 checks["balanced_36_cells"]=len(cells)==36 and all(len(v)==5 for v in cells.values())
 positives=[s for s in summaries if s["gen_infer_enabled"] and s["training_condition"]=="clean" and s["heldout_condition"]=="clean"]
 checks["clean_enabled_gate_uses_acquired_matrix"]=len(positives)==3 and all(s["acquired_matrix_present"]==5 and s["route_acquired_linear"]==5 and s["exact_acquired_linear_holdout_pairs"]==5 and s["heldout_statuses"]==["recognized_transformed"] for s in positives)
 checks["deterministic_within_cell"]=all(s["deterministic"] for s in summaries)
 out={"raw_sha256":sha(RAW),"amendment_sha256":sha(AMEND),"analyzer_sha256":sha(Path(__file__)),"checks":checks,"all_amended_checks_pass":all(checks.values()),"summaries":summaries};path=ROOT/"evaluation/reports/substrate_genmint_heldout_transfer_v1_1_analysis_20260926.json";path.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()
