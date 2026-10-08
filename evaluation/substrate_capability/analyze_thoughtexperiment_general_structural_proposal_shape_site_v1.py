#!/usr/bin/env python3
"""Independent integrity and outcome analysis for the shape EditSite probe."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_general_structural_proposal_shape_site_v1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_shape_site_v1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_shape_site_v1_scores_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_general_structural_proposal_shape_site_v1_analysis_20261002.json'
CONDITIONS=('key_to_signature','signature_to_key','ambiguous')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def good(x):return bool(x and x.get('utility')==1.0 and x.get('receipt_verified') and x.get('primary_preserved'))
def main():
 lock=json.loads(LOCK.read_text());orders=json.loads(ORDERS.read_text());scores=json.loads(SCORES.read_text());errors=[];checks={}
 all_rows=orders['workers']+scores['workers']
 checks['locked_sources_stable']=all(r.get('source_stable') and r.get('source_before')==lock['sources']==r.get('source_after') for r in all_rows)
 checks['score_binds_orders']=scores['orders_sha256']==sha(ORDERS)
 ow={int(x['worker']):x for x in orders['workers']};sw={int(x['worker']):x for x in scores['workers']}
 checks['four_workers_complete']=set(ow)==set(range(4)) and set(sw)==set(range(4))
 checks['orders_precede_and_exclude_heldout']=all(not any(k in json.dumps(x) for k in ('utility','heldout_score','proposal_outcomes')) for x in orders['workers'])
 target_preserved=[];proposal_identity=[];different_sites=[];ambiguous_abstains=[];receipt_ok=[];host_contrast=[]
 matched_utility=[];reverse_utility=[];rows=[]
 for i in range(4):
  o=ow[i];s=sw[i];props=o['proposals'];po=s['proposal_outcomes']
  target_preserved.append(o['target_before']==o['target_after'] and o['target_before']['name']=='sd_mint_quantum')
  a=props['key_to_signature'];b=props['signature_to_key'];c=props['ambiguous']
  proposal_identity.append(all(x['built'] and x['target']=='sd_mint_quantum' and x['operator']=='swap_term_leaf' and x['host_reference_match'] is not None for x in (a,b)))
  different_sites.append(a.get('digest')!=b.get('digest') and "'key' -> 'signature'" in str(a.get('site')) and "'signature' -> 'key'" in str(b.get('site')))
  ambiguous_abstains.append(not c['built'] and c['candidate'] is None)
  host=s['host_candidate_outcomes'];host_contrast.append(0<sum(x.get('utility')==1.0 for x in host)<len(host))
  receipt_ok.append(len(host)==len(o['host_candidates']) and all(x.get('receipt_verified') and x.get('primary_preserved') for x in host))
  ma=po['key_to_signature'];rv=po['signature_to_key']
  matched_utility.append(good(ma));reverse_utility.append(good(rv))
  if not proposal_identity[-1]:errors.append(f'worker {i}: ordered proposals failed target/operator/reference gate')
  if not different_sites[-1]:errors.append(f'worker {i}: directional cues did not select distinct expected sites')
  if not ambiguous_abstains[-1]:errors.append(f'worker {i}: ambiguous site cue did not abstain')
  if not target_preserved[-1]:errors.append(f'worker {i}: target changed during proposal capture')
  if not receipt_ok[-1]:errors.append(f'worker {i}: host candidate receipt/isolation failure')
  if not host_contrast[-1]:errors.append(f'worker {i}: host reference lacks useful/failing contrast')
  if not matched_utility[-1]:errors.append(f'worker {i}: key-to-signature proposal failed held-out utility')
  if reverse_utility[-1]:errors.append(f'worker {i}: reversed proposal unexpectedly passed; direction contrast absent')
  rows.append({'worker':i,'matched_site_utility':bool(ma and ma.get('utility')==1.0),
   'reversed_site_utility':bool(rv and rv.get('utility')==1.0),'ambiguous_abstained':ambiguous_abstains[-1],
   'matched_cases':ma.get('task_cases') if ma else None,'reversed_cases':rv.get('task_cases') if rv else None,
   'host_useful_labels':[x['label'] for x in host if x.get('utility')==1.0]})
 checks['target_preserved']=all(target_preserved)
 checks['proposals_match_host_reference']=all(proposal_identity)
 checks['directional_site_selection']=all(different_sites)
 checks['ambiguous_direction_abstention']=all(ambiguous_abstains)
 checks['all_host_candidate_receipts_and_isolation']=all(receipt_ok)
 checks['host_success_failure_contrast']=all(host_contrast)
 checks['cue_matched_proposal_passes_heldout']=all(matched_utility)
 checks['reversed_proposal_fails_heldout']=all(not x for x in reverse_utility)
 costs=[{'worker':i,'host_enumeration_ns':ow[i]['host_enumeration_ns'],
  'task_context_setup_ns':ow[i]['task_context_setup_ns'],
  **{f'{k}_composer_ns':ow[i]['proposals'][k]['composer_ns'] for k in CONDITIONS},
  **{f'{k}_branch_trial_ns':sum(sw[i]['proposal_outcomes'][k].get('cost_ns',{}).values()) if sw[i]['proposal_outcomes'][k] else 0 for k in CONDITIONS}}
  for i in range(4)]
 summary={'schema':'GeneralStructuralProposalShapeSiteV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'inputs':{'lock_sha256':sha(LOCK),'orders_sha256':sha(ORDERS),'scores_sha256':sha(SCORES)},
  'checks':checks,'errors':errors,'workers':rows,'costs':costs,
  'aggregate':{'workers':4,'host_candidates_scored':sum(len(sw[i]['host_candidate_outcomes']) for i in sw),
   'cue_matched_proposals_useful':sum(matched_utility),'reversed_proposals_useful':sum(reverse_utility),
   'median_key_to_signature_composer_ms':statistics.median(ow[i]['proposals']['key_to_signature']['composer_ns'] for i in ow)/1e6,
   'median_reversed_composer_ms':statistics.median(ow[i]['proposals']['signature_to_key']['composer_ns'] for i in ow)/1e6}}
 OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'checks':checks,'errors':errors,'aggregate':summary['aggregate']},sort_keys=True))
 return int(not all(checks.values()))
if __name__=='__main__':raise SystemExit(main())
