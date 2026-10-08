#!/usr/bin/env python3
"""Validate coactivation population × production Hebbian join-order work."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/can_coactivation_population_join_order_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/can_coactivation_population_join_order_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/can_coactivation_population_join_order_v1_analysis_20261001.json"
TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(n,q,r) for n in (32,64,128) for q in (0,n,4*n,n*(n-1)//4,n*(n-1)) for r in range(3)}
 checks={"complete_45_cell_panel":len(runs)==45 and {(x["n"],x["q"],x["replicate"]) for x in runs}==expected,"45_fresh_processes":len({x["pid"] for x in runs})==45,"stable_locked_inputs":raw["locked_inputs"]==lock==raw["post_run_inputs"],"exactly_target_rules_active":all(x[arm]["active_rules"]==list(TARGETS) for x in runs for arm in ("base","sparse_first")),"installed_orders_verified":all(all(x[arm]["installed_match_order"][t][0]==("coactivated_with" if arm=="sparse_first" else "has_concept") for t in TARGETS) for x in runs for arm in ("base","sparse_first")),"read_only_fixed_point":all(x[arm]["progress"]==0 and x[arm]["terminal_progress"]==0 and x[arm]["before_digest"]==x[arm]["after_digest"] for x in runs for arm in ("base","sparse_first")),"baseline_sparse_exact_graph_parity":all(x["base"]["before_digest"]==x["sparse_first"]["before_digest"]==x["base"]["after_digest"]==x["sparse_first"]["after_digest"] for x in runs)}
 reconciliation=[]
 for x in runs:
  for arm in ("base","sparse_first"):
   v=x[arm];summed=sum(v["target_work"][name]["candidate_tests"] for name in TARGETS);global_count=int(v["global"].get("cand_tested",0));reconciliation.append(global_count==summed)
 checks["per_rule_candidates_reconcile_global_all_90_arms"]=len(reconciliation)==90 and all(reconciliation)
 groups=[]
 for n in (32,64,128):
  for q in (0,n,4*n,n*(n-1)//4,n*(n-1)):
   cells=[x for x in runs if x["n"]==n and x["q"]==q]
   row={"n":n,"q":q,"q_over_n":q/n,"replicates":len(cells)}
   for arm,label in (("base","baseline"),("sparse_first","sparse_first")):
    all_total=[int(x[arm]["global"].get("cand_tested",0)) for x in cells]
    row[label]={"median_cand_tested":statistics.median(all_total),"median_rule_enumerations":statistics.median(int(x[arm]["global"].get("rule_enumerations",0)) for x in cells),"per_rule_candidate_tests":{t:statistics.median(int(x[arm]["target_work"][t]["candidate_tests"]) for x in cells) for t in TARGETS},"median_term_evals":statistics.median(int(x[arm]["global"].get("term_evals_total",0)) for x in cells)}
   row["sparse_first_reduction_pct"]=None if row["baseline"]["median_cand_tested"]==0 else 100*(1-row["sparse_first"]["median_cand_tested"]/row["baseline"]["median_cand_tested"])
   groups.append(row)
 payload={"protocol":"CAN_COACTIVATION_POPULATION_JOIN_ORDER_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"per_order_cells":len(reconciliation),"groups":groups,"claim_boundary":"Controlled synthetic matcher panel of two production Hebbian rules with coactivation population independently varied. It measures finite candidate work and order sensitivity, not full learning behavior, asymptotic complexity, or natural-task frequency.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analysis_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
