#!/usr/bin/env python3
"""Task-blind IEEE edge probe transfer across Abs and Div Term families."""
import hashlib,json,math,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_DIRECTED_EDGE_OPERATOR_TRANSFER_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_directed_edge_operator_transfer_v1.py'
ABS_RUN=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_2.py';ABS_LOCK=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_2_lock_20261004.json';ABS_RAW=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_2_20261004.json';ABS_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_term_directed_float_edge_probes_v1_2.py';ABS_ANALYSIS=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_2_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v1_20261004.json'
KEYS=('ax','ay','ex','ey');CAP=8;SEED=581903;WIDE_N=4096
PAIRS=((0.0,0.0),(1e-200,2e-200),(-1e-200,2e-200),(1e200,2e200),(-1e200,2e200),(1.,math.nextafter(1.,2.)),(-1.,math.nextafter(-1.,-2.)),(0.,5e-324),(5e-324,1e-323))

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,ABS_RUN,ABS_LOCK,ABS_RAW,ABS_ANALYZER,ABS_ANALYSIS,ROOT/'domains/contract_query.py',ROOT/'runners/dsl/src/term.rs']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def V(x):return {'type':'Var','name':x}
def Lit(x):return {'type':'Lit','value':x}
def Eq(a,b):return {'type':'Eq','a':a,'b':b}
def terms_for_div():return [
 {'id':'identity_eq','term':Eq(V('ax'),V('ex'))},
 {'id':'quotient_eq','term':Eq({'type':'Div','a':V('ax'),'b':V('ex')},Lit(1.0))}]
def truth(task,row):
 a,_,b,_=row
 return abs(a)==abs(b) if task=='absolute' else a==b
def wide_rows(task,seed=SEED,n=WIDE_N):
 rng=random.Random(seed+(0 if task=='absolute' else 1200));rows=[]
 # Holdout edge values differ from proposal slate.
 edges=[(1e-250,2e-250),(1e150,math.nextafter(1e150,math.inf)),(-1e-300,2e-300),(2e-160,3e-160),(1e307,1.1e307)] if task=='absolute' else [(0.,5e-324),(5e-324,0.),(1e-300,1e-300),(1e300,1e300),(1e300,math.nextafter(1e300,math.inf))]
 for a,b in edges:
  for x,y in ((a,b),(b,a),(-a,b)):
   if math.isfinite(x) and math.isfinite(y):rows.append([x,0.,y,0.])
 while len(rows)<n:
  a=math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  if task=='absolute':
   mode=rng.randrange(3)
   if mode==0:b=math.copysign(abs(a),rng.choice((-1,1)))
   elif mode==1:b=math.nextafter(a,math.inf)
   else:b=math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  else:
   mode=rng.randrange(3)
   if mode==0:b=a
   elif mode==1:b=math.nextafter(a,math.inf)
   else:b=math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  if math.isfinite(a) and math.isfinite(b):rows.append([a,0.,b,0.])
 return rows[:n]
def abs_panel():
 from term_directed_float_edge_probes_v1_2 import input_data
 panels,search,_=input_data();idx=next(i for i,p in enumerate(panels) if p['task']=='absolute' and p['worker']==4);p=panels[idx];w=search[idx]['no_residual_control'];survivors=[h for h in w['candidate_terms'] if h['id'] in w['final_survivor_ids']]
 return {'name':'absolute_square_underflow','task':'absolute','terms':survivors,'training':[x for x in p['training']],'prior_pool':[list(x) for x in p['selection_order']],'holdout':wide_rows('absolute'),'source_panel':{'task':p['task'],'worker':p['worker'],'candidate_ids':[x['id'] for x in survivors]}}
def div_panel():
 train=[]
 for a in (1.,2.,-1.,-3.):train.append({'row':[a,0.,a,0.],'label':1})
 for a,b in ((1.,2.),(-2.,1.),(3.,-1.),(-1.,-4.)):train.append({'row':[a,0.,b,0.],'label':0})
 prior=[[a,0.,b,0.] for a,b in ((1.,1.),(2.,2.),(-1.,-1.),(1.,2.),(-2.,1.),(3.,-1.),(-1.,-4.),(4.,4.))]
 return {'name':'division_zero_denominator','task':'identity','terms':terms_for_div(),'training':train,'prior_pool':prior,'holdout':wide_rows('identity'),'source_panel':{'task':'identity','worker':-1,'candidate_ids':['identity_eq','quotient_eq']}}
