#!/usr/bin/env python3
"""Source-locked first-use versus prebuilt describe-faculty measurement."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, resource, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_FACULTY_FIRST_USE_REUSE_V1_1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_faculty_first_use_reuse_v1_1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_faculty_first_use_reuse_v1_1_20260927.json'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
EXPECTED='I see the grey thing stays, the yellow counter, and the blue thing moves.'
PERCEPTS=[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}]

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def runtime_inputs():
    spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.inputs()
def inputs(): return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'runtime_inputs':runtime_inputs()}
def rss():
    values={}
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith(('VmRSS:','VmHWM:')): values[line.split(':',1)[0]]=int(line.split()[1])*1024
    values['resource_peak_rss_bytes']=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    return values
def nid(node): return int(node.value if hasattr(node,'value') else node)

def worker(arm,rep):
    before=inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene, _ensure_describe
    adapter=WorldAdapter(seeds=()); phases=[]
    def sample(name): phases.append({'phase':name,'memory':rss(),'rule_count':int(adapter.inner.rule_count())})
    sample('before_boot')
    t=time.perf_counter_ns(); c=time.process_time_ns(); boot=load_all_seeds(adapter); boot_wall=time.perf_counter_ns()-t; boot_cpu=time.process_time_ns()-c; sample('after_boot')
    attach_scene(adapter,PERCEPTS); sample('after_scene')
    faculty_setup=None
    if arm=='prebuilt':
        t=time.perf_counter_ns(); c=time.process_time_ns(); result=_ensure_describe(adapter)
        faculty_setup={'wall_ns':time.perf_counter_ns()-t,'process_cpu_ns':time.process_time_ns()-c,'available':result is not None,'rule_count_after':int(adapter.inner.rule_count())}
        sample('after_prebuild')
    requests=[]; replies=[]
    for idx in range(2):
        count_before=int(adapter.inner.rule_count()); t=time.perf_counter_ns(); c=time.process_time_ns()
        try: reply=str(adapter.converse('describe what you see',speech_act='instruction',speaker='alice')); error=None
        except BaseException as exc: reply=''; error=f'{type(exc).__name__}: {exc}'
        wall=time.perf_counter_ns()-t; cpu=time.process_time_ns()-c; count_after=int(adapter.inner.rule_count())
        replies.append(reply); requests.append({'index':idx+1,'wall_ns':wall,'process_cpu_ns':cpu,'rule_count_before':count_before,'rule_count_after':count_after,'new_rules':count_after-count_before,'error':error}); sample(f'after_request_{idx+1}')
    inbound=[m for m in adapter.s.nodes('Message') if adapter.s.node(m)['attrs'].get('from')=='interlocutor' and adapter.s.node(m)['attrs'].get('text')=='describe what you see']; inbound.sort(key=nid)
    lifecycle=[]
    for msg in inbound:
        goals=[g for g in adapter.s.nodes('Goal') if msg in adapter.inner.neighbours(g,'comprehends')]; events=[]
        for goal in goals:
            attrs=adapter.s.node(goal)['attrs']; state=adapter.s.node(msg)['attrs'].get('discourse_state_id'); kinds=[]
            if state is not None:
                for event in adapter.inner.neighbours(state,'has_event'):
                    ea=adapter.s.node(event)['attrs']
                    if goal in adapter.inner.neighbours(event,'for_goal'): kinds.append(ea.get('kind'))
            lifecycle.append({'goal_count':len(goals),'status':attrs.get('lifecycle_status'),'events':kinds})
    after=inputs()
    return {'arm':arm,'replicate':rep,'pid':os.getpid(),'locked_inputs':before,'post_run_inputs':after,'source_stable':before==after,
      'boot_loaded':boot.get('loaded'),'boot_failed':len(boot.get('failed',[])),'boot_wall_ns':boot_wall,'boot_process_cpu_ns':boot_cpu,
      'faculty_setup':faculty_setup,'requests':requests,'replies':replies,'lifecycle':lifecycle,'phases':phases,
      'peak_rss_bytes':rss().get('resource_peak_rss_bytes'),'environment':{'python':sys.version,'platform':platform.platform()}}

def main():
    if sys.argv[1:]==['--lock']:
        print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True)); return
    if sys.argv[1:]==['--worker']:
        arm=os.environ['OCEL0_FACULTY_ARM']; rep=int(os.environ['OCEL0_FACULTY_REP']); print(json.dumps(worker(arm,rep),sort_keys=True)); return
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing/stale first-use/reuse lock')
    schedule=[('lazy',0),('prebuilt',0),('prebuilt',1),('lazy',1),('lazy',2),('prebuilt',2)]; runs=[]
    for arm,rep in schedule:
        env=os.environ.copy(); env.update(OCEL0_FACULTY_ARM=arm,OCEL0_FACULTY_REP=str(rep))
        proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        runs.append(json.loads(proc.stdout)); print(f'completed arm={arm} replicate={rep} pid={runs[-1]["pid"]}',file=sys.stderr,flush=True)
    post=inputs()
    def ok(r):
        setup_delta=((r['faculty_setup'] or {}).get('rule_count_after',0)-r['phases'][2]['rule_count']) if r['arm']=='prebuilt' else 0
        request_rules=[x['new_rules'] for x in r['requests']]
        rule_schedule=(request_rules==[24,0]) if r['arm']=='lazy' else (setup_delta==18 and request_rules==[6,0])
        return r['source_stable'] and r['locked_inputs']==locked==r['post_run_inputs'] and r['boot_loaded']>0 and len(r['requests'])==2 and r['replies']==[EXPECTED,EXPECTED] and len(r['lifecycle'])==2 and all(x['goal_count']==1 and x['status']=='resolved' and x['events']==['selection','execution','action_result'] for x in r['lifecycle']) and all(x['error'] is None for x in r['requests']) and rule_schedule and ((r['faculty_setup'] or {}).get('available') if r['arm']=='prebuilt' else True)
    checks={'six_unique_processes':len(runs)==6 and len({r['pid'] for r in runs})==6,'three_per_arm':sum(r['arm']=='lazy' for r in runs)==3 and sum(r['arm']=='prebuilt' for r in runs)==3,'parent_source_stable':post==locked,'all_workers_pass':all(ok(r) for r in runs)}
    report={'schema_version':1,'run_id':'describe-faculty-first-use-reuse-v1.1-20260927','locked_inputs':locked,'post_run_inputs':post,'checks':checks,'all_checks_pass':all(checks.values()),'schedule':schedule,'runs':runs,'claim_boundary':'Route-specific cost timing and reuse on the locked scene fixture; not causal rule necessity, natural task frequency, transfer, or scaling.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
    if not all(checks.values()): raise SystemExit('first-use/reuse gates failed')
if __name__=='__main__': main()
