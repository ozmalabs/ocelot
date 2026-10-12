#!/usr/bin/env python3
"""Independent replay analysis for coverage-aware class return v1."""
import hashlib, json, statistics, sys, itertools
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'runners/dsl/python'))
LOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
OUT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
RUNNER=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
KEYS=('ax','ay','ex','ey')
def env(row): return dict(zip(KEYS,map(float,row)))
def truth(task,row):
 a,b,c,d=row
 return {'additive':lambda:a+b==c+d,'product':lambda:a*b==c*d,
         'ordering':lambda:a<c,'opposition':lambda:a==-c,
         'inequality':lambda:a!=c}[task]()
def main():
 lock=json.loads(LOCK.read_text()); raw=json.loads(RAW.read_text()); errors=[]
 if raw.get('lock_sha256')!=sha(LOCK): errors.append('capture lock hash mismatch')
 if raw.get('sources')!=lock.get('sources'): errors.append('capture source map mismatch')
 if len(raw.get('workers',[]))!=len(lock.get('panels',[])): errors.append('worker count mismatch')
 panels={(p['task'],p['worker']):p for p in lock['panels']}
 summary={d:{'panels':0,'decisions':{},'expansions':0,'labels':[],'exact_class_returns':0,'false_class_returns':0,'help_calls':0} for d in ('all',)}['all']
 rows=[]
 from substrate_rs import _native
 native=_native.Substrate()
 for w in raw.get('workers',[]):
  key=(w.get('task'),w.get('worker')); p=panels.get(key); r=w.get('result',{})
  if p is None: errors.append(f'unlocked worker {key}'); continue
  if w.get('training')!=p.get('training'): errors.append(f'training mismatch {key}')
  initial={h['id']:h for h in p['initial_hypotheses']}; alive=dict(initial)
  for step in r.get('steps',[]):
   row=tuple(map(float,step.get('row',[]))); label=truth(key[0],row)
   if step.get('label') is not label: errors.append(f'oracle label mismatch {key}')
   for hid,h in list(alive.items()):
    try: pred=native.evaluate(h['term'],env(row))
    except Exception: pred=None
    if type(pred) is not bool or pred is not label: alive.pop(hid)
  reported={h.get('id'):h for h in r.get('survivors',[])}
  if set(alive)!=set(reported): errors.append(f'survivor replay mismatch {key}')
  if r.get('calls')!=len(r.get('steps',[])): errors.append(f'call count mismatch {key}')
  for step in r.get('steps',[]):
   if step.get('after',0)>step.get('before',0): errors.append(f'nonmonotone survivor count {key}')
  decision=r.get('decision','missing');summary['panels']+=1
  summary['decisions'][decision]=summary['decisions'].get(decision,0)+1
  summary['expansions']+=len(r.get('expansions',[]));summary['labels'].append(r.get('calls',0))
  survivors=r.get('survivors',[])
  current=(p['original_selection_pool']+p['original_challenge_order'] if r.get('domain')=='original'
           else p['original_selection_pool']+p['original_challenge_order']+p['zero_selection_pool']+p['zero_challenge_pool'])
  probes=list(dict.fromkeys(tuple(map(float,x)) for x in current))
  signatures=[]
  for h in survivors:
   try: signatures.append(tuple((type(v).__name__,v) for v in (native.evaluate(h['term'],env(row)) for row in probes)))
   except Exception: signatures.append(('evaluation_error',h['id']))
  if decision=='behavior_class' and (len(set(signatures))!=1 or not r.get('coverage',{}).get('adequate')):
   errors.append(f'independent behavior class mismatch {key}')
  vals=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5)
  holdout=[x for x in itertools.product(vals,repeat=4) if x!=(0.,0.,0.,0.)]
  exact_by_id={}
  for h in survivors:
   bad=False
   for row in holdout:
    try: v=native.evaluate(h['term'],env(row))
    except Exception: bad=True; break
    if type(v) is not bool or v is not truth(key[0],row): bad=True; break
   exact_by_id[h['id']]=not bad
   if reported.get(h['id'],{}).get('heldout',{}).get('exact')!=(not bad):
    errors.append(f'independent heldout mismatch {key}:{h["id"]}')
  exact=bool(survivors) and all(exact_by_id.values())
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
