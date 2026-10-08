#!/usr/bin/env python3
"""Prospective cross-family CEGIS/grammar-expansion capability panel."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/STRUCTURAL_INDUCTION_CROSS_FAMILY_V1_PREREG_20261003.md';AN=ROOT/'evaluation/substrate_capability/analyze_structural_induction_cross_family_v1.py';LOCK=ROOT/'evaluation/substrate_capability/structural_induction_cross_family_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/structural_induction_cross_family_v1_20261003.json'
SOURCES=('domains/generator.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('xor_opposition','absolute_equality','additive_equality');OPS_ORDER=('Neg','Not','Abs','Plus');BASE=('Eq',);MAX_SIZE=11;TIMEOUT=2.;QUERY_BUDGET=12;STOP_K=6;VALUES=tuple(range(-2,3));HELDOUT=(-2.5,-1.5,-.5,.5,1.5,2.5);WORKERS=5;SEED=771003
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r,t):
 if t=='xor_opposition':return (r[0]==-r[2]) != (r[1]==-r[3])
 if t=='absolute_equality':return abs(r[0])==abs(r[2])
 return r[0]+r[1]==r[2]
def panels():
 allrows=list(itertools.product(VALUES,repeat=4));out=[]
 for task in TASKS:
  for wid in range(WORKERS):
   rng=random.Random(SEED+TASKS.index(task)*100+wid)
   pos=[r for r in allrows if truth(r,task)];neg=[r for r in allrows if not truth(r,task)]
   training=[list(r) for r in rng.sample(pos,4)+rng.sample(neg,4)]
   remaining=[r for r in allrows if list(r) not in training];rng.shuffle(remaining)
   reserve=[list(r) for r in remaining[:24]]
   out.append({'task':task,'worker':wid,'training':[{'row':r,'label':int(truth(r,task))} for r in training],'reserve':reserve})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,AN]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'semantic_engine':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def run(p):
 from substrate_rs import _native
 from domains.generator import synthesize
 native=_native.Substrate();train=list(p['training']);ops=list(BASE);nextop=0;streak=0;queries=[];events=[];searches=[];term=None;status='budget_exhausted'
 def fit():
  t=time.perf_counter_ns();c=time.process_time_ns();v=synthesize(native,[(env(x['row']),float(x['label'])) for x in train],ops=ops,consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False);dt=time.perf_counter_ns()-t;dc=time.process_time_ns()-c
  z=v.get('dict') if v else None;searches.append({'ops':list(ops),'example_count':len(train),'halt':v.get('halt_reason') if v else 'no_result','explored':v.get('explored',0) if v else 0,'wall_ns':dt,'cpu_ns':dc,'term':z});return z
 term=fit()
 if term is None:
  while nextop<len(OPS_ORDER) and term is None:
   ops.append(OPS_ORDER[nextop]);nextop+=1;term=fit()
 for row in p['reserve']:
  if len(queries)>=QUERY_BUDGET:status='query_budget_exhausted';break
  if term is None:status='no_fit';break
  pred=bool(native.evaluate(term,env(row)));label=int(truth(row,p['task']));dis=pred!=bool(label)
  ev={'row':row,'candidate_term':term,'prediction':pred,'label':label,'disagrees':dis,'streak_before':streak};train.append({'row':row,'label':label});queries.append(row)
  if dis:
   streak=0
   if nextop<len(OPS_ORDER):ops.append(OPS_ORDER[nextop]);nextop+=1
   term=fit()
   while term is None and nextop<len(OPS_ORDER):ops.append(OPS_ORDER[nextop]);nextop+=1;term=fit()
  else:streak+=1
  ev['streak_after']=streak;ev['ops_after']=list(ops);events.append(ev)
  if term is None:status='no_fit';break
  if streak>=STOP_K:status='agreement_threshold';break
 else:status='reserve_exhausted'
 scores=None
 if term is not None:
  grid=list(itertools.product(HELDOUT,repeat=4));tp=fp=fn=tn=0
  for r in grid:
   y=bool(truth(r,p['task']));pr=bool(native.evaluate(term,env(r)))
   if y and pr:tp+=1
   elif y:fn+=1
   elif pr:fp+=1
   else:tn+=1
  scores={'n':len(grid),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':not(fp or fn)}
 return {'task':p['task'],'worker':p['worker'],'initial_training':p['training'],'reserve':p['reserve'],'revealed_training':train,'events':events,'searches':searches,'final_term':term,'final_ops':ops,'status':status,'oracle_calls':len(queries),'heldout':scores}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'StructuralInductionCrossFamilyV1Lock','sources':source_map(),'panels':panels(),'tasks':TASKS,'base_ops':BASE,'expansion_order':OPS_ORDER,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'query_budget':QUERY_BUDGET,'stop_k':STOP_K,'heldout_values':HELDOUT},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a[:1]==['--worker']:
  print(json.dumps(run(json.loads(LOCK.read_text())['panels'][int(a[1])]),sort_keys=True,separators=(',',':')));return 0
 if a!=['--run']:raise SystemExit('usage --lock | --run | --worker ID')
 l=json.loads(LOCK.read_text())
 if source_map()!=l['sources']:raise SystemExit('source drift')
 ep={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for i in range(len(l['panels'])):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=ep,text=True,capture_output=True,timeout=120)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-1500:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if source_map()!=l['sources']:raise SystemExit('source drift during run')
 OUT.write_text(json.dumps({'schema':'StructuralInductionCrossFamilyV1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':source_map(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
