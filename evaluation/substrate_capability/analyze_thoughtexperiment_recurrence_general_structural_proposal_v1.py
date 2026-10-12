#!/usr/bin/env python3
"""Independent integrity and outcome analysis for recurrence proposal transfer."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_recurrence_general_structural_proposal_v1 as runner
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_general_structural_proposal_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_general_structural_proposal_v1_1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 om={int(x['worker']):x for x in orders['workers']};sm={int(x['worker']):x for x in scores['workers']}
 ids=set(range(int(lock['workers'])));joined=[(om[i],sm[i]) for i in sorted(ids & om.keys() & sm.keys())]
 checks={
  'exact_worker_schedule':set(om)==ids and set(sm)==ids and len(orders['workers'])==len(ids) and len(scores['workers'])==len(ids),
  'lock_and_order_linkage':scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS),
  'source_lock_current':runner.frozen()==lock['sources'],
  'per_worker_source_stable':all(a['source_before']==lock['sources']==a['source_after']==b['source_before']==b['source_after'] for a,b in joined),
  'cue_and_order_stage_blind':all(a['cue']==lock['cue'] and 'heldout' not in json.dumps(a).lower() and 'oracle_pass' not in json.dumps(a) for a,_ in joined),
  'target_and_operator_selected':all(a.get('built') and a.get('target')==lock['target'] and a.get('operator')==lock['expected_operator'] for a,_ in joined),
  'generic_proposal_fails_recurrence_oracle':all(not b['proposal_score']['oracle_pass'] and not b['proposal_score']['utility'] for _,b in joined),
  'domain_reference_passes_recurrence_oracle':all(b['positive_reference_score']['label']==lock['positive_reference'] and b['positive_reference_score']['oracle_pass'] and b['positive_reference_score']['utility'] for _,b in joined),
  'branch_receipts_and_primary_isolation':all(b['proposal_score']['receipt_verified'] and b['proposal_score']['primary_preserved'] and b['positive_reference_score']['receipt_verified'] and b['positive_reference_score']['primary_preserved'] for _,b in joined),
  'proposal_site_is_generic_marker':all("adopted_variant_probe" in str(a.get('site')) for a,_ in joined),
 }
 checks={k:bool(v) for k,v in checks.items()}
 report={'schema':'ThoughtexperimentRecurrenceGeneralStructuralProposalV1_1Analysis','checks':checks,
  'all_checks_pass':all(checks.values()),'aggregate':{'workers':len(joined),
   'generic_proposal_passes':sum(bool(b['proposal_score']['oracle_pass']) for _,b in joined),
   'dedup_reference_passes':sum(bool(b['positive_reference_score']['oracle_pass']) for _,b in joined),
   'median_composer_ms':sorted(a['compose_ns']/1e6 for a,_ in joined)[len(joined)//2]},
  'rows':[{'worker':a['worker'],'target':a.get('target'),'operator':a.get('operator'),'site':a.get('site'),
   'proposal_cases':b['proposal_score']['task_cases'],'proposal_receipt':b['proposal_score']['receipt_verified'],
   'proposal_primary_preserved':b['proposal_score']['primary_preserved'],
   'reference_cases':b['positive_reference_score']['task_cases'],
   'cost_ns':{'composer':a['compose_ns'],**b['proposal_score']['cost_ns']}} for a,b in joined]}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
