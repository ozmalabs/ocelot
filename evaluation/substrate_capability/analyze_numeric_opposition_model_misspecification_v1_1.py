#!/usr/bin/env python3
"""Independent exact holdout and query-transition audit."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/numeric_opposition_model_misspecification_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_model_misspecification_v1_1_analysis_20261003.json'
sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import numeric_opposition_model_misspecification_v1_1 as runner
from substrate_rs import _native
lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());workers=raw['workers'];native=_native.Substrate()
assert runner.source_map()==lock['sources']==raw['sources']
assert raw['lock_sha256']==runner.sha(LOCK)
def exact_score(term):
 tp=fp=fn=tn=invalid=0
 for row in __import__('itertools').product(runner.HELDOUT_VALUES,repeat=4):
  try:pred=native.evaluate(term,runner.env(row))
  except Exception:invalid+=1;continue
  actual=bool(runner.truth(row))
  if type(pred) is not bool:invalid+=1;continue
  if pred and actual:tp+=1
  elif pred:fp+=1
  elif actual:fn+=1
  else:tn+=1
 return {'n':1296,'typed':invalid==0,'invalid_type_count':invalid,
  'exact':fp==0 and fn==0 and invalid==0,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
shape_ok=len(workers)==5 and len({w['worker'] for w in workers})==5
coverage_ok=True;transition_ok=True;rescore_ok=True;opaque_query_equality=True
for w in workers:
 panel=lock['panels'][w['worker']]
 coverage_ok &= (len(w['training'])==4 and len(w['query_pool'])==32
  and set(map(tuple,w['query_pool'])).isdisjoint({tuple(x['row']) for x in w['training']}))
 coverage_ok &= sorted(map(tuple,w['paired_random_order']))==sorted(map(tuple,w['query_pool']))
 exact_initial=[]
 for h in w['hypotheses']:
  sc=exact_score(h['term']);rescore_ok &= sc=={k:h['heldout'][k] for k in sc};exact_initial.append(sc['exact'])
 rescore_ok &= not any(exact_initial)
 arms={a['policy']:a for a in w['arms']}
 opaque_query_equality &= (set(arms)=={'max_entropy','paired_sequential'}
  and all(a['query_order']==panel['paired_random_order'] for a in arms.values()))
 for a in arms.values():
  survivors={h['id']:h['term'] for h in w['hypotheses']}
  for step in a['steps']:
   transition_ok &= step['before']==len(survivors)
   transition_ok &= isinstance(step.get('input_env'),dict) and set(step['input_env'])==set(runner.KEYS)
   transition_ok &= tuple(step['query'])==tuple(step['input_env'][k] for k in runner.KEYS)
   actual=bool(runner.truth(step['query']))
   for pred in step['predictions']:
    h=survivors.get(pred['hypothesis'])
    if h is None:transition_ok=False;continue
    try:actual_pred=native.evaluate(h,runner.env(step['query']))
    except Exception:
     transition_ok &= pred.get('evaluation_error') is True and pred.get('output') is None
     continue
    transition_ok &= not pred.get('evaluation_error') and type(pred['output']) is type(actual_pred) and pred['output']==actual_pred
   kept={}
   for hid,term in survivors.items():
    try:value=native.evaluate(term,runner.env(step['query']))
    except Exception:continue
    if type(value) is bool and value==actual:kept[hid]=term
   survivors=kept
   transition_ok &= step['after']==len(survivors)
  transition_ok &= a['oracle_calls']==len(a['steps']) and len(survivors)==len(a['survivors'])
  for h in a['survivors']:rescore_ok &= h['heldout']==exact_score(h['term'])
checks={'five_frozen_panels_and_disjoint_coverage':bool(shape_ok and coverage_ok),
 'query_policies_replay_on_frozen_pools':bool(opaque_query_equality and transition_ok),
 'partial_term_error_bucket_and_elimination':all(all(w['selector_error_control'].values()) for w in workers),
 'all_initial_and_final_terms_rescored_exactly':bool(rescore_ok),
 'source_lock_and_capture_binding':runner.source_map()==raw['sources']==lock['sources'] and raw['lock_sha256']==runner.sha(LOCK)}
false_singletons=[];survivors_total=0;empty_stops=0;calls=[]
for w in workers:
 for a in w['arms']:
  calls.append(a['oracle_calls']);survivors_total+=len(a['survivors'])
  if a['stop']=='empty_version_space':empty_stops+=1
  if a['stop']=='singleton' and len(a['survivors'])==1 and not a['survivors'][0]['heldout']['exact']:
   false_singletons.append({'worker':w['worker'],'policy':a['policy'],'hypothesis':a['survivors'][0]['id']})
analysis={'schema':'NumericOppositionModelMisspecificationV1Analysis','checks':checks,
 'passed':sum(checks.values()),'total':len(checks),'false_confidence_singletons':false_singletons,
 'empty_version_space_stops':empty_stops,'total_final_survivors':survivors_total,
 'median_oracle_calls':__import__('statistics').median(calls),
 'interpretation':'An empty version space or unresolved aliased set can expose inadequate grammar, but a unique training/query survivor may still be false on disjoint holdouts.',
 'limits':['one additive target relation, absent from Neg/Eq/And','five repeated deterministic panels','simulated local oracle; query-call counts are not real oracle economics']}
OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n')
print(json.dumps(analysis,indent=2,sort_keys=True))
if not all(checks.values()):raise SystemExit(1)
