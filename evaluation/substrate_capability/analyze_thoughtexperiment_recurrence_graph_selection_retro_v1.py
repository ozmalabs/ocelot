#!/usr/bin/env python3
"""Independent audit of retrospective recurrence graph-selection transfer."""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
raw=json.loads((ROOT/'evaluation/reports/thoughtexperiment_recurrence_graph_selection_retro_v1_20261002.json').read_text())
source=json.loads((ROOT/'evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json').read_text())
by_worker={w['worker']:w for w in source['workers']};rows=raw['workers']
checks={
 'explicitly_retrospective_input':raw['retrospective_known_data'] is True,
 'three_complete_worker_replays':len(rows)==3 and all(r['candidate_count']==8 and r['training_probe_count']==6 for r in rows),
 'unique_graph_term_winner_matches_training_max':all(r['decision'].get('ok') and r['decision'].get('matching_evidence_count')==max(r['training_matches_by_digest'].values())==6 and sum(v==6 for v in r['training_matches_by_digest'].values())==1 for r in rows),
 'all_winners_are_recurrence_dedup_candidate':all(r['selected_label']=='dedup_identity_fix' for r in rows),
 'winner_passes_all_heldout_episodes':all(r['heldout_matches_by_digest'][r['decision']['proposal_id']]==6 for r in rows),
 'other_candidates_do_not_match_train_max':all(all(v<6 for k,v in r['training_matches_by_digest'].items() if k!=r['decision']['proposal_id']) for r in rows),
 'other_candidates_fail_some_heldouts':all(all(r['heldout_matches_by_digest'][k]<6 for k in r['heldout_matches_by_digest'] if k!=r['decision']['proposal_id']) for r in rows),
 'train_heldout_keys_disjoint':all(not (set(r['recurrence_keys_train'])&set(r['recurrence_keys_heldout'])) for r in rows),
 'primary_isolation_and_residual_return':all(r['primary_rule_set_unchanged'] and r['primary_candidate_nodes_absent'] and r['residual_returned'] for r in rows),
 'raw_capture_workers_match':all(r['worker'] in by_worker for r in rows),
}
out={'schema':'RecurrenceGraphSelectionRetrospectiveV1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
 'mean_graph_selection_ms':statistics.mean(r['decision_ns'] for r in rows)/1e6,
 'scope':'Retrospective scorer/API transfer over previously published recurrence training evidence; held-out outcomes are reported only after graph-Term selection but were already visible in the source capture.'}
print(json.dumps(out,indent=2,sort_keys=True))
if not out['all_checks_pass']:raise SystemExit(1)
