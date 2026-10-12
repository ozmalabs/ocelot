#!/usr/bin/env python3
"""Record dirty-rule counts/names before each primary live closure call."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
from substrate_rs import _native
from substrate.world_adapter import WorldAdapter
PARENT=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_6.py';PARENT_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json';PARENT_RAW=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz';PARENT_ANALYSIS=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json'
ENTRY=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v1_1_20261004.json';ENTRY_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_entry_states_v1_1_lock_20261004.json';ENTRY_ANALYSIS=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v1_1_analysis_20261004.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_DIRTY_RULE_ENTRY_AUDIT_V1_PREREG_20261004.md';RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_live_runtime_dirty_rule_entry_audit_v1.py';LOCK=ROOT/'evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_20261004.json'
spec=importlib.util.spec_from_file_location('dirty_rule_parent',PARENT);P=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(P)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 entry=json.loads(ENTRY.read_text());elock=json.loads(ENTRY_LOCK.read_text())['locked_inputs'];analysis=json.loads(ENTRY_ANALYSIS.read_text())
 if not entry.get('source_stable') or entry.get('locked_inputs')!=elock or entry.get('post_run_inputs')!=elock or not analysis.get('passed'):raise SystemExit('closure-entry reference capture stale or failed')
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'parent_runner_sha256':sha(PARENT),'parent_lock_sha256':sha(PARENT_LOCK),'parent_capture_sha256':sha(PARENT_RAW),'parent_analysis_sha256':sha(PARENT_ANALYSIS),'parent_worker_inputs':P.lock_inputs(),'entry_capture_sha256':sha(ENTRY),'entry_lock_sha256':sha(ENTRY_LOCK),'entry_analysis_sha256':sha(ENTRY_ANALYSIS),'native_sha256':sha(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def projection(task):return [{'route':t.get('route'),'reply_nonempty':t.get('reply_nonempty'),'goal_count':t.get('goal_count'),'goal':{k:t.get('goal',{}).get(k) for k in ('kind','status','transition_kinds','transition_links_all_bound','closed')} if isinstance(t.get('goal'),dict) else None} for t in task.get('turns',[])]
def normalized(observations):
 out=[]
 for o in observations or []:
  c=o['counter_rows'];g={k:v for k,v in c['global'] if not k.endswith('_ns') and k!='scheduler_plan_ns'};out.append({'prompt':o.get('prompt'),'global':g,'per_rule':c['per_rule'],'clauses':c['clauses'],'metadata':c['metadata'],'identities':c['identities'],'edge_candidates':c['edge_candidates']})
 return out
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite dirty-rule audit')
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeDirtyRuleEntryAuditV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 assert_measuring_engine();locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale dirty-rule audit lock')
 rows=[];original=WorldAdapter.converse
 def capture(agent,*args,**kwargs):
  facade=agent.inner;cache=facade._method_cache;old=cache.get('run_rules');had='run_rules' in cache
  if old is None:old=facade.run_rules
  calls=[]
  def wrapped(*ra,**rk):
   names=[list(x) for x in facade.dirty_rule_names()];count=int(facade.dirty_rule_count());rule_rows=facade.export_rules();keys={};by_name={}
   for i,r in enumerate(rule_rows):
    keys.setdefault((str(r.get('name')),str(r.get('area','global'))),[]).append(i);by_name.setdefault(str(r.get('name')),[]).append(i)
   mapped=[];ambiguous=[]
   for name,area in names:
    matches=keys.get((str(name),str(area)),[]) or by_name.get(str(name),[])
    if len(matches)==1:mapped.append(matches[0])
    else:ambiguous.append({'name':name,'area':area,'candidate_indices':matches})
   calls.append({'call_index':len(calls),'dirty_rule_count':count,'dirty_rule_names':names,'dirty_rule_local_indices':mapped,'ambiguous_names':ambiguous,'active_rule_count':sum(bool(r.get('active',True)) for r in rule_rows)})
   return old(*ra,**rk)
  cache['run_rules']=wrapped
  try:reply=original(agent,*args,**kwargs)
  finally:
   if had:cache['run_rules']=old
   else:cache.pop('run_rules',None)
  rows.append({'prompt':str(args[0]) if args else None,'reply':reply,'calls':calls});return reply
 WorldAdapter.converse=capture
 try:payload=P.worker(0,'on')
 finally:WorldAdapter.converse=original
 with gzip.open(PARENT_RAW,'rt',encoding='utf-8') as f:raw=json.load(f)
 parent=next(x for x in raw['runs'] if x.get('replicate')==0 and x.get('audit_mode')=='on')
 parity={'task':projection(payload.get('task_result',{}))==projection(parent.get('task_result',{})),'replies':[x['reply'] for x in rows]==[x.get('reply') for x in parent['requests']],'graph_digest':payload.get('graph_semantic_sha256')==parent.get('graph_semantic_sha256'),'behavioral_counters':normalized(payload.get('native_counter_observations'))==normalized(parent.get('native_counter_observations'))}
 post=inputs();result={'schema':'LiveRuntimeDirtyRuleEntryAuditV1','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'requests':rows,'work_rows':[[{'operation_id':r[0],'name':r[2],'value':r[4]} for r in q.get('work_rows',[]) if r[2] in ('scheduler_selected_rules','scheduler_pass','scheduler_fixedpoint_probe_slots')] for q in parent['requests']],'parent_parity':parity,'all_checks_pass':locked==post and len(rows)==2 and all(parity.values())}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'all_checks_pass':result['all_checks_pass'],'calls_per_request':[len(x['calls']) for x in rows],'parent_parity':parity,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
