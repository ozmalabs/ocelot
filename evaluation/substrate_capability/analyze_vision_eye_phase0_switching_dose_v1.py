#!/usr/bin/env python3
"""Independently score source-locked visual switching-dose captures."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_switching_dose_v1_20261004.json'
ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_switching_dose_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_switching_dose_v1_lock_20261004.json'
ANALYZER=Path(__file__).resolve();BLOCKS=(1,10,100,1000,4000);SITES=((5,5),(12,12))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(weights,n=16):
    total=sum(weights)
    if total<=0:return [float('nan'),float('nan')],float('nan')
    cy=sum((i//n)*w for i,w in enumerate(weights))/total;cx=sum((i%n)*w for i,w in enumerate(weights))/total
    spread=math.sqrt(sum(w*((i//n-cy)**2+(i%n-cx)**2) for i,w in enumerate(weights))/total)
    return [cy,cx],spread
def score(fields,site):
    vals=[]
    for f in fields:
        center,spread=metrics(f['weights']);vals.append({'unit':f['unit'],'center':center,'spread':spread,'distance':math.dist(center,site)})
    selected=[x for x in vals if x['spread']<3 and x['distance']<1]
    return {'localized':bool(selected),'units': [x['unit'] for x in selected],'best_spread':min(x['spread'] for x in vals),'best_distance':min(x['distance'] for x in vals)}
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());groups=[]
    for block in BLOCKS:
        rows=[r for r in d['rows'] if r['block_steps']==block]
        final=[]
        for r in rows:
            cp=r['checkpoints'][-1];scores={f'{y},{x}':score(cp['fields'],(y,x)) for y,x in SITES}
            final.append({'seed':r['seed'],'both_localized':all(x['localized'] for x in scores.values()),'scores':scores,'switches':r['switches'],'writes':r['input_writes'],'input_ms_per_step':r['input_update_ns']/1e6/8000,'closure_ms_per_step':r['closure_mean_ns']/1e6})
        groups.append({'block_steps':block,'retained_both_count':sum(x['both_localized'] for x in final),'n':len(final),'median_switches':statistics.median(x['switches'] for x in final),'median_input_writes':statistics.median(x['writes'] for x in final),'median_input_ms_per_step':statistics.median(x['input_ms_per_step'] for x in final),'median_closure_ms_per_step':statistics.median(x['closure_ms_per_step'] for x in final),'workers':final})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'five_doses_three_seeds':all(g['n']==3 for g in groups),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'final_equal_exposure':all(all(next(r for r in d['rows'] if r['seed']==w['seed'] and r['block_steps']==g['block_steps'])['checkpoints'][-1]['exposures_per_site']==[4000,4000] for w in g['workers']) for g in groups)}
    result={'schema':'VisionEyeSwitchingDoseV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'groups':groups,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']}
    ANALYSIS.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'dose_summary':[{k:g[k] for k in ('block_steps','retained_both_count','median_switches','median_input_writes')} for g in groups],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
