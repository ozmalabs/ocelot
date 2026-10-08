#!/usr/bin/env python3
"""Train retinotopy on two shapes, freeze, then test an unseen shape at both sites."""
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
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_HELDOUT_SHAPE_RESPONSE_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_heldout_shape_response_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/vision_eye_phase0_heldout_shape_response_v1_20261005.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');SEED_IDS=(6,7,8);SITES=((5,5),(12,12));ETA=0.005;TRAIN_STEPS=8000;REPEATS=5;CAP=200_000;N_UNITS=4;H=W=16
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}
def masks():
    return {'train_square3':{(dy,dx) for dy in range(-1,2) for dx in range(-1,2)},'train_plus5':{(0,0),(-1,0),(1,0),(0,-1),(0,1)},'heldout_x5':{(0,0),(-1,-1),(-1,1),(1,-1),(1,1)}}
def absolute_mask(name,site):
    y,x=site;return {(y+dy)*W+(x+dx) for dy,dx in masks()[name]}
def capture_fields(s,eye):
    out=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf)
        out.append({'unit':i,'center':[float(cy),float(cx)],'spread':float(rf_spread(rf)),'weights':[float(v) for v in rf.reshape(-1)]})
    return out
def run_case(seed):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye']);wp=s.nodes('WaveParams')[0]
    for k,v in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,k,v)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed);set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=ETA,frozen=0.0)
    cells={r*W+c:n for (r,c),n in wave.cells.items()};train_names=('train_square3','train_plus5');train=[absolute_mask(name,site) for name,site in zip(train_names,SITES)];current=set();exposure=[0,0];writes=0;input_ns=0;closure_ns=0;progress=0
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    start=seed%2
    for step in range(1,TRAIN_STEPS+1):
        site=(start+step-1)%2;target=train[site];exposure[site]+=1;t=time.perf_counter_ns()
        for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
        for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
        input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
    learned=capture_fields(s,eye);train_writes=writes;s.set_attr(eye.eye,'frozen',1.0);probes=[];probe_ns=0;probe_input_ns=0
    schedule=(('seen_square3',0),('seen_plus5',1),('heldout_x5',0),('heldout_x5',1))
    for rep in range(REPEATS):
        for name,site in schedule:
            target=absolute_mask(name,SITES[site]);step=TRAIN_STEPS+len(probes)+1;t=time.perf_counter_ns()
            for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
            for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
            probe_input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));probe_ns+=time.perf_counter_ns()-t
            probes.append({'step':step,'rep':rep,'pattern':name,'site_index':site,'site':list(SITES[site]),'mask':[int(i) for i in sorted(target)],'active_count':len(target),'acts':[float(s.node(u)['attrs']['act']) for u in eye.units],'winners':[int(i) for i,u in enumerate(eye.units) if int(s.node(u)['attrs']['win_step'])==step and float(s.node(u)['attrs']['winner'])==1.0]})
    final=capture_fields(s,eye)
    return {'seed':seed,'start_site':start,'eta':ETA,'train_steps':TRAIN_STEPS,'train_exposures_per_site':exposure,'train_input_writes':train_writes,'probe_input_writes':writes-train_writes,'train_input_update_ns':input_ns,'train_closure_ns':closure_ns,'frozen_probe_closure_ns':probe_ns,'frozen_probe_input_ns':probe_input_ns,'progress':progress,'learned_fields':learned,'post_probe_fields':final,'probes':probes}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite held-out-shape artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeHeldoutShapeResponseV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale held-out-shape source lock')
    rows=[run_case(seed) for seed in SEED_IDS];post=inputs()
    expected_names={'seen_square3','seen_plus5','heldout_x5'}
    checks={'source_stable':locked==post,'three_seeds':len(rows)==3,'complete_training':all(r['train_steps']==8000 and r['train_exposures_per_site']==[4000,4000] for r in rows),'all_probe_cells':all(len(r['probes'])==20 and {p['pattern'] for p in r['probes']}==expected_names for r in rows),'probe_replicates':all(all(sum(p['pattern']==name for p in r['probes'])==10 for name in expected_names) for r in rows),'active_counts':all(all(p['active_count']==(9 if p['pattern']=='seen_square3' else 5) for p in r['probes']) for r in rows),'one_current_winner':all(len(p['winners'])==1 for r in rows for p in r['probes']),'frozen_weights_exact':all(r['learned_fields']==r['post_probe_fields'] for r in rows),'positive_progress':all(r['progress']>0 for r in rows)}
    report={'schema':'VisionEyeHeldoutShapeResponseV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEED_IDS),'sites':[list(x) for x in SITES],'eta':ETA,'training_steps':TRAIN_STEPS,'test_repeats_per_pattern':REPEATS,'frozen_during_probes':True},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'three trained small spatial maps, tested on seen square/plus and unseen X geometries at trained sites; probe uses fixed binary patterns and native WUnit activity/winner rules, not natural images or semantic shape recognition.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
