#!/usr/bin/env python3
"""Join current live task rule patterns to native per-event candidate work."""
from __future__ import annotations
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from domains.engine_provenance import assert_measuring_engine
BASE=ROOT/'scripts/substrate_live_describe_scene_access_trace_v2_1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_TASK_RUNTIME_JOIN_CAPTURE_V1_PREREG_20260927.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_TASK_RUNTIME_JOIN_CAPTURE_V1_AMENDMENT_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/live_task_runtime_join_capture_v1_lock_20260927.json'
RAW=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_workers_raw_20260927.json'
GRAPH=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_runtime_graph_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_20260927.json'
ANALYZER=ROOT/'scripts/analyze_substrate_live_task_runtime_join_capture_v1.py'
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical_json(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()
def load_base():
 spec=importlib.util.spec_from_file_location('live_describe_trace_base',BASE);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def fingerprint():
 base=load_base();paths=(str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(BASE.relative_to(ROOT)))
 return {'base_inputs':base.lock_inputs(),'files':{p:sha(ROOT/p) for p in paths},'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def worker(rep):
 base=load_base();patterns={};pattern_history=[];adapter_holder={};active_at_boot=0;checkpoint={};
 import substrate.boot_all as boot_all
 import domains.conversation_action as ca
 def capture_patterns(inner):
  rules=inner.export_rules();access=inner.rule_access_sets()
  if len(rules)!=len(access):raise RuntimeError(f'rule/access slot mismatch {len(rules)} vs {len(access)}')
  result={}
  for slot,(rule,row) in enumerate(zip(rules,access)):
   if int(row[0])!=slot:raise RuntimeError('RuleIdx/export slot mismatch')
   result[slot]={'rule_index':slot,'rule_name':str(row[1]),'active':bool(row[2]),'match':[list(e) for e in rule.get('match',[])],
    'match_arity':len(rule.get('match',[])),'reads':list(row[3]),'term_edge_reads':list(row[4]),'writes':list(row[5])}
  return result
 original_load=boot_all.load_all_seeds
 def load_capture(adapter,*args,**kwargs):
  nonlocal active_at_boot
  report=original_load(adapter,*args,**kwargs)
  adapter_holder['adapter']=adapter;patterns.update(capture_patterns(adapter.inner));active_at_boot=sum(bool(x['active']) for x in patterns.values())
  inner=adapter.inner;original_snapshot=inner.scale_audit_per_rule_snapshot
  def snapshot_with_rule_patterns():
   rows=original_snapshot();pattern_history.append(capture_patterns(inner));return rows
  inner.scale_audit_per_rule_snapshot=snapshot_with_rule_patterns
  return report
 boot_all.load_all_seeds=load_capture
 original_record=ca._record_live_goal_event
 def capture_pre_action(agent,inbound,goal,kind,*,payload=None):
  if kind=='action_result' and __import__('threading').current_thread().name=='request-B':
   graph=agent.s.graph_to_dict();blob=canonical_json(graph)
   checkpoint.update({'graph':graph if rep==0 else None,'sha256':sha_bytes(blob),'node_count':len(graph.get('nodes',[])),'edge_count':len(graph.get('edges',[])),
    'thread':'request-B','event_kind':kind,'message_id':int(inbound.value if hasattr(inbound,'value') else inbound),'goal_id':int(goal.value if hasattr(goal,'value') else goal)})
  return original_record(agent,inbound,goal,kind,payload=payload)
 ca._record_live_goal_event=capture_pre_action
 before=fingerprint();result=base.worker(rep,False);after=fingerprint()
 work=[];multi=[];producer=result.get('producer_work',[])
 if len(pattern_history)!=len(producer):raise RuntimeError(f'per-event pattern snapshot mismatch {len(pattern_history)} vs {len(producer)}')
 for event,event_patterns in zip(producer,pattern_history):
  metrics={}
  for idx,name,count in event['counters']['per_rule']:
   metrics.setdefault(int(idx),{})[str(name)]=int(count)
  for idx,vals in metrics.items():
   info=event_patterns.get(idx) or patterns.get(idx)
   if not info:raise RuntimeError(f'unmapped RuleIdx {idx} in event-time rule snapshot')
   row={'event_kind':event['kind'],'thread':event['thread'],'goal_id':event['goal_id'],'rule_index':idx,'rule_name':info['rule_name'],
    'match_arity':info['match_arity'],'candidate_tests':vals.get('candidate_tests',0),'candidate_pairs':vals.get('candidate_pairs',0),
    'term_evaluations':vals.get('term_evaluations',0),'where_evaluations':vals.get('where_evaluations',0),'match':info['match']}
   work.append(row)
   if info['active'] and info['match_arity']>=3 and vals.get('candidate_tests',0)>0:multi.append(row)
 result.pop('worker_started_inputs',None);result.pop('worker_finished_inputs',None)
 return {'replicate':rep,'pid':result['pid'],'before':before,'after':after,'task':result,
  'active_rule_count':active_at_boot,'rule_patterns':list(patterns.values()),'event_rule_patterns':pattern_history,
  'producer_rule_work':work,'multi_edge_firing_work':multi,'runtime_graph_checkpoint':{k:v for k,v in checkpoint.items() if k!='graph'},
  'runtime_graph':checkpoint.get('graph')}
def main():
 assert_measuring_engine()
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+'\n');print(LOCK);return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=fingerprint()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit('missing or stale current-source lock')
 runs=[]
 for rep in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(rep)],cwd=ROOT,env={**os.environ,'OZMA_NO_LLM':'1','OZMA_SEED_PERSIST_DISABLED':'1'},text=True,capture_output=True,check=True)
  runs.append(json.loads(p.stdout))
 post=fingerprint();snap=next((r['runtime_graph'] for r in runs if r['runtime_graph'] is not None),None)
 if snap is None:raise RuntimeError('missing representative runtime graph')
 GRAPH.write_bytes(canonical_json(snap)+b'\n');graph_hash=sha_bytes(canonical_json(snap))
 for r in runs:r.pop('runtime_graph',None)
 raw={'schema_version':1,'run_id':'substrate-live-task-runtime-join-capture-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'runtime_graph_path':str(GRAPH.relative_to(ROOT)),'runtime_graph_sha256':graph_hash,'runs':runs}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True,default=str)+'\n')
 payload={'schema_version':1,'raw_path':str(RAW.relative_to(ROOT)),'runtime_graph_path':str(GRAPH.relative_to(ROOT)),'locked_inputs':locked,'post_run_inputs':post,'worker_count':len(runs),'all_worker_inputs_stable':post==locked and all(r['before']==locked==r['after'] for r in runs),'runtime_graph_sha256':graph_hash,'runtime_graph_node_count':len(snap.get('nodes',[])),'runtime_graph_edge_count':len(snap.get('edges',[]))}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps(payload,indent=2))
if __name__=='__main__':main()
