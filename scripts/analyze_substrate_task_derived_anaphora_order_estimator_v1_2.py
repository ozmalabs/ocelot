#!/usr/bin/env python3
"""Independent integrity, order-ranking, parity, and cost analysis."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/anaphora_order_estimator_v1_2_raw_20260929.json"
LOCK=ROOT/"evaluation/substrate_capability/anaphora_order_estimator_v1_2_lock_20260929.json"
OUT=ROOT/"evaluation/reports/anaphora_order_estimator_v1_2_analysis_20260929.json"
ORDERS=tuple(itertools.permutations(range(4)));BUDGETS=(8,32,128)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 expected={(d,f"exact_{i}",rep) for d in (0,2,4) for i in range(24) for rep in range(2)}|{(d,"exact_source",rep) for d in (0,2,4) for rep in range(2)}|{(d,m,rep) for d in (0,2,4) for m in ("plain_source","plain_B8","plain_B32","plain_B128") for rep in range(2)}
 successful=[x for x in runs if "worker_error" not in x]
 actual={(int(x["distractors"]),x["mode"],int(x["replicate"])) for x in successful}
 checks={"174_exact_cells":len(runs)==174 and len(successful)==174 and actual==expected,
 "174_unique_worker_processes":len({x["pid"] for x in successful})==174,
 "source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x.get("before")==lock==x.get("after") for x in successful),
 "all_child_logs_present_and_hash_valid":len(raw["child_logs"])==174 and all((ROOT/x["path"]).is_file() and sha(ROOT/x["path"])==x["sha256"] and x["returncode"]==0 for x in raw["child_logs"])}
 indexed={(int(x["distractors"]),int(x["replicate"]),x["mode"]):x for x in successful}
 predictor_cells={b:[] for b in BUDGETS};policy_rows=[];order_maps={}
 for d in (0,2,4):
  for rep in range(2):
   group=[indexed.get((d,rep,"exact_source"))]+[indexed.get((d,rep,f"exact_{i}")) for i in range(24)]
   group=[x for x in group if x is not None]
   checks[f"D{d}_r{rep}_source_plus_all_24_requests"]=len(group)==25 and len({tuple(x["requested_order"]) for x in group[1:]})==24 and {tuple(x["requested_order"]) for x in group[1:]}==set(ORDERS)
   checks[f"D{d}_r{rep}_all_order_clauses_valid"]=len(group)==25 and all(len(x["installed_order"])==4 and set(x["installed_order"])==set(range(4)) for x in group)
   checks[f"D{d}_r{rep}_task_oracle_and_fixed_point"]=len(group)==25 and all(x["task_oracle_pass"] and x["terminal_report"].get("status")=="fixed_point" and int(x["terminal_report"].get("budget_overshoot",0))==0 for x in group)
   checks[f"D{d}_r{rep}_whole_graph_parity"]=len({x["graph_sha256"] for x in group})==1
   source=group[0] if group else None
   checks[f"D{d}_r{rep}_untouched_source_order"]=source is not None and tuple(source["installed_order"])==tuple(source["source_order"]) and tuple(source["source_order"])==(0,1,2,3)
   by_request={tuple(x["requested_order"]):x for x in group[1:]}
   order_maps[f"D{d}_r{rep}"]={"requested_to_installed":{"".join(map(str,k)):v["installed_order"] for k,v in by_request.items()}}
   cost_by_installed={}
   for x in group:
    if not x["audit_enabled"]: continue
    rid=int(x["target_rule_id"]);vals=[int(v) for i,k,v in x["per_rule_counters"] if int(i)==rid and str(k)=="candidate_tests"]
    clauses={int(ci):int(n) for i,ci,n in x["clause_counters"] if int(i)==rid}
    checks[f"D{d}_r{rep}_{x['mode']}_target_candidate_counter"]=len(vals)==1 and rid>=0 and int(x["target_candidate_tests"])==vals[0]
    checks[f"D{d}_r{rep}_{x['mode']}_clause_counter_conservation"]=len(clauses)==4 and set(clauses)==set(range(4)) and len(vals)==1 and sum(clauses.values())==vals[0]
    cost_by_installed[tuple(x["installed_order"])]=vals[0] if len(vals)==1 else -1
   checks[f"D{d}_r{rep}_source_counter_exists"]=source is not None and (0,1,2,3) in cost_by_installed
   for b in BUDGETS:
    pred_rows=[x.get("estimator_predictions",{}).get(str(b),x.get("estimator_predictions",{}).get(b)) for x in group]
    encoded=[json.dumps(z,sort_keys=True) for z in pred_rows]
    checks[f"D{d}_r{rep}_B{b}_same_snapshot_predictions"]=len(pred_rows)==25 and len(set(encoded))==1 and pred_rows[0] is not None
    pred=pred_rows[0] if pred_rows else None
    if pred is None: continue
    checks[f"D{d}_r{rep}_B{b}_scores_all_24_requests"]=len(pred["scores"])==24 and {tuple(s["order"]) for s in pred["scores"]}==set(ORDERS)
    idx=int(pred["selected_order_index"]);requested=tuple(pred["selected_order"])
    checks[f"D{d}_r{rep}_B{b}_selected_request_consistent"]=idx in range(24) and requested==ORDERS[idx]
    selected_exact=by_request.get(requested);selected_installed=tuple(selected_exact["installed_order"]) if selected_exact else None
    selected_cost=cost_by_installed.get(selected_installed,-1) if selected_installed is not None else -1
    optimum=min((v for v in cost_by_installed.values() if v>=0),default=-1)
    predictor_cells[b].append({"distractors":d,"replicate":rep,"selected_request":list(requested),"selected_installed_order":list(selected_installed) if selected_installed is not None else None,"selected_exact_candidate_tests":selected_cost,"optimal_realized_candidate_tests":optimum,"regret_ratio":selected_cost/optimum if selected_cost>=0 and optimum>0 else None,"selected_optimal":selected_cost==optimum})
    plain=indexed.get((d,rep,f"plain_B{b}"));base=indexed.get((d,rep,"plain_source"))
    checks[f"D{d}_r{rep}_plain_B{b}_exists"]=plain is not None
    if plain and source:
     checks[f"D{d}_r{rep}_plain_B{b}_semantic_graph_parity"]=plain["task_oracle_pass"] and plain["task_output"]==source["task_output"] and plain["graph_sha256"]==source["graph_sha256"] and plain["terminal_report"].get("status")=="fixed_point"
     checks[f"D{d}_r{rep}_plain_B{b}_executes_selected_request"]=tuple(plain["requested_order"])==requested and selected_exact is not None and tuple(plain["installed_order"])==selected_installed
     checks[f"D{d}_r{rep}_plain_B{b}_planning_install_charged"]=b in plain["estimator_planning_times"] and int(plain["order_install_ns"])>=0 and int(plain["estimator_python_peak_bytes"])>=0
     if base:
      plan_ns=int(plain["estimator_planning_times"].get(str(b),plain["estimator_planning_times"].get(b,{})).get("wall_ns",0));combined=plan_ns+int(plain["order_install_ns"])+int(plain["closure_ns"])
      policy_rows.append({"distractors":d,"replicate":rep,"budget":b,"requested_order":list(requested),"installed_order":plain["installed_order"],"selected_exact_candidate_tests":selected_cost,"source_exact_candidate_tests":cost_by_installed.get(tuple(source["installed_order"])),"planner_wall_ns":plan_ns,"install_ns":int(plain["order_install_ns"]),"plain_closure_ns":int(plain["closure_ns"]),"combined_ns":combined,"source_plain_closure_ns":int(base["closure_ns"]),"combined_to_source_ratio":combined/max(1,int(base["closure_ns"]))})
   # The source arm is an independent plain baseline and must match its audit twin.
   base=indexed.get((d,rep,"plain_source"))
   if base and source:
    checks[f"D{d}_r{rep}_plain_source_semantic_graph_parity"]=base["task_oracle_pass"] and base["task_output"]==source["task_output"] and base["graph_sha256"]==source["graph_sha256"] and tuple(base["installed_order"])==tuple(source["installed_order"])
 summaries={}
 for b,vals in predictor_cells.items():
  regrets=[x["regret_ratio"] for x in vals if x["regret_ratio"] is not None]
  summaries[str(b)]={"cells":len(vals),"optimal_selections":sum(x["selected_optimal"] for x in vals),"median_regret_ratio":statistics.median(regrets) if regrets else None,"maximum_regret_ratio":max(regrets) if regrets else None}
 cost_summary=[]
 for b in BUDGETS:
  rows=[x for x in policy_rows if x["budget"]==b]
  cost_summary.append({"budget":b,"cells":len(rows),"median_combined_to_source_ratio":statistics.median(x["combined_to_source_ratio"] for x in rows) if rows else None,"combined_below_source_cells":sum(x["combined_to_source_ratio"]<1 for x in rows)})
 result={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"all_checks_pass":all(checks.values()),"order_maps":order_maps,"predictor_summary":summaries,"predictor_cells":predictor_cells,"combined_cost_summary":cost_summary,"plain_policy_rows":policy_rows,"claim_boundary":"One authored four-edge anaphora rule, three controlled conversation context sizes, six task/replicate cells, 24 requested clause orders, and one bounded sample planner. No natural task prevalence or general optimizer claim."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":result["all_checks_pass"],"checks_passed":result["checks_passed"],"checks_total":result["checks_total"],"predictor_summary":summaries,"combined_cost_summary":cost_summary},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
