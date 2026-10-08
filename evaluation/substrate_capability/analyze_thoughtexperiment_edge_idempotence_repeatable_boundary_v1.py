#!/usr/bin/env python3
"""Independent analysis for generic edge-once behavior on repeatable replies."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_edge_idempotence_repeatable_boundary_v1 as runner
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_edge_idempotence_repeatable_boundary_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 om={int(x['worker']):x for x in orders['workers']};sm={int(x['worker']):x for x in scores['workers']};ids=set(range(lock['workers']))
 pairs=[(om[i],sm[i]) for i in sorted(ids & om.keys() & sm.keys())]
 checks={
  'exact_worker_schedule':set(om)==ids and set(sm)==ids and len(orders['workers'])==len(ids) and len(scores['workers'])==len(ids),
  'capture_linkage':orders.get('lock_sha256')==sha(LOCK) and scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS),
  'source_lock_current':runner.frozen()==lock['sources'],
  'source_stable':all(a['source_before']==lock['sources']==a['source_after']==b['source_before']==b['source_after'] for a,b in pairs),
  'generic_candidate_is_coarse_agent_edge_guard':all(a['generic_site']==[['agent','sent',None]] and any(d['label']=='edge_once:agent:sent:any_target' for d in a['descriptors']) for a,_ in pairs),
  'composer_target_and_edit_recorded':all(a['composer']['removed_rule']==lock['target'] and a['composer']['kind']=='add_match_guard' for a,_ in pairs),
  'source_rule_passes_train_and_heldout':all(a['baseline_train']['correct'] and a['baseline_train']['reply_counts_by_input']==[1,1] and b['baseline_heldout']['correct'] and b['baseline_heldout']['reply_counts_by_input']==[1,1,1] for a,b in pairs),
  'both_proposals_fail_training':all(len(a['candidate_outcomes'])==2 and all(not x['outcome']['correct'] for x in a['candidate_outcomes']) and all(x['outcome']['reply_counts_by_input']!=[1,1] for x in a['candidate_outcomes']) for a,_ in pairs),
  'selector_abstains_on_all_wrong':all(not a['decision'].get('ok') and a['selected_label'] is None for a,_ in pairs),
  'heldout_diagnostic_shows_false_suppression':all(not b['generic_heldout_diagnostic']['correct'] and b['generic_heldout_diagnostic']['reply_counts_by_input']==[1,0,0] for _,b in pairs),
  'branch_evidence_and_rule_store_isolation':all(a['branch_evidence_isolated'] and a['primary_rule_preserved'] and all(x['outcome']['rule_store_stable_during_sequence'] for x in a['candidate_outcomes']) for a,_ in pairs),
 }
 checks={k:bool(v) for k,v in checks.items()}
 report={'schema':'ThoughtexperimentRepeatableEdgeBoundaryV1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
  'aggregate':{'workers':len(pairs),'source_train_replies':sum(len(a['baseline_train']['reply_counts_by_input']) for a,_ in pairs),
   'source_heldout_replies':sum(len(b['baseline_heldout']['reply_counts_by_input']) for _,b in pairs),
   'coarse_guard_training_reply_counts':[x['outcome']['reply_counts_by_input'] for a,_ in pairs for x in a['candidate_outcomes'] if x['label']=='edge_once:agent:sent:any_target'],
   'coarse_guard_heldout_reply_counts':[b['generic_heldout_diagnostic']['reply_counts_by_input'] for _,b in pairs]},
  'rows':[{'worker':a['worker'],'candidate_outcomes':a['candidate_outcomes'],'baseline_train':a['baseline_train'],
   'decision':a['decision'],'composer':a['composer'],'generic_site':a['generic_site'],
   'baseline_heldout':b['baseline_heldout'],'generic_heldout_diagnostic':b['generic_heldout_diagnostic']} for a,b in pairs]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if report['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
