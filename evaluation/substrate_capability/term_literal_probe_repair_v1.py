#!/usr/bin/env python3
"""Compare edge-only with literal-boundary probes on a structured alias control."""
import hashlib,json,math,os,platform,random,subprocess,sys,time,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_LITERAL_PROBE_REPAIR_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_literal_probe_repair_v1.py'
UP_RUN=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v2.py';UP_LOCK=ROOT/'evaluation/substrate_capability/term_directed_edge_operator_transfer_v2_lock_20261004.json';UP_RAW=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v2_20261004.json';UP_AN=ROOT/'evaluation/substrate_capability/analyze_term_directed_edge_operator_transfer_v2.py';UP_OUT=ROOT/'evaluation/reports/term_directed_edge_operator_transfer_v2_analysis_20261004.json'
ABS_RUN=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_2.py';ABS_LOCK=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_2_lock_20261004.json';ABS_RAW=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_2_20261004.json';ABS_ANALYSIS=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_2_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_literal_probe_repair_v1_20261004.json'
KEYS=('ax','ay','ex','ey');CAP=8

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,UP_RUN,UP_LOCK,UP_RAW,UP_AN,UP_OUT,ABS_RUN,ABS_LOCK,ABS_RAW,ABS_ANALYSIS,ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve();return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def V(x):return {'type':'Var','name':x}
def L(x):return {'type':'Lit','value':x}
def EQ(a,b):return {'type':'Eq','a':a,'b':b}
def CMP(t,a,b):return {'type':t,'a':a,'b':b}
def interval_alias():
 guard={'type':'And','items':[CMP('Gte',V('ax'),L(.125)),CMP('Lt',V('ax'),L(.126)),CMP('Gte',V('ex'),L(.25)),CMP('Lt',V('ex'),L(.251))]}
 return {'id':'literal_interval_alias','term':{'type':'Or','items':[EQ(V('ax'),V('ex')),guard]}}
def holdout_from_v2(panel):
 rows=[list(r) for r in panel['holdout']]
 # Remove the point-guard exceptional assignments; test distinct interior rows.
 rows=[r for r in rows if not (float(r[0])==.125 and float(r[2])==.25) and not (float(r[0])==.25 and float(r[2])==.125)]
 rows.extend([[.1255,0.,.2505,0.],[.2505,0.,.1255,0.]])
 return rows[:4096]
def panels():
 import term_directed_edge_operator_transfer_v2 as up
 base=up.panels();out=[]
 for p in base:
  q=dict(p);q['terms']=list(p['terms']);q['holdout']=[list(x) for x in p['holdout']]
  if p['name']=='structured_literal_alias':
   q['name']='structured_literal_interval';q['terms']=[p['terms'][0],interval_alias()];q['holdout']=holdout_from_v2(p)
  out.append(q)
 return out
def edge_pairs():return ((0.,0.),(-0.,-0.),(1e-200,2e-200),(-1e-200,2e-200),(1e200,2e200),(-1e200,2e200),(1.,math.nextafter(1.,2.)),(-1.,math.nextafter(-1.,-2.)),(0.,5e-324),(5e-324,1e-323))
def term_vars(t):
 s=set()
 def w(x):
  if isinstance(x,dict):
   if x.get('type')=='Var':s.add(x['name'])
   for z in x.values():w(z)
  elif isinstance(x,list):
   for z in x:w(z)
 w(t);return sorted(s)
def literal_bounds(t):
 found=[]
 def w(x):
  if isinstance(x,dict):
   ty=x.get('type')
   if ty in ('Eq','Lt','Lte','Gt','Gte'):
    a=x.get('a',{});b=x.get('b',{})
    if a.get('type')=='Var' and b.get('type')=='Lit' and isinstance(b.get('value'),(int,float)):found.append((a['name'],float(b['value'])))
    if b.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):found.append((b['name'],float(a['value'])))
   for z in x.values():w(z)
  elif isinstance(x,list):
   for z in x:w(z)
 w(t);return sorted(set(found))
