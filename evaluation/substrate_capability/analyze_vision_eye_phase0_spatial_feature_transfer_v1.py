#!/usr/bin/env python3
"""Independently score location and geometry diagnostics from raw weights."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_spatial_feature_transfer_v1_20261004.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_spatial_feature_transfer_v1_analysis_20261004.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_spatial_feature_transfer_v1_lock_20261004.json';ANALYZER=Path(__file__).resolve();SITES=((5,5),(12,12))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def score(weights,site,n=16):
    total=sum(weights)
    if total<=0:return {'localized':False,'center':None,'spread':None,'distance':None}
    y=sum((i//n)*w for i,w in enumerate(weights))/total;x=sum((i%n)*w for i,w in enumerate(weights))/total
    spread=math.sqrt(sum(w*((i//n-y)**2+(i%n-x)**2) for i,w in enumerate(weights))/total);distance=math.dist((y,x),site)
    return {'localized':spread<3 and distance<1,'center':[y,x],'spread':spread,'distance':distance}
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());groups=[]
    for arm in ('solid5_control','mixed_geometry'):
        rows=[r for r in d['rows'] if r['arm']==arm];workers=[]
        for r in rows:
            c=r['checkpoints'][-1];loc={}
            for site in SITES:
                vals=[{'unit':f['unit'],**score(f['weights'],site)} for f in c['fields']];best=min(vals,key=lambda z:float('inf') if z['distance'] is None else z['distance'])
                loc[f'{site[0]},{site[1]}']={'best':best,'units':[v['unit'] for v in vals if v['localized']]}
            expected={'5,5':2.0,'12,12':2.0} if arm=='solid5_control' else {'5,5':math.sqrt(4/3),'12,12':math.sqrt(0.8)}
            geometry={key:{'expected_uniform_pattern_rms':value,'observed_best_center_unit_rms':loc[key]['best']['spread'],'absolute_error':abs(loc[key]['best']['spread']-value)} for key,value in expected.items()}
            workers.append({'seed':r['seed'],'both_localized':all(v['units'] for v in loc.values()),'locations':loc,'exploratory_geometry_diagnostic':geometry,'input_writes':r['input_writes'],'input_ms_per_step':r['input_update_ns']/8e9,'closure_ms_per_step':r['closure_mean_ns']/1e6})
        groups.append({'arm':arm,'both_localized_count':sum(w['both_localized'] for w in workers),'n':len(workers),'median_geometry_absolute_error':statistics.median(v['absolute_error'] for w in workers for v in w['exploratory_geometry_diagnostic'].values()),'median_input_writes':statistics.median(w['input_writes'] for w in workers),'median_input_ms_per_step':statistics.median(w['input_ms_per_step'] for w in workers),'median_closure_ms_per_step':statistics.median(w['closure_ms_per_step'] for w in workers),'workers':workers})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'three_seeds_each_arm':all(g['n']==3 for g in groups),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'equal_final_exposures':all(r['checkpoints'][-1]['exposures_per_site']==[4000,4000] for r in d['rows'])}
    out={'schema':'VisionEyeSpatialFeatureTransferV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'groups':groups,'checks':checks,'passed':all(checks.values()),'exploratory_diagnostic':'Observed best-center unit spread compared with the analytically computed RMS spread of each uniform binary input mask; this was not a preregistered gate.','claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':[{'arm':g['arm'],'both_localized':g['both_localized_count'],'median_geometry_error':g['median_geometry_absolute_error'],'median_writes':g['median_input_writes']} for g in groups],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
