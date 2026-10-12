#!/usr/bin/env python3
"""Measure phase-0 location and feature-geometry learning under interleaving."""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import domains.seed_registry
from domains.engine_provenance import assert_measuring_engine
from domains.eye_world import PreVisualWorld,set_params,rf_centre,rf_spread
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core,load_seeds_into
from substrate_rs import _native
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_SPATIAL_FEATURE_TRANSFER_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_spatial_feature_transfer_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/vision_eye_phase0_spatial_feature_transfer_v1_20261004.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');SEED_IDS=(6,7,8);SITES=((5,5),(12,12));ARMS=('solid5_control','mixed_geometry');ETA=0.005;STEPS=8000;CAP=200_000;N_UNITS=4;H=W=16
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}
def patterns(arm):
    solid={(dy,dx) for dy in range(-2,3) for dx in range(-2,3)}
    if arm=='solid5_control': shapes=(solid,solid)
    else: shapes=({(dy,dx) for dy in range(-1,2) for dx in range(-1,2)}, {(0,0),(-1,0),(1,0),(0,-1),(0,1)})
    return [{(cy+dy)*W+(cx+dx) for dy,dx in shape} for (cy,cx),shape in zip(SITES,shapes)]
def fields(s,eye):
    out=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf)
        out.append({'unit':i,'center':[float(cy),float(cx)],'spread':float(rf_spread(rf)),'weights':[float(v) for v in rf.reshape(-1)]})
    return out
def run_case(seed,arm):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye']);wp=s.nodes('WaveParams')[0]
    for k,v in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,k,v)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed);set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=ETA)
    cells={r*W+c:n for (r,c),n in wave.cells.items()};patches=patterns(arm);start=seed%2;current=set();exposure=[0,0];switches=0;writes=0;input_ns=0;closure_ns=0;progress=0;checkpoints=[]
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for step in range(1,STEPS+1):
        site=(start+(step-1))%2;target=patches[site];exposure[site]+=1
        if current and current!=target:switches+=1
        t=time.perf_counter_ns()
        for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
        for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
        input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step))
        t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
        if step in (4000,8000):checkpoints.append({'step':step,'exposures_per_site':exposure.copy(),'active_count':len(current),'argmax_entries':s._inner.rule_scheduler_checkpoint()['eval_cache']['entry_counts'][3],'fields':fields(s,eye)})
    return {'seed':seed,'arm':arm,'start_site':start,'eta':ETA,'steps':STEPS,'pattern_sizes':[len(p) for p in patches],'exposures_per_site':exposure,'switches':switches,'input_writes':writes,'input_update_ns':input_ns,'closure_ns':closure_ns,'closure_mean_ns':closure_ns//STEPS,'progress':progress,'checkpoints':checkpoints}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior spatial-feature artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeSpatialFeatureTransferV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale spatial-feature source lock')
    rows=[run_case(seed,arm) for arm in ARMS for seed in SEED_IDS];post=inputs()
    checks={'source_stable':locked==post,'six_workers':len(rows)==6,'three_seeds_each_arm':all(sum(r['arm']==a for r in rows)==3 for a in ARMS),'full_horizon':all(r['steps']==STEPS and [c['step'] for c in r['checkpoints']]==[4000,8000] for r in rows),'equal_exposures':all(r['exposures_per_site']==[4000,4000] for r in rows),'schedule_exact':all(r['switches']==7999 for r in rows),'active_counts_match_protocol':all(r['pattern_sizes']==([25,25] if r['arm']=='solid5_control' else [9,5]) for r in rows),'input_write_counts_exact':all(r['input_writes']==25+7999*50 if r['arm']=='solid5_control' else r['input_writes']==(9 if r['start_site']==0 else 5)+7999*14 for r in rows),'runtime_gates':all(r['progress']>0 and all(c['active_count']==(25 if r['arm']=='solid5_control' else r['pattern_sizes'][1-r['start_site']]) and c['argmax_entries']>0 for c in r['checkpoints']) for r in rows)}
    report={'schema':'VisionEyeSpatialFeatureTransferV1','locked_inputs':locked,'post_run_inputs':post,'sites':[list(x) for x in SITES],'seeds':list(SEED_IDS),'eta':ETA,'arms':list(ARMS),'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'six runs comparing a solid-patch control with mixed square/cross geometry at two fixed sites in one authored visual learner; no semantic class transfer, natural-image benchmark, or general learning claim.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
