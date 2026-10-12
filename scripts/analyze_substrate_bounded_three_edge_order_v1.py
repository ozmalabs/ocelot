#!/usr/bin/env python3
"""Audit sampled three-edge cost estimates against exact native work."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_bounded_three_edge_order_v1_workers_raw_20260927.json"
OUT=ROOT/"evaluation/reports/substrate_bounded_three_edge_order_v1_analysis_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/bounded_three_edge_order_v1_lock_20260927.json"
FAMILIES=("rule_edits","fb_samples")
ORDERS=("LMR","RML","LRM","RLM")
ORDER_EDGES={"LMR":("left","middle","right"),"RML":("right","middle","left"),"LRM":("left","right","middle"),"RLM":("right","left","middle")}
EXACT_MODES=tuple("exact_"+o for o in ORDERS if o!="RML")
SAMPLE_MODES={8:"sample_B8",32:"sample_B32",128:"sample_B128"}
ALL_MODES=("control_RML",)+EXACT_MODES+tuple(SAMPLE_MODES.values())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_cells():return {(m,q,mode,rep) for m in (16,64) for q in (0,4,16) for mode in ALL_MODES for rep in range(3)}
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];actual={(x["multiplicity"],x["decoy_ratio"],x["mode"],x["replicate"]) for x in runs}
 checks={"126_worker_factorial":len(runs)==126 and actual==expected_cells(),"fresh_pid_per_cell":len({x["pid"] for x in runs})==126,"source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["before"]==lock==x["after"] for x in runs)}
 rows=[];groups={}
 for x in runs:
  m,q,mode,rep=x["multiplicity"],x["decoy_ratio"],x["mode"],x["replicate"];p=x["plain"];a=x["audit"];c=a["counters"];wi=int(a["writer_rule_index"]);pre=f"m{m}_q{q}_{mode}_rep{rep}"
  per={int(i):int(n) for i,name,n in a["per_rule"] if int(i)==wi and name=="candidate_tests"};clauses={int(i):{} for i in (wi,)}
  for i,j,n in a["clause_candidates"]:
   if int(i)==wi:clauses[wi][int(j)]=int(n)
  installed=tuple(a["installed_order"]);path_order=tuple(z for z in installed if z in {"left","middle","right"});expected_path=ORDER_EDGES[mode.removeprefix("exact_")] if mode.startswith("exact_") else (ORDER_EDGES["RML"] if mode=="control_RML" else None)
  if mode.startswith("sample_B"):expected_path=ORDER_EDGES[a["selected_order"]]
  checks[pre+"_plain_audit_state_parity"]=p["graph"]==a["graph"] and p["report"]==a["report"]
  checks[pre+"_closure_semantics"]=a["report"]["status"]=="fixed_point" and a["report"]["budget_overshoot"]==0 and a["seen_edges"]==1 and a["grid_cells"]==4 and a["trigger_edges"]==0
  checks[pre+"_queue_conservation"]=all(c.get(f"deferred_queue:{f}:enqueued_items")==m and c.get(f"deferred_queue:{f}:drained_items")==m and c.get(f"deferred_queue:{f}:drain_batches")==1 for f in FAMILIES)
  checks[pre+"_queue_producer_attribution"]=all({int(i):int(n) for i,name,n in a["per_rule"] if int(i)==wi and name==f"deferred_queue_enqueued:{f}"}=={wi:m} for f in FAMILIES)
  checks[pre+"_installed_order_readback"]=installed==("trigger","has_game",*expected_path) and path_order==tuple(expected_path)
  checks[pre+"_writer_candidate_conservation"]=set(per)=={wi} and set(clauses[wi])==set(range(5)) and sum(clauses[wi].values())==per.get(wi,-1)
  checks[pre+"_positive_timers_and_memory"]=all(v>0 for v in (p["writer_install_ns"],p["closure_cpu_ns"],p["closure_wall_ns"],p["peak_rss_kib_plain"],a["writer_install_ns"],a["closure_cpu_ns"],a["closure_wall_ns"],a["peak_rss_kib_plain"])) and (not mode.startswith("sample_B") or (p["planning_wall_ns"]>0 and p["planning_cpu_ns"]>0 and p["planner_python_peak_bytes"]>0 and p["planner_memory_probe_wall_ns"]>0))
  if mode.startswith("sample_B"):
   checks[pre+"_sample_budget_respected"]=all(z["sampled_candidate_probes"]<=int(mode.split("B")[1])*3 for z in p["planner"]["scores"].values())
   checks[pre+"_sample_scores_deterministic_plain_audit"]=all(p["planner"]["scores"][o]["estimated_path_candidate_tests"]==a["planner"]["scores"][o]["estimated_path_candidate_tests"] and p["planner"]["scores"][o]["selected"]==a["planner"]["scores"][o]["selected"] for o in ORDERS)
  total=per.get(wi,0);by_edge={installed[j]:n for j,n in clauses[wi].items()}
  row={"multiplicity":m,"decoy_ratio":q,"mode":mode,"replicate":rep,"installed_order":list(installed),"candidate_tests_writer":total,"candidate_tests_by_installed_edge":by_edge,"planner":p["planner"],"planning_cpu_ns":p["planning_cpu_ns"],"planning_wall_ns":p["planning_wall_ns"],"planner_python_peak_bytes":p["planner_python_peak_bytes"],"writer_install_ns":p["writer_install_ns"],"plain_closure_cpu_ns":p["closure_cpu_ns"],"plain_closure_wall_ns":p["closure_wall_ns"],"combined_policy_wall_ns":p["planning_wall_ns"]+p["writer_install_ns"]+p["closure_wall_ns"],"peak_rss_kib_plain":p["peak_rss_kib_plain"],"queue_items_per_family":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES}}
  rows.append(row);groups.setdefault((m,q,mode,rep),[]).append({"graph":a["graph"],"row":row})
 checks["all_modes_same_terminal_graph"]=all(len({json.dumps(groups[m,q,mode,rep][0]["graph"],sort_keys=True) for mode in ALL_MODES})==1 for m in (16,64) for q in (0,4,16) for rep in range(3))
 exact={}
 for m in (16,64):
  for q in (0,4,16):
   for rep in range(3):
    exact[m,q,rep]={o:(groups[m,q,"control_RML",rep][0]["row"]["candidate_tests_writer"]-2 if o=="RML" else groups[m,q,"exact_"+o,rep][0]["row"]["candidate_tests_writer"]-2) for o in ORDERS}
    control=groups[m,q,"control_RML",rep][0]["row"]["candidate_tests_writer"]-2
    checks[f"m{m}_q{q}_rep{rep}_control_is_RML_exact"]=control==exact[m,q,rep]["RML"]
    for budget,smode in SAMPLE_MODES.items():
     srow=groups[m,q,smode,rep][0]["row"];plan=srow["planner"];pred={o:plan["scores"][o]["estimated_path_candidate_tests"] for o in ORDERS};selected=plan["selected"]
     checks[f"m{m}_q{q}_rep{rep}_B{budget}_selection_readback"]=tuple(srow["installed_order"][2:])==ORDER_EDGES[selected]
     checks[f"m{m}_q{q}_rep{rep}_B{budget}_selection_regret_defined"]=selected in ORDERS and exact[m,q,rep][selected]>=min(exact[m,q,rep].values())
 summary=[];sample_metrics={str(b):{"n":0,"selected_optimal":0,"regret_sum":0.0,"relative_error_sum":0.0,"planner_wall_ns":[],"planner_cpu_ns":[],"python_peak_bytes":[],"rss_kib":[]} for b in SAMPLE_MODES}
 for m in (16,64):
  for q in (0,4,16):
   ent={"multiplicity":m,"decoy_ratio":q,"exact_native_candidate_tests_by_order":{}}
   for o in ORDERS:
    vals=[exact[m,q,r][o] for r in range(3)];ent["exact_native_candidate_tests_by_order"][o]=int(statistics.median(vals))
   for budget,smode in SAMPLE_MODES.items():
    srows=[groups[m,q,smode,r][0]["row"] for r in range(3)];sc=sample_metrics[str(budget)]
    for r,sr in enumerate(srows):
     er=exact[m,q,r];pred={o:sr["planner"]["scores"][o]["estimated_path_candidate_tests"] for o in ORDERS};best=min(er,key=er.get);chosen=sr["planner"]["selected"]
     sc["n"]+=1;sc["selected_optimal"]+=int(er[chosen]==er[best]);sc["regret_sum"]+=er[chosen]/max(1,er[best]);sc["relative_error_sum"]+=sum(abs(pred[o]-er[o])/max(1,er[o]) for o in ORDERS)/len(ORDERS);sc["planner_wall_ns"].append(sr["planning_wall_ns"]);sc["planner_cpu_ns"].append(sr["planning_cpu_ns"]);sc["python_peak_bytes"].append(sr["planner_python_peak_bytes"]);sc["rss_kib"].append(sr["peak_rss_kib_plain"])
    ent[f"B{budget}"]={"selected_orders":[z["planner"]["selected"] for z in srows],"writer_candidate_tests":[z["candidate_tests_writer"] for z in srows],"combined_wall_ns_median":int(statistics.median(z["combined_policy_wall_ns"] for z in srows)),"planner_wall_ns_median":int(statistics.median(z["planning_wall_ns"] for z in srows)),"python_peak_bytes_median":int(statistics.median(z["planner_python_peak_bytes"] for z in srows))}
   summary.append(ent)
 for b,z in sample_metrics.items():
  n=max(1,z["n"]);z.update({"selection_accuracy":z["selected_optimal"]/n,"mean_candidate_work_regret":z["regret_sum"]/n,"mean_relative_prediction_error":z["relative_error_sum"]/n,"median_planner_wall_ns":int(statistics.median(z["planner_wall_ns"])),"median_planner_cpu_ns":int(statistics.median(z["planner_cpu_ns"])),"median_python_peak_bytes":int(statistics.median(z["python_peak_bytes"])),"median_process_peak_rss_kib":int(statistics.median(z["rss_kib"]))});del z["planner_wall_ns"];del z["planner_cpu_ns"];del z["python_peak_bytes"];del z["rss_kib"]
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"summary_by_setting":summary,"sample_quality_by_budget":sample_metrics,"claim_boundary":"Capped sample predictions, order selection, native candidate work and memory/time for one synthetic three-edge chain, four installed orders and B=8/32/128. No arbitrary-query, natural-task or general tractability claim."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
