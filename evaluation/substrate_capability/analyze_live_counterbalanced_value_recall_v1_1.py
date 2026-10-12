#!/usr/bin/env python3
"""Independent exact-value oracle and graph-identity analysis."""
import gzip,hashlib,itertools,json,statistics,re
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];LOCK=ROOT/'evaluation/substrate_capability/live_counterbalanced_value_recall_v1_lock_20261003.json';CAP=ROOT/'evaluation/reports/live_counterbalanced_value_recall_v1_20261003.jsonl.gz';OUT=ROOT/'evaluation/reports/live_counterbalanced_value_recall_v1_1_analysis_20261003.json'
ARMS={'value_14':[('My secret code is 14.','statement'),('What is my secret code?','question')],'value_29':[('My secret code is 29.','statement'),('What is my secret code?','question')],'fresh_control':[('What is my secret code?','question')]}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(v):
 if isinstance(v,dict) and set(v)=={'__nid__'}:return int(v['__nid__'])
 if isinstance(v,int):return int(v)
 return None
def has_num(s,n):return re.search(r'(?<!\d)'+str(n)+r'(?!\d)',s) is not None
def substantive_abstention(s):
 low=s.lower()
 if not low.strip() or low.startswith('error:'):return False
 return any(x in low for x in ("don't know",'do not know','not know','no information',"haven't",'have not','not told',"can't tell",'cannot tell','do not hold','does not hold'))
