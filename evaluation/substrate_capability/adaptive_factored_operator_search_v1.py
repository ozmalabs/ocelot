#!/usr/bin/env python3
"""Residual-conditioned staged grammar search with audited singleton acceptance."""
import hashlib,itertools,json,math,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/ADAPTIVE_FACTORED_OPERATOR_SEARCH_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_adaptive_factored_operator_search_v1.py'
FACTRUN=ROOT/'evaluation/substrate_capability/factored_operator_search_v1.py';FACTAN=ROOT/'evaluation/substrate_capability/analyze_factored_operator_search_v1.py';FACTLOCK=ROOT/'evaluation/substrate_capability/factored_operator_search_v1_lock_20261004.json';FACTRAW=ROOT/'evaluation/reports/factored_operator_search_v1_20261004.json';FACTOUT=ROOT/'evaluation/reports/factored_operator_search_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/adaptive_factored_operator_search_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/adaptive_factored_operator_search_v1_20261004.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
OPS=('Plus','Times','Abs','Min');BASE=('Neg','Eq','And');SIZE=7;TIMEOUT=3.;MAX_SOLUTIONS=128;ACTIVE_BUDGET=6;AUDIT_BUDGET=4;HELD=(-2.5,-1.5,-.5,.5,1.5,2.5);KEYS=('ax','ay','ex','ey');TASKS=('additive','product','absolute','minimum')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(task,r):
 if task=='additive':return r[0]+r[1]==r[2]+r[3]
 if task=='product':return r[0]*r[1]==r[2]*r[3]
 if task=='absolute':return abs(r[0])==abs(r[2])
 return min(r[0],r[1])==min(r[2],r[3])
