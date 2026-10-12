#!/usr/bin/env python3
"""Independent analysis of end-to-end GenInfer residual robustness."""
from __future__ import annotations
import hashlib,json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"evaluation/reports/substrate_genmint_residual_robustness_v1_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_genmint_residual_robustness_v1_analysis_20260926.json"
M=[1,1,0,2];LAYOUTS={"original":[(0,0),(1,0),(2,0),(0,2)],"orthogonal_pairs":[(0,0),(0,1),(1,0),(1,1)],"paired_square":[(0,0),(1,0),(0,1),(1,1)]};PREDS=["p0","p0","p1","p1"]
CONDS=["positive","corrupt_p0_r_1","corrupt_p0_r_2","corrupt_p0_r_3"];MODES=["no_identity","stable_identity"];ENABLED=[False,True]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mapped(rows,slots):
 a,b,c,d=M;mins=[min(x[i] for x in rows) for i in slots];out=[]
 for row in rows:
  rr=list(row);rr[slots[0]]=a*(row[slots[0]]-mins[0])+b*(row[slots[1]]-mins[1]);rr[slots[1]]=c*(row[slots[0]]-mins[0])+d*(row[slots[1]]-mins[1]);out.append(rr)
 return out
def expected(layout,mode,cond):
 stable=mode=="stable_identity";slots=[2,3] if stable else [1,2];base=[]
 for i,(p,(r,c)) in enumerate(zip(PREDS,LAYOUTS[layout])):base.append([p,f"rel{i}",r,c,"red"] if stable else [p,r,c,"red"])
 first=mapped(base,slots);second=mapped(first,slots)
 if cond!="positive":first[0][slots[0]]+=int(cond.rsplit("_",1)[1])
 return base,first,second
def stable_view(s):
 out={k:v for k,v in s.items() if k!="repetition"}
 out["initial_linear_generators"]=[{k:v for k,v in g.items() if k!="node"} for g in s["initial_linear_generators"]]
 out["steps"]=[]
 for step in s["steps"]:
  row={k:v for k,v in step.items() if k!="closure_seconds"}
  row["linear_generators"]=[{k:v for k,v in g.items() if k!="node"} for g in step["linear_generators"]]
  out["steps"].append(row)
 out["final_linear_generators"]=[{k:v for k,v in g.items() if k!="node"} for g in s["final_linear_generators"]]
 return out
def main():
 raw=json.loads(SRC.read_text());samples=raw["samples"];lookup={(s["layout"],s["mode"],s["condition"],s["gen_infer_enabled"],s["repetition"]):s for s in samples}
 cells=[(l,m,c,e) for l in LAYOUTS for m in MODES for c in CONDS for e in ENABLED];rng=random.Random(20260926);sched={}
 for rep in range(1,6):order=cells.copy();rng.shuffle(order);sched[str(rep)]=[list(x) for x in order]
 expected_keys={(l,m,c,e,r) for l in LAYOUTS for m in MODES for c in CONDS for e in ENABLED for r in range(1,6)}
 valid_status={"recognized","recognized_transformed","recognized_duplicate","minted"}
 def all_steps():return [(key,s,step) for key,s in lookup.items() for step in s["steps"]]
 checks={"complete_240_sequences":len(samples)==240 and set(lookup)==expected_keys,
  "locked_factorial_and_schedule":raw["protocol"]["matrix"]==M and raw["protocol"]["conditions"]==CONDS and raw["protocol"]["modes"]==MODES and raw["protocol"]["schedule_by_repetition"]==sched,
  "base_and_target_signatures_match_design":all((s["base"],s["steps"][0]["goal"],s["steps"][1]["goal"])==expected(l,m,c) for (l,m,c,e,r),s in lookup.items()),
  "two_terminal_observations_per_sequence":all(len(s["steps"])==2 and all(st["observation"]["attrs"]["status"] in valid_status for st in s["steps"]) for s in samples),
  "disabled_arm_does_not_mint_linear_generators":all(not s["initial_linear_generators"] and all(not st["linear_generators"] for st in s["steps"]) for s in samples if not s["gen_infer_enabled"]),
  "repeated_semantic_outputs_stable":all(len({json.dumps(stable_view(lookup[l,m,c,e,r]),sort_keys=True) for r in range(1,6)})==1 for l,m,c,e in cells),
  "finite_positive_closure_timings":all(math.isfinite(float(st["closure_seconds"])) and st["closure_seconds"]>0 for _,_,st in all_steps()),
  "native_hash_current":sha(Path(raw["provenance"]["native_extension_path"]))==raw["provenance"]["native_extension_sha256"],
  "source_hashes_current":all(sha(ROOT/p)==h for p,h in raw["provenance"]["source_sha256"].items())}
 summary={}
 for layout in LAYOUTS:
  summary[layout]={}
  for mode in MODES:
   summary[layout][mode]={}
   for cond in CONDS:
    summary[layout][mode][cond]={}
    for enabled in ENABLED:
     rows=[lookup[layout,mode,cond,enabled,r] for r in range(1,6)];first=[x["steps"][0] for x in rows];later=[x["steps"][1] for x in rows]
     first_gens=[g for x in first for g in x["linear_generators"]];allfirst=[g["matrix"] for g in first_gens]
     later_status=[x["observation"]["attrs"]["status"] for x in later]
     summary[layout][mode][cond]["enabled" if enabled else "disabled"]={"n":5,"first_statuses":dict((v,sum(x["observation"]["attrs"]["status"]==v for x in first)) for v in sorted({x["observation"]["attrs"]["status"] for x in first})),"first_exact_generator_count":sum(any(g["matrix"]==M for g in x["linear_generators"]) for x in first),"first_generator_matrix_counts":{json.dumps(matrix):allfirst.count(matrix) for matrix in sorted({tuple(g["matrix"]) for g in first_gens}) for matrix in [list(matrix)]},"first_quanta_median":statistics.median(x["quanta_added"] for x in first),"downstream_statuses":dict((v,later_status.count(v)) for v in sorted(set(later_status))),"downstream_quanta_median":statistics.median(x["quanta_added"] for x in later),"final_generator_counts":[len(x["final_linear_generators"]) for x in rows],"median_closure_seconds":{"first":statistics.median(x["closure_seconds"] for x in first),"downstream":statistics.median(x["closure_seconds"] for x in later)}}
 contrasts={}
 for layout in LAYOUTS:
  for mode in MODES:
   for cond in CONDS:
    key=f"{layout}/{mode}/{cond}";on=summary[layout][mode][cond]["enabled"];off=summary[layout][mode][cond]["disabled"]
    contrasts[key]={"enabled_first_exact_generator":on["first_exact_generator_count"],"enabled_downstream_recognized_transformed":on["downstream_statuses"].get("recognized_transformed",0),"disabled_downstream_recognized_transformed":off["downstream_statuses"].get("recognized_transformed",0),"enabled_minus_disabled_downstream_quanta_median":on["downstream_quanta_median"]-off["downstream_quanta_median"],"enabled_final_generator_counts":on["final_generator_counts"]}
 result={"schema_version":1,"source":str(SRC.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"summary_by_layout_mode_condition":summary,"enabled_disabled_contrasts":contrasts,"runtime_seconds":raw["runtime_seconds"],"interpretation":"Full-seed, authored repeated-predicate sensitivity only. Enabled-arm outcomes and generator recovery are descriptive; they are not universal capability estimates."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"analysis":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"runtime_seconds":result["runtime_seconds"],"contrasts":contrasts},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
