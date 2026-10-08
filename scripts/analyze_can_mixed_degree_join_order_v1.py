#!/usr/bin/env python3
"""Exhaustive 24-order candidate-work oracle for CAN's production motif."""
import hashlib,importlib.util,itertools,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/can_mixed_degree_join_order_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/can_mixed_degree_join_order_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/can_mixed_degree_join_order_v1_analysis_20261001.json"
RUNNER=ROOT/"evaluation/substrate_capability/can_mixed_degree_join_order_v1.py"
SEED=ROOT/"seeds/can_native_reimplementation.json"
spec=importlib.util.spec_from_file_location("can_mixed_runner",RUNNER);RUN=importlib.util.module_from_spec(spec);spec.loader.exec_module(RUN)
def graph_relations(n,q,layout):
 pairs=RUN.pair_rows(n,q,layout);return {"has_concept":[("mt",f"c{i}") for i in range(n)],"coactivated_with":[(f"c{a}",f"co{j}") for j,(a,b) in enumerate(pairs)],"coactivation_of":[(f"co{j}",f"c{b}") for j,(a,b) in enumerate(pairs)]}
def prefix_work(n,q,layout,order):
 rels=graph_relations(n,q,layout);out={r:{} for r in rels};inc={r:{} for r in rels}
 for rel,pairs in rels.items():
  for a,b in pairs:out[rel].setdefault(a,[]).append(b);inc[rel].setdefault(b,[]).append(a)
 counts=[0]*len(order);binding={}
 def descend(i):
  if i==len(order):return
  src,rel,tgt=order[i];bs=binding.get(src);bt=binding.get(tgt)
  if bs is not None:candidates=[(bs,v) for v in out[rel].get(bs,[])]
  elif bt is not None:candidates=[(v,bt) for v in inc[rel].get(bt,[])]
  else:candidates=list(rels[rel])
  counts[i]+=len(candidates)
  for a,b in candidates:
   if bs is not None and bs!=a:continue
   if bt is not None and bt!=b:continue
   old_s=binding.get(src);old_t=binding.get(tgt);binding[src]=a;binding[tgt]=b;descend(i+1)
   if old_s is None:binding.pop(src,None)
   else:binding[src]=old_s
   if old_t is None:binding.pop(tgt,None)
   else:binding[tgt]=old_t
 descend(0);return counts
def predicted_order(edges,cards):
 rem=list(range(len(edges)));bound=set();out=[]
 def card(pos):return int(cards.get(edges[pos][1],0))
 def pop(pos):
  value=rem[pos];rem[pos]=rem[-1];rem.pop();return value
 first=pop(min(range(len(rem)),key=lambda p:card(rem[p])));out.append(edges[first]);bound.update((edges[first][0],edges[first][2]))
 while rem:
  con=[p for p,i in enumerate(rem) if edges[i][0] in bound or edges[i][2] in bound];opts=con or list(range(len(rem)));chosen=opts[0]
  for p in opts[1:]:
   if card(rem[p])<card(rem[chosen]):chosen=p
  i=pop(chosen);out.append(edges[i]);bound.update((edges[i][0],edges[i][2]))
 return [list(x) for x in out]
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"];seed=json.loads(SEED.read_text());source_edges=next(r["match"] for r in seed["rules"] if r.get("name")=="can_native_hebbian_mint")
 expected={(n,q,layout,rep) for n in (16,32) for q in RUN.qvalues(n) for layout in RUN.LAYOUTS for rep in range(3)};actual={(x["n"],x["q"],x["layout"],x["replicate"]) for x in runs}
 order_ok=[];prefix_ok=[];sum_ok=[];graph_ok=[];rule_ok=[];results=[]
 for row in runs:
  x=row["result"];n=row["n"];q=row["q"];layout=row["layout"];cards={"has_concept":n,"coactivated_with":q,"coactivation_of":q};pred=predicted_order(source_edges,cards);order_ok.append(x["installed_match"]==pred)
  expected_pos=prefix_work(n,q,layout,x["installed_match"]);by_pos={int(p):int(c) for ri,p,c in x["clause_candidates"]};obs=[by_pos.get(i,0) for i in range(4)];prefix_ok.append(expected_pos==obs);sum_ok.append(sum(obs)==int(x["global"].get("cand_tested",0)))
  graph_ok.append(x["before_digest"]==x["after_digest"] and x["nodes"]==n+q+1 and x["edges"]==n+2*q and x["progress"]==0 and x["terminal_progress"]==0);rule_ok.append(x["active_rules"]==[RUN.TARGET] and int(x["global"].get("cand_tested",0))==sum(int(c) for ri,m,c in x["per_rule"] if m=="candidate_tests"))
  alternatives=[(sum(prefix_work(n,q,layout,perm)),perm) for perm in itertools.permutations(source_edges)];best_item=min(alternatives,key=lambda z:z[0]);worst_item=max(alternatives,key=lambda z:z[0]);best=best_item[0];actual_work=sum(obs);results.append((row,obs,actual_work,best,pred,worst_item[0],best_item[1],worst_item[1]))
 checks={"complete_36_cells":len(runs)==36 and actual==expected,"36_fresh_processes":len({x["pid"] for x in runs})==36,"stable_source_lock":raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["start"]==lock==x["end"] for x in runs),"native_install_order_matches_independent_replay":len(order_ok)==36 and all(order_ok),"prefix_counts_match_independent_typed_join_simulator":len(prefix_ok)==36 and all(prefix_ok),"prefix_totals_reconcile_global_counter":len(sum_ok)==36 and all(sum_ok),"read_only_graph_and_fixed_point":len(graph_ok)==36 and all(graph_ok),"active_rule_and_per_rule_reconciliation":len(rule_ok)==36 and all(rule_ok),"all_24_orders_evaluated":len(results)==36 and all(z[2]>=z[3]>0 and z[5]>=z[2] for z in results)}
 groups=[]
 for n in (16,32):
  for q in RUN.qvalues(n):
   for layout in RUN.LAYOUTS:
     cells=[z for z in results if (z[0]["n"],z[0]["q"],z[0]["layout"])==(n,q,layout)];actuals=[z[2] for z in cells];best=[z[3] for z in cells];worst=[z[5] for z in cells]
     best_order=[list(e) for e in cells[0][6]]
     groups.append({"n":n,"q":q,"layout":layout,"replicates":len(cells),"installed_order":[list(e) for e in cells[0][4]],"best_order":best_order,"best_clause_candidates":prefix_work(n,q,layout,best_order),"worst_order":[list(e) for e in cells[0][7]],"median_clause_candidates":[statistics.median(z[1][i] for z in cells) for i in range(4)],"median_actual_tests":statistics.median(actuals),"median_best_of_24":statistics.median(best),"median_worst_of_24":statistics.median(worst),"median_regret_ratio":statistics.median(a/b for a,b in zip(actuals,best)),"optimal_replicates":sum(a==b for a,b in zip(actuals,best))})
 regrets=[z[2]/z[3] for z in results];payload={"protocol":"CAN_MIXED_DEGREE_JOIN_ORDER_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"groups":groups,"aggregate":{"optimal_workers":sum(z[2]==z[3] for z in results),"median_regret_ratio":statistics.median(regrets),"max_regret_ratio":max(regrets)},"claim_boundary":"Effect-free native enumeration of one production CAN Hebbian pattern on uniform and deliberately source-skewed coactivation layouts; finite N/Q only.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":len(checks),"workers":len(runs),"aggregate":payload["aggregate"]},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("CAN mixed-degree order analysis failed")
if __name__=="__main__":main()
