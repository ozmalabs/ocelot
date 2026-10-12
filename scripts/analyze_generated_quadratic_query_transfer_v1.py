#!/usr/bin/env python3
"""Independent replay and integrity checks for generated query transfer v1."""
from __future__ import annotations
import hashlib,json,random,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
import substrate_rs as srs
from domains.engine_provenance import engine_provenance,rust_source_fingerprint
from scripts import substrate_generated_quadratic_query_transfer_v1 as runner

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def entropy(values):
 from collections import Counter
 n=len(values); return -sum((k/n)*__import__('math').log2(k/n) for k in Counter((type(v).__name__,repr(v)) for v in values).values())
def target(task,e): return e['r']+e['r']*e['c'] if task=='first_output' else e['c']+e['r']*e['r']
def main():
 lock=json.loads(runner.LOCK.read_text()); raw=json.loads(runner.RAW.read_text()); native=srs.Substrate()._inner
 errors=[]; checks={}
 checks['raw_lock_equals_current_lock']=raw.get('lock')==lock
 checks['source_fingerprints_stable']=lock.get('engine')==runner.fingerprint() and raw.get('post_engine')==lock.get('engine')
 checks['locked_design_matches_independent_definitions']=lock.get('design')==runner.design()
 checks['exact_task_coverage']=set(raw.get('tasks',{}))==set(runner.TASKS)
 total=0; outcomes={}
 for task,fn in runner.TASKS.items():
  payload=raw.get('tasks',{}).get(task,{ }); terms=payload.get('terms',[]); gen=payload.get('generation',{})
  if len(terms)!=gen.get('pool_size'): errors.append(task+': pool size mismatch')
  # Each returned program must fit the locked training examples; target correctness is assessed separately.
  for term in terms:
   for e in runner.TRAIN:
    if native.evaluate(term,e)!=fn(e): errors.append(task+': generated term does not fit training data')
  exact=[i for i,t in enumerate(terms) if all(native.evaluate(t,e)==fn(e) for e in runner.HELDOUT)]
  if gen.get('halt_reason') not in ('max_size','solution_limit','saturated'): errors.append(task+': unexpected generator halt')
  if len(terms)<2 or not exact: errors.append(task+': insufficient pool or no exact heldout target')
  runs=payload.get('runs',[]); expected={(r,p) for r in range(1,runner.REPS+1) for p in ('entropy','fixed_first','seeded_random')}
  got={(x.get('rep'),x.get('policy')) for x in runs}
  if len(runs)!=len(expected) or got!=expected: errors.append(task+': incomplete/duplicate policy matrix')
  counts={p:[] for p in ('entropy','fixed_first','seeded_random')}; exact_unique={p:0 for p in counts}; evaluation_counts={p:[] for p in counts}
  for row in runs:
   total+=1; pol=row['policy']; counts[pol].append(row.get('oracle_calls',-1)); evaluation_counts[pol].append(row.get('prediction_evaluations',-1))
   if row.get('pool_contains_heldout_exact') != bool(exact): errors.append(task+': wrong pre-query exact-pool flag')
   if len(row.get('query_order',[]))!=len(runner.GRID) or set(map(str,row['query_order']))!=set(map(str,runner.GRID)): errors.append(task+': query order mismatch')
   expected_random=random.Random(runner.SEED+row['rep']*2027+list(runner.TASKS).index(task)*200003).sample(row['query_order'],len(row['query_order']))
   if pol=='seeded_random' and row.get('random_order')!=expected_random: errors.append(task+': random order mismatch')
   alive=list(range(len(terms))); observations=[{'inputs':e,'expected':fn(e)} for e in runner.TRAIN]; used=[o['inputs'] for o in observations]
   for step,h in enumerate(row.get('history',[])):
    remaining=[e for e in row['query_order'] if e not in used]
    if pol=='entropy':
     scores=[]
     for index,e in enumerate(remaining):
      vals=[native.evaluate(terms[i],e) for i in alive]
      scores.append((entropy(vals),-row['query_order'].index(e),e,vals))
     if not scores: errors.append(task+': active policy queried after grid exhaustion'); break
     chosen=max(scores,key=lambda z:(z[0],z[1]))[2]
    elif pol=='fixed_first': chosen=remaining[0] if remaining else None
    else: chosen=next((e for e in row['random_order'] if e not in used),None)
    if h.get('query')!=chosen: errors.append(task+f': {pol} query choice mismatch rep={row["rep"]} step={step}')
    pred={str(i):native.evaluate(terms[i],chosen) for i in alive}
    if h.get('predictions')!=pred or h.get('survivors_before')!=alive: errors.append(task+': recorded predictions/survivors mismatch')
    label=fn(chosen)
    if h.get('oracle_label')!=label: errors.append(task+': oracle label mismatch')
    alive=[i for i in alive if pred[str(i)]==label]; used.append(chosen); observations.append({'inputs':chosen,'expected':label})
   if row.get('survivors')!=alive or row.get('oracle_calls')!=len(row.get('history',[])): errors.append(task+': final survivor/call mismatch')
   is_unique=len(alive)==1 and alive[0] in exact
   if row.get('unique_survivor_is_heldout_exact')!=is_unique: errors.append(task+': exact survivor mismatch')
   if is_unique: exact_unique[pol]+=1
   if row.get('prediction_evaluations',-1)<0: errors.append(task+': invalid evaluation count')
  outcomes[task]={'pool_size':len(terms),'heldout_exact_pool_members':len(exact),'generation':gen,'policy_median_oracle_calls':{p:statistics.median(v) if v else None for p,v in counts.items()},'policy_exact_unique_survivor':exact_unique,'policy_median_prediction_evaluations':{p:statistics.median(v) if v else None for p,v in evaluation_counts.items()}}
 checks['complete_120_worker_cells']=total==120
 checks['all_terms_fit_training_and_independent_holdout_scored']=not any('training data' in e for e in errors) and all(v['heldout_exact_pool_members']>0 for v in outcomes.values())
 checks['policy_replay_and_capture_fields_valid']=not errors
 checks['all_policies_retain_exact_heldout_survivor']=all(v['policy_exact_unique_survivor'][p]==runner.REPS for v in outcomes.values() for p in ('entropy','fixed_first','seeded_random'))
 out={'run_id':runner.STEM,'checks':checks,'integrity_pass':all(checks.values()),'passed_checks':sum(checks.values()),'total_checks':len(checks),'errors':errors,'task_results':outcomes,'claim_boundary':'Two authored scalar components, fixed grammar and finite oracle. Measures integration of existing enumerative generation with native finite-grid query selection, not broad learning prevalence, autonomous grammar choice, or self-modification.'}
 runner.OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
 if not out['integrity_pass']: raise SystemExit('generated query transfer integrity failed')
if __name__=='__main__':main()
