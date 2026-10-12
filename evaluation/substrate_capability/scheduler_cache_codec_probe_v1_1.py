#!/usr/bin/env python3
"""Source-locked round-trip probe for nonempty scheduler EvalCache families."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import assert_measuring_engine
import substrate_rs as sr
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_SCHEDULER_CACHE_CODEC_V1_1_PREREG_20261004.md'
SOURCES=('runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/src/persist.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock','substrate/seed_loader.py','seeds/can_native_reimplementation.json')
LOCK=ROOT/'evaluation/substrate_capability/scheduler_cache_codec_probe_v1_1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/scheduler_cache_codec_probe_v1_1_20261004.json'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def inputs():
    prov=assert_measuring_engine()
    return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'sources':{x:sha(ROOT/x) for x in SOURCES}}

def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing to overwrite prior cache-codec artifacts')
        LOCK.write_text(json.dumps({'schema':'SchedulerCacheCodecProbeV1_1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT)); return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing or stale cache-codec source lock')
    s=sr.Substrate()._inner
    seed=json.loads((ROOT/'seeds/can_native_reimplementation.json').read_text())
    s.load_seed_manifest(engine_rules_only(seed))
    owner=s.add_node('Microtheory',{'name':'owner'})
    target=s.add_node('Concept',{'name':'target'})
    s.add_edge(owner,'has_concept',target,{})
    if not s.export_rules(): raise RuntimeError('seed did not load the term-bearing rules needed for a valid cache key')
    cp=s.rule_scheduler_checkpoint()
    cache=cp['eval_cache']
    cache['entry_counts']=[0,1,1,1,2,0]
    cache['neighbours']=[[owner.value,'has_concept',False,{'__fset__':[{'__nid__':target.value}]}]]
    binding=[['owner',{'__nid__':owner.value}],['score',7]]
    cache['filter']=[[0,binding,{'__fset__':[{'__nid__':target.value}]}]]
    cache['argmax']=[[0,binding,{'__nid__':target.value}]]
    cache['holds']=[['codec_concept',None,target.value,{'__tuple__':[1,'x']}],['codec_concept',owner.value,None,True]]
    restore=sr.Substrate()._inner
    restore.graph_from_dict(s.graph_to_dict())
    rules=s.export_rules(); rules=json.loads(rules) if isinstance(rules,str) else rules
    restore.import_rules_preserving_match_order(rules)
    restore.restore_rule_scheduler_checkpoint(cp)
    actual=restore.rule_scheduler_checkpoint()
    post=inputs()
    checks={'source_stable':locked==post,'schema_v6':actual.get('schema')=='RuleSchedulerCheckpointV6',
        'nonempty_four_cache_families':actual['eval_cache']['entry_counts']==[0,1,1,1,2,0],
        'all_cache_payloads_exact':actual['eval_cache']['neighbours']==cache['neighbours'] and actual['eval_cache']['filter']==cache['filter'] and actual['eval_cache']['argmax']==cache['argmax'] and actual['eval_cache']['holds']==cache['holds'],
        'whole_checkpoint_exact':actual==cp}
    result={'schema':'SchedulerCacheCodecProbeV1_1','locked_inputs':locked,'post_run_inputs':post,'checks':checks,'passed':all(checks.values()),
        'claim_limit':'direct checkpoint codec round-trip with valid graph node IDs and a rule term; entries are seeded through the checkpoint wire object, so this does not prove evaluator-generated cache keys or hit behavior'}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':result['passed'],'checks':checks,'output':OUT.relative_to(ROOT).as_posix()}))
    return 0 if result['passed'] else 2

if __name__=='__main__': raise SystemExit(main())
