#!/usr/bin/env python3
"""Independent separator validation and topology-family summary."""
import hashlib,itertools,json,statistics,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_transport_varied_topology_separator_census_v1_2_lock_20261003.json'
CAP=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_20261003.json'
OUT=ROOT/'evaluation/reports/llm_transport_varied_topology_separator_census_v1_2_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(n,edges,removed):
 left=set(range(n))-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 out=[]
 while left:
  s=min(left);left.remove(s);st=[s];c=[]
  while st:
   u=st.pop();c.append(u)
   for v in adj[u]&left:left.remove(v);st.append(v)
  out.append(sorted(c))
 return sorted(out,key=lambda c:(len(c),c))
def recompute(n,edges):
 tested=0
 for k in range(n+1):
  found=[]
  for s in itertools.combinations(range(n),k):
   tested+=1;cc=components(n,edges,set(s))
   if len(cc)>=2:found.append({'separator':list(s),'components':cc})
  if found:return k,tested,found
def main():
 l=json.loads(LOCK.read_text());x=json.loads(CAP.read_text());errors=[]
 def req(v,m):
  if not v:errors.append(m)
 req(x['lock_sha256']==sha(LOCK),'lock hash mismatch');req(x['sources']==l['sources']==x['post_run_sources'],'source drift');req(all(x['checks'].values()),'capture gate failure')
 runs=x['runs'];req(len(runs)==3 and len({r['pid'] for r in runs})==3,'fresh workers')
 ref={(g['model'],g['fan_in'],g['source_signature']):g for g in runs[0]['graphs']};req(len(ref)==242,'expected 242 distinct model/fan-in/topology keys')
 family=defaultdict(list)
 for rr in runs:
  obs={(g['model'],g['fan_in'],g['source_signature']):g for g in rr['graphs']};req(set(obs)==set(ref),'worker source topology key set mismatch')
  for key,g in obs.items():
   base=ref[key];edges=[tuple(e) for e in g['edges']];n=g['nodes']
   k,tested,candidates=recompute(len(n),edges)
   req((k,tested,candidates)==(g['minimum_separator_size'],g['subsets_tested'],g['minimum_separators']),'independent separator mismatch '+str(key))
   req(g['widths'] and len(g['widths'])==1,'captured width not stable for topology')
   req(g['rows_covered']>0 and len(edges)==8*g['fan_in'],'topology row/edge count mismatch')
  if rr is runs[0]:
   for g in rr['graphs']:family[(g['model'],g['fan_in'])].append(g)
 summary={}
 for (model,fan),gs in sorted(family.items()):
  summary[f'{model}/fan_in_{fan}']={'unique_topologies':len(gs),'captured_worker_rows':sum(g['rows_covered'] for g in gs),'unique_heldout_hop_instances':sum(g['unique_instances_covered'] for g in gs),
   'edge_count':8*fan,'width_counts':dict(Counter(str(g['widths'][0]) for g in gs)),
   'connected_topology_count':sum(len(g['components_before'])==1 for g in gs),
   'component_count_distribution':dict(Counter(str(len(g['components_before'])) for g in gs)),
   'minimum_separator_size_counts':dict(Counter(str(g['minimum_separator_size']) for g in gs)),
   'median_search_ms':statistics.median(g['proposal_ns']/1e6 for g in gs),
   'p95_search_ms':float(__import__('numpy').percentile([g['proposal_ns']/1e6 for g in gs],95)),
   'median_rows_per_topology':statistics.median(g['rows_covered'] for g in gs)}
 out={'schema':'LlmTransportVariedTopologySeparatorCensusV1Analysis','gates_pass':not errors,'errors':errors,'checks':x['checks'],'distinct_topology_keys':len(ref),'families':summary,
  'claim_boundary':'Two model exports over one generated text corpus and evaluator-imposed fan-in. Measures graph structure and graph-only minimum separators only; it does not run partitioned inference or estimate natural-task prevalence.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
