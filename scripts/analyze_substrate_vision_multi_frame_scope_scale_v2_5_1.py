#!/usr/bin/env python3
"""Independent equation, integrity, parity, and work audit for v2.5."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_workers_raw_20260929.json"
DRIVER=ROOT/"evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_20260929.json"
LOCK=ROOT/"evaluation/substrate_capability/vision_multi_frame_scope_scale_v2_5_1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_analysis_20260929.json"
SIZES=(16,32,48);SEEDS=(4101,7301,10703)
SIBLING_CASES=((0,"none"),(1,"equal"),(1,"contrasting"),(2,"equal"),(2,"contrasting"))
SCOPES=("global","scoped");MODES=("plain","audit")

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def cid(seed,side,sibs,state,scope,mode,omit=False):
 return f"s{seed}_n{side}_sib{sibs}_{state}_{scope}_{mode}"+("_omit" if omit else "")

def expected_outputs(row):
 side=row["side"];n=side*side;states=row["initial_act_by_frame"];affs=row["aff_by_frame"]
 frames=len(states);all_values=[float(x) for s in states for x in [s]*n]
 out=[];residual=0.0;updates=[]
 owner_counts=row["member_counts"]
 for fi,state in enumerate(states):
  pool=(all_values if row["scope"]=="global" else [float(state)]*owner_counts[fi])
  pop_mean=sum(pool)/len(pool)
  vals=[];coverage=[]
  omitted_index=0 if row["omission"] and fi==0 else None
  for i in range(n):
   if omitted_index is not None and i==omitted_index:
    vals.append(-1.0);coverage.append(False);continue
   r,c=divmod(i,side);neighbours=[]
   for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
    if 0<=rr<side and 0<=cc<side:neighbours.append(float(state))
   local=sum(neighbours)/len(neighbours) if neighbours else 0.0
   vals.append(max(float(affs[fi][i])+local-pop_mean,0.0));coverage.append(True)
  out.append(vals);updates.append(coverage)
 for actual,expected,cov in zip(row["actual_act_next"],out,updates):
  for a,e,has in zip(actual,expected,cov):
   if has:residual=max(residual,abs(float(a)-float(e)))
 return out,updates,residual

def work_summary(r):
 c=r["global_counters"];per=Counter();per_clause=Counter()
 for _,metric,value in r["per_rule_counters"]:per[metric]+=int(value)
 for _,pos,value in r["per_clause_counters"]:per_clause[int(pos)]+=int(value)
 return {"candidate_tests":int(c.get("cand_tested",0)),"candidate_attributed":per["candidate_tests"],
  "term_evaluations":int(c.get("term_evals_total",0)),"term_attributed":per["term_evaluations"],
  "term_units":int(c.get("term_units_total",0)),"term_units_by_kind":{k:int(v) for k,v in c.items() if k.startswith("term_unit:")},
  "operation_applications":int(r["progress"]),"wall_ns":int(r["closure_wall_ns"]),
  "cpu_ns":int(r["closure_cpu_ns"]),"peak_rss_bytes":int(r["peak_rss_bytes"]),
  "graph_nodes":r["graph_node_count"],"graph_edges":r["graph_edge_count"],"frame_digests":r["frame_digests"]}

def main():
 raw=json.loads(RAW.read_text());driver=json.loads(DRIVER.read_text());locked=json.loads(LOCK.read_text())["locked_inputs"]
 rows=raw["runs"];factor=[r for r in rows if not r["omission"]];omissions=[r for r in rows if r["omission"]]
 by={r["cell_id"]:r for r in rows}
 expected_ids={cid(seed,side,sib,state,scope,mode) for side in SIZES for sib,state in SIBLING_CASES
   for seed in SEEDS for scope in SCOPES for mode in MODES}
 omission_ids={cid(SEEDS[0],16,1,"contrasting",scope,mode,True) for scope in SCOPES for mode in MODES}
 checks={
  "184_unique_registered_workers":len(rows)==184 and len({r["pid"] for r in rows})==184,
  "complete_180_factorial_plus_four_omission_cells":len(factor)==180 and len(omissions)==4 and set(by)==expected_ids|omission_ids,
  "source_lock_matches_every_worker_and_postrun":raw["locked_inputs"]==locked==driver["locked_inputs"] and driver["post_run_inputs"]==locked and all(r["worker_started_inputs"]==r["worker_finished_inputs"]==locked and r["source_stable"] for r in rows),
  "frame_population_and_no_budget_exit":all(r["frame_count"]==r["sibling_frames"]+1 and r["member_counts"]==[r["units_per_frame"]]*r["frame_count"] and r["graph_node_count"]>=sum(r["member_counts"]) and 0<r["progress"]<r["budget"] and not r["budget_exit"] for r in factor),
 }
 all_res=[];profile=[]
 for r in rows:
  predicted,coverage,residual=expected_outputs(r)
  all_res.append(residual)
  r["analysis_expected_outputs"]=predicted;r["analysis_update_coverage"]=coverage;r["analysis_equation_residual"]=residual
 checks["all_clean_outputs_match_independent_equations"] = all(r["analysis_equation_residual"]<=1e-12 for r in factor)
 checks["omission_is_detected_and_equations_reconcile"] = all(
  r["member_counts"][0]==r["units_per_frame"]-1
  and r["analysis_update_coverage"][0].count(False)==1
  and r["actual_act_next"][0][0]==-1.0
  and r["analysis_equation_residual"]<=1e-12 for r in omissions)
 pairs=[]
 for seed in SEEDS:
  for side in SIZES:
   for sib,state in SIBLING_CASES:
    for scope in SCOPES:
     p=by[cid(seed,side,sib,state,scope,"plain")];a=by[cid(seed,side,sib,state,scope,"audit")]
     pairs.append((p,a))
 checks["counter_on_off_outputs_and_graph_sizes_match"] = len(pairs)==90 and all(
  p["actual_act_next"]==a["actual_act_next"] and p["frame_digests"]==a["frame_digests"]
  and p["member_counts"]==a["member_counts"] and p["graph_node_count"]==a["graph_node_count"]
  and p["graph_edge_count"]==a["graph_edge_count"] and p["progress"]==a["progress"] for p,a in pairs)
 audited=[r for r in rows if r["mode"]=="audit"]
 checks["rule_counter_conservation"] = all(
  int(r["global_counters"].get("cand_tested",0))==sum(int(v) for _,m,v in r["per_rule_counters"] if m=="candidate_tests")
  and int(r["global_counters"].get("term_evals_total",0))==sum(int(v) for _,m,v in r["per_rule_counters"] if m=="term_evaluations")
  and int(r["global_counters"].get("term_units_total",0))==sum(int(v) for _,m,v in r["per_rule_counters"] if m=="term_units")
  for r in audited)
 checks["candidate_count_matches_visible_owner_bindings"] = all(
  int(r["global_counters"].get("cand_tested",0))==sum(r["member_counts"]) for r in audited)
 checks["term_unit_counter_closed_forms"] = all(
  int(r["global_counters"].get("term_unit:NodesOfType",0))==
  (sum(r["member_counts"])*(2*r["frame_count"]*r["units_per_frame"]+1) if r["scope"]=="global" else sum(r["member_counts"]))
  for r in audited)
 checks["scoped_target_is_invariant_to_sibling_count_and_state"] = all(
  by[cid(s,n,k,st,"scoped","plain")]["actual_act_next"][0]==by[cid(s,n,k2,st2,"scoped","plain")]["actual_act_next"][0]
  for s in SEEDS for n in SIZES for (k,st),(k2,st2) in
  [((0,"none"),(1,"equal")),((1,"equal"),(1,"contrasting")),((1,"contrasting"),(2,"equal")),((2,"equal"),(2,"contrasting"))])
 checks["global_contrast_changes_target_and_equal_state_does_not"] = all(
  by[cid(s,n,1,"equal","global","plain")]["actual_act_next"][0]==by[cid(s,n,0,"none","global","plain")]["actual_act_next"][0]
  and by[cid(s,n,1,"contrasting","global","plain")]["actual_act_next"][0]!=by[cid(s,n,1,"equal","global","plain")]["actual_act_next"][0]
  for s in SEEDS for n in SIZES)
 checks["all_work_profiles_repeat_by_seed_and_factor"] = all(
  len({(int(r["global_counters"].get("cand_tested",0)),int(r["global_counters"].get("term_evals_total",0)),
        int(r["global_counters"].get("term_units_total",0)),
        tuple(sorted((k,v) for k,v in r["global_counters"].items() if not k.endswith("_ns")))) for r in
       [by[cid(s,n,k,st,sc,"audit")] for s in SEEDS]})==1
  for n in SIZES for k,st in SIBLING_CASES for sc in SCOPES)
 checks["native_engine_provenance_valid"] = raw["locked_inputs"]["engine_provenance"].get("source_match") in ("own","shared") and not raw["locked_inputs"]["engine_provenance"].get("stale_rust")
 summaries=[]
 for side in SIZES:
  for sib,state in SIBLING_CASES:
   for scope in SCOPES:
    xs=[by[cid(s,side,sib,state,scope,"plain")] for s in SEEDS]
    ys=[work_summary(by[cid(s,side,sib,state,scope,"audit")]) for s in SEEDS]
    summaries.append({"side":side,"units_per_frame":side*side,"sibling_frames":sib,"sibling_state":state,
      "total_units":(sib+1)*side*side,"scope":scope,"replicates":3,
      "candidate_tests":ys[0]["candidate_tests"],"term_evaluations_median":statistics.median(x["term_evaluations"] for x in ys),
      "term_units_median":statistics.median(x["term_units"] for x in ys),
      "nodesoftype_units_median":statistics.median(x["term_units_by_kind"].get("term_unit:NodesOfType",0) for x in ys),
      "closure_wall_seconds_median":statistics.median(x["wall_ns"] for x in ys)/1e9,
      "closure_wall_seconds_range":[min(x["wall_ns"] for x in ys)/1e9,max(x["wall_ns"] for x in ys)/1e9],
      "peak_rss_mib_median":statistics.median(x["peak_rss_bytes"] for x in ys)/(1024**2),
      "max_equation_residual":max(r["analysis_equation_residual"] for r in xs),
      "target_outputs_equal_across_seeds":len({tuple(r["actual_act_next"][0]) for r in xs})==3})
 result={"schema_version":1,"raw_sha256":sha(RAW),"driver_sha256":sha(DRIVER),"lock_sha256":sha(LOCK),
  "checks":checks,"all_checks_pass":all(checks.values()),"factorial_cell_count":len(factor),
  "omission_diagnostic_count":len(omissions),"summary_by_size_sibling_state_scope":summaries,
  "omission_diagnostics":[{"cell_id":r["cell_id"],"scope":r["scope"],"mode":r["mode"],
    "member_counts":r["member_counts"],"missing_target_index":0,"residual":r["analysis_equation_residual"]} for r in omissions],
  "claim_boundary":"Controlled synthetic visual-domain st_settle rule across up to three declared SUnit frames. Exact equation checks discriminate global competition from frame-local aggregation. This does not run image ingestion/learning or establish natural frame prevalence or learned cheap-cut locality."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"output":str(OUT),"all_checks_pass":result["all_checks_pass"],"checks":checks,"summaries":summaries},indent=2))
 return 0 if result["all_checks_pass"] else 1

if __name__=="__main__":raise SystemExit(main())
