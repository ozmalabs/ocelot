#!/usr/bin/env python3
"""Independent replay and scoring for boundary probe policy comparison v1."""
import hashlib,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=ROOT/'evaluation/substrate_capability/boundary_probe_policy_comparison_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/boundary_probe_policy_comparison_v1_lock_20261004.json'
RAW=ROOT/'evaluation/reports/boundary_probe_policy_comparison_v1_20261004.json'
OUT=ROOT/'evaluation/reports/boundary_probe_policy_comparison_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import boundary_probe_policy_comparison_v1 as m
 policy=m.loadpolicy()
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());assert raw['lock_sha256']==sha(LOCK);assert raw['sources']==lock['sources'];assert len(raw['workers'])==30
 expected=[(t,w,float(c)) for t in m.TASKS for w in range(5) for c in m.THRESHOLDS]
 assert [(x['task'],x['worker'],x['threshold']) for x in raw['workers']]==expected
 summaries={p:{'false_safe_returns':0,'exact_classes':0,'abstentions':0,'labels':0,'candidate_evaluations':0,'wide_errors':0,'wide_cases':0,'selection_ns':[]} for p in ('current','directed','fixed','abstain')}
 panels=[]
 for row,panel in zip(raw['workers'],lock['panels']):
  assert (row['task'],row['worker'],row['threshold'])==(panel['task'],panel['worker'],panel['threshold'])
  task,c=row['task'],row['threshold'];terms=panel['candidate_terms'];assert row['candidate_terms']==terms
  base=m.adapt_base(task,panel['base_panel']);support=base['original_selection_pool']+base['original_challenge_order']+base['zero_selection_pool']+base['zero_challenge_pool']
  native=_native.Substrate();
  # The fixture's held examples intentionally lie inside |ax| <= 3.
  assert max(abs(float(x[0])) for x in support)==3
  for x in support:
   vals=[native.evaluate(h['term'],policy.env(x)) for h in terms]
   assert len(set(vals))==1 and vals[0] is True
  # Independent seeded wide-domain oracle plus threshold boundary points.
  rng=random.Random(row['wider_seed']+row['worker']+int(c*1000)+(0 if task=='additive' else 100000))
  cases=[]
  for _ in range(row['wider_pairs']):
   a=rng.randint(-12,12);b=rng.randint(-12,12)
   if task=='additive':
    ey=rng.randint(-12,12);ex=a+b-ey; cases.append((a,b,ex,ey))
   else:
    if abs(b)<.2:b=1.
    ex=a;ey=b;cases.append((a,b,ex,ey))
  for x in (c-1e-6,c,c+1e-6,-c-1e-6,-c,-c+1e-6):
   cases.append(tuple(m.instantiate(task,x)[k] for k in m.KEYS))
  candidate_ok={h['id']:all(native.evaluate(h['term'],policy.env(x)) is True for x in cases) for h in terms}
  assert all(candidate_ok[h['id']] for h in terms[:2]);assert not candidate_ok[terms[2]['id']]
  arms=row['arms'];current=arms['current'];assert isinstance(current,dict)
  # Current policy's singleton/class return is explicitly exposed in its report.
  current_ids=[h['id'] for h in current.get('survivors',[])]
  current_bad=any(not candidate_ok[x] for x in current_ids)
  summaries['current']['false_safe_returns']+=int(current_bad)
  summaries['current']['wide_errors']+=sum(not candidate_ok[x] for x in current_ids)
  summaries['current']['wide_cases']+=len(cases)*len(current_ids)
  if current_ids and not current_bad:summaries['current']['exact_classes']+=1
  for name in ('directed','fixed'):
   arm=arms[name];assert arm.get('choice',{}).get('ok') is True
   q=arm['query_row'];assert tuple(q) in [tuple(m.instantiate(task,x)[k] for k in m.KEYS) for x in ((c-.5,c,c+.5) if name=='directed' else range(-16,17,2))]
   assert m.truth(task,q) is True and arm['label'] is True
   survivors=arm['survivor_ids'];assert survivors==[terms[0]['id'],terms[1]['id']]
   assert arm['candidate_evaluations']==len(terms)*(3 if name=='directed' else 17)
   assert not any(not candidate_ok[x] for x in survivors)
   summaries[name]['exact_classes']+=1;summaries[name]['labels']+=1
   summaries[name]['candidate_evaluations']+=arm['candidate_evaluations'];summaries[name]['wide_cases']+=len(cases)*len(survivors)
   summaries[name]['wide_errors']+=sum(not candidate_ok[x] for x in survivors)
   summaries[name]['selection_ns'].append(arm['selection_ns'])
  abst=arms['abstain'];assert abst['action']=='abstain' and abst['observed_abs_ax_max']==3
  summaries['abstain']['abstentions']+=1
  panels.append({'task':task,'worker':row['worker'],'threshold':c,'current_ids':current_ids,'current_false_safe':current_bad,'directed_query':arms['directed']['query_row'],'fixed_query':arms['fixed']['query_row'],'directed_survivors':arms['directed']['survivor_ids'],'fixed_survivors':arms['fixed']['survivor_ids'],'restricted_candidate_wide_errors':sum(1 for x in cases if native.evaluate(terms[2]['term'],policy.env(x)) is not True),'wide_cases':len(cases)})
 # Current policy returns the unsafe three-member equivalence class on all rows.
 assert summaries['current']['false_safe_returns']==30
 for name in ('directed','fixed'):assert summaries[name]['exact_classes']==30 and summaries[name]['wide_errors']==0
 assert summaries['abstain']['abstentions']==30
 for s in summaries.values():
  times=s.pop('selection_ns',[]);s['median_selection_ns']=sorted(times)[len(times)//2] if times else None
 result={'schema':'BoundaryProbePolicyComparisonV1Analysis','passed':True,'lock_sha256':sha(LOCK),'capture_sha256':sha(RAW),'summary':summaries,'panels':panels,'claim_boundary':'Authored arithmetic candidate policy comparison only; no general boundary extractor, autonomous candidate invention, or natural-task prevalence claim.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':True,'summary':summaries},sort_keys=True))
if __name__=='__main__':main()
