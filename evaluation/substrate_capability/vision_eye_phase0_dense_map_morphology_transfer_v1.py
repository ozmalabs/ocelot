#!/usr/bin/env python3
"""Paired square/cross feature transfer on a nine-site retinotopy grid."""
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
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_vision_eye_phase0_dense_map_morphology_transfer_v1.py';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_dense_map_morphology_transfer_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/vision_eye_phase0_dense_map_morphology_transfer_v1_20261005.json';PRIOR_LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_dense_map_interpolation_v1_lock_20261005.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');SEED_IDS=(30,31,32,33,34,35);MORPHOLOGIES=('square','cross');TRAIN_SITES=tuple((y,x) for y in (3,8,13) for x in (3,8,13));HELDOUT_SITES=tuple((y,x) for y in (5,6,10,11) for x in (5,6,10,11));ALL_SITES=TRAIN_SITES+HELDOUT_SITES
ETA=0.005;EXPOSURE=4000;REPEATS=3;CAP=200_000;N_UNITS=9;H=W=16
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'prior_dense_map_lock_sha256':sha(PRIOR_LOCK),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}
def mask(site,morph):
    y,x=site;offsets=((0,0),(0,-1),(0,1),(-1,0),(1,0)) if morph=='cross' else tuple((dy,dx) for dy in (-1,0,1) for dx in (-1,0,1))
    return {(y+dy)*W+x+dx for dy,dx in offsets}
def fields(s,eye):
    out=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf);out.append({'unit':i,'center':[float(cy),float(cx)],'spread':float(rf_spread(rf)),'weights':[float(v) for v in rf.reshape(-1)]})
    return out
def run_case(seed,morph):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye']);wp=s.nodes('WaveParams')[0]
    for k,v in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,k,v)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed);set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=ETA,frozen=0.0)
    cells={r*W+c:n for (r,c),n in wave.cells.items()};train_masks=[mask(x,morph) for x in TRAIN_SITES];current=set();exposure=[0]*len(TRAIN_SITES);switches=0;writes=0;input_ns=0;closure_ns=0;progress=0;start=seed%len(TRAIN_SITES);order=[(start+i)%len(TRAIN_SITES) for i in range(len(TRAIN_SITES))];steps=len(TRAIN_SITES)*EXPOSURE
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for step in range(1,steps+1):
        site=order[(step-1)//EXPOSURE];target=train_masks[site];exposure[site]+=1
        if current and current!=target:switches+=1
        t=time.perf_counter_ns()
        for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
        for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
        input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
    learned=fields(s,eye);train_writes=writes;set_params(eye,frozen=1.0);freeze=float(s.node(s.nodes('EyeParams')[0])['attrs']['frozen']);probes=[];probe_ns=0;probe_input_ns=0
    for rep in range(REPEATS):
        for site_index,site in enumerate(ALL_SITES):
            target=mask(site,morph);step=steps+len(probes)+1;t=time.perf_counter_ns()
            for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
            for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
            probe_input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));probe_ns+=time.perf_counter_ns()-t
            probes.append({'step':step,'rep':rep,'site_index':site_index,'location_status':'trained' if site_index<9 else 'heldout','site':list(site),'mask':sorted(target),'active_count':len(target),'acts':[float(s.node(u)['attrs']['act']) for u in eye.units],'winners':[i for i,u in enumerate(eye.units) if int(s.node(u)['attrs']['win_step'])==step and float(s.node(u)['attrs']['winner'])==1.0]})
    return {'seed':seed,'morphology':morph,'start_site':start,'site_order':order,'eta':ETA,'steps':steps,'exposures_per_site':exposure,'switches':switches,'train_input_writes':train_writes,'probe_input_writes':writes-train_writes,'train_input_update_ns':input_ns,'train_closure_ns':closure_ns,'probe_input_ns':probe_input_ns,'probe_closure_ns':probe_ns,'progress':progress,'freeze_value':freeze,'sites':[list(x) for x in TRAIN_SITES],'heldout_sites':[list(x) for x in HELDOUT_SITES],'learned_fields':learned,'post_probe_fields':fields(s,eye),'probes':probes}
def expected_writes(morph):
    return len(mask(TRAIN_SITES[0],morph))+sum(len(mask(TRAIN_SITES[i],morph))+len(mask(TRAIN_SITES[i+1],morph)) for i in range(8))
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite morphology-transfer artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeDenseMapMorphologyTransferV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale morphology-transfer source lock')
    rows=[run_case(seed,morph) for morph in MORPHOLOGIES for seed in SEED_IDS];post=inputs()
    checks={'source_stable':locked==post,'twelve_workers':len(rows)==12,'six_paired_seeds':all(sum(r['seed']==s and r['morphology']==m for r in rows)==1 for s in SEED_IDS for m in MORPHOLOGIES),'site_grid_exact':all(r['sites']==[list(x) for x in TRAIN_SITES] and r['heldout_sites']==[list(x) for x in HELDOUT_SITES] for r in rows),'units_exact':all(len(r['learned_fields'])==9 for r in rows),'exposures_exact':all(r['exposures_per_site']==[EXPOSURE]*9 for r in rows),'steps_exact':all(r['steps']==36000 for r in rows),'switches_exact':all(r['switches']==8 for r in rows),'writes_exact':all(r['train_input_writes']==expected_writes(r['morphology']) for r in rows),'probe_matrix_exact':all(len(r['probes'])==25*REPEATS and all(sum(p['site_index']==i for p in r['probes'])==REPEATS for i in range(25)) for r in rows),'active_counts_exact':all(all(p['active_count']==(5 if r['morphology']=='cross' else 9) for p in r['probes']) for r in rows),'unique_winners':all(len(p['winners'])==1 for r in rows for p in r['probes']),'frozen_parity':all(r['freeze_value']==1.0 and r['learned_fields']==r['post_probe_fields'] for r in rows),'runtime_progress':all(r['progress']>0 for r in rows)}
    report={'schema':'VisionEyeDenseMapMorphologyTransferV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEED_IDS),'morphologies':list(MORPHOLOGIES),'train_sites':[list(x) for x in TRAIN_SITES],'heldout_sites':[list(x) for x in HELDOUT_SITES],'eta':ETA,'exposures_per_site':EXPOSURE,'units':N_UNITS,'repeats_per_site':REPEATS},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'paired square and five-cell-cross retinotopy maps from six fresh seeds in one authored phase-0 learner; not shape recognition or natural-vision evidence.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