def panels():return [abs_panel(),div_panel()]
def vars_of(term):
 out=set()
 def walk(x):
  if isinstance(x,dict):
   if x.get('type')=='Var':out.add(x['name'])
   for z in x.values():walk(z)
  elif isinstance(x,list):
   for z in x:walk(z)
 walk(term);return sorted(out)
def probes_for(terms,forbidden,holdout):
 vars_=sorted(set().union(*(set(vars_of(h['term'])) for h in terms)));denied={tuple(map(float,x)) for x in forbidden}|{tuple(map(float,x)) for x in holdout};rows=[]
 for i,a in enumerate(vars_):
  for b in vars_[i+1:]:
   for x,y in PAIRS:
    for l,r in ((x,y),(y,x)):
     env={k:0. for k in KEYS};env[a]=l;env[b]=r;key=tuple(env[k] for k in KEYS)
     if key not in denied and key not in rows:rows.append(key)
 return [dict(zip(KEYS,r)) for r in rows]
def worker(panel):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();terms=panel['terms'];probes=probes_for(terms,[x['row'] for x in panel['training']]+panel['prior_pool'],panel['holdout']);n_eval=0
 def ev(term,e):
  nonlocal n_eval
  n_eval+=1;return classify(n.evaluate(term,e))
 survivors=terms.copy();before=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in panel['prior_pool']]);events=[];used=set();start=time.perf_counter_ns();cpu=time.process_time_ns()
 while len(survivors)>1 and len(events)<CAP:
  avail=[e for e in probes if tuple(float(e[k]) for k in KEYS) not in used]
  choice=select_discriminating_input(ev,survivors,avail,[])
  if not choice.get('ok'):break
  q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(truth(panel['task'],row));b=[h['id'] for h in survivors]
  survivors=[h for h in survivors if ev(h['term'],q) is label];used.add(tuple(row));events.append({'row':row,'label':label,'before':b,'after':[h['id'] for h in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
 after=partition_hypotheses_by_behavior(ev,survivors,probes);policy_evals=n_eval;wall=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu
 wide=[]
 for h in terms:
  mismatch=invalid=0
  for row in panel['holdout']:
   pred=classify(n.evaluate(h['term'],dict(zip(KEYS,row))));y=bool(truth(panel['task'],row))
   if pred is None:invalid+=1
   elif pred is not y:mismatch+=1
  wide.append({'id':h['id'],'holdout_n':len(panel['holdout']),'mismatches':mismatch,'invalid':invalid})
 return {'name':panel['name'],'task':panel['task'],'candidate_ids':[h['id'] for h in terms],'probe_slate':probes,'prior_partition':before,'events':events,'survivor_ids':[h['id'] for h in survivors],'final_partition':after,'decision':'accept_behavior_class' if survivors and after['all_agree_on_probes'] else 'request_help','policy_native_evaluations':policy_evals,'policy_wall_ns':wall,'policy_cpu_ns':cpu_ns,'wide_scores':wide}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(ABS_ANALYSIS.read_text()).get('passed'):raise SystemExit('upstream absolute probe analysis failed')
  ps=panels();LOCK.write_text(json.dumps({'schema':'TermDirectedEdgeOperatorTransferV1Lock','sources':source_map(),'absolute_lock_sha256':sha(ABS_LOCK),'absolute_capture_sha256':sha(ABS_RAW),'panels':ps,'edge_pairs':PAIRS,'label_cap':CAP,'wide_seed':SEED,'wide_n':WIDE_N},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());ps=panels()
  if source_map()!=l['sources'] or ps!=l['panels'] or sha(ABS_RAW)!=l['absolute_capture_sha256']:raise SystemExit('source/panel drift')
  results=[worker(p) for p in ps]
  if source_map()!=l['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'TermDirectedEdgeOperatorTransferV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':results,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
