#!/usr/bin/env python3
"""Phase-sampled RSS profile for the full-seed live scene fixture."""
import hashlib, importlib.util, json, platform, resource, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_BOOT_MEMORY_PROFILE_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_scene_boot_memory_profile_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_boot_memory_profile_v1_20260927.json'
TIMING=ROOT/'scripts/substrate_describe_scene_uninstrumented_timing_v2.py'
EXPECTED='I see the grey thing stays, the yellow counter, and the blue thing moves.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 spec=importlib.util.spec_from_file_location('timing_v2',TIMING);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'timing_runtime_inputs':m.inputs()}
def rss():
 d={}
 for line in Path('/proc/self/status').read_text().splitlines():
  if line.startswith(('VmRSS:','VmHWM:')):d[line.split(':',1)[0]]=int(line.split()[1])*1024
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  if line.startswith(('Rss:','Pss:','Pss_Anon:','Pss_File:','Pss_Shmem:','Anonymous:','Private_Dirty:','Shared_Clean:','Shared_Dirty:')):d[line.split(':',1)[0]]=int(line.split()[1])*1024
 d['resource_peak_rss_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
 return d
def main():
 if sys.argv[1:]==['--lock']:
  print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale profile lock')
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains.conversation_action import attach_scene
 phases=[]
 def sample(name):phases.append({'phase':name,'memory':rss()})
 sample('post_interpreter_before_adapter')
 adapter=WorldAdapter(seeds=());sample('post_adapter_construction')
 t=time.perf_counter_ns();load_all_seeds(adapter);boot_ns=time.perf_counter_ns()-t;sample('post_full_seed_boot')
 attach_scene(adapter,[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}]);sample('post_scene_attachment')
 barrier=threading.Barrier(3);replies={};errors={};timings={}
 def call(k):
  barrier.wait();w=time.perf_counter_ns();c=time.thread_time_ns()
  try:replies[k]=str(adapter.converse('describe what you see',speech_act='instruction',speaker='alice'))
  except BaseException as e:errors[k]=f'{type(e).__name__}: {e}'
  timings[k]={'wall_ns':time.perf_counter_ns()-w,'cpu_ns':time.thread_time_ns()-c}
 ts=[threading.Thread(target=call,args=(k,),name=f'mem-{k}') for k in ('A','B')]
 for t in ts:t.start()
 barrier.wait()
 for t in ts:t.join(180)
 joined=all(not t.is_alive() for t in ts);sample('post_two_request_schedule')
 inbounds=[m for m in adapter.s.nodes('Message') if adapter.s.node(m)['attrs'].get('from')=='interlocutor' and adapter.s.node(m)['attrs'].get('text')=='describe what you see']
 goals=[]
 for m in inbounds:
  gs=[g for g in adapter.s.nodes('Goal') if m in adapter.inner.neighbours(g,'comprehends')]
  goals.append({'count':len(gs),'statuses':[adapter.s.node(g)['attrs'].get('lifecycle_status') for g in gs]})
 after=inputs();checks={'source_stable':after==locked,'threads_joined':joined,'no_errors':not errors,'two_requests':len(inbounds)==2 and set(replies)=={'A','B'},'expected_replies':all(x==EXPECTED for x in replies.values()),'resolved_goals':len(goals)==2 and all(g['count']==1 and g['statuses']==['resolved'] for g in goals),'rss_finite_nondecreasing':all(isinstance(x['memory'].get('VmRSS'),int) for x in phases) and all(a['memory']['resource_peak_rss_bytes']<=b['memory']['resource_peak_rss_bytes'] for a,b in zip(phases,phases[1:]))}
 report={'schema_version':1,'run_id':'describe-scene-boot-memory-profile-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'checks':checks,'all_checks_pass':all(checks.values()),'boot_wall_ns':boot_ns,'thread_timings':timings,'replies':replies,'thread_errors':errors,'request_goals':goals,'phases':phases,'environment':{'python':sys.version,'platform':platform.platform()},'claim_boundary':'RSS phase changes locate footprint growth in time, not ownership by Python/native component.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'phases':[{ 'phase':x['phase'],'rss_gib':round(x['memory']['VmRSS']/2**30,3),'peak_gib':round(x['memory']['resource_peak_rss_bytes']/2**30,3),'anonymous_gib':round(x['memory'].get('Anonymous',0)/2**30,3),'pss_anon_gib':round(x['memory'].get('Pss_Anon',0)/2**30,3),'private_dirty_gib':round(x['memory'].get('Private_Dirty',0)/2**30,3)} for x in phases]},indent=2))
 if not all(checks.values()):raise SystemExit('memory profile gate failed')
if __name__=='__main__':main()
