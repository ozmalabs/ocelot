#!/usr/bin/env python3
"""Independent gates and summary for the where-aware selector v2 panel."""
import hashlib,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/prefix_cost_selector_v2_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/prefix_cost_selector_v2_lock_20261001.json"
OUT=ROOT/"evaluation/reports/prefix_cost_selector_v2_20261001.json"
def work(x):return int(x["candidate_tests"])
def productive(x):
 ps=x["percepts"]
 if len(ps)!=20:return False
 for i in range(19):
  p=ps.get(f"percept:{i}",{})
  if p.get("percept_epoch")!=1 or any(float(p.get(k,0))!=0 for k in ("intensity","red_green","blue_yellow","salience")):return False
 p=ps.get("percept:19",{})
 return p.get("percept_epoch")==1 and abs(float(p.get("intensity",0))-.55)<1e-9 and abs(float(p.get("red_green",0))-.25)<1e-9 and abs(float(p.get("blue_yellow",0))+.5)<1e-9 and "salience" in p
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];orders=set(itertools.permutations(range(5)));checks={
  "three_workers_and_processes":len(runs)==3 and {x["replicate"] for x in runs}=={0,1,2} and len({x["pid"] for x in runs})==3,
  "source_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["start"]==lock==x["end"] for x in runs),
  "new_heldout_profile":all(x["profile"]=="heldout_latin_v2" and x["n"]==20 for x in runs) and len({x["pair_edge_digest"] for x in runs})==1,
  "all_120_orders_measured":all(len(x["permutations"])==120 and {tuple(y["order"]) for y in x["permutations"]}==orders for x in runs),
  "selector_repeat_and_worker_determinism":len({tuple(x["selector_order"]) for x in runs})==1 and all(all(y["order"]==x["selector_order"] for y in x["repeat_decisions"]) for x in runs),
  "productive_guard_and_values":all(productive(x["default"]) and productive(x["selected"]) and productive(x["default_plain"]) and productive(x["selected_plain"]) and all(productive(y) for y in x["permutations"]) for x in runs),
  "semantic_parity_and_fixed_point":all(len({x["default"]["digest"],*(y["digest"] for y in x["permutations"])})==1 and x["default"]["digest"]==x["default_plain"]["digest"] and x["selected"]["digest"]==x["selected_plain"]["digest"] and x["default"]["terminal"]==0 and all(y["terminal"]==0 for y in x["permutations"]) for x in runs),
  "selected_and_exact_min_reconcile":all(x["selected"]["order"]==x["selector_order"] and (work(x["best"]),tuple(x["best"]["order"]))==min((work(y),tuple(y["order"])) for y in x["permutations"]) for x in runs),
 }
 rows=[]
 for x in runs:
  s=statistics.median(y["search_ns"] for y in x["timings"]);i=statistics.median(y["index_ns"] for y in x["timings"]);actual=work(x["selected"]);best=work(x["best"]);default=work(x["default"])
  rows.append({"replicate":x["replicate"],"selected_order":x["selector_order"],"estimated_work":x["estimated_work"],"selected_work":actual,"best_order":x["best"]["order"],"best_work":best,"default_work":default,"regret_pct":100*(actual/best-1),"vs_default_pct":100*(actual/default-1),"index_median_us":i/1000,"search_median_us":s/1000,"total_median_us":(i+s)/1000})
 payload={"protocol":"PREFIX_COST_SELECTOR_V2","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":rows,"claim_boundary":"One source-locked synthetic N=20 retinal profile with partial evaluation of supported production guard terms; Python selector prototype, not native integration or natural-workload generalization.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("selector v2 gate failed")
if __name__=="__main__":main()