def semantic_digest(g):
 ids={int(x['id']):i for i,x in enumerate(g.get('nodes',[]))};nodes=[]
 for x in g.get('nodes',[]):
  y={k:v for k,v in x.items() if k!='id'}
  if y.get('type')=='Interlocutor' and isinstance(y.get('attrs',{}).get('believed_concepts'),dict):
   fc=y['attrs']['believed_concepts'].get('__fset__')
   if isinstance(fc,list):y['attrs']['believed_concepts']['__fset__']=sorted(fc)
  nodes.append(y)
 edges=sorted((ids[int(e['src'])],e['type'],ids[int(e['tgt'])]) for e in g.get('edges',[]))
 return hashlib.sha256(json.dumps({'nodes':nodes,'edges':edges},sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text())['locked_inputs'];errs=[];rows=[];by=defaultdict(list);pids=set();header=footer=None
 def req(ok,msg):
  if not ok:errs.append(msg)
 with gzip.open(CAP,'rt') as f:
  header=json.loads(next(f));req(header.get('locked_inputs')==lock,'header lock mismatch')
  for line in f:
   x=json.loads(line)
   if x.get('record_type')=='footer':footer=x;continue
   arm=x.get('condition');rep=x.get('replicate');req(arm in ARMS and rep in (0,1,2),'unexpected worker');pids.add(x.get('pid'));req(x.get('source_stable') is True and x.get('locked_inputs')==lock==x.get('post_run_inputs'),'worker source mismatch')
   g=x.get('final_graph',{});req(x.get('final_graph_digest')==hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest(),'invalid raw graph digest');nodes={int(n['id']):n for n in g.get('nodes',[])};edges=g.get('edges',[]);turns=x.get('turns',[]);prompts=[p for p,s in ARMS.get(arm,[])];req(len(turns)==len(prompts),'turn count mismatch')
   roots={p:{i for i,n in nodes.items() if n.get('type')=='Message' and n.get('attrs',{}).get('from')=='interlocutor' and n.get('attrs',{}).get('text')==p} for p in set(prompts)};req(all(len(v)==1 for v in roots.values()),'expected exactly one message root per distinct prompt')
   goalids={i for i,n in nodes.items() if n.get('type')=='Goal'};eventids={i for i,n in nodes.items() if n.get('type')=='DiscourseEvent'};gf=defaultdict(set);ef=defaultdict(set)
   for e in edges:
    a,b=int(e['src']),int(e['tgt']);r=e['type']
    if r=='comprehends':
     if a in goalids and any(b in v for v in roots.values()):gf[a].add(b)
     if b in goalids and any(a in v for v in roots.values()):gf[b].add(a)
    if r=='represents_message' and a in eventids and any(b in v for v in roots.values()):ef[a].add(b)
    if r=='for_goal' and a in eventids and b in goalids:ef[a].update(gf.get(b,set()))
    if r=='originated_in' and a in goalids and b in eventids:ef[b].update(gf.get(a,set()))
   for gid,n in nodes.items():
    if gid in goalids:
     ev=ref(n.get('attrs',{}).get('origin_event'))
     if ev in eventids:ef[ev].update(gf.get(gid,set()))
   owner={i:next(iter(fs)) for d in (gf,ef) for i,fs in d.items() if len(fs)==1};
   for p,v in roots.items():
    for rid in v:owner[rid]=rid
   frame_roots={rid for vs in roots.values() for rid in vs};cross=[];boundary_by=defaultdict(set);boundary_edges=[]
   for e in edges:
    a,b=int(e['src']),int(e['tgt'])
    if a in owner and b in owner and owner[a]!=owner[b]:cross.append({'source_frame':owner[a],'target_frame':owner[b],'type':e['type']})
    elif (a in owner)!=(b in owner):
     own=a if a in owner else b;un=b if a in owner else a;boundary_by[un].add(owner[own]);boundary_edges.append({'frame':owner[own],'boundary_node':un,'type':e['type']})
   shared_inter={tuple(sorted(fs)) for fs in boundary_by.values() if len(fs)>1};direct={(min(e['source_frame'],e['target_frame']),max(e['source_frame'],e['target_frame'])) for e in cross};inter=direct|shared_inter
   adj={r:set() for r in frame_roots}
   for a,b in inter:adj[a].add(b);adj[b].add(a)
   # Exhaust all orders (at most two task frames) for exact interaction width.
   best=len(frame_roots)
   for order in itertools.permutations(frame_roots):
    w={k:set(v) for k,v in adj.items()};z=0
    for v in order:
     ns=w[v];z=max(z,len(ns))
     for q in ns:w[q].update(ns-{q});w[q].discard(v)
     w[v].clear()
    best=min(best,z)
   req(all(len(t.get('new_inbound_message_ids',[]))==1 and t.get('prompt')==p and t.get('speech_act')==s for t,(p,s) in zip(turns,ARMS.get(arm,[]))),'per-turn inbound identity trace mismatch')
   reply=turns[-1].get('reply','');has14=has_num(reply,14);has29=has_num(reply,29)
   substantive=bool(reply.strip()) and not reply.lower().startswith('error:')
   success=(substantive and has14 and not has29) if arm=='value_14' else ((substantive and has29 and not has14) if arm=='value_29' else (substantive_abstention(reply) and not has14 and not has29))
   msg_to_frame={rid:p for p,v in roots.items() for rid in v};goal_links=[]
   for gid,fs in gf.items():
    for rid in fs:goal_links.append({'goal_id':gid,'goal_kind':nodes[gid].get('attrs',{}).get('kind'),'message_id':rid,'prompt':msg_to_frame.get(rid)})
   row={'condition':arm,'replicate':rep,'pid':x.get('pid'),'turn_count':len(turns),'graph_nodes':len(nodes),'graph_edges':len(edges),'root_ids':{p:sorted(v) for p,v in roots.items()},'owned_goal_links':goal_links,'unowned_goal_count':sum(i not in owner for i in goalids),'owner_conflict_count':sum(len(v)>1 for v in gf.values()),'cross_frame_edges':cross,'shared_boundary_node_count':sum(len(v)>1 for v in boundary_by.values()),'interaction_edges':[list(e) for e in sorted(inter)],'exact_interaction_treewidth':best,'turn_prompts':[t['prompt'] for t in turns],'replies':[t['reply'] for t in turns],'routes':[[a.get('route') for a in t.get('action_results',[])] for t in turns],'goal_summaries':[t.get('new_goal_summaries',[]) for t in turns],'answer_contains_14':has14,'answer_contains_29':has29,'substantive_reply':substantive,'task_oracle_pass':bool(success),'wall_ns':[t.get('wall_ns') for t in turns],'peak_rss_bytes':x.get('peak_rss_bytes'),'graph_digest':x.get('final_graph_digest'),'semantic_graph_digest':semantic_digest(g)}
   rows.append(row);by[arm].append(row)
 req(len(pids)==9,'expected nine unique workers');req(footer is not None,'footer missing')
 if footer:req(footer.get('post_run_inputs')==lock and all(footer.get('checks',{}).values()),'runner footer gate failed')
 summaries={}
 for arm in ARMS:
  grp=by[arm];req(len(grp)==3,f'{arm}: expected three replicates')
  if len(grp)==3:req(len({r['semantic_graph_digest'] for r in grp})==1,f'{arm}: semantic replicate digest mismatch')
  summaries[arm]={'workers':len(grp),'oracle_passes':sum(r['task_oracle_pass'] for r in grp),'oracle_rate':sum(r['task_oracle_pass'] for r in grp)/len(grp) if grp else None,'median_nodes':statistics.median(r['graph_nodes'] for r in grp) if grp else None,'median_edges':statistics.median(r['graph_edges'] for r in grp) if grp else None,'median_owned_goals':statistics.median(len(r['owned_goal_links']) for r in grp) if grp else None,'median_boundary_nodes':statistics.median(r['shared_boundary_node_count'] for r in grp) if grp else None,'median_cross_frame_edges':statistics.median(len(r['cross_frame_edges']) for r in grp) if grp else None,'median_treewidth':statistics.median(r['exact_interaction_treewidth'] for r in grp) if grp else None,'median_peak_rss_mib':statistics.median(r['peak_rss_bytes'] for r in grp)/(1024**2) if grp else None}
 out={'schema':'LiveCounterbalancedValueRecallV1_1Analysis','gates_pass':not errs,'errors':errs,'by_condition':summaries,'rows':rows,'oracle':'Value arms require a substantive non-error reply containing the matching standalone numeral and forbidding the other. Fresh control requires a substantive explicit abstention and neither numeral. The v1 numeral-only fresh-control criterion incorrectly counted the runtime error as a pass and is superseded here.','replicate_comparison':'Raw digests are retained; semantic digests only sort the unordered __fset__ values in Interlocutor.attrs.believed_concepts, the sole observed replicate variation. Graph order and directed typed topology remain exact.','claim_boundary':header.get('claim_boundary')};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates_pass':out['gates_pass'],'errors':errs,'by_condition':summaries},indent=2));return int(bool(errs))
if __name__=='__main__':raise SystemExit(main())
