#!/usr/bin/env python3
"""Independent integrity and selector-quality analysis for query-ranking v1."""
import json,math,random,statistics,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
RAW=ROOT/'evaluation/reports/substrate_label_blind_query_ranking_v1_20260930_raw.json';LOCK=ROOT/'evaluation/substrate_capability/substrate_label_blind_query_ranking_v1_20260930_lock.json';OUT=ROOT/'evaluation/reports/substrate_label_blind_query_ranking_v1_20260930_analysis.json'
from cegis_faculty_on_sum_of_n import family as tri_family
from cegis_faculty_on_variance import family as var_family
from jabberwock_closes_the_euler_tie import _family as euler_family
TASKS=('triangular_number','population_variance','euler_characteristic');POLICIES=('fixed_first','seeded_random','entropy_ranked','oracle_best');REPS=10;SEED=20260930
def canon(v):return ('bool',v) if isinstance(v,bool) else ('number',float(v)) if isinstance(v,(int,float)) else (type(v).__name__,repr(v))
def entropy(preds):
 c=Counter(map(canon,preds));n=len(preds);return -sum((k/n)*math.log2(k/n) for k in c.values()) if n else 0.0
def euler_value(faces):
 allfaces=set()
 for face in faces:
  face=tuple(sorted(face))
  for mask in range(1,1<<len(face)):allfaces.add(tuple(face[i] for i in range(len(face)) if mask>>i&1))
 by=Counter(len(x)-1 for x in allfaces);return sum(((-1)**dim)*count for dim,count in by.items())
def expected(task,inp):
 if task=='triangular_number':return inp*(inp+1)//2
 if task=='population_variance':
  mean=sum(inp)/len(inp);return sum((x-mean)**2 for x in inp)/len(inp)
 return euler_value(inp)
