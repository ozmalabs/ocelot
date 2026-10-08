#!/usr/bin/env python3
"""Independent analysis for recurrence compose-and-select integration."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_recurrence_compose_and_select_v1 as runner
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_compose_and_select_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 om={int(x['worker']):x for x in orders['workers']};sm={int(x['worker']):x for x in scores['workers']};ids=set(range(lock['workers']))
 joined=[(om[i],sm[i]) for i in sorted(ids & om.keys() & sm.keys())]
 def counts(a):return {x['proposal_id']:sum(bool(r['correct']) for r in x['rows']) for x in a['candidate_outcomes']}
 checks={
  'exact_worker_schedule':set(om)==ids and set(sm)==ids and len(orders['workers'])==len(ids) and len(scores['workers'])==len(ids),
  'capture_lock_and_stage_linkage':orders.get('lock_sha256')==sha(LOCK) and scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS),
  'source_lock_current':runner.frozen()==lock['sources'],
  'per_worker_source_stable':all(a['source_before']==lock['sources']==a['source_after']==b['source_before']==b['source_after'] for a,b in joined),
  'nine_unique_hypotheses_and_composer_proposal':all(len(a['candidate_descriptors'])==9 and len({x['proposal_id'] for x in a['candidate_descriptors']})==9 and sum(x['label'].startswith('composer_') for x in a['candidate_descriptors'])==1 for a,_ in joined),
  'selection_input_labels_opaque':all(len(a['selector_proposals'])==9 and all(x['proposal_label']=='hypothesis' for x in a['selector_proposals']) and {x['proposal_id'] for x in a['selector_proposals']}=={x['proposal_id'] for x in a['candidate_descriptors']} for a,_ in joined),
  'unique_train_max_selected':all(a['decision'].get('ok') and a['decision'].get('proposal_id')==max(counts(a),key=counts(a).get) and list(counts(a).values()).count(max(counts(a).values()))==1 for a,_ in joined),
  'selected_candidate_is_recurrence_fix':all(a['selected_label']=='dedup_identity_fix' and b['selected_label']=='dedup_identity_fix' for a,b in joined),
  'disjoint_training_and_heldout_keys':all(not(set(a['training_keys']) & {k for r in b['heldout_rows'] for k in r.get('recurrence_keys',[])}) for a,b in joined),
  'heldout_selected_candidate_passes':all(len(b['heldout_rows'])==lock['repeats'] and all(r['correct'] and r['offer_counts']==[1,1] and r['fixedpoint_progress']==0 for r in b['heldout_rows']) for _,b in joined),
  'tie_and_all_wrong_abstain':all(not a['controls']['tie'].get('ok') and not a['controls']['all_wrong'].get('ok') for a,_ in joined),
  'branch_evidence_isolation_and_primary_preservation':all(a['branch_evidence_isolated'] and a['primary_rules_unchanged'] for a,_ in joined),
 }
 checks={k:bool(v) for k,v in checks.items()}
 rows=[]
 for a,b in joined:
  c=counts(a);rows.append({'worker':a['worker'],'selected_label':a['selected_label'],'training_match_counts':c,
   'composer':a['composer'],'heldout':b['heldout_rows'],'training_scoring_ns':a['training_scoring_ns'],
   'selector_ns':a['selector_ns'],'heldout_runtime_ns':b['heldout_runtime_ns']})
 report={'schema':'ThoughtexperimentRecurrenceComposeAndSelectV1_1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
  'aggregate':{'workers':len(joined),'candidate_count':lock['candidate_count'],
   'composer_proposals':sum(x['composer']['operator']==lock['composer_operator'] for x,_ in joined),
   'selected_recurrence_repairs':sum(x['selected_label']=='dedup_identity_fix' for x,_ in joined),
   'heldout_correct':sum(sum(bool(r['correct']) for r in y['heldout_rows']) for _,y in joined),
   'median_selector_ms':sorted(x['selector_ns']/1e6 for x,_ in joined)[len(joined)//2],
   'median_training_panel_ms':sorted(x['training_scoring_ns']/1e6 for x,_ in joined)[len(joined)//2]},'rows':rows}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if report['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
