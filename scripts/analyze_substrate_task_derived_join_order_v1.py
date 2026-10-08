#!/usr/bin/env python3
"""Independent semantic/work analysis for task-derived join-order replay v1."""
from __future__ import annotations
import hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_task_derived_join_order_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_task_derived_join_order_v1_analysis_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_v1_lock_20260927.json'
EXPECTED={(''.join(map(str,p)),r) for p in __import__('itertools').permutations(range(4)) for r in range(3)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical_match(rows):return tuple((str(a),str(b),str(c)) for a,b,c in rows)
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw['runs']
 actual={(x['worker']['permutation'],x['worker']['replicate']) for x in runs}
 checks={'72_permutation_replicate_cells':len(runs)==72 and actual==EXPECTED,
  'unique_fresh_processes':len({x['worker']['pid'] for x in runs})==72,
  'source_native_lock_stable':raw['locked_inputs']==lock==raw['post_run_inputs'] and all(x['before']==lock==x['after'] for x in runs)}
 grouped=defaultdict(list);rows=[];expected_types=None
 for wrap in runs:
  w=wrap['worker'];label=w['permutation'];rep=w['replicate'];tr=w['task_run'];idx=w['target_rule_index'];installed=w['installed_match'];
  checks[f'{label}_r{rep}_identity_oracles']=tr['task_oracle_pass'] and tr['common_ground_oracle_pass']
  checks[f'{label}_r{rep}_all_ten_fixed_points']=len(tr['checkpoints'])==10 and tr['all_checkpoints_fixed']
  checks[f'{label}_r{rep}_target_rule_present']=isinstance(idx,int) and len(installed)==4
  types=tuple(e[1] for e in installed)
  checks[f'{label}_r{rep}_installed_clause_multiset']=sorted(types)==sorted(('has_active_goal','originated_in','has_event','for_goal'))
  cell_total=0;clause_totals=[0]*4;checkpoint_rows=[]
  for cp,audit in zip(tr['checkpoints'],w['audit_rows']):
   per=sum(int(n) for i,name,n in audit['per_rule'] if int(i)==idx and name=='candidate_tests')
   clauses=[0]*4
   for i,j,n in audit['clauses']:
    if int(i)==idx and 0<=int(j)<4:clauses[int(j)]+=int(n)
   checks[f'{label}_r{rep}_cp{int(cp["event_index"])}_clause_conservation']=sum(clauses)==per
   cell_total+=per
   for j,n in enumerate(clauses):clause_totals[j]+=n
   checkpoint_rows.append({'event_index':cp['event_index'],'target_candidate_tests':per,'candidate_tests_by_clause':clauses,
      'target_rule_enumerations':sum(int(n) for i,name,n in audit['per_rule'] if int(i)==idx and name=='rule_enumerations'),
      'all_rule_candidate_tests':int(cp['counters'].get('cand_tested',0)),
      'wall_ns':int(cp['wall_ns']),'cpu_ns':int(cp['cpu_ns'])})
  checks[f'{label}_r{rep}_audit_checkpoint_count']=len(checkpoint_rows)==10
  row={'permutation':label,'replicate':rep,'pid':w['pid'],'installed_edge_order':list(types),
    'target_rule_index':idx,'target_candidate_tests_total':cell_total,'target_candidate_tests_by_installed_clause':clause_totals,
    'all_rule_candidate_tests_total':sum(x['all_rule_candidate_tests'] for x in checkpoint_rows),
    'closure_wall_ns_total':sum(x['wall_ns'] for x in checkpoint_rows),'closure_cpu_ns_total':sum(x['cpu_ns'] for x in checkpoint_rows),
    'final_digest':tr['final_digest'],'checkpoint_work':checkpoint_rows}
  rows.append(row);grouped[label].append(row)
 checks['identical_terminal_graph_across_all_arms']=len({r['final_digest'] for r in rows})==1
 by_order=defaultdict(list)
 for label,rs in grouped.items():
  readbacks={tuple(r['installed_edge_order']) for r in rs};checks[f'{label}_repeat_installed_order_stable']=len(readbacks)==1
  checks[f'{label}_repeat_terminal_graph_stable']=len({r['final_digest'] for r in rs})==1
  by_order[next(iter(readbacks))].extend(rs)
 order_summary=[]
 for order,rs in sorted(by_order.items(),key=lambda z:(statistics.median(r['target_candidate_tests_total'] for r in z[1]),z[0])):
  order_summary.append({'installed_edge_order':list(order),'authored_permutations':sorted({r['permutation'] for r in rs}),
    'worker_count':len(rs),'target_candidate_tests_median':int(statistics.median(r['target_candidate_tests_total'] for r in rs)),
    'target_candidate_tests_min':min(r['target_candidate_tests_total'] for r in rs),'target_candidate_tests_max':max(r['target_candidate_tests_total'] for r in rs),
    'all_rule_candidate_tests_median':int(statistics.median(r['all_rule_candidate_tests_total'] for r in rs)),
    'closure_wall_ns_median':int(statistics.median(r['closure_wall_ns_total'] for r in rs)),
    'closure_cpu_ns_median':int(statistics.median(r['closure_cpu_ns_total'] for r in rs))})
 costs=[r['target_candidate_tests_total'] for r in rows];best=min(costs);worst=max(costs)
 payload={'schema_version':1,'raw_sha256':sha(RAW),'analysis_sha256':sha(Path(__file__).resolve()),
  'checks':checks,'all_checks_pass':all(checks.values()),'checks_passed':sum(checks.values()),'checks_total':len(checks),
  'worker_count':len(rows),'distinct_installed_orders':len(order_summary),'target_candidate_work':{'min':best,'max':worst,'ratio':worst/max(1,best),'median':int(statistics.median(costs))},
  'installed_order_summary':order_summary,'rows':rows,
  'claim_boundary':'One frozen common-ground conversational fixture, one varied four-edge production rule, fixture-supplied identity links, 24 authored permutations and three repetitions. Native audit is enabled; no optimizer or uninstrumented latency claim.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':payload['all_checks_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'installed_orders':payload['distinct_installed_orders'],'target_work':payload['target_candidate_work']},indent=2))
 if not payload['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
