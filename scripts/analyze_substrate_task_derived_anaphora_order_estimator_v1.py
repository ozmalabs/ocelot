#!/usr/bin/env python3
"""Independent integrity, semantic, ranking, and cost analysis."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/anaphora_order_estimator_v1_raw_20260929.json"
LOCK=ROOT/"evaluation/substrate_capability/anaphora_order_estimator_v1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/anaphora_order_estimator_v1_analysis_20260929.json"
RULE="rule_anaphoric_it_resolves_to_prior_about_concept"
ORDERS=((0,1,2,3),(1,0,2,3),(1,2,0,3),(1,2,3,0),(2,1,0,3),(2,1,3,0),(2,3,1,0),(3,2,1,0))
BUDGETS=(8,32,128)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 expected={(d,f"exact_{i}",r) for d in (0,2,4) for i in range(8) for r in range(2)}|{(d,m,r) for d in (0,2,4) for m in ("plain_source","plain_B8","plain_B32","plain_B128") for r in range(2)}
 actual={(int(x["distractors"]),x["mode"],int(x["replicate"])) for x in runs if "worker_error" not in x}
 checks={"72_exact_factorial_cells":len(runs)==72 and len(actual)==72 and actual==expected,
 "unique_worker_processes":len({x["pid"] for x in runs if "worker_error" not in x})==72,
 "source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x.get("before")==lock==x.get("after") for x in runs if "worker_error" not in x),
 "all_logs_present_and_hash_valid":len(raw["child_logs"])==72 and all((ROOT/x["path"]).is_file() and sha(ROOT/x["path"])==x["sha256"] and x["returncode"]==0 for x in raw["child_logs"])}
 exact={(int(x["distractors"]),int(x["replicate"]),int(x["mode"].split("_")[1])):x for x in runs if x["mode"].startswith("exact_") and "worker_error" not in x}
 plain={(int(x["distractors"]),int(x["replicate"]),x["mode"]):x for x in runs if x["mode"].startswith("plain_") and "worker_error" not in x}
 exact_costs={};predictors={};rows=[]
 for d in (0,2,4):
  for rep in range(2):
   group=[exact[d,rep,i] for i in range(8) if (d,rep,i) in exact]
   checks[f"D{d}_r{rep}_all_eight_orders_present"]=len(group)==8 and {tuple(x["installed_order"]) for x in group}==set(ORDERS)
   checks[f"D{d}_r{rep}_all_order_task_oracles"]=len(group)==8 and all(x["task_oracle_pass"] for x in group)
   checks[f"D{d}_r{rep}_all_order_fixed_points"]=len(group)==8 and all(x["terminal_report"].get("status")=="fixed_point" and int(x["terminal_report"].get("budget_overshoot",0))==0 for x in group)
   checks[f"D{d}_r{rep}_whole_graph_parity"]=len({x["graph_sha256"] for x in group})==1
   costmap={}
   for x in group:
    key=tuple(x["installed_order"]);rid=int(x["target_rule_id"])
    vals=[int(v) for i,k,v in x["per_rule_counters"] if int(i)==rid and str(k)=="candidate_tests"]
    clauses={int(ci):int(n) for i,ci,n in x["clause_counters"] if int(i)==rid}
    checks[f"{d}_{rep}_{key}_one_target_candidate_metric"]=len(vals)==1 and rid>=0 and int(x["target_candidate_tests"])==vals[0]
    checks[f"{d}_{rep}_{key}_clause_counter_conservation"]=len(clauses)==4 and set(clauses)==set(range(4)) and sum(clauses.values())==vals[0]
    costmap[key]=vals[0] if len(vals)==1 else -1
   exact_costs[d,rep]=costmap
   # The estimator reads the same pre-closure snapshot in all eight exact arms.
   for budget in BUDGETS:
    records=[x["estimator_predictions"].get(str(budget),x["estimator_predictions"].get(budget)) for x in group]
    serial=[json.dumps(y,sort_keys=True) for y in records]
    checks[f"D{d}_r{rep}_B{budget}_deterministic_predictions"]=len(records)==8 and len(set(serial))==1 and records[0] is not None
    if not records or records[0] is None: continue
    rec=records[0];idx=int(rec["selected_order_index"]);pred=tuple(rec["selected_order"])
    checks[f"D{d}_r{rep}_B{budget}_selected_realized_order"]=idx in range(8) and pred in set(ORDERS)
    est=[float(z["estimated_candidate_tests"]) for z in rec["scores"]]
    checks[f"D{d}_r{rep}_B{budget}_scores_cover_all_orders"]=len(est)==8 and all(v>=0 for v in est)
    chosen=costmap.get(pred,-1);optimal=min(costmap.values()) if costmap else -1
    predictors.setdefault(budget,[]).append({"distractors":d,"replicate":rep,"selected_order":list(pred),"estimated_work":est[idx] if idx<len(est) else None,"selected_exact_candidate_tests":chosen,"optimal_exact_candidate_tests":optimal,"regret_ratio":(chosen/optimal if optimal>0 and chosen>=0 else None),"selected_optimal":chosen==optimal})
   # Plain variants must reproduce exact task and graph outputs for this same cell.
   reference=group[0] if group else None
   for mode in ("plain_source","plain_B8","plain_B32","plain_B128"):
    x=plain.get((d,rep,mode));checks[f"D{d}_r{rep}_{mode}_present"]=x is not None
    if x is None or reference is None: continue
    checks[f"D{d}_r{rep}_{mode}_task_graph_parity"]=x["task_oracle_pass"] and x["task_output"]==reference["task_output"] and x["graph_sha256"]==reference["graph_sha256"] and x["terminal_report"].get("status")=="fixed_point"
    if mode=="plain_source": checks[f"D{d}_r{rep}_source_order_retained"]=tuple(x["installed_order"])==(0,1,2,3)
    else:
     budget=int(mode.removeprefix("plain_B"));selected=x["estimator_predictions"].get(str(budget),x["estimator_predictions"].get(budget))
     checks[f"D{d}_r{rep}_{mode}_executes_prediction"]=selected is not None and tuple(x["installed_order"])==tuple(selected["selected_order"])
     checks[f"D{d}_r{rep}_{mode}_charged_policy_metrics"]=budget in x["estimator_planning_times"] and int(x["order_install_ns"])>=0
     if selected is not None:
      baseline=plain[d,rep,"plain_source"]
      plan_ns=int(x["estimator_planning_times"].get(str(budget),x["estimator_planning_times"].get(budget,{})).get("wall_ns",0))
      combined=plan_ns+int(x["order_install_ns"])+int(x["closure_ns"])
      rows.append({"distractors":d,"replicate":rep,"budget":budget,"selected_order":x["installed_order"],"selected_candidate_tests":costmap.get(tuple(x["installed_order"])),"source_candidate_tests":costmap.get((0,1,2,3)),"planner_wall_ns":plan_ns,"install_ns":int(x["order_install_ns"]),"selected_plain_closure_ns":int(x["closure_ns"]),"selected_combined_ns":combined,"source_plain_closure_ns":int(baseline["closure_ns"]),"combined_to_source_ratio":combined/max(1,int(baseline["closure_ns"]))})
 # Aggregate summaries use the six task/replicate cells; report cells as the unit.
 predictor_summary={}
 for b,vals in predictors.items():
  regrets=[v["regret_ratio"] for v in vals if v["regret_ratio"] is not None]
  predictor_summary[str(b)]={"cells":len(vals),"selected_optimal_cells":sum(v["selected_optimal"] for v in vals),"median_regret_ratio":statistics.median(regrets) if regrets else None,"max_regret_ratio":max(regrets) if regrets else None,"median_estimated_to_selected_exact_ratio":statistics.median(v["estimated_work"]/v["selected_exact_candidate_tests"] for v in vals if v["selected_exact_candidate_tests"]>0 and v["estimated_work"] is not None) if any(v["selected_exact_candidate_tests"]>0 and v["estimated_work"] is not None for v in vals) else None}
 cost_summary=[]
 for b in BUDGETS:
  vals=[r for r in rows if r["budget"]==b]
  cost_summary.append({"budget":b,"cells":len(vals),"median_combined_to_source_ratio":statistics.median(r["combined_to_source_ratio"] for r in vals) if vals else None,"all_cells_combined_below_source":bool(vals) and all(r["combined_to_source_ratio"]<1 for r in vals)})
 result={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"all_checks_pass":all(checks.values()),"exact_order_costs":{f"D{d}_r{rep}":{"/".join(map(str,k)):v for k,v in m.items()} for (d,rep),m in exact_costs.items()},"predictor_summary":predictor_summary,"combined_cost_summary":cost_summary,"plain_policy_rows":rows,"predictor_cells":predictors,"claim_boundary":"One authored four-edge anaphora rule, three controlled context sizes, six graph/replicate cells, eight installer-realized orders, and a bounded sample planner. No natural task prevalence or general optimizer claim."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":result["all_checks_pass"],"checks_passed":result["checks_passed"],"checks_total":result["checks_total"],"predictor_summary":predictor_summary,"combined_cost_summary":cost_summary},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
