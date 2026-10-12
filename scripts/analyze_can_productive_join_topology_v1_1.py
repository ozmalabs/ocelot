#!/usr/bin/env python3
"""Independent gates for productive CAN topology and join-order panel."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/can_productive_join_topology_v1_1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/can_productive_join_topology_v1_1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/can_productive_join_topology_v1_1_analysis_20261001.json"
ORDERS=("authored","sparse","best");LAYOUTS=("cyclic","hub","clustered");TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
EXPECTED_ORDERS={"authored":["has_concept","has_concept","coactivation_of","coactivated_with"],"sparse":["coactivated_with","coactivation_of","has_concept","has_concept"],"best":["has_concept","coactivated_with","coactivation_of","has_concept"]}
def metric_sum(arm,name,metric):
 names={int(x[0]):str(x[2]) for x in arm["rule_metadata"]}
 return sum(int(count) for idx,key,count in arm["per_rule"] if names.get(int(idx))==name and key==metric)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(layout,n,q,rep) for layout in LAYOUTS for n in (32,64) for q in (n,4*n,n*(n-1)//4) for rep in range(3)}
 arms=[(r,k) for r in runs for k in ORDERS]
 checks={
  "complete_54_layout_size_population_cells":len(runs)==54 and {(r["layout"],r["n"],r["q"],r["replicate"]) for r in runs}==expected,
  "54_fresh_processes":len({r["pid"] for r in runs})==54,
  "source_inputs_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["start"]==lock==r["end"] for r in runs),
  "exact_active_rules":all(r[k]["active_rules"]==list(TARGETS) for r,k in arms),
  "all_installed_orders_verified":all(all(r[k]["installed_match_order"][t]==EXPECTED_ORDERS[k] for t in TARGETS) for r,k in arms),
  "productive_pair_oracle_and_bounded_growth":all(r[k]["initial_reweight_pairs"]==r["q"]//2 and len(r[k]["pair_results"])==r["q"] and all(p["causal_present"] and p["evidence_tick"]==1 and p["confirm"]==1 and p["disconfirm"]==0 for p in r[k]["pair_results"]) and r[k]["nodes"]==r["n"]+r["q"]+1 and r[k]["edges"]==r["n"]+3*r["q"] for r,k in arms),
  "terminal_fixed_point_and_step_cap":all(r[k]["progress"]<100000 and r[k]["terminal_progress"]==0 for r,k in arms),
  "canonical_graph_parity_across_orders":all(len({r[k]["after_digest"] for k in ORDERS})==1 for r in runs),
  "instrumentation_semantic_parity":all(r[k]["after_digest"]==r[f"{k}_plain"]["after_digest"] and r[k]["progress"]==r[f"{k}_plain"]["progress"] for r in runs for k in ORDERS),
  "per_rule_candidates_reconcile_global":all(sum(metric_sum(r[k],t,"candidate_tests") for t in TARGETS)==int(r[k]["global"].get("cand_tested",0)) for r,k in arms),
  "three_pair_layouts_are_distinct":all(len({next(r for r in runs if r["layout"]==layout and r["n"]==n and r["q"]==q and r["replicate"]==rep)["authored"]["pair_digest"] for layout in LAYOUTS})==3 for n in (32,64) for q in (n,4*n,n*(n-1)//4) for rep in range(3)),
  "pair_input_held_constant_across_order_arms":all(len({r[k]["pair_digest"] for k in ORDERS})==1 for r in runs),
 }
 groups=[]
 for layout in LAYOUTS:
  for n in (32,64):
   for q in (n,4*n,n*(n-1)//4):
    cells=[r for r in runs if r["layout"]==layout and r["n"]==n and r["q"]==q];g={"layout":layout,"n":n,"q":q,"q_over_n":q/n,"replicates":len(cells)}
    for k in ORDERS:
     data=[r[k] for r in cells]
     g[k]={"median_candidate_tests":statistics.median(int(x["global"].get("cand_tested",0)) for x in data),"median_term_evals":statistics.median(int(x["global"].get("term_evals_total",0)) for x in data),"median_wall_ms":statistics.median(int(x["wall_ns"]) for x in data)/1e6,"median_progress":statistics.median(int(x["progress"]) for x in data)}
    base=g["authored"]["median_candidate_tests"]
    g["candidate_reduction_pct_vs_default"]={k:(None if base==0 else 100*(1-g[k]["median_candidate_tests"]/base)) for k in ORDERS}
    groups.append(g)
 payload={"protocol":"CAN_PRODUCTIVE_JOIN_TOPOLOGY_V1_1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"orders":list(ORDERS),"layouts":list(LAYOUTS),"groups":groups,"claim_boundary":"Synthetic productive closure for two production CAN Hebbian rules over three generated pair layouts; finite sizes and one source revision.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("productive topology analyzer gate failed")
if __name__=="__main__":main()
