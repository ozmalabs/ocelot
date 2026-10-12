#!/usr/bin/env python3
"""Task-blind numerical edge probes from variables in ambiguous Terms."""
import hashlib,json,math,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_DIRECTED_FLOAT_EDGE_PROBES_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_directed_float_edge_probes_v1.py'
SR=ROOT/'evaluation/substrate_capability/residual_triggered_resynthesis_v1_2.py';SL=ROOT/'evaluation/substrate_capability/residual_triggered_resynthesis_v1_2_lock_20261004.json';SRAW=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_20261004.json';SA=ROOT/'evaluation/substrate_capability/analyze_residual_triggered_resynthesis_v1_2.py';SOUT=ROOT/'evaluation/reports/residual_triggered_resynthesis_v1_2_analysis_20261004.json'
SEL=ROOT/'evaluation/substrate_capability/resynthesis_selector_budget_v1_2.py';SELLOCK=ROOT/'evaluation/substrate_capability/resynthesis_selector_budget_v1_2_lock_20261004.json';SELRAW=ROOT/'evaluation/reports/resynthesis_selector_budget_v1_2_20261004.json';SELAN=ROOT/'evaluation/substrate_capability/analyze_resynthesis_selector_budget_v1_2.py';SELOUT=ROOT/'evaluation/reports/resynthesis_selector_budget_v1_2_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_directed_float_edge_probes_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_directed_float_edge_probes_v1_20261004.json'
KEYS=('ax','ay','ex','ey');TASK='absolute';WORKER=4;ARMS=('no_residual_control','residual_arm');LABEL_BUDGET=8
EDGE_PAIRS=((1e-200,2e-200),(-1e-200,2e-200),(1e200,2e200),(-1e200,2e200),(1.0,math.nextafter(1.0,2.0),),(-1.0,math.nextafter(-1.0,-2.0)),(0.0,5e-324),(5e-324,1e-323))
SEED=209417;WIDE_N=4096

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,SR,SL,SRAW,SA,SOUT,SEL,SELLOCK,SELRAW,SELAN,SELOUT,ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def input_data():
 sl=json.loads(SL.read_text());sr=json.loads(SRAW.read_text());sel=json.loads(SELRAW.read_text());return sl['panels'],sr['workers'],sel['workers']
def term_vars(t):
 out=set()
 def walk(x):
  if isinstance(x,dict):
   if x.get('type')=='Var' and isinstance(x.get('name'),str):out.add(x['name'])
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(t);return out
def proposal_slate(terms,forbidden):
 varset=set().union(*(term_vars(h['term']) for h in terms));vars_=sorted(varset)
 if len(vars_)<2:return []
 denied={tuple(map(float,x)) for x in forbidden};held={tuple(x) for x in __import__('itertools').product((-2.5,-1.5,-.5,.5,1.5,2.5),repeat=4)}
 # Task-neutral IEEE challenges: each unordered variable pair receives signed
 # tiny/large values, adjacent floats, and subnormal values in both orders.
 pairs=((1e-200,2e-200),(-1e-200,2e-200),(1e200,2e200),(-1e200,2e200),(1.0,math.nextafter(1.0,2.0)),(-1.0,math.nextafter(-1.0,-2.0)),(0.0,5e-324),(5e-324,1e-323))
 rows=[]
 for i,a in enumerate(vars_):
  for b in vars_[i+1:]:
   for x,y in pairs:
    for left,right in ((x,y),(y,x)):
     env={k:0.0 for k in KEYS};env[a]=left;env[b]=right;row=tuple(env[k] for k in KEYS)
     if row not in denied and row not in held and row not in rows:rows.append(row)
 return [dict(zip(KEYS,row)) for row in rows]
def stress_holdout(seed=SEED,n=WIDE_N):
 import random
 rng=random.Random(seed);rows=[]
 scales=[1e-308,1e-300,1e-200,1e-160,1e-100,1e-10,1.,1e10,1e100,1e150,1e160,1e200,1e300,1e308]
 for x in scales:
  for y in (math.nextafter(x,math.inf),2*x if x<8e307 else x/2,-x):
   if math.isfinite(y): rows.append([x,0.0,y,0.0])
   if math.isfinite(y): rows.append([-x,0.0,y,0.0])
 while len(rows)<n:
  # Log-uniform magnitudes plus independent signs, including subnormal ranges.
  a=math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  b=math.copysign(10.**rng.uniform(-320,308),rng.choice((-1,1)))
  if math.isfinite(a) and math.isfinite(b):rows.append([a,0.0,b,0.0])
 return rows[:n]
