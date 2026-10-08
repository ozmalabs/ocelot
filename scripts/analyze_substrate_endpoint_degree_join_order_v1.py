#!/usr/bin/env python3
"""Independent analysis of endpoint-degree join-order oracle capture."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_endpoint_degree_join_order_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_endpoint_degree_join_order_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/endpoint_degree_join_order_v1_lock_20260926.json"
FAMILIES=("rule_edits","fb_samples")
POLICIES=("count_control","endpoint_degree")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_cells():return {(m,q,p,r) for m in (4,16,64) for q in (0,4,16) for p in POLICIES for r in range(3)}
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];actual={(x["multiplicity"],x["decoy_ratio"],x["policy"],x["replicate"]) for x in runs}
 checks={"54_worker_factorial":len(runs)==54 and actual==expected_cells(),"fresh_pid_per_cell":len({x["pid"] for x in runs})==54,"source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["before"]==lock==x["after"] for x in runs)}
 rows=[];groups={}
 for x in runs:
  m,q,pname,rep=x["multiplicity"],x["decoy_ratio"],x["policy"],x["replicate"];p=x["plain"];a=x["audit"];c=a["counters"];pre=f"m{m}_q{q}_{pname}_rep{rep}";wi=int(a["writer_rule_index"]);per={int(i):int(n) for i,name,n in a["per_rule"] if int(i)==wi and name=="candidate_tests"};clauses={int(i):{} for i in (wi,)}
  for i,j,n in a["match_clause_candidates"]:
   if int(i)==wi:clauses[wi][int(j)]=int(n)
  installed=tuple(e[1] for e in a["installed_match"]);expected_order=("trigger","has_game","right","left") if pname=="count_control" else ("trigger","has_game","left","right")
  checks[pre+"_plain_audit_semantic_parity"]=p["graph"]==a["graph"] and p["report"]==a["report"]
  checks[pre+"_fixed_point_outputs"]=a["report"]["status"]=="fixed_point" and a["report"]["budget_overshoot"]==0 and a["seen_edges"]==1 and a["grid_cells"]==4 and a["trigger_edges"]==0
  checks[pre+"_queue_conservation"]=all(c.get(f"deferred_queue:{f}:enqueued_items")==m and c.get(f"deferred_queue:{f}:drained_items")==m and c.get(f"deferred_queue:{f}:drain_batches")==1 for f in FAMILIES)
  checks[pre+"_writer_queue_attribution"]=all({int(i):int(n) for i,name,n in a["per_rule"] if int(i)==wi and name==f"deferred_queue_enqueued:{f}"}=={wi:m} for f in FAMILIES)
  checks[pre+"_installed_order_readback"]=installed==expected_order and tuple(p["installed_match"][i][1] for i in range(4))==installed and tuple(p["authored_order"])==tuple(a["authored_order"])
  checks[pre+"_writer_clause_conservation"]=set(per)=={wi} and set(clauses[wi])=={0,1,2,3} and sum(clauses[wi].values())==per.get(wi,-1)
  checks[pre+"_positive_timers"]=all(v>0 for v in (p["install_ns"],p["closure_cpu_ns"],p["closure_wall_ns"],a["install_ns"],a["closure_cpu_ns"],a["closure_wall_ns"])) and (pname=="count_control" or (p["estimate"]["planning_wall_ns"]>0 and p["estimate"]["planning_cpu_ns"]>0))
  if pname=="endpoint_degree":
   est=p["estimate"];actual_tests=per.get(wi,-1)
   checks[pre+"_oracle_selects_lower_candidate_cost"]=est["selected"]=="left_then_right" and est["left_then_right"]<est["right_then_left"]
   checks[pre+"_oracle_predicts_measured_treatment"]=actual_tests==est["left_then_right"]+2 and sum(clauses[wi].values())==actual_tests
  else:
   checks[pre+"_count_control_uses_existing_tie_order"]=p["estimate"]["selected"]=="control_authored_order" and installed==("trigger","has_game","right","left")
  edge_counts={}
  for clause,n in clauses[wi].items():edge_counts[installed[clause]]=n
  row={"multiplicity":m,"decoy_ratio":q,"policy":pname,"replicate":rep,"installed_order":list(installed),"candidate_tests_writer":per.get(wi),"candidate_tests_by_installed_edge":edge_counts,"planner_estimate":p["estimate"],"rule_install_ns":p["install_ns"],"plain_closure_cpu_ns":p["closure_cpu_ns"],"plain_closure_wall_ns":p["closure_wall_ns"],"policy_total_wall_ns":p["estimate"]["planning_wall_ns"]+p["install_ns"]+p["closure_wall_ns"],"queue_items_per_family":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES},"scheduler_plan_ns":c.get("scheduler_plan_ns",0)}
  rows.append(row);groups.setdefault((m,q,pname),[]).append({"graph":a["graph"],"row":row})
 checks["policy_control_final_graph_parity"]=all(groups[m,q,"count_control"][r]["graph"]==groups[m,q,"endpoint_degree"][r]["graph"] for m in (4,16,64) for q in (0,4,16) for r in range(3))
 for m in (4,16,64):
  for q in (0,4,16):
   for r in range(3):
    ctl=groups[m,q,"count_control"][r]["row"];opt=groups[m,q,"endpoint_degree"][r]["row"];est=opt["planner_estimate"]
    checks[f"m{m}_q{q}_rep{r}_count_control_matches_oracle_bad_order"]=ctl["candidate_tests_writer"]==est["right_then_left"]+2
 checks["integer_work_repeats_exactly"]=all(len({json.dumps({k:z["row"][k] for k in ("candidate_tests_writer","candidate_tests_by_installed_edge","queue_items_per_family","installed_order")},sort_keys=True) for z in v})==1 for v in groups.values())
 summary=[]
 for m in (4,16,64):
  for q in (0,4,16):
   ent={"multiplicity":m,"decoy_ratio":q}
   for pname in POLICIES:
    rs=[z["row"] for z in groups[m,q,pname]]
    ent[pname]={"installed_order":rs[0]["installed_order"],"candidate_tests_writer":rs[0]["candidate_tests_writer"],"candidate_tests_by_installed_edge":rs[0]["candidate_tests_by_installed_edge"],"planning_cpu_ns_median":int(statistics.median(z["planner_estimate"]["planning_cpu_ns"] for z in rs)),"planning_wall_ns_median":int(statistics.median(z["planner_estimate"]["planning_wall_ns"] for z in rs)),"rule_install_ns_median":int(statistics.median(z["rule_install_ns"] for z in rs)),"plain_closure_wall_ns_median":int(statistics.median(z["plain_closure_wall_ns"] for z in rs)),"policy_total_wall_ns_median":int(statistics.median(z["policy_total_wall_ns"] for z in rs))}
   summary.append(ent)
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"summary_by_multiplicity_ratio":summary,"claim_boundary":"Exact endpoint-degree candidate-cost oracle for one authored two-edge chain at M=4/16/64 and balanced decoy ratios 0/4/16. Planning/install/closure time are separately measured; no general optimizer, arbitrary join, natural-task, or memory claim."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
