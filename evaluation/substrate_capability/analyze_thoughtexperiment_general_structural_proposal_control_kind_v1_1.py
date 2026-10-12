#!/usr/bin/env python3
"""Independent integrity and held-out analysis for general-rule A8 v1."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_general_structural_proposal_control_kind_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_control_kind_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_control_kind_v1_1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_control_kind_v1_1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def good(row):return bool(row and row.get('utility')==1.0 and row.get('receipt_verified') and row.get('primary_preserved'))
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text());errors=[];checks={}
 checks['lock_orders_score_source_stability']=all(w.get('source_stable') and w.get('source_before')==lock['sources']==w.get('source_after') for w in orders['workers']+scores['workers'])
 if not checks['lock_orders_score_source_stability']:errors.append('source lock mismatch or unstable workers')
 checks['score_binds_orders']=scores['orders_sha256']==sha(ORDERS)
 if not checks['score_binds_orders']:errors.append('scores do not bind frozen orders')
 ow={int(x['worker']):x for x in orders['workers']};sw={int(x['worker']):x for x in scores['workers']}
 checks['four_workers_complete']=set(ow)==set(range(4)) and set(sw)==set(range(4))
 if not checks['four_workers_complete']:errors.append('worker set incomplete')
 checks['orders_outcome_blind']=all(not any(k in json.dumps(row) for k in ('utility','heldout_score','proposal_outcome')) for row in orders['workers'])
 if not checks['orders_outcome_blind']:errors.append('order capture contains held-out outcome')
 target_operator=[];proposal_pass=[];source_pass=[];fault_fail=[];contrast=[];host_success=[];costs=[]
 for i in range(4):
  order=ow[i];score=sw[i];p=order['prompted'];n=order['unprompted'];so=score['proposal_outcome']
  target_operator.append(p.get('dispatch_path')=='compose_experiment_rule' and p.get('dispatch_served_by')=='python' and p.get('target')=='classify_kind_family' and p.get('operator')=='flip_comparison' and p.get('candidate') is not None and p.get('target_preserved') and p.get('candidate_host_reference_match') is not None)
  if not target_operator[-1]:errors.append(f'worker {i}: prompted target/operator/reference gate failed')
  if n.get('candidate') is not None or n.get('grounded'):errors.append(f'worker {i}: unprompted path failed to abstain')
  proposal_pass.append(good(so))
  if not proposal_pass[-1]:errors.append(f'worker {i}: proposal failed held-out utility/receipt/isolation')
  source_pass.append(good(score['source_control']));fault_fail.append(not good(score['fault_control']))
  if not source_pass[-1] or not fault_fail[-1]:errors.append(f'worker {i}: source/fault controls do not discriminate')
  outcomes=score['host_candidate_outcomes'];host_success.append(sum(x.get('utility')==1.0 for x in outcomes))
  if len(outcomes)!=len(p['host_reference_descriptors']) or not 0<host_success[-1]<len(outcomes):errors.append(f'worker {i}: incomplete or uninformative host candidate set')
  if any(not x.get('receipt_verified') or not x.get('primary_preserved') for x in outcomes):errors.append(f'worker {i}: host branch receipt or isolation failure')
  costs.append({'worker':i,'proposal_decision_ns':p['graph_decision_ns'],'host_candidate_enumeration_ns':p['host_enumeration_ns'],
   'task_context_setup_ns':p['task_context_setup_ns'],'proposal_branch_trial_ns':sum(so.get('cost_ns',{}).values()) if so else None,
   'host_candidate_count':len(outcomes),'host_useful_count':host_success[-1]})
 checks['prompted_graph_target_operator_and_reference_match']=all(target_operator)
 checks['unprompted_graph_abstention']=all(not ow[i]['unprompted']['grounded'] and ow[i]['unprompted']['candidate'] is None for i in ow)
 checks['proposal_heldout_utility_receipt_isolation']=all(proposal_pass)
 checks['source_fault_controls_discriminate']=all(source_pass) and all(fault_fail)
 checks['host_reference_has_success_and_failure']=all(0<n<len(ow[i]['prompted']['host_reference_candidates']) for i,n in enumerate(host_success))
 checks['host_receipts_and_primary_isolation']=all(all(x.get('receipt_verified') and x.get('primary_preserved') for x in sw[i]['host_candidate_outcomes']) for i in sw)
 summary={'schema':'GeneralStructuralProposalControlKindV1_1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'inputs':{'lock_sha256':sha(LOCK),'orders_sha256':sha(ORDERS),'scores_sha256':sha(SCORES)},'checks':checks,'errors':errors,'costs':costs,
  'aggregate':{'workers':len(sw),'graph_proposals_heldout_pass':sum(proposal_pass),'source_controls_pass':sum(source_pass),
   'fault_controls_expected_failures':sum(fault_fail),'host_candidates':sum(len(sw[i]['host_candidate_outcomes']) for i in sw),
   'median_graph_decision_ms':statistics.median(x['proposal_decision_ns'] for x in costs)/1e6,
   'median_host_enumeration_ms':statistics.median(x['host_candidate_enumeration_ns'] for x in costs)/1e6}}
 OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'checks':checks,'errors':errors,'aggregate':summary['aggregate']},sort_keys=True))
 return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
