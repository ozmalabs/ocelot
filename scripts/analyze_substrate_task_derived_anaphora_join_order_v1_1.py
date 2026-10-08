#!/usr/bin/env python3
"""Independent integrity and candidate-work analysis for anaphora order replay."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_task_derived_anaphora_join_order_v1_1_workers_raw_20260928.json"
LOCK=ROOT/"evaluation/substrate_capability/task_derived_anaphora_join_order_v1_1_lock_20260928.json"
OUT=ROOT/"evaluation/reports/substrate_task_derived_anaphora_join_order_v1_1_analysis_20260928.json"
RULE="rule_anaphoric_it_resolves_to_prior_about_concept"
CLAUSES=(
 ["m","has_mention","mention"],["m","responds_to","m_prev"],
 ["m_prev","has_intent","intent_prev"],["intent_prev","about_concept","c"],
)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())["locked_inputs"];runs=raw["runs"]
 expected={("".join(map(str,p)),r) for p in itertools.permutations(range(4)) for r in range(2)}
 successful=[x for x in runs if "worker" in x];actual={(x["worker"]["permutation"],int(x["worker"]["replicate"])) for x in successful}
 checks={"48_exact_permutation_replicate_cells":len(runs)==48 and len(successful)==48 and actual==expected,
         "unique_fresh_processes":len({x["worker"]["pid"] for x in successful})==48,
         "source_native_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and len(successful)==48 and all(x["before"]==lock==x["after"] for x in successful),
         "all_child_logs_present_and_zero_exit":len(raw["child_logs"])==48 and all((ROOT/x["path"]).is_file() and sha(ROOT/x["path"])==x["sha256"] and x["returncode"]==0 for x in raw["child_logs"])}
 by_order={};rows=[]
 for item in successful:
  w=item["worker"];label=w["permutation"];rep=int(w["replicate"]);installed=w["installed_match"]
  key=f"{label}_r{rep}";checks[key+"_installed_clause_multiset"]=sorted(map(tuple,installed))==sorted(map(tuple,CLAUSES))
  checks[key+"_task_oracle"]=bool(w["task_oracle_pass"]) and w["task_output"]["intent_exists"] and w["task_output"]["it_refers_to"]==["question"] and "question" in w["task_output"]["intent_about_concept"]
  checks[key+"_fixed_point"]=w["terminal_report"].get("status")=="fixed_point" and int(w["terminal_report"].get("budget_overshoot",0))==0
  checks[key+"_rule_metadata"]=any(str(m[2])==RULE and int(m[3])==4 for m in w["rule_metadata"])
  metadata=[m for m in w["rule_metadata"] if str(m[2])==RULE]
  target_id=int(metadata[0][0]) if len(metadata)==1 else -1
  metrics=[(int(i),str(metric),int(value)) for i,metric,value in w["per_rule_counters"] if int(i)==target_id and str(metric)=="candidate_tests"]
  clauses={int(cl):int(n) for i,cl,n in w["clause_counters"] if int(i)==target_id}
  tests=metrics[0][2] if len(metrics)==1 else -1
  checks[key+"_one_target_candidate_counter"]=len(metrics)==1 and target_id>=0
  checks[key+"_clause_candidate_conservation"]=set(clauses)==set(range(4)) and sum(clauses.values())==tests
  order=tuple(x[1] for x in installed);by_order.setdefault(order,[]).append({"permutation":label,"replicate":rep,"candidate_tests":tests,"candidate_tests_by_clause":clauses,"second_closure_progress":w["second_closure_progress"],"elapsed_ns_audit_on":w["second_closure_elapsed_ns_audit_on"],"graph_sha256":w["graph_sha256"]})
  rows.append({"permutation":label,"replicate":rep,"installed_edge_order":list(order),"target_candidate_tests":tests,"candidate_tests_by_clause":clauses,"task_output":w["task_output"],"graph_sha256":w["graph_sha256"]})
 checks["all_permutation_graph_digests_match"]=len(successful)==48 and len({x["worker"]["graph_sha256"] for x in successful})==1
 summary=[]
 for order,values in sorted(by_order.items()):
  counts=[v["candidate_tests"] for v in values]
  summary.append({"installed_edge_order":list(order),"requested_permutation_repeats":len(values),"candidate_tests_by_replicate":counts,"median_candidate_tests":statistics.median(counts),"range_candidate_tests":[min(counts),max(counts)],"median_audit_on_closure_ns":int(statistics.median(v["elapsed_ns_audit_on"] for v in values))})
 result={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"analysis_sha256":sha(Path(__file__).resolve()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"all_checks_pass":all(checks.values()),"requested_permutation_count":24,"realized_installed_order_count":len(by_order),"rows":rows,"summary_by_installed_order":summary,"claim_boundary":"One two-turn anaphora task, minimal declared intent seed profile, one four-edge path rule, all authored clause permutations, native opt-in candidate counters; not a general optimizer or natural-task prevalence estimate."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":result["all_checks_pass"],"checks_passed":result["checks_passed"],"checks_total":result["checks_total"],"installed_orders":len(by_order)},indent=2))
 if not result["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
