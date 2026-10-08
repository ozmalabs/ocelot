#!/usr/bin/env python3
"""Term-directed edge probes with signed-zero and structured alias controls."""
import hashlib,json,math,os,platform,random,subprocess,sys,time,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_DIRECTED_EDGE_OPERATOR_TRANSFER_V2_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_directed_edge_operator_transfer_v2.py'
ABS_RUN=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_2.py';ABS_LOCK=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_2_lock_20261004.json';ABS_RAW=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_2_20261004.json';ABS_ANALYSIS=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_2_analysis_20261004.json'
TRANSFER_RUN=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v1.py';TRANSFER_LOCK=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v1_lock_20261004.json';TRANSFER_RAW=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v1_20261004.json';TRANSFER_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_term_directed_edge_operator_transfer_v1.py';TRANSFER_ANALYSIS=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v2_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v2_20261004.json'
KEYS=('ax','ay','ex','ey');CAP=8;SEED=778291;WIDE_N=4096
EDGE_PAIRS=((0.,0.),(-0.,-0.),(1e-200,2e-200),(-1e-200,2e-200),(1e200,2e200),(-1e200,2e200),(1.,math.nextafter(1.,2.)),(-1.,math.nextafter(-1.,-2.)),(0.,5e-324),(5e-324,1e-323))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,ABS_RUN,ABS_LOCK,ABS_RAW,ABS_ANALYSIS,TRANSFER_RUN,TRANSFER_LOCK,TRANSFER_RAW,TRANSFER_ANALYZER,TRANSFER_ANALYSIS,ROOT/'domains/contract_query.py',ROOT/'runners/dsl/src/term.rs']
 b=Path(_native.__file__).resolve();return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def V(n):return {'type':'Var','name':n}
def L(x):return {'type':'Lit','value':x}
def EQ(a,b):return {'type':'Eq','a':a,'b':b}
def build_identity_terms(alias=False):
 exact={'id':'identity_eq','term':EQ(V('ax'),V('ex'))}
 if not alias:other={'id':'quotient_eq','term':EQ({'type':'Div','a':V('ax'),'b':V('ex')},L(1.0))}
 else:
  guard={'type':'And','items':[EQ(V('ax'),L(.125)),EQ(V('ex'),L(.25))]}
  other={'id':'literal_alias','term':{'type':'Or','items':[exact['term'],guard]}}
 return [exact,other]
def training_identity():
 rows=[]
 for x in (1.,2.,-1.,-3.):rows.append({'row':[x,0.,x,0.],'label':1})
 for x,y in ((1.,2.),(-2.,1.),(3.,-1.),(-1.,-4.)):rows.append({'row':[x,0.,y,0.],'label':0})
 return rows
def prior_identity():return [[x,0.,y,0.] for x,y in ((1.,1.),(2.,2.),(-1.,-1.),(1.,2.),(-2.,1.),(3.,-1.),(-1.,-4.),(4.,4.))]
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def holdout(task,seed=SEED,n=WIDE_N,alias=False):
 rng=random.Random(seed+(0 if task=='absolute' else 1700 if not alias else 3200));rows=[]
 if task=='absolute':
  edges=((1e-250,2e-250),(1e150,math.nextafter(1e150,math.inf)),(-1e-300,2e-300),(2e-160,3e-160),(1e307,1.1e307))
 elif alias:
  edges=((.125,.25),(.25,.125),(.125,.5),(.5,.125))
 else:
  edges=((-0.,-0.),(-0.,0.),(0.,-0.),(0.,5e-324),(5e-324,0.),(1e-300,1e-300),(1e300,1e300),(1e300,math.nextafter(1e300,math.inf)))
 for x,y in edges:
  for a,b in ((x,y),(y,x)):
   rows.append([a,0.,b,0.])
 while len(rows)<n:
  x=math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  if task=='absolute':
   mode=rng.randrange(3)
   y=math.copysign(abs(x),rng.choice((-1,1))) if mode==0 else math.nextafter(x,math.inf) if mode==1 else math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  elif alias:
   mode=rng.randrange(4)
   y=x if mode==0 else math.nextafter(x,math.inf) if mode==1 else .25 if mode==2 and x==.125 else math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  else:
   mode=rng.randrange(3);y=x if mode==0 else math.nextafter(x,math.inf) if mode==1 else math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  if math.isfinite(x) and math.isfinite(y):rows.append([x,0.,y,0.])
 return rows[:n]
def truth(task,row):
 a,_,b,_=row;return abs(a)==abs(b) if task=='absolute' else a==b
