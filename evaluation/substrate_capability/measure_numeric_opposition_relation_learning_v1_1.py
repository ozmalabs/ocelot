#!/usr/bin/env python3
"""Source-locked supervised relation induction via domains.generator.synthesize."""
from __future__ import annotations
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_RELATION_LEARNING_V1_1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_numeric_opposition_relation_learning_v1_2.py'
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_relation_learning_v1_1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_relation_learning_v1_1_20261003.json'
SOURCE_PATHS=('domains/generator.py','domains/engine_provenance.py','runners/dsl/src/term.rs',
 'runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs',
 'runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
 'runners/dsl/python/substrate_rs/__init__.py')
OPS=('Neg','Eq','And');CONSTS=();MAX_SIZE=9;TIMEOUT_S=12.0;WORKERS=5;BASE_SEED=61030
HELDOUT_VALUES=(-2.5,-1.5,-0.5,0.5,1.5,2.5)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def make_env(row):return {'ax':float(row[0]),'ay':float(row[1]),'ex':float(row[2]),'ey':float(row[3])}
def panels():
 domain=range(-3,4);nonzero=(-3,-2,-1,1,2,3)
 out=[]
 for worker in range(WORKERS):
  rng=random.Random(BASE_SEED+worker)
  x=rng.choice(nonzero);y=rng.choice(nonzero)
  p=[(x,0,-x,0),(0,y,0,-y)]
  p.extend((x,y,-x,-y) for x,y in rng.sample(list(itertools.product(nonzero,repeat=2)),6))
  a,b=rng.choice(list(itertools.product(nonzero,repeat=2)));e=rng.choice([x for x in domain if x!=-b])
  n=[(a,b,-a,e)]
  a,b=rng.choice(list(itertools.product(nonzero,repeat=2)));e=rng.choice([x for x in domain if x!=-a])
  n.append((a,b,e,-b))
  all_rows=list(itertools.product(domain,repeat=4))
  extra=[r for r in all_rows if (r[0],r[1])!=(-r[2],-r[3]) and r not in n]
  n.extend(rng.sample(extra,6))
  out.append({'worker':worker,'seed':BASE_SEED+worker,'training':[
   {'row':list(r),'label':1} for r in p]+[{'row':list(r),'label':0} for r in n]})
 return out
def frozen():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 files={str(p):sha(ROOT/p) for p in SOURCE_PATHS}
 files.update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PREREG,ANALYZER)})
 return {'files':files,'native_binary':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())},
  'semantic_engine':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def worker(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine is stale')
 native=_native.Substrate();examples=[(make_env(x['row']),float(x['label'])) for x in panel['training']]
 before=frozen();wall0=time.perf_counter_ns();cpu0=time.process_time_ns()
 result=synthesize(native,examples,ops=OPS,consts=CONSTS,max_size=MAX_SIZE,timeout_s=TIMEOUT_S,
  include_output_constants=False,return_trace=False)
 wall=time.perf_counter_ns()-wall0;cpu=time.process_time_ns()-cpu0
 term=result.get('dict') if result else None
 if term:
  predictions=[bool(native.evaluate(term,make_env(row))) for row in itertools.product(HELDOUT_VALUES,repeat=4)]
  positives=sum((r[0]==-r[2] and r[1]==-r[3]) for r in itertools.product(HELDOUT_VALUES,repeat=4))
  tp=sum(p for p,row in zip(predictions,itertools.product(HELDOUT_VALUES,repeat=4)) if row[0]==-row[2] and row[1]==-row[3])
  fp=sum(p for p,row in zip(predictions,itertools.product(HELDOUT_VALUES,repeat=4)) if not(row[0]==-row[2] and row[1]==-row[3]))
  fn=positives-tp
  heldout={'n':len(predictions),'positive_n':positives,'negative_n':len(predictions)-positives,
    'tp':tp,'fp':fp,'fn':fn,'tn':len(predictions)-positives-fp,'exact':not(fp or fn)}
 else:heldout={'n':1296,'positive_n':36,'negative_n':1260,'tp':0,'fp':0,'fn':36,'tn':0,'exact':False}
 after=frozen()
 return {'worker':panel['worker'],'training':panel['training'],'term':term,
  'term_str':result.get('term_str') if result else None,'size':result.get('size') if result else None,
  'fits':result.get('fits') if result else False,'halt_reason':result.get('halt_reason') if result else 'no_result',
  'explored':result.get('explored',0) if result else 0,'distinct':result.get('distinct',0) if result else 0,
  'synth_elapsed_s':result.get('elapsed_s',0.0) if result else 0.0,'wall_ns':wall,'cpu_ns':cpu,
  'heldout':heldout,'sources_before':before,'sources_after':after,'source_stable':before==after}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  lock=json.loads(LOCK.read_text());i=int(args[1]);print(json.dumps(worker(lock['panels'][i]),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  from domains.engine_provenance import build_is_stale
  if build_is_stale(str(ROOT)):raise SystemExit('native engine is stale')
  LOCK.write_text(json.dumps({'schema':'NumericOppositionRelationLearningV1_1Lock','sources':frozen(),
   'panels':panels(),'ops':OPS,'constants':CONSTS,'max_size':MAX_SIZE,'timeout_s':TIMEOUT_S,
   'workers':WORKERS,'heldout_values':HELDOUT_VALUES,'heldout_count':1296,
   'panel_design':'eight positives include x-axis, y-axis, and two-axis examples; negatives include x-only and y-only counterexamples plus six sampled non-opposition pairs',
   'task':'infer whether expected displacement is componentwise negative of actual displacement'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=30)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'NumericOppositionRelationLearningV1_1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'workers':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
