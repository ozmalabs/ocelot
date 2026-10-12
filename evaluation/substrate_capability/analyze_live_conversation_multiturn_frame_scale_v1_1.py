#!/usr/bin/env python3
"""Independent topology and task-oracle analysis of live multi-turn frames."""
import gzip,hashlib,itertools,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/live_conversation_multiturn_frame_scale_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/live_conversation_multiturn_frame_scale_v1_20261003.jsonl.gz'
OUT=ROOT/'evaluation/reports/live_conversation_multiturn_frame_scale_v1_1_analysis_20261003.json'
SIZES=(1,2,4,8);REPS=(0,1,2);PROMPT='report your organisation'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(v):
 if isinstance(v,dict) and set(v)=={'__nid__'}:return int(v['__nid__'])
 if isinstance(v,int):return int(v)
 return None
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def semantic_digest(g):
 ids={int(x['id']):i for i,x in enumerate(g.get('nodes',[]))}
 nodes=[]
 for x in g.get('nodes',[]):
  y={k:v for k,v in x.items() if k!='id'}
  if y.get('type')=='SystemModel' and isinstance(y.get('attrs'),dict):
   y['attrs']={k:v for k,v in y['attrs'].items() if k not in ('runtime_s','ts')}
  nodes.append(y)
 edges=sorted((ids[int(e['src'])],e['type'],ids[int(e['tgt'])]) for e in g.get('edges',[]))
 return hashlib.sha256(json.dumps({'nodes':nodes,'edges':edges},sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def exact_tw(adj,nodes):
 nodes=tuple(sorted(nodes));n=len(nodes)
 if n<=1:return 0
 if n>8:return None
 best=n
 for order in itertools.permutations(nodes):
  work={v:set(adj[v]) for v in nodes};width=0
  for v in order:
   ns=work[v];width=max(width,len(ns))
   if width>=best:break
   for x in ns:work[x].update(ns-{x})
   for x in ns:work[x].discard(v)
   work[v].clear()
  else:best=min(best,width)
  if best==0:break
 return best
def main():
 errors=[]
 def req(ok,msg):
  if not ok:errors.append(msg)
 locked=json.loads(LOCK.read_text())['locked_inputs'];header=None;footer=None;rows=[];by_size=defaultdict(list);pids=set()
 with gzip.open(CAP,'rt') as stream:
  header=json.loads(next(stream));req(header.get('record_type')=='header','capture header missing')
  req(header.get('locked_inputs')==locked,'header/lock mismatch')
  req(tuple(header.get('sizes',()))==SIZES and tuple(header.get('replicates',()))==REPS and header.get('prompt')==PROMPT,'locked workload mismatch')
  for line in stream:
   if not line.strip():continue
   r=json.loads(line)
   if r.get('record_type')=='footer':footer=r;continue
   n=int(r.get('n_turns',-1));rep=int(r.get('replicate',-1));req(n in SIZES and rep in REPS,'unexpected size/replicate')
   if n not in SIZES or rep not in REPS:continue
   pids.add(r.get('pid'));req(r.get('source_stable') is True and r.get('locked_inputs')==locked==r.get('post_run_inputs'),'worker source-lock mismatch')
   graph=r.get('final_graph',{});req(r.get('final_graph_digest')==digest(graph),'graph digest mismatch')
   nodes={int(x['id']):x for x in graph.get('nodes',[])};edges=graph.get('edges',[]);req(len(nodes)==len(graph.get('nodes',[])),'duplicate node ID')
   req(all(int(e['src']) in nodes and int(e['tgt']) in nodes for e in edges),'edge endpoint missing')
   roots={i for i,x in nodes.items() if x['type']=='Message' and x.get('attrs',{}).get('from')=='interlocutor' and x.get('attrs',{}).get('text')==PROMPT}
   goalids={i for i,x in nodes.items() if x['type']=='Goal'};eventids={i for i,x in nodes.items() if x['type']=='DiscourseEvent'}
   gf=defaultdict(set);ef=defaultdict(set)
   for e in edges:
    a,b=int(e['src']),int(e['tgt']);rel=e['type']
    if rel=='comprehends':
     if a in goalids and b in roots:gf[a].add(b)
     if b in goalids and a in roots:gf[b].add(a)
    if rel=='represents_message' and a in eventids and b in roots:ef[a].add(b)
    if rel=='for_goal' and a in eventids and b in goalids:
     for f in gf.get(b,set()):ef[a].add(f)
    if rel=='originated_in' and a in goalids and b in eventids:
     for f in gf.get(a,set()):ef[b].add(f)
   for gid,node in nodes.items():
    if gid in goalids:
     origin=ref(node.get('attrs',{}).get('origin_event'))
     if origin in eventids:
      for f in gf.get(gid,set()):ef[origin].add(f)
   # Revisit for_goal edges after all Goal roots were discovered.
   for e in edges:
    if e['type']=='for_goal':
     ev,gid=int(e['src']),int(e['tgt'])
     if ev in eventids and gid in goalids:
      for f in gf.get(gid,set()):ef[ev].add(f)
   cand=defaultdict(set)
   for x in roots:cand[x].add(x)
   for x,fs in gf.items():cand[x].update(fs)
   for x,fs in ef.items():cand[x].update(fs)
   owners={x:next(iter(fs)) for x,fs in cand.items() if len(fs)==1};conflicts={x:sorted(fs) for x,fs in cand.items() if len(fs)>1}
   frames=sorted(set(owners.values()));boundary=set(nodes)-set(owners)
   # Per-turn identity trace emitted by the runner is checked against final graph identity.
   turns=r.get('turns',[]);req(len(turns)==n,'turn count mismatch')
   prompt_roots=sorted(roots);req(len(roots)==n,'prompt Message count mismatch')
   turn_contracts=[]
   for t in turns:
    linked=[gid for gid,fs in gf.items() if len(fs)==1 and next(iter(fs)) in roots]
    # Reconstruct this turn's newly created Goal via the runner's per-turn ID list,
    # then verify its graph relation independently.
    listed=[int(g['id']) for g in t.get('new_goal_summaries',[]) if g.get('kind')=='report_self']
    turn_roots=[int(x) for x in t.get('new_inbound_message_ids',[])]
    rooted=[gid for gid in listed if gid in gf and len(gf[gid])==1 and len(turn_roots)==1 and gf[gid]=={turn_roots[0]} and turn_roots[0] in roots]
    summary_ok=(len(t.get('new_inbound_message_ids',[]))==1 and len(listed)==1 and len(rooted)==1 and
      any(g['id']==rooted[0] and g['status']=='resolved' for g in t.get('new_goal_summaries',[])) and
      'organised into' in t.get('reply','').lower() and any(x.get('route')=='self_report' for x in t.get('action_results',[])))
    turn_contracts.append(summary_ok)
   req(all(turn_contracts),f'per-turn report_self contract failed at N={n} rep={rep}')
   linked_report=[gid for gid in goalids if nodes[gid].get('attrs',{}).get('kind')=='report_self' and len(gf.get(gid,set()))==1]
   req(len(roots)==n and len(linked_report)==n and len(set(next(iter(gf[g])) for g in linked_report))==n,'report_self Message ownership mismatch')
   graph_edges=[];bframes=defaultdict(set);boundary_inc=[]
   for e in edges:
    a,b=int(e['src']),int(e['tgt'])
    if a in owners and b in owners and owners[a]!=owners[b]:graph_edges.append(e)
    elif (a in owners)!=(b in owners):
     own=a if a in owners else b;unown=b if a in owners else a
     bframes[unown].add(owners[own]);boundary_inc.append({'frame':owners[own],'boundary_node':unown,'type':e['type']})
   inter={tuple(sorted((owners[int(e['src'])],owners[int(e['tgt'])]))) for e in graph_edges}
   for fs in bframes.values():
    for a,b in itertools.combinations(sorted(fs),2):inter.add((a,b))
   adj={f:set() for f in frames}
   for a,b in inter:adj[a].add(b);adj[b].add(a)
   goal_kinds={}
   for gid in goalids:goal_kinds[nodes[gid].get('attrs',{}).get('kind','<none>')]=goal_kinds.get(nodes[gid].get('attrs',{}).get('kind','<none>'),0)+1
   owned_types={str(f):dict(Counter(nodes[x]['type'] for x,o in owners.items() if o==f)) for f in frames}
   row={'n_turns':n,'replicate':rep,'pid':r['pid'],'graph_digest':r['final_graph_digest'],'graph_nodes':len(nodes),'graph_edges':len(edges),
    'node_type_counts':dict(Counter(x['type'] for x in nodes.values())),'prompt_roots':prompt_roots,'frame_count':len(frames),
    'frame_sizes':{str(f):sum(o==f for o in owners.values()) for f in frames},'owned_nodes_by_frame_type':owned_types,
    'report_self_goal_count':len(linked_report),'unowned_goal_kinds':dict(Counter(nodes[g].get('attrs',{}).get('kind','<none>') for g in goalids if g not in owners)),
    'goal_kind_counts':goal_kinds,'owner_conflict_count':len(conflicts),'owner_conflicts':conflicts,'unowned_node_count':len(boundary),
    'boundary_incidence_count':len(boundary_inc),'distinct_incident_boundary_nodes':len(bframes),
    'shared_boundary_nodes':sum(len(x)>1 for x in bframes.values()),'direct_cross_frame_edge_count':len(graph_edges),
    'direct_cross_frame_edge_types':dict(Counter(e['type'] for e in graph_edges)),'interaction_edges':[list(x) for x in sorted(inter)],
    'exact_interaction_treewidth':exact_tw(adj,frames),'task_turn_contracts_pass':sum(turn_contracts),'peak_rss_bytes':r.get('peak_rss_bytes'),
    'graph_nodes_reported':r.get('graph_nodes'),'graph_edges_reported':r.get('graph_edges'),'boot_wall_ns':r.get('boot_wall_ns'),'boot_process_cpu_ns':r.get('boot_process_cpu_ns'),
    'turn_wall_ns':[int(t.get('wall_ns',0)) for t in turns],'turn_process_cpu_ns':[int(t.get('process_cpu_ns',0)) for t in turns]}
   row['semantic_graph_digest_excluding_generated_systemmodel_timing']=semantic_digest(graph)
   rows.append(row);by_size[n].append(row)
 req(footer is not None,'capture footer missing')
 if footer:
  req(footer.get('post_run_inputs')==locked,'footer source-lock mismatch')
  req(all(footer.get('checks',{}).get(k) is True for k in ('twelve_workers','all_workers_zero','all_worker_records','source_stable')),'runner integrity gate failed')
  req(len(footer.get('run_status',[]))==12 and all(x.get('returncode')==0 and x.get('output_bytes',0)>0 for x in footer.get('run_status',[])),'worker output failure')
 req(len(rows)==12 and len(pids)==12,'expected 12 distinct workers')
 summaries={}
 for n in SIZES:
  group=by_size[n];req(len(group)==3,'replicate count mismatch at N='+str(n))
  if len(group)==3:req(len({r['semantic_graph_digest_excluding_generated_systemmodel_timing'] for r in group})==1,'semantic replicate graph mismatch at N='+str(n))
  summaries[str(n)]={'workers':len(group),'median_graph_nodes':statistics.median(r['graph_nodes'] for r in group),'median_graph_edges':statistics.median(r['graph_edges'] for r in group),
   'median_peak_rss_mib':statistics.median(r['peak_rss_bytes'] for r in group)/(1024**2),
   'median_frame_count':statistics.median(r['frame_count'] for r in group),'median_frame_sizes':statistics.median(sum(r['frame_sizes'].values()) for r in group),
   'median_distinct_incident_boundary_nodes':statistics.median(r['distinct_incident_boundary_nodes'] for r in group),
   'median_boundary_incidence_count':statistics.median(r['boundary_incidence_count'] for r in group),
   'median_cross_frame_edge_count':statistics.median(r['direct_cross_frame_edge_count'] for r in group),
   'median_interaction_treewidth':statistics.median(r['exact_interaction_treewidth'] for r in group)}
 out={'schema':'LiveConversationMultiturnFrameScaleV1_1Analysis','gates_pass':not errors,'errors':errors,'by_n_turns':summaries,'rows':rows,
  'memory_definition':'Peak RSS from a fresh process that boots once and runs exactly N identical live turns; includes full-seed runtime, graph, and task processing.',
  'claim_boundary':header.get('claim_boundary'),'analysis_script_sha256':sha(__file__),
  'ownership_rule':'Message roots from exact prompt text; Goal via explicit comprehends edge; Event via for_goal, originated_in, origin_event reference, or represents_message. All other nodes unowned.',
  'replicate_comparison':'Retain and verify the raw graph digest per worker. Compare replicated graph identity using stable graph-node array position as canonical identity and remove only generated SystemModel attrs runtime_s and ts, which differ by fresh-process execution time; edge topology, all other node fields, and attrs remain exact.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates_pass':out['gates_pass'],'errors':errors,'by_n_turns':summaries},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
