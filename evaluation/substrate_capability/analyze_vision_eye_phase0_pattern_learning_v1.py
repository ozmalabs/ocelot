#!/usr/bin/env python3
"""Independent RF-statistic and outcome analysis for phase-0 pattern learning."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_pattern_learning_v1_20261004.json'
ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_pattern_learning_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_pattern_learning_v1_lock_20261004.json'
ANALYZER=Path(__file__).resolve()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def metrics(weights,n=16):
    total=sum(weights)
    if total<=0:return [float('nan'),float('nan')],float('nan')
    cy=sum((i//n)*w for i,w in enumerate(weights))/total;cx=sum((i%n)*w for i,w in enumerate(weights))/total
    spread=math.sqrt(sum(w*((i//n-cy)**2+(i%n-cx)**2) for i,w in enumerate(weights))/total)
    return [cy,cx],spread
def main():
    analyzer_before=file_sha(ANALYZER);data=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text())
    per=[]
    for r in data['rows']:
        units=[]
        for f in r['fields']:
            center,spread=metrics(f['weights']);units.append({'unit':f['unit'],'center':center,'spread':spread,'winner':f['winner'],'center_delta':math.dist(center,r['target_center'])})
        best=min(units,key=lambda u:u['spread']);per.append({'condition':r['condition'],'seed':r['seed'],'target_center':r['target_center'],'best_spread':best['spread'],'best_center':best['center'],'best_center_delta':best['center_delta'],'localized':best['spread']<3.0 and best['center_delta']<1.0,'units':units,'closure_mean_ns':r['closure_mean_ns'],'input_update_ns':r['input_update_ns'],'input_writes':r['input_writes'],'argmax_entries':r['argmax_entries']})
    fixed=[x for x in per if x['condition']=='fixed'];shuffled=[x for x in per if x['condition']=='shuffled']
    checks={'all_six_fixed_cases_localize':len(fixed)==6 and all(x['localized'] for x in fixed),'no_shuffled_case_localizes':len(shuffled)==6 and not any(x['localized'] for x in shuffled),'paired_sequence_control_distinct':all(a['seed']==b['seed'] and a['target_center']==b['target_center'] for a,b in zip(sorted(fixed,key=lambda x:(x['seed'],x['target_center'])),sorted(shuffled,key=lambda x:(x['seed'],x['target_center'])))),'input_horizon_exact':all(r['steps']==4000 and r['active_count_min']==25 and r['active_count_max']==25 for r in data['rows']),'source_lock_stable':data['locked_inputs']==lock['locked_inputs']==data['post_run_inputs'],'runner_pass_matches_checks':data['passed'] and all(data['checks'].values()),'analyzer_source_stable':analyzer_before==file_sha(ANALYZER)}
    result={'schema':'VisionEyePhase0PatternLearningV1Analysis','analyzer_sha256':analyzer_before,'analyzer_source_stable':analyzer_before==file_sha(ANALYZER),'capture_sha256':hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),'lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'cases':per,'fixed_localized':sum(x['localized'] for x in fixed),'fixed_total':len(fixed),'shuffled_localized':sum(x['localized'] for x in shuffled),'shuffled_total':len(shuffled),'median_closure_ms':{c:statistics.median(x['closure_mean_ns']/1e6 for x in per if x['condition']==c) for c in ('fixed','shuffled')},'checks':checks,'passed':all(checks.values()),'claim_limit':data['claim_limit']}
    ANALYSIS.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'fixed_localized':f"{result['fixed_localized']}/{result['fixed_total']}",'shuffled_localized':f"{result['shuffled_localized']}/{result['shuffled_total']}",'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
