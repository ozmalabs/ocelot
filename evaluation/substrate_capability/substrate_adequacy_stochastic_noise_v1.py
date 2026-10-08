#!/usr/bin/env python3
"""Locked multi-task response curve for signed Bernoulli label noise."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RUNNER=Path(__file__).resolve()
ORACLE=ROOT/'evaluation/substrate_capability/independent_adequacy_noise_oracles_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_STOCHASTIC_NOISE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_stochastic_noise_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_stochastic_noise_v1_1_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_stochastic_noise_v1_raw_20261002.json'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_STOCHASTIC_NOISE_V1_1_AMENDMENT_20261002.md'
PROVIDERS=[f'noise-provider-{i}' for i in range(5)]
KEYS={p:hashlib.sha256(('noise-dose-test-key:'+p).encode()).digest() for p in PROVIDERS}
GOOD={'parity':'def parity(value):\n    return value % 2 == 0\n','threshold':'def exceeds(left, right, limit):\n    return left + right > limit\n'}
BAD={'parity':'def always_false(value):\n    return False\n','threshold':'def always_false(left, right, limit):\n    return False\n'}
DOMAINS={'parity':[{'value':x} for x in range(-8,9)],'threshold':[{'left':a,'right':b,'limit':c} for a,b,c in itertools.product(range(-4,5),repeat=3)]}
HELD={'parity':[{'value':x} for x in range(-50,51)],'threshold':[{'left':a,'right':b,'limit':c} for a,b,c in itertools.product((-20,-7,0,8,21),(-13,-2,5,19),(-11,-1,4,12,27))]}
TASKS=['parity','threshold']; PROBS=[0.0,0.1,0.5]; COUNTS=[1,3,5]; TRIALS=20; WORKERS=3
SOURCE_FILES=('domains/adequacy_probe_selection.py','domains/adequacy_provider_auth.py','domains/independent_adequacy.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/src/term.rs')
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(RUNNER.parent)]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(rel,suffixes):
 h=hashlib.sha256()
 for p in sorted(x for x in (ROOT/rel).rglob('*') if x.is_file() and x.suffix in suffixes): h.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 return h.hexdigest()
def active():
 import substrate_rs
 f={s:sha(ROOT/s) for s in SOURCE_FILES}; f.update(native=sha(substrate_rs._native.__file__),oracle=sha(ORACLE),adequacy_tree=tree('domains',('.py',)))
 return f
def frozen(): return {'schema':'SubstrateAdequacyStochasticNoiseV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ORACLE,PROTOCOL,ANALYZER,AMENDMENT)},'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'tasks':TASKS,'flip_probabilities':PROBS,'provider_counts':COUNTS,'trials_per_cell_per_worker':TRIALS,'workers':WORKERS,'key_hashes':{k:hashlib.sha256(v).hexdigest() for k,v in KEYS.items()}}}
def run_worker(worker_id,lock):
 if active()!=lock['active']: raise RuntimeError('source/native drift')
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label,verify_signed_audit_evidence
 from domains import independent_adequacy as ia
 from independent_adequacy_noise_oracles_v1 import label as oracle
 import substrate_rs
 native=substrate_rs._native.Substrate(); terms={}; ids={}
 for task in TASKS:
  src=GOOD[task] if task=='parity' else GOOD['threshold']; alt=BAD[task]
  # Parse the authored Terms with the same native AST reader used by acquisition.
  from substrate.world_adapter import WorldAdapter
  from domains import code_reading as cdr
  wa=WorldAdapter(shadow_read=False,deep_ingest=False); _,eng,_=cdr._resolve(wa)
  good_name='parity' if task=='parity' else 'exceeds'; bad_name='always_false'
  good_read=cdr.read_function(wa,src,good_name); bad_read=cdr.read_function(wa,alt,bad_name)
  good=good_read['term']; bad=bad_read['term']
  if good is None or bad is None: raise RuntimeError('task Term parse failed')
  terms[task]=(good,bad)
  ids[task]=(ia.candidate_id_for_write_shape(src,good_name,good_read['args'],good,None),ia.candidate_id_for_write_shape(alt,bad_name,bad_read['args'],bad,None))
 rows=[]
 for task,quality,p,n in itertools.product(TASKS,('correct','wrong'),PROBS,COUNTS):
  good,bad=terms[task]; candidate=good if quality=='correct' else bad; challenger=bad if quality=='correct' else good; cid=ids[task][0 if quality=='correct' else 1]
  for trial in range(TRIALS):
   seed=f'noise-dose-v1:{worker_id}:{task}:{quality}:{p}:{n}:{trial}'
   selection=select_disagreement_probe(cid,candidate,[challenger],[],DOMAINS[task],lambda t,e:native.evaluate(t,e),seed=seed)
   sources=[f'oracle:{task}:v1']; request=ia.propose_audit_request(cid,candidate,[],[selection['input']],acquisition_source_ids=sources,count=1,seed=selection['selection_id']); probe=request['probes'][0]
   truth=oracle(task,probe['inputs']); rng=random.Random(seed+':noise'); labels=[]; flipped=[]
   for i,provider in enumerate(PROVIDERS[:n]):
    flip=rng.random()<p; value=(not truth) if flip else truth; flipped.append(flip)
    raw={'source_id':provider,'label_id':f'{worker_id}:{task}:{quality}:{p}:{n}:{trial}:{i}','expected':value,'oracle_sha256':sha(ORACLE)}
    labels.append(sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],KEYS[provider]))
   evidence=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':labels}]
   receipt=ia.adjudicate_audit_receipt(request,cid,candidate,evidence,lambda t,e:native.evaluate(t,e),acquisition_source_ids=sources)
   auth=verify_signed_audit_evidence(request,evidence,receipt,KEYS)
   held=[native.evaluate(candidate,env)==oracle(task,env) for env in HELD[task]]
   eligible=receipt['status']=='accepted' and selection['prediction_entropy_bits']>0 and auth['ok']
   rows.append({'worker':worker_id,'pid':os.getpid(),'task':task,'quality':quality,'p':p,'providers':n,'trial':trial,'seed':seed,'candidate':candidate,'challenger':challenger,'candidate_id':cid,'selection':selection,'request':request,'evidence':evidence,'receipt':receipt,'auth_ok':auth['ok'],'adoption_eligible':eligible,'flipped':flipped,'truth':truth,'heldout_exact':sum(held),'heldout_count':len(held)})
 return rows
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale source lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=f'{ROOT}:{ROOT}/runners/dsl/python:{RUNNER.parent}:'
 workers=[]
 for wid in range(1,WORKERS+1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(wid)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
  if p.returncode: raise RuntimeError(p.stderr[-4000:])
  data=json.loads(p.stdout.strip().splitlines()[-1]); workers.append(data); print(f'worker {wid}: {len(data)} trials',flush=True)
 post=frozen(); cap={'schema':'SubstrateAdequacyStochasticNoiseV1Capture','lock':lock,'post_lock':post,'source_stable':post==lock,'workers':workers,'host':platform.platform(),'python':sys.version}
 RAW.write_text(json.dumps(cap,indent=2,sort_keys=True)+'\n'); print(json.dumps({'workers':len(workers),'trials':sum(map(len,workers)),'source_stable':cap['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--worker': print(json.dumps(run_worker(int(sys.argv[2]),json.loads(LOCK.read_text())),sort_keys=True))
 else: main()
