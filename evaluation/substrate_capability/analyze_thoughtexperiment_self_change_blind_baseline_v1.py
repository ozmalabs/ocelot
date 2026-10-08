#!/usr/bin/env python3
"""Independent accuracy, minimality, abstention, and lock gates."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_self_change_blind_baseline_v1_lock_20261005.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_self_change_blind_baseline_v1_20261005.json'
OUT=CAP.with_name('thoughtexperiment_self_change_blind_baseline_v1_analysis_20261005.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l=json.loads(LOCK.read_text());c=json.loads(CAP.read_text());ws=c.get('workers',[]);errors=[]
 if c.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 if len(ws)!=3 or len({w.get('pid') for w in ws})!=3:errors.append('worker count or process uniqueness')
 expected={'fn_threshold_001':'threshold_adjustment','fp_context_002':'guard_strengthening','missing_relation_003':'relation_addition','wrong_effect_004':'effect_substitution','runaway_noop_005':'firing_budget_guard','ambiguous_minimal_006':'threshold_adjustment'}
 summaries=[]
 for w in ws:
  if w.get('sources_before')!=l['sources'] or w.get('sources_after')!=l['sources']:errors.append(f"worker {w.get('worker')}: source lock mismatch")
  rows=w.get('rows',[])
  if len(rows)!=7 or len({r.get('opaque_case_id') for r in rows})!=7:errors.append(f"worker {w.get('worker')}: case set/opaque IDs invalid")
  for r in rows:
   cid=r['case_id'];selected=r['selected']
   ad={x['family'] for x in r['candidate_scores'] if x['gain']>x['noop_gain']+5 and x['gain']>x['placebo_gain']+5 and x['protected_regressions']==0 and x['resource_cost']<=x['resource_budget'] and x['replications']>=2 and x['replicated_gain']>=5}
   if ad!=set(r['harness_admissible_families']):errors.append(cid+': harness admissibility ledger disagrees with independent calculation')
   if r.get('answer_key_passed') is not False:errors.append(cid+': answer key entered policy')
   if cid in expected:
    if len(selected)!=1 or selected[0]['family']!=expected[cid]:errors.append(cid+': selected family mismatch')
    if selected and (selected[0]['proofs_passed']!=1 or selected[0]['family'] not in ad):errors.append(cid+': selected patch lacks passing proofs or harness admissibility')
    if cid=='ambiguous_minimal_006':
     options=[x for x in r['candidate_scores'] if x['family'] in ad]
     if len(options)<2 or selected[0]['mdl_cost']!=min(x['mdl_cost'] for x in options):errors.append(cid+': MDL did not select minimal admissible candidate')
    if r['abort'] is not None:errors.append(cid+': unexpected abort')
   else:
    if selected:errors.append(cid+': unsupported candidate selected')
    if not r['abort'] or r['abort']['reason']!='no_causally_supported_patch':errors.append(cid+': expected honest graph abort absent')
   summaries.append((cid,len(selected),bool(r['abort'])))
 result={'schema':'ThoughtexperimentSelfChangeBlindBaselineV1Analysis','gates_pass':not errors,'errors':errors,'summary':{'workers':len(ws),'unique_worker_pids':len({w.get('pid') for w in ws}),'case_rows':len(summaries),'expected_family_selections_per_worker':6,'honest_aborts_per_worker':sum(x[0]=='correlation_only_007' and x[2] for x in summaries)//max(1,len(ws)),'proof_and_minimality_gate':'pass' if not errors else 'fail','scope':'blind graph-native patch selection from host-supplied candidate representations and measurements; no candidate invention or rule adoption'}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
