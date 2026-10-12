#!/usr/bin/env python3
"""Independent semantic replay and cost summaries for strict live route."""
import importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_live_route_cost_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_live_route_cost_v1_analysis_20261002.json'
def import_file(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def main():
 runner=import_file('live_route_runner',ROOT/'evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1.py'); base=runner.base
 lock=json.loads(LOCK.read_text()); capture=json.loads(RAW.read_text())
 if runner.frozen()!=lock or capture['lock']!=lock or capture['post_lock']!=lock or not capture['source_stable']: raise SystemExit('source/native lock mismatch')
 from domains import independent_adequacy as ia
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label,verify_signed_audit_evidence
 from independent_adequacy_noise_oracles_v1 import label as oracle
 import substrate_rs
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr
 native=substrate_rs._native.Substrate(); parsed={}; candidate_ids={}
 for task in base.TASKS:
  wa=WorldAdapter(shadow_read=False,deep_ingest=False); _,eng,_=cdr._resolve(wa); good_name='parity' if task=='parity' else 'exceeds'; bad_name='always_false'
  gr=cdr.read_function(wa,base.GOOD[task],good_name); br=cdr.read_function(wa,base.BAD[task],bad_name); parsed[task]=(gr,br)
  candidate_ids[task]=(ia.candidate_id_for_write_shape(base.GOOD[task],good_name,gr['args'],gr['term'],None),ia.candidate_id_for_write_shape(base.BAD[task],bad_name,br['args'],br['term'],None))
 rows=capture['workers']; cases=runner.CASES; tasks=base.TASKS; counts=base.COUNTS
 expected_schedule={(t,c,m,r) for t in tasks for c in cases for m in counts if not(c=='conflicting_signed_labels' and m==1) for r in range(1,runner.REPEATS+1)}
 observed={(r['task'],r['case'],r['providers'],r['rep']) for r in rows}
 checks=[('fresh_worker_count',len(rows)==len(expected_schedule)==66 and len({r['pid'] for r in rows})==len(rows)),('complete_schedule',observed==expected_schedule),('post_worker_source_stability',all(r['active_after']==lock['active'] for r in rows)),('timings_present_positive',all(r['process_wall_ns']>0 and all(v>0 for v in r['timing_ns'].values()) for r in rows))]
 selection_ok=[]; request_ok=[]; labels_ok=[]; receipt_ok=[]; auth_ok=[]; outcome_ok=[]; heldout_ok=[]
 for row in rows:
  task=row['task']; case=row['case']; m=row['providers']; rep=row['rep']; gr,br=parsed[task]; good_name='parity' if task=='parity' else 'exceeds'
  if case=='truthful_correct': source,name,other,other_name=base.GOOD[task],good_name,base.BAD[task],'always_false'; quality='correct'
  else: source,name,other,other_name=base.BAD[task],'always_false',base.GOOD[task],good_name; quality='wrong'
  term=(gr if quality=='correct' else br)['term']; challenger=(br if quality=='correct' else gr)['term']; cid=candidate_ids[task][0 if quality=='correct' else 1]
  seed=f'live-route-cost-v1:{task}:{case}:{m}:{rep}'; sel=select_disagreement_probe(cid,term,[challenger],[],base.DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=seed)
  selection_ok.append(sel==row['selection'] and sel['prediction_entropy_bits']>0)
  source_ids=[f'oracle:{task}:v1']; req=ia.propose_audit_request(cid,term,[],[sel['input']],acquisition_source_ids=source_ids,count=1,seed=sel['selection_id']); request_ok.append(req==row['request'] and row['context']['selection']==sel)
  truth=oracle(task,sel['input']); values=([not truth]*m if case=='trusted_false_label' else ([truth]*((m+1)//2)+[not truth]*(m//2) if case=='conflicting_signed_labels' else [truth]*m))
  labels=[]
  for i,provider in enumerate(base.PROVIDERS[:m]):
   raw={'source_id':provider,'label_id':f'{task}:{case}:{m}:{rep}:{i}','expected':values[i],'oracle_sha256':runner.sha(base.ORACLE)}
   labels.append(sign_label(raw,req['request_id'],req['probes'][0]['probe_id'],req['probes'][0]['input_sha256'],base.KEYS[provider]))
  labels_ok.append(labels==row['rows'][0]['labels'] and values==row['labels_expected'])
  evidence=[{'probe_id':req['probes'][0]['probe_id'],'inputs':req['probes'][0]['inputs'],'labels':labels}]
  receipt=ia.adjudicate_audit_receipt(req,cid,term,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=source_ids); receipt_ok.append(receipt==row['receipt'])
  auth=verify_signed_audit_evidence(req,evidence,receipt,base.KEYS); auth_ok.append(auth==row['auth'] and auth['ok'])
  statuses={'truthful_correct':'accepted','truthful_wrong':'rejected','trusted_false_label':'accepted','conflicting_signed_labels':'ambiguous'}
  adopts=case in ('truthful_correct','trusted_false_label')
  exact=sum(native.evaluate(term,e)==oracle(task,e) for e in base.HELD[task]); matches=sum(x['prediction']==x['expected'] for x in row['heldout'])
  outcome_ok.append(receipt['status']==statuses[case] and row['shape_delta']==int(adopts) and len(row['added_shapes'])==row['shape_delta'] and ((exact==len(base.HELD[task])) if case=='truthful_correct' else (exact<len(base.HELD[task]))) and row['truth']==truth)
  heldout_ok.append(len(row['heldout'])==len(base.HELD[task]) and matches==exact and all(x['expected']==oracle(task,x['inputs']) and x['prediction']==native.evaluate(term,x['inputs']) for x in row['heldout']))
 checks += [('selections_recomputed',all(selection_ok)),('requests_recomputed',all(request_ok)),('signed_labels_recomputed',all(labels_ok)),('receipts_recomputed',all(receipt_ok)),('provider_auth_recomputed',all(auth_ok)),('actual_live_outcomes',all(outcome_ok)),('heldouts_recomputed',all(heldout_ok))]
 # Analyze medians by exact workload cell; preserve samples as raw records.
 groups={}
 for task in tasks:
  for case in cases:
   for m in counts:
    cell=[r for r in rows if r['task']==task and r['case']==case and r['providers']==m]
    if not cell: continue
    def med_ns(key): return statistics.median(r['timing_ns'][key] for r in cell)/1e6
    groups[f'{task}/{case}/m{m}']={'n':len(cell),'receipt_status':cell[0]['receipt']['status'],'adoption_rate':sum(r['shape_delta'] for r in cell)/len(cell),'heldout_exact_per_run':sum(x['prediction']==x['expected'] for x in cell[0]['heldout']),'heldout_count':len(cell[0]['heldout']),'median_ms':{'process_wall':statistics.median(r['process_wall_ns'] for r in cell)/1e6,'adapter_construct':med_ns('adapter_construct'),'probe_selection':med_ns('probe_selection'),'request_signing':med_ns('request_signing'),'receipt_adjudication':med_ns('receipt_adjudication'),'live_converse':med_ns('live_converse'),'pipeline_after_ready':med_ns('pipeline_after_ready')}}
 result={'schema':'SubstrateAdequacyLiveRouteCostV1Analysis','checks':[{'name':n,'pass':ok} for n,ok in checks],'passed':sum(ok for _,ok in checks),'total':len(checks),'cells':groups,'limits':['two authored tasks, one host, three repetitions per cell','microbenchmark and fresh process wall are descriptive','test providers and synthetic domains','false signer outcome is an expected failure, not label truth']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':result['passed'],'total':result['total'],'cells':len(groups),'analysis':str(OUT.relative_to(ROOT))},indent=2))
 if not all(ok for _,ok in checks): raise SystemExit(1)
if __name__=='__main__': main()
