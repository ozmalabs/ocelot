#!/usr/bin/env python3
"""Replay an evaluator-generated Argmax cache from the source vision-eye rule."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import domains.seed_registry  # register source manifests
import substrate_rs as sr
from domains.engine_provenance import assert_measuring_engine
from domains.eye_world import PreVisualWorld,set_params
from domains.wave_world import WaveWorld
from substrate.boot_core import boot_core,load_seeds_into
from substrate_rs import _native

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_SCHEDULER_CACHE_VISION_EYE_ARGMAX_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/scheduler_cache_vision_eye_argmax_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/scheduler_cache_vision_eye_argmax_v1_20261004.json'
SOURCES=('substrate/boot_core.py','domains/eye_world.py','domains/wave_world.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
SEEDS=('vision_eye.json','vision_waves.json')
CAP=200_000

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_sha256':{name:sha(ROOT/'seeds'/name) for name in SEEDS},'sources':{name:sha(ROOT/name) for name in SOURCES}}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def build():
    s,agent=boot_core();load_seeds_into(s,agent,['vision_waves','vision_eye'])
    params=s.nodes('WaveParams')[0]
    for key,value in (('propagate',0.0),('oja',1.0),('oja_eta',0.0)):s.set_attr(params,key,value)
    wave=WaveWorld(s,h=16,w=16,seed=0);eye=PreVisualWorld(wave,n_units=4,seed=0)
    set_params(eye,eye=1.0,phase0=1.0,eye_open=0.0,saw=0.0,ph0_eta=5e-4)
    patch=[rc for rc in wave.cells if 3<=rc[0]<=7 and 3<=rc[1]<=7]
    s._inner.scale_audit_set_enabled(False);s._inner.scale_audit_reset();s._inner.scale_audit_set_enabled(True)
    for step in range(1,5):
        wave.step(ignite_k=0)
        eye.present_bursts(patch)
        s.set_attr(eye.eye,'step',float(step))
        s._inner.run_rules(CAP)
    return s,eye
def snapshot(s):
    rules=s._inner.export_rules();rules=json.loads(rules) if isinstance(rules,str) else rules
    return {'graph':s.graph_to_dict(),'rules':rules,'scheduler':s._inner.rule_scheduler_checkpoint()}
def restore(state):
    s=sr.Substrate()._inner;s.graph_from_dict(state['graph']);s.import_rules_preserving_match_order(state['rules']);s.restore_rule_scheduler_checkpoint(state['scheduler']);return s
def run(s):
    s.scale_audit_set_enabled(False);s.scale_audit_set_per_rule_enabled(False);s.scale_audit_reset();s.scale_audit_per_rule_reset();s.scale_audit_set_per_rule_enabled(True);s.scale_audit_set_enabled(True)
    steps=int(s.run_rules(CAP))
    glob={str(k):int(v) for k,v in dict(s.scale_audit_snapshot()).items() if not str(k).endswith('_ns') and k!='scheduler_plan_ns'}
    ids={int(a):(int(store),int(local)) for a,store,local in s.scale_audit_rule_identity_snapshot()};per={}
    for aid,metric,value in s.scale_audit_per_rule_snapshot():
        if int(aid) in ids:per.setdefault(str(ids[int(aid)][1]),{})[str(metric)]=int(value)
    s.scale_audit_set_per_rule_enabled(False);s.scale_audit_set_enabled(False)
    return {'steps':steps,'global':glob,'per_rule':per,'graph':s.graph_to_dict(),'scheduler':s.rule_scheduler_checkpoint()}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior vision-eye cache artifacts')
        LOCK.write_text(json.dumps({'schema':'SchedulerCacheVisionEyeArgmaxV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale vision-eye cache source lock')
    source,eye=build();state=snapshot(source);counts=state['scheduler']['eval_cache']['entry_counts']
    source._inner.force_all_dirty();state=snapshot(source);state['scheduler']['any_mutation']=False
    live=restore(state);replay=restore(state)
    roundtrip=(live.rule_scheduler_checkpoint()==state['scheduler'] and replay.rule_scheduler_checkpoint()==state['scheduler'])
    live_out=run(live);replay_out=run(replay);post=inputs()
    source_rules=state['rules'];winner_rule=next((r for r in source_rules if r.get('name')=='ph0_wunit_winner'),None)
    unit_state=[n for n in source.graph_to_dict()['nodes'] if n['type']=='WUnit']
    checks={'source_stable':locked==post,'four_input_steps':all(float(source.node(eye.eye)['attrs']['step'])==4.0 for _ in [0]),'source_winner_rule_loaded':winner_rule is not None,
      'argmax_evaluated':int(dict(source._inner.scale_audit_snapshot()).get('term_eval:Argmax',0))>0,'argmax_cache_nonempty':counts[3]>0,
      'four_units_present':len(unit_state)==4,'checkpoint_roundtrip_exact':roundtrip,
      'global_work_exact':live_out['global']==replay_out['global'],'per_rule_work_exact':canonical(live_out['per_rule'])==canonical(replay_out['per_rule']),
      'post_graph_exact':canonical(live_out['graph'])==canonical(replay_out['graph']),'post_scheduler_exact':canonical(live_out['scheduler'])==canonical(replay_out['scheduler'])}
    report={'schema':'SchedulerCacheVisionEyeArgmaxV1','locked_inputs':locked,'post_run_inputs':post,'cache_entry_counts':counts,'argmax_evaluations_during_input':int(dict(source._inner.scale_audit_snapshot()).get('term_eval:Argmax',0)),'source_winner_rule':winner_rule,'winner_units_at_capture':[n for n in unit_state if n['attrs'].get('winner')==1.0],'live':live_out,'replay':replay_out,'checks':checks,'passed':all(checks.values()),
      'claim_limit':'one source-authored vision-eye phase-0 rule, four units, a fixed 5x5 burst patch, four input steps and one no-op replay closure; does not establish natural input prevalence, cache speedup, scaling, or general inference capability'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'cache_entry_counts':counts,'argmax_evaluations':report['argmax_evaluations_during_input'],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
