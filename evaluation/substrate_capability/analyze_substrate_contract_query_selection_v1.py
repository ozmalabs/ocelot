#!/usr/bin/env python3
"""Independent formula, information-score, and random-baseline analysis."""
import json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_contract_query_selection_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_contract_query_selection_v1_lock_20261001.json'
OUT=ROOT/'evaluation/reports/substrate_contract_query_selection_v1_analysis_20261001.json'
def f(name,x):return {'identity':lambda x:x,'square':lambda x:x*x,'absolute':lambda x:abs(x),'negative':lambda x:-x,'cube':lambda x:x*x*x}[name](x)
def entropy(values):
 counts={}
 for v in values:
  k=(type(v).__name__,repr(v));counts[k]=counts.get(k,0)+1
 n=len(values);return -sum((c/n)*math.log2(c/n) for c in counts.values())
def survivors(ids,obs):return [h for h in ids if all(f(h,o['inputs']['x'])==o['expected'] for o in obs)]
def random_baseline(task,rep,ids,target,initial,trials,seed,task_index):
 rng=random.Random(seed+rep*101+task_index*10007);counts=[]
 for _ in range(trials):
  ss=list(ids);obs=list(initial);order=list(range(-5,6));rng.shuffle(order);n=0
  for x in order:
   if any(o['inputs']['x']==x for o in obs):continue
   y=f(target,x);obs.append({'inputs':{'x':x},'expected':y});n+=1;ss=survivors(ss,obs)
   if len(ss)<=1:break
  counts.append(n)
 return counts
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());ws=raw['workers'];assert raw['lock']==raw['post_lock']==lock
 assert len(ws)==6 and all(w.get('kind')=='worker' for w in ws) and len({w['pid'] for w in ws})==6
 assert all(w['source_stable'] and w['before']==w['after']==lock['active'] for w in ws)
 design=lock['design'];tasks=design['tasks'];grid=[p['x'] for p in design['candidate_inputs']]
 assert sorted((w['task'],w['rep']) for w in ws)==[(t,r) for t in tasks for r in (1,2)]
 rounds=[];random_all=[]
 for w in ws:
  task=tasks[w['task']];ids=w['hypothesis_ids'];target=w['target_id_for_analysis_only'];assert target==task['target'] and target in ids
  obs=list(w['initial_observations']);assert all(len({f(h,o['inputs']['x']) for h in ids})==1 for o in obs)
  assert len(w['history'])==1
  h=w['history'][0];x=h['query']['x'];assert x in grid and all(o['inputs']['x']!=x for o in obs)
  ss=survivors(ids,obs);assert h['survivors_before']==ss
  pred={r['hypothesis']:r['output'] for r in h['predictions']}
  expected={name:f(name,x) for name in ss};assert pred==expected
  scores=[]
  for candidate_x in grid:
   if any(o['inputs']['x']==candidate_x for o in obs):continue
   scores.append((entropy([f(name,candidate_x) for name in ss]),candidate_x))
  best=max(s for s,_ in scores);first=max((s,-candidate_x) for s,candidate_x in scores)
  assert abs(h['entropy_bits']-best)<1e-12 and (h['entropy_bits'],-x)==first
  label=f(target,x);assert h['oracle_output']==label
  obs.append({'inputs':{'x':x},'expected':label});assert survivors(ids,obs)==[target]
  final=w['final_selector_status'];assert not final['ok'] and final['surviving_hypotheses']==[target]
  expected_random=random_baseline(w['task'],w['rep'],ids,target,w['initial_observations'],design['random_trials'],design['seed'],list(tasks).index(w['task']))
  assert w['random_query_counts']==expected_random and max(expected_random)<=len(grid)
  rounds.append({'task':w['task'],'rep':w['rep'],'selected_input':x,'entropy_bits':h['entropy_bits'],'selected_rounds':len(w['history']),'random_mean_rounds':statistics.mean(expected_random),'random_median_rounds':statistics.median(expected_random),'random_one_query_rate':sum(n==1 for n in expected_random)/len(expected_random)})
  random_all.extend(expected_random)
 by_task={}
 for task in tasks:
  rs=[r for r in rounds if r['task']==task]
  by_task[task]={'workers':len(rs),'selected_queries':sum(r['selected_rounds'] for r in rs),'unique_on_first_query':all(r['selected_rounds']==1 for r in rs),'selected_input_by_worker':[r['selected_input'] for r in rs],
   'random_mean_queries':statistics.mean(r['random_mean_rounds'] for r in rs),'random_one_query_rate':statistics.mean(r['random_one_query_rate'] for r in rs)}
 result={'schema':'SubstrateContractQuerySelectionV1Analysis','workers':6,'source_lock_stable':True,'task_families':by_task,
  'total_selected_queries':sum(r['selected_rounds'] for r in rounds),'random_baseline_mean_queries':statistics.mean(random_all),
  'random_baseline_median_queries':statistics.median(random_all),'random_baseline_one_query_rate':sum(n==1 for n in random_all)/len(random_all),
  'selector_runtime_median_us':statistics.median(w['selector_elapsed_ns'] for w in ws)/1e3,
  'claim_boundary':'The selector maximizes predictive disagreement over a finite caller-supplied hypothesis set and candidate grid. It did not generate hypotheses, select tasks or labels, or establish that a hypothesis set contains the intended program.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
