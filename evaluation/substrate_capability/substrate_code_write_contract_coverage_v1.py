#!/usr/bin/env python3
"""Locked adversarial contract-coverage experiment for code-write teaching."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CODE_WRITE_CONTRACT_COVERAGE_V1_PREREG_20261001.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_code_write_contract_coverage_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_code_write_contract_coverage_v1_lock_20261001.json'
RAW=ROOT/'evaluation/reports/substrate_code_write_contract_coverage_v1_raw_20261001.json'
SOURCE='def identity(value):\n    return value\n';REQUEST='Write a function that squares an integer.'
NARROW=[{'inputs':{'value':0},'expected':0},{'inputs':{'value':1},'expected':1}]
WIDE=NARROW+[{'inputs':{'value':2},'expected':4}]
HELDOUT=[{'value':-3},{'value':-2},{'value':2},{'value':3}]
ACTIVE=('domains/code_reading.py','domains/code_writing.py','domains/code_write_growth.py','domains/ast_to_term.py',
 'domains/teach.py','substrate/world_adapter.py','substrate/boot_all.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
 'seeds/code_constructions.json','seeds/code_write_constructions.json','seeds/code_write_request_cues.json','seeds/code_write_gap.json','seeds/gap_awareness.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(paths,suffixes):
 entries=[]
 for rel in paths:
  p=ROOT/rel
  for f in ([p] if p.is_file() else sorted(x for x in p.rglob('*') if x.is_file())):
   if f.suffix in suffixes or f.name in {'_native.abi3.so','_native.build.json'}:entries.append((f.relative_to(ROOT).as_posix(),sha(f)))
 h=hashlib.sha256()
 for a,b in sorted(entries):h.update(a.encode()+b'\0'+b.encode()+b'\n')
 return h.hexdigest()
def active():
 sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')];import substrate_rs as srs
 r={x:sha(ROOT/x) for x in ACTIVE};r['native']=sha(Path(srs._native.__file__).resolve());return r
def seedsha():
 files=sorted([*(ROOT/'seeds').glob('*.json'),*(ROOT/'seeds/generated').glob('*.json')]);h=hashlib.sha256()
 for p in files:h.update(p.relative_to(ROOT).as_posix().encode()+b'\0'+sha(p).encode()+b'\n')
 return h.hexdigest()
def payload():
 return {'schema':'SubstrateCodeWriteContractCoverageV1Lock','files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL)},
  'active':active(),'trees':{'domains':tree(('domains',),('.py',)),'substrate':tree(('substrate',),('.py',)),'seed_manifests':seedsha(),'rust':tree(('runners/dsl/src',),('.rs',)),'python_native':tree(('runners/dsl/python/substrate_rs',),('.py',))},
  'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'design':{'arms':['aliasing_narrow','discriminating_wide'],'repetitions':2,'seed':20261023,'source':SOURCE,'request':REQUEST,'narrow':NARROW,'wide':WIDE,'heldout':HELDOUT}}
def worker(arm,rep):
 os.environ.setdefault('OZMA_NO_LLM','1');os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1');lock=json.loads(LOCK.read_text());before=active()
 if before!=lock['active']:raise RuntimeError('active source differs from lock')
 from domains import code_reading as cdr,code_writing as cw,code_write_growth as cwg
 from substrate.boot_all import load_all_seeds
 from substrate.world_adapter import WorldAdapter
 agent=WorldAdapter(seeds=());t=time.perf_counter_ns();boot=load_all_seeds(agent);boot_ns=time.perf_counter_ns()-t
 sub,native,_=cdr._resolve(agent);shapes0=[n for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction']
 contract=NARROW if arm=='aliasing_narrow' else WIDE
 t=time.perf_counter_ns();teach=cwg.teach_write_shape_from_example(agent,SOURCE,request_text=REQUEST,contract_examples=contract);acquire_ns=time.perf_counter_ns()-t
 composed=cw.compose_function_from_request(agent,REQUEST);written=cw.write_function_from_request(agent,REQUEST,name='candidate')
 ns={}
 try:exec(written.get('source',''),ns);fn=ns.get('candidate')
 except Exception:fn=None
 held=[]
 for env in HELDOUT:
  nv=native.evaluate(composed['term'],env) if composed.get('ok') else None
  try:pv=fn(**env) if callable(fn) else None
  except Exception as e:pv={'error':type(e).__name__}
  held.append({'input':env,'native':nv,'python':pv})
 shapes1=[n for n in sub.nodes('ShapeSignature') if sub.node(n)['attrs'].get('kind')=='code_write_construction'];after=active()
 return {'kind':'worker','arm':arm,'rep':rep,'pid':os.getpid(),'source_stable':before==after,'before':before,'after':after,
  'boot_ns':boot_ns,'shape_count_before':len(shapes0),'shape_count_after':len(shapes1),'taught_identity_present':any(sub.node(n)['attrs'].get('name')=='taught_identity' for n in shapes1),
  'teach':teach,'compose':composed,'written':{k:written.get(k) for k in ('ok','construction','source','sample_ok')},'heldout':held,'acquire_ns':acquire_ns,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return
 current=payload()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=current:raise SystemExit('missing/stale lock')
 if RAW.exists():raise SystemExit('refusing overwrite capture')
 schedule=[(a,r) for a in ('aliasing_narrow','discriminating_wide') for r in (1,2)];random.Random(20261023).shuffle(schedule)
 env=dict(os.environ,OZMA_NO_LLM='1',OZMA_SEED_PERSIST_DISABLED='1');env['PYTHONPATH']=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
 rows=[];start=time.perf_counter()
 for i,(a,r) in enumerate(schedule,1):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',a,str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
  row=json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode==0 else {'kind':'worker_error','arm':a,'rep':r,'error':p.stderr[-4000:]}
  rows.append(row);print(f'{i}/4 {a} r={r}: {row["kind"]}',flush=True)
 post=payload();RAW.write_text(json.dumps({'schema':'SubstrateCodeWriteContractCoverageV1Capture','lock':current,'post_lock':post,'schedule':[{'arm':a,'rep':r} for a,r in schedule],'workers':rows,'elapsed_seconds':time.perf_counter()-start,'environment':{'python':sys.version,'platform':platform.platform()}},indent=2,sort_keys=True,default=str)+'\n')
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'workers':len(rows),'errors':sum(w.get('kind')!='worker' for w in rows),'stable':current==post}))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3])),sort_keys=True,default=str))
 else:main()
