#!/usr/bin/env python3
"""Locked fresh-process gate for opt-in request-level code contracts."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CODE_WRITE_CONTRACT_VALIDATION_V1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_code_write_contract_validation_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_contract_validation_v1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_code_write_contract_validation_v1_raw_20261001.json'
SOURCE='def parity(value):\n    return value % 2 == 0\n'
PARITY='Write a function that returns the parity of an integer.'
SQUARE='Write a function that squares an integer.'
PARITY_CASES=[{'inputs':{'value':v},'expected':v%2==0} for v in (-7,-2,0,3,8)]
SQUARE_CASES=[{'inputs':{'value':v},'expected':v*v} for v in (-7,-2,0,3,8)]
ACTIVE=('domains/code_reading.py','domains/code_writing.py','domains/code_write_growth.py','domains/ast_to_term.py',
 'domains/teach.py','substrate/world_adapter.py','substrate/boot_all.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
 'seeds/code_constructions.json','seeds/code_write_constructions.json','seeds/code_write_request_cues.json',
 'seeds/code_write_gap.json','seeds/gap_awareness.json')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(paths,suffixes):
 entries=[]
 for rel in paths:
  p=ROOT/rel
  for f in ([p] if p.is_file() else sorted(x for x in p.rglob('*') if x.is_file())):
   if f.suffix in suffixes or f.name in {'_native.abi3.so','_native.build.json'}: entries.append((f.relative_to(ROOT).as_posix(),sha(f)))
 h=hashlib.sha256()
 for a,b in sorted(entries): h.update(a.encode()+b'\0'+b.encode()+b'\n')
 return h.hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
 import substrate_rs as srs
 r={x:sha(ROOT/x) for x in ACTIVE}; r['native']=sha(Path(srs._native.__file__).resolve()); return r
def seedsha():
 files=sorted([*(ROOT/'seeds').glob('*.json'),*(ROOT/'seeds/generated').glob('*.json')]); h=hashlib.sha256()
 for p in files: h.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 return h.hexdigest()
def payload():
 return {'schema':'SubstrateCodeWriteContractValidationV1Lock',
  'files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},'active':active(),
  'trees':{'domains':tree(('domains',),('.py',)),'substrate':tree(('substrate',),('.py',)),
   'seed_manifests':seedsha(),'rust':tree(('runners/dsl/src',),('.rs',)),
   'python_native':tree(('runners/dsl/python/substrate_rs',),('.py',))},
  'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'design':{'arms':['aligned_parity','mismatched_parity_as_square'],'repetitions':2,'seed':20261021,
   'source':SOURCE,'parity_request':PARITY,'square_request':SQUARE,'parity_contract':PARITY_CASES,'square_contract':SQUARE_CASES}}
def worker(arm,rep):
 os.environ.setdefault('OZMA_NO_LLM','1'); os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 lock=json.loads(LOCK.read_text()); before=active()
 if before!=lock['active']: raise RuntimeError('active source differs from lock')
 from domains import code_reading as cdr,code_write_growth as cwg
 from substrate.boot_all import load_all_seeds
 from substrate.world_adapter import WorldAdapter
 agent=WorldAdapter(seeds=()); t=time.perf_counter_ns(); boot=load_all_seeds(agent); boot_ns=time.perf_counter_ns()-t
 sub,_,_=cdr._resolve(agent); shapes0=[n for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction']
 if arm=='aligned_parity': req,cases=PARITY,PARITY_CASES
 else: req,cases=SQUARE,SQUARE_CASES
 t=time.perf_counter_ns(); result=cwg.teach_write_shape_from_example(agent,SOURCE,request_text=req,contract_examples=cases); acquire_ns=time.perf_counter_ns()-t
 shapes1=[n for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction']
 post=active()
 return {'kind':'worker','arm':arm,'rep':rep,'pid':os.getpid(),'source_stable':before==post,'before':before,'after':post,
  'boot_ns':boot_ns,'boot_loaded':len(getattr(boot,'loaded',[]) or []),'shape_count_before':len(shapes0),'shape_count_after':len(shapes1),
  'taught_shape_present':any(sub.node(n)['attrs'].get('name')=='taught_parity' for n in shapes1),
  'result':result,'acquire_ns':acquire_ns,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 current=payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=current: raise SystemExit('missing/stale lock')
 if RAW.exists(): raise SystemExit('refusing overwrite capture')
 schedule=[(a,r) for a in ('aligned_parity','mismatched_parity_as_square') for r in (1,2)];random.Random(20261021).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1');env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 rows=[];start=time.perf_counter()
 for i,(a,r) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',a,str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','arm':a,'rep':r,'error':p.stderr[-4000:]}
  rows.append(row);print(f'{i}/4 {a} r={r}: {row["kind"]}',flush=True)
 post=payload();RAW.write_text(json.dumps({'schema':'SubstrateCodeWriteContractValidationV1Capture','lock':current,'post_lock':post,'schedule':[{'arm':a,'rep':r} for a,r in schedule],'workers':rows,'elapsed_seconds':time.perf_counter()-start,'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(rows),'errors':sum(x.get('kind')!='worker' for x in rows),'stable':current==post}))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str))
 else:main()
