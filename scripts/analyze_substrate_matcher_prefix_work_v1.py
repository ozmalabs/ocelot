#!/usr/bin/env python3
"""Verify native matcher prefix counts against a separate Python enumerator."""
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_matcher_prefix_work_v1_workers_20261001.json"
LOCK=ROOT/"evaluation/substrate_capability/substrate_matcher_prefix_work_v1_lock_20261001.json"
OUT=ROOT/"evaluation/reports/substrate_matcher_prefix_work_v1_analysis_20261001.json"
RUNNER=ROOT/"evaluation/substrate_capability/substrate_matcher_prefix_work_v1.py"
spec=importlib.util.spec_from_file_location("prefix_runner",RUNNER);RUN=importlib.util.module_from_spec(spec);spec.loader.exec_module(RUN)
def order_oracle(edges,cards):
 remaining=list(range(len(edges)));bound=set();out=[]
 def card(i):return int(cards.get(edges[i][1],0))
 def pop_swap(position):
  value=remaining[position];remaining[position]=remaining[-1];remaining.pop();return value
 first=pop_swap(min(range(len(remaining)),key=lambda j:card(remaining[j])));out.append(edges[first]);bound.update((edges[first][0],edges[first][2]))
 while remaining:
  connected=[j for j,i in enumerate(remaining) if edges[i][0] in bound or edges[i][2] in bound];options=connected or list(range(len(remaining)));chosen=options[0]
  for j in options[1:]:
   if card(remaining[j])<card(remaining[chosen]):chosen=j
  index=pop_swap(chosen);out.append(edges[index]);bound.update((edges[index][0],edges[index][2]))
 return [list(x) for x in out]
def prefix_oracle(n,topology,installed):
 edge_pairs=RUN.graph_edges(n,topology);out={i:[] for i in range(n)};inc={i:[] for i in range(n)}
 for a,b in edge_pairs:out[a].append(b);inc[b].append(a)
 counts=[0]*len(installed);binding={}
 def visit(i):
  if i==len(installed):
   return
  src,relation,tgt=installed[i]
  if relation!="causal_influence":raise AssertionError(relation)
  bs=binding.get(src);bt=binding.get(tgt)
  if bs is not None:candidates=[(bs,v) for v in out[bs]]
  elif bt is not None:candidates=[(v,bt) for v in inc[bt]]
  else:candidates=list(edge_pairs)
  counts[i]+=len(candidates)
  for a,b in candidates:
   if bs is not None and bs!=a:continue
   if bt is not None and bt!=b:continue
   old_s=binding.get(src);old_t=binding.get(tgt)
   binding[src]=a;binding[tgt]=b;visit(i+1)
   if old_s is None:binding.pop(src,None)
   else:binding[src]=old_s
   if old_t is None:binding.pop(tgt,None)
   else:binding[tgt]=old_t
 visit(0);return counts
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw["runs"]
 expected={(n,t,p,o,r) for n in (16,32) for t in ("path","star","ring") for p in ("path4","star4","cycle4") for o in ("authored","reversed") for r in range(3)}
 actual={(x["n"],x["topology"],x["pattern"],x["order_input"],x["replicate"]) for x in runs}
 unique_worker=len({x["pid"] for x in runs})==108
 start_stable=raw["locked_inputs"]==lock==raw["post_run_inputs"] and all(x["start"]==lock==x["end"] for x in runs)
 order_ok=[];prefix_ok=[];total_ok=[];mutation_ok=[];rule_ok=[]
 for x in runs:
  original=RUN.pattern(x["pattern"]);source=original if x["order_input"]=="authored" else list(reversed(original));predicted=order_oracle(source,{"causal_influence":x["graph_edge_count"]});order_ok.append(x["installed_match"]==predicted)
  expected_prefix=prefix_oracle(x["n"],x["topology"],x["installed_match"]);by_pos={int(pos):int(count) for rid,pos,count in x["clause_candidates"]};observed=[by_pos.get(i,0) for i in range(4)];prefix_ok.append(expected_prefix==observed)
  total_ok.append(sum(observed)==int(x["global"].get("cand_tested",0)))
  mutation_ok.append(x["progress"]==0 and x["terminal_progress"]==0 and x["before_digest"]==x["after_digest"] and x["nodes"]==x["n"] and x["edges"]==x["graph_edge_count"])
  rule_ok.append(x["active_rules"]==["matcher_prefix_work_probe"] and int(x["global"].get("cand_tested",0))==sum(v for _,m,v in x["per_rule"] if m=="candidate_tests"))
 checks={"complete_108_cells":len(runs)==108 and actual==expected,"108_fresh_workers":unique_worker,"stable_source_lock":start_stable,"installed_order_matches_independent_greedy_oracle":len(order_ok)==108 and all(order_ok),"prefix_counters_match_independent_join_enumerator":len(prefix_ok)==108 and all(prefix_ok),"clause_sums_match_global_candidate_tests":len(total_ok)==108 and all(total_ok),"read_only_fixed_point_and_graph_preservation":len(mutation_ok)==108 and all(mutation_ok),"single_rule_and_per_rule_reconciliation":len(rule_ok)==108 and all(rule_ok),"below_match_step_cap":all(x["progress"]<1000 for x in runs)}
 groups=[]
 for n in (16,32):
  for pat in ("path4","star4","cycle4"):
   for topo in ("path","star","ring"):
    row={"n":n,"pattern":pat,"graph":topo}
    for order in ("authored","reversed"):
     cells=[x for x in runs if (x["n"],x["pattern"],x["topology"],x["order_input"])==(n,pat,topo,order)];totals=[int(x["global"].get("cand_tested",0)) for x in cells]
     per=[prefix_oracle(n,topo,c["installed_match"]) for c in cells]
     row[order]={"replicates":len(cells),"installed_order":[e for e in cells[0]["installed_match"]],"median_candidate_tests":statistics.median(totals),"median_clause_candidates":[statistics.median(v[i] for v in per) for i in range(4)],"median_wall_ms":statistics.median(int(x["wall_ns"]) for x in cells)/1e6}
    a=row["authored"]["median_candidate_tests"];b=row["reversed"]["median_candidate_tests"];row["reversed_over_authored"]=(b/a if a else None);groups.append(row)
 payload={"protocol":"SUBSTRATE_MATCHER_PREFIX_WORK_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"workers":len(runs),"groups":groups,"claim_boundary":"Exact native candidate-test prefix accounting for effect-free four-clause patterns over small synthetic causal graphs; validates counter semantics and shape/topology sensitivity only.","raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":len(checks),"workers":len(runs)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("prefix-work analyzer gate failed")
if __name__=="__main__":main()
