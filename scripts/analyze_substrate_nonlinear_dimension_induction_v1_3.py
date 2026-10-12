#!/usr/bin/env python3
"""Independent scoring of the locked nonlinear dimension transfer capture."""
from __future__ import annotations
import json, hashlib
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_nonlinear_dimension_induction_v1_3_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/nonlinear_dimension_induction_v1_3_lock_20261005.json'
OUT=ROOT/'evaluation/reports/substrate_nonlinear_dimension_induction_v1_3_analysis_20261005.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exact_matrix_transfer(base,target,matrix):
    if not isinstance(matrix,list) or len(matrix)!=4:return False
    mx=min(r[2] for r in base);my=min(r[3] for r in base)
    predicted={r[1]:(matrix[0]*(r[2]-mx)+matrix[1]*(r[3]-my),matrix[2]*(r[2]-mx)+matrix[3]*(r[3]-my)) for r in base}
    expected={r[1]:(r[2],r[3]) for r in target}
    return predicted==expected
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());cases=lock['inputs']['cases'];samples=raw['samples']
    native_path=Path(lock['native_extension']['path']).resolve()
    current_source={p:sha(ROOT/p) for p in lock['source_sha256']}
    ix={(s['family'],s['replicate'],s['enabled']):s for s in samples}
    expected={(c['family'],c['replicate'],arm) for c in cases for arm in (False,True)}
    observed=set(ix); duplicate=len(samples)-len(observed)
    by=defaultdict(list); status=Counter(); summary={}
    for fam in lock['inputs']['families']:
        for arm in (False,True):
            rows=[ix[(fam,r,arm)] for r in range(lock['inputs']['repetitions']) if (fam,r,arm) in ix]
            train=Counter(x['events'][0]['status'] for x in rows);transfer=Counter(x['events'][1]['status'] for x in rows)
            gens=[x['final_generators'] for x in rows]
            summary[f'{fam}:{"enabled" if arm else "frozen"}']={'n':len(rows),'train_status':dict(train),'transfer_status':dict(transfer),'any_quanta':sum(x['total_quanta']>0 for x in rows),'mean_train_ms':round(1000*sum(x['events'][0]['closure_seconds'] for x in rows)/max(1,len(rows)),3),'mean_transfer_ms':round(1000*sum(x['events'][1]['closure_seconds'] for x in rows)/max(1,len(rows)),3),'final_generators':gens}
    controls={};transfer_score={}
    for fam in lock['inputs']['families']:
        on=[ix[(fam,r,True)] for r in range(lock['inputs']['repetitions']) if (fam,r,True) in ix]
        off=[ix[(fam,r,False)] for r in range(lock['inputs']['repetitions']) if (fam,r,False) in ix]
        controls[fam]={'production_train_recognized':sum(x['events'][0]['status']=='recognized_transformed' for x in on),'production_transfer_recognized':sum(x['events'][1]['status']=='recognized_transformed' for x in on),'frozen_train_minted':sum(x['events'][0]['status']=='minted' for x in off),'frozen_transfer_minted':sum(x['events'][1]['status']=='minted' for x in off)}
        for arm,rows in [('enabled',on),('frozen',off)]:
            for row in rows:
                case=next(c for c in cases if c['family']==fam and c['replicate']==row['replicate'])
                initial={(g.get('name'),tuple(g.get('matrix') or [])) for g in row['initial_generators'] if g.get('kind')=='linear'}
                new=[g for g in row['final_generators'] if g.get('kind')=='linear' and (g.get('name'),tuple(g.get('matrix') or [])) not in initial]
                exact=[g for g in new if exact_matrix_transfer(case['transfer_base'],case['transfer_target'],g.get('matrix'))]
                transfer_score[f'{fam}:{arm}:{row["replicate"]}']={'new_linear_generators':new,'exact_transfer_prediction':bool(exact),'production_transfer_recognized':row['events'][1]['status']=='recognized_transformed'}
    lin_rows=[ix[('linear',r,True)] for r in range(lock['inputs']['repetitions']) if ('linear',r,True) in ix]
    linear_exact=sum(any(g.get('matrix')==[1,1,0,2] for g in x['final_generators'] if g.get('kind')=='linear') for x in lin_rows)
    linear_route=sum(x['events'][0]['status']=='recognized_transformed' and x['events'][1]['status']=='recognized_transformed' for x in lin_rows)
    gates={'raw_lock_matches':raw.get('lock_sha256')==sha(LOCK),'pre_post_source_native_stable':raw.get('source_native_stable') is True and raw.get('pre_lock_payload')==raw.get('post_lock_payload')==lock,'current_non_native_sources_match_lock':current_source==lock.get('source_sha256'),'captured_native_matches_lock':raw.get('provenance',{}).get('native_extension_sha256')==lock.get('native_extension',{}).get('sha256') and sha(native_path)==lock.get('native_extension',{}).get('sha256'),'complete_factorial':observed==expected,'no_duplicate_cells':duplicate==0,'all_event_rows_present':all(len(x['events'])==2 for x in samples),'all_timings_finite_positive':all(all(0<x['closure_seconds'] for x in s['events']) for s in samples),'nonlinear_schedules_not_exactly_linear':all(not c['any_exact_linear_fit'] for c in cases if c['family']=='coupled_quadratic'),'linear_family_schedules_are_linear':all(c['any_exact_linear_fit'] for c in cases if c['family']=='linear'),'linear_positive_control_exact_matrix':linear_exact==lock['inputs']['repetitions'],'linear_positive_control_transfer_route':linear_route==lock['inputs']['repetitions'],'frozen_arm_mints_no_linear_generators':all(not v['new_linear_generators'] for k,v in transfer_score.items() if ':frozen:' in k)}
    result={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),'n_samples':len(samples),'n_cells':len(observed),'duplicates':duplicate,'summary':summary,'controls':controls,'linear_positive_control':{'exact_matrix':linear_exact,'both_stages_recognized':linear_route},'independent_transfer_scoring':transfer_score,'interpretation':'This measures full-seed routing and transformation transfer on registered finite shape fixtures. Recognition status and exact map prediction are reported separately. A positive nonlinear induction outcome requires a newly minted map whose independent identity-aligned transfer prediction is exact and production decode recognizes the transfer observation. The run is inadmissible if the linear positive control fails.','limitations':['No claim about natural-task prevalence or general nonlinear learning.','Held-operator application is covered by separate codebook-ablation evidence, not this capture.','Resource timing is one process/build capture; no commodity-scale inference follows.']}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':result['admitted'],'gates':gates},indent=2));return 0 if result['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
