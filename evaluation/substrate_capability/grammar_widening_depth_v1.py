#!/usr/bin/env python3
"""Source-locked expanded-grammar size/recovery study."""
import hashlib,itertools,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/GRAMMAR_WIDENING_DEPTH_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_grammar_widening_depth_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/grammar_widening_depth_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/grammar_widening_depth_v1_20261003.json'
PANEL_LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json'
SOURCES=('domains/generator.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product');KEYS=('ax','ay','ex','ey');VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5);SIZES=(7,9);TIMEOUT=12.;OPS={'additive':('Neg','Eq','And','Plus'),'product':('Neg','Eq','And','Times')};MAX_SOLUTIONS=128
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(task,r):return r[0]+r[1]==r[2]+r[3] if task=='additive' else r[0]*r[1]==r[2]*r[3]
def score(native,task,term):
 fp=fn=invalid=0;tp=tn=0
 for r in itertools.product(VALUES,repeat=4):
  try:v=native.evaluate(term,env(r))
  except Exception:invalid+=1;continue
  y=truth(task,r)
  if type(v) is not bool:invalid+=1
  elif v and y:tp+=1
  elif v:fp+=1
  elif y:fn+=1
  else:tn+=1
 return {'n':1296,'exact':not invalid and not fp and not fn,'invalid':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def panels():
 prev=json.loads(PANEL_LOCK.read_text());return [p for p in prev['panels'] if p['task'] in TASKS]
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER,PANEL_LOCK]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def worker(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 rows=[]
 examples=[(env(x['row']),float(x['label'])) for x in panel['training']];probes=[env(r) for r in panel['selection_pool']]
 for size in SIZES:
  native=_native.Substrate();wall=time.perf_counter_ns();cpu=time.process_time_ns()
  v=synthesize(native,examples,ops=OPS[panel['task']],consts=(),max_size=size,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
  wall=time.perf_counter_ns()-wall;cpu=time.process_time_ns()-cpu
  hs=[] if not v else [{'id':f'h{i:03d}','term':h['term'].to_dict(),'heldout':score(native,panel['task'],h['term'].to_dict())} for i,h in enumerate(v.get('hypotheses',[]))]
  rows.append({'max_size':size,'ops':OPS[panel['task']],'timeout_s':TIMEOUT,'wall_ns':wall,'cpu_ns':cpu,'explored':0 if not v else v.get('explored',0),'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':hs})
 return {'task':panel['task'],'worker':panel['worker'],'training':panel['training'],'selection_pool':panel['selection_pool'],'arms':rows}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'GrammarWideningDepthV1Lock','sources':source_map(),'panels':panels(),'tasks':TASKS,'sizes':SIZES,'timeout_s':TIMEOUT,'ops':OPS,'max_solutions':MAX_SOLUTIONS,'heldout_values':VALUES},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
  for i,p in enumerate(lock['panels']):
   q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=90)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2000:]}')
   workers.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'GrammarWideningDepthV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
