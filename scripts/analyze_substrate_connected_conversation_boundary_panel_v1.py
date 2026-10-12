#!/usr/bin/env python3
"""Independent structural and replication audit for the conversation panel."""
import hashlib,json,statistics
from itertools import combinations,permutations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json';LOCK=ROOT/'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_analysis_20260926.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def exact_width(vertices,edges):
 best=len(vertices)
 for order in permutations(vertices):
  adj={v:set() for v in vertices}
  for a,b in edges:adj[a].add(b);adj[b].add(a)
  width=0
  for v in order:
   ns=adj[v];width=max(width,len(ns))
   for a,b in combinations(ns,2):adj[a].add(b);adj[b].add(a)
   for x in ns:adj[x].discard(v)
  best=min(best,width)
 return best
def reconstruct(c):
 owner={int(n):int(f) for n,f in c['frame_owner']};direct=[];boundary={};inter=set()
 for e in c['final_graph']['edges']:
  a,b=int(e['src']),int(e['tgt']);fa,fb=owner.get(a),owner.get(b)
  if fa is not None and fb is not None and fa!=fb:direct.append((a,e['type'],b,fa,fb));inter.add(tuple(sorted((fa,fb))))
  elif (fa is None)!=(fb is None):
   f=fa if fa is not None else fb;node=b if fa is not None else a;boundary.setdefault(node,set()).add(f)
 for fs in boundary.values():inter.update(combinations(sorted(fs),2))
 frames=sorted(set(owner.values()));sizes={str(f):sum(x==f for x in owner.values()) for f in frames}
 return owner,frames,sizes,direct,boundary,inter
def main():
 p=json.loads(RAW.read_text());lk=json.loads(LOCK.read_text());runs=p['runs'];cases=[c for r in runs for c in r['cases']]
 expected=[('common_ground_stress',None,10,2,4,[5,1,1,5]),('concurrent_goals',2,8,2,2,[5,5]),('concurrent_goals',4,16,4,4,[5]*4),('concurrent_goals',8,32,8,8,[5]*8)]
 checks={'schema_and_12_cases':p.get('schema_version')==1 and len(cases)==12,'source_lock_and_capture':p['locked_inputs']==lk['locked_inputs'] and p['post_run_inputs']==p['locked_inputs'] and p['lock_sha256']==sha(LOCK),'three_fresh_workers':len(runs)==3 and len({r['pid'] for r in runs})==3 and all(r['started_inputs']==p['locked_inputs']==r['finished_inputs'] for r in runs),'complete_replicated_workloads':all(sum(c['case_id']==cid and c.get('requested_goal_count')==n for c in cases)==3 for cid,n,*_ in expected),'event_frame_and_goal_ownership':True,'fixed_point_and_task_lifecycles':True,'replica_graph_counter_parity':True,'reconstructed_edges_boundaries_and_widths':True,'positive_counters_and_timings':all(c['total_candidate_pairs']>=0 and c['total_term_evaluations']>=0 and c['peak_rss_kib']>0 for c in cases)}
 groups=[]
 for cid,n,ev_count,g_count,frame_count,expected_sizes in expected:
  xs=[c for c in cases if c['case_id']==cid and c.get('requested_goal_count')==n]
  if not all(c['event_count']==ev_count and c['goal_count']==g_count and c['frame_count']==frame_count and sorted(c['frame_sizes'].values())==sorted(expected_sizes) and len(c['frame_owner'])==ev_count+g_count for c in xs):checks['event_frame_and_goal_ownership']=False
  if not all(all(cp['closure'].get('status')=='fixed_point' for cp in c['checkpoints']) and len(c['checkpoints'])==ev_count and all(g['status']=='resolved' for g in c['goals']) for c in xs):checks['fixed_point_and_task_lifecycles']=False
  for c in xs:
   expected_trans=([4,5,6],[7,8,9]) if cid=='common_ground_stress' else [list(range(n+3*i,n+3*i+3)) for i in range(n)]
   actual=[g['transition_indices'] for g in sorted(c['goals'],key=lambda g:g['frame'])]
   if actual!=list(expected_trans):checks['fixed_point_and_task_lifecycles']=False
  if len({c['final_graph_digest'] for c in xs})!=1 or len({json.dumps([(z['graph_digest'],z['candidate_pairs'],z['term_evaluations']) for z in c['checkpoints']],sort_keys=True) for c in xs})!=1:checks['replica_graph_counter_parity']=False
  rec=[reconstruct(c) for c in xs]
  if any(c['frame_sizes']!=sizes or len(c['direct_cross_frame_edges'])!=len(direct) or len(c['boundary_nodes_by_frames'])!=len(boundary) or c['frame_interaction_edges']!=[list(x) for x in sorted(inter)] or c['exact_interaction_treewidth']!=exact_width(frames,inter) for c,(owner,frames,sizes,direct,boundary,inter) in zip(xs,rec)):checks['reconstructed_edges_boundaries_and_widths']=False
  groups.append({'case_id':cid,'requested_goals':n,'replicates':len(xs),'events':ev_count,'frames':frame_count,'frame_sizes':expected_sizes,'median_direct_cross_frame_edges':statistics.median(len(x['direct_cross_frame_edges']) for x in xs),'median_boundary_nodes':statistics.median(len(x['boundary_nodes_by_frames']) for x in xs),'median_boundary_incidences':statistics.median(x['boundary_incidence_count'] for x in xs),'interaction_treewidth':xs[0]['exact_interaction_treewidth'],'median_candidate_pairs':statistics.median(x['total_candidate_pairs'] for x in xs),'median_term_evaluations':statistics.median(x['total_term_evaluations'] for x in xs),'median_peak_rss_mib':statistics.median(x['peak_rss_kib'] for x in xs)/1024})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'case_count':len(cases),'summary_by_workload':groups,'claim_boundary':p['claim_boundary']};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
