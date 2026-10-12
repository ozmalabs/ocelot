#!/usr/bin/env python3
"""Independent work simulation and ordering-regret analysis for mixed relations."""
import hashlib,importlib.util,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_mixed_relation_join_cost_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/substrate_mixed_relation_join_cost_v1_analysis_20261001.json"
RUNNER=ROOT/"evaluation/substrate_capability/substrate_mixed_relation_join_cost_v1.py"
spec=importlib.util.spec_from_file_location("mixed_runner",RUNNER);RUN=importlib.util.module_from_spec(spec);spec.loader.exec_module(RUN)
def order_oracle(edges,cards):
 rem=list(range(len(edges)));bound=set();out=[]
 def card(j):return int(cards.get(edges[j][1],0))
 def pop(pos):
  value=rem[pos];rem[pos]=rem[-1];rem.pop();return value
 first=pop(min(range(len(rem)),key=lambda j:card(rem[j])));out.append(edges[first]);bound.update((edges[first][0],edges[first][2]))
 while rem:
  connected=[j for j,i in enumerate(rem) if edges[i][0] in bound or edges[i][2] in bound];opts=connected or list(range(len(rem)));chosen=opts[0]
  for j in opts[1:]:
   if card(rem[j])<card(rem[chosen]):chosen=j
  idx=pop(chosen);out.append(edges[idx]);bound.update((edges[idx][0],edges[idx][2]))
 return [list(x) for x in out]
def relation_graph(n,populations):
 return {rel:RUN.relation_pairs(n,count) for rel,count in populations.items()}
def prefix_work(n,installed,populations):
 pairs=relation_graph(n,populations);out={r:{i:[] for i in range(n)} for r in pairs};inc={r:{i:[] for i in range(n)} for r in pairs}
 for rel,edges in pairs.items():
  for a,b in edges:out[rel][a].append(b);inc[rel][b].append(a)
 counts=[0]*len(installed);binding={}
 def descend(depth):
  if depth==len(installed):return
  src,rel,tgt=installed[depth];bs=binding.get(src);bt=binding.get(tgt)
  if bs is not None:candidates=[(bs,v) for v in out[rel][bs]]
  elif bt is not None:candidates=[(v,bt) for v in inc[rel][bt]]
  else:candidates=list(pairs[rel])
  counts[depth]+=len(candidates)
  for a,b in candidates:
   if bs is not None and bs!=a:continue
   if bt is not None and bt!=b:continue
   os=binding.get(src);ot=binding.get(tgt);binding[src]=a;binding[tgt]=b;descend(depth+1)
   if os is None:binding.pop(src,None)
   else:binding[src]=os
   if ot is None:binding.pop(tgt,None)
   else:binding[tgt]=ot
 descend(0);return counts
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(n,p,sp,r) for n in (16,32) for p in RUN.PATTERNS for sp in RUN.SPARSE_POSITIONS for r in range(3)};actual={(x["n"],x["pattern"],x["sparse_position"],x["replicate"]) for x in runs}
 order_checks=[];prefix_checks=[];prefix_sums=[];graphs=[];active=[];regrets=[];cells=[]
 for row in runs:
  x=row["result"];n=row["n"];shape=row["pattern"];sp=row["sparse_position"];cards=x["relation_populations"];orig=RUN.pattern(shape);pred=order_oracle(orig,cards);order_checks.append(x["installed_match"]==pred)
  expected_prefix=prefix_work(n,x["installed_match"],cards);by_pos={int(pos):int(c) for idx,pos,c in x["clause_candidates"]};observed=[by_pos.get(i,0) for i in range(4)];prefix_checks.append(expected_prefix==observed);prefix_sums.append(sum(observed)==int(x["global"].get("cand_tested",0)))
  graphs.append(x["before_digest"]==x["after_digest"] and x["progress"]==0 and x["terminal_progress"]==0 and x["nodes"]==n and x["edges"]==sum(cards.values()));active.append(x["active_rules"]==["mixed_relation_join_probe"])
  all_order_costs=[(sum(prefix_work(n,perm,cards)),perm) for perm in itertools.permutations(orig)];best=min(v for v,_ in all_order_costs);observed_total=sum(observed);regrets.append((observed_total,best));cells.append((row,observed,observed_total,best,pred))
 checks={"complete_90_cells":len(runs)==90 and actual==expected,"90_fresh_workers":len({x["pid"] for x in runs})==90,"source_lock_stable":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["start"]==lock==x["end"] for x in runs),"installed_order_matches_independent_greedy":len(order_checks)==90 and all(order_checks),"native_prefix_counts_match_independent_simulation":len(prefix_checks)==90 and all(prefix_checks),"prefix_sums_match_global_candidate_tests":len(prefix_sums)==90 and all(prefix_sums),"read_only_terminal_graph_preservation":len(graphs)==90 and all(graphs),"exact_single_rule_set":len(active)==90 and all(active),"all_24_orders_evaluated":len(regrets)==90 and all(best>0 and actual>=best for actual,best in regrets)}
 groups=[]
 for n in (16,32):
  for shape in RUN.PATTERNS:
   for sparse_pos in RUN.SPARSE_POSITIONS:
    rows=[x for x in cells if (x[0]["n"],x[0]["pattern"],x[0]["sparse_position"])==(n,shape,sparse_pos)];tot=[x[2] for x in rows];best=[x[3] for x in rows]
    groups.append({"n":n,"pattern":shape,"sparse_position":sparse_pos,"replicates":len(rows),"installed_order":[list(e) for e in rows[0][4]],"median_actual_candidate_tests":statistics.median(tot),"median_best_of_24_candidate_tests":statistics.median(best),"median_regret_ratio":statistics.median(a/b for a,b in zip(tot,best)),"selector_optimal_replicates":sum(a==b for a,b in zip(tot,best))})
 ratios=[a/b for a,b in regrets];payload={"protocol":"SUBSTRATE_MIXED_RELATION_JOIN_COST_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"groups":groups,"aggregate":{"optimal_workers":sum(a==b for a,b in regrets),"median_regret_ratio":statistics.median(ratios),"max_regret_ratio":max(ratios)},"claim_boundary":"Finite synthetic four-relation path/star/cycle patterns; exact candidate work compared to all 24 clause permutations per graph. No natural-workload or universal heuristic claim.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":len(checks),"workers":len(runs),"aggregate":payload["aggregate"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("mixed-relation join cost gates failed")
if __name__=="__main__":main()
