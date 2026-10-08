#!/usr/bin/env python3
"""Independent graph-profile and min-fill-certificate audit."""
import hashlib,itertools,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_task_graph_structural_census_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_task_graph_structural_census_v1_1_analysis_20261003.json'
INPUTS={
 'bigville':ROOT/'evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json',
 'conversation':ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json',
 'discourse':ROOT/'evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def graphs():
 b=json.loads(INPUTS['bigville'].read_text());out=[]
 for r in b['runs']:
  own={int(n):int(f) for n,f in r.get('runtime_node_frame',[])}
  for c in r['checkpoints']:out.append(('bigville_dynamic_link',r['replicate'],r['topology'],c['stage'],c['graph'],own))
 v=json.loads(INPUTS['conversation'].read_text())
 for r in v['runs']:
  for c in r['cases']:out.append(('connected_conversation',r['replicate'],c['case_id'],'final',c['final_graph'],{int(n):int(f) for n,f in c.get('frame_owner',[])}))
 d=json.loads(INPUTS['discourse'].read_text())
 for ri,r in enumerate(d['runs']):out.append(('discourse_connected_task',r.get('replicate') or r.get('arm') or f'run_{ri}','two_goal_connected_task','final',r['final_graph'],{int(n):int(f) for n,f in r.get('frame_owner',[])}))
 return out
def graph_metrics(g,owners):
 ns=sorted(int(x['id']) for x in g['nodes']);nset=set(ns);raw=[(int(e['src']),int(e['tgt'])) for e in g['edges'] if int(e['src']) in nset and int(e['tgt']) in nset];loops=sum(a==b for a,b in raw);es=sorted(set(tuple(sorted((a,b))) for a,b in raw if a!=b));adj={v:set() for v in ns}
 for a,b in es:adj[a].add(b);adj[b].add(a)
 unseen=set(ns);parts=[]
 while unseen:
  root=min(unseen);unseen.remove(root);stack=[root];q=[]
  while stack:
   u=stack.pop();q.append(u)
   for v in adj[u]&unseen:unseen.remove(v);stack.append(v)
  parts.append(q)
 parts.sort(key=lambda c:(len(c),sorted(c)));arts=[];cut_max=[]
 for base in parts:
  for v in base:
   remaining=set(base);remaining.remove(v);cc=0
   while remaining:
    root=min(remaining);remaining.remove(root);stack=[root];cc+=1
    while stack:
     u=stack.pop()
     for w in adj[u]&remaining:remaining.remove(w);stack.append(w)
   if cc>1:
    arts.append(v);cut_max.append(cc)
  # Cut balance is checked only for articulation nodes, independently of original components.
 cut_largest=[]
 for v in arts:
  remaining=set(ns);remaining.remove(v);sizes=[]
  while remaining:
   root=min(remaining);remaining.remove(root);stack=[root];size=0
   while stack:
    u=stack.pop();size+=1
    for w in adj[u]&remaining:remaining.remove(w);stack.append(w)
   sizes.append(size)
  cut_largest.append(max(sizes,default=0))
 crossings=known_unknown=0;labelled={v:f for v,f in owners.items() if v in nset}
 for a,b in es:
  oa=labelled.get(a);ob=labelled.get(b)
  if oa is not None and ob is not None and oa!=ob:crossings+=1
  elif (oa is None)!=(ob is None):known_unknown+=1
 canonical=hashlib.sha256(json.dumps([ns,es],separators=(',',':')).encode()).hexdigest();degs=sorted(len(adj[v]) for v in ns)
 return {'graph_sha256':canonical,'node_count':len(ns),'raw_edge_count':len(raw),'simple_undirected_edge_count':len(es),'self_loop_count':loops,'duplicate_pair_count':len(raw)-loops-len(es),'density':(2*len(es)/(len(ns)*(len(ns)-1))) if len(ns)>1 else 0.0,'degree_min':degs[0] if degs else 0,'degree_median':statistics.median(degs) if degs else 0,'degree_max':degs[-1] if degs else 0,'component_sizes':sorted([len(c) for c in parts]),'articulation_nodes':sorted(arts),'articulation_count':len(arts),'articulation_cut_largest_component_min':min(cut_largest) if cut_largest else None,'articulation_cut_largest_component_median':statistics.median(cut_largest) if cut_largest else None,'owner_labeled_node_count':len(labelled),'owner_labeled_frame_count':len(set(labelled.values())),'known_owner_crossing_edges':crossings,'known_unknown_owner_edges':known_unknown}
def cert_width(nodes,edges,order):
 adj={v:set() for v in nodes}
 for a,b in edges:adj[a].add(b);adj[b].add(a)
 remaining=set(nodes);width=0
 for v in order:
  nbr=adj[v]&remaining;width=max(width,len(nbr));nbr=list(nbr)
  for i,a in enumerate(nbr):
   for b in nbr[i+1:]:adj[a].add(b);adj[b].add(a)
  remaining.remove(v)
 return width
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errors=[]
 def req(c,msg):
  if not c:errors.append(msg)
 req(cap['lock_sha256']==sha(LOCK),'lock hash mismatch');req(cap['sources_before']==lock['sources']==cap['sources_after'],'source drift');req(all(cap['checks'].values()),'runner gates fail')
 req(all(all(json.loads(INPUTS[k].read_text())['checks'].values()) for k in INPUTS),'upstream checks fail')
 source_graphs=graphs();rows=cap['rows'];req(len(source_graphs)==78 and len(rows)==78,'coverage mismatch');index={(r['family'],r.get('capture_run',r['replicate']),r['case'],r['checkpoint']):r for r in rows};by=defaultdict(list);hash_width={}
 for family,rep,case,stage,g,owners in source_graphs:
  key=(family,rep,case,stage);r=index.get(key);req(r is not None,'missing row '+str(key))
  if r is None:continue
  m=graph_metrics(g,owners)
  for field,value in m.items():req(r.get(field)==value,f'{key} profile mismatch: {field}')
  order=[int(v) for v in r['minfill_elimination_order']];nodes=sorted(int(x['id']) for x in g['nodes']);edges=sorted(set(tuple(sorted((int(e['src']),int(e['tgt'])))) for e in g['edges'] if int(e['src'])!=int(e['tgt'])))
  width=cert_width(nodes,edges,order);req(len(order)==len(nodes) and set(order)==set(nodes),'order is not a permutation '+str(key));req(width==r['minfill_treewidth_upper_bound'],'min-fill width certificate mismatch '+str(key));hash_width[r['graph_sha256']]=width;by[family].append(r)
 req(set(index)=={(a,b,c,d) for a,b,c,d,_,_ in source_graphs},'extra output rows')
 manifest=cap.get('run_manifest',{});req(manifest.get('manifest_schema')=='substrate-run-manifest-v1','shared manifest missing')
 explicit=manifest.get('explicit_inputs',{});req(all(p in explicit and explicit[p].get('exists') for p in [lock['sources']['artifacts'][i]['path'] for i in range(len(lock['sources']['artifacts']))]),'manifest explicit input coverage incomplete')
 log=manifest.get('stdout_stderr_capture') or {};lp=ROOT/log.get('path','missing');req(lp.is_file() and sha(lp)==log.get('sha256'),'console log missing/hash mismatch')
 req(manifest.get('hardware',{}).get('cpu_model') is not None and cap['timing'].get('process_cpu_ns') is not None and cap['timing'].get('peak_rss_bytes')>0,'hardware/CPU/RSS record incomplete')
 summary={}
 for fam,rs in sorted(by.items()):
  unique={r['graph_sha256']:r for r in rs};cats=Counter(r['separator_result']['status'] for r in rs)
  summary[fam]={'snapshots':len(rs),'distinct_graph_topologies':len(unique),'node_count_min_median_max':[min(r['node_count'] for r in rs),statistics.median(r['node_count'] for r in rs),max(r['node_count'] for r in rs)],'edge_count_min_median_max':[min(r['simple_undirected_edge_count'] for r in rs),statistics.median(r['simple_undirected_edge_count'] for r in rs),max(r['simple_undirected_edge_count'] for r in rs)],'separator_status_counts':dict(cats),'median_articulation_count':statistics.median(r['articulation_count'] for r in rs),'max_articulation_count':max(r['articulation_count'] for r in rs),'minfill_upper_bound_min_median_max':[min(r['minfill_treewidth_upper_bound'] for r in rs),statistics.median(r['minfill_treewidth_upper_bound'] for r in rs),max(r['minfill_treewidth_upper_bound'] for r in rs)],'known_owner_crossing_min_median_max':[min(r['known_owner_crossing_edges'] for r in rs),statistics.median(r['known_owner_crossing_edges'] for r in rs),max(r['known_owner_crossing_edges'] for r in rs)],'minfill_unique_topology_total_ms':sum(r['minfill_unique_topology_ns'] for r in unique.values())/1e6}
 out={'schema':'SubstrateTaskGraphStructuralCensusV1Analysis','gates_pass':not errors,'errors':errors,'checks':cap['checks'],'families':summary,'total_snapshots':len(rows),'distinct_graph_topologies':len(hash_width),'manifest_schema':manifest.get('manifest_schema'),'claim_boundary':'Three prior source-locked authored/generated task graph families; simple undirected structural projection only. No task-fidelity inference-factor claim, semantic partition parity, natural-use prevalence, or native partitioned execution.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
