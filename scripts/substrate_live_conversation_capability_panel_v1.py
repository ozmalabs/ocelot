#!/usr/bin/env python3
"""Source-locked cold-process panel across distinct conversation task routes."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_CONVERSATION_CAPABILITY_PANEL_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/live_conversation_capability_panel_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/live_conversation_capability_panel_v1_20260927.json'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
SCENE=[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}]
TASKS={'scene_description':('describe what you see','statement'),'held_self_knowledge_answer':('How are you organised?','question'),'self_report_action':('report your organisation','statement'),'unknown_word_clarification':('quorplezap the door','statement'),'concern_authoring':('Compare where the two letters differ and judge the trial on that region.','statement')}
SCHEDULE=[('scene_description',0),('unknown_word_clarification',0),('held_self_knowledge_answer',0),('concern_authoring',0),('self_report_action',0),('self_report_action',1),('concern_authoring',1),('held_self_knowledge_answer',1),('unknown_word_clarification',1),('scene_description',1)]
EXPECTED_SCENE='I see the grey thing stays, the yellow counter, and the blue thing moves.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
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
 if condition=='scene_description':ca.attach_scene(a,SCENE)
 teacher_calls={'count':0}
 try:a.set_self_teacher(lambda q:(teacher_calls.__setitem__('count',teacher_calls['count']+1),'teacher')[1])
 except Exception:pass
 old_action=ca.act_on_instruction;old_ensure=ca._ensure_describe;actions=[];ensure=[]
 def action_wrap(agent,comp,inbound=None):
  out=old_action(agent,comp,inbound);actions.append({k:out.get(k) for k in ('route','goal_kind','reply','concern')});return out
 def ensure_wrap(agent):
  n=int(agent.inner.rule_count());out=old_ensure(agent);ensure.append({'rule_delta':int(agent.inner.rule_count())-n,'available':out is not None});return out
 ca.act_on_instruction=action_wrap;ca._ensure_describe=ensure_wrap
 text,speech_act=TASKS[condition];rules_before=int(a.inner.rule_count());t=time.perf_counter_ns();c=time.process_time_ns();error=None
 try:reply=str(a.converse(text,speech_act=speech_act,speaker='alice'))
 except BaseException as exc:reply='';error=f'{type(exc).__name__}: {exc}'
 call_wall=time.perf_counter_ns()-t;call_cpu=time.process_time_ns()-c;rules_after=int(a.inner.rule_count())
 ca.act_on_instruction=old_action;ca._ensure_describe=old_ensure
 inbound=[m for m in a.s.nodes('Message') if a.s.node(m)['attrs'].get('from')=='interlocutor' and a.s.node(m)['attrs'].get('text')==text];inbound.sort(key=nid)
 turn=[]
 for msg in inbound:
  ma=a.s.node(msg)['attrs'];iid=ma.get('communication_interpretation_id');interp=dict(a.s.node(iid)['attrs']) if iid is not None and a.s.has_node(iid) else {};goals=[];outbound=[]
  for g in a.s.nodes('Goal'):
   if msg not in a.inner.neighbours(g,'comprehends'):continue
   ga=a.s.node(g)['attrs'];state=ma.get('discourse_state_id');events=[]
   if state is not None:
    for e in a.inner.neighbours(state,'has_event'):
     if g in a.inner.neighbours(e,'for_goal'):events.append(a.s.node(e)['attrs'].get('kind'))
   goals.append({'kind':ga.get('kind'),'status':ga.get('lifecycle_status'),'events':events})
  for m in a.s.nodes('Message'):
   aa=a.s.node(m)['attrs']
   if aa.get('from') in ('agent','adapter') and msg in a.inner.neighbours(m,'responds_to'):
    acts=[a.s.node(x)['attrs'].get('name') for x in a.inner.neighbours(m,'has_speech_act')]
    outbound.append({'text':aa.get('text'),'trouble_source':aa.get('trouble_source'),'expects_response':aa.get('expects_response'),'speech_acts':acts})
  turn.append({'goal_count':len(goals),'goals':goals,'interpretation':{k:interp.get(k) for k in ('kind','dispatch_path','cognitive_disposition','arbitration_basis')},'communication_route':ma.get('communication_route'),'outbound_messages':outbound})
 post=inputs()
 return {'condition':condition,'replicate':rep,'pid':os.getpid(),'prompt':text,'speech_act':speech_act,'locked_inputs':before,'post_run_inputs':post,'source_stable':before==post,'boot_loaded':boot.get('loaded'),'boot_failures':len(boot.get('failed',[])),'boot_wall_ns':boot_wall,'boot_process_cpu_ns':boot_cpu,'task_wall_ns':call_wall,'task_process_cpu_ns':call_cpu,'rule_count_delta':rules_after-rules_before,'faculty_build_calls':ensure,'action_results':actions,'reply':reply,'error':error,'teacher_calls':teacher_calls['count'],'turns':turn,'peak_rss_bytes':rss()['resource_peak_rss_bytes'],'final_rss':rss(),'environment':{'python':sys.version,'platform':platform.platform()}}
def task_ok(r,locked):
 if not(r.get('source_stable') and r.get('locked_inputs')==locked==r.get('post_run_inputs') and r.get('boot_loaded',0)>0 and r.get('error') is None and len(r.get('turns',[]))==1):return False
 t=r['turns'][0];actions=r['action_results'];route=[x.get('route') for x in actions]
 if r['condition']=='scene_description':return r['reply']==EXPECTED_SCENE and any(x.get('kind')=='describe_scene' and x.get('status')=='resolved' and x.get('events')==['selection','execution','action_result'] for x in t['goals']) and len(r['faculty_build_calls'])==1 and r['faculty_build_calls'][0]['rule_delta']==18
 if r['condition']=='held_self_knowledge_answer':return 'organis' in r['reply'].lower() and not r['reply'].rstrip().endswith('?')
 if r['condition']=='self_report_action':return any(x.get('route')=='self_report' for x in route) and any(x.get('kind')=='report_self' and x.get('status')=='resolved' and x.get('events')==['selection','execution','action_result'] for x in t['goals']) and bool(r['reply'].strip())
 if r['condition']=='unknown_word_clarification':return 'quorplezap' in r['reply'].lower() and r['reply'].rstrip().endswith('?') and any('quorplezap' in str(m.get('trouble_source','')).lower() and m.get('expects_response') is True and 'clarification' in m.get('speech_acts',[]) for m in t['outbound_messages'])
 if r['condition']=='concern_authoring':return any(x.get('route')=='concern_authored' and x.get('concern') is not None for x in actions) and bool(r['reply'].strip()) and 'no attached world/faculty' not in r['reply'].lower() and r['teacher_calls']==0
 return False
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  r=worker(os.environ['OCEL0_TASK_CONDITION'],int(os.environ['OCEL0_TASK_REP']));print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale live capability panel lock')
 runs=[]
 for cond,rep in SCHEDULE:
  env=os.environ.copy();env.update(OCEL0_TASK_CONDITION=cond,OCEL0_TASK_REP=str(rep));p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True)
  if p.stdout.strip():runs.append(json.loads(p.stdout))
  else:runs.append({'condition':cond,'replicate':rep,'worker_error':p.stderr,'returncode':p.returncode})
  print(f'completed={cond}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 post=inputs();checks={'ten_workers':len(runs)==10,'ten_unique_processes':len({r.get('pid') for r in runs})==10,'two_per_condition':all(sum(r.get('condition')==k for r in runs)==2 for k in TASKS),'parent_source_lock_stable':post==locked,'all_workers_pass_task_contract':len(runs)==10 and all(task_ok(r,locked) for r in runs)}
 report={'schema_version':1,'run_id':'live-conversation-capability-panel-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'schedule':SCHEDULE,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'claim_boundary':'Five repository-contract live tasks, two cold full-seed processes each. Selected capabilities only; no natural-prevalence, general-accuracy, ablation, or scaling claim.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('live capability panel gates failed')
if __name__=='__main__':main()