def worker():
 import itertools
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 from adaptive_factored_operator_search_v1 import classify,truth,score
 panels,search,sel= input_data();idx=next(i for i,p in enumerate(panels) if p['task']==TASK and p['worker']==WORKER);p=panels[idx];sw=search[idx];qw=sel[idx];n=_native.Substrate();outputs=[]
 for armname in ARMS:
  base=sw[armname]; candidates=base['candidate_terms'];prior=base['final_survivor_ids'];terms=[h for h in candidates if h['id'] in prior]
  if len(terms)!=3:raise RuntimeError(f'expected three survivor Terms, got {len(terms)}')
  forbidden=[x['row'] for x in p['training']]+p['selection_order'];probes=proposal_slate(terms,forbidden)
  eval_count=0
  def evaluate(term,env):
   nonlocal eval_count
   eval_count+=1
   return classify(n.evaluate(term,env))
  start=time.perf_counter_ns();cpu=time.process_time_ns();q=qw['arms'][armname];previous=q['all_events'];survivors=terms.copy();used={tuple(e['row']) for e in previous};labels=[]
  for e in previous:
   env=dict(zip(KEYS,e['row']));survivors=[h for h in survivors if evaluate(h['term'],env) is bool(e['label'])]
  partition_before=partition_hypotheses_by_behavior(evaluate,survivors,[dict(zip(KEYS,e)) for e in p['selection_order']])
  events=[]
  while len(survivors)>1 and len(labels)<LABEL_BUDGET:
   available=[e for e in probes if tuple(float(e[k]) for k in KEYS) not in used]
   choice=select_discriminating_input(evaluate,survivors,available,[])
   if not choice.get('ok'):break
   env=choice['query'];row=tuple(float(env[k]) for k in KEYS);label=bool(truth(TASK,[env[k] for k in KEYS]));before=[h['id'] for h in survivors]
   survivors=[h for h in survivors if evaluate(h['term'],env) is label];used.add(row);labels.append({'row':list(row),'label':label});events.append({'row':list(row),'label':label,'before':before,'after':[h['id'] for h in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
  final_partition=partition_hypotheses_by_behavior(evaluate,survivors,probes)
  decision='accept_behavior_class' if len(survivors)>0 and final_partition.get('all_agree_on_probes') else 'request_help'
  policy_evaluations=eval_count;policy_wall_ns=time.perf_counter_ns()-start;policy_cpu_ns=time.process_time_ns()-cpu
  wide=stress_holdout();wide_scores=[]
  for h in terms:
   exact_finite=score(n,TASK,h['term'])['exact'];mismatch=0;invalid=0
   for row in wide:
    pred=evaluate(h['term'],dict(zip(KEYS,row)));label=bool(truth(TASK,row))
    if pred is None:invalid+=1
    elif pred is not label:mismatch+=1
   wide_scores.append({'id':h['id'],'finite_exact':exact_finite,'stress_n':len(wide),'stress_mismatches':mismatch,'stress_invalid':invalid})
  outputs.append({'arm':armname,'candidate_ids':[h['id'] for h in terms],'prior_selection_events':previous,'probe_slate':probes,'probe_count':len(probes),'prior_partition':partition_before,'new_events':events,'survivor_ids':[h['id'] for h in survivors],'final_partition':final_partition,'decision':decision,'policy_native_evaluations':policy_evaluations,'policy_wall_ns':policy_wall_ns,'policy_cpu_ns':policy_cpu_ns,'holdout_native_evaluations':len(terms)*len(wide),'wide_scoring_wall_ns':time.perf_counter_ns()-start-policy_wall_ns,'wide_scoring_cpu_ns':time.process_time_ns()-cpu-policy_cpu_ns,'wide_holdout_seed':SEED,'wide_holdout_n':WIDE_N,'wide_scores':wide_scores})
 return {'task':TASK,'worker':WORKER,'arms':outputs,'strict_singleton_control':'request_help'}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(SOUT.read_text()).get('passed') or not json.loads(SELOUT.read_text()).get('passed'):raise SystemExit('upstream analyses invalid')
  panels,_,_=input_data();LOCK.write_text(json.dumps({'schema':'TermDirectedFloatEdgeProbesV1Lock','sources':source_map(),'resynthesis_lock_sha256':sha(SL),'resynthesis_capture_sha256':sha(SRAW),'selector_lock_sha256':sha(SELLOCK),'selector_capture_sha256':sha(SELRAW),'panel':next(i for i,p in enumerate(panels) if p['task']==TASK and p['worker']==WORKER),'task':TASK,'worker':WORKER,'arms':ARMS,'label_budget':LABEL_BUDGET,'wide_seed':SEED,'wide_n':WIDE_N,'heldout_values':(-2.5,-1.5,-.5,.5,1.5,2.5)},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources']:raise SystemExit('source drift')
  row=worker()
  if source_map()!=l['sources']:raise SystemExit('source drift during worker')
  OUT.write_text(json.dumps({'schema':'TermDirectedFloatEdgeProbesV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'result':row,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
