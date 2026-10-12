#!/usr/bin/env python3
"""Capture a fixed five-task episode in one fresh substrate graph per worker."""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_MULTI_TASK_EPISODE_OWNERSHIP_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/multi_task_episode_ownership_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/multi_task_episode_ownership_v1_20261004.json'
TASK_ORDER=['scene_description','unknown_word_clarification','held_self_knowledge_answer','concern_authoring','self_report_action']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def structural_graph_sha(graph):
 # Only generated diagnostic timing fields differed in the initial two-worker comparison.
 def clean(v):
  if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in {'ts','runtime_s'}}
  if isinstance(v,list):return [clean(x) for x in v]
  return v
 return hashlib.sha256(json.dumps(clean(graph),sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('multi_task_base',BASE);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def inputs():
 m=load_base()
 return {'runner_sha256':sha(__file__),'protocol_sha256':sha(PROTOCOL),'base_harvest_runner_sha256':sha(BASE),'base_runtime_inputs':m.inputs()}
def worker(rep):
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();before=inputs();m=load_base()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());boot=load_all_seeds(a);ca.attach_scene(a,m.SCENE)
 turns=[];messages=[]
 for condition in TASK_ORDER:
  prompt,speech_act=m.TASKS[condition]
  before_nodes=len(a.s.nodes('Message'))
  started=time.perf_counter_ns();error=None
  try:reply=str(a.converse(prompt,speech_act=speech_act,speaker='alice'))
  except BaseException as exc:reply='';error=f'{type(exc).__name__}: {exc}'
  elapsed=time.perf_counter_ns()-started
  inbound=[x for x in a.s.nodes('Message') if a.s.node(x)['attrs'].get('from')=='interlocutor' and a.s.node(x)['attrs'].get('text')==prompt]
  inbound.sort(key=m.nid)
  msgid=m.nid(inbound[-1]) if inbound else None
  route=None
  # Route is read from generated graph-backed interpretation, never inferred from reply text.
  if msgid is not None:
   attrs=a.s.node(inbound[-1])['attrs'];iid=attrs.get('communication_interpretation_id')
   if iid is not None and a.s.has_node(iid):route=a.s.node(iid)['attrs'].get('dispatch_path')
   messages.append({'id':msgid,'prompt':prompt,'condition':condition})
  turns.append({'condition':condition,'prompt':prompt,'speech_act':speech_act,'message_id':msgid,'route':route,'reply':reply,'error':error,'elapsed_ns':elapsed,'message_count_before':before_nodes,'message_count_after':len(a.s.nodes('Message'))})
 graph=a.inner.graph_to_dict();nodes={int(n['id']):n for n in graph['nodes']};edges=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']]
 owners=[];by_turn=[]
 def ref(v):return int(v['__nid__']) if isinstance(v,dict) and set(v)=={'__nid__'} else int(v) if isinstance(v,int) else None
 for i,t in enumerate(turns):
  root=t['message_id'];goals=set()
  if root is not None:
   for x,rel,y in edges:
    if rel=='comprehends':
     if x==root and y in nodes and nodes[y]['type']=='Goal':goals.add(y)
     if y==root and x in nodes and nodes[x]['type']=='Goal':goals.add(x)
  events=set()
  for gid in goals:
   o=ref(nodes[gid].get('attrs',{}).get('origin_event'))
   if o in nodes and nodes[o]['type']=='DiscourseEvent':events.add(o)
  for x,rel,y in edges:
   if rel=='for_goal':
    if x in nodes and nodes[x]['type']=='DiscourseEvent' and y in goals:events.add(x)
    if y in nodes and nodes[y]['type']=='DiscourseEvent' and x in goals:events.add(y)
  owned=({root} if root in nodes else set())|goals|events;owners.append(owned)
  by_turn.append({'turn':i,'condition':t['condition'],'message_id':root,'goal_ids':sorted(goals),'event_ids':sorted(events),'owned_node_ids':sorted(owned),'owned_node_count':len(owned),'owned_types':dict(sorted(__import__('collections').Counter(nodes[n]['type'] for n in owned).items()))})
 owner={n:i for i,ids in enumerate(owners) for n in ids};cross=[]
 for x,rel,y in edges:
  if x in owner and y in owner and owner[x]!=owner[y]:cross.append([x,rel,y])
 graph_digest=hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
 return {'replicate':rep,'pid':os.getpid(),'boot_loaded':boot.get('loaded'),'boot_failures':len(boot.get('failed',[])),'locked_inputs':before,'post_run_inputs':inputs(),'turns':turns,'owner_projection':by_turn,'owner_intersections':[{ 'a':i,'b':j,'count':len(owners[i]&owners[j]),'ids':sorted(owners[i]&owners[j])} for i in range(len(owners)) for j in range(i+1,len(owners))],'cross_owner_edges':cross,'graph':graph,'graph_summary':{'nodes':len(nodes),'edges':len(edges),'raw_sha256':graph_digest,'structural_sha256':structural_graph_sha(graph)}}
def main():
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine()
 if sys.argv[1:]==['--worker']:
  print(json.dumps(worker(int(os.environ['OCEL0_MULTI_TASK_REP'])),separators=(',',':')));return
 locked=inputs()
 if sys.argv[1:]==['--lock']:
  if OUT.exists():raise SystemExit('result exists; refusing to replace')
  LOCK.write_text(json.dumps({'schema':'MultiTaskEpisodeOwnershipV1Lock','locked_inputs':locked},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale lock')
 if OUT.exists():raise SystemExit('result exists; refusing to replace')
 runs=[]
 for rep in range(2):
  env=os.environ.copy();env['OCEL0_MULTI_TASK_REP']=str(rep)
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
  if p.returncode:raise SystemExit(f'worker {rep} failed: {p.stderr[-2000:]}')
  runs.append(json.loads(p.stdout))
 checks={'two_workers':len(runs)==2,'distinct_pids':len({r['pid'] for r in runs})==2,'source_lock_stable':all(r['locked_inputs']==locked==r['post_run_inputs'] for r in runs),'five_turns_each':all(len(r['turns'])==5 for r in runs),'all_message_ids_resolve':all(all(t['message_id'] is not None for t in r['turns']) for r in runs),'normalized_graph_structure_reproduces':len({r['graph_summary']['structural_sha256'] for r in runs})==1,'graph_summaries_reproduce':len({(r['graph_summary']['nodes'],r['graph_summary']['edges'],r['graph_summary']['structural_sha256']) for r in runs})==1,'task_outcomes_reproduce':len({json.dumps([{k:t[k] for k in ('condition','route','reply','error')} for t in r['turns']],sort_keys=True) for r in runs})==1,'owner_projections_reproduce':len({json.dumps(r['owner_projection'],sort_keys=True) for r in runs})==1,'cross_owner_edges_reproduce':len({json.dumps(r['cross_owner_edges'],sort_keys=True) for r in runs})==1}
 out={'schema':'MultiTaskEpisodeOwnershipV1','locked_inputs':locked,'checks':checks,'passed':all(checks.values()),'runs':runs,'claim_boundary':'Two fresh workers replay one fixed authored five-task sequence in one graph each. Raw graph hashes include diagnostic timing fields; normalized structure removes only ts/runtime_s, the sole observed between-worker differences. Relation-derived ownership is a conservative projection, not a complete dependency model or natural-task estimate.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'graph':runs[0]['graph_summary'],'cross_owner_edges':len(runs[0]['cross_owner_edges']),'owners':runs[0]['owner_projection']},indent=2))
 if not out['passed']:raise SystemExit('episode gates failed')
if __name__=='__main__':main()
