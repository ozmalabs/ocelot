#!/usr/bin/env python3
"""Exhaustively audit separators and assignment-count proxies for task K4,8."""
from __future__ import annotations
import hashlib,itertools,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_MODE_NEURON_SEPARATOR_AUDIT_V1_PREREG_20261002.md'
PRIOR=ROOT/'evaluation/reports/llm_mode_neuron_task_graph_inference_census_v1_20261002.json'
PRIOR_RUNNER=ROOT/'evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1.py'
PRIOR_LOCK=ROOT/'evaluation/substrate_capability/llm_mode_neuron_task_graph_inference_census_v1_lock_20261002.json'
RUNNER=Path(__file__).resolve()
LOCK=ROOT/'evaluation/substrate_capability/llm_mode_neuron_separator_audit_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_mode_neuron_separator_audit_v1_20261002.json'

def digest(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sources():return {'artifacts':[digest(x) for x in (PROTOCOL,PRIOR,PRIOR_RUNNER,PRIOR_LOCK,RUNNER)],'domain_cardinality':3,'mode_count':4,'neuron_count':8}
def comps(vertices,edges,removed):
 left=set(vertices)-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  root=next(iter(left));stack=[root];left.remove(root);c=[]
  while stack:
   u=stack.pop();c.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(c))
 return sorted(out,key=lambda x:(len(x),x))
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/result')
  LOCK.write_text(json.dumps({'schema':'LlmModeNeuronSeparatorAuditV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source/capture drift from lock')
 data=json.loads(PRIOR.read_text());rows=[row for run in data['runs'] for row in run['rows']]
 checks={'30_rows':len(rows)==30,'prior_capture_checks_pass':all(data['checks'].values()),
  'topology_is_connected_K4_8':all(r['connected'] and r['nodes']==12 and r['undirected_factors']==32 and r['mode_neuron_edges']==32 for r in rows)}
 vertices=list(range(12));modes=set(range(4));neurons=set(range(4,12));edges=[(m,n) for m in modes for n in neurons]
 assert len(edges)==32
 sep_counts={};minimum=None;minimum_sets=[];minimum_profiles=[]
 for mask in range(1<<len(vertices)):
  removed={v for v in vertices if mask>>v&1};parts=comps(vertices,edges,removed)
  if len(parts)>=2:
   k=len(removed);sep_counts[str(k)]=sep_counts.get(str(k),0)+1
   if minimum is None or k<minimum:minimum=k;minimum_sets=[];minimum_profiles=[]
   if k==minimum:
    minimum_sets.append(sorted(removed));minimum_profiles.append({'removed_modes':len(removed&modes),'removed_neurons':len(removed&neurons),'components':parts})
 checks.update({'all_4096_subsets_enumerated':(1<<len(vertices))==4096,'source_unchanged':before==sources(),
  'same_graph_profile_all_rows':len({(r['nodes'],r['undirected_factors'],r['mode_neuron_edges'],r['connected']) for r in rows})==1,
  'min_separator_size_four':minimum==4,'role_separator_found':sorted(modes) in minimum_sets})
 mono=8*(3**5)+sum(3**k for k in range(4,0,-1));conditioned=(3**4)*8*3
 result={'schema':'LlmModeNeuronSeparatorAuditV1','checks':checks,'gates_pass':all(checks.values()),
  'source_lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'source_hashes':before,
  'rows':len(rows),'distinct_topologies':1,'topology':'complete bipartite K4,8, repeated over 30 held-out weighted rows',
  'subsets_examined':4096,'valid_separator_counts_by_size':sep_counts,'minimum_separator_size':minimum,
  'minimum_separators':minimum_sets,'minimum_separator_profiles':minimum_profiles,
  'operation_proxy':{'cardinality':3,'monolithic_width':4,'monolithic_table_assignments':mono,
   'condition_on_four_modes_table_assignments':conditioned,'monolithic_over_conditioned_ratio':mono/conditioned,
   'interpretation':'proxy counts, excluding combination, search, storage, and scheduling costs'},
  'limits':['one real model export/layer and fixed authored incidence topology','no automatic separator proposal','no execution-time or memory comparison','no prevalence or task-utility claim']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2));return 0 if result['gates_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
