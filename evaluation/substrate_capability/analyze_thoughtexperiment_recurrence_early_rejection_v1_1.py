#!/usr/bin/env python3
"""Independent paired-outcome and work-budget review."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_early_rejection_v1_orders_20261002.json'
SP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_early_rejection_v1_scores_20261002.json'
LP=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_early_rejection_v1_lock_20261002.json'
orders=json.loads(OP.read_text());scores=json.loads(SP.read_text());ow=orders['workers'];sw=scores['workers'];held={w['worker']:w for w in sw}
def good(o):return o.get('offer_counts')==[1,1] and o.get('fixedpoint_progress')==0 and len(o.get('recurrence_keys',[]))==2
train_pairs=[];held_pairs=[]
for w in ow:
 for pid,rows in w['baseline_training'].items():
  for b,r in zip(rows,w['bounded_training'][pid]):train_pairs.append((w['worker'],pid,b['outcome'],r['outcome']))
for w in sw:
 for pid,rows in w['heldout'].items():
  for row in rows:held_pairs.append((w['worker'],pid,row['baseline'],row['bounded']))
pairs=train_pairs+held_pairs
checks={
 'four_workers_eight_candidates':len(ow)==4 and len(sw)==4 and all(len(w['descriptors'])==8 for w in ow),
 'candidate_descriptors_stable_across_workers':all(w['descriptors']==ow[0]['descriptors'] for w in ow),
 'four_train_and_heldout_samples_per_candidate':all(all(len(v)==4 for v in w['baseline_training'].values()) and all(len(v)==4 for v in w['bounded_training'].values()) for w in ow) and all(all(len(v)==4 for v in w['heldout'].values()) for w in sw),
 'orders_exclude_heldout_data':all('heldout_' not in json.dumps(w) for w in ow),
 'all_256_paired_episode_outcomes_match':len(train_pairs)==len(held_pairs)==128 and all(good(b)==good(r) for _,_,b,r in pairs),
 'same_candidate_keyed_inputs_in_pairs':all(b.get('recurrence_keys')==r.get('recurrence_keys') for _,_,b,r in pairs),
 'baseline_and_bounded_choose_same_unique_repair':all(w['decisions']['baseline'].get('ok') and w['decisions']['bounded'].get('ok') and w['decisions']['baseline']['proposal_id']==w['decisions']['bounded']['proposal_id'] and w['decisions']['bounded']['matching_evidence_count']==4 for w in ow),
 'selected_repair_is_dedup_and_passes_all_splits':all(next(d['proposal_label'] for d in w['descriptors'] if d['proposal_id']==w['decisions']['bounded']['proposal_id'])=='dedup_identity_fix' and all(good(x['outcome']) for x in w['bounded_training'][w['decisions']['bounded']['proposal_id']]) and all(good(x['bounded']) for x in held[w['worker']]['heldout'][w['decisions']['bounded']['proposal_id']]) for w in ow),
 'selected_candidate_never_budget_rejected':all(all(x['outcome']['bounded_status']=='fixedpoint' for x in w['bounded_training'][w['decisions']['bounded']['proposal_id']]) and all(x['bounded']['bounded_status']=='fixedpoint' for x in held[w['worker']]['heldout'][w['decisions']['bounded']['proposal_id']]) for w in ow),
 'bounded_stage_work_never_exceeds_200':all(max(r['bounded_work_by_stage'].values(),default=0)<=200 for _,_,_,r in pairs),
 'first_stage_caps_reject_before_second_candidate':all(r['capped_stage']!='first_candidate' or (not r['second_candidate_sweeps'] and r['budget_exhausted_by_stage']['first_candidate']) for _,_,_,r in pairs),
 'primary_state_and_residual_contract':all(w['primary_rules_unchanged'] and w['primary_candidate_evidence_absent'] and w['residual_returned'] for w in ow),
 'source_hashes_stable_across_stages':all(w['source_stable'] and w['source_before']==w['source_after']==held[w['worker']]['source_before']==held[w['worker']]['source_after'] for w in ow) and all(w['source_stable'] for w in sw),
 'order_lock_score_chain_valid':orders['lock_sha256']==hashlib.sha256(LP.read_bytes()).hexdigest() and scores['orders_sha256']==hashlib.sha256(OP.read_bytes()).hexdigest(),
}
caps={'baseline_training':sum(b.get('fixedpoint_progress',0)>=100 for _,_,b,_ in train_pairs),
 'bounded_training':sum(r.get('bounded_status')=='work_budget_exhausted' for _,_,_,r in train_pairs),
 'baseline_heldout':sum(b.get('fixedpoint_progress',0)>=100 for _,_,b,_ in held_pairs),
 'bounded_heldout':sum(r.get('bounded_status')=='work_budget_exhausted' for _,_,_,r in held_pairs)}
baseline_ns=sum(w['baseline_training_runtime_ns']+held[w['worker']]['baseline_heldout_runtime_ns'] for w in ow)
bounded_ns=sum(w['bounded_training_runtime_ns']+held[w['worker']]['bounded_heldout_runtime_ns'] for w in ow)
cost={'paired_candidate_episodes':len(pairs),'baseline_total_runtime_ms':baseline_ns/1e6,'bounded_total_runtime_ms':bounded_ns/1e6,
 'measured_runtime_ratio_baseline_over_bounded':baseline_ns/bounded_ns if bounded_ns else None,
 'mean_candidate_enumeration_ms':statistics.mean(w['candidate_enumeration_ns'] for w in ow)/1e6,
 'mean_graph_decision_ms_baseline':statistics.mean(w['decision_ns']['baseline'] for w in ow)/1e6,
 'mean_graph_decision_ms_bounded':statistics.mean(w['decision_ns']['bounded'] for w in ow)/1e6,
 'mean_baseline_episode_ms':baseline_ns/len(pairs)/1e6,'mean_bounded_episode_ms':bounded_ns/len(pairs)/1e6}
out={'schema':'RecurrenceEarlyRejectionV1Analysis','checks':checks,'selection_and_semantic_gates_pass':all(checks.values()),
 'baseline_and_bounded_cap_counts':caps,'cost_summary':cost,
 'scope':'Paired current-versus-early-rejection candidate evaluation; recurrence task, candidates, predictions, and oracle remain authored/host-generated.'}
dest=ROOT/'evaluation/reports/thoughtexperiment_recurrence_early_rejection_v1_1_analysis_20261002.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if not out['selection_and_semantic_gates_pass']:raise SystemExit(1)
