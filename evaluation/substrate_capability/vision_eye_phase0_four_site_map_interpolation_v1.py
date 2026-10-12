#!/usr/bin/env python3
"""Measure four-site retinotopy and frozen responses at interpolating locations."""
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
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_FOUR_SITE_MAP_INTERPOLATION_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_four_site_map_interpolation_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/vision_eye_phase0_four_site_map_interpolation_v1_20261005.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');SEED_IDS=(12,13,14);TRAIN_SITES=((3,3),(3,12),(12,3),(12,12));HELDOUT_SITES=((3,6),(3,9),(6,3),(9,3),(6,12),(9,12),(12,6),(12,9),(6,6),(6,9),(9,6),(9,9));ALL_SITES=TRAIN_SITES+HELDOUT_SITES
ETA=0.005;TRAIN_STEPS=16000;EXPOSURES_PER_SITE=4000;REPEATS=5;CAP=200_000;N_UNITS=4;H=W=16
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}
def mask(site):
    y,x=site;return {(y+dy)*W+(x+dx) for dy in range(-1,2) for dx in range(-1,2)}
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
    cells={r*W+c:n for (r,c),n in wave.cells.items()};train_masks=[mask(x) for x in TRAIN_SITES];current=set();exposures=[0]*len(TRAIN_SITES);switches=0;writes=0;input_ns=0;closure_ns=0;progress=0;start=seed%len(TRAIN_SITES)
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for step in range(1,TRAIN_STEPS+1):
        site=(start+step-1)%len(TRAIN_SITES);target=train_masks[site];exposures[site]+=1
        if current and current!=target:switches+=1
        t=time.perf_counter_ns()
        for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
        for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
        input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
    learned=capture_fields(s,eye);train_writes=writes;set_params(eye,frozen=1.0);freeze_value=float(s.node(s.nodes('EyeParams')[0])['attrs']['frozen']);probes=[];probe_ns=0;probe_input_ns=0
    for rep in range(REPEATS):
        for site_index,site in enumerate(ALL_SITES):
            target=mask(site);step=TRAIN_STEPS+len(probes)+1;t=time.perf_counter_ns()
            for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
            for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
            probe_input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));probe_ns+=time.perf_counter_ns()-t
            probes.append({'step':step,'rep':rep,'site_index':site_index,'location_status':'trained' if site_index<4 else 'heldout','site':list(site),'mask':[int(i) for i in sorted(target)],'active_count':len(target),'acts':[float(s.node(u)['attrs']['act']) for u in eye.units],'winners':[int(i) for i,u in enumerate(eye.units) if int(s.node(u)['attrs']['win_step'])==step and float(s.node(u)['attrs']['winner'])==1.0]})
    final=capture_fields(s,eye)
    return {'seed':seed,'start_site':start,'eta':ETA,'train_steps':TRAIN_STEPS,'train_exposures_per_site':exposures,'train_switches':switches,'train_input_writes':train_writes,'probe_input_writes':writes-train_writes,'train_input_update_ns':input_ns,'train_closure_ns':closure_ns,'frozen_probe_closure_ns':probe_ns,'frozen_probe_input_ns':probe_input_ns,'progress':progress,'frozen_param_value':freeze_value,'learned_fields':learned,'post_probe_fields':final,'probes':probes}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite four-site interpolation artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeFourSiteMapInterpolationV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale four-site source lock')
    rows=[run_case(seed) for seed in SEED_IDS];post=inputs()
    checks={'source_stable':locked==post,'three_seeds':len(rows)==3,'four_site_exposures_exact':all(r['train_exposures_per_site']==[4000]*4 for r in rows),'training_switches_exact':all(r['train_switches']==TRAIN_STEPS-1 for r in rows),'training_writes_exact':all(r['train_input_writes']==9+((TRAIN_STEPS-1)*18) for r in rows),'probe_matrix_exact':all(len(r['probes'])==80 and {p['site_index'] for p in r['probes']}==set(range(16)) for r in rows),'five_repeats_each_site':all(all(sum(p['site_index']==i for p in r['probes'])==REPEATS for i in range(16)) for r in rows),'probe_activity':all(p['active_count']==9 for r in rows for p in r['probes']),'unique_winners':all(len(p['winners'])==1 for r in rows for p in r['probes']),'freeze_and_weight_parity':all(r['frozen_param_value']==1.0 and r['learned_fields']==r['post_probe_fields'] for r in rows),'positive_progress':all(r['progress']>0 for r in rows)}
    report={'schema':'VisionEyeFourSiteMapInterpolationV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEED_IDS),'train_sites':[list(x) for x in TRAIN_SITES],'heldout_sites':[list(x) for x in HELDOUT_SITES],'eta':ETA,'training_steps':TRAIN_STEPS,'exposures_per_training_site':EXPOSURES_PER_SITE,'units':N_UNITS,'probe_repeats_per_site':REPEATS},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'three four-site authored binary spatial maps, tested at four trained and twelve held-out positions with the same square mask; probes are frozen. Measures this retinotopy envelope, not natural vision or general spatial reasoning.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
