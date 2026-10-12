#!/usr/bin/env python3
"""Independent semantic, work-conservation, and timing analysis for join skew."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_join_degree_skew_v1_workers_raw_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_join_degree_skew_v1_analysis_20260926.json"
LOCK=ROOT/"evaluation/substrate_capability/join_degree_skew_v1_lock_20260926.json"
FAMILIES=("rule_edits","fb_samples")
ORDERS=("trigger_left_right","trigger_right_left")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_cells():
 return {(m,q,s,o,r) for m in (4,16,64) for q in (0,4,16) for s in (("none",) if q==0 else ("left","balanced","right")) for o in ORDERS for r in range(3)}
def expected_installed_order(m,dl,dr,order):
 if m+dl<m+dr:left,right="left","right"
 elif m+dr<m+dl:left,right="right","left"
 else:left,right=("right","left") if order=="trigger_left_right" else ("left","right")
 return ("trigger","has_game",left,right)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 actual={(x["multiplicity"],x["decoy_ratio"],x["decoy_split"],x["order"],x["replicate"]) for x in runs}
 checks={"126_worker_factorial":len(runs)==126 and actual==expected_cells(),"fresh_pid_per_cell":len({x["pid"] for x in runs})==126,"source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["before"]==lock==x["after"] for x in runs)}
 rows=[];groups={}
 for x in runs:
  m,q,split,order,rep=x["multiplicity"],x["decoy_ratio"],x["decoy_split"],x["order"],x["replicate"];p=x["plain"];a=x["audit"];c=a["counters"];dl,dr=x["left_decoys"],x["right_decoys"];key=(m,q,split,order);pre=f"m{m}_q{q}_{split}_{order}_rep{rep}"
  wi=int(a["writer_rule_index"]);per={str(i):int(n) for i,name,n in a["per_rule"] if int(i)==wi and name=="candidate_tests"};clauses={int(i):{} for i in (wi,)}
  for i,j,n in a["match_clause_candidates"]:
   if int(i)==wi:clauses[wi][int(j)]=int(n)
  checks[pre+"_plain_audit_parity"]=p["graph"]==a["graph"] and p["report"]==a["report"]
  checks[pre+"_closure_outputs"]=a["report"]["status"]=="fixed_point" and a["report"]["budget_overshoot"]==0 and a["seen_edges"]==1 and a["grid_cells"]==4 and a["trigger_edges"]==0
  checks[pre+"_queue_conservation"]=all(c.get(f"deferred_queue:{f}:enqueued_items")==m and c.get(f"deferred_queue:{f}:drained_items")==m and c.get(f"deferred_queue:{f}:drain_batches")==1 for f in FAMILIES)
  checks[pre+"_writer_queue_attribution"]=all({int(i):int(n) for i,name,n in a["per_rule"] if int(i)==wi and name==f"deferred_queue_enqueued:{f}"}=={wi:m} for f in FAMILIES)
  checks[pre+"_candidate_clause_conservation"]=set(per)=={str(wi)} and set(clauses[wi])=={0,1,2,3} and sum(clauses[wi].values())==per.get(str(wi),-1)
  installed=tuple(edge[1] for edge in a["installed_match"])
  checks[pre+"_installed_order_matches_locked_counts"]=installed==expected_installed_order(m,dl,dr,order) and tuple(a["authored_match_order"])==(("trigger","left","right","game") if order=="trigger_left_right" else ("trigger","right","left","game"))
  checks[pre+"_timing_positive"]=all(z>0 for z in (p["closure_cpu_ns"],p["closure_wall_ns"],a["closure_cpu_ns"],a["closure_wall_ns"]))
  checks[pre+"_fixture_counts"]=dl+dr==q*m and (dl==0 and dr==0 if q==0 else ((dl,dr)==(q*m,0) if split=="left" else ((dl,dr)==(q*m//2,q*m//2) if split=="balanced" else (dl,dr)==(0,q*m))))
  by_edge={installed[clause]:count for clause,count in clauses[wi].items()}
  row={"multiplicity":m,"decoy_ratio":q,"decoy_split":split,"left_decoys":dl,"right_decoys":dr,"authored_order":order,"installed_order":list(installed),"replicate":rep,"candidate_tests_per_writer":per.get(str(wi)),"candidate_tests_by_installed_edge":by_edge,"candidate_tests_by_clause":clauses[wi],"queue_items_per_family":{f:c.get(f"deferred_queue:{f}:enqueued_items",0) for f in FAMILIES},"plain_cpu_ns":p["closure_cpu_ns"],"plain_wall_ns":p["closure_wall_ns"],"audit_cpu_ns":a["closure_cpu_ns"],"audit_wall_ns":a["closure_wall_ns"],"scheduler_plan_ns":c.get("scheduler_plan_ns",0)}
  rows.append(row);groups.setdefault(key,[]).append({"graph":a["graph"],"row":row})
 checks["cross_order_semantics_equal"]=all(groups[m,q,s,ORDERS[0]][rep]["graph"]==groups[m,q,s,ORDERS[1]][rep]["graph"] for m,q,s,o,rep in expected_cells() if o==ORDERS[0])
 checks["integer_work_repeats_exactly"]=all(len({json.dumps({k:z["row"][k] for k in ("candidate_tests_per_writer","candidate_tests_by_clause","queue_items_per_family")},sort_keys=True) for z in v})==1 for v in groups.values())
 summary=[]
 for m in (4,16,64):
  for q in (0,4,16):
   for split in (("none",) if q==0 else ("left","balanced","right")):
    for o in ORDERS:
     rs=[x for x in rows if (x["multiplicity"],x["decoy_ratio"],x["decoy_split"],x["authored_order"])==(m,q,split,o)]
     summary.append({"multiplicity":m,"decoy_ratio":q,"split":split,"authored_order":o,"installed_order":rs[0]["installed_order"],"candidate_tests_per_writer":rs[0]["candidate_tests_per_writer"],"candidate_tests_by_installed_edge":rs[0]["candidate_tests_by_installed_edge"],"candidate_tests_by_clause":rs[0]["candidate_tests_by_clause"],"plain_cpu_ns_median":int(statistics.median(x["plain_cpu_ns"] for x in rs)),"plain_wall_ns_median":int(statistics.median(x["plain_wall_ns"] for x in rs)),"audit_cpu_ns_median":int(statistics.median(x["audit_cpu_ns"] for x in rs)),"audit_wall_ns_median":int(statistics.median(x["audit_wall_ns"] for x in rs)),"scheduler_plan_ns_median":int(statistics.median(x["scheduler_plan_ns"] for x in rs))})
 payload={"schema_version":1,"raw_sha256":sha(RAW),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"all_checks_pass":all(checks.values()),"checks_passed":sum(checks.values()),"checks_total":len(checks),"rows":rows,"summary_by_multiplicity_split_order":summary,"claim_boundary":"Candidate tests by clause, queue work, plain/audit parity, and closure-call CPU/wall time for one synthetic isolated two-edge join schema at M=4/16/64 and one-sided decoy ratios 0/4/16. No natural-task prevalence, memory, general complexity, or universal runtime claim."}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
