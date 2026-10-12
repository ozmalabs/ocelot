#!/usr/bin/env python3
"""Independent structural and matcher-work checks for context-scale replay."""
from __future__ import annotations
import hashlib,itertools,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_1_analysis_20260929.json'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_context_scale_v1_1_lock_20260929.json'
COUNTS=(0,8,32)
EXPECTED={(d,''.join(map(str,p)),r) for d in COUNTS for p in itertools.permutations(range(4)) for r in range(3)}
CLAUSES={'has_active_goal','originated_in','has_event','for_goal'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());locked=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs']
 checks={'expected_216_cells':len(runs)==216 and all('worker_error' not in x for x in runs)}
 flat=[x.get('worker',{}) for x in runs if 'worker' in x]
 actual={(w.get('decoy_count'),w.get('permutation'),w.get('replicate')) for w in flat}
 checks['exact_context_permutation_replicate_grid']=actual==EXPECTED
 checks['unique_fresh_processes']=len(flat)==216 and len({w['pid'] for w in flat})==216
 checks['source_native_lock_stable']=raw.get('locked_inputs')==locked==raw.get('post_run_inputs') and all(x.get('before')==locked==x.get('after') for x in runs if 'worker' in x)
 grouped=defaultdict(list);rows=[]
 for w in flat:
  d=w['decoy_count'];label=w['permutation'];rep=w['replicate'];task=w['task_run'];idx=w['target_rule_index'];installed=w['installed_match']
  key=f'D{d}_{label}_r{rep}'
  checks[key+'_decoy_inventory']=w['decoy_goal_count']==d and w['decoy_transition_count']==0
  timing=w['installation_timing']
  checks[key+'_three_adds_and_removes']=len(timing['lifecycle_add_calls'])==3 and len(timing['lifecycle_remove_calls'])==3
  checks[key+'_positive_install_timers']=all(int(t['wall_ns'])>0 and int(t['cpu_ns'])>0 for t in timing['lifecycle_add_calls']+timing['lifecycle_remove_calls'])
  checks[key+'_one_target_add']=timing['target_rule_add']['rule_name']=='discourse_goal_select_task_context_scale_v1' and sum(t['rule_name']=='discourse_goal_select_task_context_scale_v1' for t in timing['lifecycle_add_calls'])==1
  checks[key+'_task_oracles']=task['task_oracle_pass'] and task['common_ground_oracle_pass']
  checks[key+'_ten_fixed_points']=len(task['checkpoints'])==10 and task['all_checkpoints_fixed']
  order=tuple(str(e[1]) for e in installed)
  checks[key+'_installed_order_is_permutation']=len(order)==4 and set(order)==CLAUSES
  candidate_total=0;checkpoint=[];clause_total=[0]*4
  for cp,audit in zip(task['checkpoints'],w['audit_rows']):
   per=sum(int(n) for i,name,n in audit['per_rule'] if int(i)==idx and str(name)=='candidate_tests')
   clauses=[0]*4
   for i,j,n in audit['clauses']:
    if int(i)==idx and 0<=int(j)<4:clauses[int(j)]+=int(n)
   checks[key+f'_cp{cp["event_index"]}_clause_conservation']=sum(clauses)==per
   candidate_total+=per
   for j,n in enumerate(clauses):clause_total[j]+=n
   checkpoint.append({'event_index':cp['event_index'],'candidate_tests':per,'candidate_tests_by_clause':clauses,
    'wall_ns':int(cp['wall_ns']),'cpu_ns':int(cp['cpu_ns'])})
  checks[key+'_ten_audit_checkpoints']=len(checkpoint)==10
  row={'decoy_count':d,'permutation':label,'replicate':rep,'pid':w['pid'],'installed_order':list(order),
   'target_candidate_tests':candidate_total,'candidate_tests_by_installed_clause':clause_total,
   'final_digest':task['final_digest'],'checkpoint_work':checkpoint,
   'target_add_wall_ns':int(timing['target_rule_add']['wall_ns']),'target_add_cpu_ns':int(timing['target_rule_add']['cpu_ns']),
   'lifecycle_add_wall_ns':int(timing['lifecycle_add_wall_ns']),'lifecycle_add_cpu_ns':int(timing['lifecycle_add_cpu_ns']),
   'lifecycle_remove_wall_ns':int(timing['lifecycle_remove_wall_ns']),'lifecycle_remove_cpu_ns':int(timing['lifecycle_remove_cpu_ns']),
   'audit_on_closure_wall_ns':sum(int(c['wall_ns']) for c in checkpoint),'audit_on_closure_cpu_ns':sum(int(c['cpu_ns']) for c in checkpoint)}
  rows.append(row);grouped[d].append(row)
 summary=[]
 for d,rs in sorted(grouped.items()):
  checks[f'D{d}_terminal_digest_parity']=len({r['final_digest'] for r in rs})==1
  costs=[r['target_candidate_tests'] for r in rs]
  source=[r['target_candidate_tests'] for r in rs if r['permutation']=='0123']
  by_order=defaultdict(list)
  for r in rs:by_order[tuple(r['installed_order'])].append(r['target_candidate_tests'])
  order_summary=[{'installed_order':list(o),'worker_count':len(v),'median_candidate_tests':statistics.median(v),
                  'min_candidate_tests':min(v),'max_candidate_tests':max(v)}
                 for o,v in sorted(by_order.items(),key=lambda x:(statistics.median(x[1]),x[0]))]
  summary.append({'decoy_count':d,'workers':len(rs),'distinct_installed_orders':len(by_order),
   'candidate_tests':{'min':min(costs),'median':statistics.median(costs),'max':max(costs)},
   'source_authored_request':{'worker_count':len(source),'median_candidate_tests':statistics.median(source),
                              'min':min(source),'max':max(source)},
   'installation_and_closure_timing_ns':{key:{'median':statistics.median(r[key] for r in rs),'min':min(r[key] for r in rs),'max':max(r[key] for r in rs)}
     for key in ('target_add_wall_ns','target_add_cpu_ns','lifecycle_add_wall_ns','lifecycle_add_cpu_ns','lifecycle_remove_wall_ns','lifecycle_remove_cpu_ns','audit_on_closure_wall_ns','audit_on_closure_cpu_ns')},
   'by_installed_order':order_summary})
 payload={'schema_version':1,'raw_sha256':sha(RAW),'analysis_sha256':sha(Path(__file__).resolve()),
  'checks':checks,'all_checks_pass':all(checks.values()),'checks_passed':sum(checks.values()),'checks_total':len(checks),
  'worker_count':len(rows),'context_summary':summary,'rows':rows,
  'claim_boundary':'One frozen two-goal task, one four-clause rule, synthetic disconnected decoy states, 24 authored permutations and three fresh-process repeats per context. Audit-enabled exact native candidate work; no natural-task, latency, optimizer, or general tractability claim.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':payload['all_checks_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'context_summary':summary},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
