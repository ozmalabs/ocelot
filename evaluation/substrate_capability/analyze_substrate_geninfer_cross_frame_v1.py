#!/usr/bin/env python3
"""Analyze paired scoped/global GenInfer dependency cases."""
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_cross_frame_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_geninfer_cross_frame_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_cross_frame_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def median(xs):return sorted(xs)[len(xs)//2]
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data.get('cases',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture/lock hash mismatch')
 if data.get('source_manifest')!=lock.get('sources'):errors.append('source manifest mismatch')
 expected={r['id']:r for r in lock['cases']};actual={r.get('case',{}).get('id'):r for r in rows}
 if len(rows)!=36 or len(actual)!=36 or set(actual)!=set(expected):errors.append('case matrix mismatch')
 if len({r.get('pid') for r in rows})!=36:errors.append('worker process isolation failed')
 by_condition={}
 for cond in lock['conditions']:
  cell=[r for r in rows if r['case']['condition']==cond];global_ns=[];scoped_ns=[];expected_frame=1 if cond!='local_basis' else 0
  acquired={'global':0,'scoped':0};receipt_ok={'global':0,'scoped':0};counts={'global':[],'scoped':[]}
  for r in cell:
   if not r.get('source_stable'):errors.append(r['case']['id']+': source drift')
   if len(r.get('arms',[]))!=2:errors.append(r['case']['id']+': arm count')
   for arm in r.get('arms',[]):
    mode='scoped' if arm.get('scoped') else 'global';counts[mode].append(arm.get('checked'))
    target=bool(arm.get('target_generator_present'));acquired[mode]+=target
    receipt_ok[mode]+=int(arm.get('expected_base') in arm.get('receipt_bases',[]))
    if not arm.get('oracle_exact'):errors.append(r['case']['id']+': oracle mismatch')
    want=r['case']['k']*2400 if mode=='global' else 2400
    if arm.get('checked')!=want:errors.append(r['case']['id']+f': {mode} candidate formula')
    if mode=='global':global_ns.append(arm['closure_wall_ns'])
    else:scoped_ns.append(arm['closure_wall_ns'])
    should=(cond!='cross_frame_excluded')
    if mode=='global' and not target:errors.append(r['case']['id']+': global missed available basis')
    if mode=='scoped' and target!=should:errors.append(r['case']['id']+': scoped acquisition disagrees with boundary oracle')
    if target and arm.get('expected_base') not in arm.get('receipt_bases',[]):errors.append(r['case']['id']+': target base absent from receipt')
  by_condition[cond]={'cases':len(cell),'global_acquisitions':acquired['global'],'scoped_acquisitions':acquired['scoped'],
   'global_median_wall_ms':median(global_ns)/1e6 if global_ns else None,'scoped_median_wall_ms':median(scoped_ns)/1e6 if scoped_ns else None,
   'global_candidate_checks':sorted(set(counts['global'])),'scoped_candidate_checks':sorted(set(counts['scoped']))}
 report={'schema':'GenInferCrossFrameV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'summary':{'cases':len(rows),'by_condition':by_condition}}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':not errors,'errors':len(errors),'summary':report['summary']},sort_keys=True))
 return 0 if not errors else 1
if __name__=='__main__':sys.exit(main())
