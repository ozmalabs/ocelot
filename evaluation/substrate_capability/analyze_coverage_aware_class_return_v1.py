#!/usr/bin/env python3
"""Independent integrity and outcome analysis for coverage-aware class return v1."""
import hashlib, json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
OUT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_analysis_20261004.json'
RUNNER=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text()); raw=json.loads(RAW.read_text()); errors=[]
 if raw.get('lock_sha256')!=sha(LOCK): errors.append('capture lock hash mismatch')
 if raw.get('sources')!=lock.get('sources'): errors.append('capture source map mismatch')
 if len(raw.get('workers',[]))!=len(lock.get('panels',[])): errors.append('worker count mismatch')
 panels={(p['task'],p['worker']):p for p in lock['panels']}
 summary={d:{'panels':0,'decisions':{},'expansions':0,'labels':[],'exact_class_returns':0,'false_class_returns':0,'help_calls':0} for d in ('all',)}['all']
 rows=[]
 for w in raw.get('workers',[]):
  key=(w.get('task'),w.get('worker')); p=panels.get(key); r=w.get('result',{})
  if p is None: errors.append(f'unlocked worker {key}'); continue
  if w.get('training')!=p.get('training'): errors.append(f'training mismatch {key}')
  if r.get('calls')!=len(r.get('steps',[])): errors.append(f'call count mismatch {key}')
  for step in r.get('steps',[]):
   if step.get('after',0)>step.get('before',0): errors.append(f'nonmonotone survivor count {key}')
  decision=r.get('decision','missing');summary['panels']+=1
  summary['decisions'][decision]=summary['decisions'].get(decision,0)+1
  summary['expansions']+=len(r.get('expansions',[]));summary['labels'].append(r.get('calls',0))
  survivors=r.get('survivors',[])
  exact=bool(survivors) and all(x.get('heldout',{}).get('exact') for x in survivors)
  if decision=='behavior_class': summary['exact_class_returns' if exact else 'false_class_returns']+=1
  summary['help_calls']+=int(decision=='teacher_help')
  part=r.get('behavior_partition') or {}
  if decision=='behavior_class' and (part.get('class_count')!=1 or not r.get('coverage',{}).get('adequate')):
   errors.append(f'unjustified class return {key}')
  if decision=='teacher_help' and not r.get('teacher'): errors.append(f'missing teacher result {key}')
  rows.append({'task':key[0],'worker':key[1],'decision':decision,'labels':r.get('calls',0),'expansions':len(r.get('expansions',[])),'coverage_adequate':r.get('coverage',{}).get('adequate'),'survivors':len(survivors),'all_survivors_exact':exact,'help':decision=='teacher_help'})
 summary['median_labels']=statistics.median(summary.pop('labels')) if rows else None
 passed=not errors and summary['panels']==25
 result={'schema':'CoverageAwareClassReturnV1Analysis','passed':passed,'errors':errors,'capture_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'summary':summary,'rows':rows,'limits':['authored numeric task families','frozen finite probe and holdout domains','single host','does not measure persistent adoption or natural task performance']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'passed':passed,'errors':errors,'summary':summary,'analysis':str(OUT.relative_to(ROOT))},sort_keys=True))
 return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