def probe_slates(panel):
 names=sorted(set().union(*(set(term_vars(h['term'])) for h in panel['terms'])));forbid=[x['row'] for x in panel['training']]+panel['prior_pool'];denied={fpkey(r) for r in forbid+panel['holdout']};edge=[]
 for i,a in enumerate(names):
  for b in names[i+1:]:
   for x,y in edge_pairs():
    for l,r in ((x,y),(y,x)):
     e={k:0. for k in KEYS};e[a]=l;e[b]=r;row=[e[k] for k in KEYS];key=fpkey(row)
     if key not in denied and key not in {fpkey(z) for z in edge}:edge.append(row)
 lit=[]
 bound={}
 for h in panel['terms']:
  for var,val in literal_bounds(h['term']):bound.setdefault(var,set()).add(val)
 for i,a in enumerate(names):
  for b in names[i+1:]:
   for x in sorted(bound.get(a,())):
    for y in sorted(bound.get(b,())):
     for l,r in ((x,y),(y,x)):
      e={k:0. for k in KEYS};e[a]=l;e[b]=r;row=[e[k] for k in KEYS];key=fpkey(row)
      if key not in denied and key not in {fpkey(z) for z in lit}:lit.append(row)
 return edge,lit

def truth(task,row):
 a,_,b,_=row;return abs(a)==abs(b) if task=='absolute' else a==b
def policy(n,p,probe_rows):
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from adaptive_factored_operator_search_v1 import classify
 calls=0
 def ev(t,e):
  nonlocal calls
  calls+=1;return classify(n.evaluate(t,e))
 survivors=p['terms'].copy();prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set();start=time.perf_counter_ns();cpu=time.process_time_ns()
 while len(survivors)>1 and len(events)<CAP:
  avail=[dict(zip(KEYS,r)) for r in probe_rows if fpkey(r) not in used];choice=select_discriminating_input(ev,survivors,avail,[])
  if not choice.get('ok'):break
  q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(truth(p['task'],row));before=[h['id'] for h in survivors];survivors=[h for h in survivors if ev(h['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[h['id'] for h in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
 final=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in probe_rows]);decision='accept_behavior_class' if survivors and final['all_agree_on_probes'] else 'request_help'
 return {'prior_partition':prior,'events':events,'survivor_ids':[h['id'] for h in survivors],'final_partition':final,'decision':decision,'native_evaluations':calls,'wall_ns':time.perf_counter_ns()-start,'cpu_ns':time.process_time_ns()-cpu}
def worker(p):
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();edge,lits=probe_slates(p);arms=[]
 for name,rows in (('edge_only',edge),('edge_plus_literal',edge+lits)):
  q=policy(n,p,rows);scores=[]
  for h in p['terms']:
   mis=inv=0
   for r in p['holdout']:
    z=classify(n.evaluate(h['term'],dict(zip(KEYS,r))));y=bool(truth(p['task'],r))
    if z is None:inv+=1
    elif z is not y:mis+=1
   scores.append({'id':h['id'],'n':len(p['holdout']),'mismatches':mis,'invalid':inv})
  wrong=q['decision']=='accept_behavior_class' and any((z['mismatches'] or z['invalid']) for z in scores if z['id'] in q['survivor_ids'])
  arms.append({'policy':name,'edge_probe_rows':edge,'literal_probe_rows':lits,'probe_rows':rows,'prior_partition':q['prior_partition'],'events':q['events'],'survivor_ids':q['survivor_ids'],'final_partition':q['final_partition'],'decision':q['decision'],'false_class_on_holdout':wrong,'native_evaluations':q['native_evaluations'],'wall_ns':q['wall_ns'],'cpu_ns':q['cpu_ns'],'holdout_scores':scores})
 return {'name':p['name'],'task':p['task'],'candidate_ids':[h['id'] for h in p['terms']],'arms':arms}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(UP_OUT.read_text()).get('passed'):raise SystemExit('v2 evidence invalid')
  ps=panels();LOCK.write_text(json.dumps({'schema':'TermLiteralProbeRepairV1Lock','sources':source_map(),'upstream_lock_sha256':sha(UP_LOCK),'upstream_capture_sha256':sha(UP_RAW),'panels':ps,'edge_pairs':edge_pairs(),'label_cap':CAP},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());ps=panels()
  if source_map()!=l['sources'] or ps!=l['panels'] or sha(UP_RAW)!=l['upstream_capture_sha256']:raise SystemExit('source/panel drift')
  results=[worker(p) for p in ps]
  if source_map()!=l['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'TermLiteralProbeRepairV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':results,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
