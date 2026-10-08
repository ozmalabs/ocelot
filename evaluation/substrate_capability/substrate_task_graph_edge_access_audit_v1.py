#!/usr/bin/env python3
"""Retrospective edge/access audit for three locked task-graph families."""
from __future__ import annotations
import hashlib,json,os,platform,resource,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_task_graph_edge_access_audit_v1.py'
METHOD=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_GRAPH_EDGE_ACCESS_AUDIT_V1_METHOD_20261003.md'
MANIFEST=ROOT/'scripts/substrate_run_manifest.py'
DATA=[
 'evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json',
 'evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json',
 'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json',
 'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json',
 'evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json',
 'evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json',
 'evaluation/reports/substrate_task_graph_structural_census_v1_3_20261003.json',
 'evaluation/reports/substrate_task_graph_structural_census_v1_3_analysis_20261003.json',
 'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3_lock_20261003.json',
 'docs/research/engine_substrate/SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_3_RESULTS_20261003.md',
 'scripts/substrate_bigville_dynamic_link_cut_capture_v1.py',
 'scripts/substrate_connected_conversation_boundary_panel_v1.py',
 'scripts/substrate_discourse_connected_task_census_v2_1.py',
 'runners/dsl/src/access_trace.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/term.rs',
 'seeds/conversation_discourse_state.json','domains/discourse_state.py']
LOCK=ROOT/'evaluation/substrate_capability/substrate_task_graph_edge_access_audit_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_task_graph_edge_access_audit_v1_20261003.json'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def input_lock():
 return [{'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':sha(ROOT/p)} for p in DATA+[RUNNER.relative_to(ROOT).as_posix(),ANALYZER.relative_to(ROOT).as_posix(),METHOD.relative_to(ROOT).as_posix(),MANIFEST.relative_to(ROOT).as_posix()]]
def read(p):return json.loads((ROOT/p).read_text())
def projection(graph):
 ns={int(n['id']) for n in graph['nodes']};adj={n:set() for n in ns}
 for e in graph['edges']:
  a,b=int(e['src']),int(e['tgt'])
  if a in ns and b in ns and a!=b:adj[a].add(b);adj[b].add(a)
 unseen=set(ns);sizes=[]
 while unseen:
  root=min(unseen);unseen.remove(root);stack=[root];size=0
  while stack:
   u=stack.pop();size+=1
   for v in adj[u]&unseen:unseen.remove(v);stack.append(v)
  sizes.append(size)
 return sorted(sizes)
def derived_interaction(graph,owner):
 owner={int(n):int(f) for n,f in owner};boundary={};inter=set();direct=[]
 for e in graph['edges']:
  a,b=int(e['src']),int(e['tgt']);fa,fb=owner.get(a),owner.get(b)
  if fa is not None and fb is not None and fa!=fb:
   direct.append((a,e['type'],b,fa,fb));inter.add(tuple(sorted((fa,fb))))
  elif (fa is None)!=(fb is None):
   frame=fa if fa is not None else fb;node=b if fa is not None else a
   boundary.setdefault(node,set()).add(frame)
 frames=sorted(set(owner.values()))
 for touched in boundary.values():
  touched=sorted(touched)
  for i,a in enumerate(touched):
   for b in touched[i+1:]:inter.add((a,b))
 return {'frames':frames,'interaction_edges':[list(e) for e in sorted(inter)],'direct_cross_frame_edge_count':len(direct),'boundary_node_count':len(boundary),'boundary_incidence_count':sum(map(len,boundary.values()))}
