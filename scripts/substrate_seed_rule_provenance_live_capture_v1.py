#!/usr/bin/env python3
"""Capture seed load intervals over the native rule table and live accesses."""
import hashlib, importlib.util, json, sys, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_SEED_RULE_PROVENANCE_LIVE_CAPTURE_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/seed_rule_provenance_live_capture_v1_lock_20260927.json'
TRACE=ROOT/'scripts/substrate_live_describe_scene_access_trace_v2_4.py'
OUT=ROOT/'evaluation/reports/seed_rule_provenance_live_capture_v1_20260927.json'
EXPECTED='I see the grey thing stays, the yellow counter, and the blue thing moves.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def trace_module():
 s=importlib.util.spec_from_file_location('trace_v24',TRACE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def inputs():return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'runtime_inputs':trace_module().lock_inputs()}
def main():
 if sys.argv[1:]==['--lock']:
  print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale rule-provenance lock')
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 a=WorldAdapter(seeds=());inner=a.inner;original=inner.load_seed_manifest;intervals=[]
 def observed(manifest,*args,**kwargs):
  sid=str(manifest.get('id') or manifest.get('seed_id') or '<missing-seed-id>');before=int(inner.rule_count());error=None;result=None
  try:result=original(manifest,*args,**kwargs);return result
  except BaseException as exc:error=f'{type(exc).__name__}: {exc}';raise
  finally:
   after=int(inner.rule_count());intervals.append({'seed_id':sid,'rule_index_start':before,'rule_index_end_exclusive':after,'new_rule_count':after-before,'error':error})
 inner.load_seed_manifest=observed
 try:boot=load_all_seeds(a)
 finally:inner.load_seed_manifest=original
 seed_terminal_rule_count=int(inner.rule_count())
 from domains.conversation_action import attach_scene
 import domains.conversation_action as ca
 attach_scene(a,[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}])
 scene_terminal_rule_count=int(inner.rule_count())
 inner.runtime_access_trace_set_enabled(False);inner.runtime_access_trace_reset();barrier=threading.Barrier(3);replies={};errors={};faculty_builds=[];conceptualizer_builds=[]
 original_ensure=ca._ensure_describe
 original_conceptualize=ca._conceptualize_scene_lines
 def observed_ensure(agent):
  before=int(inner.rule_count());result=original_ensure(agent);after_count=int(inner.rule_count())
  faculty_builds.append({'thread':threading.current_thread().name,'rule_count_before':before,'rule_count_after':after_count,'new_rules':after_count-before})
  return result
 def observed_conceptualize(agent,lines):
  before=int(inner.rule_count());result=original_conceptualize(agent,lines);after_count=int(inner.rule_count())
  conceptualizer_builds.append({'thread':threading.current_thread().name,'rule_count_before':before,'rule_count_after':after_count,'new_rules':after_count-before})
  return result
 ca._ensure_describe=observed_ensure
 ca._conceptualize_scene_lines=observed_conceptualize
 def call(label):
  barrier.wait()
  try:replies[label]=str(a.converse('describe what you see',speech_act='instruction',speaker='alice'))
  except BaseException as exc:errors[label]=f'{type(exc).__name__}: {exc}'
 inner.runtime_access_trace_reset();inner.runtime_access_trace_set_enabled(True)
 workers=[threading.Thread(target=call,args=(name,),name=f'provenance-{name}') for name in ('A','B')]
 for t in workers:t.start()
 barrier.wait()
 for t in workers:t.join(180)
 joined=all(not t.is_alive() for t in workers);inner.runtime_access_trace_set_enabled(False);trace_rows,dropped=inner.runtime_access_trace_snapshot()
 ca._ensure_describe=original_ensure
 ca._conceptualize_scene_lines=original_conceptualize
 rules=[]
 for row in inner.rule_access_sets():
  idx=int(row[0]);metadata=inner.rule_metadata(idx)
  rules.append({'rule_index':idx,'rule_uid':int(metadata['rule_uid']),'name':str(row[1]),'active':bool(row[2])})
 by_idx={r['rule_index']:r for r in rules};uid_to_index={r['rule_uid']:r['rule_index'] for r in rules};access=[]
 for uid,kind,node,resource,peer,count in trace_rows:
  uid=int(uid);idx=uid_to_index.get(uid);meta=by_idx.get(idx,{})
  access.append({'rule_uid':uid,'rule_index':idx,'rule_name':meta.get('name'),'kind':str(kind),'node':None if node is None else int(node),'resource':None if resource is None else str(resource),'peer':None if peer is None else int(peer),'count':int(count)})
 inbound=[m for m in a.s.nodes('Message') if a.s.node(m)['attrs'].get('from')=='interlocutor' and a.s.node(m)['attrs'].get('text')=='describe what you see'];inbound.sort(key=lambda m:int(m.value if hasattr(m,'value') else m));requests=[]
 for message in inbound:
  goals=[g for g in a.s.nodes('Goal') if message in inner.neighbours(g,'comprehends')];attrs=a.s.node(message)['attrs'];events=[];st=attrs.get('discourse_state_id')
  if st is not None:
   es=list(inner.neighbours(st,'has_event'));es.sort(key=lambda e:int(a.s.node(e)['attrs'].get('event_index',-1)))
   for event in es:
    ea=a.s.node(event)['attrs']
    if any(g in inner.neighbours(event,'for_goal') for g in goals):events.append(ea.get('kind'))
  requests.append({'goal_count':len(goals),'statuses':[a.s.node(g)['attrs'].get('lifecycle_status') for g in goals],'events':events})
 after=inputs()
 out={'schema_version':1,'run_id':'seed-rule-provenance-live-capture-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'source_stable':locked==after,'boot_report':{k:boot.get(k) for k in ('total','loaded','concepts','microtheories','failed','rules_skipped','rules_materialised','order')},'initial_native_rule_count':intervals[0]['rule_index_start'] if intervals else 0,'seed_terminal_rule_count':seed_terminal_rule_count,'scene_terminal_rule_count':scene_terminal_rule_count,'native_rule_count':len(rules),'seed_load_intervals':intervals,'native_rules':rules,'faculty_builds':faculty_builds,'conceptualizer_builds':conceptualizer_builds,'trace_rows':access,'trace_event_count':sum(r['count'] for r in access),'trace_dropped':int(dropped),'threads_joined':joined,'thread_errors':errors,'replies':replies,'requests':requests,'same_task_expected_reply':all(x==EXPECTED for x in replies.values())}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'source_stable':out['source_stable'],'seed_loads':len(intervals),'native_rule_count':len(rules),'trace_events':out['trace_event_count'],'trace_dropped':out['trace_dropped'],'boot_loaded':boot.get('loaded'),'boot_failures':len(boot.get('failed',[])),'replies':replies},indent=2))
 if not out['source_stable'] or not joined:raise SystemExit('provenance capture source/join failure')
if __name__=='__main__':main()
