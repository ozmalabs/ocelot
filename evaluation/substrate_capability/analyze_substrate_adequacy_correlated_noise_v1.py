#!/usr/bin/env python3
"""Independent common-mode-noise replay and dose-response analysis."""
import hashlib,importlib.util,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_correlated_noise_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_correlated_noise_v1_analysis_20261002.json'
def main():
 lock=json.loads(LOCK.read_text()); cap=json.loads(RAW.read_text()); path=ROOT/'evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1.py'
 spec=importlib.util.spec_from_file_location('corr_runner',path); runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner); base=runner.base
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label,verify_signed_audit_evidence
 from domains import independent_adequacy as ia
 from independent_adequacy_noise_oracles_v1 import label as oracle
 import substrate_rs
 native=substrate_rs._native.Substrate(); from substrate.world_adapter import WorldAdapter; from domains import code_reading as cdr
 parsed={}; ids={}
 for task in base.TASKS:
  wa=WorldAdapter(shadow_read=False,deep_ingest=False); _,eng,_=cdr._resolve(wa); name='parity' if task=='parity' else 'exceeds'
  gr=cdr.read_function(wa,base.GOOD[task],name); br=cdr.read_function(wa,base.BAD[task],'always_false'); parsed[task]=(gr['term'],br['term'])
  ids[task]=(ia.candidate_id_for_write_shape(base.GOOD[task],name,gr['args'],gr['term'],None),ia.candidate_id_for_write_shape(base.BAD[task],'always_false',br['args'],br['term'],None))
 checks=[('lock_capture',cap['lock']==lock),('current_lock',runner.frozen()==lock),('source_stability',cap['source_stable'] and cap['post_lock']==lock),('fresh_workers',len(cap['workers'])==runner.WORKERS and len({r['pid'] for g in cap['workers'] for r in g})==runner.WORKERS),('worker_sizes',all(len(g)==1440 for g in cap['workers']))]
 rows=[r for g in cap['workers'] for r in g]; checks.append(('complete_unique_schedule',len(rows)==4320 and len({(r['worker'],r['task'],r['quality'],r['p'],r['rho'],r['providers'],r['trial']) for r in rows})==4320))
 noise_ok=[]; selection_ok=[]; receipt_ok=[]; auth_ok=[]; outcome_ok=[]; held_ok=[]; grouped=defaultdict(list)
 for row in rows:
  task=row['task']; quality=row['quality']; good,bad=parsed[task]; cand,chall=(good,bad) if quality=='correct' else (bad,good); cid=ids[task][0 if quality=='correct' else 1]
  flips=runner.correlated_flips(row['seed'],row['p'],row['rho'],row['providers']); noise_ok.append(flips==row['flips'])
  sel=select_disagreement_probe(cid,cand,[chall],[],base.DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=row['seed']); truth=oracle(task,sel['input'])
  selection_ok.append(sel['selection_id']==row['selection_id'] and sel['prediction_entropy_bits']>0 and row['truth']==truth)
  sources=[f'oracle:{task}:v1']; req=ia.propose_audit_request(cid,cand,[],[sel['input']],acquisition_source_ids=sources,count=1,seed=sel['selection_id']); probe=req['probes'][0]
  labels=[]
  for i,provider in enumerate(base.PROVIDERS[:row['providers']]):
   val=(not truth) if flips[i] else truth; raw={'source_id':provider,'label_id':f"{row['worker']}:{task}:{quality}:{row['p']}:{row['rho']}:{row['providers']}:{row['trial']}:{i}",'expected':val,'oracle_sha256':runner.sha(base.ORACLE)}
   labels.append(sign_label(raw,req['request_id'],probe['probe_id'],probe['input_sha256'],base.KEYS[provider]))
  noise_ok[-1]=noise_ok[-1] and labels==row['labels'] and req['request_id']==row['request_id']
  evidence=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':labels}]
  receipt=ia.adjudicate_audit_receipt(req,cid,cand,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=sources)
  receipt_ok.append(hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(',',':')).encode()).hexdigest()==row['receipt_hash'])
  auth=verify_signed_audit_evidence(req,evidence,receipt,base.KEYS); auth_ok.append(auth['ok'] and auth['verified_labels']==row['providers'])
  eligible=auth['ok'] and receipt['status']=='accepted' and sel['prediction_entropy_bits']>0
  outcome_ok.append(row['status']==receipt['status'] and row['adoption_eligible']==eligible)
  held=sum(native.evaluate(cand,e)==oracle(task,e) for e in base.HELD[task]); held_ok.append(row['heldout_exact']==held and row['heldout_count']==len(base.HELD[task]))
  grouped[(task,quality,row['p'],row['rho'],row['providers'])].append(row)
 checks += [('common_mode_draws_and_signed_labels',all(noise_ok)),('selected_probes_recomputed',all(selection_ok)),('receipts_recomputed',all(receipt_ok)),('provider_hmacs_verified',all(auth_ok)),('fail_closed_outcomes_recomputed',all(outcome_ok)),('heldout_scores_recomputed',all(held_ok))]
 summary=[]
 for (task,quality,p,rho,m),cell in sorted(grouped.items()):
  accepted=sum(r['status']=='accepted' for r in cell); rejected=sum(r['status']=='rejected' for r in cell); ambiguous=sum(r['status']=='ambiguous' for r in cell); eligible=sum(r['adoption_eligible'] for r in cell)
  theoretical=rho*((1-p) if quality=='correct' else p)+(1-rho)*(((1-p)**m) if quality=='correct' else p**m)
  rate=eligible/len(cell); tolerance=max(0.12,5*math.sqrt(theoretical*(1-theoretical)/len(cell)))
  checks.append((f'cell_{task}_{quality}_p{p}_rho{rho}_m{m}',len(cell)==60 and accepted+rejected+ambiguous==60 and abs(rate-theoretical)<=tolerance))
  summary.append({'task':task,'candidate_quality':quality,'p':p,'rho':rho,'providers':m,'trials':len(cell),'accepted':accepted,'rejected':rejected,'ambiguous':ambiguous,'adoption_eligible':eligible,'eligible_rate':rate,'theoretical_eligible_probability':theoretical,'heldout_exact':cell[0]['heldout_exact'],'heldout_count':cell[0]['heldout_count']})
 result={'schema':'SubstrateAdequacyCorrelatedNoiseV1Analysis','checks':[{'name':n,'pass':ok} for n,ok in checks],'passed':sum(ok for _,ok in checks),'total':len(checks),'cells':summary,'interpretation':'Common-mode error limits the value of additional provider IDs: correlated unanimous error retains a linear rho*p false-eligibility floor for wrong candidates. Refusal under any disagreement remains a central tradeoff.','limits':['two authored Boolean tasks','common-mode mixture is simulated, not estimated','mechanism-level adoption eligibility, not repeated graph writes','60 trials per task/cell']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
 if not all(ok for _,ok in checks): raise SystemExit(1)
if __name__=='__main__': main()
