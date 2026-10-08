#!/usr/bin/env python3
"""Source-locked dose response for a common-mode mixture of provider errors."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RUNNER=Path(__file__).resolve()
BASE_PATH=ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1.py'
SPEC=importlib.util.spec_from_file_location('independent_noise_base',BASE_PATH); base=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(base)
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_CORRELATED_NOISE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_correlated_noise_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_correlated_noise_v1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_correlated_noise_v1_raw_20261002.json'
RHO=[0.0,0.5,1.0]; PROBS=[0.1,0.5]; TRIALS=20; WORKERS=3
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(BASE_PATH.parent)]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 if json.loads(base.LOCK.read_text())!=base.frozen(): raise RuntimeError('independent-noise base lock is stale')
 return {'schema':'SubstrateAdequacyCorrelatedNoiseV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,BASE_PATH,base.ORACLE,base.PROTOCOL,base.LOCK,PROTOCOL,ANALYZER)},'base_lock':base.frozen(),'design':{'rho':RHO,'p':PROBS,'provider_counts':base.COUNTS,'tasks':base.TASKS,'candidate_qualities':['correct','wrong'],'trials_per_cell_per_worker':TRIALS,'workers':WORKERS},'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def correlated_flips(seed,p,rho,count):
 rng=random.Random(seed+':correlated-noise')
 if rng.random()<rho:
  flip=rng.random()<p; return [flip]*count
 return [rng.random()<p for _ in range(count)]
def worker(wid,lock):
 if frozen()!=lock: raise RuntimeError('source/protocol lock drift')
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label
 from domains import independent_adequacy as ia
 from independent_adequacy_noise_oracles_v1 import label as oracle
 import substrate_rs
 native=substrate_rs._native.Substrate(); parsed={}; candidate_ids={}
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr
 for task in base.TASKS:
  wa=WorldAdapter(shadow_read=False,deep_ingest=False); _,eng,_=cdr._resolve(wa)
  name='parity' if task=='parity' else 'exceeds'; alt='always_false'
  good_read=cdr.read_function(wa,base.GOOD[task],name); bad_read=cdr.read_function(wa,base.BAD[task],alt)
  good,bad=good_read.get('term'),bad_read.get('term')
  if good is None or bad is None: raise RuntimeError('Term parsing failed')
  parsed[task]=(good,bad); candidate_ids[task]=(ia.candidate_id_for_write_shape(base.GOOD[task],name,good_read['args'],good,None),ia.candidate_id_for_write_shape(base.BAD[task],alt,bad_read['args'],bad,None))
 output=[]
 for task in base.TASKS:
  good,bad=parsed[task]
  for quality in ('correct','wrong'):
   candidate,challenger=(good,bad) if quality=='correct' else (bad,good); cid=candidate_ids[task][0 if quality=='correct' else 1]
   for p in PROBS:
    for rho in RHO:
     for count in base.COUNTS:
      for trial in range(TRIALS):
       seed=f'corr-noise-v1:{wid}:{task}:{quality}:{p}:{rho}:{count}:{trial}'
       selection=select_disagreement_probe(cid,candidate,[challenger],[],base.DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=seed)
       sources=[f'oracle:{task}:v1']; request=ia.propose_audit_request(cid,candidate,[],[selection['input']],acquisition_source_ids=sources,count=1,seed=selection['selection_id']); probe=request['probes'][0]; truth=oracle(task,probe['inputs'])
       flips=correlated_flips(seed,p,rho,count); labels=[]; sigs=[]
       for i,provider in enumerate(base.PROVIDERS[:count]):
        value=(not truth) if flips[i] else truth; raw={'source_id':provider,'label_id':f'{wid}:{task}:{quality}:{p}:{rho}:{count}:{trial}:{i}','expected':value,'oracle_sha256':sha(base.ORACLE)}
        signed=sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],base.KEYS[provider]); labels.append(signed); sigs.append(signed['signature'])
       evidence=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':labels}]
       receipt=ia.adjudicate_audit_receipt(request,cid,candidate,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=sources)
       auth=base.verify_signed_audit_evidence(request,evidence,receipt,base.KEYS) if hasattr(base,'verify_signed_audit_evidence') else None
       # The base module imports the signer only inside its worker; import verifier directly here.
       from domains.adequacy_provider_auth import verify_signed_audit_evidence
       auth=verify_signed_audit_evidence(request,evidence,receipt,base.KEYS)
       eligible=auth['ok'] and receipt['status']=='accepted' and selection['prediction_entropy_bits']>0
       held=sum(native.evaluate(candidate,e)==oracle(task,e) for e in base.HELD[task])
       output.append({'worker':wid,'pid':os.getpid(),'task':task,'quality':quality,'p':p,'rho':rho,'providers':count,'trial':trial,'seed':seed,'flips':flips,'labels':labels,'truth':truth,'status':receipt['status'],'adoption_eligible':eligible,'receipt_hash':hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'selection_id':selection['selection_id'],'request_id':request['request_id'],'heldout_exact':held,'heldout_count':len(base.HELD[task])})
 return output
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=f'{ROOT}:{ROOT}/runners/dsl/python:{BASE_PATH.parent}:'
 workers=[]
 for wid in range(1,WORKERS+1):
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',str(wid)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
  if proc.returncode: raise RuntimeError(proc.stderr[-4000:])
  rows=json.loads(proc.stdout.strip().splitlines()[-1]); workers.append(rows); print(f'worker {wid}: {len(rows)} trials',flush=True)
 cap={'schema':'SubstrateAdequacyCorrelatedNoiseV1Capture','lock':lock,'post_lock':frozen(),'source_stable':frozen()==lock,'workers':workers,'host':platform.platform(),'python':sys.version}
 RAW.write_text(json.dumps(cap,separators=(',',':'))+'\n'); print(json.dumps({'workers':len(workers),'trials':sum(map(len,workers)),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--worker': print(json.dumps(worker(int(sys.argv[2]),json.loads(LOCK.read_text())),separators=(',',':')))
 else: main()
