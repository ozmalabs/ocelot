#!/usr/bin/env python3
"""Independent integrity and exhaustive-order analysis for retinal panel."""
import hashlib,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/photon_retinal_join_order_v1_1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/photon_retinal_join_order_v1_1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/photon_retinal_join_order_v1_1_analysis_20261001.json"
PROFILES=("uniform","correlated","rotated")
def candidates(a):return int(a["global"].get("cand_tested",0))
def metric_sum(arm,name,metric):
 names={int(x[0]):str(x[2]) for x in arm["rule_metadata"]}
 return sum(int(count) for idx,key,count in arm["per_rule"] if names.get(int(idx))==name and key==metric)
def productive(a):
 ps=a["percepts"]
 if len(ps)!=12:return False
 for i in range(11):
  x=ps.get(f"percept:{i}",{})
  if x.get("percept_epoch")!=1 or any(float(x.get(k,0))!=0.0 for k in ("intensity","red_green","blue_yellow","salience")):return False
 x=ps.get("percept:11",{})
 return (x.get("percept_epoch")==1 and abs(float(x.get("intensity",0))-0.55)<1e-9 and abs(float(x.get("red_green",0))-0.25)<1e-9 and abs(float(x.get("blue_yellow",0))+0.5)<1e-9 and "salience" in x)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];expected_orders=list(itertools.permutations(range(5)))
 checks={
  "complete_nine_workers":len(runs)==9 and {(r["profile"],r["replicate"]) for r in runs}=={(p,i) for p in PROFILES for i in range(3)},
  "nine_fresh_processes":len({r["pid"] for r in runs})==9,
  "source_inputs_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["start"]==lock==r["end"] for r in runs),
  "exact_120_unique_orders_per_worker":all(len(r["permutations"])==120 and {tuple(a["order_indices"]) for a in r["permutations"]}==set(expected_orders) for r in runs),
  "default_order_is_valid_five_clause_permutation":all(tuple(REL for REL in r["default"]["installed_order"]) in (tuple(tuple(a["installed_order"]) for a in r["permutations"])) for r in runs),
  "same_input_graph_all_arms":all(len({r["default"]["before_digest"],*(a["before_digest"] for a in r["permutations"])})==1 for r in runs),
  "exact_productive_guard_oracle_all_orders":all(productive(r["default"]) and all(productive(a) for a in r["permutations"]) for r in runs),
  "canonical_semantic_parity_all_orders":all(len({r["default"]["after_digest"],*(a["after_digest"] for a in r["permutations"])})==1 for r in runs),
  "fixed_point_all_orders":all(r["default"]["progress"]<100 and r["default"]["terminal_progress"]==0 and all(a["progress"]<100 and a["terminal_progress"]==0 for a in r["permutations"]) for r in runs),
  "instrumented_plain_default_best_parity":all(r["default"]["after_digest"]==r["default_plain"]["after_digest"]==r["best"]["after_digest"]==r["best_plain"]["after_digest"] and r["default"]["progress"]==r["default_plain"]["progress"] and r["best"]["progress"]==r["best_plain"]["progress"] for r in runs),
  "best_is_exhaustive_minimum":all((candidates(r["best"]),tuple(r["best"]["order_indices"]))==min((candidates(a),tuple(a["order_indices"])) for a in r["permutations"]) for r in runs),
  "candidate_counter_reconciliation":all(metric_sum(a,"photon_column_synthesizes_retinal_percept","candidate_tests")==candidates(a) for r in runs for a in [r["default"],*r["permutations"]]),
  "best_order_stable_across_replicates":all(len({tuple(r["best"]["order_indices"]) for r in runs if r["profile"]==p})==1 for p in PROFILES),
 }
 groups=[]
 for p in PROFILES:
  cells=[r for r in runs if r["profile"]==p];best_orders={tuple(r["best"]["order_indices"]) for r in cells};work_by_order={}
  for a in cells[0]["permutations"]:
   order=tuple(a["order_indices"]);work_by_order[order]=statistics.median(candidates(next(x for x in r["permutations"] if tuple(x["order_indices"])==order)) for r in cells)
  ranking=sorted(work_by_order.items(),key=lambda x:(x[1],x[0]))
  default_median=statistics.median(candidates(r["default"]) for r in cells);best_order=next(iter(best_orders));best_median=work_by_order[best_order]
  groups.append({"profile":p,"replicates":len(cells),"default_order":cells[0]["default"]["installed_order"],"default_median_candidate_tests":default_median,"best_order_indices":list(best_order),"best_order_types":[cells[0]["permutations"][list(expected_orders).index(best_order)]["installed_order"][i] for i in range(5)],"best_median_candidate_tests":best_median,"candidate_reduction_pct_vs_default":100*(1-best_median/default_median),"top_10_orders":[{"indices":list(order),"median_candidate_tests":work} for order,work in ranking[:10]],"unique_work_values":len(set(work_by_order.values()) )})
 payload={"protocol":"PHOTON_RETINAL_JOIN_ORDER_V1_1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"profiles":groups,"claim_boundary":"Exhaustive ordering over one five-clause production retinal rule with controlled synthetic receptor supports; finite fixture, not a general selector or natural-image claim.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("retinal ordering analyzer gate failed")
if __name__=="__main__":main()
