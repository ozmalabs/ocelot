#!/usr/bin/env python3
"""Locked live-route threshold transfer under signed label and domain stress."""
from __future__ import annotations
import hashlib, itertools, json, os, platform, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; RUNNER=Path(__file__).resolve()
ORACLE=ROOT/'evaluation/substrate_capability/independent_threshold_oracle_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_threshold_noise_v1.py'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_THRESHOLD_NOISE_V1_2_AMENDMENT_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_threshold_noise_v1_2_lock_20261002.json'
RAW=ROOT/'evaluation/reports/substrate_adequacy_threshold_noise_v1_2_raw_20261002.json'
PROVIDERS=('threshold-oracle-a','threshold-oracle-b')
KEYS={p:hashlib.sha256(('threshold-noise-test-key:'+p).encode()).digest() for p in PROVIDERS}
GOOD='def exceeds(left, right, limit):\n    return left + right > limit\n'
BAD='def always_false(left, right, limit):\n    return False\n'
SMALL=[{'left':a,'right':b,'limit':c} for a,b,c in itertools.product(range(-3,4), repeat=3)]
ALIAS=[{'left':a,'right':b,'limit':c} for a,b,c in itertools.product(range(-2,1),range(-2,1),range(1,5))]
HELDOUT=[{'left':a,'right':b,'limit':c} for a,b,c in itertools.product((-20,-7,0,8,21),(-13,-2,5,19),(-11,-1,4,12,27))]
CASES={
 'truthful_positive':{'candidate':GOOD,'name':'exceeds','challenger':BAD,'challenger_name':'always_false','domain':SMALL,'labels':'truth','expected':'accepted','adopt':1,'heldout':'all'},
 'truthful_wrong_broad':{'candidate':BAD,'name':'always_false','challenger':GOOD,'challenger_name':'exceeds','domain':SMALL,'labels':'truth','expected':'rejected','adopt':0,'heldout':'wrong'},
 'truthful_wrong_alias':{'candidate':BAD,'name':'always_false','challenger':GOOD,'challenger_name':'exceeds','domain':ALIAS,'labels':'truth','expected':'accepted','adopt':0,'heldout':'wrong'},
 'trusted_false_label':{'candidate':BAD,'name':'always_false','challenger':GOOD,'challenger_name':'exceeds','domain':SMALL,'labels':'false','expected':'accepted','adopt':1,'heldout':'wrong'},
 'conflicting_signed_labels':{'candidate':BAD,'name':'always_false','challenger':GOOD,'challenger_name':'exceeds','domain':SMALL,'labels':'conflict','expected':'ambiguous','adopt':0,'heldout':'wrong'},
}
REPEATS=3
SOURCES=('domains/adequacy_probe_selection.py','domains/adequacy_provider_auth.py','domains/independent_adequacy.py','domains/code_reading.py','domains/code_write_growth.py','domains/code_writing.py','substrate/world_adapter.py','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/term.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(RUNNER.parent)]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree_digest(rel,suffixes):
 h=hashlib.sha256()
 for p in sorted(x for x in (ROOT/rel).rglob('*') if x.is_file() and x.suffix in suffixes): h.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 return h.hexdigest()
def active():
 import substrate_rs
 f={s:sha(ROOT/s) for s in SOURCES}; f['native_binary']=sha(substrate_rs._native.__file__); f['oracle']=sha(ORACLE); f['domains_tree']=tree_digest('domains',('.py',)); f['substrate_tree']=tree_digest('substrate',('.py',)); f['rust_tree']=tree_digest('runners/dsl/src',('.rs',))
 h=hashlib.sha256()
 for p in sorted([*ROOT.glob('seeds/*.json'),*ROOT.glob('seeds/generated/*.json')]): h.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 f['seed_inventory']=h.hexdigest(); return f
def frozen(): return {'schema':'SubstrateAdequacyThresholdNoiseV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ORACLE,PROTOCOL,ANALYZER,AMENDMENT)},'active':active(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'design':{'cases':CASES,'repeats':REPEATS,'provider_key_hashes':{k:hashlib.sha256(v).hexdigest() for k,v in KEYS.items()}}}
def shape_ids(sub): return sorted(str(n) for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction')
def worker(case,rep,lock):
 if active()!=lock['active']: raise RuntimeError('source/native/seed drift')
 from substrate.world_adapter import WorldAdapter
 from domains import code_reading as cdr, independent_adequacy as ia
 from domains.adequacy_probe_selection import select_disagreement_probe
 from domains.adequacy_provider_auth import sign_label
 from independent_threshold_oracle_v1 import label as oracle
 spec=CASES[case]; wa=WorldAdapter(shadow_read=False,deep_ingest=False,trusted_adequacy_provider_keys=KEYS,require_discriminating_code_example_probe=True)
 sub,native,_=cdr._resolve(wa); candidate_read=cdr.read_function(wa,spec['candidate'],spec['name']); challenger_read=cdr.read_function(wa,spec['challenger'],spec['challenger_name'])
 term=candidate_read.get('term'); challenger=challenger_read.get('term')
 if term is None or challenger is None: raise RuntimeError('Term parse failed')
 cid=ia.candidate_id_for_write_shape(spec['candidate'],spec['name'],candidate_read['args'],term,None)
 seed=f'threshold-noise-v1:{case}'; sources=['threshold-fixture:independent-oracle-v1']; acquisition=[]
 selection=select_disagreement_probe(cid,term,[challenger],acquisition,spec['domain'],lambda t,e:native.evaluate(t,e),seed=seed)
 context={'challenger_terms':[challenger],'acquisition_rows':acquisition,'admissible_inputs':spec['domain'],'acquisition_source_ids':sources,'seed':seed,'selection':selection}
 request=ia.propose_audit_request(cid,term,acquisition,[selection['input']],acquisition_source_ids=sources,count=1,seed=selection['selection_id']); probe=request['probes'][0]; truth=oracle(probe['inputs']); labels=[]
 vals=[truth] if spec['labels']=='truth' else [not truth] if spec['labels']=='false' else [truth,not truth]
 for i,value in enumerate(vals):
  provider=PROVIDERS[i]; raw={'source_id':provider,'label_id':f'{case}:{rep}:{i}','expected':value,'oracle_sha256':sha(ORACLE)}
  labels.append(sign_label(raw,request['request_id'],probe['probe_id'],probe['input_sha256'],KEYS[provider]))
 rows=[{'probe_id':probe['probe_id'],'inputs':probe['inputs'],'labels':labels}]
 receipt=ia.adjudicate_audit_receipt(request,cid,term,rows,lambda t,e:native.evaluate(t,e),acquisition_source_ids=sources)
 before=shape_ids(sub); reply=wa.converse(spec['candidate'],code_example_evidence={'request':request,'audit_rows':rows,'receipt':receipt,'probe_selection_context':context}); after=shape_ids(sub)
 held=[]
 for env in HELDOUT:
  predicted=native.evaluate(term,env); expected=oracle(env); held.append({'inputs':env,'prediction':predicted,'expected':expected,'match':predicted==expected})
 return {'case':case,'rep':rep,'pid':os.getpid(),'task':'sum_exceeds_limit','term':term,'challenger':challenger,'candidate_id':cid,'selection':selection,'context':context,'request':request,'rows':rows,'receipt':receipt,'truth_at_probe':truth,'labels':vals,'shape_delta':len(set(after)-set(before)),'adopted_ids':sorted(set(after)-set(before)),'heldout':held,'active_after':active(),'reply':reply}
def main():
 lock=frozen()
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('capture exists; refusing overwrite')
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1'); env['PYTHONPATH']=f'{ROOT}:{ROOT}/runners/dsl/python:{RUNNER.parent}:'
 rows=[]
 for case in CASES:
  for rep in range(1,REPEATS+1):
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',case,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode: raise RuntimeError(f'{case}/{rep}: {p.stderr[-3000:]}')
   row=json.loads(p.stdout.strip().splitlines()[-1]); rows.append(row); print(f"{case}/{rep}: receipt={row['receipt']['status']} entropy={row['selection']['prediction_entropy_bits']:.3f} adopted={row['shape_delta']} heldout={sum(x['match'] for x in row['heldout'])}/{len(row['heldout'])}",flush=True)
 post=frozen(); capture={'schema':'SubstrateAdequacyThresholdNoiseV1Capture','lock':lock,'post_lock':post,'source_stable':post==lock,'workers':rows,'schedule':[{'case':c,'rep':r} for c in CASES for r in range(1,REPEATS+1)],'host':platform.platform(),'python':sys.version}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n'); print(json.dumps({'workers':len(rows),'source_stable':capture['source_stable'],'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--worker': print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),json.loads(LOCK.read_text())),sort_keys=True))
 else: main()
