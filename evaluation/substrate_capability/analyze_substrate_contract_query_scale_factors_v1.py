#!/usr/bin/env python3
"""Independent formula, query, and native-work verification for factor sweep."""
import json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_contract_query_scale_factors_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_scale_factors_v1_lock_20261001.json'
OUT=ROOT/'evaluation/reports/substrate_contract_query_scale_factors_v1_analysis_20261001.json'
def value(i,k,x):
 for bit,point in enumerate(range(-k,0)):
  if x==point:return 10*((i>>bit)&1)
 return x
def entropy(vals):
 counts={}
 for v in vals:
  z=(type(v).__name__,repr(v));counts[z]=counts.get(z,0)+1
 n=len(vals);return -sum((c/n)*math.log2(c/n) for c in counts.values())
def consistent(ids,k,obs):return [i for i in ids if all(value(i,k,o['inputs']['x'])==o['expected'] for o in obs)]
def calls_for(ids,k,obs,grid):
 ss=list(ids);n=0
 for row in obs:
  n+=len(ss);x=row['inputs']['x'];y=row['expected'];ss=[i for i in ss if value(i,k,x)==y]
 if len(ss)<2:return n
 return n+len(ss)*sum(not any(o['inputs']['x']==q['x'] for o in obs) for q in grid)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ws=raw['workers'];assert raw['lock']==raw['post_lock']==lock
 d=lock['design'];cells={c['cell']:c for c in d['cells']};reps=d['repetitions']
 assert len(ws)==len(cells)*reps and all(w.get('kind')=='worker' for w in ws) and len({w['pid'] for w in ws})==len(ws)
 assert all(w['source_stable'] and w['before']==w['after']==lock['active'] for w in ws)
 assert {(w['cell'],w['rep']) for w in ws}=={(c,r) for c in cells for r in range(1,reps+1)}
 rows=[]
 for w in ws:
  c=cells[w['cell']];h=c['H'];k=c['K'];depth=k+c['D'];grid=c['candidate_inputs'];target=int(c['target_id'][1:]);ids=list(range(h));obs=list(c['initial_observations'])
  assert (w['H'],w['K'],w['D'],w['N'])==(h,k,c['D'],c['N']) and w['target_id_for_analysis_only']==c['target_id']
  assert len(w['history'])==k and len(grid)==c['N']
  expected_calls=0;selected=[]
  for row in w['history']:
   survivors=consistent(ids,k,obs);assert row['survivors_before']==[f'h{i}' for i in survivors]
   x=row['query']['x'];selected.append(x);assert x in [q['x'] for q in grid] and all(o['inputs']['x']!=x for o in obs)
   pred={p['hypothesis']:p['output'] for p in row['predictions']};assert pred=={f'h{i}':value(i,k,x) for i in survivors}
   scores=[]
   for q in grid:
    if any(o['inputs']['x']==q['x'] for o in obs):continue
    scores.append((entropy([value(i,k,q['x']) for i in survivors]),q['x']))
   best=max(s for s,_ in scores);first=max((s,-x0) for s,x0 in scores)
   assert abs(row['entropy_bits']-best)<1e-12 and (row['entropy_bits'],-x)==first
   label=value(target,k,x);assert row['oracle_output']==label
   expected_calls+=calls_for(ids,k,obs,grid);obs.append({'inputs':{'x':x},'expected':label})
  assert selected==list(range(-k,0)) and consistent(ids,k,obs)==[target]
  assert not w['terminal'].get('ok') and w['terminal'].get('surviving_hypotheses')==[f'h{target}']
  expected_calls+=calls_for(ids,k,obs,grid);assert w['native_evaluation_calls']==expected_calls
  rows.append({'cell':w['cell'],'rep':w['rep'],'H':h,'K':k,'D':c['D'],'N':c['N'],'depth':depth,
   'native_evaluation_calls':expected_calls,'elapsed_ms':w['selection_elapsed_ns']/1e6,
   'ns_per_native_eval':w['selection_elapsed_ns']/expected_calls})
 def summary(names):
  selected=[r for r in rows if r['cell'] in names]
  return {'cells':names,'median_ms':statistics.median(r['elapsed_ms'] for r in selected),
   'median_native_evaluation_calls':statistics.median(r['native_evaluation_calls'] for r in selected),
   'median_ns_per_native_eval':statistics.median(r['ns_per_native_eval'] for r in selected)}
 factors={'hypothesis_count':[summary(['baseline']),summary(['h256']),summary(['h512'])],
  'neutral_expression_depth':[summary(['baseline']),summary(['d16']),summary(['d64'])],
  'candidate_grid_size':[summary(['baseline']),summary(['n100']),summary(['n500'])]}
 result={'schema':'SubstrateContractQueryScaleFactorsV1Analysis','workers':len(ws),'source_lock_stable':True,
  'rows':rows,'independent_factor_summaries':factors,
  'interpretation':'Native operation counts are independently replayed from sequential survivor filtering and input scoring. Timing includes Python selector orchestration and native Term evaluation. Each axis is varied around the same baseline; the small synthetic cells do not establish asymptotic complexity.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
