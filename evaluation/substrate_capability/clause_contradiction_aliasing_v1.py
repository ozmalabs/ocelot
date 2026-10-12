#!/usr/bin/env python3
"""Classify direct comparison clauses as satisfiable, impossible, or unresolved."""
import hashlib,json,math,platform,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/CLAUSE_CONTRADICTION_ALIASING_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_clause_contradiction_aliasing_v1.py';BASE=ROOT/'evaluation/substrate_capability/clause_aware_generated_guards_v1.py';BASELOCK=ROOT/'evaluation/substrate_capability/clause_aware_generated_guards_v1_lock_20261004.json';BASERAW=ROOT/'evaluation/reports/clause_aware_generated_guards_v1_20261004.json';BASEAN=ROOT/'evaluation/reports/clause_aware_generated_guards_v1_analysis_20261004.json';CLAUSE=ROOT/'evaluation/substrate_capability/clause_aware_literal_proposals_v1.py';CLOCK=ROOT/'evaluation/substrate_capability/clause_aware_literal_proposals_v1_lock_20261004.json';CRAW=ROOT/'evaluation/reports/clause_aware_literal_proposals_v1_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/clause_contradiction_aliasing_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/clause_contradiction_aliasing_v1_20261004.json';KEYS=('ax','ay','ex','ey');CAP=8
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def V(x):return {'type':'Var','name':x}
def L(x):return {'type':'Lit','value':x}
def C(op,a,b):return {'type':op,'a':a,'b':b}
def wrap(p,name,guard,witness=None,expected='satisfiable'):
 q=dict(p);q['name']=name;q['terms']=p['terms'][:];term={'type':'Or','items':[C('Eq',V('ax'),V('ex')),guard]};q['terms']=[q['terms'][0],{'id':'false_'+name,'term':term}];q['witness']=witness;q['status_expected']=expected
 if witness is not None:
  from substrate_rs import _native
  from adaptive_factored_operator_search_v1 import classify
  n=_native.Substrate();rows=[list(r) for r in p['holdout'] if classify(n.evaluate(term,dict(zip(KEYS,r)))) is not True];rows.append(witness);q['holdout']=rows[:4096]
 else:
  from substrate_rs import _native
  from adaptive_factored_operator_search_v1 import classify
  n=_native.Substrate();q['holdout']=[list(r) for r in p['holdout'] if classify(n.evaluate(term,dict(zip(KEYS,r)))) is not True]
 return q
def panels():
 import clause_aware_generated_guards_v1 as g
 p=next(x for x in g.base_panels() if x['name']=='interval_arity_4');out=list(g.base_panels())
 for x in out:x['status_expected']='unresolved' if x['unsupported_expected'] else 'satisfiable'
 contradiction={'type':'And','items':[C('Gte',V('ax'),L(80.)),C('Lt',V('ax'),L(70.)),C('Gte',V('ay'),L(90.)),C('Lt',V('ay'),L(91.))]}
 out.append(wrap(p,'contradictory_bounds',contradiction,None,'unsat'))
 nxt=math.nextafter(1.,math.inf);gap={'type':'And','items':[C('Gt',V('ax'),L(1.)),C('Lt',V('ax'),L(nxt)),C('Gte',V('ay'),L(95.)),C('Lt',V('ay'),L(96.))]}
 out.append(wrap(p,'adjacent_float_gap',gap,None,'unsat'))
 max_finite=sys.float_info.max;overflow={'type':'And','items':[C('Gt',V('ax'),L(max_finite)),C('Gte',V('ay'),L(95.)),C('Lt',V('ay'),L(96.))]}
 out.append(wrap(p,'finite_domain_upper_edge',overflow,None,'unsat'))
 repeated={'type':'And','items':[C('Gte',V('ax'),L(70.)),C('Lt',V('ax'),L(71.)),C('Lte',V('ax'),L(70.5)),C('Gte',V('ay'),L(80.)),C('Lt',V('ay'),L(81.))]}
 out.append(wrap(p,'repeated_compatible_bounds',repeated,[70.25,80.25,0.,0.]))
 alias={'type':'And','items':[C('Eq',V('ax'),V('ay')),C('Gte',V('ax'),L(90.)),C('Lt',V('ax'),L(91.))]}
 out.append(wrap(p,'cross_variable_alias',alias,[90.25,90.25,0.,0.],'unresolved'))
 combo={'type':'Or','items':[contradiction,alias]}
 out.append(wrap(p,'unsat_plus_alias_disjunction',combo,[90.25,90.25,0.,0.],'unresolved'))
 return out
def branches(g):
 if isinstance(g,dict) and g.get('type')=='Or':return sum((branches(z) for z in g.get('items',[])),[])
 return [g]
def parse_clause(b):
 if not isinstance(b,dict) or b.get('type')!='And':return None
 inv={'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'};out=[]
 for z in b.get('items',[]):
  if not isinstance(z,dict) or z.get('type') not in inv:return None
  a=z.get('a',{});c=z.get('b',{});op=z['type']
  if a.get('type')=='Var' and c.get('type')=='Lit' and isinstance(c.get('value'),(int,float)):out.append((a['name'],op,float(c['value'])))
  elif c.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):out.append((c['name'],inv[op],float(a['value'])))
  else:return None
 return out or None