def abs_panel():
 from term_directed_float_edge_probes_v1_2 import input_data
 p,search,_=input_data();i=next(i for i,x in enumerate(p) if x['task']=='absolute' and x['worker']==4);base=search[i]['no_residual_control'];terms=[h for h in base['candidate_terms'] if h['id'] in base['final_survivor_ids']]
 return {'name':'absolute_square_underflow','task':'absolute','terms':terms,'training':p[i]['training'],'prior_pool':[list(x) for x in p[i]['selection_order']],'holdout':holdout('absolute'),'source':'inherited_locked_panel'}
def identity_panel(alias=False):
 return {'name':'structured_literal_alias' if alias else 'division_signed_zero','task':'identity','terms':build_identity_terms(alias),'training':training_identity(),'prior_pool':prior_identity(),'holdout':holdout('identity',alias=alias),'source':'authored_locked_control'}
def panels():return [abs_panel(),identity_panel(False),identity_panel(True)]
def term_vars(t):
 out=set()
 def w(x):
  if isinstance(x,dict):
   if x.get('type')=='Var':out.add(x['name'])
   for v in x.values():w(v)
  elif isinstance(x,list):
   for v in x:w(v)
 w(t);return sorted(out)
def probes(terms,forbidden,held):
 names=sorted(set().union(*(set(term_vars(h['term'])) for h in terms)));denied={fpkey(x) for x in forbidden+held};rows=[]
 for i,a in enumerate(names):
  for b in names[i+1:]:
   for x,y in EDGE_PAIRS:
    for l,r in ((x,y),(y,x)):
     env={k:0. for k in KEYS};env[a]=l;env[b]=r;row=[env[k] for k in KEYS];key=fpkey(row)
     if key not in denied and key not in {fpkey(z) for z in rows}:rows.append(row)
 return [dict(zip(KEYS,r)) for r in rows]
def worker(p):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();terms=p['terms'];forbidden=[x['row'] for x in p['training']]+p['prior_pool'];proposal=probes(terms,forbidden,p['holdout']);calls=0
 def ev(t,e):
  nonlocal calls
  calls+=1;return classify(n.evaluate(t,e))
 surv=terms.copy();prior=partition_hypotheses_by_behavior(ev,surv,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];seen=set();start=time.perf_counter_ns();cpu=time.process_time_ns()
 while len(surv)>1 and len(events)<CAP:
  avail=[e for e in proposal if fpkey([e[k] for k in KEYS]) not in seen];choice=select_discriminating_input(ev,surv,avail,[])
  if not choice.get('ok'):break
  q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(truth(p['task'],row));before=[h['id'] for h in surv];surv=[h for h in surv if ev(h['term'],q) is label];seen.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[h['id'] for h in surv],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
 final=partition_hypotheses_by_behavior(ev,surv,proposal);decision='accept_behavior_class' if surv and final['all_agree_on_probes'] else 'request_help';policy_eval=calls;wall=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu
 scores=[]
 for h in terms:
  mis=inv=0
  for row in p['holdout']:
   pred=classify(n.evaluate(h['term'],dict(zip(KEYS,row))));label=bool(truth(p['task'],row))
   if pred is None:inv+=1
   elif pred is not label:mis+=1
  scores.append({'id':h['id'],'n':len(p['holdout']),'mismatches':mis,'invalid':inv})
 return {'name':p['name'],'task':p['task'],'candidate_ids':[h['id'] for h in terms],'probe_slate':proposal,'prior_partition':prior,'events':events,'survivor_ids':[h['id'] for h in surv],'final_partition':final,'decision':decision,'policy_native_evaluations':policy_eval,'policy_wall_ns':wall,'policy_cpu_ns':cpu_ns,'holdout_scores':scores}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(ABS_ANALYSIS.read_text()).get('passed') or not json.loads(TRANSFER_ANALYSIS.read_text()).get('passed'):raise SystemExit('upstream evidence invalid')
  ps=panels();LOCK.write_text(json.dumps({'schema':'TermDirectedEdgeOperatorTransferV2Lock','sources':source_map(),'abs_capture_sha256':sha(ABS_RAW),'transfer_capture_sha256':sha(TRANSFER_RAW),'panels':ps,'edge_pairs':EDGE_PAIRS,'label_cap':CAP,'wide_seed':SEED,'wide_n':WIDE_N},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());ps=panels()
  if source_map()!=l['sources'] or ps!=l['panels'] or sha(ABS_RAW)!=l['abs_capture_sha256'] or sha(TRANSFER_RAW)!=l['transfer_capture_sha256']:raise SystemExit('source/panel drift')
  results=[worker(p) for p in ps]
  if source_map()!=l['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'TermDirectedEdgeOperatorTransferV2Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':results,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
