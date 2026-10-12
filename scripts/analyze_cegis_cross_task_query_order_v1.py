#!/usr/bin/env python3
"""Independent task-label, schedule, query, and cost audit for cross-task CEGIS probe."""
import json,random,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/cegis_cross_task_query_order_v1_20260930_raw.json';LOCK=ROOT/'evaluation/substrate_capability/cegis_cross_task_query_order_v1_20260930_lock.json';OUT=ROOT/'evaluation/reports/cegis_cross_task_query_order_v1_20260930_analysis.json'
SEED=20260930;REPS=5
TRI_FAMILY=[f'n={n}' for n in range(2,13)]
VAR_FAMILY=[f'L{i}' for i in range(12)]
TRI_HELD=[('n=17',17),('n=23',23),('n=50',50),('n=99',99),('n=100',100),('n=250',250)]
VAR_HELD=[('H0',[5,5,5,5,5]),('H1',[1,100]),('H2',[3,1,4,1,5,9,2,6]),('H3',[12,7,19,3,25,8]),('H4',[0,0,0,0,1])]
def tri(n):return n*(n+1)//2
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());checks={}
 sched=[(task,arm,r) for task in ('triangular_number','population_variance') for r in range(1,6) for arm in ('fixed_order','seeded_permutation')];random.Random(SEED).shuffle(sched)
 checks['worker_count']=len(raw.get('workers',[]))==20;checks['schedule_exact']=raw.get('schedule')==[list(x) for x in sched];checks['lock_matches_capture']=raw.get('lock')==lock;checks['no_worker_failures']=len(raw.get('worker_failures',[]))==0
 rows=raw.get('workers',[]);checks['unique_worker_pids']=len({r.get('pid') for r in rows})==20 and None not in {r.get('pid') for r in rows};expected={(t,a,r) for t,a,r in sched};observed={(x.get('task'),x.get('arm'),x.get('replicate')) for x in rows};checks['cells_exact']=observed==expected
 by={(x['task'],x['arm'],x['replicate']):x for x in rows if x.get('worker_error') is None};paired={}
 for task in ('triangular_number','population_variance'):
  fam=TRI_FAMILY if task=='triangular_number' else VAR_FAMILY; known='n=1' if task=='triangular_number' else 'K0'; pairs=[]
  for rep in range(1,6):
   armrows={arm:by.get((task,arm,rep)) for arm in ('fixed_order','seeded_permutation')}
   for arm,row in armrows.items():
    if row is None:continue
    order=fam.copy()
    if arm=='seeded_permutation':random.Random(SEED+rep+(1000 if task=='population_variance' else 0)).shuffle(order)
    checks[f'{task}_{arm}_{rep}_order']=row.get('candidate_order')==order
    checks[f'{task}_{arm}_{rep}_literal_policy']=row.get('literal_policy')=='base literals only; outputs wrapped as TargetLabel'
    checks[f'{task}_{arm}_{rep}_native_work']=bool(row.get('native_calls')) and all(isinstance(x.get('explored'),int) and isinstance(x.get('elapsed_s'),(int,float)) for x in row['native_calls'])
    checks[f'{task}_{arm}_{rep}_query_rows']=row['result'].get('rows')==[known]+row.get('selected_queries',[]) and set(row.get('selected_queries',[]))<=set(fam)
    checks[f'{task}_{arm}_{rep}_oracle_calls']=bool(row.get('oracle_calls'))
    if task=='triangular_number':
     held=TRI_HELD; expected_held=[tri(n) for _,n in held]
    else:
     held=VAR_HELD;expected_held=[statistics.pvariance(xs) for _,xs in held]
    got=row.get('heldout',[])
    checks[f'{task}_{arm}_{rep}_heldout_labels']=len(got)==len(held) and all(x.get('name')==name and x.get('input')==inp and abs(float(x.get('expected'))-float(y))<1e-6 for x,(name,inp),y in zip(got,held,expected_held))
    checks[f'{task}_{arm}_{rep}_heldout_scores']=all(bool(x.get('exact'))==(x.get('predicted') is not None and abs(float(x['predicted'])-float(x['expected']))<1e-6) for x in got)
   if all(armrows.values()):
    a,b=armrows['fixed_order'],armrows['seeded_permutation']
    pairs.append({'replicate':rep,'fixed_queries':a['selected_queries'],'permuted_queries':b['selected_queries'],'fixed_term':a['result']['final_term'],'permuted_term':b['result']['final_term'],'fixed_converged':a['result']['converged'],'permuted_converged':b['result']['converged'],'fixed_heldout_exact':sum(x['exact'] for x in a['heldout']),'permuted_heldout_exact':sum(x['exact'] for x in b['heldout']),'fixed_oracle_calls':len(a['oracle_calls']),'permuted_oracle_calls':len(b['oracle_calls']),'fixed_candidates':sum(x['explored'] for x in a['native_calls']),'permuted_candidates':sum(x['explored'] for x in b['native_calls']),'fixed_search_s':sum(x['elapsed_s'] for x in a['native_calls']),'permuted_search_s':sum(x['elapsed_s'] for x in b['native_calls']),'fixed_wall_s':a['wall_s'],'permuted_wall_s':b['wall_s']})
  paired[task]={'pairs':pairs,'summary':{'same_query_pairs':sum(x['fixed_queries']==x['permuted_queries'] for x in pairs),'same_final_term_pairs':sum(x['fixed_term']==x['permuted_term'] for x in pairs),'fixed_queries_median':statistics.median([len(x['fixed_queries']) for x in pairs]) if pairs else None,'permuted_queries_median':statistics.median([len(x['permuted_queries']) for x in pairs]) if pairs else None,'fixed_calls_median':statistics.median([x['fixed_oracle_calls'] for x in pairs]) if pairs else None,'permuted_calls_median':statistics.median([x['permuted_oracle_calls'] for x in pairs]) if pairs else None,'fixed_candidates_median':statistics.median([x['fixed_candidates'] for x in pairs]) if pairs else None,'permuted_candidates_median':statistics.median([x['permuted_candidates'] for x in pairs]) if pairs else None,'fixed_search_s_median':statistics.median([x['fixed_search_s'] for x in pairs]) if pairs else None,'permuted_search_s_median':statistics.median([x['permuted_search_s'] for x in pairs]) if pairs else None,'fixed_wall_s_median':statistics.median([x['fixed_wall_s'] for x in pairs]) if pairs else None,'permuted_wall_s_median':statistics.median([x['permuted_wall_s'] for x in pairs]) if pairs else None}}
 checks['all_ten_pairs_summarized']=all(len(paired[t]['pairs'])==5 for t in paired);valid=all(checks.values());out={'schema_version':1,'valid':valid,'checks':checks,'tasks':paired};OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'valid':valid,'checks':checks,'tasks':{t:v['summary'] for t,v in paired.items()},'analysis':str(OUT)},indent=2));
 if not valid:sys.exit(1)
if __name__=='__main__':main()
