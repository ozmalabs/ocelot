#!/usr/bin/env python3
"""Independent checks and work summaries for the authored path-join replay."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_task_derived_path_join_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_task_derived_path_join_v1_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_path_join_v1_lock_20260927.json'
ORDERS={''.join(map(str,p)) for p in itertools.permutations(range(3))}
EXPECTED={(m,q,p,r) for m in (1,8,32) for q in (0,4) for p in ORDERS for r in range(3)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw['runs'];actual={(x['multiplicity'],x['decoy_ratio'],x['permutation'],x['replicate']) for x in runs}
 checks={'108_factorial_cells':len(runs)==108 and actual==EXPECTED,'108_unique_pids':len({x['pid'] for x in runs})==108,
  'source_native_lock_stable':raw['locked_inputs']==lock==raw['post_run_inputs'] and all(x['before']==lock==x['after'] for x in runs)}
 rows=[];groups=defaultdict(list)
 for w in runs:
  m,q,p,rep=w['multiplicity'],w['decoy_ratio'],w['permutation'],w['replicate'];plain,a=w['plain'],w['audit'];prefix=f'm{m}_q{q}_p{p}_r{rep}'
  checks[prefix+'_plain_audit_graph_parity']=plain['graph']==a['graph']
  checks[prefix+'_plain_audit_report_parity']=plain['report']==a['report']
  checks[prefix+'_fixed_point']=a['report']['status']=='fixed_point' and a['report']['budget_overshoot']==0
  checks[prefix+'_exact_positive_effects']=a['commit_count']==m and a['commit_edges']==m and a['positive_canaries_passed']==m and a['positive_patches_queued']==m and a['source_status']=='commit_ready'
  checks[prefix+'_decoys_unchanged']=all(x=='pending' for x in a['decoy_canary_statuses']) and all(x=='ready' for x in a['decoy_patch_states'])
  checks[prefix+'_balanced_relation_populations']=set(a['relation_counts'].values())=={m+q*m}
  checks[prefix+'_installed_clause_count']=len(a['installed_order'])==3 and sorted(a['installed_order'])==sorted(('selected_patch','has_canary','has_canary_evidence'))
  total=sum(int(n) for i,name,n in a['per_rule'] if int(i)==a['rule_index'] and name=='candidate_tests')
  per_clause=[0]*3
  for i,j,n in a['clause_candidates']:
   if int(i)==a['rule_index'] and 0<=int(j)<3:per_clause[int(j)]+=int(n)
  checks[prefix+'_native_clause_conservation']=total==sum(per_clause) and per_clause==a['target_candidate_tests_by_clause'] and total==a['target_candidate_tests']
  checks[prefix+'_positive_candidate_work']=total>0
  row={'multiplicity':m,'decoy_ratio':q,'permutation':p,'replicate':rep,'pid':w['pid'],'installed_order':a['installed_order'],
   'target_candidate_tests':total,'target_candidate_tests_by_installed_clause':per_clause,'report':a['report'],'counters':a['counters'],
   'plain_graph':plain['graph'],'final_graph':a['graph'],'effect_outcomes':{'commits':a['commit_count'],'commit_edges':a['commit_edges'],'passed_canaries':a['positive_canaries_passed'],'queued_patches':a['positive_patches_queued'],'source_status':a['source_status']}}
  rows.append(row);groups[m,q].append(row)
 for m in (1,8,32):
  for q in (0,4):
   items=groups[m,q];digests={json.dumps(r['final_graph'],sort_keys=True) for r in items}
   checks[f'm{m}_q{q}_terminal_graph_order_and_repeat_invariance']=len(digests)==1
   checks[f'm{m}_q{q}_exactly_18_cells']=len(items)==18
 summary=[]
 for m in (1,8,32):
  for q in (0,4):
   rr=groups[m,q];by_order=defaultdict(list)
   for r in rr:by_order[tuple(r['installed_order'])].append(r)
   summary.append({'multiplicity':m,'decoy_ratio':q,'population_per_relation':m+q*m,
    'installed_orders':[{'order':list(o),'worker_count':len(v),'authored_permutations':sorted({r['permutation'] for r in v}),
      'candidate_tests_median':int(statistics.median(r['target_candidate_tests'] for r in v)),
      'candidate_tests_min':min(r['target_candidate_tests'] for r in v),'candidate_tests_max':max(r['target_candidate_tests'] for r in v)}
      for o,v in sorted(by_order.items(),key=lambda z:(statistics.median(r['target_candidate_tests'] for r in z[1]),z[0]))],
    'distinct_installed_orders':len(by_order),'candidate_tests_min':min(r['target_candidate_tests'] for r in rr),
    'candidate_tests_max':max(r['target_candidate_tests'] for r in rr),'candidate_tests_median':int(statistics.median(r['target_candidate_tests'] for r in rr))})
 payload={'schema_version':1,'raw_sha256':sha(RAW),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,
  'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_checks_pass':all(checks.values()),'worker_count':len(rows),
  'summary_by_graph_setting':summary,'rows':rows,
  'claim_boundary':'One task-authored self-change policy path rule on generated positive/decoy graphs; six authored match orders; native audit-on counters and plain parity. No natural prevalence, learned order optimizer, or speed claim.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':payload['all_checks_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'summary_by_graph_setting':summary},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