def make_audit():
 big=read(DATA[0]);conv=read(DATA[2]);disc=read(DATA[4]);census=read(DATA[6]);ind=read(DATA[7])
 req(all(big['checks'].values()) and all(conv['checks'].values()) and all(disc['checks'].values()),'upstream capture check failure')
 req(ind['gates_pass'] and census['sources_before']==census['sources_after'],'structural census analyzer/source check failed')
 original_locks=[read(DATA[i])['locked_inputs'] for i in (1,3,5)]
 original_capture_locks={'bigville':big['locked_inputs']==original_locks[0] and big['post_run_inputs']==original_locks[0],
  'conversation':conv['locked_inputs']==original_locks[1] and conv['post_run_inputs']==original_locks[1],
  'discourse':disc['locked_inputs']==original_locks[2] and disc['lock_sha256']==sha(ROOT/DATA[5]),
  'structural_census':census['lock_sha256']==sha(ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3_lock_20261003.json')}
 req(all(original_capture_locks.values()),'upstream capture lock mismatch')
 bsnaps=[];trace_total=Counter();trace_missing=Counter();distinct_access=set()
 for ri,r in enumerate(big['runs']):
  for c in r['checkpoints']:
   g=c['graph'];typed={(int(e['src']),e['type'],int(e['tgt'])) for e in g['edges']}
   access=Counter()
   for uid,kind,node,res,peer,count in c['runtime_access_trace']:
    if kind not in ('term_edge_read','term_edge_attr_read'):continue
    typ=res if kind=='term_edge_read' else None
    if kind=='term_edge_attr_read':
     types={t for a,t,b in typed if a==int(node) and b==int(peer)}
     typ=next(iter(types)) if len(types)==1 else '__ambiguous__'
    key=(kind,typ);access[key]+=int(count);trace_total[key]+=int(count)
    if (int(node),typ,int(peer)) not in typed:trace_missing[key]+=int(count)
    distinct_access.add((kind,typ,int(node),int(peer)))
   bsnaps.append({'run_index':ri,'replicate':r['replicate'],'topology':r['topology'],'checkpoint':c['stage'],
   'projection_components':projection(g),'edge_type_counts':dict(sorted(Counter(e['type'] for e in g['edges']).items())),
    'node_type_counts':dict(sorted(Counter(n['type'] for n in g['nodes']).items())),
    'task_dependency_pair_count':c['partition_metrics']['dependency_pair_count'],'dependency_width_upper_bound':c['partition_metrics']['induced_width_upper_bound'],
    'target_rule_reads_any':r['target_rule_reads_any'],'partition_execution':c['partition_execution'],'trace_dropped':c['trace_dropped'],
    'edge_access_counts':{f'{k[0]}|{k[1]}':v for k,v in sorted(access.items())}})
 convrows=[]
 for r in conv['runs']:
  for ci,c in enumerate(r['cases']):
   derived=derived_interaction(c['final_graph'],c['frame_owner'])
   convrows.append({'replicate':r['replicate'],'case_id':c['case_id'],'requested_goal_count':c.get('requested_goal_count'),'case_index':ci,
   'projection_components':projection(c['final_graph']),'derived_frame_interaction':derived,
    'edge_type_counts':dict(sorted(Counter(e['type'] for e in c['final_graph']['edges']).items())),
    'node_type_counts':dict(sorted(Counter(n['type'] for n in c['final_graph']['nodes']).items())),
    'producer_frame_interaction_edges':c['frame_interaction_edges'],'producer_exact_interaction_treewidth':c['exact_interaction_treewidth'],
    'static_rule_access_captured':False,'concrete_runtime_access_trace_captured':False,'closure_checkpoints':len(c['checkpoints'])})
 discrows=[]
 for ri,r in enumerate(disc['runs']):
  derived=derived_interaction(r['final_graph'],r['frame_owner'])
  traces=[e for cp in r['checkpoints'] for e in cp['trace_events']]
  discrows.append({'arm':r.get('arm',f'run_{ri}'),'projection_components':projection(r['final_graph']),
   'edge_type_counts':dict(sorted(Counter(e['type'] for e in r['final_graph']['edges']).items())),
   'node_type_counts':dict(sorted(Counter(n['type'] for n in r['final_graph']['nodes']).items())),
   'derived_frame_interaction':derived,'producer_frame_interaction_edges':r['frame_interaction_edges'],
   'static_rule_access':r['static_rule_access'],'concrete_trace_event_count':len(traces),
   'concrete_trace_kind_counts':dict(sorted(Counter(e['kind'] for e in traces).items())),
   'trace_dropped':sum(cp['trace_dropped'] for cp in r['checkpoints'])})
 return {'schema':'SubstrateTaskGraphEdgeAccessAuditV1Exploratory','source_lock':input_lock(),
  'upstream_checks':{'bigville':big['checks'],'conversation':conv['checks'],'discourse':disc['checks'],'structural_analysis_gates_pass':ind['gates_pass']},
  'capture_lock_checks':original_capture_locks,
  'bigville':{'snapshots':bsnaps,'edge_access_event_multiplicity':{f'{k[0]}|{k[1]}':v for k,v in sorted(trace_total.items())},
   'trace_to_typed_directed_edge_missing_counts':{f'{k[0]}|{k[1]}':v for k,v in sorted(trace_missing.items())},
   'distinct_observed_access_tuples':len(distinct_access)},
  'connected_conversation':{'snapshots':convrows},'discourse':{'runs':discrows},
  'structural_projection_summary':ind['families'],
  'limitations':['retrospective/exploratory; captures were inspected before this audit was formalized',
   'runtime trace is partial and is not a completeness proof',
   'conversation capture has no static rule access sets or concrete runtime access trace',
   'static rule access signatures are not concrete factor scopes',
   'no partitioned closure or inference semantic parity was evaluated']}
def req(condition,message):
 if not condition:raise SystemExit(message)
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'SubstrateTaskGraphEdgeAccessAuditV1Lock','inputs':input_lock()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=read(LOCK.relative_to(ROOT));before=input_lock();req(lock['inputs']==before,'source drift from lock')
 from scripts.substrate_run_manifest import start_console_capture,finish_console_capture,capture_run_manifest
 run_id='substrate_task_graph_edge_access_audit_v1_20261003';console=start_console_capture(run_id);start=datetime.now(timezone.utc).isoformat();w0=time.perf_counter_ns();c0=time.process_time_ns();audit=make_audit();wall=time.perf_counter_ns()-w0;cpu=time.process_time_ns()-c0;after=input_lock();log=finish_console_capture(console)
 explicit=[p for p in DATA+[RUNNER.relative_to(ROOT).as_posix(),ANALYZER.relative_to(ROOT).as_posix(),METHOD.relative_to(ROOT).as_posix(),MANIFEST.relative_to(ROOT).as_posix(),LOCK.relative_to(ROOT).as_posix()]]
 manifest=capture_run_manifest(run_id=run_id,runner=RUNNER.relative_to(ROOT).as_posix(),protocol_files=[METHOD.relative_to(ROOT).as_posix()],source_files=[ANALYZER.relative_to(ROOT).as_posix(),MANIFEST.relative_to(ROOT).as_posix(),'runners/dsl/src/access_trace.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/term.rs'],data_files=DATA+ [LOCK.relative_to(ROOT).as_posix()],analysis_files=[ANALYZER.relative_to(ROOT).as_posix()],started_utc=start,exit_status=0,stdout_stderr_capture=log)
 checks={'source_stable':before==lock['inputs']==after,'upstream_gates':all(all(v.values()) if isinstance(v,dict) else v for v in audit['upstream_checks'].values()),
  'snapshot_coverage':len(audit['bigville']['snapshots'])==63 and len(audit['connected_conversation']['snapshots'])==12 and len(audit['discourse']['runs'])==3,
  'bigville_observed_edges_match':not any(audit['bigville']['trace_to_typed_directed_edge_missing_counts'].values()),
  'conversation_interactions_reconstructed':all(x['derived_frame_interaction']['interaction_edges']==x['producer_frame_interaction_edges'] for x in audit['connected_conversation']['snapshots']),
  'discourse_interactions_reconstructed':all(x['derived_frame_interaction']['interaction_edges']==x['producer_frame_interaction_edges'] for x in audit['discourse']['runs'])}
 out={'schema':'SubstrateTaskGraphEdgeAccessAuditV1ExploratoryCapture','lock_sha256':sha(LOCK),'sources_before':before,'sources_after':after,'checks':checks,'timing':{'wall_ns':wall,'process_cpu_ns':cpu,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024},'audit':audit,'run_manifest':manifest}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'timing':out['timing']},indent=2));return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
