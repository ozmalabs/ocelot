#!/usr/bin/env python3
"""Verify graph-first installation order and compare matched CAN captures."""
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/can_install_time_join_order_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/can_install_time_join_order_v1_lock_20261001.json"
PRIOR_RAW=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_workers_20261001.json"
PRIOR_ANALYSIS=ROOT/"evaluation/reports/can_productive_coactivation_closure_v1_analysis_20261001.json"
OUT=ROOT/"evaluation/reports/can_install_time_join_order_v1_analysis_20261001.json"
SEED=ROOT/"seeds/can_native_reimplementation.json";TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
def predicted_order(edges,cards):
 remaining=list(range(len(edges)));bound=set();out=[]
 def card(pos):return int(cards.get(edges[pos][1],0))
 def remove_swap(pos):
  value=remaining[pos];remaining[pos]=remaining[-1];remaining.pop();return value
 first=remove_swap(min(range(len(remaining)),key=lambda j:card(remaining[j])))
 out.append(edges[first]);bound.update((edges[first][0],edges[first][2]))
 while remaining:
  connected=[j for j,p in enumerate(remaining) if edges[p][0] in bound or edges[p][2] in bound]
  options=connected or list(range(len(remaining)))
  pick=options[0]
  for j in options[1:]:
   if card(remaining[j])<card(remaining[pick]):pick=j
  pos=remove_swap(pick);out.append(edges[pos]);bound.update((edges[pos][0],edges[pos][2]))
 return [list(x) for x in out]
def rule_counts(arm,name,metric):
 names={int(x[0]):str(x[2]) for x in arm["rule_metadata"]}
 return sum(int(count) for idx,key,count in arm["per_rule"] if names.get(int(idx))==name and key==metric)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];prior=json.loads(PRIOR_RAW.read_text());prior_analysis=json.loads(PRIOR_ANALYSIS.read_text());old=prior["runs"]
 expected={(n,q,r) for n in (32,64,128) for q in (0,n,4*n,n*(n-1)//4,n*(n-1)) for r in range(3)}
 old_by={(x["n"],x["q"],x["replicate"]):x for x in old};new_by={(x["n"],x["q"],x["replicate"]):x for x in runs}
 seed=json.loads(SEED.read_text());rules={x["name"]:x["match"] for x in seed["rules"] if x.get("name") in TARGETS}
 arms=[(x,k) for x in runs for k in ("graph_first_authored","graph_first_sparse_authored")]
 order_ok=[]
 for x,k in arms:
  arm=x[k];variant=k.endswith("sparse_authored");cards={"has_concept":x["n"],"coactivated_with":x["q"],"coactivation_of":x["q"]}
  for target in TARGETS:
   authored=rules[target];edges=[authored[2],authored[3],authored[0],authored[1]] if variant else authored
   order_ok.append(arm["installed_match_order"][target]==predicted_order(edges,cards))
 integrity=prior["locked_inputs"]==prior["post_run_inputs"] and prior_analysis["all_checks_pass"] and all(x["start"]==prior["locked_inputs"]==x["end"] for x in old)
 parity=[]
 for key,x in new_by.items():
  p=old_by[key]
  parity.extend([x["graph_first_authored"]["before_digest"]==p["base"]["before_digest"],x["graph_first_sparse_authored"]["before_digest"]==p["sparse"]["before_digest"],x["graph_first_authored"]["after_digest"]==p["base"]["after_digest"],x["graph_first_sparse_authored"]["after_digest"]==p["sparse"]["after_digest"]])
 checks={"complete_45_cells":len(runs)==45 and set(new_by)==expected,"fresh_workers":len({x["pid"] for x in runs})==45,"source_and_prior_capture_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["start"]==lock==x["end"] for x in runs) and integrity,"only_target_rules_active":all(x[k]["active_rules"]==list(TARGETS) for x,k in arms),"independent_order_oracle":len(order_ok)==180 and all(order_ok),"bounded_closure_and_terminal_fixedpoint":all(x[k]["progress"]<100000 and x[k]["terminal_progress"]==0 for x,k in arms),"pair_oracle_and_growth":all(x[k]["initial_reweight_pairs"]==x["q"]//2 and len(x[k]["pair_results"])==x["q"] and all(p["causal_present"] and p["evidence_tick"]==1 and p["confirm"]==1 and p["disconfirm"]==0 for p in x[k]["pair_results"]) and x[k]["nodes"]==x["n"]+x["q"]+1 and x[k]["edges"]==x["n"]+3*x["q"] for x,k in arms),"matched_prior_canonical_result_parity":len(parity)==180 and all(parity),"per_rule_global_candidate_reconciliation":all(sum(rule_counts(x[k],t,"candidate_tests") for t in TARGETS)==int(x[k]["global"].get("cand_tested",0)) for x,k in arms)}
 groups=[]
 for n in (32,64,128):
  for q in (0,n,4*n,n*(n-1)//4,n*(n-1)):
   g={"n":n,"q":q,"replicates":3};cells=[new_by[n,q,r] for r in range(3)];oldcells=[old_by[n,q,r] for r in range(3)]
   for k,label in (("graph_first_authored","data_first_authored"),("graph_first_sparse_authored","data_first_sparse_authored")):
    vals=[x[k] for x in cells];g[label]={"installed_first_clause":sorted(set(v["installed_match_order"][TARGETS[0]][0][1] for v in vals)),"median_candidate_tests":statistics.median(int(v["global"].get("cand_tested",0)) for v in vals),"median_wall_ms":statistics.median(int(v["wall_ns"]) for v in vals)/1e6}
   g["rules_before_data_authored_candidate_tests"]=statistics.median(int(x["base"]["global"].get("cand_tested",0)) for x in oldcells);g["rules_before_data_sparse_candidate_tests"]=statistics.median(int(x["sparse"]["global"].get("cand_tested",0)) for x in oldcells)
   groups.append(g)
 payload={"protocol":"CAN_INSTALL_TIME_JOIN_ORDER_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"groups":groups,"claim_boundary":"Install-time cardinality ordering measured on the same controlled productive CAN fixture; compared with source-locked rules-before-data controls. No general optimizer guarantee or natural workload claim.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":len(checks),"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("install-time order analysis failed")
if __name__=="__main__":main()
