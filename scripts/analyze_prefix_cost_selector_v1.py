#!/usr/bin/env python3
"""Independent analysis of the bounded prefix-cost selector panel."""
import hashlib,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/prefix_cost_selector_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/prefix_cost_selector_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/prefix_cost_selector_v1_analysis_20261001.json"
PROFILES=("uniform","correlated","rotated")
def candidates(row):return int(row["candidate_tests"])
def productive(row):
 ps=row["percepts"]
 if len(ps)!=16:return False
 for i in range(15):
  x=ps.get(f"percept:{i}",{})
  if x.get("percept_epoch")!=1 or any(float(x.get(k,0))!=0.0 for k in ("intensity","red_green","blue_yellow","salience")):return False
 x=ps.get("percept:15",{})
 return x.get("percept_epoch")==1 and abs(float(x.get("intensity",0))-0.55)<1e-9 and abs(float(x.get("red_green",0))-0.25)<1e-9 and abs(float(x.get("blue_yellow",0))+0.5)<1e-9 and "salience" in x
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];orders=list(itertools.permutations(range(5)));hist_can=raw["historical"]["can"];hist_photon=raw["historical"]["photon"]
 checks={
  "complete_three_worker_heldout_schedule":len(runs)==3 and {r["replicate"] for r in runs}=={0,1,2},
  "three_fresh_processes":len({r["pid"] for r in runs})==3,
  "source_native_and_capture_inputs_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["start"]==lock==r["end"] for r in runs),
  "historical_capture_locks_valid":all(x["valid_source_lock"] for x in raw["historical_capture_validation"]),
  "historical_can_nonempty_cases_cover_22":len(hist_can)==22 and all(x["order"]==x["best_order"] for x in hist_can),
  "historical_retinal_regret_uses_exhaustive_work":len(hist_photon)==3 and all(x["selected_work"]>=x["best_work"] for x in hist_photon),
  "exactly_120_unique_heldout_orders":all(len(r["permutations"])==120 and {tuple(x["order"]) for x in r["permutations"]}==set(orders) for r in runs),
  "selector_deterministic_across_21_repeats":all(len({tuple(x["order"]) for x in r["repeat_decisions"]})==1 and all(x["order"]==r["selector_order"] for x in r["repeat_decisions"]) for r in runs),
  "heldout_graph_input_stable":len({r["pair_edge_digest"] for r in runs})==1,
  "productive_guard_and_value_oracle_all_orders":all(productive(r["default"]) and productive(r["default_plain"]) and productive(r["selected_plain"]) and all(productive(x) for x in r["permutations"]) for r in runs),
  "canonical_final_graph_parity_all_orders":all(len({r["default"]["digest"],*(x["digest"] for x in r["permutations"])})==1 for r in runs),
  "terminal_fixed_point_all_orders":all(r["default"]["progress"]<100 and r["default"]["terminal"]==0 and all(x["progress"]<100 and x["terminal"]==0 for x in r["permutations"]) for r in runs),
  "instrumented_plain_default_and_selected_parity":all(r["default"]["digest"]==r["default_plain"]["digest"] and r["selected"]["digest"]==r["selected_plain"]["digest"] and r["selected"]["progress"]==r["selected_plain"]["progress"] for r in runs),
  "exhaustive_best_and_selected_work_reconciled":all((candidates(r["best"]),tuple(r["best"]["order"]))==min((candidates(x),tuple(x["order"])) for x in r["permutations"]) and r["selected"]["order"]==r["selector_order"] for r in runs),
 }
 held=[]
 for r in runs:
  timing_index=statistics.median(x["index_ns"] for x in r["timings"]);timing_search=statistics.median(x["search_ns"] for x in r["timings"]);best_work=candidates(r["best"]);selected_work=candidates(r["selected"])
  held.append({"replicate":r["replicate"],"selector_order":r["selector_order"],"estimated_work":r["estimated_work"],"actual_selected_candidate_tests":selected_work,"exact_best_order":r["best"]["order"],"exact_best_candidate_tests":best_work,"selector_regret_pct":100*(selected_work/best_work-1),"default_candidate_tests":candidates(r["default"]),"selector_index_build_median_us":timing_index/1000,"selector_search_median_us":timing_search/1000,"selector_total_median_us":(timing_index+timing_search)/1000,"selector_total_p95_us":statistics.quantiles([x["index_ns"]+x["search_ns"] for x in r["timings"]],n=20)[18]/1000})
 can_matches=sum(x["order"]==x["best_order"] for x in hist_can)
 photon_summary=[{"profile":x["profile"],"selected_order":x["order"],"best_order":x["best_order"],"selected_work":x["selected_work"],"best_work":x["best_work"],"regret_pct":100*(x["selected_work"]/x["best_work"]-1)} for x in hist_photon]
 payload={"protocol":"PREFIX_COST_SELECTOR_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"heldout_workers":len(runs),"heldout":held,"historical":{"can_nonempty_cases":len(hist_can),"can_match_measured_best":can_matches,"can_order_mismatches":[x for x in hist_can if x["order"]!=x["best_order"]],"retinal":photon_summary},"claim_boundary":"Bounded-sample Python selector evaluated on source-locked synthetic CAN/retinal fixtures, including a newly generated N=16 retinal profile; not a production engine integration or natural-workload result.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("prefix-cost selector analyzer gate failed")
if __name__=="__main__":main()
