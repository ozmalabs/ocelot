#!/usr/bin/env python3
"""Independent paired semantic and cache-work analysis."""
import json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_contract_query_memoization_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_memoization_v1_lock_20261001.json'
OUT=ROOT/'evaluation/reports/substrate_contract_query_memoization_v1_analysis_20261001.json'
def val(i,k,x):
 for b,p in enumerate(range(-k,0)):
  if x==p:return 10*((i>>b)&1)
 return x
def entropy(vs):
 d={}
 for v in vs:
  q=(type(v).__name__,repr(v));d[q]=d.get(q,0)+1
 n=len(vs);return -sum((c/n)*math.log2(c/n) for c in d.values())
def survivors(ids,k,obs):return [i for i in ids if all(val(i,k,o['inputs']['x'])==o['expected'] for o in obs)]
def eval_calls(ids,k,obs,grid):
 ss=list(ids);calls=0
 for o in obs:
  calls+=len(ss);x=o['inputs']['x'];y=o['expected'];ss=[i for i in ss if val(i,k,x)==y]
 if len(ss)<2:return calls
 return calls+len(ss)*sum(not any(o['inputs']['x']==q['x'] for o in obs) for q in grid)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ws=raw['workers'];assert raw['lock']==raw['post_lock']==lock
 cells={c['cell']:c for c in lock['design']['cells']};assert len(ws)==12 and all(w.get('kind')=='worker' for w in ws) and len({w['pid'] for w in ws})==12
 assert all(w['source_stable'] and w['before']==w['after']==lock['active'] for w in ws)
 pairs={(w['cell'],w['rep']):{} for w in ws}
 for w in ws:pairs[(w['cell'],w['rep'])][w['arm']]=w
 assert all(set(p)=={'off','on'} for p in pairs.values())
 summaries=[]
 for (cell_name,rep),pair in pairs.items():
  c=cells[cell_name];h=c['H'];k=c['K'];grid=c['inputs'];target=int(c['target_id'][1:]);ids=list(range(h));off,on=pair['off'],pair['on']
  assert off['history']==on['history'] and off['terminal']==on['terminal']
  for w in (off,on):
   obs=list(c['initial']);queries=w['history'];assert len(queries)==k
   for row in queries:
    ss=survivors(ids,k,obs);assert row['survivors_before']==[f'h{i}' for i in ss]
    x=row['query']['x'];pred={p['hypothesis']:p['output'] for p in row['predictions']}
    assert pred=={f'h{i}':val(i,k,x) for i in ss}
    scores=[]
    for q in grid:
     if any(o['inputs']['x']==q['x'] for o in obs):continue
     scores.append((entropy([val(i,k,q['x']) for i in ss]),q['x']))
    best=max(s for s,_ in scores);first=max((s,-q) for s,q in scores)
    assert abs(row['entropy_bits']-best)<1e-12 and (row['entropy_bits'],-x)==first
    y=val(target,k,x);assert row['oracle_output']==y;obs.append({'inputs':row['query'],'expected':y})
   assert w['terminal']['surviving_hypotheses']==[f'h{target}']
  expected_off=0;obs=list(c['initial'])
  for row in off['history']:
   expected_off+=eval_calls(ids,k,obs,grid);obs.append({'inputs':row['query'],'expected':row['oracle_output']})
  expected_off+=eval_calls(ids,k,obs,grid)
  assert off['native_evaluation_calls']==expected_off and off['cache_entries']==0
  expected_cache=h*(len(grid)+len(c['initial']))
  assert on['native_evaluation_calls']==expected_cache and on['cache_entries']==expected_cache
  assert on['cache_serialized_bytes']>0
  for w in (off,on):
   nc=w['noncacheable_control'];assert nc['callback_calls']==4 and nc['cache_entries']==0
   assert nc['result']['ok'] and nc['result']['query']=={'x':1}
  summaries.append({'cell':cell_name,'rep':rep,'H':h,'N':len(grid),
   'uncached_evaluations':off['native_evaluation_calls'],'cached_evaluations':on['native_evaluation_calls'],
   'evaluation_reduction':off['native_evaluation_calls']/on['native_evaluation_calls'],
   'uncached_ms':off['selection_elapsed_ns']/1e6,'cached_ms':on['selection_elapsed_ns']/1e6,
   'speedup':off['selection_elapsed_ns']/on['selection_elapsed_ns'],
   'cache_entries':on['cache_entries'],'cache_bytes':on['cache_serialized_bytes'],
   'uncached_peak_rss':off['peak_rss_bytes'],'cached_peak_rss':on['peak_rss_bytes']})
 by_cell={}
 for name in cells:
  rows=[r for r in summaries if r['cell']==name]
  by_cell[name]={'median_uncached_ms':statistics.median(r['uncached_ms'] for r in rows),
   'median_cached_ms':statistics.median(r['cached_ms'] for r in rows),'median_speedup':statistics.median(r['speedup'] for r in rows),
   'native_eval_reduction':statistics.median(r['evaluation_reduction'] for r in rows),
   'cache_entries':rows[0]['cache_entries'],'cache_bytes':statistics.median(r['cache_bytes'] for r in rows),
   'semantic_history_identical':True}
 result={'schema':'SubstrateContractQueryMemoizationV1Analysis','workers':len(ws),'source_lock_stable':True,
  'cells':by_cell,'paired_rows':summaries,
  'claim_boundary':'Pure-Term memoization preserves the tested finite query histories and reduces native calls. Wall speed is measured, not inferred from call counts; no safety/performance claim applies to graph-dependent Terms or evaluator state changes.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
