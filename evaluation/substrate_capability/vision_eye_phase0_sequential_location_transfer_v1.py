#!/usr/bin/env python3
"""Test sequential acquisition and retention of two visual locations."""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import domains.seed_registry
from domains.engine_provenance import assert_measuring_engine
from domains.eye_world import PreVisualWorld,set_params,rf_centre,rf_spread
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core,load_seeds_into
from substrate_rs import _native

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_SEQUENTIAL_TRANSFER_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_sequential_location_transfer_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/vision_eye_phase0_sequential_location_transfer_v1_20261004.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json')
SITES=((5,5),(12,12));SEEDS_RUN=(0,1,2);N_UNITS=4;STEPS_PER_STAGE=4000;ACTIVE=25;H=W=16;CAP=200_000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{name:sha(ROOT/'seeds'/name) for name in SEEDS},'sources':{name:sha(ROOT/name) for name in SOURCES}}
def measure(eye,s):
    fields=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf)
        fields.append({'unit':i,'winner':float(s.node(u)['attrs']['winner']),'spread':float(rf_spread(rf)),'center':[float(cy),float(cx)],'weights':[float(v) for v in rf.reshape(-1)]})
    return fields
def run_worker(seed,order):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye'])
    wp=s.nodes('WaveParams')[0]
    for key,value in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,key,value)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed)
    set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=5e-4)
    cell_by_index={r*W+c:node for (r,c),node in wave.cells.items()}
    locs=[SITES[0],SITES[1]] if order=='A_then_B' else [SITES[1],SITES[0]]
    current=set();rows=[];total_writes=0
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for stage,site in enumerate(locs,1):
        target={r*W+c for r in range(site[0]-2,site[0]+3) for c in range(site[1]-2,site[1]+3)}
        t=time.perf_counter_ns();writes=0
        for idx in current-target:s.set_attr(cell_by_index[idx],'bursting',0.0);writes+=1
        for idx in target-current:s.set_attr(cell_by_index[idx],'bursting',1.0);writes+=1
        input_ns=time.perf_counter_ns()-t;total_writes+=writes;current=target
        closure_ns=0;progress=0
        for local in range(1,STEPS_PER_STAGE+1):
            global_step=(stage-1)*STEPS_PER_STAGE+local;s.set_attr(eye.eye,'step',float(global_step))
            t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
        rows.append({'stage':stage,'trained_center':list(site),'steps':STEPS_PER_STAGE,'active_count':len(current),'input_writes_at_boundary':writes,'input_update_ns':input_ns,'closure_ns':closure_ns,'closure_mean_ns':closure_ns//STEPS_PER_STAGE,'progress':progress,'argmax_entries':s._inner.rule_scheduler_checkpoint()['eval_cache']['entry_counts'][3],'fields':measure(eye,s)})
    return {'seed':seed,'order':order,'training_order':[list(x) for x in locs],'total_input_writes':total_writes,'graph_nodes':len(s.graph_to_dict()['nodes']),'graph_edges':len(s.graph_to_dict()['edges']),'stages':rows}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior sequential-transfer artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyePhase0SequentialTransferV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale sequential-transfer lock')
    rows=[]
    for seed in SEEDS_RUN:
        for order in ('A_then_B','B_then_A'):rows.append(run_worker(seed,order))
    post=inputs();checks={'source_stable':locked==post,'six_workers':len(rows)==6,'both_orders_present':{r['order'] for r in rows}=={'A_then_B','B_then_A'},'two_full_stages':all(len(r['stages'])==2 and all(x['steps']==STEPS_PER_STAGE for x in r['stages']) for r in rows),'activity_fixed':all(x['active_count']==ACTIVE for r in rows for x in r['stages']),'all_progress':all(x['progress']>0 for r in rows for x in r['stages']),'argmax_cache_present':all(x['argmax_entries']>0 for r in rows for x in r['stages'])}
    report={'schema':'VisionEyePhase0SequentialTransferV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEEDS_RUN),'centers':[list(x) for x in SITES],'orders':['A_then_B','B_then_A'],'units':N_UNITS,'steps_per_stage':STEPS_PER_STAGE,'active_cells':ACTIVE},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'six authored sequential-location workers in one 16x16 vision-eye family; tests retention within two fixed patterns, not natural-task prevalence, open-ended visual recognition, cross-domain transfer, or general self-improvement'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'workers':len(rows),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
