#!/usr/bin/env python3
"""Independent review of the five-policy control-kind pilot captures."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_five_policy_control_kind_pilot_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_review_20261002.json'
ARMS={'experience_rank','frozen_rank','default_order','random_order','target_memoization'}
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def contains_heldout(v)->bool:
 forbidden={'heldout','heldout_utility','heldout_score','heldout_scores','heldout_outcomes'}
 if isinstance(v,dict):return any(k in forbidden or contains_heldout(x) for k,x in v.items())
 if isinstance(v,list):return any(contains_heldout(x) for x in v)
 return False
def main()->int:
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 ow=orders['workers'];sw=scores['workers']
 runner=(ROOT/'evaluation/substrate_capability/thoughtexperiment_five_policy_control_kind_pilot_v1.py').read_text()
 desc={x['label']:x['digest'] for x in ow[0]['candidate_descriptors']}
 checks={
  'schemas_and_lock_linked':orders.get('schema')=='FivePolicyControlKindPilotV1OrderCapture' and
    lock.get('schema')=='FivePolicyControlKindPilotV1Lock' and orders.get('lock')==lock,
  'order_source_lock_parity':orders['source_before']==orders['source_after']==lock['sources'],
  'score_source_lock_parity':all(w['source_stable'] and w['source_before']==w['source_after']==lock['sources'] for w in sw),
  'four_order_and_score_workers':len(ow)==len(sw)==4 and {x['worker'] for x in ow}=={x['worker'] for x in sw},
  'separate_processes_in_source_locked_runner':('for i in range(WORKERS)' in runner and
    "'--order-worker'" in runner and "'--score-worker'" in runner and
    'subprocess.run(' in runner),
  'six_stable_candidate_bundles':all(len(w['candidate_descriptors'])==6 and
    {x['label']:x['digest'] for x in w['candidate_descriptors']}==desc for w in ow),
  'five_permutation_orders':all(set(w['orders'])==ARMS and all(len(o)==6 and set(o)==set(desc) for o in w['orders'].values()) for w in ow),
  'order_capture_has_no_heldout_fields':not contains_heldout(orders),
  'experience_uses_only_other_families':all(w['experience_record_families']==['navigation','recurrence','shape_axis'] for w in ow),
  'target_memo_uses_control_train_rows':all(w['target_memo_training_rows']==6 and w['training_record_families']==['control_kind','navigation','recurrence','shape_axis'] for w in ow),
  'experience_equals_frozen_on_zero_transfer':all(w['orders']['experience_rank']==w['orders']['frozen_rank'] and
    all(t['prior_successes']==t['prior_failures']==0 for t in w['experience_rank_traces'].values()) for w in ow),
  'score_capture_binds_to_exact_order_hash':scores.get('orders_sha256')==sha(ORDERS),
  'heldout_trials_follow_frozen_orders_and_stop_on_success':all(
    all(v['arms'][a]['order']==o['orders'][a] and
      [t['label'] for t in v['arms'][a]['trials']]==o['orders'][a][:len(v['arms'][a]['trials'])] and
      (v['arms'][a]['success']==(v['arms'][a]['trials'][-1]['heldout_utility']>=1.0)) and
      (v['arms'][a]['success'] or len(v['arms'][a]['trials'])==6)
      for a in ARMS) for o,v in zip(ow,sw)),
  'all_arms_solve_heldout_cases':all(all(v['arms'][a]['success'] for a in ARMS) for v in sw),
 }
 outcomes={a:{'first_candidate_passes':sum(w['arms'][a]['first_candidate_utility']>=1 for w in sw),
   'median_attempts':statistics.median(w['arms'][a]['attempts_until_success'] for w in sw),
   'worker_attempts':[w['arms'][a]['attempts_until_success'] for w in sw],
   'median_trial_elapsed_ns':statistics.median(sum(t['trial_elapsed_ns'] for t in w['arms'][a]['trials']) for w in sw)} for a in sorted(ARMS)}
 report={'schema':'FivePolicyControlKindPilotV1Review','orders_sha256':sha(ORDERS),'scores_sha256':sha(SCORES),
  'checks':checks,'passed':sum(checks.values()),'total':len(checks),'valid':all(checks.values()),
  'outcomes':outcomes,'claim_boundary':'one authored lexical task; per-trial timing includes setup/scoring and is not full experiment economics'}
 serialized=json.dumps(report,indent=2,sort_keys=True)+'\n'
 if OUT.exists():
  if OUT.read_text()!=serialized:raise SystemExit('review changed; preserve old output and version the reviewer')
 else:OUT.write_text(serialized)
 print(json.dumps({'passed':report['passed'],'total':report['total'],'valid':report['valid'],'review':OUT.relative_to(ROOT).as_posix()},sort_keys=True))
 return 0 if report['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
