#!/usr/bin/env python3
"""Cold-process measurement of scene-description prompt formulations."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_FACULTY_PROMPT_FAMILY_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_faculty_prompt_family_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_faculty_prompt_family_v1_20260927.json'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
SCENE=[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}]
PROMPTS={'canonical':('describe what you see','describe_scene'),'tell_see':('tell me what you see','describe_scene'),'describe_scene':('describe the scene','describe_scene'),'report_observe':('report what you observe','describe_scene'),'self_identity_control':('tell me about yourself','self_report')}
SCHEDULE=[('canonical',0),('report_observe',0),('self_identity_control',0),('tell_see',0),('describe_scene',0),('describe_scene',1),('tell_see',1),('self_identity_control',1),('report_observe',1),('canonical',1)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 s=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'runtime_inputs':m.inputs()}
def rss():
 d={}
 for line in Path('/proc/self/status').read_text().splitlines():
  if line.startswith(('VmRSS:','VmHWM:')):d[line.split(':',1)[0]]=int(line.split()[1])*1024
 d['resource_peak_rss_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024);return d
def nid(n):return int(n.value if hasattr(n,'value') else n)
def worker(condition,rep):
 before=inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 import domains.conversation_action as ca
 a=WorldAdapter(seeds=());t=time.perf_counter_ns();c=time.process_time_ns();boot=load_all_seeds(a);boot_wall=time.perf_counter_ns()-t;boot_cpu=time.process_time_ns()-c
 ca.attach_scene(a,SCENE);prompt,expected_route=PROMPTS[condition];ensure=[];actions=[];scene_calls=[];inner=a.inner
 old_ensure=ca._ensure_describe;old_scene=ca._act_describe_scene;old_action=ca.act_on_instruction
 def ensure_wrap(agent):
  n=int(inner.rule_count());z=old_ensure(agent);ensure.append({'rules_before':n,'rules_after':int(inner.rule_count()),'new_rules':int(inner.rule_count())-n});return z
 def scene_wrap(agent,comp,inbound):
  scene_calls.append(prompt);return old_scene(agent,comp,inbound)
 def action_wrap(agent,comp,inbound=None):
  result=old_action(agent,comp,inbound);actions.append({'route':result.get('route'),'goal_kind':result.get('goal_kind')});return result
 ca._ensure_describe=ensure_wrap;ca._act_describe_scene=scene_wrap;ca.act_on_instruction=action_wrap
 count_before=int(inner.rule_count());t=time.perf_counter_ns();c=time.process_time_ns();error=None
 try:reply=str(a.converse(prompt,speech_act='instruction',speaker='alice'))
 except BaseException as exc:reply='';error=f'{type(exc).__name__}: {exc}'
 request_wall=time.perf_counter_ns()-t;request_cpu=time.process_time_ns()-c;count_after=int(inner.rule_count())
 ca._ensure_describe=old_ensure;ca._act_describe_scene=old_scene;ca.act_on_instruction=old_action
 inbound=[m for m in a.s.nodes('Message') if a.s.node(m)['attrs'].get('from')=='interlocutor' and a.s.node(m)['attrs'].get('text')==prompt]
 goals=[]
 for msg in inbound:
  for g in a.s.nodes('Goal'):
   if msg not in inner.neighbours(g,'comprehends'):continue
   ga=a.s.node(g)['attrs'];state=a.s.node(msg)['attrs'].get('discourse_state_id');events=[]
   if state is not None:
    for e in inner.neighbours(state,'has_event'):
     if g in inner.neighbours(e,'for_goal'):events.append(a.s.node(e)['attrs'].get('kind'))
   goals.append({'kind':ga.get('kind'),'status':ga.get('lifecycle_status'),'events':events})
 after=inputs()
 return {'condition':condition,'replicate':rep,'pid':os.getpid(),'prompt':prompt,'expected_route':expected_route,'locked_inputs':before,'post_run_inputs':after,'source_stable':before==after,'boot_loaded':boot.get('loaded'),'boot_failures':len(boot.get('failed',[])),'boot_wall_ns':boot_wall,'boot_process_cpu_ns':boot_cpu,'request_wall_ns':request_wall,'request_process_cpu_ns':request_cpu,'request_rule_delta':count_after-count_before,'ensure_calls':ensure,'scene_route_calls':scene_calls,'action_observations':actions,'reply':reply,'error':error,'goals':goals,'current_rss':rss(),'peak_rss_bytes':rss()['resource_peak_rss_bytes'],'environment':{'python':sys.version,'platform':platform.platform()}}
def worker_ok(r,locked):
 expected='describe_scene' if r['condition']!='self_identity_control' else 'self_report';gkind=expected
 route_hits=[x for x in r['action_observations'] if x['route']==expected]
 base=r['source_stable'] and r['locked_inputs']==locked==r['post_run_inputs'] and r['boot_loaded']>0 and r['error'] is None and r['expected_route']==expected and len(r['goals'])==1 and r['goals'][0]['kind']==gkind and r['goals'][0]['status']=='resolved' and r['goals'][0]['events']==['selection','execution','action_result'] and len(route_hits)==1
 if expected=='describe_scene':return base and len(r['scene_route_calls'])==1 and len(r['ensure_calls'])==1 and r['ensure_calls'][0]['new_rules']==18 and r['request_rule_delta']==24 and all(c in r['reply'].lower() for c in ('grey','yellow','blue'))
 return base and len(r['scene_route_calls'])==0 and len(r['ensure_calls'])==0 and r['request_rule_delta']==0 and not any(x['route']=='describe_scene' for x in r['action_observations'])
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  r=worker(os.environ['OCEL0_PROMPT_CONDITION'],int(os.environ['OCEL0_PROMPT_REP']));print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale prompt-family lock')
 runs=[]
 for condition,rep in SCHEDULE:
  env=os.environ.copy();env.update(OCEL0_PROMPT_CONDITION=condition,OCEL0_PROMPT_REP=str(rep))
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True)
  if p.stdout.strip():runs.append(json.loads(p.stdout))
  else:runs.append({'condition':condition,'replicate':rep,'worker_error':p.stderr,'returncode':p.returncode})
  print(f'completed={condition}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 post=inputs();checks={'ten_workers':len(runs)==10,'unique_processes':len({r['pid'] for r in runs})==10,'two_replicates_per_condition':all(sum(r['condition']==k for r in runs)==2 for k in PROMPTS),'parent_lock_stable':post==locked,'all_workers_pass':len(runs)==10 and all(worker_ok(r,locked) for r in runs)}
 report={'schema_version':1,'run_id':'describe-faculty-prompt-family-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'schedule':SCHEDULE,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'claim_boundary':'Five source-stratified prompts, two cold processes each; not natural traffic prevalence or faculty necessity.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('prompt-family gates failed')
if __name__=='__main__':main()
