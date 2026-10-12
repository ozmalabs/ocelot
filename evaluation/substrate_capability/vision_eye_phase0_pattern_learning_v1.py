#!/usr/bin/env python3
"""Fixed-location versus activity-matched shuffled phase-0 learning panel."""
from __future__ import annotations
import hashlib,json,random,sys,time
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
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_EYE_PHASE0_PATTERN_LEARNING_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_pattern_learning_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/vision_eye_phase0_pattern_learning_v1_20261004.json'
SOURCES=('substrate/boot_core.py','substrate/seed_loader.py','domains/eye_world.py','domains/wave_world.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json')
SITES=((5,5),(12,12));SEED_IDS=(0,1,2);CONDITIONS=('fixed','shuffled');N_UNITS=4;STEPS=4000;ACTIVE=25;H=W=16;CAP=200_000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{name:sha(ROOT/'seeds'/name) for name in SEEDS},'sources':{name:sha(ROOT/name) for name in SOURCES}}
def run_case(condition,seed,site):
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye'])
    wp=s.nodes('WaveParams')[0]
    for key,value in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(wp,key,value)
    wave=WaveWorld(s,h=H,w=W,seed=seed);eye=PreVisualWorld(wave,n_units=N_UNITS,seed=seed)
    set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=5e-4)
    cell_by_index={r*W+c:node for (r,c),node in wave.cells.items()}
    target={r*W+c for r in range(site[0]-2,site[0]+3) for c in range(site[1]-2,site[1]+3)}
    rng=random.Random(90_000+seed*101+site[0]*17+site[1])
    previous=set();input_hash=hashlib.sha256();active_counts=[];write_count=0;input_ns=0;closure_ns=0;progress=0
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_set_per_rule_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_per_rule_reset()
    for step in range(1,STEPS+1):
        current=target if condition=='fixed' else set(rng.sample(range(H*W),ACTIVE))
        t=time.perf_counter_ns()
        for idx in previous-current:s.set_attr(cell_by_index[idx],'bursting',0.0);write_count+=1
        for idx in current-previous:s.set_attr(cell_by_index[idx],'bursting',1.0);write_count+=1
        input_ns+=time.perf_counter_ns()-t;previous=current
        active_counts.append(len(current));input_hash.update(bytes(sorted(current)))
        s.set_attr(eye.eye,'step',float(step))
        t=time.perf_counter_ns();progress+=int(s._inner.run_rules(CAP));closure_ns+=time.perf_counter_ns()-t
    fields=[]
    for i,u in enumerate(eye.units):
        rf=eye.rf(i);cy,cx=rf_centre(rf);fields.append({'unit':i,'winner':float(s.node(u)['attrs']['winner']),'spread':float(rf_spread(rf)),'center':[float(cy),float(cx)],'weights':[float(v) for v in rf.reshape(-1)]})
    rules=s._inner.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
    nodes=s.graph_to_dict()['nodes'];edges=s.graph_to_dict()['edges']
    return {'condition':condition,'seed':seed,'target_center':list(site),'steps':STEPS,'active_count_min':min(active_counts),'active_count_max':max(active_counts),'active_count_total':sum(active_counts),'input_sequence_sha256':input_hash.hexdigest(),'input_writes':write_count,'input_update_ns':input_ns,'closure_ns':closure_ns,'closure_mean_ns':closure_ns//STEPS,'closure_progress_steps':progress,'graph_node_count':len(nodes),'graph_edge_count':len(edges),'argmax_entries':s._inner.rule_scheduler_checkpoint()['eval_cache']['entry_counts'][3],'ph0_rule_names':[r.get('name') for r in rules if str(r.get('name','')).startswith('ph0_wunit_')],'fields':fields}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior phase-0 pattern-learning artifacts')
        LOCK.write_text(json.dumps({'schema':'VisionEyePhase0PatternLearningV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale phase-0 pattern-learning source lock')
    rows=[]
    for seed in SEED_IDS:
        for site in SITES:
            for condition in CONDITIONS:rows.append(run_case(condition,seed,site))
    post=inputs();checks={'source_stable':locked==post,'case_count':len(rows)==len(SEED_IDS)*len(SITES)*len(CONDITIONS),'input_counts_exact':all(r['active_count_min']==ACTIVE and r['active_count_max']==ACTIVE for r in rows),'all_rules_loaded':all('ph0_wunit_winner' in r['ph0_rule_names'] for r in rows),'all_steps_progressed':all(r['closure_progress_steps']>0 for r in rows),'all_argmax_nonempty':all(r['argmax_entries']>0 for r in rows)}
    report={'schema':'VisionEyePhase0PatternLearningV1','locked_inputs':locked,'post_run_inputs':post,'parameters':{'seeds':list(SEED_IDS),'patch_centers':[list(x) for x in SITES],'conditions':list(CONDITIONS),'units':N_UNITS,'steps':STEPS,'active_cells_per_step':ACTIVE},'rows':rows,'checks':checks,'passed':all(checks.values()),'claim_limit':'twelve authored fixed-patch versus temporally shuffled cases on one 16x16 vision-eye family; no human/natural task distribution, cross-domain transfer, alternative learning settings, or broad self-improvement claim'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'cases':len(rows),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
