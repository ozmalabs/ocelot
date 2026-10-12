#!/usr/bin/env python3
"""Independent review of prospective recurrence graph-selection panel."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_v1_1_orders_20261002.json'
SP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_v1_1_scores_20261002.json'
LP=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_graph_selection_v1_1_lock_20261002.json'
orders=json.loads(OP.read_text());scores=json.loads(SP.read_text());lock=json.loads(LP.read_text())
ow=orders['workers'];sw=scores['workers'];held={w['worker']:w for w in sw}
def correct(o):return o.get('offer_counts')==[1,1] and o.get('fixedpoint_progress')==0 and len(o.get('recurrence_keys',[]))==2
def all_training(r):return [x for vals in r['training'].values() for x in vals]
checks={
 'four_complete_workers_and_all_candidates':len(ow)==4 and len(sw)==4 and all(len(w['candidate_descriptors'])==8 for w in ow),
 'candidate_descriptors_identical_across_workers':all(w['candidate_descriptors']==ow[0]['candidate_descriptors'] for w in ow),
 'four_training_episodes_per_candidate_worker':all(all(len(v)==4 for v in w['training'].values()) for w in ow),
 'orders_contain_training_only':all(all('heldout' not in row for row in all_training(w)) for w in ow),
 'episode_oracle_recomputed_from_offer_counts':all(x['outcome']['oracle_correct']==correct(x['outcome']) for w in ow for x in all_training(w)),
 'unique_graph_term_winner_matches_training_max':all(w['decision'].get('ok') and w['decision'].get('matching_evidence_count')==4 and sum(sum(correct(x['outcome']) for x in vals)==4 for vals in w['training'].values())==1 for w in ow),
 'all_winners_are_dedup_identity_fix':all(next(d['proposal_label'] for d in w['candidate_descriptors'] if d['proposal_id']==w['decision']['proposal_id'])=='dedup_identity_fix' for w in ow),
 'selected_proposals_pass_four_heldout_episodes':all(all(correct(x['outcome']) for x in held[w['worker']]['heldout'][w['decision']['proposal_id']]) for w in ow),
 'alternatives_below_train_max_and_fail_heldouts':all(all(sum(correct(x['outcome']) for x in w['training'][pid])<4 and any(not correct(x['outcome']) for x in held[w['worker']]['heldout'][pid]) for pid in w['training'] if pid!=w['decision']['proposal_id']) for w in ow),
 'train_heldout_keys_disjoint':all(not(set(w['training_recurrence_keys'])&set(held[w['worker']]['heldout_recurrence_keys'])) for w in ow),
 'each_episode_has_two_due_keys':all(len(x['outcome']['recurrence_keys'])==2 for w in ow for x in all_training(w)) and all(len(x['outcome']['recurrence_keys'])==2 for w in sw for vals in w['heldout'].values() for x in vals),
 'primary_isolation_and_residual_return':all(w['primary_rules_unchanged'] and w['primary_candidate_evidence_absent'] and w['residual_returned'] for w in ow),
 'all_fixed_points_valid':all(x['outcome']['fixedpoint_progress']==0 for w in ow for x in all_training(w) if x['outcome']['oracle_correct']) and all(x['outcome']['fixedpoint_progress']==0 for w in sw for vals in w['heldout'].values() for x in vals),
 'source_hashes_stable_across_stages':all(w['source_stable'] and w['source_before']==w['source_after']==held[w['worker']]['source_before']==held[w['worker']]['source_after'] for w in ow) and all(w['source_stable'] for w in sw),
 'order_lock_and_score_chain_valid':orders['lock_sha256']==hashlib.sha256(LP.read_bytes()).hexdigest() and scores['orders_sha256']==hashlib.sha256(OP.read_bytes()).hexdigest(),
}
cost={'mean_candidate_enumeration_ms':statistics.mean(w['enumeration_ns'] for w in ow)/1e6,
 'mean_training_episode_runtime_ms':statistics.mean(w['training_episode_runtime_ns'] for w in ow)/(4*8*4)/1e6,
 'mean_graph_term_selection_ms':statistics.mean(w['decision_ns'] for w in ow)/1e6,
 'mean_heldout_episode_runtime_ms':statistics.mean(w['heldout_episode_runtime_ns'] for w in sw)/(4*8*4)/1e6,
 'train_candidate_episodes':sum(len(all_training(w)) for w in ow),'heldout_candidate_episodes':sum(sum(len(v) for v in w['heldout'].values()) for w in sw)}
out={'schema':'RecurrenceGraphSelectionV1_1Analysis','checks':checks,'all_checks_pass':all(checks.values()),'cost_summary':cost,
 'sample_unit':'One fresh recurrence episode contains two separately keyed due candidates.',
 'scope':'Prospective source-locked four-worker recurrence candidate selection: four train and four held-out episodes per candidate and worker; host generates candidates and task oracle.'}
dest=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_v1_1_analysis_20261002.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if not out['all_checks_pass']:raise SystemExit(1)
