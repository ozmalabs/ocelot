#!/usr/bin/env python3
"""Analyze the locked A8 proposal bridge captures and reconcile costs."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_2_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_2_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_2_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_a8_proposal_bridge_v1_2_analysis_20261002.json'

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def main()->int:
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 errors=[];checks={}
 checks['locked_sources_stable']=lock['sources']==orders['source_before']==orders['source_after']==scores['source_before']==scores['source_after']
 if not checks['locked_sources_stable']:errors.append('lock/source fingerprints differ')
 checks['scores_bind_orders']=scores['orders_sha256']==sha(ORDERS)
 if not checks['scores_bind_orders']:errors.append('scores do not bind to frozen orders')
 ow={int(x['worker']):x for x in orders['workers']};sw={int(x['worker']):x for x in scores['workers']}
 checks['four_complete_workers']=set(ow)==set(range(4)) and set(sw)==set(range(4))
 if not checks['four_complete_workers']:errors.append('worker set incomplete')
 all_graph_pass=[];all_host_pass=[];host_prefix=[];costs=[];worker_rows=[]
 for worker in range(4):
  o=ow[worker];s=sw[worker];proposal=o['prompted_graph_proposal'];no=o['unprompted_graph_proposal']
  if not o['source_stable'] or not s['source_stable']:errors.append(f'worker {worker}: source drift')
  if not proposal['grounded'] or proposal['served_by']!='graph' or not proposal['built']:
   errors.append(f'worker {worker}: prompted graph proposal missing/not graph-served')
  if proposal['kind']!='flip_comparison' or proposal['target']!='hop_descend_gradient':
   errors.append(f'worker {worker}: wrong graph operator or target')
  if not proposal['target_rule_preserved_during_composition']:
   errors.append(f'worker {worker}: target rule mutated during proposal')
  if no['built'] or no['candidate'] is not None:
   errors.append(f'worker {worker}: unprompted path did not abstain')
  desc=o['host_reference_descriptors'];outcomes=s['host_candidate_outcomes']
  if len(desc)!=6 or len(outcomes)!=len(desc):errors.append(f'worker {worker}: host candidate matrix incomplete')
  if [x['digest'] for x in desc]!=[x['digest'] for x in outcomes]:
   errors.append(f'worker {worker}: candidate descriptors and held-out outcomes mismatch')
  if len({x['digest'] for x in outcomes})!=len(outcomes):errors.append(f'worker {worker}: duplicate host candidate digest')
  if any(not x['receipt_verified'] or not x['primary_preserved'] for x in outcomes):
   errors.append(f'worker {worker}: host candidate branch receipt/isolation failure')
  if any(x['oracle_pass']!=all(c.get('pass',False) for c in x['task_cases']) for x in outcomes):
   errors.append(f'worker {worker}: task case/oracle summary mismatch')
  graph=s['prompted_graph_proposal_outcome']
  if not graph or not graph['outcome']['receipt_verified'] or not graph['outcome']['primary_preserved']:
   errors.append(f'worker {worker}: prompted proposal evaluation invalid')
  if graph and graph['digest_match'] is not True:errors.append(f'worker {worker}: graph digest is not in host reference set')
  graphrow=graph['outcome'] if graph else {}
  graph_pass=bool(graphrow.get('utility',0)>=1.0 and graphrow.get('oracle_pass'))
  host_pass=[x for x in outcomes if x['utility']>=1.0]
  fault=s['fault_rule_control'];source=s['source_rule_control']
  if fault['utility']>=1.0 or not fault['receipt_verified'] or not fault['primary_preserved']:
   errors.append(f'worker {worker}: fault control did not fail with a valid isolated receipt')
  if source['utility']<1.0 or not source['receipt_verified'] or not source['primary_preserved']:
   errors.append(f'worker {worker}: source rule control failed or invalid')
  all_graph_pass.append(graph_pass);all_host_pass.append(len(host_pass))
  first=outcomes[0] if outcomes else None
  attempts=next((i+1 for i,x in enumerate(outcomes) if x['utility']>=1.0),len(outcomes))
  host_prefix.append(attempts)
  common=int(o['common_task_context_setup_ns']);enum=int(o['host_candidate_enumeration_ns'])
  graph_trial=int(graphrow.get('cost_ns',{}).get('candidate_trial_ns',0))
  host_trial=sum(int(x['cost_ns']['candidate_trial_ns']) for x in outcomes[:attempts])
  graph_cost=common+int(proposal['composer_total_ns'])+graph_trial
  host_cost=common+enum+host_trial
  costs.append({'worker':worker,'common_task_context_setup_ns':common,'host_candidate_enumeration_ns':enum,
   'graph_composer_total_ns':int(proposal['composer_total_ns']),
   'graph_applicability_precompute_ns':int(proposal['applicability_precompute_ns']),
   'graph_candidate_trial_ns':graph_trial,'host_default_prefix_trial_ns':host_trial,
   'host_exhaustive_audit_trial_ns':sum(int(x['cost_ns']['candidate_trial_ns']) for x in outcomes),
   'graph_prompted_selection_ns':graph_cost,'host_default_selection_ns':host_cost,
   'heldout_reference_context_setup_ns':int(s['heldout_context_setup_ns']),
   'heldout_reference_enumeration_ns':int(s['heldout_reference_enumeration_ns'])})
  worker_rows.append({'worker':worker,'graph_proposal_pass':graph_pass,
   'graph_proposal_digest':proposal['candidate_digest'],'graph_matches_host_candidate':bool(graph and graph['digest_match']),
   'host_candidate_success_labels':[x['label'] for x in outcomes if x['utility']>=1.0],
   'host_default_first_candidate_pass':bool(first and first['utility']>=1.0),
   'host_default_attempts_to_success':attempts,'unprompted_abstained':not no['built']})
 checks['prompted_graph_proposal_passes_heldout']=all(all_graph_pass)
 if not checks['prompted_graph_proposal_passes_heldout']:errors.append('prompted graph proposal failed held-out oracle')
 checks['host_reference_has_success_and_failure']=all(0<n<len(sw[w]['host_candidate_outcomes']) for w,n in enumerate(all_host_pass))
 checks['unprompted_abstention']=all(row['unprompted_abstained'] for row in worker_rows)
 if not checks['unprompted_abstention']:errors.append('unprompted composer did not always abstain')
 checks['cost_ledger_reconciles']=all(row['graph_prompted_selection_ns']==row['common_task_context_setup_ns']+
  row['graph_composer_total_ns']+row['graph_candidate_trial_ns'] and row['host_default_selection_ns']==row['common_task_context_setup_ns']+
  row['host_candidate_enumeration_ns']+row['host_default_prefix_trial_ns'] for row in costs)
 if not checks['cost_ledger_reconciles']:errors.append('selection cost ledger does not reconcile')
 summary={'schema':'ThoughtexperimentA8ProposalBridgeV1_2Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'inputs':{'orders_sha256':sha(ORDERS),'scores_sha256':sha(SCORES),'lock_sha256':sha(LOCK)},
  'checks':checks,'errors':errors,'workers':worker_rows,'costs':costs,
  'aggregate':{'workers':len(worker_rows),'graph_prompted_successes':sum(all_graph_pass),
   'graph_prompted_first_choice_utility':sum(all_graph_pass)/len(all_graph_pass),
   'host_default_successes':sum(1 for x in worker_rows if x['host_default_first_candidate_pass']),
   'host_default_median_attempts':statistics.median(host_prefix),
   'host_candidates_scored':sum(len(sw[w]['host_candidate_outcomes']) for w in sw),
   'host_useful_candidates':sum(all_host_pass),
   'median_graph_prompted_selection_ms':statistics.median(x['graph_prompted_selection_ns'] for x in costs)/1e6,
   'median_host_default_selection_ms':statistics.median(x['host_default_selection_ns'] for x in costs)/1e6,
   'median_host_exhaustive_audit_ms':statistics.median(x['host_exhaustive_audit_trial_ns'] for x in costs)/1e6}}
 OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'checks':checks,'errors':errors,'aggregate':summary['aggregate']},sort_keys=True))
 return 1 if any(not x for x in checks.values()) else 0
if __name__=='__main__':raise SystemExit(main())