def sat(v,cs):
 for op,x in cs:
  if op=='Eq' and v!=x:return False
  if op=='Lt' and not v<x:return False
  if op=='Lte' and not v<=x:return False
  if op=='Gt' and not v>x:return False
  if op=='Gte' and not v>=x:return False
 return True
def solve_clause(cs):
 by={}
 for v,op,x in cs:by.setdefault(v,[]).append((op,x))
 env={k:0. for k in KEYS};checks=0
 for v,limits in by.items():
  candidates=set()
  for _,x in limits:candidates.update((x,math.nextafter(x,-math.inf),math.nextafter(x,math.inf)))
  found=[]
  for x in sorted(candidates):
   if not math.isfinite(x):continue
   checks+=len(limits)
   if sat(x,limits):found.append(x)
  if found:env[v]=found[0];continue
  # For finite binary64 values and conjunctions of unary order/equality
  # comparisons, all endpoints and adjacent floats suffice to decide emptiness.
  return 'proven_unsat',None,checks
 return 'satisfiable',[env[k] for k in KEYS],checks
def classify_guard(guard):
 statuses=[];rows=[];checks=0
 for b in branches(guard):
  cs=parse_clause(b)
  if cs is None:statuses.append('unresolved');continue
  status,row,n=solve_clause(cs);checks+=n;statuses.append(status)
  if row is not None:rows.append(row)
 return statuses,rows,checks
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,BASE,BASELOCK,BASERAW,BASEAN,CLAUSE,CLOCK,CRAW,ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1.py',ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def main():
 import term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 a=sys.argv[1:];ps=panels()
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(BASEAN.read_text()).get('passed'):raise SystemExit('upstream generated guard invalid')
  LOCK.write_text(json.dumps({'schema':'ClauseContradictionAliasingV1Lock','sources':source_map(),'upstream_lock_sha256':sha(BASELOCK),'upstream_capture_sha256':sha(BASERAW),'panels':{p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps},'label_cap':CAP},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources'] or {p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps}!=lock['panels']:raise SystemExit('source/panel drift')
  results=[]
  for p in ps:
   edge,lit=h.probe_slates(p);base=edge+lit;guard=p['terms'][1]['term']['items'][1];st=time.perf_counter_ns();cpu=time.process_time_ns();statuses,raw_rows,checks=classify_guard(guard);denied={fpkey(z['row']) for z in p['training']}|{fpkey(z) for z in p['prior_pool']}|{fpkey(z) for z in p['holdout']}|{fpkey(z) for z in base};rows=[]
   for row in raw_rows:
    if row[0]!=row[2] and fpkey(row) not in denied and row not in rows:rows.append(row)
   missing=max(0,statuses.count('satisfiable')-len(rows));gen={'statuses':statuses,'constraint_checks':checks,'unproposed_satisfiable_branches':missing,'wall_ns':time.perf_counter_ns()-st,'cpu_ns':time.process_time_ns()-cpu};unresolved=statuses.count('unresolved')>0 or missing>0;arms=[]
   for name,probes,incomplete in [('pairwise',base,False),('clause_aware',base+rows,unresolved)]:
    wall_start=time.perf_counter_ns();cpu_start=time.process_time_ns();n=_native.Substrate();calls=0
    def ev(term,env):
     nonlocal calls
     calls+=1;return classify(n.evaluate(term,env))
    survivors=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
    while len(survivors)>1 and len(events)<CAP:
     avail=[dict(zip(KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,survivors,avail,[])
     if not choice.get('ok'):break
     q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(h.truth(p['task'],row));before=[z['id'] for z in survivors];survivors=[z for z in survivors if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
    part=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in probes]);under='accept_behavior_class' if survivors and part['all_agree_on_probes'] else 'request_help';false_survives=p['terms'][1]['id'] in [z['id'] for z in survivors];final='request_help' if incomplete and false_survives and under=='accept_behavior_class' else under;scores=[]
    for t in p['terms']:
     bad=invalid=0
     for r in p['holdout']:
      pred=classify(n.evaluate(t['term'],dict(zip(KEYS,r))));truth=bool(h.truth(p['task'],r))
      if pred is None:invalid+=1
      elif pred is not truth:bad+=1
     scores.append({'id':t['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
    arms.append({'policy':name,'incomplete':incomplete,'proposal_rows':probes,'events':events,'survivor_ids':[z['id'] for z in survivors],'prior_partition':prior,'final_partition':part,'underlying_decision':under,'decision':final,'native_evaluations':calls,'wall_ns':time.perf_counter_ns()-wall_start,'cpu_ns':time.process_time_ns()-cpu_start,'holdout_scores':scores})
   results.append({'name':p['name'],'status_expected':p['status_expected'],'witness':p['witness'],'clause_proposals':rows,'clause_analysis':gen,'arms':arms})
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'ClauseContradictionAliasingV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':results,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
