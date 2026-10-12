#!/usr/bin/env python3
"""Independent receptive-field scoring for eta/switch interaction runs."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_eta_switch_interaction_v1_20261004.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_eta_switch_interaction_v1_analysis_20261004.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_eta_switch_interaction_v1_lock_20261004.json';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def score(weights,site,n=16):
    total=sum(weights)
    if total<=0:return {'localized':False,'center':None,'spread':None,'distance':None}
    y=sum((i//n)*v for i,v in enumerate(weights))/total;x=sum((i%n)*v for i,v in enumerate(weights))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(weights))/total);dist=math.dist((y,x),site)
    return {'localized':spread<3 and dist<1,'center':[y,x],'spread':spread,'distance':dist}
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());groups=[]
    for condition in d['conditions']:
        b,e=condition['block_steps'],condition['eta'];rows=[r for r in d['rows'] if r['block_steps']==b and r['eta']==e];workers=[]
        for r in rows:
            c=r['checkpoints'][-1]
            loc={}
            for y,x in ((5,5),(12,12)):
                vals=[{'unit':f['unit'],**score(f['weights'],(y,x))} for f in c['fields']]
                best=min(vals,key=lambda z:float('inf') if z['distance'] is None else z['distance'])
                loc[f'{y},{x}']={'best':best,'units':[v['unit'] for v in vals if v['localized']]}
            workers.append({'seed':r['seed'],'both_localized':all(v['units'] for v in loc.values()),'locations':loc,'switches':r['switches'],'input_writes':r['input_writes'],'input_ms_per_step':r['input_update_ns']/8e9,'closure_ms_per_step':r['closure_mean_ns']/1e6})
        groups.append({'block_steps':b,'eta':e,'both_localized_count':sum(w['both_localized'] for w in workers),'n':len(workers),'median_input_ms_per_step':statistics.median(w['input_ms_per_step'] for w in workers),'median_closure_ms_per_step':statistics.median(w['closure_ms_per_step'] for w in workers),'workers':workers})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'all_conditions_three_seeds':all(g['n']==3 for g in groups),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'equal_final_exposures':all(r['checkpoints'][-1]['exposures_per_site']==[4000,4000] for r in d['rows'])}
    out={'schema':'VisionEyeEtaSwitchInteractionV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'groups':groups,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':[{'block_steps':g['block_steps'],'eta':g['eta'],'both_localized':g['both_localized_count']} for g in groups],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
