#!/usr/bin/env python3
"""Independent gates and cost reconciliation for the quanta-route A8 transfer."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_a8_quanta_route_transfer_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_a8_quanta_route_transfer_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_a8_quanta_route_transfer_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_a8_quanta_route_transfer_v1_analysis_20261002.json'
CASES=('H1_vertical_portal','H2_horizontal_portal')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def _valid(row):
 return bool(row.get('passed') and row.get('reached_goal') and row.get('wall_hits')==0
  and row.get('crossed_opening') and row.get('steps',99)<=16 and row.get('closed')==0.0
  and row.get('minted_hypotheses')==0 and row.get('receipt_verified')
  and row.get('primary_preserved'))
def _trial_ns(rows):
 return sum(int(r.get('branch_creation_ns',0))+int(r.get('candidate_patch_ns',0))+
  int(r.get('task_elapsed_ns',0)) for r in rows)

def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 errors=[];checks={}
 checks['locked_sources_stable']=lock['sources']==orders['source_before']==orders['source_after']==scores['source_before']==scores['source_after']
 if not checks['locked_sources_stable']:errors.append('lock/source fingerprints differ')
 checks['scores_bind_orders']=scores['orders_sha256']==sha(ORDERS)
 if not checks['scores_bind_orders']:errors.append('score capture does not bind frozen orders')
 ow={int(x['worker']):x for x in orders['workers']};sw={int(x['worker']):x for x in scores['workers']}
 checks['four_complete_workers']=set(ow)==set(range(4)) and set(sw)==set(range(4))
 if not checks['four_complete_workers']:errors.append('worker set incomplete')
 checks['orders_blind_to_heldout']=all(not any(k in row for k in ('outcomes','utility','passed','heldout_scores')) for row in orders['workers'])
 if not checks['orders_blind_to_heldout']:errors.append('order stage contains held-out outcomes')
 graph_pass=[];host_pass=[];costs=[];worker_rows=[]
 for worker in range(4):
  o=ow[worker];s=sw[worker];p=o['prompted'];n=o['unprompted']
  if not o['source_stable'] or not s['source_stable']:errors.append(f'worker {worker}: source drift')
  prompt_ok=p.get('served_by')=='graph' and p.get('built') and p.get('kind')=='flip_comparison' and p.get('target')=='qf_hop_route' and p.get('target_rule_preserved')
  no_ok=n.get('served_by')=='graph' and not n.get('built') and n.get('candidate') is None
  if not prompt_ok:errors.append(f'worker {worker}: prompted graph target/operator gate failed')
  if not no_ok:errors.append(f'worker {worker}: no-cue graph abstention gate failed')
  host=s['host_outcomes'];desc=o['host_descriptors']
  if len(host)!=len(desc) or len(host)<2:errors.append(f'worker {worker}: incomplete host candidate outcomes')
  if [x['semantic_digest'] for x in host]!=[x['semantic_digest'] for x in desc]:errors.append(f'worker {worker}: host candidate order/digest mismatch')
  for outcome in host:
   if tuple(x.get('case') for x in outcome['cases'])!=CASES:errors.append(f'worker {worker}: held-out case set mismatch for {outcome["label"]}')
   if not all(_valid(row) for row in outcome['cases']):
    if outcome['utility']:errors.append(f'worker {worker}: candidate utility summary inconsistent')
   if any(not row.get('receipt_verified') or not row.get('primary_preserved') for row in outcome['cases']):errors.append(f'worker {worker}: candidate receipt/isolation failure')
  graph=s['graph_outcome'];gout=graph['outcome'] if graph else {}
  flip=next((x for x in host if x['label']=='flip_comparison'),None)
  sem_match=bool(flip and p.get('candidate') and p['candidate'].get('rules',{}).get('qf_hop_route')
   and graph and graph.get('semantic_digest_match') and gout.get('semantic_digest')==flip.get('semantic_digest'))
  if not sem_match:errors.append(f'worker {worker}: graph proposal semantic identity mismatch')
  gp=bool(gout.get('utility') and all(_valid(x) for x in gout.get('cases',[])))
  if not graph or tuple(x.get('case') for x in gout.get('cases',[]))!=CASES:errors.append(f'worker {worker}: graph held-out matrix incomplete')
  graph_pass.append(gp);successes=[x for x in host if x.get('utility') and all(_valid(row) for row in x.get('cases',[]))]
  host_pass.append(len(successes))
  for control_name,expected in (('source_control',True),('fault_control',False)):
   control=s[control_name]
   if len(control)!=2:errors.append(f'worker {worker}: {control_name} case matrix incomplete')
   if any(not x.get('receipt_verified') or not x.get('primary_preserved') for x in control):errors.append(f'worker {worker}: {control_name} receipt/isolation failure')
   if expected and not all(_valid(x) for x in control):errors.append(f'worker {worker}: source control did not pass both worlds')
   if not expected and all(_valid(x) for x in control):errors.append(f'worker {worker}: fault control unexpectedly passed both worlds')
  first=next((i+1 for i,x in enumerate(host) if x.get('utility') and all(_valid(row) for row in x['cases'])),len(host))
  graph_trial=_trial_ns(gout.get('cases',[]));host_trial=sum(_trial_ns(x['cases']) for x in host[:first])
  common=int(o['common_setup_ns']);enum=int(o['host_enumeration_ns'])
  graph_cost=common+int(p.get('composer_ns',0))+graph_trial
  host_cost=common+enum+host_trial
  costs.append({'worker':worker,'common_setup_ns':common,'host_enumeration_ns':enum,
   'graph_composer_ns':int(p.get('composer_ns',0)),'graph_candidate_trials_ns':graph_trial,
   'host_default_prefix_trials_ns':host_trial,'host_exhaustive_trials_ns':sum(_trial_ns(x['cases']) for x in host),
   'graph_selection_ns':graph_cost,'host_default_selection_ns':host_cost,
   'heldout_world_setup_ns':sum(int(x.get('common_case_setup_ns',0)) for x in (host[0]['cases'] if host else []))})
  worker_rows.append({'worker':worker,'graph_proposal_pass':gp,'semantic_digest_match':sem_match,
   'host_success_labels':[x['label'] for x in successes],'host_default_first_candidate_pass':bool(host and host[0].get('utility')),
   'host_default_attempts_to_success':first,'unprompted_abstained':no_ok,
   'graph_case_results':gout.get('cases',[])})
 checks['prompted_graph_proposal_passes_both_worlds']=all(graph_pass)
 if not checks['prompted_graph_proposal_passes_both_worlds']:errors.append('prompted graph proposal did not pass both portal worlds in every worker')
 checks['semantic_candidate_identity']=all(x['semantic_digest_match'] for x in worker_rows)
 checks['host_candidates_have_success_and_failure']=all(0<n<len(ow[w]['host_candidates']) for w,n in enumerate(host_pass))
 if not checks['host_candidates_have_success_and_failure']:errors.append('host candidate set lacks success/failure contrast')
 checks['source_fault_controls_discriminate']=all(all(_valid(r) for r in sw[w]['source_control']) and not all(_valid(r) for r in sw[w]['fault_control']) for w in sw)
 checks['unprompted_graph_abstention']=all(x['unprompted_abstained'] for x in worker_rows)
 checks['cost_ledger_reconciles']=all(x['graph_selection_ns']==x['common_setup_ns']+x['graph_composer_ns']+x['graph_candidate_trials_ns'] and x['host_default_selection_ns']==x['common_setup_ns']+x['host_enumeration_ns']+x['host_default_prefix_trials_ns'] for x in costs)
 if not checks['cost_ledger_reconciles']:errors.append('selection-cost ledger mismatch')
 summary={'schema':'ThoughtexperimentA8QuantaRouteTransferV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'inputs':{'lock_sha256':sha(LOCK),'orders_sha256':sha(ORDERS),'scores_sha256':sha(SCORES)},
  'checks':checks,'errors':errors,'workers':worker_rows,'costs':costs,
  'aggregate':{'workers':len(worker_rows),'graph_passes':sum(graph_pass),'host_useful_candidates':sum(host_pass),
   'host_candidates_scored':sum(len(sw[w]['host_outcomes']) for w in sw),
   'median_graph_selection_ms':statistics.median(x['graph_selection_ns'] for x in costs)/1e6,
   'median_host_default_selection_ms':statistics.median(x['host_default_selection_ns'] for x in costs)/1e6,
   'median_host_exhaustive_trials_ms':statistics.median(x['host_exhaustive_trials_ns'] for x in costs)/1e6}}
 OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'checks':checks,'errors':errors,'aggregate':summary['aggregate']},sort_keys=True))
 return 1 if any(not value for value in checks.values()) else 0
if __name__=='__main__':raise SystemExit(main())
