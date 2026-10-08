#!/usr/bin/env python3
"""Independent structural and exact-result audit for varied-topology solver."""
import hashlib,itertools,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_solver_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/llm_transport_varied_topology_solver_v1_20261003.json'
OUT=ROOT/'evaluation/reports/llm_transport_varied_topology_solver_v1_analysis_20261003.json'
TOL=1e-8
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(n,edges,removed):
 left=set(range(n))-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  root=min(left);left.remove(root);stack=[root];part=[]
  while stack:
   u=stack.pop();part.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(part))
 return sorted(out,key=lambda c:(len(c),c))
def recompute(edges):
 tested=0
 for k in range(17):
  found=[]
  for s in itertools.combinations(range(16),k):
   tested+=1;cc=components(16,edges,set(s))
   if len(cc)>=2:found.append({'separator':list(s),'components':cc})
  if found:return k,tested,found
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errors=[]
 def req(c,msg):
  if not c:errors.append(msg)
 req(cap['lock_sha256']==sha(LOCK),'lock hash mismatch');req(cap['sources']==lock['sources']==cap['post_run_sources'],'source drift');req(all(cap['checks'].values()),'capture gates fail')
 runs=cap['runs'];req(len(runs)==3 and len({r['pid'] for r in runs})==3,'fresh worker count');req(all(len(r['rows'])==320 for r in runs),'case coverage')
 summary={};by=defaultdict(list);worker_cost=[]
 for w in runs:
  cache={}
  for r in w['rows']:
   key=r['anonymous_topology_signature'];edges=[tuple(e) for e in r['anonymous_edges']]
   k,tested,cands=recompute(edges)
   req((k,tested,cands)==(r['minimum_separator_size'],r['subsets_tested'],r['proposal_candidates']),'independent separator mismatch '+key)
   if key in cache:req(cache[key]==(k,tested,cands),'cache content mismatch '+key)
   else:cache[key]=(k,tested,cands)
   req(r['proposal_candidates'] and len(r['proposal_candidates'][0]['components'])>=2,'invalid selected separator')
   t=r['timing_ns'];route=t['graph_build']+t['factor_extract']+t['proposal']+t['conditioned_solver'];base=t['graph_build']+t['factor_extract']+t['minfill_order']+t['junction_tree']
   req(route>=0 and base>0,'invalid timing');by[(r['model'],r['fan_in'])].append((route,base,r));
  proposal=sum(r['timing_ns']['proposal'] for r in w['rows']);route=sum(r['timing_ns']['graph_build']+r['timing_ns']['factor_extract']+r['timing_ns']['proposal']+r['timing_ns']['conditioned_solver'] for r in w['rows']);base=sum(r['timing_ns']['graph_build']+r['timing_ns']['factor_extract']+r['timing_ns']['minfill_order']+r['timing_ns']['junction_tree'] for r in w['rows']);worker_cost.append({'replicate':w['replicate'],'unique_topologies':w['unique_topologies'],'cache_hits':w['cache_hits'],'proposal_ms':proposal/1e6,'proposal_amortized_ms_per_case':proposal/len(w['rows'])/1e6,'structural_batch_ms':route/1e6,'monolithic_batch_ms':base/1e6,'batch_speedup':base/route})
 for (model,fan),items in sorted(by.items()):
  rs=[x[0] for x in items];bs=[x[1] for x in items];summary[f'{model}/fan_in_{fan}']={'cases':len(items),'median_proposal_ms':statistics.median(r['timing_ns']['proposal']/1e6 for _,_,r in items),'median_conditioned_ms':statistics.median(r['timing_ns']['conditioned_solver']/1e6 for _,_,r in items),'median_junction_tree_ms':statistics.median(r['timing_ns']['junction_tree']/1e6 for _,_,r in items),'paired_median_speedup':statistics.median(b/a for a,b,_ in items),'aggregate_speedup':sum(bs)/sum(rs),'topology_cache_hits':sum(1 for _,_,r in items if r['cache_hit'])}
 out={'schema':'LlmTransportVariedTopologySolverV1Analysis','gates_pass':not errors,'errors':errors,'checks':cap['checks'],'worker_costs':worker_cost,'by_model_fan_in':summary,'claim_boundary':'Three fresh workers over 320 unique generated and evaluator-pruned 16-node factor graphs; exact structural route versus the current Python min-fill junction-tree implementation. Does not estimate natural-task prevalence or establish substrate-learning capability.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
