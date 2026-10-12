#!/usr/bin/env python3
"""Amended review with source-correct per-worker recurrence split counts."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
raw_path=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_retro_v1_20261002.json'
source_path=ROOT/'evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json'
lock_path=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_graph_selection_retro_v1_lock_20261002.json'
raw=json.loads(raw_path.read_text());source=json.loads(source_path.read_text())
lock=json.loads(lock_path.read_text())
by_worker={w['worker']:w for w in source['workers']};rows=raw['workers']
checks={
 'retrospective_scope_disclosed':raw['retrospective_known_data'] is True,
 'three_replays_use_two_train_and_heldout_each':len(rows)==3 and all(r['candidate_count']==8 and r['training_probe_count']==2 and len(r['recurrence_keys_heldout'])==2 for r in rows),
 'unique_graph_winner_is_training_max':all(r['decision'].get('ok') and r['decision'].get('matching_evidence_count')==max(r['training_matches_by_digest'].values())==2 and sum(v==2 for v in r['training_matches_by_digest'].values())==1 for r in rows),
 'all_winners_are_dedup_identity_fix':all(r['selected_label']=='dedup_identity_fix' for r in rows),
 'winner_passes_two_heldouts_per_replay':all(r['heldout_matches_by_digest'][r['decision']['proposal_id']]==2 for r in rows),
 'other_candidates_do_not_match_training_max':all(all(v<2 for k,v in r['training_matches_by_digest'].items() if k!=r['decision']['proposal_id']) for r in rows),
 'other_candidates_fail_a_heldout_each':all(all(r['heldout_matches_by_digest'][k]<2 for k in r['heldout_matches_by_digest'] if k!=r['decision']['proposal_id']) for r in rows),
 'train_and_heldout_keys_disjoint':all(not(set(r['recurrence_keys_train'])&set(r['recurrence_keys_heldout'])) for r in rows),
 'primary_has_only_compact_residual':all(r['primary_rule_set_unchanged'] and r['primary_candidate_nodes_absent'] and r['residual_returned'] for r in rows),
 'input_capture_and_worker_identity_bind':raw['input_raw_sha256']==hashlib.sha256(source_path.read_bytes()).hexdigest() and all(r['worker'] in by_worker for r in rows),
 'replay_lock_and_input_hash_bind':raw['lock_sha256']==hashlib.sha256(lock_path.read_bytes()).hexdigest() and lock['sources'].get(str(source_path.relative_to(ROOT)))==hashlib.sha256(source_path.read_bytes()).hexdigest(),
}
out={'schema':'RecurrenceGraphSelectionRetrospectiveV1_1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
 'literal_preregistered_gate_passed':False,
 'mean_graph_selection_ms':statistics.mean(r['decision_ns'] for r in rows)/1e6,
 'scope':'Retrospective API-transfer replay, two train and two held-out episodes per worker. Not an independent or blinded recurrence experiment.'}
out_path=ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_retro_v1_1_analysis_20261002.json'
out_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
if not out['all_checks_pass']:raise SystemExit(1)
