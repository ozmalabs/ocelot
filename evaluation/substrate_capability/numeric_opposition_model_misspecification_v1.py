#!/usr/bin/env python3
"""Source-locked active-query probe with an out-of-grammar target relation."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PRE=ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_MODEL_MISSPECIFICATION_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_numeric_opposition_model_misspecification_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_model_misspecification_v1_20261003.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py',
 'runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
OPS=('Neg','Eq','And');MAX_SIZE=9;TIMEOUT=12.;MAX_SOLUTIONS=128;CALL_BUDGET=6;WORKERS=5
TRAIN_VALUES=(-3.,-2.,-1.,1.,2.,3.);HELDOUT_VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5)
KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(row):return dict(zip(KEYS,map(float,row)))
def truth(row):return float(row[0]+row[1]==row[2]+row[3])
def panels():
 rows=list(itertools.product(TRAIN_VALUES,repeat=4));out=[]
 for worker in range(WORKERS):
  rng=random.Random(20261041+worker);pos=[r for r in rows if truth(r)];neg=[r for r in rows if not truth(r)]
  train=rng.sample(pos,2)+rng.sample(neg,2)
  query=[r for r in rows if r not in train];rng.shuffle(query);query=query[:32]
  order=list(query);random.Random(20262041+worker).shuffle(order)
  out.append({'worker':worker,'seed':20261041+worker,'training':[{'row':list(r),'label':int(truth(r))} for r in train],
   'query_pool':[list(r) for r in query],'paired_random_order':[list(r) for r in order]})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},
  'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def observe_equal(a,b):return type(a) is type(b) and a==b
def score(native,term):
 tp=fp=fn=tn=invalid=0
 for row in itertools.product(HELDOUT_VALUES,repeat=4):
  pred=native.evaluate(term,env(row));actual=bool(truth(row))
  if type(pred) is not bool:invalid+=1;continue
  if pred and actual:tp+=1
  elif pred:fp+=1
  elif actual:fn+=1
  else:tn+=1
 return {'n':1296,'exact':fp==0 and fn==0 and invalid==0,'typed':invalid==0,
  'invalid_type_count':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def worker(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 from domains.contract_query import select_discriminating_input
 native=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']]
 queries=[env(x) for x in panel['query_pool']]
 t=time.perf_counter_ns();c0=time.process_time_ns()
 version=synthesize(native,examples,ops=OPS,consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,
  include_output_constants=False,probe_envs=queries,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
 synth_ns=time.perf_counter_ns()-t;cpu_ns=time.process_time_ns()-c0
 hypotheses=[] if not version else [{'id':f'h{i:03d}','term':h['term'].to_dict()} for i,h in enumerate(version.get('hypotheses',[]))]
 arms=[]
 for policy in ('max_entropy','paired_sequential'):
  survivors=list(hypotheses);used=[];observations=[];steps=[];selector_ns=0
  order=panel['paired_random_order']
  stop='empty_version_space' if not survivors else 'query_budget'
  for _ in range(CALL_BUDGET):
   if len(survivors)==0:stop='empty_version_space';break
   if len(survivors)==1:stop='singleton';break
   available=[r for r in order if r not in used]
   if policy=='max_entropy':
    t=time.perf_counter_ns();pick=select_discriminating_input(lambda term,e:native.evaluate(term,e),survivors,available,observations);selector_ns+=time.perf_counter_ns()-t
    if not pick.get('ok'):stop=pick.get('reason','selector_abstained');break
    query=pick['query'];predictions=pick['predictions']
    row=[float(query[k]) for k in KEYS]
   else:
    row=next((r for r in available if len({str(native.evaluate(h['term'],env(r))) for h in survivors})>1),None)
    if row is None:stop='no_discriminating_query';break
    query=env(row);predictions=[{'hypothesis':h['id'],'output':native.evaluate(h['term'],query)} for h in survivors]
   label=bool(truth(row));before=len(survivors);used.append(row)
   observations.append({'inputs':query,'expected':label})
   survivors=[h for h in survivors if observe_equal(native.evaluate(h['term'],query),label)]
   steps.append({'query':row,'label':label,'before':before,'after':len(survivors),'predictions':predictions})
   if not survivors:stop='empty_version_space';break
  if len(survivors)==1:stop='singleton'
  arms.append({'policy':policy,'query_order':order,'steps':steps,'oracle_calls':len(steps),'selector_ns':selector_ns,'stop':stop,
   'survivors':[{'id':h['id'],'term':h['term'],'heldout':score(native,h['term'])} for h in survivors]})
 return {'worker':panel['worker'],'training':panel['training'],'query_pool':panel['query_pool'],
  'paired_random_order':panel['paired_random_order'],'hypotheses':[{'id':h['id'],'term':h['term'],'heldout':score(native,h['term'])} for h in hypotheses],
  'version_halt_reason':None if not version else version.get('halt_reason'),'version_explored':0 if not version else version.get('explored',0),
  'version_ns':synth_ns,'version_cpu_ns':cpu_ns,'arms':arms}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  from domains.engine_provenance import build_is_stale
  if build_is_stale(str(ROOT)):raise SystemExit('native engine stale')
  LOCK.write_text(json.dumps({'schema':'NumericOppositionModelMisspecificationV1Lock','sources':source_map(),
   'panels':panels(),'ops':OPS,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,
   'call_budget':CALL_BUDGET,'heldout_values':HELDOUT_VALUES,'heldout_count':1296},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources']:raise SystemExit('source drift from lock')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};results=[]
  for i,panel in enumerate(lock['panels']):
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=90)
   if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
   results.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'NumericOppositionModelMisspecificationV1Results','lock_sha256':sha(LOCK),
   'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':results},indent=2,sort_keys=True)+'\n')
  print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':
  print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
