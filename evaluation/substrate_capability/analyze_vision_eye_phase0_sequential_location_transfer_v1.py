#!/usr/bin/env python3
"""Independently score per-unit receptive fields across sequential stages."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_sequential_location_transfer_v1_20261004.json'
ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_sequential_location_transfer_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_sequential_location_transfer_v1_lock_20261004.json'
ANALYZER=Path(__file__).resolve()
def file_sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(weights,n=16):
    total=sum(weights)
    if total<=0:return [float('nan'),float('nan')],float('nan')
    cy=sum((i//n)*w for i,w in enumerate(weights))/total;cx=sum((i%n)*w for i,w in enumerate(weights))/total
    spread=math.sqrt(sum(w*((i//n-cy)**2+(i%n-cx)**2) for i,w in enumerate(weights))/total)
    return [cy,cx],spread
def localized(fields,center):
    rows=[]
    for f in fields:
        c,s=metrics(f['weights']);rows.append({'unit':f['unit'],'center':c,'spread':s,'delta':math.dist(c,center)})
    good=[x for x in rows if x['spread']<3.0 and x['delta']<1.0]
    return {'localized':bool(good),'localized_units':[x['unit'] for x in good],'best_spread':min(x['spread'] for x in rows),'best_center_delta':min(x['delta'] for x in rows),'units':rows}
def main():
    analyzer_before=file_sha(ANALYZER);data=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=[]
    for r in data['rows']:
        stages=[]
        for i,stage in enumerate(r['stages']):
            locs=[stage['trained_center']]
            if i:locs=[tuple(x) for x in (r['stages'][0]['trained_center'],r['stages'][1]['trained_center'])]
            scores={f'{x[0]},{x[1]}':localized(stage['fields'],x) for x in locs}
            stages.append({'stage':stage['stage'],'trained_center':stage['trained_center'],'localized_by_location':scores,'closure_mean_ns':stage['closure_mean_ns'],'input_writes_at_boundary':stage['input_writes_at_boundary']})
        workers.append({'seed':r['seed'],'order':r['order'],'stages':stages})
    checks={'stage1_acquires_first_location':all(w['stages'][0]['localized_by_location'][','.join(map(str,w['stages'][0]['trained_center']))]['localized'] for w in workers),'stage2_acquires_second_location':all(w['stages'][1]['localized_by_location'][','.join(map(str,w['stages'][1]['trained_center']))]['localized'] for w in workers),'stage2_retains_first_location':all(w['stages'][1]['localized_by_location'][','.join(map(str,w['stages'][0]['trained_center']))]['localized'] for w in workers),'both_training_orders_pass':{w['order'] for w in workers}=={'A_then_B','B_then_A'},'input_horizon_and_activity':all(all(s['steps']==4000 and s['active_count']==25 for s in r['stages']) for r in data['rows']),'source_lock_stable':data['locked_inputs']==lock['locked_inputs']==data['post_run_inputs'],'runner_gates_pass':data['passed'] and all(data['checks'].values()),'analyzer_source_stable':analyzer_before==file_sha(ANALYZER)}
    result={'schema':'VisionEyePhase0SequentialTransferV1Analysis','analyzer_sha256':analyzer_before,'capture_sha256':file_sha(CAPTURE),'lock_sha256':file_sha(LOCK),'workers':workers,'checks':checks,'passed':all(checks.values()),'claim_limit':data['claim_limit']}
    ANALYSIS.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
