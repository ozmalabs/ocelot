#!/usr/bin/env python3
"""Compare native post-rule tracing with default visual adapter ticks."""
from __future__ import annotations
import hashlib, json, platform, resource, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from domains.complex_cells import grating
from scripts.rung8_lib import H,W
import numpy as np

STEM='vision_native_rule_phase_trace_v1_20260929'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_NATIVE_RULE_PHASE_TRACE_V1_PREREG_20260929.md'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json'
RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
ANALYZER=ROOT/'scripts/analyze_substrate_vision_native_rule_phase_trace_v1.py'
CHECKPOINT_DIR=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'
SEEDS=(20260935,20260936,20260937)
SCOPES=('global','root_scoped')
ATTRS=('act','act_next','theta','rate','act_step','rate_step')
MAX_EVENTS=10_000
MAX_STEPS=200_000

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def exact_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def node_num(node): return int(node.value if hasattr(node,'value') else node)
def peak_rss_bytes():
    v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(v*(1024 if sys.platform.startswith('linux') else 1))

def source_inputs():
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    base_inputs=base.source_inputs()
    # The shared builder's source closure includes every nearby runner. Remove
    # this runner's own entry to avoid hashing a value that contains itself.
    base_inputs.get('source_closure_sha256',{}).pop(
        f'scripts/{Path(__file__).name}',None)
    files=('runners/dsl/src/substrate.rs','runners/dsl/src/py.rs',
           'runners/dsl/python/substrate_rs/__init__.py',
           'runners/dsl/python/substrate_rs/_native.build.json',
           'domains/wave_world.py','domains/engine_provenance.py')
    checkpoints={str(s):CHECKPOINT_DIR/f'seed_{s}.json' for s in SEEDS}
    return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),
        'analyzer_sha256':sha(ANALYZER),'base_builder_sha256':sha(Path(base.__file__)),
        'base_source_inputs':base_inputs,
        'source_sha256':{p:sha(ROOT/p) for p in files},
        'checkpoints':{k:sha(v) for k,v in checkpoints.items()},
        'checkpoint_lock_sha256':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json'),
        'native_extension_sha256':sha(Path(_native.__file__).resolve()),
        'engine_provenance':engine_provenance(),'python':sys.version,
        'platform':platform.platform(),'max_events':MAX_EVENTS,'max_steps':MAX_STEPS,
        'seeds':list(SEEDS),'scopes':list(SCOPES),'watched_attrs':list(ATTRS)}

def build(seed,scope):
    cp=json.loads((CHECKPOINT_DIR/f'seed_{seed}.json').read_text())
    graph=cp['graph']; expected=cp['prepared_graph_sha256']
    if base.graph_digest(graph)!=expected: raise RuntimeError(f'seed {seed}: source checkpoint graph digest mismatch')
    s,(wa,wb),(ua,ub),top,_=base.build_pair(seed,scope=='root_scoped')
    inner=s._inner
    rules=inner.export_rules()
    expected_rule='st_settle_root_scoped_benchmark' if scope=='root_scoped' else 'st_settle'
    selected=[r for r in rules if r.get('name') in ('st_settle','st_settle_root_scoped_benchmark')]
    if len(selected)!=1 or selected[0].get('name')!=expected_rule: raise RuntimeError('incorrect scope rule loaded')
    inner.graph_from_dict(graph)
    if base.graph_digest(inner.graph_to_dict())!=expected: raise RuntimeError('restored checkpoint digest mismatch')
    if [set(inner.neighbours(w.retina,'has_sunit')) for w in (wa,wb)] != [set(ua),set(ub)]:
        raise RuntimeError('restored Retina ownership mismatch')
    return s,inner,wa,wb,ua,ub,expected

def state(s,units):
    return {key:[float(s.node(u)['attrs'].get(key,0.0)) for u in units] for key in ATTRS}

def inputs():
    frame=grating((H,W),0.0,0.0,4.0).astype(np.float32)
    blank=np.zeros((H,W),dtype=np.float32)
    return frame,blank

def run_arm(seed,scope,traced):
    s,inner,wa,wb,ua,ub,checkpoint_hash=build(seed,scope)
    frame,blank=inputs(); trace_reports=[]
    if traced:
        watch_rules=['oo_sunit_rate','st_settle' if scope=='global' else 'st_settle_root_scoped_benchmark']
        node_ids=[node_num(u) for u in (*ua,*ub)]
        def traced_tick(max_steps=100_000,detect_cycles=False):
            report=s.tick_with_rule_state_trace(watch_rules,node_ids,list(ATTRS),MAX_EVENTS,max_steps,detect_cycles)
            trace_reports.append(report)
            return int(report['steps'])
        s.tick=traced_tick
    t0=time.perf_counter_ns();c0=time.process_time_ns()
    after=[]
    for world,units,image,label in ((wa,ua,frame,'target'),(wb,ub,blank,'sibling_blank')):
        call_wall0=time.perf_counter_ns();call_cpu0=time.process_time_ns()
        step=int(world.step(frame=image))
        after.append({'label':label,'step_return':step,'root_step':float(s.node(world.retina)['attrs'].get('step',0.0)),
            'state_A':state(s,ua),'state_B':state(s,ub),
            'graph_sha256':exact_digest(inner.graph_to_dict()),
            'call_wall_ns':time.perf_counter_ns()-call_wall0,
            'call_process_cpu_ns':time.process_time_ns()-call_cpu0})
    return {'seed':seed,'scope':scope,'arm':'traced' if traced else 'default',
        'checkpoint_sha256':checkpoint_hash,'steps':after,
        'trace_reports':trace_reports,'trace_event_count':sum(len(r['events']) for r in trace_reports),
        'trace_dropped_events':sum(int(r['dropped_events']) for r in trace_reports),
        'worker_wall_ns':time.perf_counter_ns()-t0,'worker_process_cpu_ns':time.process_time_ns()-c0,
        'peak_rss_bytes':peak_rss_bytes(),'graph_node_count':len(inner.graph_to_dict().get('nodes',[])),
        'graph_edge_count':len(inner.graph_to_dict().get('edges',[])),
        'source_stable':source_inputs()==LOCKED_INPUTS}

def main():
    global LOCKED_INPUTS
    if sys.argv[1:]==['--lock']:
        LOCK.parent.mkdir(parents=True,exist_ok=True)
        LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return
    LOCKED_INPUTS=source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=LOCKED_INPUTS:
        raise SystemExit('missing or stale source lock')
    if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
    workers=[]
    for seed in SEEDS:
        for scope in SCOPES:
            default=run_arm(seed,scope,False)
            traced=run_arm(seed,scope,True)
            workers.append({'seed':seed,'scope':scope,'default':default,'traced':traced})
            RAW.parent.mkdir(parents=True,exist_ok=True)
            RAW.write_text(json.dumps({'run_id':STEM,'locked_inputs':LOCKED_INPUTS,
                'expected_workers':len(SEEDS)*len(SCOPES),'workers':workers,
                'source_stable':source_inputs()==LOCKED_INPUTS},indent=2,sort_keys=True)+'\n')
            print(f"seed={seed} scope={scope} trace_events={traced['trace_event_count']} dropped={traced['trace_dropped_events']} parity={[a['graph_sha256']==b['graph_sha256'] for a,b in zip(default['steps'],traced['steps'])]}",flush=True)
    if source_inputs()!=LOCKED_INPUTS:raise SystemExit('source drift during capture')

if __name__=='__main__':
    LOCKED_INPUTS={}
    main()
