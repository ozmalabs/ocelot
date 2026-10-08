#!/usr/bin/env python3
"""Independent analysis for bidirectional edge-identity guard proposals."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_bidirectional_edge_identity_guards_v1 as runner
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_bidirectional_edge_identity_guards_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_bidirectional_edge_identity_guards_v1_analysis_20261002.json'
EXPECTED={'recurrence':'edge_once:out:candidate:has_mint_offer:any_target',
 'conversation':'edge_once:in:m:responds_to:any_target'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evidence_counts(family_row):
 return {x['proposal_id']:sum(bool(r['correct']) for r in x['rows']) for x in family_row['training_outcomes']}
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 om={int(x['worker']):x for x in orders['workers']};sm={int(x['worker']):x for x in scores['workers']};ids=set(range(lock['workers']))
 joined=[(om[i],sm[i]) for i in sorted(ids & om.keys() & sm.keys())]
 def family_pairs(family):return [(a['families'][family],b['families'][family]) for a,b in joined]
 def selected_pass(family,a,b):
  pid=a['decision'].get('proposal_id');row=next((x for x in b['candidate_outcomes'] if x['proposal_id']==pid),None)
  return row is not None and all(x['correct'] for x in row['trials'])
 checks={
  'exact_workers_and_stage_linkage':set(om)==ids and set(sm)==ids and len(orders['workers'])==len(ids) and len(scores['workers'])==len(ids) and scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS),
  'current_source_lock':runner.frozen()==lock['sources'],
  'source_stable_everywhere':all(a['source_before']==lock['sources']==a['source_after']==b['source_before']==b['source_after'] for a,b in joined),
  'both_families_present':all(set(a['families'])==set(lock['families']) and set(b['families'])==set(lock['families']) for a,b in joined),
  'four_hypotheses_per_family':all(len(a['families'][f]['descriptors'])==4 and len(b['families'][f]['candidate_outcomes'])==4 for a,b in joined for f in lock['families']),
  'three_derived_guards_and_one_composer':all(sum(d['label'].startswith('edge_once:') for d in a['families'][f]['descriptors'])==3 and sum(d['label'].startswith('composer:') for d in a['families'][f]['descriptors'])==1 for a,b in joined for f in lock['families']),
  'selector_input_opaque':all(all(x['proposal_label']=='hypothesis' for x in a['families'][f]['selector_proposals']) for a,b in joined for f in lock['families']),
  'unique_training_winner_matches_term':all(a['families'][f]['decision'].get('ok') and a['families'][f]['decision'].get('proposal_id')==max(evidence_counts(a['families'][f]),key=evidence_counts(a['families'][f]).get) and list(evidence_counts(a['families'][f]).values()).count(max(evidence_counts(a['families'][f]).values()))==1 for a,b in joined for f in lock['families']),
  'right_scope_selected_both_families':all(a['families'][f]['selected_label']==EXPECTED[f] for a,b in joined for f in lock['families']),
  'selected_candidates_pass_heldout':all(selected_pass(f,a['families'][f],b['families'][f]) for a,b in joined for f in lock['families']),
  'same_act_train_and_mixed_repeated_heldout':all(all(x['output_counts']==[1,1] for x in a['families']['conversation']['source_train']) and all(x['output_counts']==[1,1,1] for x in b['families']['conversation']['source_heldout']) for a,b in joined),
  'source_positive_controls_pass':all(all(x['correct'] for x in a['families'][f]['source_train']) and all(x['correct'] for x in b['families'][f]['source_heldout']) for a,b in joined for f in lock['families']),
  'all_wrong_and_tie_controls_abstain':all(not a['families'][f]['controls']['all_wrong'].get('ok') and not a['families'][f]['controls']['tie'].get('ok') for a,b in joined for f in lock['families']),
  'false_scope_proposals_fail_heldout':all(sum(all(t['correct'] for t in c['trials']) for c in b['families'][f]['candidate_outcomes'])==1 for a,b in joined for f in lock['families']),
  'primary_rules_and_branch_evidence_isolated':all(a['families'][f]['primary_rule_unchanged'] and a['families'][f]['branch_evidence_isolated'] and all(all(t['rule_store_stable'] for t in c['rows']) for c in a['families'][f]['training_outcomes']) and all(all(t['rule_store_stable'] for t in c['trials']) for c in b['families'][f]['candidate_outcomes']) for a,b in joined for f in lock['families']),
 }
 checks={k:bool(v) for k,v in checks.items()}
 rows=[]
 for a,b in joined:
  for family in lock['families']:
   x=a['families'][family];y=b['families'][family];counts=evidence_counts(x)
   rows.append({'worker':a['worker'],'family':family,'selected_label':x['selected_label'],
    'training_correct_counts':counts,'heldout_candidate_outcomes':y['candidate_outcomes'],
    'source_heldout':y['source_heldout'],'composer':x['composer'],'derived_sites':x['sites'],
    'cost_ns':{'composer':x['compose_ns'],'training_scoring':x['training_scoring_ns'],
     'selection':x['selector_ns'],'heldout_all_candidates':sum(t.get('sequence_runtime_ns',0) for c in y['candidate_outcomes'] for t in c['trials'])}})
 counts={f:sum(1 for x in rows if x['family']==f and x['selected_label']==EXPECTED[f]) for f in lock['families']}
 heldout_correct={}
 for family in lock['families']:
  heldout_correct[family]=0
  for row in rows:
   if row['family']!=family or row['selected_label']!=EXPECTED[family]:continue
   candidate=next((c for c in row['heldout_candidate_outcomes'] if c['label']==EXPECTED[family]),None)
   if candidate:heldout_correct[family]+=sum(bool(t['correct']) for t in candidate['trials'])
 report={'schema':'ThoughtexperimentBidirectionalEdgeIdentityGuardsV1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
  'aggregate':{'workers':len(joined),'families':list(lock['families']),'selected_scope_workers':counts,
   'selected_heldout_correct_by_family':heldout_correct,'analysis_check_count':len(checks)},'rows':rows}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if report['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
