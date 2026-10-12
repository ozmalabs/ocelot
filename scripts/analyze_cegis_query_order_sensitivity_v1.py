#!/usr/bin/env python3
"""Independent checks and paired summary for the CEGIS order-sensitivity probe."""
import hashlib, json, random, statistics, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/cegis_query_order_sensitivity_v1_20260930_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/cegis_query_order_sensitivity_v1_20260930_lock.json'
OUT=ROOT/'evaluation/reports/cegis_query_order_sensitivity_v1_20260930_analysis.json'
SEED=20260930; REPS=5; HOLD=(17,23,50,99,100,250)
def target(n): return n*(n+1)//2
def main():
    raw=json.loads(RAW.read_text()); lock=json.loads(LOCK.read_text()); checks={}
    sched=[(arm,r) for r in range(1,REPS+1) for arm in ('fixed_order','seeded_permutation')]; random.Random(SEED).shuffle(sched)
    checks['worker_count']=len(raw.get('workers',[]))==10
    checks['schedule_exact']=raw.get('schedule')==[list(x) for x in sched]
    checks['lock_matches_capture']=raw.get('lock')==lock
    checks['no_worker_failures']=len(raw.get('worker_failures',[]))==0
    rows=raw.get('workers',[]); checks['unique_worker_pids']=len({r.get('pid') for r in rows})==10 and None not in {r.get('pid') for r in rows}
    expected={(arm,r) for arm,r in sched}; observed={(x.get('arm'),x.get('replicate')) for x in rows}
    checks['cells_exact']=observed==expected
    by={(r['arm'],r['replicate']):r for r in rows if 'worker_error' not in r or r['worker_error'] is None}
    per=[]
    for rep in range(1,REPS+1):
        pair={arm:by.get((arm,rep)) for arm in ('fixed_order','seeded_permutation')}
        for arm,row in pair.items():
            if row is None: continue
            order=row.get('candidate_order',[]); expected_order=list(range(2,13))
            if arm=='seeded_permutation': random.Random(SEED+rep).shuffle(expected_order)
            checks[f'{arm}_{rep}_order']=order==expected_order
            checks[f'{arm}_{rep}_query_labels_in_family_calls']=all(int(q.split('=')[1]) in row.get('candidate_family_oracle_calls',[]) for q in row.get('selected_queries',[]))
            checks[f'{arm}_{rep}_rows_reconcile']=row['result'].get('rows')==['n=1']+row.get('selected_queries',[])
            held=row.get('heldout',[])
            checks[f'{arm}_{rep}_heldout_labels']=len(held)==len(HOLD) and all(x.get('n')==n and x.get('expected')==target(n) for x,n in zip(held,HOLD))
            checks[f'{arm}_{rep}_heldout_flags']=all(x.get('exact')==(x.get('predicted') is not None and abs(float(x['predicted'])-target(x['n']))<1e-9) for x in held)
        if all(pair.values()):
            a,b=pair['fixed_order'],pair['seeded_permutation']
            per.append({'replicate':rep,'fixed_queries':a['selected_queries'],'permuted_queries':b['selected_queries'],'fixed_term':a['result']['final_term'],'permuted_term':b['result']['final_term'],'fixed_converged':a['result']['converged'],'permuted_converged':b['result']['converged'],'fixed_heldout_exact':sum(x['exact'] for x in a['heldout']),'permuted_heldout_exact':sum(x['exact'] for x in b['heldout']),'fixed_family_oracle_calls':len(a['candidate_family_oracle_calls']),'permuted_family_oracle_calls':len(b['candidate_family_oracle_calls']),'fixed_total_oracle_calls':len(a['oracle_calls']),'permuted_total_oracle_calls':len(b['oracle_calls']),'fixed_wall_s':a['wall_s'],'permuted_wall_s':b['wall_s']})
    checks['all_replicates_summarized']=len(per)==5
    valid=all(checks.values())
    summary={'schema_version':1,'valid':valid,'checks':checks,'paired':per,'summary':{'same_query_sequence_pairs':sum(x['fixed_queries']==x['permuted_queries'] for x in per),'same_final_term_pairs':sum(x['fixed_term']==x['permuted_term'] for x in per),'fixed_total_calls_median':statistics.median([x['fixed_total_oracle_calls'] for x in per]) if per else None,'permuted_total_calls_median':statistics.median([x['permuted_total_oracle_calls'] for x in per]) if per else None,'fixed_family_calls_median':statistics.median([x['fixed_family_oracle_calls'] for x in per]) if per else None,'permuted_family_calls_median':statistics.median([x['permuted_family_oracle_calls'] for x in per]) if per else None,'fixed_wall_median_s':statistics.median([x['fixed_wall_s'] for x in per]) if per else None,'permuted_wall_median_s':statistics.median([x['permuted_wall_s'] for x in per]) if per else None}}
    OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'valid':valid,'checks':checks,'summary':summary['summary'],'analysis':str(OUT)},indent=2))
    if not valid: sys.exit(1)
if __name__=='__main__': main()
