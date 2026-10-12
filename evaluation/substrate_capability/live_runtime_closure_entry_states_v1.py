#!/usr/bin/env python3
"""Capture exact primary graph/rule states before each live run_rules call."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
from substrate.world_adapter import WorldAdapter
PARENT=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_6.py';PARENT_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json';PARENT_RAW=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz';PARENT_ANALYSIS=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json'
CAPTURE=ROOT/'evaluation/reports/live_runtime_store_states_v1_2_20261004.json';CAPTURE_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_store_states_v1_2_lock_20261004.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_CLOSURE_ENTRY_STATES_V1_PREREG_20261004.md';RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_runtime_closure_entry_states_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_entry_states_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v1_20261004.json';DATA=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v1_payloads'
spec=importlib.util.spec_from_file_location('closure_entry_parent',PARENT);P=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(P)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 cap=json.loads(CAPTURE.read_text());caplock=json.loads(CAPTURE_LOCK.read_text())['locked_inputs']
 if not cap.get('source_stable') or cap.get('locked_inputs')!=caplock or cap.get('post_run_inputs')!=caplock:raise SystemExit('v1.2 store capture is stale or failed source lock')
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'parent_runner_sha256':sha(PARENT),'parent_lock_sha256':sha(PARENT_LOCK),'parent_capture_sha256':sha(PARENT_RAW),'parent_analysis_sha256':sha(PARENT_ANALYSIS),'parent_worker_inputs':P.lock_inputs(),'store_capture_sha256':sha(CAPTURE),'store_capture_lock_sha256':sha(CAPTURE_LOCK),'native_sha256':sha(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()
def projection(task):return [{'route':t.get('route'),'reply_nonempty':t.get('reply_nonempty'),'goal_count':t.get('goal_count'),'goal':{k:t.get('goal',{}).get(k) for k in ('kind','status','transition_kinds','transition_links_all_bound','closed')} if isinstance(t.get('goal'),dict) else None} for t in task.get('turns',[])]
def normalized_counters(observations):
 rows=[]
 for obs in observations or []:
  c=obs.get('counter_rows',{});g={k:v for k,v in c.get('global',[]) if not k.endswith('_ns') and k!='scheduler_plan_ns'}
  rows.append({'prompt':obs.get('prompt'),'global':g,'per_rule':c.get('per_rule'),'clauses':c.get('clauses'),'metadata':c.get('metadata'),'identities':c.get('identities'),'edge_candidates':c.get('edge_candidates')})
 return rows
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists() or DATA.exists():raise SystemExit('refusing to overwrite prior closure-entry capture')
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeClosureEntryStatesV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine();locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale closure-entry source lock')
 records=[];original_converse=WorldAdapter.converse
 def capture_request(agent,*args,**kwargs):
  facade=agent.inner;cache=facade._method_cache;old=cache.get('run_rules');had='run_rules' in cache
  if old is None:old=facade.run_rules
  request_i=len(records)+1;calls=[];seen={}
  def capture_run_rules(*run_args,**run_kwargs):
   graph=facade.graph_to_dict();rules=facade.export_rules();blob=canonical({'graph':graph,'rules':rules});digest=hashlib.sha256(blob).hexdigest()
   if digest not in seen:
    name=f'request_{request_i}_state_{len(seen)+1}_{digest[:16]}.json.gz';path=DATA/name;path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.GzipFile(filename=str(path),mode='wb',mtime=0,compresslevel=6) as stream:stream.write(blob)
    seen[digest]={'path':(Path('evaluation/reports/live_runtime_closure_entry_states_v1_payloads')/name).as_posix(),'state_sha256':digest,'uncompressed_bytes':len(blob)}
   max_steps=int(run_args[0]) if run_args else int(run_kwargs.get('max_steps',100_000))
   calls.append({'call_index':len(calls),'state_sha256':digest,'max_steps':max_steps})
   return old(*run_args,**run_kwargs)
  cache['run_rules']=capture_run_rules
  try:reply=original_converse(agent,*args,**kwargs)
  finally:
   if had:cache['run_rules']=old
   else:cache.pop('run_rules',None)
  records.append({'prompt':str(args[0]) if args else None,'reply':reply,'calls':calls,'states':list(seen.values())})
  return reply
 WorldAdapter.converse=capture_request
 try:payload=P.worker(0,'on')
 finally:WorldAdapter.converse=original_converse
 with gzip.open(PARENT_RAW,'rt',encoding='utf-8') as f:raw=json.load(f)
 parent=next(r for r in raw['runs'] if r.get('replicate')==0 and r.get('audit_mode')=='on')
 parity={'task':projection(payload.get('task_result',{}))==projection(parent.get('task_result',{})),'replies':[r['reply'] for r in records]==[r.get('reply') for r in parent.get('requests',[])],'graph_digest':payload.get('graph_semantic_sha256')==parent.get('graph_semantic_sha256'),'behavioral_counters':normalized_counters(payload.get('native_counter_observations'))==normalized_counters(parent.get('native_counter_observations'))}
 post=inputs();result={'schema':'LiveRuntimeClosureEntryStatesV1','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'replicate':0,'audit_mode':'on','requests':records,'native_counter_observations':payload.get('native_counter_observations'),'task_result':payload.get('task_result'),'graph_semantic_sha256':payload.get('graph_semantic_sha256'),'parent_parity':parity,'all_checks_pass':locked==post and len(records)==2 and all(records[i]['calls'] for i in range(2)) and all(parity.values())}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_checks_pass':result['all_checks_pass'],'source_stable':result['source_stable'],'calls_per_request':[len(x['calls']) for x in records],'unique_states_per_request':[len(x['states']) for x in records],'parent_parity':parity,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
