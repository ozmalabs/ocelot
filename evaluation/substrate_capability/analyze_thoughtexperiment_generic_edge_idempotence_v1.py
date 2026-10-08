#!/usr/bin/env python3
"""Independent analysis for generic emitted-edge idempotence hypotheses."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_generic_edge_idempotence_v1 as runner
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_generic_edge_idempotence_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_generic_edge_idempotence_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 om={int(x['worker']):x for x in orders['workers']};sm={int(x['worker']):x for x in scores['workers']};ids=set(range(lock['workers']))
 joined=[(om[i],sm[i]) for i in sorted(ids & om.keys() & sm.keys())]
 def train_counts(row):return {x['proposal_id']:sum(bool(r['correct']) for r in x['rows']) for x in row['outcomes']}
 checks={
  'exact_worker_schedule':set(om)==ids and set(sm)==ids and len(orders['workers'])==len(ids) and len(scores['workers'])==len(ids),
  'capture_hash_linkage':orders.get('lock_sha256')==sha(LOCK) and scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS),
  'source_lock_current':runner.frozen()==lock['sources'],
  'source_stable_in_all_workers':all(a['source_before']==lock['sources']==a['source_after']==b['source_before']==b['source_after'] for a,b in joined),
  'exact_generated_surface_no_specialized_candidate':all(len(a['descriptors'])==4 and len({d['proposal_id'] for d in a['descriptors']})==4 and sum(d['label'].startswith('edge_once:') for d in a['descriptors'])==3 and not any('dedup_identity_fix' in d['label'] for d in a['descriptors']) for a,_ in joined),
  'composer_generic_candidate_present':all(a['composition']['target']==lock['target'] and a['composition']['operator']=='add_match_guard' and sum(d['label'].startswith('composer:') for d in a['descriptors'])==1 for a,_ in joined),
  'opaque_selector_inputs':all(len(a['selector_proposals'])==4 and all(d['proposal_label']=='hypothesis' for d in a['selector_proposals']) for a,_ in joined),
  'unique_training_max_selected':all(a['decision'].get('ok') and a['decision'].get('proposal_id')==max(train_counts(a),key=train_counts(a).get) and list(train_counts(a).values()).count(max(train_counts(a).values()))==1 for a,_ in joined),
  'selected_edge_candidate_is_candidate_offer':all(a['selected_label']=='edge_once:candidate:has_mint_offer' and b['selected_label']==a['selected_label'] for a,b in joined),
  'training_scores_discriminate':all(train_counts(a).get(a['decision'].get('proposal_id'))==lock['repeats'] and sum(bool(r['correct']) for x in a['outcomes'] if x['label'].startswith('composer:') for r in x['rows'])==0 for a,_ in joined),
  'heldout_selected_proposal_passes':all(len(b['heldout_rows'])==lock['repeats'] and all(r['correct'] and r['offer_counts']==[1,1] and r['fixedpoint_progress']==0 for r in b['heldout_rows']) for _,b in joined),
  'heldout_keys_disjoint':all(not(set(a['training_keys']) & {k for r in b['heldout_rows'] for k in r['keys']}) for a,b in joined),
  'tie_and_all_wrong_abstain':all(not a['controls']['tie'].get('ok') and not a['controls']['all_wrong'].get('ok') for a,_ in joined),
  'branch_isolation_and_primary_preservation':all(a['branch_isolated'] and a['primary_rule_unchanged'] for a,_ in joined),
 }
 checks={k:bool(v) for k,v in checks.items()}
 rows=[]
 for a,b in joined:
  rows.append({'worker':a['worker'],'selected_label':a['selected_label'],'training_correct_counts':train_counts(a),
   'candidate_training_outcomes':a['outcomes'],'heldout':b['heldout_rows'],'composition':a['composition'],
   'compose_ns':a['compose_ns'],'training_scoring_ns':a['training_scoring_ns'],'selector_ns':a['selector_ns']})
 report={'schema':'ThoughtexperimentGenericEdgeIdempotenceV1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
  'aggregate':{'workers':len(joined),'generated_hypotheses_per_worker':lock['candidate_count'],
   'selected_candidate_workers':sum(a['selected_label']=='edge_once:candidate:has_mint_offer' for a,_ in joined),
   'heldout_correct':sum(sum(bool(r['correct']) for r in b['heldout_rows']) for _,b in joined),
   'median_composer_ms':sorted(a['compose_ns']/1e6 for a,_ in joined)[len(joined)//2],
   'median_training_panel_ms':sorted(a['training_scoring_ns']/1e6 for a,_ in joined)[len(joined)//2],
   'median_selector_ms':sorted(a['selector_ns']/1e6 for a,_ in joined)[len(joined)//2]},'rows':rows}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if report['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
