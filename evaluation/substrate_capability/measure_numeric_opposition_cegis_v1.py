#!/usr/bin/env python3
"""Counterexample-guided relation resynthesis over a frozen numeric panel."""
import hashlib,itertools,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve(); PRE=ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_CEGIS_V1_PREREG_20261003.md'
UPLOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_active_query_v1_1_lock_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_v1_lock_20261003.json'; OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_v1_20261003.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_numeric_opposition_cegis_v1.py'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
OPS=('Neg','Eq','And'); BUDGET=6; MAX_SIZE=9; TIMEOUT=12.; MAX_SOLUTIONS=128; GRID=(-2.5,-1.5,-.5,.5,1.5,2.5)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def truth(r):return r[0]==-r[2] and r[1]==-r[3]
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def sources():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 fs=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER,UPLOCK]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in fs},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'semantic_engine':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels():return json.loads(UPLOCK.read_text())['panels']
def run_panel(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 from domains.contract_query import select_discriminating_input
 native=_native.Substrate(); training=panel['training']; used=[]; rounds=[]; status='budget_exhausted'; final=[]
 for turn in range(BUDGET+1):
  examples=[(env(x['row']),float(x['label'])) for x in training]
  t=time.perf_counter_ns(); c=time.process_time_ns()
  version=synthesize(native,examples,ops=OPS,consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False,
    probe_envs=[env(r) for r in panel['query_pool']],max_solutions=MAX_SOLUTIONS,saturate_k=999999)
  wall=time.perf_counter_ns()-t; cpu=time.process_time_ns()-c
  hyps=[] if not version else [{'id':f'h{i:03d}','term':h['term'].to_dict()} for i,h in enumerate(version.get('hypotheses',[]))]
  roundrow={'turn':turn,'training':training.copy(),'hypotheses':hyps,'version_halt':version.get('halt_reason') if version else 'no_result','explored':version.get('explored',0) if version else 0,'synth_wall_ns':wall,'synth_cpu_ns':cpu}
  final=hyps
  if not hyps: status='no_fit';rounds.append(roundrow);break
  if len(hyps)==1: status='singleton';rounds.append(roundrow);break
  if turn>=BUDGET: status='budget_exhausted';rounds.append(roundrow);break
  avail=[r for r in panel['query_pool'] if r not in used and r not in [x['row'] for x in training]]
  if not avail:status='pool_exhausted';rounds.append(roundrow);break
  t=time.perf_counter_ns(); picked=select_discriminating_input(lambda term,e:native.evaluate(term,e),hyps,[env(r) for r in avail],[]); sel=time.perf_counter_ns()-t
  if not picked.get('ok'):status='selector_abstain';rounds.append(roundrow);break
  row=[int(picked['query'][k]) for k in ('ax','ay','ex','ey')]
  if row in used or row in [x['row'] for x in training]:raise RuntimeError('duplicate query')
  label=int(truth(row));roundrow.update({'query':row,'label':label,'selection_ns':sel,'entropy_bits':picked.get('entropy_bits')});rounds.append(roundrow)
  training=training+[{'row':row,'label':label}];used.append(row)
 grid=list(itertools.product(GRID,repeat=4)); scores=[]
 for h in final:
  tp=fp=fn=tn=0
  for r in grid:
   y=truth(r); p=bool(native.evaluate(h['term'],env(r)))
   if y and p:tp+=1
   elif y:fn+=1
   elif p:fp+=1
   else:tn+=1
  scores.append({'hypothesis':h['id'],'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':fp==0 and fn==0})
 return {'worker':panel['worker'],'initial_training':panel['training'],'query_pool':panel['query_pool'],'rounds':rounds,'status':status,'oracle_calls':len(used),'final_hypotheses':final,'heldout_scores':scores}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'NumericOppositionCEGISV1Lock','sources':sources(),'upstream_lock_sha256':sha(UPLOCK),'panels':panels(),'ops':OPS,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'query_budget':BUDGET,'heldout_grid':GRID},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args[:1]==['--worker']:
  i=int(args[1]);print(json.dumps(run_panel(panels()[i]),sort_keys=True,separators=(',',':')));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --run | --worker ID')
 lock=json.loads(LOCK.read_text())
 if sources()!=lock['sources']:raise SystemExit('source drift')
 envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'}; rows=[]
 for i,panel in enumerate(lock['panels']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=360)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if sources()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'NumericOppositionCEGISV1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':sources(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
