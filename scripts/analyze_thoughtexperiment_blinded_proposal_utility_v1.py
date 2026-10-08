#!/usr/bin/env python3
"""Recompute descriptive metrics and integrity checks for proposal-utility v1."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_analysis_20261002.json'
FAMILIES=('shape_axis','recurrence','navigation','control_kind')
ARMS=('experience_rank','frozen_rank','default_order','random_order','target_memoization')

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def main()->int:
 orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 order_workers={int(row['worker']):row for row in orders['workers']}
 score_workers={int(row['worker']):row for row in scores['workers']}
 errors=[];checks={}
 checks['source_stable']=orders['source_before']==orders['source_after']==scores['source_before']==scores['source_after']
 if not checks['source_stable']:errors.append('source fingerprints differ across captures')
 checks['orders_bound_to_scores']=scores['orders_sha256']==sha(ORDERS)
 if not checks['orders_bound_to_scores']:errors.append('score capture does not bind to frozen orders')
 checks['four_workers']=set(order_workers)==set(range(4)) and set(score_workers)==set(range(4))
 if not checks['four_workers']:errors.append('worker set is incomplete')
 arm_summary={};family_summary={};coverage={};attempted_trials=0
 for family in FAMILIES:
  labels_total=0;labels_seen=0;family_summary[family]={}
  for worker in range(4):
   order=order_workers[worker]['families'][family]
   result=score_workers[worker]['families'][family]
   labels=[row['label'] for row in order['candidate_descriptors']]
   labels_total+=len(labels)
   if labels!=[row['label'] for row in result['candidate_descriptors']]:errors.append(f'{family}/{worker}: descriptor mismatch')
   for arm in ARMS:
    cell=result['arms'][arm];planned=order['orders'][arm];trials=cell['trials']
    got=[row['label'] for row in trials]
    if got!=planned[:len(got)]:errors.append(f'{family}/{worker}/{arm}: trials are not order prefix')
    if not trials or cell['attempts_until_success']!=len(trials) or not cell['success']:
     errors.append(f'{family}/{worker}/{arm}: missing terminal success')
    if not trials[-1]['utility']>=1.0 or any(row['utility']>=1.0 for row in trials[:-1]):
     errors.append(f'{family}/{worker}/{arm}: stopping rule mismatch')
    if any(not row['primary_preserved'] or not row['receipt_verified'] for row in trials):
     errors.append(f'{family}/{worker}/{arm}: isolation or receipt failure')
    attempted_trials+=len(trials)
   for arm in ARMS:
    family_summary[family].setdefault(arm,{'first_candidate_successes':0,'attempts':[]})
    cell=result['arms'][arm]
    family_summary[family][arm]['first_candidate_successes']+=int(cell['first_candidate_utility']>=1.0)
    family_summary[family][arm]['attempts'].append(int(cell['attempts_until_success']))
   labels_seen+=len({trial['label'] for arm in ARMS for trial in result['arms'][arm]['trials']})
  coverage[family]={'candidate_instances':labels_total,'unique_heldout_instances_scored':labels_seen}
 checks['all_policy_orders_are_permutations']=True
 for row in orders['workers']:
  for family in FAMILIES:
   labels={x['label'] for x in row['families'][family]['candidate_descriptors']}
   for arm,seq in row['families'][family]['orders'].items():
    if arm not in ARMS or len(seq)!=len(labels) or set(seq)!=labels:
     checks['all_policy_orders_are_permutations']=False
 if not checks['all_policy_orders_are_permutations']:errors.append('incomplete or invalid policy permutation')
 checks['all_attempted_branches_valid']=not any('isolation or receipt failure' in e for e in errors)
 for family in FAMILIES:
  for arm in ARMS:
   row=family_summary[family][arm]
   row['median_attempts']=statistics.median(row['attempts'])
   row['attempts'].sort()
 arm_summary={}
 for arm in ARMS:
  cells=[worker['families'][family]['arms'][arm] for worker in scores['workers'] for family in FAMILIES]
  costs=[row['end_to_end_selection_ns']/1e6 for row in scores['cost_ledger'] if row['arm']==arm]
  arm_summary[arm]={'first_candidate_successes':sum(row['first_candidate_utility']>=1.0 for row in cells),
   'cells':len(cells),'median_attempts':statistics.median(row['attempts_until_success'] for row in cells),
   'mean_selection_cost_ms':statistics.mean(costs),'median_selection_cost_ms':statistics.median(costs)}
 total_instances=sum(row['candidate_instances'] for row in coverage.values())
 total_scored=sum(row['unique_heldout_instances_scored'] for row in coverage.values())
 checks['exhaustive_heldout_candidate_coverage']=total_scored==total_instances
 if not checks['exhaustive_heldout_candidate_coverage']:
  errors.append(f'held-out coverage {total_scored}/{total_instances}; preregistered exhaustive-scoring gate fails')
 result={'schema':'BlindedProposalUtilityV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'inputs':{'orders_sha256':sha(ORDERS),'scores_sha256':sha(SCORES)},'checks':checks,'errors':errors,
  'family_summary':family_summary,'arm_summary':arm_summary,'heldout_candidate_coverage':coverage,
  'totals':{'worker_family_policy_cells':sum(1 for _ in scores['cost_ledger']),'candidate_trials':attempted_trials,
   'heldout_candidate_instances':total_instances,'unique_heldout_candidate_instances_scored':total_scored,
   'coverage_fraction':total_scored/total_instances}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'checks':checks,'errors':errors,
  'totals':result['totals'],'arm_summary':arm_summary},sort_keys=True))
 return 1 if any(not value for value in checks.values()) else 0

if __name__=='__main__':raise SystemExit(main())
