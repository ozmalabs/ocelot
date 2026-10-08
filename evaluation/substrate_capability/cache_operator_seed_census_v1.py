#!/usr/bin/env python3
"""Source-locked census of Argmax/Holds terms in executable seed rules."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from substrate.seed_loader import engine_rules_only

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CACHE_OPERATOR_SEED_CENSUS_V1_PREREG_20261004.md'
SEED_DIR=ROOT/'seeds'
LOCK=ROOT/'evaluation/substrate_capability/cache_operator_seed_census_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/cache_operator_seed_census_v1_20261004.json'
OPS=('Argmax','Holds')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def seed_paths():return sorted(SEED_DIR.glob('*.json'))
def inputs():return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'seed_loader_sha256':sha(ROOT/'substrate/seed_loader.py'),'seed_sha256':{p.name:sha(p) for p in seed_paths()}}
def count_terms(obj):
    counts={op:0 for op in OPS}
    if isinstance(obj,dict):
        typ=obj.get('type')
        if typ in counts:counts[typ]+=1
        for value in obj.values():
            sub=count_terms(value)
            for op in OPS:counts[op]+=sub[op]
    elif isinstance(obj,list):
        for value in obj:
            sub=count_terms(value)
            for op in OPS:counts[op]+=sub[op]
    return counts
def census():
    seeds=[];totals={'Argmax':0,'Holds':0};rules_with={'Argmax':0,'Holds':0,'both':0}
    for path in seed_paths():
        manifest=json.loads(path.read_text())
        if not isinstance(manifest,dict):continue
        executable=engine_rules_only(manifest).get('rules') or []
        rows=[]
        for rule in executable:
            if not isinstance(rule,dict) or 'match' not in rule:continue
            parts={key:count_terms(rule.get(key)) for key in ('match','where','effects')}
            sums={op:sum(parts[k][op] for k in parts) for op in OPS}
            if any(sums.values()):
                rows.append({'name':rule.get('name'),'terms':sums,'by_section':parts})
                for op in OPS:
                    totals[op]+=sums[op]
                    rules_with[op]+=int(sums[op]>0)
                rules_with['both']+=int(all(sums[op]>0 for op in OPS))
        if rows:seeds.append({'seed':path.name,'executable_rule_count':sum(1 for r in executable if isinstance(r,dict) and 'match' in r),'operator_rules':rows})
    return {'schema':'CacheOperatorSeedCensusV1','operator_occurrences':totals,'rules_with_operator':rules_with,'seed_count':len(seeds),'seeds':seeds}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite prior cache-operator census')
        LOCK.write_text(json.dumps({'schema':'CacheOperatorSeedCensusV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale cache-operator census lock')
    payload=census();post=inputs();payload.update({'locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post})
    payload['passed']=payload['source_stable'] and payload['seed_count']>0
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':payload['passed'],'source_stable':payload['source_stable'],'seed_count':payload['seed_count'],'operator_occurrences':payload['operator_occurrences'],'rules_with_operator':payload['rules_with_operator'],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if payload['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
