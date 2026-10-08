#!/usr/bin/env python3
"""Independent recomputation for articulation frame discovery capture."""
from __future__ import annotations
import collections,hashlib,importlib.util,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_articulation_frame_discovery_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_articulation_frame_discovery_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_articulation_frame_discovery_v1_analysis_20261003.json'
CENSUS=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_items():
 spec=importlib.util.spec_from_file_location('census_independent_v1_3',CENSUS);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.extract_graphs()
def componentize(nodes,edges,removed):
 live=set(nodes)-set(removed);adj={n:set() for n in live}
 for a,b in edges:
  if a in live and b in live:adj[a].add(b);adj[b].add(a)
 out=[]
 while live:
  root=min(live);live.remove(root);stack=[root];comp=[]
  while stack:
   u=stack.pop();comp.append(u)
   for v in adj[u]&live:live.remove(v);stack.append(v)
  out.append(sorted(comp))
 return sorted(out,key=lambda c:(len(c),c))
def discover(nodes,edges):
 adj={n:set() for n in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 disc={};low={};parent={};arts=set();clock=0
 def dfs(u):
  nonlocal clock
  clock+=1;disc[u]=low[u]=clock;children=0
  for v in sorted(adj[u]):
   if v not in disc:
    parent[v]=u;children+=1;dfs(v);low[u]=min(low[u],low[v])
    if (u not in parent and children>1) or (u in parent and low[v]>=disc[u]):arts.add(u)
   elif parent.get(u)!=v:low[u]=min(low[u],disc[v])
 for u in nodes:
  if u not in disc:dfs(u)
 return sorted(arts),componentize(nodes,edges,arts)
def metrics(nodes,edges,owner,arts,parts):
 own={int(n):int(v) for n,v in owner.items() if int(n) in set(nodes)};live=[n for n in own if n not in set(arts)];component={n:i for i,c in enumerate(parts) for n in c};
 groups=collections.Counter(own[n] for n in live);clusters=collections.Counter(component[n] for n in live if n in component);joint=collections.Counter((own[n],component[n]) for n in live if n in component)
 tp=sum(v*(v-1)//2 for v in joint.values());fp=sum(v*(v-1)//2 for v in clusters.values())-tp;fn=sum(v*(v-1)//2 for v in groups.values())-tp
 precision=tp/(tp+fp) if tp+fp else 1.;recall=tp/(tp+fn) if tp+fn else 1.;f1=2*precision*recall/(precision+recall) if precision+recall else 0.
 purity=sum(max(collections.Counter(own[n] for n in c if n in own).values()) for c in parts if any(n in own for n in c))/len(live) if live else None
 same=cross=cut_same=cut_cross=0
 for a,b in edges:
  if a not in own or b not in own:continue
  cut=a in arts or b in arts
  if own[a]==own[b]:same+=1;cut_same+=int(cut)
  else:cross+=1;cut_cross+=int(cut)
 return {'owner_labeled_nodes':len(own),'owner_frames':len(set(own.values())),'surviving_labeled_nodes':len(live),'coverage':len(live)/len(own) if own else 1.,
  'component_purity':purity,'pairwise_tp':tp,'pairwise_fp':fp,'pairwise_fn':fn,'pairwise_precision':precision,'pairwise_recall':recall,'pairwise_f1':f1,
  'annotated_same_owner_edges':same,'same_owner_edges_touching_cut':cut_same,'annotated_cross_owner_edges':cross,'cross_owner_edges_touching_cut':cut_cross,
  'cross_owner_edge_cut_recall':cut_cross/cross if cross else None,'same_owner_edge_cut_rate':cut_same/same if same else None}
def main():
 lock=json.loads(LOCK.read_text());capture=json.loads(CAP.read_text());errs=[]
 if capture.get('lock_sha256')!=sha(LOCK):errs.append('capture lock hash mismatch')
 if capture.get('sources_before')!=lock['sources'] or capture.get('sources_after')!=lock['sources']:errs.append('capture source lock mismatch')
 items=source_items();rows=capture.get('rows',[])
 if len(items)!=78 or len(rows)!=78:errs.append('expected 78 source graph snapshots')
 byfamily=collections.defaultdict(list)
 for ix,(item,row) in enumerate(zip(items,rows)):
  if (row.get('family'),row.get('case'),row.get('checkpoint'),str(row.get('replicate'))) != (item['family'],item['case'],item['checkpoint'],str(item['replicate'])):errs.append(f'row {ix}: source identity mismatch')
  g=item['graph'];nodes=sorted(int(x['id']) for x in g['nodes']);ns=set(nodes);raw=[(int(e['src']),int(e['tgt'])) for e in g['edges']];edges=sorted({tuple(sorted((a,b))) for a,b in raw if a!=b and a in ns and b in ns})
  arts,parts=discover(nodes,edges)
  if arts!=row.get('articulation_nodes'):errs.append(f'row {ix}: articulation mismatch')
  if parts!=row.get('proposed_components'):errs.append(f'row {ix}: component mismatch')
  m=metrics(nodes,edges,item['owners'],arts,parts)
  for k,v in m.items():
   rv=row.get(k)
   if isinstance(v,float) and isinstance(rv,(float,int)):
    if abs(v-rv)>1e-12:errs.append(f'row {ix}: {k} mismatch')
   elif v!=rv:errs.append(f'row {ix}: {k} mismatch')
  byfamily[item['family']].append(row)
 summary={}
 for fam,cell in byfamily.items():
  def stat(k):
   x=[r[k] for r in cell if r.get(k) is not None];return {'min':min(x),'median':statistics.median(x),'max':max(x)} if x else None
  summary[fam]={'graphs':len(cell),'unique_topologies':len({r['graph_sha256'] for r in cell}),
   'coverage':stat('coverage'),'component_purity':stat('component_purity'),'pairwise_precision':stat('pairwise_precision'),
   'pairwise_recall':stat('pairwise_recall'),'pairwise_f1':stat('pairwise_f1'),
   'cross_owner_edge_cut_recall':stat('cross_owner_edge_cut_recall'),'same_owner_edge_cut_rate':stat('same_owner_edge_cut_rate'),
   'median_owner_frames':statistics.median(r['owner_frames'] for r in cell),
   'median_articulation_nodes':statistics.median(len(r['articulation_nodes']) for r in cell),
   'median_scored_components':statistics.median(sum(bool(c['owner_counts']) for c in r['scored_components']) for r in cell)}
 out={'schema':'ArticulationFrameDiscoveryV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'gates_pass':not errs,'errors':errs,'summary':{'graphs':len(rows),'families':summary}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':not errs,'error_count':len(errs),'summary':out['summary']},sort_keys=True));return 0 if not errs else 1
if __name__=='__main__':sys.exit(main())
