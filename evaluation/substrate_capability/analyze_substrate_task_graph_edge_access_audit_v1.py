#!/usr/bin/env python3
"""Independent verifier for the retrospective edge/access audit."""
import hashlib,json,statistics
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_task_graph_edge_access_audit_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_task_graph_edge_access_audit_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_task_graph_edge_access_audit_v1_analysis_20261003.json'
BIG='evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json'
CONV='evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json'
DISC='evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json'
CENSUS='evaluation/reports/substrate_task_graph_structural_census_v1_3_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def comps(g):
 ns={int(n['id']) for n in g['nodes']};adj={n:set() for n in ns}
 for e in g['edges']:
  a,b=int(e['src']),int(e['tgt'])
  if a in ns and b in ns and a!=b:adj[a].add(b);adj[b].add(a)
 left=set(ns);sizes=[]
 while left:
  root=min(left);left.remove(root);stack=[root];size=0
  while stack:
   u=stack.pop();size+=1
   for v in adj[u]&left:left.remove(v);stack.append(v)
  sizes.append(size)
 return sorted(sizes)
def interaction(g,owners):
 owners={int(n):int(f) for n,f in owners};boundary={};pairs=set();direct=0
 for e in g['edges']:
  a,b=int(e['src']),int(e['tgt']);fa,fb=owners.get(a),owners.get(b)
  if fa is not None and fb is not None and fa!=fb:direct+=1;pairs.add(tuple(sorted((fa,fb))))
  elif (fa is None)!=(fb is None):
   frame=fa if fa is not None else fb;node=b if fa is not None else a;boundary.setdefault(node,set()).add(frame)
 for fs in boundary.values():
  fs=sorted(fs)
  for i,a in enumerate(fs):
   for b in fs[i+1:]:pairs.add((a,b))
 return {'frames':sorted(set(owners.values())),'interaction_edges':[list(x) for x in sorted(pairs)],'direct_cross_frame_edge_count':direct,'boundary_node_count':len(boundary),'boundary_incidence_count':sum(map(len,boundary.values()))}
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errors=[]
 def req(c,msg):
  if not c:errors.append(msg)
 req(cap['lock_sha256']==sha(LOCK),'audit lock hash mismatch')
 req(cap['sources_before']==lock['inputs']==cap['sources_after'],'audit source drift')
 req(all(cap['checks'].values()),'audit runner gates fail')
 req(all(cap['audit']['capture_lock_checks'].values()),'upstream capture lock mismatch')
 inputs=lock['inputs'];
 for row in inputs:req(sha(ROOT/row['path'])==row['sha256'],'source digest mismatch: '+row['path'])
 big=json.loads((ROOT/BIG).read_text());conv=json.loads((ROOT/CONV).read_text());disc=json.loads((ROOT/DISC).read_text());census=json.loads((ROOT/CENSUS).read_text())
 cin={ (r['family'],r['capture_run'],r['case'],r['checkpoint']):r for r in census['rows']};audit=cap['audit']
 br={(r['run_index'],r['replicate'],r['topology'],r['checkpoint']):r for r in audit['bigville']['snapshots']};expected_big=0;miss=Counter();multi=Counter();proj_comp_match=0
 for ri,r in enumerate(big['runs']):
  for c in r['checkpoints']:
   key=(ri,r['replicate'],r['topology'],c['stage']);row=br.get(key);req(row is not None,'missing Bigville audit row '+str(key))
   if row is None:continue
   g=c['graph'];raw=Counter(e['type'] for e in g['edges']);nodes=Counter(n['type'] for n in g['nodes'])
   req(row['edge_type_counts']==dict(sorted(raw.items())),'Bigville edge type profile mismatch '+str(key));req(row['node_type_counts']==dict(sorted(nodes.items())),'Bigville node type profile mismatch '+str(key))
   req(row['projection_components']==comps(g),'Bigville component profile mismatch '+str(key))
   sr=cin.get(('bigville_dynamic_link',ri,r['topology'],c['stage']));req(sr is not None,'missing structural census row '+str(key))
   if sr:req(sr['component_sizes']==row['projection_components'],'structural census profile disagreement '+str(key));proj_comp_match+=1
   edge_set={(int(e['src']),e['type'],int(e['tgt'])) for e in g['edges']}
   calc=Counter()
   for uid,kind,node,res,peer,count in c['runtime_access_trace']:
    if kind not in ('term_edge_read','term_edge_attr_read'):continue
    if kind=='term_edge_read':typ=res
    else:
     types={t for a,t,b in edge_set if a==int(node) and b==int(peer)};typ=next(iter(types)) if len(types)==1 else '__ambiguous__'
    calc[(kind,typ)]+=int(count);multi[(kind,typ)]+=int(count);expected_big+=int(count)
    if (int(node),typ,int(peer)) not in edge_set:miss[(kind,typ)]+=int(count)
   want={f'{k[0]}|{k[1]}':v for k,v in sorted(calc.items())};req(row['edge_access_counts']==want,'Bigville trace profile mismatch '+str(key))
   req(row['target_rule_reads_any']==r['target_rule_reads_any'],'Bigville reads_any mismatch '+str(key))
   req(c['trace_dropped']==0,'Bigville trace dropped rows '+str(key))
 cv={(x['replicate'],x['case_id'],x['case_index']):x for x in audit['connected_conversation']['snapshots']};expected_cv=0
 for r in conv['runs']:
  for ci,c in enumerate(r['cases']):
   key=(r['replicate'],c['case_id'],ci);row=cv.get(key);req(row is not None,'missing conversation audit row '+str(key))
   if row is None:continue
   g=c['final_graph'];own=c['frame_owner'];d=interaction(g,own)
   req(row['projection_components']==comps(g),'conversation projection mismatch '+str(key))
   req(row['derived_frame_interaction']==d and d['interaction_edges']==c['frame_interaction_edges'],'conversation interaction reconstruction mismatch '+str(key))
   req(row['edge_type_counts']==dict(sorted(Counter(e['type'] for e in g['edges']).items())),'conversation edge type mismatch '+str(key))
   req(row['node_type_counts']==dict(sorted(Counter(n['type'] for n in g['nodes']).items())),'conversation node type mismatch '+str(key))
   req(row['producer_exact_interaction_treewidth']==c['exact_interaction_treewidth'],'conversation width mismatch '+str(key))
   sr=cin.get(('connected_conversation',r['replicate'],f"{c['case_id']}#{ci}",'final'));req(sr is not None,'missing census conversation row '+str(key))
   if sr:req(sr['component_sizes']==row['projection_components'],'conversation structural projection disagreement '+str(key))
   expected_cv+=1
 dr={x['arm']:x for x in audit['discourse']['runs']};expected_disc=0
 for ri,r in enumerate(disc['runs']):
  arm=r.get('arm',f'run_{ri}');row=dr.get(arm);req(row is not None,'missing discourse audit row '+arm)
  if row is None:continue
  g=r['final_graph'];derived=interaction(g,r['frame_owner']);trace=[e for cp in r['checkpoints'] for e in cp['trace_events']]
  req(row['projection_components']==comps(g),'discourse projection mismatch '+arm)
  req(row['derived_frame_interaction']==derived and derived['interaction_edges']==r['frame_interaction_edges'],'discourse interaction reconstruction mismatch '+arm)
  req(row['edge_type_counts']==dict(sorted(Counter(e['type'] for e in g['edges']).items())),'discourse edge type mismatch '+arm)
  req(row['node_type_counts']==dict(sorted(Counter(n['type'] for n in g['nodes']).items())),'discourse node type mismatch '+arm)
  req(row['concrete_trace_event_count']==len(trace),'discourse trace count mismatch '+arm)
  req(row['concrete_trace_kind_counts']==dict(sorted(Counter(e['kind'] for e in trace).items())),'discourse trace kinds mismatch '+arm)
  req(not any(x['reads_any'] or x['writes_any'] for x in r['static_rule_access']),'unexpected discourse wildcard')
  sr=cin.get(('discourse_connected_task',arm,'two_goal_connected_task','final'));req(sr is not None,'missing discourse census row '+arm)
  if sr:req(sr['component_sizes']==row['projection_components'],'discourse structural projection disagreement '+arm)
  expected_disc+=1
 req(expected_big==sum(multi.values()),'Bigville event multiplicity reconciliation failed')
 req(not any(miss.values()),'observed Bigville edge access absent from typed graph')
 manifest=cap.get('run_manifest',{});req(manifest.get('manifest_schema')=='substrate-run-manifest-v1','shared manifest missing')
 explicit=manifest.get('explicit_inputs',{});req(all(x['path'] in explicit and explicit[x['path']].get('exists') for x in inputs),'manifest explicit inputs incomplete')
 log=manifest.get('stdout_stderr_capture') or {};lp=ROOT/log.get('path','missing');req(lp.is_file() and sha(lp)==log.get('sha256'),'parent console log hash mismatch')
 req(manifest.get('hardware',{}).get('cpu_model') is not None and cap['timing']['process_cpu_ns']>0 and cap['timing']['peak_rss_bytes']>0,'CPU/RSS/hardware missing')
 summary={'bigville_snapshots':len(br),'bigville_observed_edge_access_event_multiplicity':expected_big,'bigville_typed_edge_trace_misses':sum(miss.values()),'bigville_distinct_observed_access_tuples':audit['bigville']['distinct_observed_access_tuples'],'bigville_reads_any_runs':sum(bool(r['target_rule_reads_any']) for r in big['runs']),'bigville_partition_refused_snapshots':sum(c['partition_execution']['status']=='refused_wildcard_rule_access' for r in big['runs'] for c in r['checkpoints']),'conversation_snapshots':expected_cv,'conversation_projection_disconnected_snapshots':sum(len(x['projection_components'])>1 for x in cv.values()),'conversation_complete_frame_interaction_graphs':sum(len(x['derived_frame_interaction']['interaction_edges'])==len(x['derived_frame_interaction']['frames'])*(len(x['derived_frame_interaction']['frames'])-1)//2 for x in cv.values()),'conversation_concrete_access_trace_available':False,'discourse_runs':expected_disc,'discourse_concrete_trace_event_count':sum(x['concrete_trace_event_count'] for x in dr.values()),'discourse_static_rule_count':sum(len(r['static_rule_access']) for r in disc['runs']),'discourse_static_wildcard_rule_count':sum(sum(bool(x['reads_any'] or x['writes_any']) for x in r['static_rule_access']) for r in disc['runs']),'discourse_projection_disconnected_runs':sum(len(x['projection_components'])>1 for x in dr.values()),'discourse_complete_frame_interaction_graphs':sum(len(x['derived_frame_interaction']['interaction_edges'])==len(x['derived_frame_interaction']['frames'])*(len(x['derived_frame_interaction']['frames'])-1)//2 for x in dr.values()),'structural_projection_rows_independently_matched':proj_comp_match+expected_cv+expected_disc}
 out={'schema':'SubstrateTaskGraphEdgeAccessAuditV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary,'claim_boundary':'Retrospective descriptive audit. Observed typed edge reads match captured Bigville graph edges; producer refuses partitioning on reads_any. Owner-derived interaction graphs can be complete when full-node projections are disconnected. Conversation concrete access evidence is absent and discourse traces are sparse. No semantic decomposition safety or speed result.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
