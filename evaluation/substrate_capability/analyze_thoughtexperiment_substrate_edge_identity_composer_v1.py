#!/usr/bin/env python3
"""Independent gates for the substrate edge-identity composer capture."""
from __future__ import annotations
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
import thoughtexperiment_substrate_edge_identity_composer_v1 as runner
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_substrate_edge_identity_composer_v1_analysis_20261002.json'
EXPECTED={'recurrence':('mrl_offer_due_once','add_edge_identity_guard','out candidate has_mint_offer any endpoint'),
 'conversation':('reply_to_adjacency_pair','add_edge_identity_guard','in m responds_to any endpoint')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text())
 om={int(x['worker']):x for x in orders['workers']};sm={int(x['worker']):x for x in scores['workers']};ids=set(range(lock['workers']))
 joined=[(om[i],sm[i]) for i in sorted(ids & om.keys() & sm.keys())]
 def timed(a,b,f):
  x=a['families'][f]['proposal'];y=b['families'][f]
  values=[x['compose_ns'],a['families'][f]['training_scoring_ns'],a['families'][f]['source_control_ns'],
   y['heldout_scoring_ns'],y['source_control_ns'],a['worker_stage_wall_ns'],b['worker_stage_wall_ns']]
  return all(isinstance(v,int) and v>=0 for v in values)
 checks={
  'exact_workers_and_stage_linkage':set(om)==ids and set(sm)==ids and len(orders['workers'])==len(ids) and len(scores['workers'])==len(ids) and scores.get('lock_sha256')==sha(LOCK) and scores.get('orders_sha256')==sha(ORDERS),
  'current_source_lock':runner.frozen()==lock['sources'],
  'source_stable_everywhere':all(a['source_before']==lock['sources']==a['source_after']==b['source_before']==b['source_after'] for a,b in joined),
  'both_families_present':all(set(a['families'])==set(lock['families']) and set(b['families'])==set(lock['families']) for a,b in joined),
  'unique_expected_proposal_and_semantic_change':all(
   a['families'][f]['proposal']['built'] and a['families'][f]['proposal']['target']==EXPECTED[f][0]
   and a['families'][f]['proposal']['operator']==EXPECTED[f][1]
   and a['families'][f]['proposal']['site']==EXPECTED[f][2]
   and a['families'][f]['proposal']['digest']!=a['families'][f]['proposal']['source_rule_digest']
   for a,b in joined for f in lock['families']),
  'training_utility_and_source_controls':all(
   len(a['families'][f]['training'])==lock['repeats'] and all(x['correct'] for x in a['families'][f]['training'])
   and len(a['families'][f]['source_training'])==lock['repeats'] and all(x['correct'] for x in a['families'][f]['source_training'])
   for a,b in joined for f in lock['families']),
  'heldout_utility_and_source_controls':all(
   len(b['families'][f]['heldout'])==lock['repeats'] and all(x['correct'] for x in b['families'][f]['heldout'])
   and len(b['families'][f]['source_heldout'])==lock['repeats'] and all(x['correct'] for x in b['families'][f]['source_heldout'])
   for a,b in joined for f in lock['families']),
  'primary_target_preserved':all(a['families'][f]['primary_rule_unchanged'] for a,b in joined for f in lock['families']),
  'no_overlap_abstains':all(not a['controls']['no_overlap']['built'] for a,b in joined),
  'ambiguous_site_abstains':all(not a['controls']['ambiguous_site']['built'] and 'tied or no cue overlap' in a['controls']['ambiguous_site']['wall'] for a,b in joined),
  'phase_timings_complete':all(timed(a,b,f) for a,b in joined for f in lock['families']),
  'harness_has_no_edge_scanner_or_candidate_generator':
   'generic_edge_guard_hypotheses' not in runner.RUNNER.read_text() and '_default_candidates(' not in runner.RUNNER.read_text(),
 }
 checks={k:bool(v) for k,v in checks.items()}
 rows=[]
 for a,b in joined:
  for f in lock['families']:
   x=a['families'][f];y=b['families'][f];p=x['proposal']
   rows.append({'worker':a['worker'],'family':f,'target':p['target'],'operator':p['operator'],'site':p['site'],
    'proposal_digest':p['digest'],'source_rule_digest':p['source_rule_digest'],
    'training_outcomes':x['training'],'heldout_outcomes':y['heldout'],
    'timing_ns':{'composition':p['compose_ns'],'training_scoring':x['training_scoring_ns'],
     'heldout_scoring':y['heldout_scoring_ns'],'source_training':x['source_control_ns'],
     'source_heldout':y['source_control_ns']}})
 summary={}
 for f in lock['families']:
  frows=[r for r in rows if r['family']==f]
  summary[f]={'proposals':len(frows),'heldout_correct':sum(sum(bool(t['correct']) for t in r['heldout_outcomes']) for r in frows),
   'median_composition_ms':statistics.median(r['timing_ns']['composition'] for r in frows)/1e6,
   'median_training_ms':statistics.median(r['timing_ns']['training_scoring'] for r in frows)/1e6,
   'median_heldout_ms':statistics.median(r['timing_ns']['heldout_scoring'] for r in frows)/1e6}
 report={'schema':'SubstrateEdgeIdentityComposerV1Analysis','checks':checks,'all_checks_pass':all(checks.values()),
  'aggregate':{'workers':len(joined),'analysis_check_count':len(checks),'summary':summary,
   'no_overlap_abstentions':sum(not x['controls']['no_overlap']['built'] for x,_ in joined),
   'ambiguous_site_abstentions':sum(not x['controls']['ambiguous_site']['built'] for x,_ in joined)},'rows':rows}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if report['all_checks_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
