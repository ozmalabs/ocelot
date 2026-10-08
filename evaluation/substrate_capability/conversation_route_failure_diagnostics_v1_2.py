#!/usr/bin/env python3
"""No-op instrumentation of scene and concern route failures in one episode."""
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONVERSATION_ROUTE_FAILURE_DIAGNOSTICS_V1_2_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/conversation_route_failure_diagnostics_v1_2_lock_20261004.json'
OUT=ROOT/'evaluation/reports/conversation_route_failure_diagnostics_v1_2_20261004.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_conversation_route_failure_diagnostics_v1_2.py'
SOURCE_DEPS=['domains/conversation_action.py','domains/reflective_faculty.py','substrate/world_adapter.py','scripts/arc_self_report.py','domains/language_world.py','domains/language_production.py','scripts/language_test.py']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def base():
 s=importlib.util.spec_from_file_location('route_diag_base',BASE);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
def inputs():return {'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'base_runner_sha256':sha(BASE),'direct_source_dependencies':{p:sha(ROOT/p) for p in SOURCE_DEPS},'base_inputs':base().inputs()}
def worker(rep):
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();before=inputs();b=base()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());boot=load_all_seeds(a);ca.attach_scene(a,b.SCENE)
 trace=[];active={'condition':None}
 def wrap(name,fn):
  def call(*args,**kwargs):
   row={'condition':active['condition'],'function':name}
   if name=='_ensure_describe':row['rule_count_before']=int(a.inner.rule_count())
   if name=='_act_describe_scene':
    agent=args[0];row['inbound_id']=int(args[2].value if hasattr(args[2],'value') else args[2]);row['describe_goal_ids_before']=[int(g.value if hasattr(g,'value') else g) for g in agent.s.nodes('Goal') if agent.s.node(g)['attrs'].get('kind')=='describe_scene']
   try:result=fn(*args,**kwargs);row['returned_type']=type(result).__name__
   except BaseException as exc:row['exception']=f'{type(exc).__name__}: {exc}';raise
   if name=='_ensure_describe':
    row['rule_count_after']=int(a.inner.rule_count());row['built']=result is not None
    row['installed_describe_rules']=[r for r in a.inner.export_rules() if 'comprehend_describe_directive' in str(r.get('name',r.get('id','')))]
   if name=='_act_describe_scene':
    agent=args[0];inbound=args[2];mid=int(inbound.value if hasattr(inbound,'value') else inbound);before=set(row['describe_goal_ids_before']);new=[]
    for g in agent.s.nodes('Goal'):
     gid=int(g.value if hasattr(g,'value') else g);attrs=agent.s.node(g)['attrs']
     if attrs.get('kind')=='describe_scene' and gid not in before:
      parents=[int(m.value if hasattr(m,'value') else m) for m in agent.inner.neighbours(g,'comprehends')]
      described=[int(s.value if hasattr(s,'value') else s) for s in agent.inner.neighbours(g,'describes')]
      new.append({'id':gid,'attrs':dict(attrs),'comprehends_message_ids':parents,'bound_to_inbound':mid in parents,'described_scene_ids':described})
    row['new_describe_goals']=new
   if isinstance(result,dict):row['summary']={k:(int(v.value) if hasattr(v,'value') else v) for k,v in result.items() if k in ('route','goal_kind','note','acted','reply','concern')}
   trace.append(row);return result
  return call
 names=('_ensure_describe','_act_describe_scene','act_on_instruction','ask_back');original={n:getattr(ca,n) for n in names}
 for n in names:setattr(ca,n,wrap(n,original[n]))
 rows=[]
 try:
  for condition in b.TASKS:
   prompt,speech=b.TASKS[condition];active['condition']=condition
   try:reply=str(a.converse(prompt,speech_act=speech,speaker='alice'));error=None
   except BaseException as exc:reply='';error=f'{type(exc).__name__}: {exc}'
   found=[m for m in a.s.nodes('Message') if a.s.node(m)['attrs'].get('from')=='interlocutor' and a.s.node(m)['attrs'].get('text')==prompt];found.sort(key=b.nid);mid=b.nid(found[-1]) if found else None
   attrs=a.s.node(found[-1])['attrs'] if found else {};iid=attrs.get('communication_interpretation_id');ia=a.s.node(iid)['attrs'] if iid is not None and a.s.has_node(iid) else {}
   rows.append({'condition':condition,'message_id':mid,'reply':reply,'error':error,'message_fields':{k:attrs.get(k) for k in ('comp_kind','comp_predicate','comp_content','comp_dispatch_path','communication_route','instruction_outcome')},'interpretation_fields':{k:ia.get(k) for k in ('kind','cognitive_disposition','arbitration_basis','language_repair_focus')},'trace':[]})
   rows[-1]['trace']=trace[sum(len(x['trace']) for x in rows[:-1]):]
 finally:
  for n,fn in original.items():setattr(ca,n,fn)
 graph=a.inner.graph_to_dict();digest=hashlib.sha256(json.dumps(graph,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
 return {'replicate':rep,'pid':os.getpid(),'boot_loaded':boot.get('loaded'),'locked_inputs':before,'post_run_inputs':inputs(),'turns':rows,'graph_summary':{'nodes':len(graph['nodes']),'edges':len(graph['edges']),'sha256':digest}}
def main():
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine()
 if sys.argv[1:]==['--worker']:
  print(json.dumps(worker(int(os.environ['OCEL0_ROUTE_DIAG_REP'])),separators=(',',':'),default=str));return
 locked=inputs()
 if sys.argv[1:]==['--lock']:
  LOCK.write_text(json.dumps({'locked_inputs':locked},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('stale/missing source lock')
 if OUT.exists():raise SystemExit('capture exists')
 runs=[]
 for rep in range(2):
  env=os.environ.copy();env['OCEL0_ROUTE_DIAG_REP']=str(rep);p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
  if p.returncode:raise SystemExit(p.stderr[-2000:])
  runs.append(json.loads(p.stdout))
 checks={'two_distinct_workers':len(runs)==2 and len({r['pid'] for r in runs})==2,'stable_sources':all(r['locked_inputs']==locked==r['post_run_inputs'] for r in runs),'five_prompts':all(len(r['turns'])==5 for r in runs),'all_messages_resolve':all(t['message_id'] is not None for r in runs for t in r['turns'])}
 result={'schema':'ConversationRouteFailureDiagnosticsV1_2','locked_inputs':locked,'checks':checks,'passed':all(checks.values()),'runs':runs,'claim_boundary':'Two workers, one fixed five-task order. No-op instrumentation captures the native installed rule and newly minted Goal links; it does not establish prevalence or prompt validity.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'output':str(OUT.relative_to(ROOT))},indent=2))
 if not result['passed']:raise SystemExit('capture gates failed')
if __name__=='__main__':main()
