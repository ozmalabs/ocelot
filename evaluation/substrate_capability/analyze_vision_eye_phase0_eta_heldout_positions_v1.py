#!/usr/bin/env python3
"""Independently score eta rescue on held-out spatial pairs and seeds."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_eta_heldout_positions_v1_20261004.json';ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_eta_heldout_positions_v1_analysis_20261004.json';LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_eta_heldout_positions_v1_lock_20261004.json';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def score(weights,site,n=16):
    total=sum(weights)
    if total<=0:return {'localized':False,'center':None,'spread':None,'distance':None}
    y=sum((i//n)*v for i,v in enumerate(weights))/total;x=sum((i%n)*v for i,v in enumerate(weights))/total
    spread=math.sqrt(sum(v*((i//n-y)**2+(i%n-x)**2) for i,v in enumerate(weights))/total);distance=math.dist((y,x),site)
    return {'localized':spread<3 and distance<1,'center':[y,x],'spread':spread,'distance':distance}
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());groups=[]
    for pair in ('original','heldout'):
        for eta in (0.0005,0.005):
            rows=[r for r in d['rows'] if r['pair_id']==pair and r['eta']==eta];workers=[]
            for r in rows:
                c=r['checkpoints'][-1];loc={}
                for idx,site in enumerate(r['sites']):
                    vals=[{'unit':f['unit'],**score(f['weights'],site)} for f in c['fields']];best=min(vals,key=lambda z:float('inf') if z['distance'] is None else z['distance'])
                    loc[f'{site[0]},{site[1]}']={'best':best,'units':[v['unit'] for v in vals if v['localized']]}
                workers.append({'seed':r['seed'],'both_localized':all(v['units'] for v in loc.values()),'locations':loc,'input_writes':r['input_writes'],'input_ms_per_step':r['input_update_ns']/8e9,'closure_ms_per_step':r['closure_mean_ns']/1e6})
            groups.append({'pair_id':pair,'eta':eta,'both_localized_count':sum(w['both_localized'] for w in workers),'n':len(workers),'median_closure_ms_per_step':statistics.median(w['closure_ms_per_step'] for w in workers),'median_input_ms_per_step':statistics.median(w['input_ms_per_step'] for w in workers),'workers':workers})
    checks={'capture_gates_pass':d['passed'] and all(d['checks'].values()),'four_cells_three_seeds':all(g['n']==3 for g in groups),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'analyzer_stable':before==sha(ANALYZER),'equal_exposures_and_writes':all(r['exposures_per_site']==[4000,4000] and r['input_writes']==399975 for r in d['rows'])}
    out={'schema':'VisionEyeEtaHeldoutPositionsV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'groups':groups,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':[{'pair':g['pair_id'],'eta':g['eta'],'retained':g['both_localized_count']} for g in groups],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
