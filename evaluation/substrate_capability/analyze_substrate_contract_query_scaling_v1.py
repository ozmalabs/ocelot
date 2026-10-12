#!/usr/bin/env python3
"""Independent closed-form analysis for query scaling and open-world trials."""
import json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_contract_query_scaling_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_scaling_v1_lock_20261001.json'
PRELOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_scaling_v1_lock_20261001_pre_analysis_correction.json'
OUT=ROOT/'evaluation/reports/substrate_contract_query_scaling_v1_analysis_20261001.json'
REPS=2;RANDOM_TRIALS=2000;SEED=20261031
def value(index,k,x):
 for b,p in enumerate(range(-k,0)):
  if x==p:return 10*((index>>b)&1)
 return x
def entropy(vals):
 counts={}
 for v in vals:
  key=(type(v).__name__,repr(v));counts[key]=counts.get(key,0)+1
 n=len(vals);return -sum((c/n)*math.log2(c/n) for c in counts.values())
def survivors(ids,k,obs):return [i for i in ids if all(value(i,k,o['inputs']['x'])==o['expected'] for o in obs)]
def selector_eval_calls(ids,k,obs,grid):
 ss=list(ids);calls=0
 for row in obs:
  before=len(ss);calls+=before;x=row['inputs']['x'];y=row['expected']
  ss=[i for i in ss if value(i,k,x)==y]
 if len(ss)<2:return calls
 unused=sum(not any(row['inputs']['x']==q for row in obs) for q in grid)
 return calls+len(ss)*unused
def random_counts(h,k,target,grid,initial,case_index,rep):
 rng=random.Random(SEED+case_index*1009+rep*79);counts=[]
 for _ in range(RANDOM_TRIALS):
  ss=list(range(h));obs=list(initial);order=list(grid);rng.shuffle(order);n=0
  for x in order:
   if any(o['inputs']['x']==x for o in obs):continue
   y=value(target,k,x);obs.append({'inputs':{'x':x},'expected':y});n+=1
   ss=[i for i in ss if value(i,k,x)==y]
   if len(ss)<=1:break
  counts.append(n)
 return counts
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());prelock=json.loads(PRELOCK.read_text());ws=raw['workers']
 assert raw['lock']==raw['post_lock']==prelock
 assert lock['active']==prelock['active'] and lock['design']==prelock['design']
 assert {k:v for k,v in lock['files'].items() if not k.endswith('analyze_substrate_contract_query_scaling_v1.py')} == {k:v for k,v in prelock['files'].items() if not k.endswith('analyze_substrate_contract_query_scaling_v1.py')}
 assert len(ws)==10 and all(w.get('kind')=='worker' for w in ws) and len({w['pid'] for w in ws})==10
 assert all(w['source_stable'] and w['before']==w['after']==lock['active'] for w in ws)
 d=lock['design'];cases={c['case']:c for c in d['cases']};expected={(name,r) for name,_ in [(c['case'],c['target_id']) for c in d['cases']] for r in range(1,REPS+1)}
 assert {(w['case'],w['rep']) for w in ws}==expected
 scale_rows=[];open_alias=[];open_conflict=[]
 for w in ws:
  c=cases[w['case']];h=len(c['hypotheses']);k=c['K'];target=int(c['target_id'][1:]);ids=list(range(h));grid=[p['x'] for p in c['candidate_inputs']]
  assert w['hypothesis_count']==h and w['term_depth']==k and w['input_count']==4*k
  assert w['target_id_for_analysis_only']==c['target_id']
  obs=list(w['initial_observations']);history=w['history'];alias=c.get('alias_decoy')
  if w['case'].startswith('open_conflict'):
   assert history==[] and w['terminal'].get('ok') is False and w['terminal'].get('surviving_hypotheses')==[]
   assert w['native_evaluation_calls']==h*len(obs)
   open_conflict.append(w);continue
  expected_rounds=k;assert len(history)==expected_rounds
  calls=0;selected=[]
  for row in history:
   ss=survivors(ids,k,obs);assert [f'h{i}' for i in ss]==row['survivors_before']
   x=row['query']['x'];selected.append(x);assert x in grid and all(o['inputs']['x']!=x for o in obs)
   predictions={r['hypothesis']:r['output'] for r in row['predictions']}
   assert predictions=={f'h{i}':value(i,k,x) for i in ss}
   scores=[]
   for q in grid:
    if any(o['inputs']['x']==q for o in obs):continue
    scores.append((entropy([value(i,k,q) for i in ss]),q))
   best=max(s for s,_ in scores);tie=max((s,-q) for s,q in scores)
   assert abs(row['entropy_bits']-best)<1e-12 and (row['entropy_bits'],-x)==tie
   label=value(target,k,x);assert row['oracle_output']==label
   obs.append({'inputs':{'x':x},'expected':label})
   calls += selector_eval_calls(ids,k,obs[:-1],grid)
  assert len(set(selected))==k
  assert w['terminal'].get('ok') is False and w['terminal'].get('surviving_hypotheses')==[f'h{target}']
  calls += selector_eval_calls(ids,k,obs,grid)
  assert calls==w['native_evaluation_calls']
  if w['case'].startswith('scale_'):
   rc=random_counts(h,k,target,grid,c['initial_observations'],[cc['case'] for cc in d['cases']].index(w['case']),w['rep'])
   assert w['random_query_counts']==rc and max(rc)<=len(grid)
   scale_rows.append({'case':w['case'],'rep':w['rep'],'H':h,'K':k,'N_inputs':len(grid),'selected_queries':len(history),
    'median_random_queries':statistics.median(rc),'mean_random_queries':statistics.mean(rc),'native_eval_calls':calls,'elapsed_ms':w['selection_elapsed_ns']/1e6})
  else:
   assert alias is not None and w['terminal'].get('surviving_hypotheses')==[f'h{target}']
   held=w['heldout'];assert held['input']['x']==alias and held['candidate_id']==f'h{target}'
   assert held['candidate_output']==value(target,k,alias) and held['oracle_output']==held['candidate_output']+100
   open_alias.append({'rep':w['rep'],'selected_queries':len(history),'singleton_candidate':held['candidate_id'],
    'heldout_candidate_output':held['candidate_output'],'heldout_oracle_output':held['oracle_output']})
 # An unqueried unanimous input is where the out-of-set target diverges; selector cannot distinguish it.
 by_h={}
 for h in (8,32,128):
  rows=[r for r in scale_rows if r['H']==h]
  by_h[str(h)]={'K':int(math.log2(h)),'input_count':4*int(math.log2(h)),
   'median_native_eval_calls':statistics.median(r['native_eval_calls'] for r in rows),
   'median_elapsed_ms':statistics.median(r['elapsed_ms'] for r in rows),
   'median_random_queries':statistics.median(r['median_random_queries'] for r in rows),
   'selector_queries':sum(r['selected_queries'] for r in rows)}
 result={'schema':'SubstrateContractQueryScalingV1Analysis','workers':10,'source_lock_stable':True,
  'scaling_by_hypothesis_count':by_h,'observational_alias_workers':len(open_alias),'observational_alias_false_singleton_count':sum(r['heldout_candidate_output']!=r['heldout_oracle_output'] for r in open_alias),
  'observational_alias':open_alias,'direct_contradiction_workers':len(open_conflict),'direct_contradiction_empty_set_refusals':sum(not w['terminal'].get('surviving_hypotheses') for w in open_conflict),
  'claim_boundary':'The finite selector scales over supplied binary-coded Term hypotheses and admits an open-world blind spot: a singleton means unique within the candidate set and queried observations, not globally correct. The target and labels are harness-owned.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
