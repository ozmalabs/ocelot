#!/usr/bin/env python3
"""Capture fixed ingress frames and native rule accesses on five live routes."""
from __future__ import annotations
import gzip, hashlib, importlib.util, json, os, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
HARVEST=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
FRAME_BASE=ROOT/'scripts/substrate_live_held_topic_evidence_v1_6.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_MULTIROUTE_FRAME_ACCESS_V1_PREREG_20261006.md'
RUNNER=Path(__file__).resolve()
LOCK=ROOT/'evaluation/substrate_capability/multiroute_frame_access_v1_20261006_lock.json'
OUTDIR=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006'
CAPTURE=OUTDIR/'capture.json.gz'
SCHEDULE=[['scene_description',0],['unknown_word_clarification',0],['held_self_knowledge_answer',0],['concern_authoring',0],['self_report_action',0],['self_report_action',1],['concern_authoring',1],['held_self_knowledge_answer',1],['unknown_word_clarification',1],['scene_description',1]]

def sha(p):return 'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inputs():
 from substrate_rs import _native
 h=load(HARVEST,'harvest_multiroute'); b=load(FRAME_BASE,'frame_base_multiroute')
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'harvest_runner_sha256':sha(HARVEST),
         'harvest_inputs':h.inputs(),'frame_base_sha256':sha(FRAME_BASE),'native_extension_sha256':sha(Path(_native.__file__).resolve()),
         'schedule':SCHEDULE,'frame_rule':'PreOutcomeTaskFrameCaptureV1 fixed typed ingress projection'}
def nid(x):return int(x.value if hasattr(x,'value') else x)
def frame_at(base,agent,mid):
 graph=agent.s.graph_to_dict(); nodes={int(r['id']):r for r in graph.get('nodes',[])}
 edges=[(int(r['src']),str(r['type']),int(r['tgt'])) for r in graph.get('edges',[])];root=nid(mid);owned={root}
 for src,rel,tgt in edges:
  other=None
  if src==root and rel=='has_mention' and nodes.get(tgt,{}).get('type')=='Mention':other=tgt
  elif root in (src,tgt):
   candidate=tgt if src==root else src;typ=nodes.get(candidate,{}).get('type')
   if ((rel in {'has_interpretation','interprets'} and typ=='CommunicationInterpretation') or (rel in {'represents_message','for_message'} and typ=='DiscourseEvent')):other=candidate
  if other is not None:owned.add(other)
 incident=[e for e in edges if e[0] in owned or e[2] in owned]
 internal=[e for e in incident if e[0] in owned and e[2] in owned]
 boundary=[e for e in incident if (e[0] in owned)!=(e[2] in owned)]
 external={e[2] if e[0] in owned else e[0] for e in boundary}
 return {'root_message_id':root,'node_count':len(nodes),'edge_count':len(edges),'owned_ids':sorted(owned),'owned_node_count':len(owned),
  'owned_type_counts':dict(sorted(Counter(nodes[n]['type'] for n in owned).items())),
  'boundary_unique_external_node_count':len(external),'boundary_external_type_counts':dict(sorted(Counter(nodes[n]['type'] for n in external if n in nodes).items())),
  'boundary_incidence_count':len(boundary),'boundary_edge_type_counts':dict(sorted(Counter(e[1] for e in boundary).items())),
  'boundary_external_ids':sorted(external),
  'internal_edge_count':len(internal),'owned_induced_state_treewidth_upper_bound':base.min_fill_width_upper_bound(owned,internal)}
