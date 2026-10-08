#!/usr/bin/env python3
"""Locked articulation-based frame-proposal benchmark on census-v1.3 graphs."""
from __future__ import annotations
import hashlib,importlib.util,json,platform,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_articulation_frame_discovery_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ARTICULATION_FRAME_DISCOVERY_V1_PREREG_20261003.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_articulation_frame_discovery_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_articulation_frame_discovery_v1_20261003.json'
CENSUS_RUNNER=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3.py'
CENSUS_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_task_graph_structural_census_v1_3.py'
CENSUS_PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_3_RESULTS_20261003.md'
CENSUS_LOCK=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3_lock_20261003.json'
INPUTS=[ROOT/'evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json',ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json',ROOT/'evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json']
INPUT_LOCKS=[ROOT/'evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json',ROOT/'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json',ROOT/'evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json']
def digest(path):
 p=Path(path);return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def sources():
 return {'files':[digest(p) for p in [RUNNER,ANALYZER,PROTOCOL,CENSUS_RUNNER,CENSUS_ANALYZER,CENSUS_PROTOCOL,CENSUS_LOCK,*INPUTS,*INPUT_LOCKS]],'projection':'simple undirected; all nodes, self-loops excluded, duplicate undirected pairs collapsed','proposal':'remove every articulation vertex simultaneously; connected components are proposed frames'}
def census_module():
 spec=importlib.util.spec_from_file_location('locked_census_v1_3',CENSUS_RUNNER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def adjacency(nodes,edges,removed=frozenset()):
 live=set(nodes)-set(removed);adj={v:set() for v in live}
 for a,b in edges:
  if a in live and b in live:adj[a].add(b);adj[b].add(a)
 return adj
def components(nodes,edges,removed=frozenset()):
 adj=adjacency(nodes,edges,removed);left=set(adj);out=[]
 while left:
  root=min(left);left.remove(root);stack=[root];part=[]
  while stack:
   u=stack.pop();part.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  out.append(sorted(part))
 return sorted(out,key=lambda x:(len(x),x))
def articulation_points(nodes,edges):
 adj=adjacency(nodes,edges);disc={};low={};parent={};arts=set();clock=0
 def visit(u):
  nonlocal clock
  clock+=1;disc[u]=low[u]=clock;children=0
  for v in sorted(adj[u]):
   if v not in disc:
    parent[v]=u;children+=1;visit(v);low[u]=min(low[u],low[v])
    if u not in parent and children>1:arts.add(u)
    if u in parent and low[v]>=disc[u]:arts.add(u)
   elif parent.get(u)!=v:low[u]=min(low[u],disc[v])
 for v in sorted(nodes):
  if v not in disc:visit(v)
 return sorted(arts)
def profile(item):
 g=item['graph'];nodes=sorted(int(x['id']) for x in g['nodes']);ns=set(nodes)
 raw=[(int(e['src']),int(e['tgt'])) for e in g['edges']];edges=sorted({tuple(sorted((a,b))) for a,b in raw if a!=b and a in ns and b in ns})
 arts=articulation_points(nodes,edges);parts=components(nodes,edges,set(arts));owner={int(n):int(o) for n,o in item['owners'].items() if int(n) in ns}
 comps=[]
 for ix,part in enumerate(parts):
  labels=[owner[n] for n in part if n in owner]
  if labels:comps.append({'component':ix,'nodes':part,'owner_counts':{str(k):v for k,v in sorted(__import__('collections').Counter(labels).items())}})
 assigned={n:i for i,c in enumerate(comps) for n in c['nodes'] if n in owner}
 surviving=[n for n in owner if n not in arts];counts=[]
 for c in comps:
  cc={int(k):v for k,v in c['owner_counts'].items()};counts.append(cc)
 assigned_n=sum(len(c['nodes']) for c in comps)
 purity_num=sum(max(c.values()) for c in counts) if counts else 0
 tp=fp=fn=0
 from collections import Counter
 frame_groups=Counter(owner[n] for n in surviving);cluster_groups=Counter(assigned[n] for n in surviving if n in assigned);joint=Counter((owner[n],assigned[n]) for n in surviving if n in assigned)
 for (fa,cl),v in joint.items():tp+=v*(v-1)//2
 for v in cluster_groups.values():fp+=v*(v-1)//2
 for v in frame_groups.values():fn+=v*(v-1)//2
 fp-=tp;fn-=tp
 precision=tp/(tp+fp) if tp+fp else (1.0 if tp==0 else 0.0);recall=tp/(tp+fn) if tp+fn else 1.0;f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
 cross_edges=same_edges=cut_cross=cut_same=0
 for a,b in edges:
  if a not in owner or b not in owner:continue
  if owner[a]==owner[b]:same_edges+=1;cut_same+=int(a in arts or b in arts)
  else:cross_edges+=1;cut_cross+=int(a in arts or b in arts)
 return {'family':item['family'],'capture_run':str(item['capture_run']),'replicate':str(item['replicate']),'case':item['case'],'checkpoint':item['checkpoint'],
  'graph_sha256':hashlib.sha256(json.dumps([nodes,edges],separators=(',',':')).encode()).hexdigest(),'nodes':len(nodes),'edges':len(edges),
  'owner_labeled_nodes':len(owner),'owner_frames':len(set(owner.values())),'articulation_nodes':arts,'proposed_components':parts,'scored_components':comps,
  'surviving_labeled_nodes':len(surviving),'coverage':len(surviving)/len(owner) if owner else 1.0,
  'component_purity':purity_num/len(surviving) if surviving else None,'pairwise_tp':tp,'pairwise_fp':fp,'pairwise_fn':fn,
  'pairwise_precision':precision,'pairwise_recall':recall,'pairwise_f1':f1,
  'annotated_same_owner_edges':same_edges,'same_owner_edges_touching_cut':cut_same,
  'annotated_cross_owner_edges':cross_edges,'cross_owner_edges_touching_cut':cut_cross,
  'cross_owner_edge_cut_recall':cut_cross/cross_edges if cross_edges else None,
  'same_owner_edge_cut_rate':cut_same/same_edges if same_edges else None}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing lock/capture')
  LOCK.write_text(json.dumps({'schema':'ArticulationFrameDiscoveryV1Lock','sources':sources(),'planned_rows':78},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 mod=census_module();items=mod.extract_graphs();rows=[profile(x) for x in items];after=sources()
 capture={'schema':'ArticulationFrameDiscoveryV1Capture','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources_before':before,'sources_after':after,'checks':{'source_stable':before==after==lock['sources'],'row_count':len(rows)==78,'families':sorted(set(r['family'] for r in rows)),'unique_graphs':len(set(r['graph_sha256'] for r in rows))},'rows':rows}
 OUT.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':capture['checks']},sort_keys=True));return 0 if all((capture['checks']['source_stable'],capture['checks']['row_count'],len(capture['checks']['families'])==3)) else 1
if __name__=='__main__':raise SystemExit(main())
