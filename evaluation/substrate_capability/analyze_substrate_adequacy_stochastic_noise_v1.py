#!/usr/bin/env python3
"""Independent replay and dose-response analysis for signed noise panel."""
import importlib.util,itertools,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1_1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_stochastic_noise_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_stochastic_noise_v1_analysis_20261002.json'
def main():
 lock=json.loads(LOCK.read_text()); cap=json.loads(RAW.read_text())
 spec=importlib.util.spec_from_file_location('noise_runner',ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py'); runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import verify_signed_audit_evidence
 from domains import independent_adequacy as ia
 from independent_adequacy_noise_oracles_v1 import label as oracle
 import substrate_rs
 native=substrate_rs._native.Substrate(); checks=[('lock_capture',cap['lock']==lock),('current_lock',runner.frozen()==lock),('source_stability',cap['source_stable'] and cap['post_lock']==lock),('three_distinct_processes',len(cap['workers'])==3 and len({r['pid'] for group in cap['workers'] for r in group})==3),('worker_trial_counts',all(len(group)==720 for group in cap['workers']))]
 rowsets=[row for group in cap['workers'] for row in group]; checks.append(('complete_schedule',len(rowsets)==2160 and len({(r['worker'],r['task'],r['quality'],r['p'],r['providers'],r['trial']) for r in rowsets})==2160))
 selection_ok=[]; labels_ok=[]; receipt_ok=[]; auth_ok=[]; held_ok=[]; status_ok=[]
 import random
 for row in rowsets:
  task=row['task']; candidate=row['candidate']; challenger=row['challenger']; req=row['request']; seed=row['seed']; sources=[f'oracle:{task}:v1']
  sel=select_disagreement_probe(row['candidate_id'],candidate,[challenger],[],runner.DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=seed)
  selection_ok.append(sel==row['selection'] and sel['input']==req['probes'][0]['inputs'] and req['seed']==sel['selection_id'] and sel['prediction_entropy_bits']>0)
  truth=oracle(task,sel['input']); rng=random.Random(seed+':noise'); expected_flips=[rng.random()<row['p'] for _ in range(row['providers'])]; labels=row['evidence'][0]['labels']
  vals=[(not truth) if flip else truth for flip in expected_flips]
  labels_ok.append(expected_flips==row['flipped'] and vals==[label['expected'] for label in labels] and row['truth']==truth)
  receipt=ia.adjudicate_audit_receipt(req,row['candidate_id'],candidate,row['evidence'],lambda t,e:native.evaluate(t,e),acquisition_source_ids=sources)
  receipt_ok.append(receipt==row['receipt'])
  auth=verify_signed_audit_evidence(req,row['evidence'],row['receipt'],runner.KEYS); auth_ok.append(auth['ok'] and auth['verified_labels']==row['providers'] and row['auth_ok'])
  candidate_prediction=native.evaluate(candidate,sel['input']); unique=set(vals)
  expected_status='ambiguous' if len(unique)>1 else 'accepted' if vals[0]==candidate_prediction else 'rejected'
  eligible=expected_status=='accepted' and sel['prediction_entropy_bits']>0
  status_ok.append(row['receipt']['status']==expected_status and row['adoption_eligible']==eligible)
  exact=sum(native.evaluate(candidate,x)==oracle(task,x) for x in runner.HELD[task])
  held_ok.append(exact==row['heldout_exact'] and row['heldout_count']==len(runner.HELD[task]))
 checks += [('probe_selection_recomputed',all(selection_ok)),('noise_draws_and_labels_recomputed',all(labels_ok)),('receipts_recomputed',all(receipt_ok)),('all_provider_signatures_verified',all(auth_ok)),('fail_closed_status_and_adoption_rule',all(status_ok)),('heldout_oracles_recomputed',all(held_ok))]
 grouped=defaultdict(list)
 for row in rowsets: grouped[(row['task'],row['quality'],row['p'],row['providers'])].append(row)
 summary=[]
 for (task,quality,p,n),rows in sorted(grouped.items()):
  accepted=sum(r['receipt']['status']=='accepted' for r in rows); rejected=sum(r['receipt']['status']=='rejected' for r in rows); ambiguous=sum(r['receipt']['status']=='ambiguous' for r in rows); eligible=sum(r['adoption_eligible'] for r in rows)
  theoretical=(1-p)**n if quality=='correct' else p**n
  summary.append({'task':task,'candidate_quality':quality,'flip_probability':p,'provider_count':n,'trials':len(rows),'accepted':accepted,'rejected':rejected,'ambiguous':ambiguous,'adoption_eligible':eligible,'eligible_rate':eligible/len(rows),'theoretical_eligible_probability':theoretical,'heldout_exact_per_trial':rows[0]['heldout_exact'],'heldout_count':rows[0]['heldout_count']})
  checks.append((f'cell_{task}_{quality}_p{p}_n{n}_counts',len(rows)==60 and accepted+rejected+ambiguous==60 and abs(eligible/60-theoretical)<=max(0.12,5*math.sqrt(theoretical*(1-theoretical)/60))))
 result={'schema':'SubstrateAdequacyStochasticNoiseV1Analysis','checks':[{'name':n,'pass':ok} for n,ok in checks],'passed':sum(ok for _,ok in checks),'total':len(checks),'cell_summaries':summary,'interpretation':'The simulated independent channels match the fail-closed receipt law: provider disagreement causes ambiguity; unanimity permits adoption only when unanimous labels match the candidate and the selected probe is discriminating. For a wrong candidate, unanimous noise can produce false adoption with probability p^m.','limits':['two authored Boolean task families','simulated provider independence and known Bernoulli noise','receipt/eligibility outcomes are mechanism-level; no repeated graph write','three processes on one host; 60 trials per cell are descriptive']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
 if not all(ok for _,ok in checks): raise SystemExit(1)
if __name__=='__main__': main()
