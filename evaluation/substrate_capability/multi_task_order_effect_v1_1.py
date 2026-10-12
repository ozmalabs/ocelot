#!/usr/bin/env python3
"""Counterbalanced five-task sequence with direct action-route and graph capture."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_multi_task_order_effect_v1_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_MULTI_TASK_ORDER_EFFECT_V1_1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/multi_task_order_effect_v1_1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/multi_task_order_effect_v1_1_20261004.json.gz'
SOURCE_DEPS=['domains/conversation_action.py','domains/reflective_faculty.py','substrate/world_adapter.py','scripts/arc_self_report.py','domains/language_world.py','domains/language_production.py','scripts/language_test.py','seeds/composer_comprehension_graph.json']
CONDITIONS=['scene_description','unknown_word_clarification','held_self_knowledge_answer','concern_authoring','self_report_action']
ORDERS=[CONDITIONS[i:]+CONDITIONS[:i] for i in range(5)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('order_effect_base',BASE);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def inputs():
 m=load_base();return {'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'base_runner_sha256':sha(BASE),'direct_source_dependencies':{p:sha(ROOT/p) for p in SOURCE_DEPS},'base_inputs':m.inputs()}
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in {'ts','runtime_s'}}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
def worker(order_id,rep):
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine();before=inputs();b=load_base()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());boot=load_all_seeds(a);ca.attach_scene(a,b.SCENE)
 teacher={'count':0}
 try:a.set_self_teacher(lambda q:(teacher.__setitem__('count',teacher['count']+1),'teacher')[1])
 except Exception:pass
 original=ca.act_on_instruction;active={'condition':None};actions=[]
 def wrapped(agent,comp,inbound=None):
  out=original(agent,comp,inbound);actions.append({'condition':active['condition'],**{k:out.get(k) for k in ('route','goal_kind','reply','concern')}});return out
 ca.act_on_instruction=wrapped
 turn_rows=[]
 try:
  for condition in ORDERS[order_id]:
   prompt,speech_act=b.TASKS[condition];active['condition']=condition;teacher_before=teacher['count'];t0=time.perf_counter_ns()
   error=None
   try:reply=str(a.converse(prompt,speech_act=speech_act,speaker='alice'))
   except BaseException as exc:reply='';error=f'{type(exc).__name__}: {exc}'
   elapsed=time.perf_counter_ns()-t0
   inbound=[m for m in a.s.nodes('Message') if a.s.node(m)['attrs'].get('from')=='interlocutor' and a.s.node(m)['attrs'].get('text')==prompt];inbound.sort(key=b.nid);msg=inbound[-1] if inbound else None;msgid=b.nid(msg) if msg else None
   linked=[];outbound=[]
   if msg:
    for g in a.s.nodes('Goal'):
     if msg not in a.inner.neighbours(g,'comprehends'):continue
     ga=a.s.node(g)['attrs'];state=a.s.node(msg)['attrs'].get('discourse_state_id');events=[]
     if state is not None:
      for e in a.inner.neighbours(state,'has_event'):
       if g in a.inner.neighbours(e,'for_goal'):events.append(a.s.node(e)['attrs'].get('kind'))
     linked.append({'id':b.nid(g),'kind':ga.get('kind'),'status':ga.get('lifecycle_status'),'events':events})
    for m in a.s.nodes('Message'):
     aa=a.s.node(m)['attrs']
     if aa.get('from') in ('agent','adapter') and msg in a.inner.neighbours(m,'responds_to'):
      acts=[a.s.node(x)['attrs'].get('name') for x in a.inner.neighbours(m,'has_speech_act')]
      outbound.append({'text':aa.get('text'),'trouble_source':aa.get('trouble_source'),'expects_response':aa.get('expects_response'),'speech_acts':acts})
   action_rows=[z for z in actions if z['condition']==condition]
   turn_rows.append({'condition':condition,'prompt':prompt,'message_id':msgid,'reply':reply,'error':error,'elapsed_ns':elapsed,'teacher_calls':teacher['count']-teacher_before,'actions':action_rows,'goals':linked,'outbound_messages':outbound})
 finally:ca.act_on_instruction=original
 graph=a.inner.graph_to_dict();digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
 out={'order_id':order_id,'order':ORDERS[order_id],'replicate':rep,'pid':os.getpid(),'boot_loaded':boot.get('loaded'),'locked_inputs':before,'post_run_inputs':inputs(),'turns':turn_rows,'graph':graph,'graph_sha256':digest(graph),'structural_sha256':digest(clean(graph))}
 return out
def contract(t):
 c=t['condition'];acts=t['actions'];routes=[x.get('route') for x in acts];goals=t['goals'];reply=t['reply'];g=lambda kind,events=None:any(x.get('kind')==kind and x.get('status')=='resolved' and (events is None or x.get('events')==events) for x in goals)
 if c=='scene_description':return {'pass':reply==load_base().EXPECTED_SCENE and g('describe_scene',['selection','execution','action_result']),'criteria':['expected exact scene reply','resolved describe_scene Goal lifecycle']}
 if c=='held_self_knowledge_answer':return {'pass':'organis' in reply.lower() and not reply.rstrip().endswith('?'),'criteria':['reply names organisation','reply is not a question']}
 if c=='self_report_action':return {'pass':'self_report' in routes and g('report_self',['selection','execution','action_result']) and bool(reply.strip()),'criteria':['direct action route self_report','resolved report_self lifecycle','nonempty reply']}
 if c=='unknown_word_clarification':return {'pass':'quorplezap' in reply.lower() and reply.rstrip().endswith('?') and any('quorplezap' in str(m.get('trouble_source','')).lower() and m.get('expects_response') is True and 'clarification' in m.get('speech_acts',[]) for m in t['outbound_messages']),'criteria':['unknown term named','question surface','outbound clarification request']}
 if c=='concern_authoring':return {'pass':None,'status':'unadjudicated','criteria':['prompt requires comparison objects absent from the fixture; clarification may be correct; independent intent adjudication required']}
 return {'pass':False,'criteria':['unknown condition']}
def main():
 from domains.engine_provenance import assert_measuring_engine
 assert_measuring_engine()
 if sys.argv[1:]==['--lock']:
  LOCK.write_text(json.dumps({'schema':'MultiTaskOrderEffectV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing/stale source lock')
 if OUT.exists():raise SystemExit('capture exists; refusing overwrite')
 runs=[]
 for order_id in range(5):
  for rep in range(2):
   env=os.environ.copy();env.update(OCEL0_ORDER_ID=str(order_id),OCEL0_ORDER_REP=str(rep))
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=600)
   if p.returncode:raise SystemExit(f'worker {order_id}/{rep} failed: {p.stderr[-2000:]}')
   runs.append(json.loads(p.stdout));print(f'completed order={order_id} replicate={rep}',file=sys.stderr,flush=True)
 checks={'ten_workers':len(runs)==10,'distinct_pids':len({r['pid'] for r in runs})==10,'source_lock_stable':all(r['locked_inputs']==locked==r['post_run_inputs'] for r in runs),'five_turns_each':all(len(r['turns'])==5 for r in runs),'all_prompt_ids_resolve':all(all(t['message_id'] is not None for t in r['turns']) for r in runs),'two_replicates_per_order':all(sum(r['order_id']==i for r in runs)==2 for i in range(5))}
 payload={'schema':'MultiTaskOrderEffectV1_1','locked_inputs':locked,'checks':checks,'passed':all(checks.values()),'runs':runs,'contract_results':[{'order_id':r['order_id'],'replicate':r['replicate'],'condition':t['condition'],'position':r['order'].index(t['condition']),'result':contract(t)} for r in runs for t in r['turns']],'claim_boundary':'Five cyclic orders, two fresh workers each, one authored prompt panel. Four tasks have scored task contracts; concern authoring is retained but unscored pending intent adjudication. No natural-task or causal order-effect claim.'}
 with OUT.open('wb') as raw:
  with gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=2,mtime=0) as zipped:
   zipped.write(json.dumps(payload,sort_keys=True,separators=(',',':')).encode())
 scored=[x for x in payload['contract_results'] if x['result']['pass'] is not None]
 print(json.dumps({'passed':payload['passed'],'checks':checks,'contract_passes':sum(x['result']['pass'] for x in scored),'scored_contract_total':len(scored),'unadjudicated':len(payload['contract_results'])-len(scored),'output':str(OUT.relative_to(ROOT))},indent=2))
 if not payload['passed']:raise SystemExit('capture gates failed')
if __name__=='__main__':
 if sys.argv[1:]==['--worker']:
  print(json.dumps(worker(int(os.environ['OCEL0_ORDER_ID']),int(os.environ['OCEL0_ORDER_REP'])),separators=(',',':')))
 else:main()
