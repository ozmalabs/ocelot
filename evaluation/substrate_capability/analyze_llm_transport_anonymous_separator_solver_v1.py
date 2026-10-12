#!/usr/bin/env python3
"""Independent validation and end-to-end cost analysis for cached separator routing."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1_3_lock_20261003.json'
CAP=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_3_20261003.json'
OUT=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_3_analysis_20261003.json'
V12=ROOT/'evaluation/reports/llm_transport_anonymous_separator_solver_v1_2_20261002.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comp(nodes,edges,removed):
 left=set(nodes)-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  s=min(left);left.remove(s);stack=[s];part=[]
  while stack:
   u=stack.pop();part.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(part))
 return sorted(out,key=lambda z:(len(z),z))
def proposal(nodes,edges):
 tested=0
 for k in range(len(nodes)+1):
  found=[]
  for sep in itertools.combinations(sorted(nodes),k):
   tested+=1;cc=comp(nodes,edges,set(sep))
   if len(cc)>=2:found.append({'separator':list(sep),'components':cc})
  if found:return k,tested,found
def energy(state,unary,pairs):
 return -sum(float(h)*state[int(v)] for v,h in unary)-sum(float(w)*state[int(a)]*state[int(b)] for a,b,w in pairs)
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());v12=json.loads(V12.read_text());errs=[]
 def req(ok,msg):
  if not ok:errs.append(msg)
 req(data['lock_sha256']==sha(LOCK),'capture lock hash mismatch');req(data['sources']==lock['sources']==data['post_run_sources'],'source drift')
 req(not data['failures'],'worker failure');req(all(data['checks'].values()),'runner gate failure')
 runs=data['runs'];req(len(runs)==3 and len({r['pid'] for r in runs})==3,'expected three fresh workers')
 allcells=[(run,c) for run in runs for c in run['rows']];req(len(allcells)==60,'expected 60 rows')
 for run in runs:
  rows=run['rows'];sigs={r['topology_signature_sha256'] for r in rows}
  req(len(sigs)==1 and run['unique_topology_count']==1 and run['proposal_searches']==1 and run['cache_hits']==19,'topology cache evidence mismatch')
  req(sum(not r['proposal_cache_hit'] for r in rows)==1 and not rows[0]['proposal_cache_hit'],'proposal must be computed once on first row')
  req(all(r['anon_seed']==20261003+run['replicate']*1000 and r['anon_map_by_native_order']==rows[0]['anon_map_by_native_order'] for r in rows),'anonymous mapping was not stable within worker')
  req(abs(run['proposal_search_ns_total']-sum(r['timing_ns']['proposal'] for r in rows))==0,'proposal accounting mismatch')
 for _,c in allcells:
  nodes=list(range(c['nodes']));edges=[tuple(e) for e in c['anonymous_edges']]
  k,tested,candidates=proposal(nodes,edges)
  observed=[{'separator':r['separator'],'components':r['components']} for r in c['proposal_candidates']]
  req((k,tested,candidates)==(c['minimum_separator_size'],c['subsets_tested'],observed),'independent proposal mismatch')
  req(len(c['proposal_candidates'])==2 and c['solved_candidate']['separator']==c['proposal_candidates'][0]['separator'],'deterministic candidate selection mismatch')
  s=c['solved_candidate'];state={int(v):float(x) for v,x in s['state'].items()}
  req(len(state)==16 and all(x in (-1.,0.,1.) for x in state.values()),'selected state invalid')
  req(abs(energy(state,c['anonymous_unary'],c['anonymous_pair_factors'])-s['energy'])<=1e-8,'selected candidate rescore mismatch')
  req(abs(s['energy']-c['jt_energy'])<=1e-8 and abs(c['jt_energy']-c['jt_direct_rescore'])<=1e-8,'selected energy differs from JT')
  req(s['target_prediction']==c['jt_prediction']==c['conditioned_prediction'],'selected signs differ from JT')
 total={}
 for run in runs:
  structural=sum(r['timing_ns']['proposal_plus_solver'] for r in run['rows'])/1e6
  mono=sum(r['timing_ns']['junction_tree'] for r in run['rows'])/1e6
  total[run['replicate']]={'structural_batch_ms':structural,'monolithic_batch_ms':mono,'speed_ratio':mono/structural}
 group={}
 for cond in ('learned','shuffled'):
  vals=[c for _,c in allcells if c['condition']==cond]
  group[cond]={'n':len(vals),'heldout_accuracy':statistics.mean(c['conditioned_accuracy'] for c in vals),
   'median_conditioned_solver_ms':statistics.median(c['timing_ns']['candidate_solver']/1e6 for c in vals),
   'median_junction_tree_ms':statistics.median(c['timing_ns']['junction_tree']/1e6 for c in vals)}
 v12cells=[c for r in v12['runs'] for c in r['rows']]
 v12route=statistics.median(c['timing_ns']['proposal_plus_solver']/1e6 for c in v12cells)
 out={'schema':'LlmTransportAnonymousSeparatorSolverV1_3Analysis','gates_pass':not errs,'errors':errs,'checks':data['checks'],'by_condition':group,
  'proposal_cache':{'searches_per_worker':[r['proposal_searches'] for r in runs],'hits_per_worker':[r['cache_hits'] for r in runs],
   'median_one_search_ms':statistics.median(r['proposal_search_ns_total']/1e6 for r in runs),'amortized_over_20_cells_ms':statistics.median(r['proposal_search_ns_total']/1e6 for r in runs)/20},
  'batch_comparison_by_worker':total,'median_batch_speed_ratio':statistics.median(r['speed_ratio'] for r in total.values()),
  'v1_2_uncached_all_candidate_median_per_cell_ms':v12route,
  'interpretation':'Graph-only proposal uses anonymous topology and exact signature caching; one valid minimum separator is solved per topology. This remains one repeated authored K8,8 graph family.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errs))
if __name__=='__main__':sys.exit(main())
