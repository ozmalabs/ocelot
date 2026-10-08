#!/usr/bin/env python3
"""Current-source live conversation workers with paired native rule counters."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,os,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_1_20261004.json.gz'
OUT=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_1_analysis_20261004.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_1.py'
BASE_RUNNER=ROOT/'scripts/substrate_live_frame_interface_capture_v1.py'
BASE_ANALYZER=ROOT/'scripts/analyze_live_frame_rule_scope_capture_v1_2.py'
BASE_RAW=ROOT/'evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz'
BASE_SUMMARY=ROOT/'evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_20261004.json'
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
SPEC=importlib.util.spec_from_file_location('live_frame_capture_for_runtime_counters',BASE_RUNNER)
BASE=importlib.util.module_from_spec(SPEC);assert SPEC and SPEC.loader;SPEC.loader.exec_module(BASE)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(Path(__file__).resolve()),'analyzer_sha256':sha(ANALYZER),'base_runner_sha256':sha(BASE_RUNNER),'base_analyzer_sha256':sha(BASE_ANALYZER),'base_raw_sha256':sha(BASE_RAW),'base_summary_sha256':sha(BASE_SUMMARY),'base_worker_inputs':BASE.lock_inputs(),'native_sha256':sha(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def worker(rep,mode):
 print('DBG start',flush=True);assert_measuring_engine();print('DBG asserted',flush=True);started=lock_inputs();print('DBG locked',flush=True)
 from substrate_rs import _native
 from substrate.world_adapter import WorldAdapter
 N=_native.Substrate; original=WorldAdapter.converse;observations=[]
 def counted(agent,*args,**kwargs):
  print('DBG counted enter',flush=True);inner=agent.inner;N.scale_audit_set_enabled(False);N.scale_audit_set_per_rule_enabled(False);N.scale_audit_reset();N.scale_audit_per_rule_reset()
  print('DBG before reset',flush=True);before=inner.export_rules();print('DBG exported before',len(before),flush=True)
  if mode=='on':N.scale_audit_set_per_rule_enabled(True);N.scale_audit_set_enabled(True)
  print('DBG converse start',flush=True);result=original(agent,*args,**kwargs);print('DBG converse done',flush=True)
  after=inner.export_rules();print('DBG exported after',len(after),flush=True)
  uid_definitions=[{'uid':int(rule['rule_uid']),'name':rule.get('name'),'definition_sha256':hashlib.sha256(json.dumps(rule,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()} for rule in after if 'rule_uid' in rule]
  print('DBG counters start',flush=True);counters={'global':[list(x) for x in N.scale_audit_snapshot()],'per_rule':[list(x) for x in N.scale_audit_per_rule_snapshot()],'clauses':[list(x) for x in N.scale_audit_match_clause_snapshot()],'metadata':[list(x) for x in N.scale_audit_rule_metadata_snapshot()],'edge_candidates':[list(x) for x in inner.scale_audit_match_edge_snapshot()]}
  print('DBG counters done',flush=True);observations.append({'prompt':str(args[0]) if args else None,'before_rule_count':len(before),'after_rule_count':len(after),'uid_definitions':uid_definitions,'counter_rows':counters})
  N.scale_audit_set_enabled(False);N.scale_audit_set_per_rule_enabled(False)
  return result
 WorldAdapter.converse=counted
 try:print('DBG worker start',flush=True);payload=BASE.instrumented_worker(rep);print('DBG worker done',flush=True)
 finally:WorldAdapter.converse=original
 payload['audit_mode']=mode;payload['native_counter_observations']=observations;payload['worker_started_inputs']=started;payload['worker_finished_inputs']=lock_inputs()
 if mode=='off':
  payload.pop('full_graph',None);payload.pop('native_exported_rules',None)
 return payload
def main():
 if sys.argv[1:]==['--worker']:
  rep=int(sys.argv[2]);mode=sys.argv[3];print(json.dumps(worker(rep,mode),sort_keys=True,default=str));return 0
 if sys.argv[1:]==['--lock']:
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeClosureCountersV1_1Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine();locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source lock')
 env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1','PYTHONHASHSEED':'0','PYTHONPATH':os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),os.environ.get('PYTHONPATH','')))}
 jobs=[(rep,mode) for rep in (0,1,2) for mode in ('off','on')];random.Random(20261004).shuffle(jobs);runs=[]
 for i,(rep,mode) in enumerate(jobs,1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(rep),mode],cwd=ROOT,env=env,text=True,capture_output=True)
  try:row=json.loads(cp.stdout)
  except Exception:row={'replicate':rep,'audit_mode':mode,'worker_error':'invalid_json','returncode':cp.returncode,'stdout_tail':cp.stdout[-2000:],'stderr_tail':cp.stderr[-2000:]}
  row['worker_returncode']=cp.returncode;runs.append(row);print(f'worker {i}/6 rep={rep} audit={mode} rc={cp.returncode}',flush=True)
 post=lock_inputs();result={'schema':'LiveRuntimeClosureCountersV1_1','run_id':'live-runtime-closure-counters-v1-20261004','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'design':{'replicates':[0,1,2],'modes':['off','on'],'prompts':list(BASE.PROMPTS),'workers':len(runs),'claim_limit':'selected two-request production-route panel'},'runs':runs,'all_checks_pass':locked==post and len(runs)==6 and all('capture'in x and x.get('worker_returncode')==0 for x in runs)}
 with gzip.open(RAW,'wt',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
 print(json.dumps({'workers':len(runs),'source_stable':result['source_stable'],'all_worker_payloads_present':result['all_checks_pass'],'raw':RAW.relative_to(ROOT).as_posix()}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
