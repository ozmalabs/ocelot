#!/usr/bin/env python3
"""Reconstruct explicit request/Goal/Event ownership from harvested raw graphs."""
import gzip,hashlib,json,itertools,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2_lock_20261004.json'
CAP=ROOT/'evaluation/reports/live_conversation_task_graph_harvest_v2_20261004.jsonl.gz'
OUT=ROOT/'evaluation/reports/live_conversation_task_graph_harvest_v2_analysis_20261004.json'
TASKS=('scene_description','held_self_knowledge_answer','self_report_action','unknown_word_clarification','concern_authoring')
PROMPTS={'scene_description':'describe what you see','held_self_knowledge_answer':'How are you organised?','self_report_action':'report your organisation','unknown_word_clarification':'quorplezap the door','concern_authoring':'Compare where the two letters differ and judge the trial on that region.'}
SCHEDULE=(('scene_description',0),('unknown_word_clarification',0),('held_self_knowledge_answer',0),('concern_authoring',0),('self_report_action',0),('self_report_action',1),('concern_authoring',1),('held_self_knowledge_answer',1),('unknown_word_clarification',1),('scene_description',1))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(v):
 if isinstance(v,dict) and set(v)=={'__nid__'}:return int(v['__nid__'])
 if isinstance(v,int):return int(v)
 return None
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def exact_tw(edges,nodes):
 nodes=tuple(sorted(nodes));n=len(nodes)
 if n<=1:return 0
 if n>10:return None
 best=n
 for order in itertools.permutations(nodes):
  adj={v:set(edges.get(v,set())) for v in nodes};width=0
  for v in order:
   ns=adj[v];width=max(width,len(ns))
   if width>=best:break
   for a in ns:
    adj[a].update(ns-{a})
   for a in ns:adj[a].discard(v)
   adj[v].clear()
  else:best=min(best,width)
  if best==0:break
 return best
def task_oracle(r):
 cond=r['condition'];reply=r.get('reply','');turns=r.get('turns',[]);actions=r.get('action_results',[]);route=[x.get('route') for x in actions]
 if len(turns)!=1 or r.get('error') is not None:return False
 t=turns[0]
 if cond=='scene_description':return reply=='I see the grey thing stays, the yellow counter, and the blue thing moves.' and any(g.get('kind')=='describe_scene' and g.get('status')=='resolved' and g.get('events')==['selection','execution','action_result'] for g in t['goals'])
 if cond=='held_self_knowledge_answer':return 'organis' in reply.lower() and not reply.rstrip().endswith('?')
 if cond=='self_report_action':return 'self_report' in route and any(g.get('kind')=='report_self' and g.get('status')=='resolved' and g.get('events')==['selection','execution','action_result'] for g in t['goals']) and bool(reply.strip())
 if cond=='unknown_word_clarification':return 'quorplezap' in reply.lower() and reply.rstrip().endswith('?') and any('quorplezap' in str(m.get('trouble_source','')).lower() and m.get('expects_response') is True and 'clarification' in m.get('speech_acts',[]) for m in t['outbound_messages'])
 if cond=='concern_authoring':return any(x.get('route')=='concern_authored' and x.get('concern') is not None for x in actions) and bool(reply.strip()) and 'no attached world/faculty' not in reply.lower() and r.get('teacher_calls')==0
 return False
