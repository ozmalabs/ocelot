#!/usr/bin/env python3
"""Same-process trace on/off isolation for live describe-scene requests."""
from __future__ import annotations
import hashlib, importlib.util, json, platform, sys, threading, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_ACCESS_TRACE_ISOLATION_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/describe_scene_access_trace_isolation_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_access_trace_isolation_v1_20260927.json'
TRACE_RUNNER=ROOT/'scripts/substrate_live_describe_scene_access_trace_v2_3.py'
BASELINE='I see the grey thing stays, the yellow counter, and the blue thing moves.'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    spec=importlib.util.spec_from_file_location('trace_v23_lock',TRACE_RUNNER); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'trace_runtime_inputs':mod.lock_inputs()}
def nid(n): return int(n.value if hasattr(n,'value') else n)

class TraceLock:
    def __init__(self,inner,adapter,enabled): self.inner=inner;self.adapter=adapter;self.enabled=enabled;self.depth={};self.rows=[];self.dropped=0
    def __enter__(self):
        self.inner.acquire(); name=threading.current_thread().name; depth=self.depth.get(name,0)
        if depth==0 and self.enabled:
            self.adapter.inner.runtime_access_trace_reset();self.adapter.inner.runtime_access_trace_set_enabled(True)
        self.depth[name]=depth+1;return self
    def __exit__(self,*exc):
        name=threading.current_thread().name;depth=self.depth[name]-1
        try:
            if depth==0:
                del self.depth[name]
                if self.enabled:
                    self.adapter.inner.runtime_access_trace_set_enabled(False);rows,dropped=self.adapter.inner.runtime_access_trace_snapshot()
                    self.rows.extend(rows);self.dropped+=int(dropped)
            else:self.depth[name]=depth
        finally:self.inner.release()
        return False

def run_arm(enabled):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene
    a=WorldAdapter(seeds=());a.inner.runtime_access_trace_set_enabled(False);a.inner.runtime_access_trace_reset();t0=time.perf_counter_ns();load_all_seeds(a);boot_ns=time.perf_counter_ns()-t0
    attach_scene(a,[{'kind':'static','colour':'grey'},{'kind':'meter','colour':'yellow'},{'kind':'mover','colour':'blue','responds_to_my_action':False}])
    proxy=TraceLock(a._conversation_lock,a,enabled);a._conversation_lock=proxy
    barrier=threading.Barrier(3);replies={};errors={};durations={}
    def call(label):
        barrier.wait();t=time.perf_counter_ns()
        try:replies[label]=str(a.converse('describe what you see',speech_act='instruction',speaker='alice'))
        except BaseException as exc:errors[label]=f'{type(exc).__name__}: {exc}'
        durations[label]=time.perf_counter_ns()-t
    ts=[threading.Thread(target=call,args=(x,),name=f'{"trace" if enabled else "plain"}-{x}') for x in ('A','B')]
    for t in ts:t.start()
    barrier.wait()
    for t in ts:t.join(120)
    joined=all(not t.is_alive() for t in ts)
    inbound=[m for m in a.s.nodes('Message') if a.s.node(m)['attrs'].get('from')=='interlocutor' and a.s.node(m)['attrs'].get('text')=='describe what you see']
    inbound.sort(key=nid);requests=[]
    for m in inbound:
        ma=dict(a.s.node(m)['attrs']);goals=[g for g in a.s.nodes('Goal') if m in a.inner.neighbours(g,'comprehends')]
        events=[]
        st=ma.get('discourse_state_id')
        if st is not None:
            state_events=list(a.inner.neighbours(st,'has_event'));state_events.sort(key=lambda e:int(a.s.node(e)['attrs'].get('event_index',-1)))
            for e in state_events:
                ea=a.s.node(e)['attrs']
                if any(g in a.inner.neighbours(e,'for_goal') for g in goals):events.append(ea.get('kind'))
        requests.append({'goal_count':len(goals),'statuses':[a.s.node(g)['attrs'].get('lifecycle_status') for g in goals],'events':events})
    if enabled:a.inner.runtime_access_trace_set_enabled(False)
    trace_count=sum(int(row[-1]) for row in proxy.rows)
    return {'trace_enabled':enabled,'boot_ns':boot_ns,'joined':joined,'errors':errors,'replies':replies,'requests':requests,'request_count':len(inbound),'durations_ns':durations,'trace_event_count':trace_count,'trace_dropped':proxy.dropped}

def main():
    if sys.argv[1:]==['--lock']:
        print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale source lock')
    before=inputs();arms=[run_arm(False),run_arm(True)];after=inputs()
    checks={'source_stable':before==after==locked,'both_workers_joined':all(x['joined'] for x in arms),'both_arms_two_requests':all(x['request_count']==2 and len(x['requests'])==2 for x in arms),'expected_replies':all(set(x['replies'])=={'A','B'} and all(v==BASELINE for v in x['replies'].values()) for x in arms),'resolved_request_goals':all(all(r['goal_count']==1 and r['statuses']==['resolved'] and r['events']==['selection','execution','action_result'] for r in x['requests']) for x in arms),'trace_off_empty':arms[0]['trace_event_count']==0 and arms[0]['trace_dropped']==0,'trace_on_complete':arms[1]['trace_event_count']>0 and arms[1]['trace_dropped']==0}
    report={'schema_version':1,'run_id':'describe-scene-access-trace-isolation-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'classification':'pass' if all(checks.values()) else 'inconclusive_or_censored','checks':checks,'all_checks_pass':all(checks.values()),'arms':arms,'environment':{'python':sys.version,'platform':platform.platform()}}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'trace_events':arms[1]['trace_event_count']},indent=2))
    if not all(checks.values()):raise SystemExit('trace isolation gate failed')
if __name__=='__main__':main()
