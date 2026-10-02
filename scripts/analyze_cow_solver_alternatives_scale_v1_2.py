#!/usr/bin/env python3
"""Independent validation and cost summary for scaled solver alternatives."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/"evaluation/reports/cow_solver_alternatives_scale_v1_2_workers_20261001.json";LOCK=ROOT/"evaluation/substrate_capability/cow_solver_alternatives_scale_v1_2_lock_20261001.json";OUT=ROOT/"evaluation/reports/cow_solver_alternatives_scale_v1_2_analysis_20261001.json"
def median_ms(xs):return statistics.median(xs)/1e6

def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];expected={(n,t,r) for n in (32,128,256) for t in ("path","banded2") for r in range(3)}
 checks={"complete_18_worker_factorial":len(runs)==18 and {(x["n"],x["topology"],x["replicate"]) for x in runs}==expected,"fresh_worker_processes":len({x["pid"] for x in runs})==18,"stable_locked_inputs":raw["locked_inputs"]==lock==raw["post_run_inputs"],"snapshot_identity_revision":all(x["snapshot"]["backend"]=="shared_graph_pages" and x["snapshot"]["source_revision"]==x["revision"] for x in runs),"primary_and_later_fork_isolation":all(x["base_digest"]==x["primary_digest_after"]==x["later_fork_digest"] and x["base_states"]==x["later_fork_states"] for x in runs),"all_workers_four_alternatives":all(len(x["alternatives"])==4 for x in runs)}
 parity=[];fixed=[]
 for w in runs:
  for alt in w["alternatives"]:
   a,b=alt["cow"],alt["eager"]
   parity.append(a["input"]==b["input"]==alt["value"] and a["steps"]==b["steps"] and a["energy"]==b["energy"] and a["frustration"]==b["frustration"] and a["coverage"]==b["coverage"] and a["states"]==b["states"] and a["graph_digest"]==b["graph_digest"])
   fixed.append(a["terminal_progress"]==b["terminal_progress"]==0)
 checks["exact_solver_and_graph_parity_72_branches"]=len(parity)==72 and all(parity);checks["fixed_point_after_settle"]=len(fixed)==72 and all(fixed)
 audits=[a[backend]["scale_audit"] for w in runs for a in w["alternatives"] for backend in ("cow","eager")]
 checks["instrumented_counter_capture_present"]=len(audits)==144 and all("cand_tested" in c and "rule_enumerations" in c for c in audits)
 checks["counter_activity_nonzero"]=all(int(c.get("cand_tested",0))>0 and int(c.get("rule_enumerations",0))>0 for c in audits)
 checks["per_rule_candidate_tests_reconcile"]=all(sum(int(row[2]) for row in branch["per_rule_audit"] if str(row[1])=="candidate_tests")==int(branch["scale_audit"].get("cand_tested",0)) for w in runs for alt in w["alternatives"] for branch in (alt["cow"],alt["eager"]))
 groups=[]
 for n in (32,128,256):
  for topo in ("path","banded2"):
   cells=[w for w in runs if w["n"]==n and w["topology"]==topo]
   cowfork=[a["cow_fork_ns"] for w in cells for a in w["alternatives"]];eagerfork=[a["eager_fork_ns"] for w in cells for a in w["alternatives"]]
   cowsolve=[a["cow"]["instrumented_settle_ns"] for w in cells for a in w["alternatives"]];eagersolve=[a["eager"]["instrumented_settle_ns"] for w in cells for a in w["alternatives"]]
   
   grouped={}
   for backend in ("cow","eager"):
    rows=[a[backend]["scale_audit"] for w in cells for a in w["alternatives"]]
    grouped[backend]={key:{"median":statistics.median(int(c.get(key,0)) for c in rows),"min":min(int(c.get(key,0)) for c in rows),"max":max(int(c.get(key,0)) for c in rows)} for key in ("cand_tested","cand_enum","cand_enum_first","cand_enum_local","cand_enum_scan","cand_enum_repeat","term_evals_total","term_units_total","rule_enumerations","where_evals","scoped_local_rule_matches","scoped_mt_seeded_rule_matches","scoped_full_fallback_rule_matches","scheduler_passes","scheduler_selected_rules","scheduler_dirty_vector_slots","scheduler_external_poll_slots")}
    queue_keys=sorted({k for c in rows for k in c if k.startswith("deferred_queue:")})
    grouped[backend]["deferred_queues"]={key:{"median":statistics.median(int(c.get(key,0)) for c in rows),"max":max(int(c.get(key,0)) for c in rows)} for key in queue_keys}
    per_rule_totals={}
    reconciliation=[]
    for w in cells:
     for alt in w["alternatives"]:
      branch=alt[backend];names={int(meta[0]):str(meta[2]) for meta in branch["rule_metadata"]}
      attributed=sum(int(row[2]) for row in branch["per_rule_audit"] if str(row[1])=="candidate_tests")
      observed=int(branch["scale_audit"].get("cand_tested",0))
      reconciliation.append({"global_cand_tested":observed,"per_rule_candidate_tests":attributed,"equal":observed==attributed})
      for rule_index,metric,count in branch["per_rule_audit"]:
       if str(metric)=="candidate_tests":
        name=names.get(int(rule_index),f"rule_index_{rule_index}");per_rule_totals[name]=per_rule_totals.get(name,0)+int(count)
    grouped[backend]["per_rule_candidate_tests_total"]={k:per_rule_totals[k] for k in sorted(per_rule_totals)}
    grouped[backend]["per_rule_candidate_test_reconciliation"]={"equal_cells":sum(x["equal"] for x in reconciliation),"cells":len(reconciliation),"mismatch_examples":[x for x in reconciliation if not x["equal"]][:3]}
   groups.append({"n":n,"topology":topo,"snapshot_capture_median_ms":median_ms([w["capture_ns"] for w in cells]),"cow_fork_median_ms":median_ms(cowfork),"eager_fork_median_ms":median_ms(eagerfork),"cow_audit_instrumented_settle_median_ms":median_ms(cowsolve),"eager_audit_instrumented_settle_median_ms":median_ms(eagersolve),"work_counters":grouped})
 payload={"protocol":"COW_SOLVER_ALTERNATIVES_SCALE_V1_2","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"alternative_branch_pairs":len(parity),"cost_by_size_topology":groups,"claim_boundary":"Instrumented native work for a reusable CoW solver consumer over 32–256 node path/banded CAN graphs; semantic parity is in the paired v1.1 run, while these counters are collected with per-rule audit enabled. Counter instrumentation is not a timing baseline. One host/three replicates; no global-optimum, natural-task, concurrency, general planning, or broad speed claim.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analysis_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"branch_pairs":len(parity)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
