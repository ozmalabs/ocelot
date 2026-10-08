#!/usr/bin/env python3
"""Independent integrity and held-out scoring for numeric active-query v1."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_active_query_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/numeric_opposition_active_query_v1_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_active_query_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return r[0]==-r[2] and r[1]==-r[3]
def observed_equal(a,b):return type(a) is type(b) and a==b
def prediction_token(value):return (type(value).__module__,type(value).__qualname__,repr(value))
ACTION_VECTOR={'Up':(-1.,0.),'Down':(1.,0.),'Left':(0.,-1.),'Right':(0.,1.),'Stay':(0.,0.)}
def target_ast():return {'type':'And','items':[{'type':'Eq','a':{'type':'Var','name':'ax'},'b':{'type':'Neg','arg':{'type':'Var','name':'ex'}}},{'type':'Eq','a':{'type':'Var','name':'ay'},'b':{'type':'Neg','arg':{'type':'Var','name':'ey'}}}]}
def main():
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 from evaluation.substrate_capability.measure_numeric_opposition_active_query_v1 import source_map
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errors=[];native=_native.Substrate();grid=list(itertools.product(lock['heldout_values'],repeat=4));worker_out=[]
 if source_map()!=lock['sources']:errors.append('current source/build map differs from pre-run lock')
 if cap.get('lock_sha256')!=sha(LOCK):errors.append('lock digest mismatch')
 if cap.get('sources')!=lock.get('sources'):errors.append('capture source map mismatch')
 if len(cap.get('workers',[]))!=5:errors.append('worker count mismatch')
 for wr in cap.get('workers',[]):
  i=wr['worker'];panel=lock['panels'][i]
  if wr.get('training')!=panel['training'] or wr.get('query_pool')!=panel['query_pool'] or wr.get('random_order')!=panel['random_order']:errors.append(f'worker {i}: locked inputs changed')
  hyps=wr.get('hypotheses',[])
  if len({h['id'] for h in hyps})!=len(hyps):errors.append(f'worker {i}: duplicate hypothesis ids')
  target=target_ast()
  if wr.get('target_term')!=target or wr.get('target_present')!=any(h['term']==target for h in hyps):errors.append(f'worker {i}: exact target support mismatch')
  for ex in panel['training']:
   if ex['label']!=int(truth(ex['row'])):errors.append(f'worker {i}: malformed training labels')
  arm_summaries=[]
  for arm in wr.get('arms',[]):
   policy=arm['policy'];survivors=list(hyps);observations=[];used=[]
   order=panel['query_pool'] if policy!='seeded_random' else panel['random_order']
   for t,step in enumerate(arm.get('steps',[])):
    if len(survivors)<2:errors.append(f'worker {i}/{policy}: queried after singleton');break
    available=[env(r) for r in order if r not in used]
    if policy=='max_entropy':
     expected=select_discriminating_input(lambda term,e:native.evaluate(term,e),survivors,available,observations)
     if not expected.get('ok') or expected.get('query')!=env(step['query']):errors.append(f'worker {i}/{policy}: query not max entropy')
    else:
     if not available or env(step['query'])!=available[0]:errors.append(f'worker {i}/{policy}: query order violation')
    q=step['query'];label=truth(q)
    if bool(step['label'])!=label:errors.append(f'worker {i}/{policy}: oracle label mismatch')
    preds=[{'hypothesis':h['id'],'output':native.evaluate(h['term'],env(q))} for h in survivors]
    if step.get('predictions')!=preds:errors.append(f'worker {i}/{policy}: prediction partition mismatch')
    if step.get('before')!=len(survivors):errors.append(f'worker {i}/{policy}: pre-count mismatch')
    used.append(q);observations.append({'inputs':env(q),'expected':label})
    survivors=[h for h in survivors if observed_equal(native.evaluate(h['term'],env(q)),label)]
    if step.get('after')!=len(survivors):errors.append(f'worker {i}/{policy}: survivor count mismatch')
   if len(used)>lock['call_budget'] or len(used)!=len(set(tuple(r) for r in used)):errors.append(f'worker {i}/{policy}: query budget/uniqueness violation')
   ids=[h['id'] for h in survivors]
   if ids!=arm.get('survivor_ids'):errors.append(f'worker {i}/{policy}: final survivors mismatch')
   if arm.get('oracle_calls')!=len(used):errors.append(f'worker {i}/{policy}: oracle call count mismatch')
   if len(survivors)>1 and len(used)<lock['call_budget']:
    available=[env(r) for r in order if r not in used]
    if policy=='max_entropy':
     can_continue=select_discriminating_input(lambda term,e:native.evaluate(term,e),survivors,available,observations).get('ok',False)
    else:
     can_continue=any(len({prediction_token(native.evaluate(h['term'],env(r))) for h in survivors})>1 for r in order if r not in used)
    if can_continue:errors.append(f'worker {i}/{policy}: stopped before singleton, agreement, or budget')
   fp=fn=tp=tn=0
   for r in grid:
    y=truth(r)
    for h in survivors:
     pred=bool(native.evaluate(h['term'],env(r)))
     if y and pred:tp+=1
     elif y:fn+=1
     elif pred:fp+=1
     else:tn+=1
   score={'survivors':len(survivors),'scored_hypothesis_cases':len(grid)*len(survivors),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'all_exact':bool(survivors) and fp==0 and fn==0}
   nav_rows=[]
   for h in survivors:
    for task in lock['navigation_tasks']:
     av=ACTION_VECTOR.get(task['actual']);ev=ACTION_VECTOR.get(task['expected']) if task['expected'] is not None else None
     relation=None if av is None or ev is None else bool(native.evaluate(h['term'],{'ax':av[0],'ay':av[1],'ex':ev[0],'ey':ev[1]}))
     proposal=bool(relation and task['kind']!='absent_target')
     nav_rows.append({'hypothesis':h['id'],'task_id':task['id'],'relation':relation,'proposal':proposal,'expected_proposal':task['kind']=='opposite'})
   reported=[{'hypothesis':hrow['hypothesis'],**x} for hrow in arm.get('navigation_transfer',[]) for x in hrow['tasks']]
   if nav_rows!=reported:errors.append(f'worker {i}/{policy}: navigation transfer scoring mismatch')
   score['navigation_cases_per_hypothesis']=len(lock['navigation_tasks']);score['navigation_proposal_correct']=sum(x['proposal']==x['expected_proposal'] for x in nav_rows);score['navigation_proposal_cases']=len(nav_rows)
   arm_summaries.append({'policy':policy,'calls':len(used),'remaining':len(survivors),'score':score})
  worker_out.append({'worker':i,'version_hypotheses':len(hyps),'version_halt_reason':wr.get('version_halt_reason'),'target_present':wr.get('target_present'),'arms':arm_summaries})
 summaries={p:[a for w in cap.get('workers',[]) for a in w['arms'] if a['policy']==p] for p in ('max_entropy','fixed_first','seeded_random')}
 result={'schema':'NumericOppositionActiveQueryV1Analysis','measurement_integrity_pass':not errors,'errors':errors,'workers':worker_out,
  'summary':{'workers':len(worker_out),'median_version_hypotheses':statistics.median([w['version_hypotheses'] for w in worker_out]) if worker_out else None,
   'target_present_workers':sum(bool(w['target_present']) for w in worker_out),'median_calls':{k:statistics.median([a['oracle_calls'] for a in v]) if v else None for k,v in summaries.items()},
   'median_selector_ms':{k:statistics.median([a['selector_ns'] for a in v])/1e6 if v else None for k,v in summaries.items()},
   'median_policy_wall_ms':{k:statistics.median([a['arm_wall_ns'] for a in v])/1e6 if v else None for k,v in summaries.items()},
   'median_synthesis_wall_ms':statistics.median([w['version_wall_ns'] for w in cap.get('workers',[])])/1e6 if cap.get('workers') else None,
   'median_synthesis_cpu_ms':statistics.median([w['version_cpu_ns'] for w in cap.get('workers',[])])/1e6 if cap.get('workers') else None,
   'exact_final_identification':{p:sum(1 for w in worker_out for a in w['arms'] if a['policy']==p and a['score']['all_exact']) for p in summaries}},
  'interpretation':'Finite, bounded version-space selection only. Hypothesis grammar, pool, numeric relation, and oracle are specified by the harness; this does not establish autonomous hypothesis or task discovery.',
  'input_hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
