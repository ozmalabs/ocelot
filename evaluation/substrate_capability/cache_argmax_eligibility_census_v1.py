#!/usr/bin/env python3
"""Source-locked census of seed Argmax sites eligible for current memoization."""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from substrate.seed_loader import engine_rules_only

RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ARGMAX_ELIGIBILITY_CENSUS_V1_PREREG_20261004.md'
SEED_DIR=ROOT/'seeds'
LOCK=ROOT/'evaluation/substrate_capability/cache_argmax_eligibility_census_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/cache_argmax_eligibility_census_v1_20261004.json'
ELIGIBLE={'Var','Lit','Attr','Not','Abs','Count','Neighbours','InNeighbours','Eq','Lt','Lte','Gt','Gte','Minus','Plus','Times','And','Or','Filter','FilterList','Exists'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_paths(): return sorted(SEED_DIR.glob('*.json'))
def inputs(): return {'runner_sha256':sha(RUNNER),'protocol_sha256':sha(PROTOCOL),'seed_loader_sha256':sha(ROOT/'substrate/seed_loader.py'),'term_sha256':sha(ROOT/'runners/dsl/src/term.rs'),'seed_sha256':{p.name:sha(p) for p in seed_paths()}}
def stable(term):
    if not isinstance(term,dict): return True
    typ=term.get('type')
    if typ not in ELIGIBLE: return False
    return all(stable(value) for key,value in term.items() if key!='type')
def visit(obj, seed, rule, rows):
    if isinstance(obj,dict):
        if obj.get('type')=='Argmax':
            parts={'source':stable(obj.get('source')),'value':stable(obj.get('value')),'default':obj.get('default') is None or stable(obj.get('default'))}
            if all(parts.values()): rows.append({'seed':seed,'rule':rule,'eligibility':'eligible','parts':parts})
            else:
                bad=[]
                for key in ('source','value','default'):
                    term=obj.get(key)
                    if term is not None and not stable(term):
                        def collect(x):
                            if isinstance(x,dict):
                                t=x.get('type')
                                if isinstance(t,str) and t not in ELIGIBLE: bad.append(t)
                                for v in x.values(): collect(v)
                            elif isinstance(x,list):
                                for v in x: collect(v)
                        collect(term)
                rows.append({'seed':seed,'rule':rule,'eligibility':'ineligible','parts':parts,'unsupported_term_types':sorted(set(bad))})
        for value in obj.values(): visit(value,seed,rule,rows)
    elif isinstance(obj,list):
        for value in obj: visit(value,seed,rule,rows)
def census():
    rows=[]
    for path in seed_paths():
        raw=json.loads(path.read_text())
        if not isinstance(raw,dict): continue
        for rule in engine_rules_only(raw).get('rules') or []:
            if isinstance(rule,dict) and 'match' in rule: visit(rule,path.name,rule.get('name'),rows)
    rule_summary=Counter((r['eligibility'],r['seed'],r['rule']) for r in rows)
    return {'schema':'CacheArgmaxEligibilityCensusV1','site_count':len(rows),'eligible_sites':sum(r['eligibility']=='eligible' for r in rows),'ineligible_sites':sum(r['eligibility']=='ineligible' for r in rows),'rules_with_eligible_site':len({(r['seed'],r['rule']) for r in rows if r['eligibility']=='eligible'}),'rules_with_ineligible_site':len({(r['seed'],r['rule']) for r in rows if r['eligibility']=='ineligible'}),'eligible_by_seed':dict(sorted(Counter(r['seed'] for r in rows if r['eligibility']=='eligible').items())),'ineligible_terms':dict(sorted(Counter(t for r in rows for t in r.get('unsupported_term_types',[])).items())),'sites':rows}
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing to overwrite prior Argmax eligibility artifacts')
        LOCK.write_text(json.dumps({'schema':'CacheArgmaxEligibilityCensusV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing or stale Argmax eligibility source lock')
    payload=census(); post=inputs(); payload.update({'locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post}); payload['passed']=payload['source_stable'] and payload['site_count']>0
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:payload[k] for k in ('passed','source_stable','site_count','eligible_sites','ineligible_sites','rules_with_eligible_site','rules_with_ineligible_site','ineligible_terms')})); return 0 if payload['passed'] else 2
if __name__=='__main__': raise SystemExit(main())