def fam(task):return tri_family() if task=='triangular_number' else var_family() if task=='population_variance' else euler_family()
def close(a,b):
 try:return abs(float(a)-float(b))<1e-6
 except:return False
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());checks={};sched=[(t,p,r) for t in TASKS for r in range(1,REPS+1) for p in POLICIES];random.Random(SEED).shuffle(sched)
 checks['worker_count']=len(raw.get('workers',[]))==120;checks['schedule_exact']=raw.get('schedule')==[list(x) for x in sched];checks['lock_matches_capture']=raw.get('lock')==lock;checks['no_worker_failures']=len(raw.get('worker_failures',[]))==0
 rows=raw.get('workers',[]);checks['unique_worker_pids']=len({x.get('pid') for x in rows})==120 and None not in {x.get('pid') for x in rows};want={(t,p,r) for t,p,r in sched};got={(x.get('task'),x.get('policy'),x.get('replicate')) for x in rows};checks['cells_exact']=want==got
 by={(x['task'],x['policy'],x['replicate']):x for x in rows if x.get('worker_error') is None};summaries={}
 for task in TASKS:
  candidates=fam(task);names=[n for n,_ in candidates];labels={n:expected(task,inp) for n,inp in candidates}
  for policy in POLICIES:
   cells=[]
   for rep in range(1,REPS+1):
    x=by.get((task,policy,rep))
    if x is None:continue
    key=f'{task}_{policy}_{rep}'
    checks[key+'_candidate_pool']=x.get('candidate_order')==names
    checks[key+'_known_fit']=bool(x.get('known_fit')) and all(all(close(p,k['label']) for p in k.get('predictions',[])) for k in x['known_fit'])
    checks[key+'_hypothesis_count']=len(x.get('hypothesis_ids',[]))==4 and x.get('true_hypothesis') in x['hypothesis_ids']
    chosen=x.get('selected_query');checks[key+'_selected_in_pool']=chosen in names
    response=x.get('oracle_responses',[]);expected_calls=len(candidates) if policy=='oracle_best' else 1
    checks[key+'_oracle_budget']=len(response)==expected_calls and all(close(z.get('label'),labels.get(z.get('name'))) and z.get('input')==dict(candidates).get(z.get('name')) for z in response)
    if policy=='fixed_first':expected_choice=names[0]
    elif policy=='seeded_random':expected_choice=random.Random(SEED+rep+TASKS.index(task)*10000).choice(candidates)[0]
    elif policy=='entropy_ranked':
     ranked=x.get('ranked',[]);checks[key+'_full_rank_table']=len(ranked)==len(candidates)
     for i,row in enumerate(ranked):
      checks[f'{key}_rank_{i}_entropy']=close(row.get('entropy_bits'),entropy(row.get('predictions',[])))
      if i:checks[f'{key}_rank_{i}_order']=(ranked[i-1]['entropy_bits']>row['entropy_bits']+1e-12 or (close(ranked[i-1]['entropy_bits'],row['entropy_bits']) and ranked[i-1]['distinct_predictions']>=row['distinct_predictions']))
     expected_choice=ranked[0]['name'] if ranked else None
     checks[key+'_selector_work']=x.get('selector_evaluations')==len(candidates)*4
    else:
     scores=[]
     for z in x.get('oracle_best_candidates',[]):
      checks[key+'_oracle_best_label_'+str(z.get('name'))]=close(z.get('label'),labels.get(z.get('name')))
      survivors=[x['hypothesis_ids'][i] for i,pred in enumerate(z.get('predictions',[])) if close(pred,z.get('label'))]
      checks[key+'_oracle_best_survivors_'+str(z.get('name'))]=survivors==z.get('survivors')
      scores.append((len(survivors),names.index(z['name']),z['name']))
     checks[key+'_oracle_best_table']=len(scores)==len(candidates)
     expected_choice=min(scores)[2] if scores else None
    checks[key+'_policy_choice']=chosen==expected_choice
    selected=next((z for z in response if z.get('name')==chosen),None)
    preds=x.get('selected_predictions',[]);truth=x.get('true_hypothesis');hypids=x.get('hypothesis_ids',[])
    checks[key+'_survivors_reconstruct']=selected is not None and [hypids[i] for i,pred in enumerate(preds) if close(pred,selected['label'])]==x.get('survivors')
    checks[key+'_truth_survives']=x.get('true_survives')==(truth in x.get('survivors',[])) and truth in x.get('survivors',[])
    checks[key+'_unique_flag']=x.get('unique_true')==(x.get('survivors')==[truth])
    checks[key+'_selector_cost']=x.get('selector_evaluations')==(len(candidates)*4 if policy=='entropy_ranked' else 0)
    cells.append({'replicate':rep,'query':chosen,'survivors':x.get('survivors'),'true_survives':x.get('true_survives'),'unique_true':x.get('unique_true'),'oracle_calls':len(response),'selector_evaluations':x.get('selector_evaluations'),'rank_wall_s':x.get('rank_wall_s'),'wall_s':x.get('wall_s')})
   summaries[(task,policy)]=cells
 taskout={}
 for task in TASKS:
  taskout[task]={}
  for policy in POLICIES:
   cells=summaries[(task,policy)];taskout[task][policy]={'workers':cells,'summary':{'n':len(cells),'mean_survivors':statistics.mean(len(x['survivors']) for x in cells) if cells else None,'unique_true_fraction':sum(x['unique_true'] for x in cells)/len(cells) if cells else None,'true_survival_fraction':sum(x['true_survives'] for x in cells)/len(cells) if cells else None,'oracle_calls_median':statistics.median(x['oracle_calls'] for x in cells) if cells else None,'selector_evaluations':statistics.median(x['selector_evaluations'] for x in cells) if cells else None,'rank_wall_median_s':statistics.median(x['rank_wall_s'] for x in cells) if cells else None,'wall_median_s':statistics.median(x['wall_s'] for x in cells) if cells else None}}
 checks['all_cells_analyzed']=all(len(summaries[(t,p)])==REPS for t in TASKS for p in POLICIES);valid=all(checks.values());out={'schema_version':1,'valid':valid,'check_count':len(checks),'checks':checks,'tasks':taskout};OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'valid':valid,'check_count':len(checks),'failed':[k for k,v in checks.items() if not v],'summary':{t:{p:x['summary'] for p,x in z.items()} for t,z in taskout.items()},'analysis':str(OUT)},indent=2));
 if not valid:sys.exit(1)
if __name__=='__main__':main()
