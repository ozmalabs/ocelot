#!/usr/bin/env python3
"""Five fresh-process uninstrumented wall/CPU/RSS measurements."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, resource, subprocess, sys, threading, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_UNINSTRUMENTED_TIMED_REPLICATION_V2_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_scene_uninstrumented_timing_v2_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_uninstrumented_timing_v2_20260927.json'
PLAIN=ROOT/'scripts/substrate_describe_scene_plain_concurrency_diagnostic_v1.py'
EXPECTED='I see the grey thing stays, the yellow counter, and the blue thing moves.'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    spec=importlib.util.spec_from_file_location('plain_concurrency_v1',PLAIN);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'runtime_inputs':mod.input_lock()}
def nid(n): return int(n.value if hasattr(n,'value') else n)
def peak_rss_bytes():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value*(1024 if sys.platform!='darwin' else 1))

def worker(rep):
    before=inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene
    process_cpu0=time.process_time_ns();wall0=time.perf_counter_ns()
    adapter=WorldAdapter(seeds=());load_all_seeds(adapter);boot_wall=time.perf_counter_ns()-wall0;boot_cpu=time.process_time_ns()-process_cpu0
    attach_scene(adapter,[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}])
    rss_after_boot=peak_rss_bytes();barrier=threading.Barrier(3);replies={};errors={};timings={}
    def call(label):
        barrier.wait();w=time.perf_counter_ns();c=time.thread_time_ns()
        try:replies[label]=str(adapter.converse('describe what you see',speech_act='instruction',speaker='alice'))
        except BaseException as exc:errors[label]={'type':type(exc).__name__,'message':str(exc)}
        timings[label]={'wall_ns':time.perf_counter_ns()-w,'thread_cpu_ns':time.thread_time_ns()-c}
    ts=[threading.Thread(target=call,args=(x,),name=f'v2-{rep}-{x}') for x in ('A','B')]
    for t in ts:t.start()
    barrier.wait()
    for t in ts:t.join(180)
    joined=all(not t.is_alive() for t in ts)
    inbounds=[m for m in adapter.s.nodes('Message') if adapter.s.node(m)['attrs'].get('from')=='interlocutor' and adapter.s.node(m)['attrs'].get('text')=='describe what you see']
    inbounds.sort(key=nid);requests=[]
    for m in inbounds:
        attrs=adapter.s.node(m)['attrs'];goals=[g for g in adapter.s.nodes('Goal') if m in adapter.inner.neighbours(g,'comprehends')]
        events=[]
        st=attrs.get('discourse_state_id')
        if st is not None:
            es=list(adapter.inner.neighbours(st,'has_event'));es.sort(key=lambda e:int(adapter.s.node(e)['attrs'].get('event_index',-1)))
            for e in es:
                ea=adapter.s.node(e)['attrs']
                if any(g in adapter.inner.neighbours(e,'for_goal') for g in goals):events.append(ea.get('kind'))
        requests.append({'goal_count':len(goals),'statuses':[adapter.s.node(g)['attrs'].get('lifecycle_status') for g in goals],'events':events,'public_reply':attrs.get('turn_reply_surface')})
    after=inputs()
    return {'replicate':rep,'pid':os.getpid(),'locked_inputs':before,'post_run_inputs':after,'source_stable':before==after,'threads_joined':joined,'thread_errors':errors,'request_count':len(inbounds),'replies':replies,'requests':requests,'boot_wall_ns':boot_wall,'boot_process_cpu_ns':boot_cpu,'thread_timings':timings,'rss_after_boot_bytes':rss_after_boot,'peak_rss_bytes':peak_rss_bytes(),'environment':{'python':sys.version,'platform':platform.platform()}}

def main():
    if sys.argv[1:]==['--lock']:
        print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
    if sys.argv[1:]==['--worker']:
        rep=int(os.environ['OCEL0_TIMING_REPLICATE']);print(json.dumps(worker(rep),sort_keys=True));return
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale v2 timing source lock')
    runs=[]
    for rep in range(5):
        env=os.environ.copy();env['OCEL0_TIMING_REPLICATE']=str(rep)
        proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        runs.append(json.loads(proc.stdout));print(f'completed replicate={rep} pid={runs[-1]["pid"]}',file=sys.stderr,flush=True)
    post=inputs()
    checks={'five_unique_processes':len(runs)==5 and len({r['pid'] for r in runs})==5,'parent_source_stable':post==locked,'all_worker_locks_match':all(r['locked_inputs']==locked==r['post_run_inputs'] and r['source_stable'] for r in runs),'all_threads_joined_no_errors':all(r['threads_joined'] and not r['thread_errors'] for r in runs),'two_requests_each':all(r['request_count']==2 and set(r['replies'])=={'A','B'} for r in runs),'expected_public_replies':all(all(v==EXPECTED for v in r['replies'].values()) for r in runs),'resolved_goals_and_exact_lifecycle':all(all(q['goal_count']==1 and q['statuses']==['resolved'] and q['events']==['selection','execution','action_result'] and q['public_reply']==EXPECTED for q in r['requests']) for r in runs)}
    report={'schema_version':1,'run_id':'describe-scene-uninstrumented-timing-v2-20260927','locked_inputs':locked,'post_run_inputs':post,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'timing_boundary':'Five fresh processes, two concurrent calls per process; no trace/audit/readback. Caller wall/CPU durations include any wait due to the shared-adapter schedule; not isolated single-call latency.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
    if not all(checks.values()):raise SystemExit('v2 timing replicate gates failed')
if __name__=='__main__':main()