def classify(x):
 if type(x)is bool:return x
 if type(x)in(int,float) and math.isfinite(x) and x in (0,1):return bool(x)
 return None
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[ROOT/x for x in SOURCES]+[RUN,PRE,AN,FACTRUN,FACTAN,FACTLOCK,FACTRAW,FACTOUT];b=Path(_native.__file__).resolve()
 return {'files':{str(x.relative_to(ROOT)):sha(x) for x in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panels():return json.loads(FACTLOCK.read_text())['panels']
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
 n=_native.Substrate();task=panel['task'];active_pool=panel['selection_order'][:24];audit_pool=panel['selection_order'][24:];seed=int(panel['seed']);shift=seed%len(OPS);order=list(OPS[shift:]+OPS[:shift])
 train=list(panel['training']);used_active=[];used_audit=[];active_calls=0;audit_calls=0;events=[];branches=[];all_terms={};survivors={};audit_candidate=None;audit_streak=0;accepted=None
 for op in order:
  examples=[(env(x['row']),float(x['label'])) for x in train];probes=[env(r) for r in active_pool]
  start=time.perf_counter_ns();cpu=time.process_time_ns();v=synthesize(n,examples,ops=BASE+(op,),consts=(),max_size=SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999);wall=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu
  branch={'operator':op,'training_before':train.copy(),'wall_ns':wall,'cpu_ns':cpu_ns,'explored':0 if not v else v.get('explored',0),'halt_reason':'no_result' if not v else v.get('halt_reason'),'term_ids':[],'new_term_ids':[],'events':[]}
  for h in ([] if not v else v.get('hypotheses',[])):
   term=h['term'].to_dict();key=json.dumps(term,sort_keys=True,separators=(',',':'));hid='term_'+hashlib.sha256(key.encode()).hexdigest()[:16]
   if hid not in all_terms:all_terms[hid]={'id':hid,'term':term,'families':[]};branch['new_term_ids'].append(hid)
   if op not in all_terms[hid]['families']:all_terms[hid]['families'].append(op)
   branch['term_ids'].append(hid);survivors.setdefault(hid,all_terms[hid])
  current=[x for x in survivors.values()]
  # Two active labels per stage at most. A newly generated branch is trained on
  # all prior residual labels, while earlier branches are only filtered.
  for _ in range(2):
   if len(current)<2 or active_calls>=ACTIVE_BUDGET:break
   avail=[r for r in active_pool if r not in used_active and r not in [x['row'] for x in train]]
   if not avail:break
   ans=select_discriminating_input(lambda term,e:classify(n.evaluate(term,e)),current,[env(r) for r in avail],[{'inputs':env(x['row']),'expected':bool(x['label'])} for x in train])
   if not ans.get('ok'):break
   q=[float(ans['query'][k]) for k in KEYS];label=bool(truth(task,q));before=[h['id'] for h in current]
   survivors={hid:h for hid,h in survivors.items() if classify(n.evaluate(h['term'],env(q))) is label};current=list(survivors.values())
   event={'kind':'active','query':q,'label':label,'before':before,'after':[h['id'] for h in current],'entropy_bits':ans['entropy_bits'],'predictions':ans['predictions']};branch['events'].append(event);events.append({'branch':op,**event});used_active.append(q);train.append({'row':q,'label':int(label)});active_calls+=1;audit_candidate=None;audit_streak=0
  current=list(survivors.values())
  if len(current)==1 and audit_calls<AUDIT_BUDGET:
   hid=current[0]['id']
   if audit_candidate!=hid:audit_candidate=hid;audit_streak=0
   for _ in range(min(2-audit_streak,AUDIT_BUDGET-audit_calls)):
    avail=[r for r in audit_pool if r not in used_audit and r not in [x['row'] for x in train]]
    if not avail:break
    q=avail[0];query=env(q);pred=classify(n.evaluate(current[0]['term'],query));label=bool(truth(task,q));before=[hid]
    if pred is label:audit_streak+=1
    else:
     survivors={};current=[];audit_candidate=None;audit_streak=0
    event={'kind':'audit','query':list(map(float,q)),'label':label,'prediction':pred,'candidate_id':hid,'before':before,'after':[h['id'] for h in current],'audit_streak':audit_streak}
    branch['events'].append(event);events.append({'branch':op,**event});used_audit.append(q);train.append({'row':list(q),'label':int(label)});audit_calls+=1
    if pred is not label:break
   if audit_candidate==hid and audit_streak>=2:
    accepted=hid;branch['decision']='accept';branches.append(branch);break
  branch['decision']='continue';branches.append(branch)
  if active_calls>=ACTIVE_BUDGET:break
 if accepted is None:decision='request_help'
 else:decision='accept'
 return {'task':task,'worker':panel['worker'],'seed':seed,'training':panel['training'],'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],'branch_order':order,'branches':branches,'events':events,'decision':decision,'accepted_id':accepted,'active_calls':active_calls,'audit_calls':audit_calls,'total_labels':active_calls+audit_calls,'final_survivor_ids':list(survivors),'final_terms':list(all_terms.values()),'heldout_scores':[{'id':h['id'],'score':score(n,task,h['term'])} for h in all_terms.values()]}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'AdaptiveFactoredOperatorSearchV1Lock','sources':source_map(),'fixed_lock_sha256':sha(FACTLOCK),'panels':panels(),'operators':OPS,'base_ops':BASE,'branch_timeout_s':TIMEOUT,'max_size':SIZE,'max_solutions':MAX_SOLUTIONS,'active_label_budget':ACTIVE_BUDGET,'audit_label_budget':AUDIT_BUDGET,'heldout_values':HELD},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources'] or panels()!=l['panels']:raise SystemExit('source/panel drift')
  e={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
  for i,p in enumerate(l['panels']):
   q=subprocess.run([sys.executable,str(RUN),'--worker',str(i)],cwd=ROOT,env=e,text=True,capture_output=True,timeout=75)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2000:]}')
   rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift')
  OUT.write_text(json.dumps({'schema':'AdaptiveFactoredOperatorSearchV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':print(json.dumps(worker(panels()[int(a[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