def worker(cond,rep):
 h=load(HARVEST,'harvest_worker_multiroute');base=load(FRAME_BASE,'frame_base_worker_multiroute')
 from substrate.world_adapter import WorldAdapter
 original_converse=WorldAdapter.converse;original_record=WorldAdapter._record_live_communication_state
 checkpoints=[];traces=[];static={}
 def record(self,mid,*args,**kwargs):
  result=original_record(self,mid,*args,**kwargs)
  if getattr(self,'_frame_active',False):checkpoints.append(frame_at(base,self,mid));self.inner.runtime_access_trace_reset()
  return result
 def converse(self,*args,**kwargs):
  self._frame_active=True;self.inner.runtime_access_trace_set_enabled(False);self.inner.runtime_access_trace_reset();self.inner.runtime_access_trace_set_enabled(True)
  try:return original_converse(self,*args,**kwargs)
  finally:
   self._frame_active=False;self.inner.runtime_access_trace_set_enabled(False);rows,dropped=self.inner.runtime_access_trace_snapshot()
   events=[{'rule_uid':int(u),'kind':str(k),'node':None if n is None else int(n),'resource':None if r is None else str(r),'peer':None if p is None else int(p),'count':int(c)} for u,k,n,r,p,c in rows]
   traces.append({'events':events,'dropped':int(dropped)})
   for row in self.inner.rule_access_sets():
    meta=self.inner.rule_metadata(int(row[0]));static[int(meta['rule_uid'])]={'name':str(row[1]),'reads':list(row[3]),'term_edge_reads':list(row[4]),'writes':list(row[5]),'reads_any':bool(row[6]),'writes_any':bool(row[7])}
 WorldAdapter.converse=converse;WorldAdapter._record_live_communication_state=record
 try:r=h.worker(cond,rep)
 finally:WorldAdapter.converse=original_converse;WorldAdapter._record_live_communication_state=original_record
 if len(checkpoints)!=1 or len(traces)!=1:raise RuntimeError(f'expected one route checkpoint/trace; got {len(checkpoints)}/{len(traces)}')
 frame=checkpoints[0];owned=set(frame['owned_ids']);external=set(frame['boundary_external_ids'])
 event_rows=traces[0]['events']; totals=Counter();roles=Counter();touched={'frame':set(),'outside_cut':set()}
 for e in event_rows:
  e['rule_name']=static.get(e['rule_uid'],{}).get('name','<unmapped>'); er=set()
  for n in (e['node'],e['peer']):
   if n is None:continue
   role='frame' if n in owned else 'boundary_external' if n in external else 'outside_cut';er.add(role);touched.setdefault(role,set()).add(n)
  e['scope_roles']=sorted(er or {'node_free'})
  for role in e['scope_roles']:roles[(role,e['kind'])]+=e['count']
  totals[e['kind']]+=e['count']
 observed={e['rule_uid'] for e in event_rows}
 r['preoutcome_frame']=frame;r['postcheckpoint_rule_access']={'dropped':traces[0]['dropped'],'event_count':sum(totals.values()),'distinct_rows':len(event_rows),
  'access_counts_by_kind':dict(sorted(totals.items())),'access_counts_by_scope_and_kind':{f'{a}/{b}':v for (a,b),v in sorted(roles.items())},
  'touched_nodes_by_scope':{k:len(v) for k,v in touched.items()},'unmapped_rule_uids':sorted(u for u in observed if u not in static),'events':event_rows}
 r['preoutcome_capture_gate']=traces[0]['dropped']==0 and not r['postcheckpoint_rule_access']['unmapped_rule_uids']
 return r
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'schema':'MultiRouteFrameAccessV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 if sys.argv[1:]==['--worker']:
  print(json.dumps(worker(os.environ['OCEL0_TASK_CONDITION'],int(os.environ['OCEL0_TASK_REP'])),sort_keys=True,separators=(',',':')));return
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale source lock')
 if CAPTURE.exists():raise SystemExit(f'refusing overwrite: {CAPTURE}')
 OUTDIR.mkdir(parents=True,exist_ok=True);runs=[];env=os.environ.copy();env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')])
 for cond,rep in SCHEDULE:
  e=env.copy();e.update(OCEL0_TASK_CONDITION=cond,OCEL0_TASK_REP=str(rep));p=subprocess.run([sys.executable,str(RUNNER),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,check=True,timeout=300);runs.append(json.loads(p.stdout));print(f'captured={cond}/{rep}',file=sys.stderr,flush=True)
 post=inputs();capture={'schema':'MultiRouteFrameAccessV1','locked_inputs':locked,'post_run_inputs':post,'runs':runs}
 CAPTURE.write_bytes(gzip.compress(json.dumps(capture,sort_keys=True,separators=(',',':')).encode(),compresslevel=5,mtime=0))
 ok=locked==post and all(r.get('source_stable') and r.get('preoutcome_capture_gate') for r in runs)
 print(json.dumps({'capture':str(CAPTURE.relative_to(ROOT)),'workers':len(runs),'integrity_pass':ok},indent=2))
 if not ok:raise SystemExit('capture integrity gate failed')
if __name__=='__main__':main()
