#!/usr/bin/env python3
"""Compare blocked and step-interleaved acquisition of two visual locations."""
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
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_INTERLEAVED_RETENTION_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_interleaved_retention_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/vision_eye_phase0_interleaved_retention_v1_20261004.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');SITES=((5,5),(12,12));SEED_IDS=(0,1,2);MODES=('blocked','interleaved');N_UNITS=4;STEPS=8000;ACTIVE=25;H=W=16;CAP=200_000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}
def fields(s,eye):
    out=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf)
        out.append({'unit':i,'winner':float(s.node(u)['attrs']['winner']),'center':[float(cy),float(cx)],'spread':float(rf_spread(rf)),'weights':[float(v) for v in rf.reshape(-1)]})
    return out
def run_case(seed,mode):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye']);wp=s.nodes('WaveParams')[0]
    for k,v in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,k,v)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed);set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=5e-4)
    cells={r*W+c:n for (r,c),n in wave.cells.items()};patches=[{r*W+c for r in range(cy-2,cy+3) for c in range(cx-2,cx+3)} for cy,cx in SITES]
    current=set();exposure=[0,0];write_count=0;input_ns=0;closure_ns=0;progress=0;checkpoints=[]
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for step in range(1,STEPS+1):
        site_idx=0 if (mode=='blocked' and step<=4000) or (mode=='interleaved' and step%2==1) else 1
        target=patches[site_idx];exposure[site_idx]+=1
        t=time.perf_counter_ns()
        for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);write_count+=1
        for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);write_count+=1
        input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step))
        t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
        if step in (4000,8000):checkpoints.append({'step':step,'exposures_per_site':exposure.copy(),'active_count':len(current),'fields':fields(s,eye),'argmax_entries':s._inner.rule_scheduler_checkpoint()['eval_cache']['entry_counts'][3]})
    return {'seed':seed,'mode':mode,'steps':STEPS,'exposures_per_site':exposure,'input_writes':write_count,'input_update_ns':input_ns,'closure_ns':closure_ns,'closure_mean_ns':closure_ns//STEPS,'progress':progress,'graph_nodes':len(s.graph_to_dict()['nodes']),'graph_edges':len(s.graph_to_dict()['edges']),'checkpoints':checkpoints}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior interleaved-retention artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeInterleavedRetentionV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale interleaved-retention source lock')
    rows=[run_case(seed,mode) for seed in SEED_IDS for mode in MODES];post=inputs()
    checks={'source_stable':locked==post,'six_cases':len(rows)==6,'both_modes_each_seed':all({r['mode'] for r in rows if r['seed']==seed}==set(MODES) for seed in SEED_IDS),'full_horizon':all(r['steps']==STEPS and [x['step'] for x in r['checkpoints']]==[4000,8000] for r in rows),'exposure_schedule_exact':all(r['exposures_per_site']==[4000,4000] and all(c['exposures_per_site']==([2000,2000] if r['mode']=='interleaved' and c['step']==4000 else [4000,4000] if c['step']==8000 else [4000,0]) for c in r['checkpoints']) for r in rows),'activity_and_progress':all(all(c['active_count']==ACTIVE and c['argmax_entries']>0 for c in r['checkpoints']) and r['progress']>0 for r in rows)}
    report={'schema':'VisionEyeInterleavedRetentionV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEED_IDS),'sites':[list(x) for x in SITES],'modes':list(MODES),'units':N_UNITS,'steps':STEPS,'active_cells':ACTIVE},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'six authored two-location learning cases on one 16x16 vision-eye family; compares blocked and one-step interleaved exposure, not larger codebook capacity, natural images, feature-class transfer, or general self-improvement'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'cases':len(rows),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
