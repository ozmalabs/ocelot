#!/usr/bin/env python3
"""Trace visual act/rate phases on a locked natural-image transform pair."""
from __future__ import annotations
import hashlib,json,platform,resource,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import numpy as np
from PIL import Image
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
from scripts.rung8_lib import H,W

STEM='natural_image_act_rate_phase_diagnostic_v1_20260929'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_NATURAL_IMAGE_ACT_RATE_PHASE_DIAGNOSTIC_V1_PREREG_20260929.md'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json';RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
ANALYZER=ROOT/'scripts/analyze_substrate_natural_image_act_rate_phase_diagnostic_v1.py'
CHECKPOINT_DIR=ROOT/'evaluation/reports/vision_multiseed_checkpoints_v2_0'
IMAGE=ROOT/'data/vision_curriculum/BSDS300/images/test/101085.jpg'
SEEDS=(20260935,20260936,20260937);SCOPES=('global','root_scoped')
ATTRS=('act','theta','rate','act_step','rate_step','aff')
RULE_RATE='oo_sunit_rate';RULES_SETTLE={'global':'st_settle','root_scoped':'st_settle_root_scoped_benchmark'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def node_num(v):return int(v.value if hasattr(v,'value') else v)
def source_inputs():
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    b=base.source_inputs();b.get('source_closure_sha256',{}).pop(f'scripts/{Path(base.__file__).name}',None);b.get('source_closure_sha256',{}).pop(f'scripts/{Path(__file__).name}',None)
    return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),
        'base_builder_sha256':sha(Path(base.__file__)),'base_source_inputs':b,
        'trace_source_sha256':{p:sha(ROOT/p) for p in ('runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py','domains/wave_world.py')},
        'checkpoint_file_sha256':{str(s):sha(CHECKPOINT_DIR/f'seed_{s}.json') for s in SEEDS},
        'prepared_checkpoint_graph_sha256':{str(s):json.loads((CHECKPOINT_DIR/f'seed_{s}.json').read_text())['prepared_graph_sha256'] for s in SEEDS},
        'checkpoint_lock_sha256':sha(ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_0_lock_20260927.json'),
        'image_sha256':sha(IMAGE),'native_extension_sha256':sha(Path(_native.__file__).resolve()),
        'engine_provenance':engine_provenance(),'python':sys.version,'platform':platform.platform(),
        'seeds':list(SEEDS),'scopes':list(SCOPES),'image':IMAGE.name,'attrs':list(ATTRS),'max_events':10000}
def frame():return np.asarray(Image.open(IMAGE).convert('L').resize((W,H),Image.Resampling.BILINEAR),np.float32)/255.0
def restore(seed,scope):
    cp=json.loads((CHECKPOINT_DIR/f'seed_{seed}.json').read_text());expected=cp['prepared_graph_sha256']
    if base.graph_digest(cp['graph'])!=expected:raise RuntimeError('checkpoint digest mismatch')
    s,(wa,wb),(ua,ub),_,_=base.build_pair(seed,scope=='root_scoped');inner=s._inner
    inner.graph_from_dict(cp['graph'])
    if base.graph_digest(inner.graph_to_dict())!=expected:raise RuntimeError('restored graph digest mismatch')
    node_ids=[node_num(u) for u in (*ua,*ub)]
    return s,inner,wa,wb,ua,ub,node_ids,expected
def capture_arm(seed,scope,image,label,traced):
    s,inner,wa,wb,ua,ub,node_ids,cp_graph=restore(seed,scope);reports=[]
    if traced:
        def traced_tick(max_steps=100000,detect_cycles=False):
            report=s.tick_with_rule_state_trace([RULE_RATE,RULES_SETTLE[scope]],node_ids,list(ATTRS),10000,max_steps,detect_cycles)
            reports.append(report);return int(report['steps'])
        s.tick=traced_tick
    t0=time.perf_counter_ns();c0=time.process_time_ns();step=int(wa.step(frame=image))
    state={key:[float(s.node(u)['attrs'].get(key,0.0)) for u in ua] for key in ATTRS}
    graph=inner.graph_to_dict()
    return {'label':label,'traced':traced,'checkpoint_graph_sha256':cp_graph,
        'input_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'step_return':step,
        'final_graph_sha256':base.graph_digest(graph),'final_target_state':state,'trace_reports':reports,
        'trace_event_count':sum(len(r['events']) for r in reports),
        'trace_dropped_events':sum(int(r['dropped_events']) for r in reports),
        'wall_ns':time.perf_counter_ns()-t0,'process_cpu_ns':time.process_time_ns()-c0,
        'peak_rss_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform.startswith('linux') else 1))}
def main():
    global LOCKED
    if sys.argv[1:]==['--lock']:
        LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':source_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
    LOCKED=source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=LOCKED:raise SystemExit('missing or stale source lock')
    if RAW.exists():raise SystemExit(f'refusing to overwrite {RAW}')
    img=frame();rot=np.rot90(img,2).copy();blank=np.zeros((H,W),np.float32);records=[]
    for seed in SEEDS:
      for scope in SCOPES:
        inputs=[]
        for label,pixels in (('original',img),('rotated_180',rot),('blank',blank)):
            default=capture_arm(seed,scope,pixels,label,False);traced=capture_arm(seed,scope,pixels,label,True)
            inputs.append({'label':label,'default':default,'traced':traced})
        records.append({'seed':seed,'scope':scope,'image':IMAGE.name,'image_file_sha256':sha(IMAGE),'inputs':inputs})
        RAW.parent.mkdir(parents=True,exist_ok=True)
        RAW.write_text(json.dumps({'run_id':STEM,'locked_inputs':LOCKED,'expected_workers':6,
            'workers':records,'source_stable':source_inputs()==LOCKED},indent=2,sort_keys=True)+'\n')
        print(f'worker={len(records)}/6 seed={seed} scope={scope} traced_events={sum(i["traced"]["trace_event_count"] for i in inputs)}',flush=True)
    if source_inputs()!=LOCKED:raise SystemExit('source drift during capture')
if __name__=='__main__':LOCKED={};main()
