#!/usr/bin/env python3
"""Independently verify the multi-task episode ownership capture."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/'evaluation/reports/multi_task_episode_ownership_v1_20261004.json'
OUT=ROOT/'evaluation/reports/multi_task_episode_ownership_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in {'ts','runtime_s'}}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
def main():
 x=json.loads(CAP.read_text());runs=x['runs']; checks={}
 checks['capture_schema']=x.get('schema')=='MultiTaskEpisodeOwnershipV1'
 checks['capture_runner_hash_current']=hashlib.sha256((ROOT/'evaluation/substrate_capability/multi_task_episode_ownership_v1.py').read_bytes()).hexdigest()==x['locked_inputs']['runner_sha256']
 checks['protocol_hash_current']=hashlib.sha256((ROOT/'docs/research/engine_substrate/SUBSTRATE_MULTI_TASK_EPISODE_OWNERSHIP_V1_PREREG_20261004.md').read_bytes()).hexdigest()==x['locked_inputs']['protocol_sha256']
 checks['base_runner_hash_current']=hashlib.sha256((ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py').read_bytes()).hexdigest()==x['locked_inputs']['base_harvest_runner_sha256']
 checks['exactly_two_runs']=len(runs)==2
 checks['worker_lock_stability']=all(r['locked_inputs']==x['locked_inputs']==r['post_run_inputs'] for r in runs)
 per=[]
 for i,r in enumerate(runs):
  graph=r['graph'];nodes={int(n['id']):n for n in graph['nodes']};edges=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']]
  checks[f'run_{i}_node_edge_counts']=len(nodes)==r['graph_summary']['nodes'] and len(edges)==r['graph_summary']['edges']
  dg=hashlib.sha256(json.dumps(clean(graph),sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
  checks[f'run_{i}_normalized_digest']=dg==r['graph_summary']['structural_sha256']
  owner=[];reconstructed=[]
  for t in r['turns']:
   root=t['message_id'];goals=set()
   for a,rel,b in edges:
    if rel=='comprehends':
     if a==root and b in nodes and nodes[b]['type']=='Goal':goals.add(b)
     if b==root and a in nodes and nodes[a]['type']=='Goal':goals.add(a)
   events=set()
   for gid in goals:
    v=nodes[gid].get('attrs',{}).get('origin_event')
    eid=int(v['__nid__']) if isinstance(v,dict) and '__nid__' in v else (int(v) if isinstance(v,int) else None)
    if eid in nodes and nodes[eid]['type']=='DiscourseEvent':events.add(eid)
   for a,rel,b in edges:
    if rel=='for_goal':
     if a in nodes and nodes[a]['type']=='DiscourseEvent' and b in goals:events.add(a)
     if b in nodes and nodes[b]['type']=='DiscourseEvent' and a in goals:events.add(b)
   owned=({root} if root in nodes else set())|goals|events;owner.append(owned)
   reconstructed.append({'turn':len(reconstructed),'condition':t['condition'],'message_id':root,'goal_ids':sorted(goals),'event_ids':sorted(events),'owned_node_ids':sorted(owned),'owned_node_count':len(owned),'owned_types':dict(sorted(Counter(nodes[n]['type'] for n in owned).items()))})
  checks[f'run_{i}_owner_projection_recomputed']=reconstructed==r['owner_projection']
  owner_of={n:j for j,s in enumerate(owner) for n in s};cross=[[a,rel,b] for a,rel,b in edges if a in owner_of and b in owner_of and owner_of[a]!=owner_of[b]]
  checks[f'run_{i}_cross_edges_recomputed']=cross==r['cross_owner_edges']
  cross_types=Counter(rel for _,rel,_ in cross)
  per.append({'replicate':r['replicate'],'graph':r['graph_summary'],'turns':[{'condition':t['condition'],'reply':t['reply'],'route':t['route'],'owned_count':len(s),'goal_count':len(next(p for p in reconstructed if p['condition']==t['condition'])['goal_ids'])} for t,s in zip(r['turns'],owner)],'cross_owner_edge_count':len(cross),'cross_owner_edge_types':dict(sorted(cross_types.items()))})
 checks['structural_reproduction']=len({r['graph_summary']['structural_sha256'] for r in runs})==1
 checks['normalized_graph_objects_equal']=all(clean(runs[0]['graph'])==clean(r['graph']) for r in runs[1:])
 diff_nodes=[]
 for a,b in zip(runs[0]['graph']['nodes'],runs[1]['graph']['nodes']):
  if a!=b:diff_nodes.append({'id':a['id'],'differing_attrs':sorted(k for k in set(a.get('attrs',{}))|set(b.get('attrs',{})) if a.get('attrs',{}).get(k)!=b.get('attrs',{}).get(k))})
 checks['task_outcomes_reproduce']=len({json.dumps([{k:t[k] for k in ('condition','route','reply','error')} for t in r['turns']],sort_keys=True) for r in runs})==1
 checks['all_runner_claim_gates_pass']=x['passed'] and all(x['checks'].values())
 out={'schema':'MultiTaskEpisodeOwnershipV1Analysis','capture_sha256':sha(CAP),'analyzer_sha256':sha(__file__),'checks':checks,'passed':all(checks.values()),'runs':per,'raw_graph_differences':{'differing_node_count':len(diff_nodes),'nodes':diff_nodes},'summary':{'graph_nodes':runs[0]['graph_summary']['nodes'],'graph_edges':runs[0]['graph_summary']['edges'],'task_count':len(runs[0]['turns']),'explicit_owner_counts':[len(r['owned_node_ids']) for r in runs[0]['owner_projection']],'all_task_owner_intersections_empty':all(z['count']==0 for z in runs[0]['owner_intersections']),'cross_owner_edges':len(runs[0]['cross_owner_edges']),'cross_owner_edge_types':dict(sorted(Counter(e[1] for e in runs[0]['cross_owner_edges']).items()))},'claim_boundary':'Two-worker replay of one fixed authored sequence. Explicit ownership projection omits reply Messages, and relation edges are not a complete causal or inference dependency model.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':out['summary']},indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
