#!/usr/bin/env python3
"""Independent ownership, replicate, and frame-interaction analysis."""
import gzip,hashlib,itertools,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/live_conversation_distinct_turn_frame_scale_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/live_conversation_distinct_turn_frame_scale_v1_20261003.jsonl.gz'
OUT=ROOT/'evaluation/reports/live_conversation_distinct_turn_frame_scale_v1_1_analysis_20261003.json'
ARMS={'independent':[('How are you organised?','question'),('quorplezap the door','statement'),('report your organisation','statement')], 'followup':[('report your organisation','statement'),('Can you explain that in simpler terms?','question'),('What part of your organisation is most important?','question')]}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(v):
 if isinstance(v,dict) and set(v)=={'__nid__'}:return int(v['__nid__'])
 if isinstance(v,int):return int(v)
 return None
def semantic_digest(g):
 ids={int(x['id']):i for i,x in enumerate(g.get('nodes',[]))};nodes=[]
 for x in g.get('nodes',[]):
  y={k:v for k,v in x.items() if k!='id'}
  if y.get('type')=='SystemModel' and isinstance(y.get('attrs'),dict):y['attrs']={k:v for k,v in y['attrs'].items() if k not in ('runtime_s','ts')}
  nodes.append(y)
 edges=sorted((ids[int(e['src'])],e['type'],ids[int(e['tgt'])]) for e in g.get('edges',[]))
 return hashlib.sha256(json.dumps({'nodes':nodes,'edges':edges},sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def tw(adj,fs):
 fs=tuple(sorted(fs));best=len(fs)
 for order in itertools.permutations(fs):
  w={x:set(adj[x]) for x in fs};width=0
  for v in order:
   ns=w[v];width=max(width,len(ns))
   for x in ns:w[x].update(ns-{x});w[x].discard(v)
   w[v].clear()
  best=min(best,width)
 return best if fs else 0
def main():
 lock=json.loads(LOCK.read_text())['locked_inputs'];errs=[];rows=[];by=defaultdict(list);pids=set();header=footer=None
 def req(ok,msg):
  if not ok:errs.append(msg)
 with gzip.open(CAP,'rt') as f:
  header=json.loads(next(f));req(header.get('locked_inputs')==lock,'header lock mismatch')
  for line in f:
   x=json.loads(line)
   if x.get('record_type')=='footer':footer=x;continue
   arm=x.get('arm');rep=x.get('replicate');req(arm in ARMS and rep in (0,1,2),'unexpected worker');pids.add(x.get('pid'))
   req(x.get('source_stable') is True and x.get('locked_inputs')==lock==x.get('post_run_inputs'),'worker source mismatch')
   g=x.get('final_graph',{});req(x.get('final_graph_digest')==hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest(),'raw graph digest invalid')
   nodes={int(n['id']):n for n in g.get('nodes',[])};edges=g.get('edges',[]);prompts=[p for p,s in ARMS.get(arm,[])]
   roots={p:{i for i,n in nodes.items() if n.get('type')=='Message' and n.get('attrs',{}).get('from')=='interlocutor' and n.get('attrs',{}).get('text')==p} for p in set(prompts)}
   req(all(len(roots[p])==1 for p in set(prompts)),'expected exactly one inbound message per distinct prompt')
   goalids={i for i,n in nodes.items() if n.get('type')=='Goal'};eventids={i for i,n in nodes.items() if n.get('type')=='DiscourseEvent'};gf=defaultdict(set);ef=defaultdict(set)
   for e in edges:
    a,b=int(e['src']),int(e['tgt']);rel=e['type']
    if rel=='comprehends':
     if a in goalids and any(b in v for v in roots.values()):gf[a].add(b)
     if b in goalids and any(a in v for v in roots.values()):gf[b].add(a)
    if rel=='represents_message' and a in eventids and any(b in v for v in roots.values()):ef[a].add(b)
    if rel=='for_goal' and a in eventids and b in goalids:ef[a].update(gf.get(b,set()))
    if rel=='originated_in' and a in goalids and b in eventids:ef[b].update(gf.get(a,set()))
   for gid,n in nodes.items():
    if gid in goalids:
     ev=ref(n.get('attrs',{}).get('origin_event'))
     if ev in eventids:ef[ev].update(gf.get(gid,set()))
   owners={i:next(iter(v)) for i,v in {**{i:set(v) for i,v in roots.items() for i in v}}.items()} if False else {}
   candidates=defaultdict(set)
   for vals in roots.values():
    for i in vals:candidates[i].add(i)
   for d in (gf,ef):
    for i,vals in d.items():candidates[i].update(vals)
   owners={i:next(iter(v)) for i,v in candidates.items() if len(v)==1};conflicts={i:v for i,v in candidates.items() if len(v)>1};frames=sorted(set(owners.values()));boundary=set(nodes)-set(owners);bframes=defaultdict(set);cross=[];inc=0
   for e in edges:
    a,b=int(e['src']),int(e['tgt'])
    if a in owners and b in owners and owners[a]!=owners[b]:cross.append((owners[a],owners[b]))
    elif (a in owners)!=(b in owners):
     inc+=1;owned=a if a in owners else b;unowned=b if a in owners else a;bframes[unowned].add(owners[owned])
   inter={tuple(sorted(v)) for v in cross}
   for v in bframes.values():inter.update(itertools.combinations(sorted(v),2))
   adj={f:set() for f in frames}
   for a,b in inter:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
   turnchecks=[]
   for t,(prompt,speech) in zip(x.get('turns',[]),ARMS.get(arm,[])):
    mids=t.get('new_inbound_message_ids',[]);turnchecks.append(len(mids)==1 and len(t.get('new_goal_summaries',[]))>=0 and t.get('prompt')==prompt and t.get('speech_act')==speech)
   req(len(turnchecks)==3 and all(turnchecks),'turn identity trace mismatch')
   row={'arm':arm,'replicate':rep,'pid':x.get('pid'),'graph_nodes':len(nodes),'graph_edges':len(edges),'frame_count':len(frames),'owned_nodes_per_frame':{str(f):sum(owner==f for owner in owners.values()) for f in frames},'roots_by_prompt':{p:sorted(v) for p,v in roots.items()},'owned_goals':sum(i in owners for i in goalids),'unowned_goals':sum(i not in owners for i in goalids),'owner_conflict_count':len(conflicts),'unowned_nodes':len(boundary),'boundary_incidence_count':inc,'distinct_incident_boundary_nodes':len(bframes),'shared_boundary_nodes':sum(len(v)>1 for v in bframes.values()),'direct_cross_frame_edges':len(cross),'interaction_edges':[list(v) for v in sorted(inter)],'exact_interaction_treewidth':tw(adj,frames),'task_routes':[[z.get('route') for z in t.get('action_results',[])] for t in x.get('turns',[])],'turn_wall_ns':[t.get('wall_ns') for t in x.get('turns',[])],'peak_rss_bytes':x.get('peak_rss_bytes'),'graph_digest':x.get('final_graph_digest')}
   row['semantic_graph_digest_excluding_generated_systemmodel_timing']=semantic_digest(g)
   rows.append(row);by[arm].append(row)
 req(len(pids)==6,'expected six distinct PIDs')
 req(footer is not None,'footer missing')
 if footer:req(footer.get('post_run_inputs')==lock and all(footer.get('checks',{}).values()),'runner footer gate failed')
 summaries={}
 for arm in ARMS:
  grp=by[arm];req(len(grp)==3,f'{arm}: expected three workers')
  if len(grp)==3:req(len({r['semantic_graph_digest_excluding_generated_systemmodel_timing'] for r in grp})==1,f'{arm}: semantic replicate graph mismatch')
  summaries[arm]={'workers':len(grp),'median_nodes':statistics.median(r['graph_nodes'] for r in grp) if grp else None,'median_edges':statistics.median(r['graph_edges'] for r in grp) if grp else None,'median_owned_goals':statistics.median(r['owned_goals'] for r in grp) if grp else None,'median_unowned_goals':statistics.median(r['unowned_goals'] for r in grp) if grp else None,'median_boundary_nodes':statistics.median(r['distinct_incident_boundary_nodes'] for r in grp) if grp else None,'median_boundary_incidence':statistics.median(r['boundary_incidence_count'] for r in grp) if grp else None,'median_direct_cross_edges':statistics.median(r['direct_cross_frame_edges'] for r in grp) if grp else None,'median_interaction_edges':statistics.median(len(r['interaction_edges']) for r in grp) if grp else None,'median_treewidth':statistics.median(r['exact_interaction_treewidth'] for r in grp) if grp else None,'median_peak_rss_mib':statistics.median(r['peak_rss_bytes'] for r in grp)/(1024**2) if grp else None}
 out={'schema':'LiveConversationDistinctTurnFrameScaleV1_1Analysis','gates_pass':not errs,'errors':errs,'by_arm':summaries,'rows':rows,'claim_boundary':header.get('claim_boundary'),'ownership':'Exact inbound Message identity; Goals only by comprehends; Events by for_goal, originated_in, origin_event, represents_message.','replicate_comparison':'Retain raw graph digests, and compare a semantic digest after remapping IDs to graph-array positions and excluding only SystemModel attrs runtime_s and ts. All other node fields, attrs, array order, and directed typed topology remain exact.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates_pass':out['gates_pass'],'errors':errs,'by_arm':summaries},indent=2));return int(bool(errs))
if __name__=='__main__':raise SystemExit(main())
