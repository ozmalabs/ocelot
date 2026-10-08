#!/usr/bin/env python3
"""Independent gate analysis for recurrence budget calibration v1."""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_budget_calibration_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def finite_tree(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,dict):return all(finite_tree(v) for v in x.values())
 if isinstance(x,list):return all(finite_tree(v) for v in x)
 return True
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 assert orders['lock_sha256']==sha(LOCK),'order/lock mismatch'
 assert scores['orders_sha256']==sha(ORDERS),'score/order mismatch'
 assert len(orders['workers'])==4 and len(scores['workers'])==4,'worker count mismatch'
 score_by={w['worker']:w for w in scores['workers']}; summaries={};checks={
  'chain_integrity':True,'source_lock':True,'four_workers':True,'training_decisions_unique':True,
  'selected_candidate_heldout_success':True,'paired_inputs_identical':True,
  'all_candidate_records_present':True,'finite_measurements':True,'rule_definition_stable':True,
  'fresh_generator_not_old_builder':True,'tie_and_all_wrong_abstain':True,
  'useful_candidate_false_rejections_absent':True}
 for rel,digest in lock['sources'].items():
  if rel=='loaded_native_binary':continue
  p=ROOT/rel
  if not p.exists() or sha(p)!=digest:checks['source_lock']=False
 from substrate_rs import _native
 if sha(Path(_native.__file__).resolve())!=lock['sources'].get('loaded_native_binary'):checks['source_lock']=False
 for worker,score in score_by.items():
  order=next((x for x in orders['workers'] if x['worker']==worker),None)
  if order is None or not order.get('source_stable') or not score.get('source_stable'):checks['source_lock']=False
  for arity_s,training in order['training'].items():
   arity=int(arity_s); held=score['heldout'][arity_s]
   expected_ids={d['candidate_id'] for d in training['descriptors']}
   for control in ('all_wrong','tie'):
    dec=training['controls'].get(control,{})
    if dec.get('ok') is True:checks['tie_and_all_wrong_abstain']=False
   arms=['reference']+[f'budget_{b}' for b in lock['budgets']]
   ref_winners={}
   for arm in arms:
    tr=training['arms'][arm]
    if set(tr['outcomes'])!=expected_ids:checks['all_candidate_records_present']=False
    if tr['decision'].get('ok') is not True or tr['decision'].get('proposal_id') not in expected_ids:
     checks['training_decisions_unique']=False
    else:ref_winners[arm]=tr['decision']['proposal_id']
    for cid,rows in tr['outcomes'].items():
     if len(rows)!=2:checks['all_candidate_records_present']=False
     for r in rows:
      if not r.get('primary_rules_unchanged'):checks['rule_definition_stable']=False
      if not finite_tree(r):checks['finite_measurements']=False
   baseline_winner=ref_winners.get('reference')
   for arm in arms[1:]:
    if ref_winners.get(arm)!=baseline_winner:checks['training_decisions_unique']=False
   useful=set()
   for cid,rows in training['arms']['reference']['outcomes'].items():
    if any(r['oracle_correct'] for r in rows):useful.add(cid)
   if baseline_winner not in useful:checks['training_decisions_unique']=False
   budget_summary={}
   for arm in arms:
    hrows=held['arms'][arm]
    if set(hrows)!=expected_ids:checks['all_candidate_records_present']=False
    if any(len(v)!=2 for v in hrows.values()):checks['all_candidate_records_present']=False
    if arm!='reference':
     selected=ref_winners.get(arm)
     if selected is None or not all(r['oracle_correct'] and r['fixedpoint'] for r in hrows.get(selected,[])):
      checks['selected_candidate_heldout_success']=False
    false_rejects=0;reference_resolved=0;budget_rejected=0;work=runtime=[]
    for cid,rows in hrows.items():
     for r in rows:
      if not r.get('primary_rules_unchanged'):checks['rule_definition_stable']=False
      if not finite_tree(r):checks['finite_measurements']=False
      if r.get('budget_rejected_stage') is not None:budget_rejected+=1
      work.append(r.get('work_units',0));runtime.append(r.get('runtime_ns',0))
      if arm!='reference':
       rr=hrows[cid]
       # The reference is a separate arm. Resolve by the same candidate/sample row.
       # Filled below from the reference arm to avoid interpreting a cap as termination.
    for cid in expected_ids:
     ref_rows=held['arms']['reference'][cid]
     rows=hrows[cid]
     for ref_r,b_r in zip(ref_rows,rows):
      if ref_r['oracle_correct']:
       reference_resolved+=1
       if not b_r['oracle_correct']:false_rejects+=1
    budget_summary[arm]={'episodes':sum(len(v) for v in hrows.values()),
     'budget_rejections':budget_rejected,'reference_resolved_episodes':reference_resolved,
     'false_rejections':false_rejects,'median_work_units':sorted(work)[len(work)//2] if work else 0,
     'median_runtime_ns':sorted(runtime)[len(runtime)//2] if runtime else 0}
    if arm!='reference' and false_rejects:
     checks['useful_candidate_false_rejections_absent']=False
   # Same deterministic task specs must be used across candidate and budget arms.
   for sample in range(2):
    digests=[]
    for arm in arms:
     for cid in expected_ids:
      rows=(training['arms'][arm]['outcomes'][cid] if arm in training['arms'] else [])
      if rows: digests.append(rows[sample]['input_digest'])
    # All candidates are scored against the same generated input per sample.
    if digests and len(set(digests))!=1:checks['paired_inputs_identical']=False
    held_digests=[]
    for arm in arms:
     for cid in expected_ids:
      held_digests.append(held['arms'][arm][cid][sample]['input_digest'])
    if len(set(held_digests))!=1:checks['paired_inputs_identical']=False
   summaries[f'w{worker}_arity{arity}']=budget_summary
 # The graph builder has its own code and explicitly refuses legacy episode-builder imports.
 runner=(ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_budget_calibration_v1.py').read_text()
 if 'thoughtexperiment_recurrence_candidate_admission_v1 import' in runner or 'early_rejection_v1 import' in runner:
  checks['fresh_generator_not_old_builder']=False
 analysis={'schema':'RecurrenceBudgetCalibrationV1Analysis','checks':checks,'passed_checks':sum(checks.values()),
  'check_count':len(checks),'all_checks_pass':all(checks.values()),'cells':summaries,
  'interpretation':'Budget rejection is censored work; false rejection is measured only when the paired reference reaches the oracle and fixed point.'}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_checks_pass':analysis['all_checks_pass'],'passed_checks':analysis['passed_checks'],'check_count':analysis['check_count'],'analysis':str(OUT)},indent=2))
 return 0 if analysis['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
