#!/usr/bin/env python3
"""Search one shared multi-operator Term grammar over four numeric task families."""
import hashlib,itertools,json,math,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/MULTI_OPERATOR_FAMILY_SEARCH_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_multi_operator_family_search_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/multi_operator_family_search_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/multi_operator_family_search_v1_20261004.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product','absolute','minimum');WORKERS=5;VALUES=(-3.,-2.,-1.,0.,1.,2.,3.);HELD=(-2.5,-1.5,-.5,.5,1.5,2.5);KEYS=('ax','ay','ex','ey')
OPS=('Neg','Eq','And','Not','Plus','Times','Div','Abs','Min','Max','Lt','Gt','Or');SIZE=7;TIMEOUT=12.;MAX_SOLUTIONS=128;BUDGET=6;SEED=82261004
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(row):return dict(zip(KEYS,map(float,row)))
def truth(task,r):
 if task=='additive':return r[0]+r[1]==r[2]+r[3]
 if task=='product':return r[0]*r[1]==r[2]*r[3]
 if task=='absolute':return abs(r[0])==abs(r[2])
 return min(r[0],r[1])==min(r[2],r[3])
def classify(x):
 if type(x) is bool:return x
 if type(x) in (int,float) and math.isfinite(x) and x in (0,1):return bool(x)
 return None
def panels():
 rows=list(itertools.product(VALUES,repeat=4));out=[]
 for ti,t in enumerate(TASKS):
  pos=[r for r in rows if truth(t,r)];neg=[r for r in rows if not truth(t,r)]
  for w in range(WORKERS):
   rng=random.Random(SEED+ti*100+w);train=rng.sample(pos,3)+rng.sample(neg,3);remain=[r for r in rows if r not in train];rng.shuffle(remain);pool=remain[:32];order=pool.copy();random.Random(SEED+10000+ti*100+w).shuffle(order)
   out.append({'task':t,'worker':w,'seed':SEED+ti*100+w,'training':[{'row':list(r),'label':int(truth(t,r))} for r in train],'selection_pool':[list(r) for r in pool],'selection_order':[list(r) for r in order]})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 paths=[ROOT/p for p in SOURCES]+[RUN,PRE,AN];b=Path(_native.__file__).resolve()
 return {'files':{str(x.relative_to(ROOT)):sha(x) for x in paths},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def score(n,task,term):
 fp=fn=invalid=0;tp=tn=0
 for row in itertools.product(HELD,repeat=4):
  try:p=classify(n.evaluate(term,env(row)))
  except Exception:invalid+=1;continue
  if p is None:invalid+=1;continue
  y=truth(task,row)
  if p and y:tp+=1
  elif p:fp+=1
  elif y:fn+=1
  else:tn+=1
 return {'n':1296,'exact':not invalid and not fp and not fn,'invalid':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def worker(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 from domains.contract_query import select_discriminating_input
 n=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']];probes=[env(r) for r in panel['selection_pool']]
 t=time.perf_counter_ns();c=time.process_time_ns();v=synthesize(n,examples,ops=OPS,consts=(),max_size=SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999);wall=time.perf_counter_ns()-t;cpu=time.process_time_ns()-c
 candidates=[] if not v else [{'id':f'h{i:03d}','term':h['term'].to_dict()} for i,h in enumerate(v.get('hypotheses',[]))]
 current=list(candidates);train=list(panel['training']);used=[];steps=[];selection_ns=0;evals=0;attempts=0;abstain=None
 for _ in range(BUDGET):
  if len(current)<2:break
  available=[r for r in panel['selection_order'] if r not in used and r not in [x['row'] for x in train]]
  if not available:break
  evals+=len(current)*len(available);attempts+=1;start=time.perf_counter_ns()
  ans=select_discriminating_input(lambda term,e:classify(n.evaluate(term,e)),current,[env(r) for r in available],[{'inputs':env(x['row']),'expected':bool(x['label'])} for x in train]);selection_ns+=time.perf_counter_ns()-start
  if not ans.get('ok'):abstain=ans.get('reason');break
  query=[float(ans['query'][k]) for k in KEYS];label=bool(truth(panel['task'],query));before=len(current);current=[h for h in current if classify(n.evaluate(h['term'],env(query))) is label]
  used.append(query);train.append({'row':query,'label':int(label)});steps.append({'query':query,'label':label,'before':before,'after':len(current),'entropy_bits':ans['entropy_bits'],'predictions':ans['predictions']})
 stop='no_fit' if not candidates else ('empty_after_query' if not current else ('singleton' if len(current)==1 else ('query_budget_exhausted' if len(steps)==BUDGET else 'selector_abstain_or_pool_exhausted')))
 return {'task':panel['task'],'worker':panel['worker'],'seed':panel['seed'],'training':panel['training'],'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],'candidates':candidates,'halt_reason':'no_result' if not v else v.get('halt_reason'),'explored':0 if not v else v.get('explored',0),'synthesis_wall_ns':wall,'synthesis_cpu_ns':cpu,'steps':steps,'stop':stop,'selector_abstain_reason':abstain,'selector_attempts':attempts,'oracle_calls':len(steps),'selector_candidate_input_evaluations':evals,'selector_ns':selection_ns,'survivors':[h['id'] for h in current],'survivor_terms':[h['term'] for h in current],'heldout_scores':[{'id':h['id'],'score':score(n,panel['task'],h['term'])} for h in candidates]}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'MultiOperatorFamilySearchV1Lock','sources':source_map(),'panels':panels(),'tasks':TASKS,'task_seed':SEED,'operators':OPS,'max_size':SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'query_budget':BUDGET,'heldout_values':HELD},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources'] or panels()!=l['panels']:raise SystemExit('source/panel drift')
  e={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
  for i in range(len(l['panels'])):
   p=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env=e,text=True,capture_output=True,timeout=75)
   if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'MultiOperatorFamilySearchV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':print(json.dumps(worker(panels()[int(a[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
