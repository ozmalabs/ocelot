#!/usr/bin/env python3
"""Retrospective stage attribution for the frozen fresh string PBE capture."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/string_composition_fresh_pbe_v1_lock_20261003.json'
PRIOR_ANALYSIS=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_analysis_20261003.json'
OUT=ROOT/'evaluation/reports/string_composition_p4_stage_attribution_v1_20261003.json'
ARMS=('main','no_retrieval','no_retrieval_escalated','main_replay')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); prior=json.loads(PRIOR_ANALYSIS.read_text())
    if raw.get('source_lock_sha256')!=sha(LOCK): raise SystemExit('capture does not match source lock')
    if not prior.get('passed'): raise SystemExit('base benchmark analysis is not passing')
    result={'schema':'StringCompositionP4StageAttributionV1','retrospective':True,'base_analysis_passed':True,'arms':{},'hashes':{'capture':sha(RAW),'lock':sha(LOCK),'base_analysis':sha(PRIOR_ANALYSIS),'attributor':sha(Path(__file__))}}
    for arm in ARMS:
        rows=raw['cases'][arm]
        if len(rows)!=18: raise SystemExit(f'{arm}: expected 18 rows')
        data={'n':len(rows),'recognized':sum(x.get('recognized') is True for x in rows),'retrieved_exemplar':0,'enumerated':0,'enum_budget_exhausted':0,'enum_found_candidate':0,'accepted_holdout_exact':0,'accepted_holdout_wrong':0,'gapped':0,'stage_counts':{}}
        for x in rows:
            construction=x.get('construction'); enum=x.get('readback',{}).get('enumerate',{}); tested=enum.get('tested')
            outcome=x.get('outcome')
            if construction=='retrieved_exemplar': data['retrieved_exemplar']+=1
            if tested is not None:
                data['enumerated']+=1
                if x.get('enumerate_outcome')=='failed': data['enum_budget_exhausted']+=1
                elif x.get('enumerate_outcome')=='ok': data['enum_found_candidate']+=1
            if outcome=='accepted_holdout_ok': data['accepted_holdout_exact']+=1
            elif outcome=='accepted_holdout_fail': data['accepted_holdout_wrong']+=1
            elif outcome=='gapped': data['gapped']+=1
            key=f"{construction or 'enumeration'}:{outcome}"
            data['stage_counts'][key]=data['stage_counts'].get(key,0)+1
        data['all_tasks_recognized']=(data['recognized']==data['n'])
        result['arms'][arm]=data
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
