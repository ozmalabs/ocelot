#!/usr/bin/env python3
"""Source-locked offline comparison of provider vote thresholds."""
from __future__ import annotations
import hashlib,importlib.util,json,math,subprocess,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SCRIPT=Path(__file__).resolve()
PROTO=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_POLICY_TRADEOFF_V1_PREREG_20261002.md'
RAW_I=ROOT/'evaluation/reports/substrate_adequacy_stochastic_noise_v1_raw_20261002.json'; ANA_I=ROOT/'evaluation/reports/substrate_adequacy_stochastic_noise_v1_analysis_20261002.json'; LOCK_I=ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1_1_lock_20261002.json'
RAW_C=ROOT/'evaluation/reports/substrate_adequacy_correlated_noise_v1_raw_20261002.json'; ANA_C=ROOT/'evaluation/reports/substrate_adequacy_correlated_noise_v1_analysis_20261002.json'; LOCK_C=ROOT/'evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1_lock_20261002.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_policy_tradeoff_v1_lock_20261002.json'; OUT=ROOT/'evaluation/reports/substrate_adequacy_policy_tradeoff_v1_analysis_20261002.json'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def import_file(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def frozen():
 files=(SCRIPT,PROTO,RAW_I,ANA_I,LOCK_I,RAW_C,ANA_C,LOCK_C)
 return {'schema':'SubstrateAdequacyPolicyTradeoffV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in files},'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'policies':{'unanimity':'q=m','majority':'q=floor(m/2)+1','supermajority_80':'q=ceil(0.8*m)'},'input_panels':['independent_noise_v1','correlated_noise_v1']}
def threshold(policy,m):
 if policy=='unanimity': return m
 if policy=='majority': return m//2+1
 return math.ceil(.8*m)
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(frozen(),indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock: raise SystemExit('stale lock or inputs')
 base=import_file('noise_base',ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py'); corr=import_file('noise_corr',ROOT/'evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1.py')
 if json.loads(LOCK_I.read_text())!=base.frozen() or json.loads(LOCK_C.read_text())!=corr.frozen(): raise SystemExit('upstream panel source lock no longer current')
 raw_i=json.loads(RAW_I.read_text()); raw_c=json.loads(RAW_C.read_text()); ana_i=json.loads(ANA_I.read_text()); ana_c=json.loads(ANA_C.read_text())
 if not (raw_i['source_stable'] and raw_c['source_stable'] and ana_i['passed']==ana_i['total'] and ana_c['passed']==ana_c['total']): raise SystemExit('upstream capture or analysis gate failure')
 from domains import independent_adequacy as ia
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label,verify_signed_audit_evidence
 from independent_adequacy_noise_oracles_v1 import label as oracle
 import substrate_rs
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr
 native=substrate_rs._native.Substrate(); parsed={}; cids={}
 for task in base.TASKS:
  wa=WorldAdapter(shadow_read=False,deep_ingest=False); _,eng,_=cdr._resolve(wa); name='parity' if task=='parity' else 'exceeds'
  gr=cdr.read_function(wa,base.GOOD[task],name); br=cdr.read_function(wa,base.BAD[task],'always_false'); parsed[task]=(gr['term'],br['term'])
  cids[task]=(ia.candidate_id_for_write_shape(base.GOOD[task],name,gr['args'],gr['term'],None),ia.candidate_id_for_write_shape(base.BAD[task],'always_false',br['args'],br['term'],None))
 rows=[]
 for panel,raw in (('independent',raw_i),('common_mode',raw_c)):
  for worker_rows in raw['workers']:
   for item in worker_rows:
    task=item['task']; quality=item['quality']; p=item['p']; rho=item.get('rho',0.0); m=item['providers']; good,bad=parsed[task]; candidate,challenger=(good,bad) if quality=='correct' else (bad,good); cid=cids[task][0 if quality=='correct' else 1]
    seed=item['seed']; select=select_disagreement_probe(cid,candidate,[challenger],[],base.DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=seed); truth=oracle(task,select['input']); request=ia.propose_audit_request(cid,candidate,[],[select['input']],acquisition_source_ids=[f'oracle:{task}:v1'],count=1,seed=select['selection_id']); probe=request['probes'][0]
    if panel=='independent': labels=item['evidence'][0]['labels']; flips=item['flipped']
    else: labels=item['labels']; flips=item['flips']
    expected_values=[(not truth) if f else truth for f in flips]
    if [x['expected'] for x in labels]!=expected_values: raise SystemExit('captured labels disagree with upstream noise process')
    evidence=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':labels}]
    receipt=ia.adjudicate_audit_receipt(request,cid,candidate,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=[f'oracle:{task}:v1'])
    verified=verify_signed_audit_evidence(request,evidence,receipt,base.KEYS)
    if not verified['ok']: raise SystemExit('signature verification failed during policy replay')
    pred=native.evaluate(candidate,select['input']); truth=(oracle(task,select['input']))
    if select['prediction_entropy_bits']<=0 or truth is not True or (quality=='correct' and pred!=truth) or (quality=='wrong' and pred==truth): raise SystemExit('case no longer has the preregistered discriminating relation')
    if panel=='independent' and (receipt!=item['receipt'] or receipt['status']!=item['receipt']['status']): raise SystemExit('independent receipt replay mismatch')
    if panel=='common_mode' and receipt['status']!=item['status']: raise SystemExit('common-mode receipt replay mismatch')
    for policy in ('unanimity','majority','supermajority_80'):
     q=threshold(policy,m); candidate_votes=sum(x['expected']==pred for x in labels); adopted=candidate_votes>=q
     rows.append({'panel':panel,'task':task,'quality':quality,'p':p,'rho':rho,'providers':m,'policy':policy,'threshold':q,'adopted':adopted,'truth':truth,'provider_values':[x['expected'] for x in labels]})
 grouped=defaultdict(list)
 for r in rows: grouped[(r['panel'],r['task'],r['quality'],r['p'],r['rho'],r['providers'],r['policy'])].append(r)
 summaries=[]; checks=[('input_source_locks',True),('upstream_all_gates',True),('replayed_every_captured_row',len(rows)==(2160+4320)*3)]
 for key,cell in sorted(grouped.items()):
  panel,task,quality,p,rho,m,policy=key; adopted=sum(r['adopted'] for r in cell); n=len(cell)
  q=threshold(policy,m)
  if quality=='correct': theoretical=(rho*(1-p)+(1-rho)*sum(math.comb(m,k)*(p**k)*((1-p)**(m-k)) for k in range(m-q+1))) if panel=='common_mode' else sum(math.comb(m,k)*(p**k)*((1-p)**(m-k)) for k in range(m-q+1))
  else: theoretical=(rho*p+(1-rho)*sum(math.comb(m,k)*(p**k)*((1-p)**(m-k)) for k in range(q,m+1))) if panel=='common_mode' else sum(math.comb(m,k)*(p**k)*((1-p)**(m-k)) for k in range(q,m+1))
  summaries.append({'panel':panel,'task':task,'quality':quality,'p':p,'rho':rho,'providers':m,'policy':policy,'threshold':q,'trials':n,'eligible':adopted,'rate':adopted/n,'exact_model_probability':theoretical})
  checks.append((f'cell_{panel}_{task}_{quality}_p{p}_rho{rho}_m{m}_{policy}',n==60 and abs(adopted/n-theoretical)<=max(.12,5*math.sqrt(theoretical*(1-theoretical)/n))))
 out={'schema':'SubstrateAdequacyPolicyTradeoffV1Analysis','checks':[{'name':n,'pass':ok} for n,ok in checks],'passed':sum(ok for _,ok in checks),'total':len(checks),'summaries':summaries,'limits':['post-capture offline sensitivity analysis','vote thresholds are hypothetical, not implemented','simulated source independence/correlation','equal label count only; compute cost and live writes not measured']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':out['passed'],'total':out['total'],'summary_count':len(summaries),'out':str(OUT.relative_to(ROOT))},indent=2))
 if not all(ok for _,ok in checks): raise SystemExit(1)
if __name__=='__main__': main()
