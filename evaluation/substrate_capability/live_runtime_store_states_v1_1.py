#!/usr/bin/env python3
"""Capture first matcher-entry state for stores in one locked live request pair."""
from __future__ import annotations
import gzip, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
from substrate.world_adapter import WorldAdapter
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_STORE_STATES_V1_1_PREREG_20261004.md'
RUNNER=Path(__file__).resolve(); ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_runtime_store_states_v1_1.py'
PARENT=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_6.py'
PARENT_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json'
PARENT_RAW=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz'
PARENT_ANALYSIS=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_store_states_v1_1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/live_runtime_store_states_v1_1_20261004.json'
DATA=ROOT/'evaluation/reports/live_runtime_store_states_v1_1_payloads'
spec=importlib.util.spec_from_file_location('live_runtime_store_parent',PARENT);P=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(P)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def lock_inputs():
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'parent_runner_sha256':sha(PARENT),'parent_lock_sha256':sha(PARENT_LOCK),'parent_capture_sha256':sha(PARENT_RAW),'parent_analysis_sha256':sha(PARENT_ANALYSIS),'parent_worker_inputs':P.lock_inputs(),'native_sha256':sha(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists() or DATA.exists():raise SystemExit('refusing to overwrite existing store-state capture')
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeStoreStatesV1_1Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine(); locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source lock')
 rows=[];original=WorldAdapter.converse
 def capture(agent,*args,**kwargs):
  _native.Substrate.scale_audit_reset_rule_store_state_snapshots();_native.Substrate.scale_audit_set_rule_store_state_capture_enabled(True)
  reply=original(agent,*args,**kwargs)
  _native.Substrate.scale_audit_set_rule_store_state_capture_enabled(False)
  out=[]
  for store_id,raw in _native.Substrate.scale_audit_rule_store_state_snapshots():
   parsed=json.loads(raw);canonical=json.dumps(parsed,sort_keys=True,separators=(',',':'),default=str).encode();name=f'request_{len(rows)+1}_store_{store_id}.json.gz';path=DATA/name;path.parent.mkdir(parents=True,exist_ok=True)
   with gzip.open(path,'wb',compresslevel=6) as f:f.write(canonical)
   out.append({'store_id':int(store_id),'path':(Path('evaluation/reports/live_runtime_store_states_v1_1_payloads')/name).as_posix(),'state_sha256':hashlib.sha256(canonical).hexdigest(),'uncompressed_bytes':len(canonical)})
  rows.append({'prompt':str(args[0]) if args else None,'reply':reply,'stores':out})
  return reply
 WorldAdapter.converse=capture
 try:payload=P.worker(0,'on')
 finally:
  WorldAdapter.converse=original;_native.Substrate.scale_audit_set_rule_store_state_capture_enabled(False)
 with gzip.open(PARENT_RAW,'rt',encoding='utf-8') as f:parent_capture=json.load(f)
 candidates=[r for r in parent_capture['runs'] if r.get('replicate')==0 and r.get('audit_mode')=='on']
 if len(candidates)!=1:raise SystemExit('parent fixed sample is not unique')
 parent_run=candidates[0]
 def normalized_counters(observations):
  rows=[]
  for obs in observations or []:
   c=obs.get('counter_rows',{});g={k:v for k,v in c.get('global',[]) if not k.endswith('_ns') and k!='scheduler_plan_ns'}
   rows.append({'prompt':obs.get('prompt'),'global':g,'per_rule':c.get('per_rule'),'clauses':c.get('clauses'),'metadata':c.get('metadata'),'identities':c.get('identities'),'edge_candidates':c.get('edge_candidates')})
  return rows
 def projection(task):return [{'route':t.get('route'),'reply_nonempty':t.get('reply_nonempty'),'goal_count':t.get('goal_count'),'goal':{k:t.get('goal',{}).get(k) for k in ('kind','status','transition_kinds','transition_links_all_bound','closed')} if isinstance(t.get('goal'),dict) else None} for t in task.get('turns',[])]
 parity={'task':projection(payload.get('task_result',{}))==projection(parent_run.get('task_result',{})),'replies':[r['reply'] for r in rows]==[r.get('reply') for r in parent_run.get('requests',[])],'graph_digest':payload.get('graph_semantic_sha256')==parent_run.get('graph_semantic_sha256'),'behavioral_counters':normalized_counters(payload.get('native_counter_observations'))==normalized_counters(parent_run.get('native_counter_observations'))}
 post=lock_inputs();result={'schema':'LiveRuntimeStoreStatesV1_1','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'replicate':0,'audit_mode':'on','requests':rows,'task_result':payload.get('task_result'),'graph_semantic_sha256':payload.get('graph_semantic_sha256'),'native_counter_observations':payload.get('native_counter_observations'),'parent_parity':parity,'all_checks_pass':locked==post and len(rows)==2 and all(parity.values())}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'all_checks_pass':result['all_checks_pass'],'request_count':len(rows),'stores_per_request':[len(r['stores']) for r in rows],'parent_parity':parity,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
