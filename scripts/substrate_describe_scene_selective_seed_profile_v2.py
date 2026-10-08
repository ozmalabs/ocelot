#!/usr/bin/env python3
"""Capability/RSS probe for the dependency-closed conversation seed profile."""
import hashlib, importlib.util, json, platform, resource, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_SELECTIVE_SEED_PROFILE_V2_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_scene_selective_seed_profile_v2_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_selective_seed_profile_v2_20260927.json'
TIMING=ROOT/'scripts/substrate_describe_scene_uninstrumented_timing_v2.py'
EXPECTED='I see the grey thing stays, the yellow counter, and the blue thing moves.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 s=importlib.util.spec_from_file_location('timing_v2',TIMING);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'runtime_inputs':m.inputs()}
def memory():
 d={}
 for line in Path('/proc/self/status').read_text().splitlines():
  if line.startswith(('VmRSS:','VmHWM:')):d[line.split(':',1)[0]]=int(line.split()[1])*1024
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  if line.startswith(('Anonymous:','Private_Dirty:','Pss_Anon:')):d[line.split(':',1)[0]]=int(line.split()[1])*1024
 d['ru_maxrss_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024);return d
def nid(n):return int(n.value if hasattr(n,'value') else n)
def main():
 if sys.argv[1:]==['--lock']:
  print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale selective-profile lock')
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 phases=[{'phase':'before_adapter','memory':memory()}]
 adapter=WorldAdapter(seeds=());report=load_all_seeds(adapter,seed_ids=['conversation','comprehend_instruction','communication_intent_arbitration','jabberwock_identity'])
 phases.append({'phase':'after_selective_boot','memory':memory()})
 attach_scene(adapter,[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}]);phases.append({'phase':'after_scene','memory':memory()})
 barrier=threading.Barrier(3);replies={};errors={};timings={}
 def call(k):
  barrier.wait();w=time.perf_counter_ns();c=time.thread_time_ns()
  try:replies[k]=str(adapter.converse('describe what you see',speech_act='instruction',speaker='alice'))
  except BaseException as e:errors[k]=f'{type(e).__name__}: {e}'
  timings[k]={'wall_ns':time.perf_counter_ns()-w,'thread_cpu_ns':time.thread_time_ns()-c}
 ts=[threading.Thread(target=call,args=(k,),name=f'selective-{k}') for k in ('A','B')]
 for t in ts:t.start()
 barrier.wait()
 for t in ts:t.join(180)
 joined=all(not t.is_alive() for t in ts);phases.append({'phase':'after_two_requests','memory':memory()})
 inbound=[m for m in adapter.s.nodes('Message') if adapter.s.node(m)['attrs'].get('from')=='interlocutor' and adapter.s.node(m)['attrs'].get('text')=='describe what you see'];inbound.sort(key=nid);requests=[]
 for m in inbound:
  attrs=adapter.s.node(m)['attrs'];goals=[g for g in adapter.s.nodes('Goal') if m in adapter.inner.neighbours(g,'comprehends')];events=[];st=attrs.get('discourse_state_id')
  if st is not None:
   es=list(adapter.inner.neighbours(st,'has_event'));es.sort(key=lambda e:int(adapter.s.node(e)['attrs'].get('event_index',-1)))
   for e in es:
    ea=adapter.s.node(e)['attrs']
    if any(g in adapter.inner.neighbours(e,'for_goal') for g in goals):events.append(ea.get('kind'))
  requests.append({'goal_count':len(goals),'statuses':[adapter.s.node(g)['attrs'].get('lifecycle_status') for g in goals],'events':events})
 after=inputs();checks={'source_stable':after==locked,'threads_joined':joined,'no_thread_errors':not errors,'two_requests':len(inbound)==2 and set(replies)=={'A','B'},'resolved_request_lifecycles':len(requests)==2 and all(r['goal_count']==1 and r['statuses']==['resolved'] and r['events']==['selection','execution','action_result'] for r in requests),'expected_public_reply':all(x==EXPECTED for x in replies.values()),'selection_complete':report.get('selection_complete') is True and report.get('status')!='selection_incomplete'}
 compact={k:report.get(k) for k in ('status','total','corpus_total','loaded','concepts','microtheories','failed','rules_skipped','order','selection_complete')}
 out={'schema_version':1,'run_id':'describe-scene-selective-seed-profile-v2-20260927','locked_inputs':locked,'post_run_inputs':after,'checks':checks,'all_checks_pass':all(checks.values()),'seed_selection':compact,'phases':phases,'replies':replies,'thread_errors':errors,'thread_timings':timings,'requests':requests,'environment':{'python':sys.version,'platform':platform.platform()},'claim_boundary':'One selective conversation profile is compared with the previously measured full-seed profile; this does not show it retains general capability.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'seed_selection':compact,'phase_memory':[{ 'phase':p['phase'],'rss_gib':round(p['memory'].get('VmRSS',0)/2**30,3),'peak_gib':round(p['memory'].get('ru_maxrss_bytes',0)/2**30,3)} for p in phases],'replies':replies},indent=2))
 if not all(checks.values()):raise SystemExit('selective seed profile gate failed')
if __name__=='__main__':main()
