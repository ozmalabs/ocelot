#!/usr/bin/env python3
"""Manifest-backed structural census over three locked task graph captures."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time,statistics
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_task_graph_structural_census_v1_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_1_AMENDMENT_20261003.md'
MANIFEST=ROOT/'scripts/substrate_run_manifest.py';WIDTH=ROOT/'domains/graph_treewidth.py'
INPUTS={
 'bigville':ROOT/'evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json',
 'conversation':ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json',
 'discourse':ROOT/'evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json'}
LOCKS={
 'bigville':ROOT/'evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json',
 'conversation':ROOT/'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json',
 'discourse':ROOT/'evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json'}
REPORTS={
 'bigville':ROOT/'docs/research/engine_substrate/SUBSTRATE_BIGVILLE_DYNAMIC_LINK_CUT_CAPTURE_V1_RESULTS_20260926.md',
 'conversation':ROOT/'docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_BOUNDARY_PANEL_V1_RESULTS_20260926.md',
 'discourse':ROOT/'docs/research/engine_substrate/SUBSTRATE_DISCOURSE_CONNECTED_TASK_CENSUS_V2_1_RESULTS_20260926.md'}
V1_RUNNER=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1.py'
V1_LOCK=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_lock_20261003.json'
V1_PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_PREREG_20261003.md'
V1_FAILURE_LOG=ROOT/'evaluation/run_logs/substrate_task_graph_structural_census_v1_20261003.stdout_stderr.log'
LOCK=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_task_graph_structural_census_v1_1_20261003.json'
def digest(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sources():
 paths=[RUNNER,ANALYZER,PROTOCOL,MANIFEST,WIDTH,V1_RUNNER,V1_LOCK,V1_PREREG,V1_FAILURE_LOG]
 for k in INPUTS:paths.extend((INPUTS[k],LOCKS[k],REPORTS[k]))
 return {'artifacts':[digest(p) for p in paths],'planned_graphs':{'bigville':63,'conversation':12,'discourse':3},'projection':'simple undirected; all node IDs, self-loops excluded from adjacency, duplicate undirected pairs collapsed','separator_scope':'exact disconnected/one-vertex separators only; no search above size 1','width_method':'domains.graph_treewidth.min_fill_upper_bound','run_manifest':'substrate-run-manifest-v1'}
def nid(v):return int(v)
def extract_graphs():
 graphs=[]
 b=json.loads(INPUTS['bigville'].read_text())
 for ri,r in enumerate(b['runs']):
  owners={nid(n):int(f) for n,f in r.get('runtime_node_frame',[])}
  for ci,c in enumerate(r['checkpoints']):
   graphs.append({'family':'bigville_dynamic_link','capture_run':ri,'replicate':r['replicate'],'case':r['topology'],'checkpoint':c['stage'],'graph':c['graph'],'owners':owners})
 v=json.loads(INPUTS['conversation'].read_text())
 for r in v['runs']:
  for c in r['cases']:
   graphs.append({'family':'connected_conversation','capture_run':r['replicate'],'replicate':r['replicate'],'case':c['case_id'],'checkpoint':'final','graph':c['final_graph'],'owners':{nid(n):int(f) for n,f in c.get('frame_owner',[])}})
 d=json.loads(INPUTS['discourse'].read_text())
 for ri,r in enumerate(d['runs']):
  run_id=r.get('replicate') or r.get('arm') or f'run_{ri}'
  graphs.append({'family':'discourse_connected_task','capture_run':run_id,'replicate':run_id,'case':'two_goal_connected_task','checkpoint':'final','graph':r['final_graph'],'owners':{nid(n):int(f) for n,f in r.get('frame_owner',[])}})
 return graphs
def components(nodes,edges,removed=frozenset()):
 left=set(nodes)-set(removed);adj={v:set() for v in left}
 for a,b in edges:
  if a in left and b in left:adj[a].add(b);adj[b].add(a)
 parts=[]
 while left:
  root=min(left);left.remove(root);stack=[root];part=[]
  while stack:
   u=stack.pop();part.append(u)
   for v in adj[u]&left:left.remove(v);stack.append(v)
  parts.append(sorted(part))
 return sorted(parts,key=lambda x:(len(x),x))
def articulation_profile(nodes,edges,base_components):
 adj={v:set() for v in nodes}
 for a,b in edges:
  if a!=b:adj[a].add(b);adj[b].add(a)
 disc={};low={};parent={};arts=set();clock=0
 def visit(u):
  nonlocal clock
  clock+=1;disc[u]=low[u]=clock;children=0
  for v in adj[u]:
   if v not in disc:
    parent[v]=u;children+=1;visit(v);low[u]=min(low[u],low[v])
    if u not in parent and children>1:arts.add(u)
    if u in parent and low[v]>=disc[u]:arts.add(u)
   elif parent.get(u)!=v:low[u]=min(low[u],disc[v])
 for v in nodes:
  if v not in disc:visit(v)
 cut_largest=[]
 for v in arts:
  sizes=[len(c) for c in components(nodes,edges,{v})]
  cut_largest.append(max(sizes,default=0))
 return sorted(arts),cut_largest
def profile(item,cache):
 g=item['graph'];nodes=sorted(nid(x['id']) for x in g['nodes']);raw_edges=[(nid(e['src']),nid(e['tgt'])) for e in g['edges']]
 node_set=set(nodes);valid=[(a,b) for a,b in raw_edges if a in node_set and b in node_set];loops=sum(a==b for a,b in valid);simple=sorted(set(tuple(sorted((a,b))) for a,b in valid if a!=b));adj={v:set() for v in nodes}
 for a,b in simple:adj[a].add(b);adj[b].add(a)
 comps=components(nodes,simple);arts,cut_largest=articulation_profile(nodes,simple,comps);owners=item['owners'];known={v:o for v,o in owners.items() if v in node_set}
 crossings=0;known_unknown=0
 for a,b in simple:
  oa=known.get(a);ob=known.get(b)
  if oa is not None and ob is not None and oa!=ob:crossings+=1
  elif (oa is None)!=(ob is None):known_unknown+=1
 gh=hashlib.sha256(json.dumps([nodes,simple],separators=(',',':')).encode()).hexdigest()
 if gh not in cache:
  from domains.graph_treewidth import min_fill_upper_bound
  t=time.perf_counter_ns();bound=min_fill_upper_bound(nodes,simple);width_ns=time.perf_counter_ns()-t
  cache[gh]={'upper_bound':int(bound['treewidth']),'elimination_order':[nid(v) for v in bound['elimination_order']],'minfill_ns':width_ns,'exact':False}
 structural=cache[gh];connected=len(comps)==1
 if not connected:separator={'status':'exact_disconnected','minimum_size':0}
 elif arts:separator={'status':'exact_articulation','minimum_size':1,'articulation_count':len(arts)}
 else:separator={'status':'not_searched_above_one','minimum_size_lower_bound':2}
 return {'family':item['family'],'capture_run':item['capture_run'],'replicate':item['replicate'],'case':item['case'],'checkpoint':item['checkpoint'],'graph_sha256':gh,'node_count':len(nodes),'raw_edge_count':len(raw_edges),'simple_undirected_edge_count':len(simple),'self_loop_count':loops,'duplicate_pair_count':len(valid)-loops-len(simple),'density':(2*len(simple)/(len(nodes)*(len(nodes)-1))) if len(nodes)>1 else 0.0,'degree_min':min((len(adj[v]) for v in nodes),default=0),'degree_median':statistics.median(len(adj[v]) for v in nodes) if nodes else 0,'degree_max':max((len(adj[v]) for v in nodes),default=0),'component_sizes':[len(c) for c in comps],'articulation_nodes':arts,'articulation_count':len(arts),'articulation_cut_largest_component_min':min(cut_largest) if cut_largest else None,'articulation_cut_largest_component_median':statistics.median(cut_largest) if cut_largest else None,'separator_result':separator,'owner_labeled_node_count':len(known),'owner_labeled_frame_count':len(set(known.values())),'known_owner_crossing_edges':crossings,'known_unknown_owner_edges':known_unknown,'minfill_treewidth_upper_bound':structural['upper_bound'],'minfill_elimination_order':structural['elimination_order'],'minfill_elapsed_ns':structural['minfill_ns'],'minfill_cache_hit':cache[gh].get('_seen',0)>0,'minfill_unique_topology_ns':structural['minfill_ns']}
def upstream_checks():
 return {k:all(json.loads(INPUTS[k].read_text()).get('checks',{}).values()) for k in INPUTS}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing lock/capture')
  LOCK.write_text(json.dumps({'schema':'SubstrateTaskGraphStructuralCensusV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 checks=upstream_checks()
 if not all(checks.values()):raise SystemExit('upstream capture has a failed gate')
 from scripts.substrate_run_manifest import start_console_capture,finish_console_capture,capture_run_manifest
 run_id='substrate_task_graph_structural_census_v1_1_20261003';console=start_console_capture(run_id);started=datetime.now(timezone.utc).isoformat();wall0=time.perf_counter_ns();cpu0=time.process_time_ns();cache={};rows=[]
 for ix,item in enumerate(extract_graphs(),1):
  row=profile(item,cache);seen=cache[row['graph_sha256']].get('_seen',0);row['minfill_cache_hit']=seen>0;cache[row['graph_sha256']]['_seen']=seen+1;rows.append(row)
  if ix%10==0:print(f'processed {ix}/78 graph snapshots; unique topologies={len(cache)}',flush=True)
 wall_ns=time.perf_counter_ns()-wall0;cpu_ns=time.process_time_ns()-cpu0;after=sources();console_record=finish_console_capture(console)
 manifest=capture_run_manifest(run_id=run_id,runner=RUNNER.relative_to(ROOT).as_posix(),protocol_files=[PROTOCOL.relative_to(ROOT).as_posix()],source_files=[ANALYZER.relative_to(ROOT).as_posix(),WIDTH.relative_to(ROOT).as_posix(),MANIFEST.relative_to(ROOT).as_posix()],data_files=[*(p.relative_to(ROOT).as_posix() for p in INPUTS.values()),*(p.relative_to(ROOT).as_posix() for p in LOCKS.values()),*(p.relative_to(ROOT).as_posix() for p in REPORTS.values()),V1_RUNNER.relative_to(ROOT).as_posix(),V1_LOCK.relative_to(ROOT).as_posix(),V1_PREREG.relative_to(ROOT).as_posix(),V1_FAILURE_LOG.relative_to(ROOT).as_posix(),LOCK.relative_to(ROOT).as_posix()],analysis_files=[ANALYZER.relative_to(ROOT).as_posix()],started_utc=started,exit_status=0,stdout_stderr_capture=console_record)
 out={'schema':'SubstrateTaskGraphStructuralCensusV1_1Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources_before':before,'sources_after':after,'upstream_checks':checks,'checks':{'source_stable':before==lock['sources']==after,'upstream_gates':all(checks.values()),'planned_coverage':len(rows)==78,'three_families':set(r['family'] for r in rows)=={'bigville_dynamic_link','connected_conversation','discourse_connected_task'},'minfill_certificates_present':all(len(r['minfill_elimination_order'])==r['node_count'] for r in rows),'valid_separator_scope':all(r['separator_result']['status'] in ('exact_disconnected','exact_articulation','not_searched_above_one') for r in rows)},'timing':{'wall_ns':wall_ns,'process_cpu_ns':cpu_ns,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'unique_graph_topologies':len(cache)},'rows':rows,'run_manifest':manifest}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':out['checks'],'timing':out['timing']},indent=2));return int(not all(out['checks'].values()))
if __name__=='__main__':raise SystemExit(main())
