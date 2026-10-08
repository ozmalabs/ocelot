#!/usr/bin/env python3
"""Counterexample-triggered single-operator grammar expansion."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_CEGIS_GRAMMAR_EXPANSION_V1_2_AMENDMENT_20261003.md';SRCLOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_grammar_expansion_v1_1_lock_20261003.json';SRCCAP=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_1_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_grammar_expansion_v1_2_lock_20261003.json';OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_2_20261003.json';AN=ROOT/'evaluation/substrate_capability/analyze_numeric_opposition_cegis_grammar_expansion_v1_2.py'
SOURCES=('domains/generator.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
GRID=(-2.5,-1.5,-.5,.5,1.5,2.5);OPS=('Neg','Eq','And','Not');SIZE=11;TIMEOUT=12.
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def target(r):return (r[0]==-r[2]) != (r[1]==-r[3])
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,AN,SRCLOCK,SRCCAP]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'semantic_engine':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def reserve(panel):
 used={tuple(x['row']) for x in panel['initial_training']}|{tuple(x) for x in panel['query_pool']}
 domain=list(itertools.product(range(-3,4),repeat=4));pool=[r for r in domain if r not in used];rng=random.Random(883001+panel['worker']);rng.shuffle(pool)
 return [list(x) for x in pool[:24]]
def stage1():return json.loads(SRCCAP.read_text())['workers']
def run(w):
 from substrate_rs import _native
 from domains.generator import synthesize
 native=_native.Substrate();train=list(w['revealed_training']);reserve_rows=w['reserve'];already=len(w['reserve_queries']);term=w['expanded_term'];events=[];status='reserve_exhausted';total_calls=already;total_synth_ns=0;halt=w['expanded_halt']
 if term is None:status='no_fit'
 else:
  for row in reserve_rows[already:already+12]:
   pred=bool(native.evaluate(term,env(row)));label=bool(target(row));events.append({'row':row,'candidate_term':term,'prediction':pred,'label':int(label),'disagrees':pred!=label});train.append({'row':row,'label':int(label)});total_calls+=1
   if pred!=label:
    t=time.perf_counter_ns();res=synthesize(native,[(env(x['row']),float(x['label'])) for x in train],ops=OPS,consts=(),max_size=SIZE,timeout_s=TIMEOUT,include_output_constants=False);dt=time.perf_counter_ns()-t;total_synth_ns+=dt;term=res.get('dict') if res else None;halt=res.get('halt_reason') if res else 'no_result'
    if term is None:status='no_fit';break
   else:status='reserve_consistent'
  else:
   if total_calls>=already+12 and len(reserve_rows)>already+12:status='query_budget_exhausted'
 score=None
 if term is not None:
  tp=fp=fn=tn=0
  for r in itertools.product(GRID,repeat=4):
   y=target(r);p=bool(native.evaluate(term,env(r)))
   if y and p:tp+=1
   elif y:fn+=1
   elif p:fp+=1
   else:tn+=1
  score={'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':not(fp or fn)}
 return {'worker':w['worker'],'trigger_v1':w['trigger'],'starting_term':w['expanded_term'],'starting_training':w['revealed_training'],'starting_reserve_queries':w['reserve_queries'],'reserve':reserve_rows,'repair_events':events,'final_training':train,'final_term':term,'status':status,'oracle_calls_total':total_calls,'additional_synthesis_ns':total_synth_ns,'last_halt':halt,'heldout':score}

def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  workers=stage1();panels=[dict(w) for w in workers]
  LOCK.write_text(json.dumps({'schema':'CegisGrammarExpansionV1_2Lock','sources':source_map(),'workers':panels,'expanded_ops':OPS,'max_size':SIZE,'timeout_s':TIMEOUT,'additional_query_budget':12,'reserve_size':24,'heldout_grid':GRID},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args[:1]==['--worker']:
  w=json.loads(LOCK.read_text())['workers'][int(args[1])];print(json.dumps(run(w),sort_keys=True,separators=(',',':')));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --run | --worker ID')
 l=json.loads(LOCK.read_text())
 if source_map()!=l['sources']:raise SystemExit('source drift')
 ep={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for i in range(len(l['workers'])):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=ep,text=True,capture_output=True,timeout=90)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-1200:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if source_map()!=l['sources']:raise SystemExit('source drift during run')
 OUT.write_text(json.dumps({'schema':'CegisGrammarExpansionV1_2Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_map(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
