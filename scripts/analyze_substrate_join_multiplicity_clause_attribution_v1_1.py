#!/usr/bin/env python3
"""Independent per-clause conservation and order-effect analysis."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/join_multiplicity_clause_attribution_v1_1_lock_20260926.json"
FAMILIES=("rule_edits","fb_samples")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(r,m,o,rep) for r in (1,8) for m in (1,4,16,32,64) for o in ("trigger_left_right","trigger_right_left") for rep in range(3)}
 checks={"60_worker_factorial":len(runs)==60 and {(x["rules"],x["multiplicity"],x["order"],x["replicate"]) for x in runs}==expected,"fresh_pid_per_cell":len({x["pid"] for x in runs})==60,"source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["before"]==lock==x["after"] for x in runs)}
 rows=[];by_key={}
 for x in runs:
  r,m,o,rep=x["rules"],x["multiplicity"],x["order"],x["replicate"];p=x["plain"];a=x["audit"];c=a["counters"];pre=f"r{r}_m{m}_{o}_rep{rep}";items=r*m
  checks[pre+"_plain_audit_semantic_parity"]=p["graph"]==a["graph"] and p["report"]==a["report"]
  checks[pre+"_closure_outputs"]=a["report"]["status"]=="fixed_point" and a["report"]["budget_overshoot"]==0 and a["seen_edges"]==r and a["grid_cells"]==4*r and a["trigger_edges"]==0
  checks[pre+"_queue_work_exact"]=all(c.get(f"deferred_queue:{f}:enqueued_items")==items and c.get(f"deferred_queue:{f}:drained_items")==items and c.get(f"deferred_queue:{f}:drain_batches")==1 for f in FAMILIES)
  writer_ids={int(w["rule_index"]) for w in a["writers"]}
  for f in FAMILIES:
   metric=f"deferred_queue_enqueued:{f}";producer={int(i):int(n) for i,name,n in a["per_rule"] if name==metric and int(i) in writer_ids}
   checks[pre+f"_{f}_per_writer_multiplicity"]=producer=={i:m for i in writer_ids}
  per={int(i):int(n) for i,name,n in a["per_rule"] if name=="candidate_tests" and int(i) in writer_ids}
  clauses={int(i):{} for i in writer_ids}
  for i,clause,n in a["match_clause_candidates"]:
   if int(i) in writer_ids:clauses[int(i)][int(clause)]=int(n)
  checks[pre+"_clause_counts_conserve_per_writer_candidates"]=all(sum(clauses[i].values())==per.get(i,0) for i in writer_ids) and set(per)==writer_ids
  checks[pre+"_candidate_clause_positions_present"]=all(set(clauses[i])=={0,1,2,3} for i in writer_ids)
  expected_installed=("trigger_0","has_game_0","right_0","left_0") if o=="trigger_left_right" else ("trigger_0","has_game_0","left_0","right_0")
  installed=tuple(edge[1] for edge in a["installed_match"])
  checks[pre+"_installed_order_readback"]=installed==expected_installed and tuple(a["authored_match_order"])==(("trigger","left","right","game") if o=="trigger_left_right" else ("trigger","right","left","game"))
  checks[pre+"_trigger_deletion_work_exact"]=c.get("rule_effect_edge_deletes")==r
  record={"rules":r,"multiplicity":m,"order":o,"replicate":rep,"candidate_tests_by_clause_per_writer":{str(j):sorted({json.dumps(clauses[i],sort_keys=True) for i in writer_ids}) for j in range(r)},"candidate_tests_total":c.get("cand_tested",0),"queue_items_expected":items,"queue_items_observed":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES},"scheduler_plan_ns":c.get("scheduler_plan_ns",0)}
  rows.append(record);by_key.setdefault((r,m,o),[]).append({"graph":a["graph"],"clauses":clauses,"installed_match":installed,"candidate_total":c.get("cand_tested",0),"queues":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES}})
 checks["cross_order_final_graph_equal"]=all(by_key[r,m,"trigger_left_right"][rep]["graph"]==by_key[r,m,"trigger_right_left"][rep]["graph"] for r in (1,8) for m in (1,4,16,32,64) for rep in range(3))
 checks["integer_work_repeats_within_cell_order"]=all(len({json.dumps({"clauses":z["clauses"],"candidate_total":z["candidate_total"],"queues":z["queues"]},sort_keys=True) for z in v})==1 for v in by_key.values())
 summary=[]
 for r in (1,8):
  for m in (1,4,16,32,64):
   entry={"rules":r,"multiplicity":m}
   for o in ("trigger_left_right","trigger_right_left"):
    z=by_key[r,m,o][0];by_edge={}
    for writer,counts in z["clauses"].items():
     for clause,count in counts.items():by_edge[z["installed_match"][clause]]=by_edge.get(z["installed_match"][clause],0)+count
    entry[o]={"authored_match_order":list(("trigger","left","right","game") if o=="trigger_left_right" else ("trigger","right","left","game")),"installed_match_order":list(z["installed_match"]),"candidate_tests_per_writer_by_clause":{str(clause):sum(vals.get(clause,0) for vals in z["clauses"].values())//r for clause in range(4)},"candidate_tests_per_writer_by_installed_edge":{name:count//r for name,count in by_edge.items()},"candidate_tests_per_writer":z["candidate_total"]//r,"queue_items_per_writer_each_family":m}
   summary.append(entry)
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"summary_by_size_order":summary,"claim_boundary":"Per-match-edge candidate tests, queue work and final-state parity for one regular two-edge join family at multiplicity 1–64, two rule counts and two literal orders. No total closure-time, memory, natural workload, or general complexity claim."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
