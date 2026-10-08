#!/usr/bin/env python3
"""Independently expose any false class member hidden by finite probe support."""
import hashlib,itertools,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runners/dsl/python'))
LOCK=ROOT/'evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json'
ULOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json'
VALS=(-3.5,-2.5,-1.5,-.5,0.,.5,1.5,2.5,3.5);KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(r):return float(r[0])==-float(r[2])
def wide(seed,n):
 rng=random.Random(seed);rows=[]
 for _ in range(n):
  x=rng.uniform(-1e6,1e6);ay=rng.uniform(-1e6,1e6);ey=rng.uniform(-1e6,1e6)
  rows.append(([x,ay,-x,ey],True));e=rng.uniform(-1e6,1e6)
  if e==-x:e+=1.0
  rows.append(([x,ay,e,ey],False))
 for x in (0.,-0.,1.,-1.,.5,-.5,1e-300,-1e-300,1e300,-1e300,sys.float_info.max,-sys.float_info.max):
  rows.append(([x,0.,-x,7.],True));e=1. if x==0. else x
  if e==-x:e=-x+2.
  rows.append(([x,0.,e,-9.],False))
 return rows
def main():
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());up=json.loads(ULOCK.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture provenance mismatch')
 if lock.get('upstream_lock_sha256')!=sha(ULOCK):errors.append('upstream lock mismatch')
 for rel,want in lock.get('sources',{}).get('files',{}).items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=want:errors.append(f'source drift: {rel}')
 panels={(p['task'],p['worker']):p for p in up['panels']};native=_native.Substrate();wide_rows=wide(lock['wide_seed'],lock['balanced_pairs']);hold=[r for r in itertools.product(VALS,repeat=4) if r!=(0.,0.,0.,0.)];rows=[]
 terms={h['id']:h['term'] for h in lock['candidate_terms']}
 if len({canon(t) for t in terms.values()})!=3:errors.append('candidate terms are not structurally unique')
 for w in raw.get('workers',[]):
  key=(w.get('task'),w.get('worker'));p=panels.get(key);r=w.get('result',{})
  if p is None:errors.append(f'unlocked panel {key}');continue
  alive={h['id']:h for h in lock['candidate_terms']}
  for step in r.get('steps',[]):
   row=tuple(map(float,step.get('row',[])));label=truth(row)
   if step.get('label') is not label:errors.append(f'oracle label mismatch {key}')
   for hid,h in list(alive.items()):
    try:v=native.evaluate(h['term'],env(row))
    except Exception:v=None
    if type(v)is not bool or v is not label:alive.pop(hid)
  survivors={h['id']:h for h in r.get('survivors',[])}
  if set(alive)!=set(survivors):errors.append(f'survivor replay mismatch {key}')
  probe_rows=list(dict.fromkeys(tuple(map(float,x)) for x in (p['original_selection_pool']+p['original_challenge_order']+p['zero_selection_pool']+p['zero_challenge_pool'])))
  signatures={hid:tuple((type(v).__name__,v) for v in (native.evaluate(terms[hid],env(q)) for q in probe_rows)) for hid in survivors}
  class_agreement=len(set(signatures.values()))==1
  if not r.get('coverage',{}).get('adequate') or not class_agreement:errors.append(f'not one adequately covered class {key}')
  hold_safe={hid:all(type(native.evaluate(term,env(q))) is bool and native.evaluate(term,env(q)) is truth(q) for q in hold) for hid,term in ((i,terms[i]) for i in survivors)}
  wide_errors={}
  for hid in survivors:
   err=0
   for q,y in wide_rows:
    try:v=native.evaluate(terms[hid],env(q))
    except Exception:v=None
    if type(v)is not bool or v is not y:err+=1
   wide_errors[hid]=err
  if not all(hold_safe.values()):errors.append(f'holdout mismatch before intended boundary {key}')
  caught_false=wide_errors.get('opposition_bounded_x_lt_4',0)>0
  expected_ids={'opposition_direct','opposition_swapped_negation','opposition_bounded_x_lt_4'}
  returned=set(survivors)
  if r.get('decision')!='behavior_class' or returned!=expected_ids:errors.append(f'expected policy false-safe class not observed {key}')
  if not caught_false:errors.append(f'wider domain did not catch restricted candidate {key}')
  rows.append({'task':key[0],'worker':key[1],'decision':r.get('decision'),'labels':r.get('calls'),'expansions':len(r.get('expansions',[])),
   'covered_probe_count':len(probe_rows),'coverage_adequate':r.get('coverage',{}).get('adequate'),'class_member_ids':sorted(returned),
   'distinct_terms':len({canon(terms[i]) for i in returned}),'all_members_holdout_safe':all(hold_safe.values()),
   'wider_cases':len(wide_rows),'wider_errors_by_member':wide_errors,'false_candidate_returned': 'opposition_bounded_x_lt_4' in returned})
 if len(rows)!=5:errors.append(f'expected five panels, got {len(rows)}')
 summary={'panels':len(rows),'false_safe_class_returns':sum(r['false_candidate_returned'] and r['wider_errors_by_member'].get('opposition_bounded_x_lt_4',0)>0 for r in rows),
  'all_returns_look_safe_on_registered_holdout':all(r['all_members_holdout_safe'] for r in rows),'median_labels':sorted(r['labels'] for r in rows)[len(rows)//2] if rows else None,
  'median_wider_errors_for_restricted_candidate':sorted(r['wider_errors_by_member'].get('opposition_bounded_x_lt_4',0) for r in rows)[len(rows)//2] if rows else None,
  'wide_cases_per_panel':len(wide_rows)}
 report={'schema':'ProbeCoverageFalseEquivalentV1Analysis','passed':not errors,'errors':errors,'lock_sha256':sha(LOCK),'capture_sha256':sha(RAW),'analyzer_sha256':sha(Path(__file__)),'summary':summary,'rows':rows,
  'interpretation':"A passed analysis here means the preregistered false-safe outcome was independently reproduced. The policy's coverage condition is inadequate for this candidate because all supplied probes and the registered holdout lie below its hidden x<4 boundary."}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':not errors,'errors':errors,'summary':summary},sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
