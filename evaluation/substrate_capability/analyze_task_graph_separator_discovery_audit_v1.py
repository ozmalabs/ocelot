#!/usr/bin/env python3
"""Independent validation and amortization analysis of separator search."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/task_graph_separator_discovery_audit_v1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/task_graph_separator_discovery_audit_v1_20261002.json'
ROLE=ROOT/'evaluation/reports/llm_transport_role_separator_v1_2_analysis_20261002.json'
OUT=ROOT/'evaluation/reports/task_graph_separator_discovery_audit_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def graph(m,n):return {**{v:set() for v in range(m+n)},**{}}
def parts(n,edges,removed):
 left=set(range(n))-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  s=min(left);left.remove(s);stack=[s];c=[]
  while stack:
   u=stack.pop();c.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(c))
 return sorted(out,key=lambda c:(len(c),c))
def independent(m,n):
 edges=[(i,m+j) for i in range(m) for j in range(n)];tested=0
 for k in range(m+n+1):
  found=[]
  for s in __import__('itertools').combinations(range(m+n),k):
   tested+=1;p=parts(m+n,edges,set(s))
   if len(p)>=2:found.append({'removed':list(s),'components':p})
  if found:return k,found,tested
def main():
 lock=json.loads(LOCK.read_text());x=json.loads(CAPTURE.read_text());role=json.load(open(ROLE));errs=[]
 def req(v,m):
  if not v:errs.append(m)
 req(x['lock_sha256']==sha(LOCK),'capture lock hash mismatch');req(x['sources']==lock['sources']==x['post_run_sources'],'source drift')
 req(all(x['checks'].values()),'runner gates fail');req(role.get('gates_pass',False),'role solver analysis gate fails')
 expected={'K4_8':(4,8),'K8_8':(8,8)};summary={}
 for name,(m,n) in expected.items():
  k,sets,tested=independent(m,n);obs=[r['graphs'][name] for r in x['runs']]
  req(all(o['search_result']['minimum_size']==k and o['search_result']['minimum_separators']==sets and o['search_result']['tested_subsets']==tested for o in obs),'independent separator result mismatch '+name)
  req(len({json.dumps(o['search_result']['minimum_separators'],sort_keys=True) for o in obs})==1,'worker candidate set differs '+name)
  times=[t/1e6 for o in obs for t in o['repeat_times_ns']]
  role_sets=[s['removed'] for s in sets]
  summary[name]={'nodes':m+n,'edges':m*n,'minimum_separator_size':k,'minimum_separators':sets,'role_shore_separators':role_sets,
   'tested_subsets_through_minimum':tested,'search_median_ms':statistics.median(times),'search_p95_ms':float(__import__('numpy').percentile(times,95))}
 # K8,8 discovery amortized over 20 held-out/control cells; measured solver times are already paired from v1.2.
 k=summary['K8_8'];learned=role['by_condition']['learned']['median_conditioned_ms'];shuffled=role['by_condition']['shuffled']['median_conditioned_ms'];search_ms=k['search_median_ms']
 k['amortization_over_20_cells_ms']=search_ms/20;k['solve_ms_learned']=learned;k['solve_ms_shuffled']=shuffled
 k['future_solves_to_amortize_learned']=search_ms/learned;k['future_solves_to_amortize_shuffled']=search_ms/shuffled
 out={'schema':'TaskGraphSeparatorDiscoveryAuditV1Analysis','gates_pass':not errs,'errors':errs,'graphs':summary,
  'interpretation':'Exhaustive graph-only topology search found small separators for these two authored bipartite model-derived families. K8,8 search cost amortizes over repeated weighted inputs; this does not show that such cuts are common or that the exhaustive search is a practical general proposer.',
  'claim_limits':['two fixed topology families only','no automatically discovered partition executed during inference','K4,8 cost proxy from separate audit; no measured conditioned runtime','K8,8 solve comparison uses externally supplied source/target roles','no natural-task prevalence or broad scale claim']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errs))
if __name__=='__main__':sys.exit(main())
