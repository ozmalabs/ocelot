#!/usr/bin/env python3
"""Independent lock, evidence, and semantic replay for threshold noise panel."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1_2_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_threshold_noise_v1_2_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_threshold_noise_v1_2_analysis_20261002.json'
CASES=('truthful_positive','truthful_wrong_broad','truthful_wrong_alias','trusted_false_label','conflicting_signed_labels')
def main():
 lock=json.loads(LOCK.read_text()); cap=json.loads(RAW.read_text()); sp=importlib.util.spec_from_file_location('threshold_runner',ROOT/'evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1.py'); runner=importlib.util.module_from_spec(sp); sp.loader.exec_module(runner)
 from domains import independent_adequacy as ia
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import verify_signed_audit_evidence
 from independent_threshold_oracle_v1 import label as oracle
 import substrate_rs
 native=substrate_rs._native.Substrate(); rows=cap['workers']; checks=[('capture_lock',cap['lock']==lock),('current_lock',runner.frozen()==lock),('source_stability',cap['source_stable'] and cap['post_lock']==lock and all(x['active_after']==lock['active'] for x in rows)),('15_unique_workers',len(rows)==15 and len({x['pid'] for x in rows})==15),('schedule', {(x['case'],x['rep']) for x in rows}=={(c,r) for c in CASES for r in (1,2,3)})]
 selection_ok=[]; auth_ok=[]; receipt_ok=[]; semantic_ok=[]
 for row in rows:
  ctx=row['context']; chosen=select_disagreement_probe(row['candidate_id'],row['term'],ctx['challenger_terms'],ctx['acquisition_rows'],ctx['admissible_inputs'],lambda t,e:native.evaluate(t,e),seed=ctx['seed']); selection_ok.append(chosen==row['selection'] and row['request']['seed']==chosen['selection_id'] and chosen['input']==row['request']['probes'][0]['inputs'])
  auth=verify_signed_audit_evidence(row['request'],row['rows'],row['receipt'],runner.KEYS); auth_ok.append(auth['ok'] and auth['verified_labels']==len(row['labels']))
  receipt=ia.adjudicate_audit_receipt(row['request'],row['candidate_id'],row['term'],row['rows'],lambda t,e:native.evaluate(t,e),acquisition_source_ids=ctx['acquisition_source_ids']); receipt_ok.append(receipt==row['receipt'])
  semantic_ok.append(all(x['expected']==oracle(x['inputs']) and x['prediction']==native.evaluate(row['term'],x['inputs']) and x['match']==(x['prediction']==x['expected']) for x in row['heldout']) and row['truth_at_probe']==oracle(row['selection']['input']))
 checks += [('selection_recomputed',all(selection_ok)),('all_signatures_valid',all(auth_ok)),('receipts_recomputed',all(receipt_ok)),('heldouts_recomputed',all(semantic_ok))]
 expected={'truthful_positive':('accepted',1,True),'truthful_wrong_broad':('rejected',0,False),'truthful_wrong_alias':('accepted',0,False),'trusted_false_label':('accepted',1,False),'conflicting_signed_labels':('ambiguous',0,False)}
 summary={}
 for case,(status,adopt,should_match) in expected.items():
  group=[x for x in rows if x['case']==case]
  def semantic_gate(x):
   matches=sum(y['match'] for y in x['heldout']); total=len(x['heldout'])
   return matches==total if should_match else matches<total
  ok=len(group)==3 and all(x['receipt']['status']==status and x['shape_delta']==adopt and semantic_gate(x) for x in group)
  checks.append((case+'_expected_outcome',ok)); summary[case]={'n':len(group),'receipt':status,'adopted_per_run':adopt,'heldout_exact_per_run':sum(y['match'] for y in group[0]['heldout']) if group else None,'heldout_count':len(group[0]['heldout']) if group else None}
 result={'schema':'SubstrateAdequacyThresholdNoiseV1Analysis','checks':[{'name':n,'pass':ok} for n,ok in checks],'passed':sum(ok for _,ok in checks),'total':len(checks),'summary':summary,'interpretation':'The trusted false-label condition is an expected, measured failure: authentication and probe disagreement do not establish label truth.','limits':['one authored task','one host','harness-supplied finite domain and provider keys','adversarial false-label rate is not prevalence']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
 if not all(ok for _,ok in checks): raise SystemExit(1)
if __name__=='__main__': main()
