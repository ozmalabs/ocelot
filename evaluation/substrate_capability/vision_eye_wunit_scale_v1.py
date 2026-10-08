#!/usr/bin/env python3
"""Scale source-authored phase-0 vision-eye rule closure by WUnit count."""
from __future__ import annotations
import hashlib,json,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import domains.seed_registry
from domains.engine_provenance import assert_measuring_engine
from domains.eye_world import PreVisualWorld,set_params
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core,load_seeds_into
from substrate_rs import _native

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_WUNIT_SCALE_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_wunit_scale_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/vision_eye_wunit_scale_v1_20261004.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SIZES=(4,16,64,256);REPS=3;STEPS=8;H=W=16;CAP=200_000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{p.name:sha(p) for p in sorted((ROOT/'seeds').glob('*.json'))},'sources':{p:sha(ROOT/p) for p in SOURCES}}
def build(n):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye'])
    wp=s.nodes('WaveParams')[0]
    for key,value in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,key,value)
    wave=WaveWorld(s,h=H,w=W,seed=0);eye=PreVisualWorld(wave,n_units=n,seed=0)
    set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=5e-4)
    patch=[rc for rc in wave.cells if 3<=rc[0]<=7 and 3<=rc[1]<=7]
    eye.present_bursts(patch)
    return s,eye,wave
def digest(s):return hashlib.sha256(json.dumps(s.graph_to_dict(),sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def run(s,eye,instrument):
    nat=s._inner
    nat.scale_audit_set_enabled(False);nat.scale_audit_set_per_rule_enabled(False);nat.scale_audit_reset();nat.scale_audit_per_rule_reset()
    if instrument:nat.scale_audit_set_per_rule_enabled(True);nat.scale_audit_set_enabled(True)
    times=[];steps=[]
    for i in range(1,STEPS+1):
        s.set_attr(eye.eye,'step',float(i))
        t=time.perf_counter_ns();steps.append(int(nat.run_rules(CAP)));times.append(time.perf_counter_ns()-t)
    counters={str(k):int(v) for k,v in dict(nat.scale_audit_snapshot()).items() if not str(k).endswith('_ns') and k!='scheduler_plan_ns'} if instrument else {}
    nat.scale_audit_set_per_rule_enabled(False);nat.scale_audit_set_enabled(False)
    return {'timings_ns':times,'steps':steps,'median_ns':int(statistics.median(times)),'p95_ns':sorted(times)[min(len(times)-1,int(.95*(len(times)-1)))],'graph_sha256':digest(s),'graph_nodes':len(s.graph_to_dict()['nodes']),'graph_edges':len(s.graph_to_dict()['edges']),'cache_entry_counts':nat.rule_scheduler_checkpoint()['eval_cache']['entry_counts'],'counters':counters}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior WUnit scaling artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyeWUnitScaleV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale WUnit scaling lock')
    rows=[]
    for rep in range(REPS):
        order=list(SIZES if rep%2==0 else reversed(SIZES))
        for n in order:
            timed_s,timed_eye,_=build(n);timed=run(timed_s,timed_eye,False)
            audit_s,audit_eye,_=build(n);audit=run(audit_s,audit_eye,True)
            rows.append({'replicate':rep,'wunit_count':n,'order_position':order.index(n),'timed':timed,'audited':audit,'same_outcome':timed['graph_sha256']==audit['graph_sha256'] and timed['steps']==audit['steps']})
    post=inputs();summaries=[]
    for n in SIZES:
        group=[r for r in rows if r['wunit_count']==n]
        summaries.append({'wunit_count':n,'median_closure_ns':int(statistics.median(x['timed']['median_ns'] for x in group)),'median_total_ns':int(statistics.median(sum(x['timed']['timings_ns']) for x in group)),'median_nodes':int(statistics.median(x['timed']['graph_nodes'] for x in group)),'median_edges':int(statistics.median(x['timed']['graph_edges'] for x in group)),'median_candidates':int(statistics.median(x['audited']['counters'].get('cand_tested',0) for x in group)),'median_terms':int(statistics.median(x['audited']['counters'].get('term_evals_total',0) for x in group)),'median_argmax_evals':int(statistics.median(x['audited']['counters'].get('term_eval:Argmax',0) for x in group)),'median_argmax_entries':int(statistics.median(x['audited']['cache_entry_counts'][3] for x in group))})
    checks={'source_stable':locked==post,'all_timing_audit_outcomes_equal':all(r['same_outcome'] for r in rows),'all_cases_completed':len(rows)==len(SIZES)*REPS,'every_case_reaches_argmax':all(r['audited']['counters'].get('term_eval:Argmax',0)>0 for r in rows),'every_case_progresses':all(sum(r['timed']['steps'])>0 for r in rows)}
    report={'schema':'VisionEyeWUnitScaleV1','locked_inputs':locked,'post_run_inputs':post,'sizes':list(SIZES),'replicates':REPS,'steps_per_case':STEPS,'rows':rows,'summaries':summaries,'checks':checks,'passed':all(checks.values()),'claim_limit':'one authored phase-0 positive-control family on one host with four graph sizes and three replicates; timed arm excludes audit instrumentation; audited twin verifies work and semantic parity; no cache-disabled control, natural input sample, cross-host replication, or general capability claim'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'summaries':summaries,'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
