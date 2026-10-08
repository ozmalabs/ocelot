#!/usr/bin/env python3
"""Paired site-count × presentation-schedule retinotopy capacity evaluation."""
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
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_SITE_COUNT_SCHEDULE_FACTORIAL_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_site_count_schedule_factorial_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/vision_eye_phase0_site_count_schedule_factorial_v1_20261005.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json');SEED_IDS=(15,16,17);SITE_SETS={2:((5,5),(12,12)),4:((3,3),(3,12),(12,3),(12,12))};HELDOUT={2:((5,12),(12,5)),4:((3,6),(3,9),(6,3),(9,3),(6,12),(9,12),(12,6),(12,9),(6,6),(6,9),(9,6),(9,9))};SCHEDULES=('interleaved','blocked');ETA=0.005;EXPOSURE=4000;REPEATS=3;CAP=200_000;N_UNITS=4;H=W=16
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{n:sha(ROOT/'seeds'/n) for n in SEEDS},'sources':{n:sha(ROOT/n) for n in SOURCES}}
def mask(site):
    y,x=site;return {(y+dy)*W+(x+dx) for dy in range(-1,2) for dx in range(-1,2)}
def fields(s,eye):
    out=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf);out.append({'unit':i,'center':[float(cy),float(cx)],'spread':float(rf_spread(rf)),'weights':[float(v) for v in rf.reshape(-1)]})
    return out
def run_case(seed,n_sites,schedule):
    sites=SITE_SETS[n_sites];held=HELDOUT[n_sites];s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye']);wp=s.nodes('WaveParams')[0]
    for k,v in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,k,v)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed);set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=ETA,frozen=0.0)
    cells={r*W+c:n for (r,c),n in wave.cells.items()};all_sites=sites+held;site_masks=[mask(x) for x in sites];current=set();exposure=[0]*n_sites;switches=0;writes=0;input_ns=0;closure_ns=0;progress=0;start=seed%n_sites;order=[(start+i)%n_sites for i in range(n_sites)];steps=n_sites*EXPOSURE
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for step in range(1,steps+1):
        if schedule=='interleaved':site=order[(step-1)%n_sites]
        else:site=order[min((step-1)//EXPOSURE,n_sites-1)]
        target=site_masks[site];exposure[site]+=1
        if current and current!=target:switches+=1
        t=time.perf_counter_ns()
        for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
        for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
        input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
    learned=fields(s,eye);train_writes=writes;set_params(eye,frozen=1.0);freeze=float(s.node(s.nodes('EyeParams')[0])['attrs']['frozen']);probes=[];probe_ns=0;probe_input_ns=0
    for rep in range(REPEATS):
        for site_index,site in enumerate(all_sites):
            target=mask(site);step=steps+len(probes)+1;t=time.perf_counter_ns()
            for idx in current-target:s.set_attr(cells[idx],'bursting',0.0);writes+=1
            for idx in target-current:s.set_attr(cells[idx],'bursting',1.0);writes+=1
            probe_input_ns+=time.perf_counter_ns()-t;current=target;s.set_attr(eye.eye,'step',float(step));t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));probe_ns+=time.perf_counter_ns()-t
            probes.append({'step':step,'rep':rep,'site_index':site_index,'location_status':'trained' if site_index<n_sites else 'heldout','site':list(site),'mask':sorted(target),'active_count':len(target),'acts':[float(s.node(u)['attrs']['act']) for u in eye.units],'winners':[i for i,u in enumerate(eye.units) if int(s.node(u)['attrs']['win_step'])==step and float(s.node(u)['attrs']['winner'])==1.0]})
    return {'seed':seed,'site_count':n_sites,'schedule':schedule,'eta':ETA,'start_site':start,'site_order':order,'steps':steps,'exposures_per_site':exposure,'switches':switches,'train_input_writes':train_writes,'probe_input_writes':writes-train_writes,'train_input_update_ns':input_ns,'train_closure_ns':closure_ns,'probe_input_ns':probe_input_ns,'probe_closure_ns':probe_ns,'progress':progress,'freeze_value':freeze,'sites':[list(x) for x in sites],'heldout_sites':[list(x) for x in held],'learned_fields':learned,'post_probe_fields':fields(s,eye),'probes':probes}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite site-count factorial artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeSiteCountScheduleFactorialV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale site-count factorial source lock')
    rows=[run_case(seed,n,sch) for n in (2,4) for sch in SCHEDULES for seed in SEED_IDS];post=inputs()
    checks={'source_stable':locked==post,'twelve_workers':len(rows)==12,'three_seeds_per_cell':all(sum(r['site_count']==n and r['schedule']==sch for r in rows)==3 for n in (2,4) for sch in SCHEDULES),'exposures_exact':all(r['exposures_per_site']==[EXPOSURE]*r['site_count'] for r in rows),'step_counts_exact':all(r['steps']==r['site_count']*EXPOSURE for r in rows),'switch_counts_exact':all(r['switches']==(r['steps']-1 if r['schedule']=='interleaved' else r['site_count']-1) for r in rows),'write_counts_exact':all(r['train_input_writes']==9+18*r['switches'] for r in rows),'probe_matrix_exact':all(len(r['probes'])==(r['site_count']+len(r['heldout_sites']))*REPEATS and all(sum(p['site_index']==i for p in r['probes'])==REPEATS for i in range(r['site_count']+len(r['heldout_sites']))) for r in rows),'unique_winners':all(len(p['winners'])==1 for r in rows for p in r['probes']),'frozen_parity':all(r['freeze_value']==1.0 and r['learned_fields']==r['post_probe_fields'] for r in rows),'runtime_progress':all(r['progress']>0 for r in rows)}
    report={'schema':'VisionEyeSiteCountScheduleFactorialV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEED_IDS),'site_counts':[2,4],'schedules':list(SCHEDULES),'exposures_per_site':EXPOSURE,'eta':ETA,'units':N_UNITS,'heldout_probe_repeats':REPEATS},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'paired schedule/site-count test in one authored retinotopy learner; not a general capacity law or natural vision result.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
