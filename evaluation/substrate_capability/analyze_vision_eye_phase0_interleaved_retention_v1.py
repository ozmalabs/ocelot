#!/usr/bin/env python3
"""Independent scoring of blocked versus interleaved spatial learning."""
from __future__ import annotations
import hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/vision_eye_phase0_interleaved_retention_v1_20261004.json'
ANALYSIS=ROOT/'evaluation/reports/vision_eye_phase0_interleaved_retention_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_eye_phase0_interleaved_retention_v1_lock_20261004.json'
ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(weights,n=16):
    total=sum(weights)
    if total<=0:return [float('nan'),float('nan')],float('nan')
    cy=sum((i//n)*w for i,w in enumerate(weights))/total;cx=sum((i%n)*w for i,w in enumerate(weights))/total
    spread=math.sqrt(sum(w*((i//n-cy)**2+(i%n-cx)**2) for i,w in enumerate(weights))/total)
    return [cy,cx],spread
def score(fields,site):
    units=[]
    for f in fields:
        center,spread=metrics(f['weights']);units.append({'unit':f['unit'],'center':center,'spread':spread,'delta':math.dist(center,site)})
    good=[u for u in units if u['spread']<3 and u['delta']<1]
    return {'localized':bool(good),'units_localized':[u['unit'] for u in good],'best_spread':min(u['spread'] for u in units),'best_delta':min(u['delta'] for u in units)}
def main():
    analyzer_before=sha(ANALYZER);data=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());sites=data['parameters']['sites'];workers=[]
    for r in data['rows']:
        checkpoints=[]
        for c in r['checkpoints']:
            per_site={f'{site[0]},{site[1]}':score(c['fields'],site) for site in sites}
            checkpoints.append({'step':c['step'],'exposures_per_site':c['exposures_per_site'],'location_scores':per_site})
        workers.append({'seed':r['seed'],'mode':r['mode'],'checkpoints':checkpoints,'closure_mean_ns':r['closure_mean_ns'],'input_update_ns':r['input_update_ns'],'input_writes':r['input_writes']})
    final=[w for w in workers if w['checkpoints'][-1]['step']==8000]
    inter=[w for w in final if w['mode']=='interleaved'];blocked=[w for w in final if w['mode']=='blocked']
    all_both=lambda group: all(all(v['localized'] for v in w['checkpoints'][-1]['location_scores'].values()) for w in group)
    checks={'blocked_final_both_sites_localized':len(blocked)==3 and all_both(blocked),'interleaved_final_both_sites_localized':len(inter)==3 and all_both(inter),'interleaved_midpoint_partial_exposure':all(w['checkpoints'][0]['exposures_per_site']==[2000,2000] for w in inter),'blocked_midpoint_first_only':all(w['checkpoints'][0]['exposures_per_site']==[4000,0] for w in blocked),'all_final_exposures_equal':all(w['checkpoints'][-1]['exposures_per_site']==[4000,4000] for w in workers),'source_lock_stable':data['locked_inputs']==lock['locked_inputs']==data['post_run_inputs'],'runner_gates_pass':data['passed'] and all(data['checks'].values()),'analyzer_source_stable':analyzer_before==sha(ANALYZER)}
    result={'schema':'VisionEyeInterleavedRetentionV1Analysis','analyzer_sha256':analyzer_before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'workers':workers,'blocked_both_localized':sum(all(v['localized'] for v in w['checkpoints'][-1]['location_scores'].values()) for w in blocked),'interleaved_both_localized':sum(all(v['localized'] for v in w['checkpoints'][-1]['location_scores'].values()) for w in inter),'median_closure_ms':{m:statistics.median(w['closure_mean_ns']/1e6 for w in workers if w['mode']==m) for m in ('blocked','interleaved')},'median_input_update_ms_per_step':{m:statistics.median(w['input_update_ns']/1e6/8000 for w in workers if w['mode']==m) for m in ('blocked','interleaved')},'checks':checks,'passed':all(checks.values()),'claim_limit':data['claim_limit']}
    ANALYSIS.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'blocked_both_localized':result['blocked_both_localized'],'interleaved_both_localized':result['interleaved_both_localized'],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