def main():
 errors=[]
 def req(ok,msg):
  if not ok:errors.append(msg)
 lock=json.loads(LOCK.read_text())['locked_inputs'];rows=[];bycondition=defaultdict(list);pids=set();footer=None;header=None
 with gzip.open(CAP,'rt') as stream:
  first=stream.readline();req(bool(first),'empty graph-harvest archive')
  if not first:raise SystemExit('empty capture')
  header=json.loads(first);req(header.get('record_type')=='header','capture header missing')
  req(header.get('locked_inputs')==lock,'capture/lock mismatch')
  req(header.get('schedule')==[list(x) for x in SCHEDULE],'locked schedule mismatch')
  for line in stream:
   if not line.strip():continue
   record=json.loads(line)
   if record.get('record_type')=='footer':footer=record;continue
   r=record;cond=r.get('condition');req(cond in TASKS,'unknown task condition')
   if cond not in TASKS:continue
   pids.add(r.get('pid'));req(r.get('source_stable') is True and r.get('locked_inputs')==lock==r.get('post_run_inputs'),'worker provenance mismatch')
   graph=r.get('final_graph',{});req(r.get('final_graph_digest')==digest(graph),'missing/incorrect graph digest')
   nodes={int(n['id']):n for n in graph.get('nodes',[])};edges=graph.get('edges',[])
   req(len(nodes)==len(graph.get('nodes',[])),'duplicate node IDs')
   req(all(int(e['src']) in nodes and int(e['tgt']) in nodes for e in edges),'edge endpoint missing')
   type_counts=Counter(n['type'] for n in nodes.values());prompt=r.get('prompt');req(prompt==PROMPTS.get(cond),'prompt/condition assignment mismatch')
   req(r.get('replicate') in (0,1),'replicate index invalid')
   inbound={i for i,n in nodes.items() if n['type']=='Message' and n.get('attrs',{}).get('from')=='interlocutor' and n.get('attrs',{}).get('text')==prompt}
   goal_frames=defaultdict(set);event_frames=defaultdict(set)
   goal_ids={i for i,n in nodes.items() if n['type']=='Goal'};event_ids={i for i,n in nodes.items() if n['type']=='DiscourseEvent'}
   for e in edges:
    if e.get('type')=='comprehends':
     a,b=int(e['src']),int(e['tgt'])
     if a in goal_ids and b in inbound:goal_frames[a].add(b)
     if b in goal_ids and a in inbound:goal_frames[b].add(a)
   for gid,n in nodes.items():
    if gid in goal_ids:
     origin=ref(n.get('attrs',{}).get('origin_event'))
     if origin in event_ids:
      for f in goal_frames.get(gid,set()):event_frames[origin].add(f)
   for e in edges:
    if e.get('type')=='for_goal':
     a,b=int(e['src']),int(e['tgt'])
     if a in event_ids and b in goal_ids:
      for f in goal_frames.get(b,set()):event_frames[a].add(f)
   candidates=defaultdict(set)
   for mid in inbound:candidates[mid].add(mid)
   for gid,fs in goal_frames.items():candidates[gid].update(fs)
   for eid,fs in event_frames.items():candidates[eid].update(fs)
   owners={nid:next(iter(fs)) for nid,fs in candidates.items() if len(fs)==1}
   conflicts={nid:sorted(fs) for nid,fs in candidates.items() if len(fs)>1}
   frames=sorted(set(owners.values()));boundary=set(nodes)-set(owners)
   owned_types={str(f):dict(Counter(nodes[n]['type'] for n,o in owners.items() if o==f)) for f in frames}
   frame_sizes={str(f):sum(o==f for o in owners.values()) for f in frames}
   cross=[];boundary_frames=defaultdict(set);boundary_incidence=[]
   for e in edges:
    a,b=int(e['src']),int(e['tgt'])
    if a in owners and b in owners and owners[a]!=owners[b]:cross.append(e)
    elif (a in owners)!=(b in owners):
     owned=a if a in owners else b;unowned=b if a in owners else a
     boundary_frames[unowned].add(owners[owned]);boundary_incidence.append({'frame':owners[owned],'boundary_node':unowned,'boundary_type':nodes[unowned]['type'],'edge_type':e['type']})
   interaction={tuple(sorted((owners[int(e['src'])],owners[int(e['tgt'])]))) for e in cross}
   for fs in boundary_frames.values():
    for a,b in itertools.combinations(sorted(fs),2):interaction.add((a,b))
   adj={f:set() for f in frames}
   for a,b in interaction:adj[a].add(b);adj[b].add(a)
   tw=exact_tw(adj,frames);task_pass=task_oracle(r)
   row={'condition':cond,'replicate':r.get('replicate'),'pid':r.get('pid'),'prompt':prompt,'task_contract_pass':task_pass,
    'route_summary':[x.get('route') for x in r.get('action_results',[])],'reply':r.get('reply'),'graph_digest':r.get('final_graph_digest'),
    'graph_nodes':len(nodes),'graph_edges':len(edges),'node_type_counts':dict(sorted(type_counts.items())),
    'request_roots':sorted(inbound),'owned_goal_count':sum(n in goal_ids for n in owners),'unowned_goal_count':len(goal_ids-set(owners)),
    'goal_inventory':[{'id':gid,'kind':nodes[gid].get('attrs',{}).get('kind'),'status':nodes[gid].get('attrs',{}).get('lifecycle_status',nodes[gid].get('attrs',{}).get('status')),'prompt_linked':gid in goal_frames,'origin_event':ref(nodes[gid].get('attrs',{}).get('origin_event'))} for gid in sorted(goal_ids)],
    'prompt_linked_goal_kinds':[nodes[gid].get('attrs',{}).get('kind') for gid in sorted(goal_ids) if gid in goal_frames],
    'unlinked_goal_kinds':[nodes[gid].get('attrs',{}).get('kind') for gid in sorted(goal_ids) if gid not in goal_frames],
    'frame_count':len(frames),'frame_sizes':frame_sizes,'owned_nodes_by_frame_type':owned_types,
    'owner_conflict_count':len(conflicts),'owner_conflicts':conflicts,'unowned_node_count':len(boundary),
    'direct_cross_frame_edges':len(cross),'direct_cross_frame_edge_types':dict(Counter(e['type'] for e in cross)),
    'boundary_incidence_count':len(boundary_incidence),'distinct_unowned_boundary_nodes_incident':len(boundary_frames),'unowned_nodes_not_touching_owner_nodes':len(boundary)-len(boundary_frames),'shared_boundary_node_count':sum(len(fs)>1 for fs in boundary_frames.values()),
    'interaction_edges':[list(x) for x in sorted(interaction)],'exact_interaction_treewidth':tw,
    'peak_rss_bytes':r.get('peak_rss_bytes'),'task_wall_ns':r.get('task_wall_ns')}
   req(bool(inbound),'no inbound prompt Message found for '+str(cond));rows.append(row);bycondition[cond].append(row)
 req(footer is not None,'capture footer missing')
 if footer:
  req(footer.get('post_run_inputs')==lock,'post-run source lock mismatch')
  req(footer.get('checks',{}).get('ten_workers') and footer.get('checks',{}).get('ten_worker_records') and footer.get('checks',{}).get('all_worker_processes_zero') and footer.get('checks',{}).get('parent_source_lock_stable'),'runner integrity gate failed')
  req(all(x.get('returncode')==0 and x.get('output_bytes',0)>0 for x in footer.get('run_status',[])),'worker process/output failure')
 req(len(rows)==10 and len(pids)==10,'expected ten unique graph workers')
 for cond in TASKS:
  group=bycondition.get(cond,[]);req(len(group)==2,'replicate count mismatch for '+cond)
  if len(group)==2:
   req({r['replicate'] for r in group}=={0,1},'replicate labels incomplete for '+cond)
   req(group[0]['graph_digest']==group[1]['graph_digest'],'replicate graph mismatch for '+cond)
 summary={'workers':len(rows),'conditions':len(bycondition),'task_contract_passes':sum(r['task_contract_pass'] for r in rows),
  'median_graph_nodes':{k:statistics.median([r['graph_nodes'] for r in v]) for k,v in bycondition.items()},
  'median_graph_edges':{k:statistics.median([r['graph_edges'] for r in v]) for k,v in bycondition.items()},
  'conditions_with_owned_goal':sum(any(r['owned_goal_count']>0 for r in v) for v in bycondition.values()),
  'conditions_with_direct_cross_frame_edges':sum(any(r['direct_cross_frame_edges']>0 for r in v) for v in bycondition.values()),
  'conditions_with_owner_conflicts':sum(any(r['owner_conflict_count']>0 for r in v) for v in bycondition.values()),
  'median_owned_nodes_per_frame_by_condition':{k:statistics.median([sum(r['frame_sizes'].values()) for r in v]) for k,v in bycondition.items()},
  'median_distinct_incident_boundary_nodes_by_condition':{k:statistics.median([r['distinct_unowned_boundary_nodes_incident'] for r in v]) for k,v in bycondition.items()},
  'median_boundary_incidence_count_by_condition':{k:statistics.median([r['boundary_incidence_count'] for r in v]) for k,v in bycondition.items()},
  'median_goal_owner_coverage_by_condition':{k:statistics.median([r['owned_goal_count']/(r['owned_goal_count']+r['unowned_goal_count']) if r['owned_goal_count']+r['unowned_goal_count'] else 0 for r in v]) for k,v in bycondition.items()},
  'prompt_linked_goal_kinds_by_condition':{k:sorted({kind for r in v for kind in r['prompt_linked_goal_kinds']}) for k,v in bycondition.items()},
  'unlinked_goal_kinds_by_condition':{k:sorted({kind for r in v for kind in r['unlinked_goal_kinds']}) for k,v in bycondition.items()}}
 out={'schema':'LiveConversationTaskGraphHarvestV2Analysis','gates_pass':not errors,'errors':errors,'summary':summary,'rows':rows,
  'claim_boundary':header.get('claim_boundary') if header else None,'analysis_script_sha256':sha(__file__),
  'ownership_rule':'Analyzer independently assigns only prompt-linked Goals and their explicit for_goal/origin_event DiscourseEvents. All other graph nodes remain shared/unowned.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates_pass':out['gates_pass'],'errors':errors,'summary':summary},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
