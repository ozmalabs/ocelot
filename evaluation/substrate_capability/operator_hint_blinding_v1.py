#!/usr/bin/env python3
"""Blinded selection between two predeclared operator expansions."""
import hashlib,itertools,json,os,platform,subprocess,sys,time,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/OPERATOR_HINT_BLINDING_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_operator_hint_blinding_v1.py'
UP=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/operator_hint_blinding_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/operator_hint_blinding_v1_20261004.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product');OPS=('Plus','Times');BASE=('Neg','Eq','And');SIZE=7;TIMEOUT=12.;MAX_SOLUTIONS=128;BUDGET=6;HELD=(-2.5,-1.5,-.5,.5,1.5,2.5);KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(task,r):return (r[0]+r[1]==r[2]+r[3]) if task=='additive' else (r[0]*r[1]==r[2]*r[3])
def classify(value):
 if type(value) is bool:return value
 if type(value) in (int,float) and math.isfinite(value) and value in (0,1):return bool(value)
 return None
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[ROOT/x for x in SOURCES]+[RUN,PRE,AN,UP];b=Path(_native.__file__).resolve()
 return {'files':{str(x.relative_to(ROOT)):sha(x) for x in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels():return [p for p in json.loads(UP.read_text())['panels'] if p['task'] in TASKS]
def fit_score(n,task,t):
 fp=fn=0
 for row in itertools.product(HELD,repeat=4):
  pred=classify(n.evaluate(t,env(row)));y=truth(task,row)
  if pred is None:return {'exact':False,'invalid':True,'fp':fp,'fn':fn}
  fp+=int(pred and not y);fn+=int(y and not pred)
 return {'exact':fp==fn==0,'invalid':False,'fp':fp,'fn':fn}
def synthesize_pair(panel,n):
 from domains.generator import synthesize
 examples=[(env(x['row']),float(x['label'])) for x in panel['training']];probes=[env(r) for r in panel['selection_pool']];result={}
 for op in OPS:
  t=time.perf_counter_ns();c=time.process_time_ns()
  v=synthesize(n,examples,ops=BASE+(op,),consts=(),max_size=SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
  result[op]={'wall_ns':time.perf_counter_ns()-t,'cpu_ns':time.process_time_ns()-c,'explored':0 if not v else v.get('explored',0),'halt_reason':'no_result' if not v else v.get('halt_reason'),'terms':[] if not v else [h['term'].to_dict() for h in v.get('hypotheses',[])]}
 return result
def policy(n,panel,terms,op_filter):
 from domains.contract_query import select_discriminating_input
 candidates=[h for h in terms if op_filter=='both' or op_filter in h['families']];pool=panel['selection_order'];train=list(panel['training']);used=[];steps=[];select_ns=0;evals=0;attempts=0;last_reason=None;start=time.perf_counter_ns()
 for _ in range(BUDGET):
  if len(candidates)<2:break
  avail=[r for r in pool if r not in used and r not in [x['row'] for x in train]]
  if not avail:break
  ex=[env(r) for r in avail];evals+=len(candidates)*len(ex);attempts+=1;t=time.perf_counter_ns()
  ans=select_discriminating_input(lambda term,e:classify(n.evaluate(term,e)),candidates,ex,[{'inputs':env(x['row']),'expected':bool(x['label'])} for x in train]);select_ns+=time.perf_counter_ns()-t
  if not ans.get('ok'):last_reason=ans.get('reason');break
  q=[float(ans['query'][k]) for k in KEYS];label=bool(truth(panel['task'],q));before=len(candidates)
  candidates=[h for h in candidates if classify(n.evaluate(h['term'],env(q))) is label]
  used.append(q);train.append({'row':q,'label':int(label)});steps.append({'query':q,'label':label,'before':before,'after':len(candidates),'entropy_bits':ans['entropy_bits'],'predictions':ans['predictions']})
 stop='empty' if not candidates else ('singleton' if len(candidates)==1 else ('budget_exhausted' if len(steps)==BUDGET else 'selector_abstain_or_pool_exhausted'))
 return {'filter':op_filter,'steps':steps,'stop':stop,'selector_abstain_reason':last_reason,'selector_attempts':attempts,'oracle_calls':len(steps),'selector_ns':select_ns,'selector_candidate_input_evaluations':evals,'wall_ns':time.perf_counter_ns()-start,'survivors':[h['id'] for h in candidates],'survivor_terms':[h['term'] for h in candidates]}
def worker(panel):
 from substrate_rs import _native
 n=_native.Substrate();s=synthesize_pair(panel,n);by={op:[] for op in OPS};terms=[];seen={}
 for op in OPS:
  for t in s[op]['terms']:
   key=json.dumps(t,sort_keys=True,separators=(',',':'))
   if key in seen:seen[key]['families'].append(op);by[op].append(seen[key]['id']);continue
   h={'id':'term_'+hashlib.sha256(key.encode()).hexdigest()[:16],'term':t,'families':[op]};seen[key]=h;terms.append(h);by[op].append(h['id'])
 arms=[policy(n,panel,terms,x) for x in ('both','Plus','Times')]
 scored=[{'id':h['id'],'families':h['families'],'holdout':fit_score(n,panel['task'],h['term'])} for h in terms]
 return {'task':panel['task'],'worker':panel['worker'],'training':panel['training'],'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],'synthesis':s,'candidates':terms,'candidate_ids_by_grammar':by,'heldout_scores':scored,'arms':arms}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'OperatorHintBlindingV1Lock','sources':source_map(),'upstream_lock_sha256':sha(UP),'panels':panels(),'tasks':TASKS,'operator_expansions':OPS,'base_ops':BASE,'max_size':SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'query_budget':BUDGET,'heldout_values':HELD},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources'] or panels()!=l['panels']:raise SystemExit('source/panel drift')
  e={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
  for i in range(len(l['panels'])):
   p=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env=e,text=True,capture_output=True,timeout=120)
   if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift')
  OUT.write_text(json.dumps({'schema':'OperatorHintBlindingV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':print(json.dumps(worker(panels()[int(a[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
