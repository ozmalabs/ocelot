#!/usr/bin/env python3
"""Independent gates and summary for productive CAN coactivation closure."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_analysis_20261001.json"
TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
def metric_sum(arm,name,metric):
 names={int(x[0]):str(x[2]) for x in arm["rule_metadata"]}
 return sum(int(count) for idx,key,count in arm["per_rule"] if names.get(int(idx))==name and key==metric)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(n,q,rep) for n in (32,64,128) for q in (0,n,4*n,n*(n-1)//4,n*(n-1)) for rep in range(3)}
 arms=[(r,k) for r in runs for k in ("base","sparse")]
 checks={
  "complete_45_cells":len(runs)==45 and {(r["n"],r["q"],r["replicate"]) for r in runs}==expected,
  "45_fresh_processes":len({r["pid"] for r in runs})==45,
  "source_inputs_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(r["start"]==lock==r["end"] for r in runs),
  "exact_active_rules":all(a[k]["active_rules"]==list(TARGETS) for a,k in arms),
  "installed_order_verified":all(all(a[k]["installed_match_order"][t][0]==("coactivated_with" if k=="sparse" else "has_concept") for t in TARGETS) for a,k in arms),
  "bounded_completion_and_terminal_fixed_point":all(a[k]["progress"]<100000 and a[k]["terminal_progress"]==0 for a,k in arms),
  "productive_pair_oracle_and_bounded_growth":all(a[k]["initial_reweight_pairs"]==a["q"]//2 and len(a[k]["pair_results"])==a["q"] and all(p["causal_present"] and p["evidence_tick"]==1 and p["confirm"]==1 and p["disconfirm"]==0 for p in a[k]["pair_results"]) and a[k]["nodes"]==a["n"]+a["q"]+1 and a[k]["edges"]==a["n"]+3*a["q"] for a,k in arms),
  "canonical_graph_parity_across_orders":all(r["base"]["after_digest"]==r["sparse"]["after_digest"] for r in runs),
  "instrumentation_semantic_parity":all(r[k]["after_digest"]==r[f"{k}_plain"]["after_digest"] and r[k]["progress"]==r[f"{k}_plain"]["progress"] and r[k]["terminal_progress"]==r[f"{k}_plain"]["terminal_progress"] for r in runs for k in ("base","sparse")),
  "per_rule_candidates_reconcile_global":all(sum(metric_sum(a[k],t,"candidate_tests") for t in TARGETS)==int(a[k]["global"].get("cand_tested",0)) for a,k in arms),
 }
 groups=[]
 for n in (32,64,128):
  for q in (0,n,4*n,n*(n-1)//4,n*(n-1)):
   cells=[r for r in runs if r["n"]==n and r["q"]==q];g={"n":n,"q":q,"q_over_n":q/n,"replicates":len(cells)}
   for arm_key,label in (("base","authored"),("sparse","sparse_first")):
    data=[r[arm_key] for r in cells]
    g[label]={"median_candidate_tests":statistics.median(int(x["global"].get("cand_tested",0)) for x in data),"median_term_evals":statistics.median(int(x["global"].get("term_evals_total",0)) for x in data),"median_wall_ms":statistics.median(int(x["wall_ns"]) for x in data)/1e6,"median_progress":statistics.median(int(x["progress"]) for x in data),"median_mint_candidates":statistics.median(metric_sum(x,"can_native_hebbian_mint","candidate_tests") for x in data),"median_reweight_candidates":statistics.median(metric_sum(x,"can_native_hebbian_reweight","candidate_tests") for x in data)}
   b=g["authored"]["median_candidate_tests"];s=g["sparse_first"]["median_candidate_tests"];g["candidate_reduction_pct"]=None if b==0 else 100*(1-s/b);groups.append(g)
 payload={"protocol":"CAN_PRODUCTIVE_COACTIVATION_CLOSURE_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"arms":len(arms),"groups":groups,"claim_boundary":"Synthetic productive closure for two production CAN Hebbian rules with supplied coactivation ledgers and half seeded causal links; finite sizes and source revision only.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("productive closure analyzer gate failed")
if __name__=="__main__":main()
