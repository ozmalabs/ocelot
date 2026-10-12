#!/usr/bin/env python3
"""Transfer and fail-closed evaluation for clause-aware proposals."""
import hashlib,json,math,platform,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/CLAUSE_AWARE_GENERATED_GUARDS_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_clause_aware_generated_guards_v1.py';CLAUSE=ROOT/'evaluation/substrate_capability/clause_aware_literal_proposals_v1.py';CLOCK=ROOT/'evaluation/substrate_capability/clause_aware_literal_proposals_v1_lock_20261004.json';CRAW=ROOT/'evaluation/reports/clause_aware_literal_proposals_v1_20261004.json';CAN=ROOT/'evaluation/reports/clause_aware_literal_proposals_v1_analysis_20261004.json';BUDGET=ROOT/'evaluation/substrate_capability/literal_proposal_budget_stress_v1.py';BRAW=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_20261004.json';BANA=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_analysis_20261004.json';LOCK=ROOT/'evaluation/substrate_capability/clause_aware_generated_guards_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/clause_aware_generated_guards_v1_20261004.json';KEYS=('ax','ay','ex','ey');CAP=8
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def V(x):return {'type':'Var','name':x}
def L(x):return {'type':'Lit','value':x}
def C(op,a,b):return {'type':op,'a':a,'b':b}
def cmp_branch(vars_,start,strict=False):
 items=[];w=[]
 for i,v in enumerate(vars_):
  lo=float(start+10*i);hi=lo+0.5
  if strict and i%2:items.extend([C('Lt',L(lo),V(v)),C('Gte',L(hi),V(v))]);w.append((lo+hi)/2)
  else:items.extend([C('Gte',V(v),L(lo)),C('Lt',V(v),L(hi))]);w.append((lo+hi)/2)
 return {'type':'And','items':items},w
def base_panels():
 import literal_proposal_budget_stress_v1 as b
 p0=b.panel();cases=[]
 for n in (2,3,4):
  guard,w=cmp_branch(KEYS[:n],20.,strict=True)
  cases.append((f'interval_arity_{n}',guard,w,False))
 a,w1=cmp_branch(('ax','ay'),30.);b,w2=cmp_branch(('ex','ey'),50.,True)
 nw=[w1[0],w1[1],w2[0],w2[1]]
 cases.append(('nested_interval_disjunction',{'type':'Or','items':[a,b]},nw,False))
 plus={'type':'Plus','items':[V('ax'),V('ay')]};times={'type':'Times','items':[V('ax'),V('ay')]}
 cases.append(('unsupported_plus_equality',C('Eq',plus,L(72.25)),[25.25,47.,0.,0.],True))
 cases.append(('unsupported_times_equality',C('Eq',times,L(117.)),[9.,13.,0.,0.],True))
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();out=[]
 for name,guard,witness,unsupported in cases:
  q=dict(p0);q['name']=name;q['terms']=p0['terms'][:];term={'type':'Or','items':[C('Eq',V('ax'),V('ex')),guard]};q['terms']=[q['terms'][0],{'id':'false_'+name,'term':term}]
  row=[0.,0.,0.,0.]
  for key,val in zip(KEYS,witness):row[KEYS.index(key)]=float(val)
  q['witness']=row;q['unsupported_expected']=unsupported
  hold=[]
  for old in p0['holdout']:
   if classify(n.evaluate(term,dict(zip(KEYS,old)))) is not True:hold.append(list(old))
  hold.extend([row]);q['holdout']=hold[:4096];out.append(q)
 return out
def branches(guard):
 if isinstance(guard,dict) and guard.get('type')=='Or':
  out=[]
  for x in guard.get('items',[]):out.extend(branches(x))
  return out
 return [guard]
def constraints(branch):
 if not isinstance(branch,dict) or branch.get('type')!='And':return None
 out=[];inv={'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'}
 for z in branch.get('items',[]):
  if not isinstance(z,dict) or z.get('type') not in inv:return None
  a=z.get('a',{});b=z.get('b',{});op=z['type']
  if a.get('type')=='Var' and b.get('type')=='Lit' and isinstance(b.get('value'),(int,float)):out.append((a['name'],op,float(b['value'])))
  elif b.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):out.append((b['name'],inv[op],float(a['value'])))
  else:return None
 return out or None
def clauses(guard):
 cs=[];unsupported=0
 for b in branches(guard):
  c=constraints(b)
  if c is None:unsupported+=1
  else:cs.append(c)
 return cs,unsupported
def sat(v,cs):
 for op,x in cs:
  if op=='Eq' and v!=x:return False
  if op=='Lt' and not v<x:return False
  if op=='Lte' and not v<=x:return False
  if op=='Gt' and not v>x:return False
  if op=='Gte' and not v>=x:return False
 return True
def propose(panel,base):
 denied={fpkey(z['row']) for z in panel['training']}|{fpkey(z) for z in panel['prior_pool']}|{fpkey(z) for z in panel['holdout']}|{fpkey(z) for z in base};out=[];tests=0;allclauses=[];unsupported=0
 for t in panel['terms'][1:]:
  root=t['term'];guard=root['items'][1];cs,bad=clauses(guard);allclauses.extend(cs);unsupported+=bad
  for branch in cs:
   by={}
   for v,op,x in branch:by.setdefault(v,[]).append((op,x))
   env={k:0. for k in KEYS};valid=True
   for v,limits in by.items():
    candidates=set()
    for _,x in limits:candidates.update((x,math.nextafter(x,-math.inf),math.nextafter(x,math.inf)))
    matches=[]
    for x in sorted(candidates):
     tests+=len(limits)
     if sat(x,limits):matches.append(x)
    if not matches:valid=False;break
    env[v]=matches[0]
   row=[env[k] for k in KEYS]
   if valid and env['ax']!=env['ex'] and fpkey(row) not in denied and row not in out:out.append(row)
 return out,unsupported,{'supported_clauses':len(allclauses),'unsupported_branches':unsupported,'constraint_checks':tests}
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,CLAUSE,CLOCK,CRAW,CAN,BUDGET,BRAW,BANA,ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1.py',ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def main():
 import clause_aware_literal_proposals_v1 as c,literal_proposal_budget_stress_v1 as budget
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from term_literal_probe_repair_v1 import probe_slates,policy,truth
 a=sys.argv[1:]
 ps=base_panels()
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(CAN.read_text()).get('passed') or not json.loads(BANA.read_text()).get('passed'):raise SystemExit('upstream analysis invalid')
  LOCK.write_text(json.dumps({'schema':'ClauseAwareGeneratedGuardsV1Lock','sources':source_map(),'upstream_clause_lock_sha256':sha(CLOCK),'upstream_clause_capture_sha256':sha(CRAW),'panels':{p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps},'label_cap':CAP},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources'] or {p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps}!=lock['panels']:raise SystemExit('source/panel drift')
  workers=[]
  for p in ps:
   edge,lit=probe_slates(p);base=edge+lit;st=time.perf_counter_ns();cpu=time.process_time_ns();rows,unsupported,cost=propose(p,base);cost.update({'wall_ns':time.perf_counter_ns()-st,'cpu_ns':time.process_time_ns()-cpu});arms=[]
   for name,probes,incomplete in [('pairwise',base,False),('clause_aware',base+rows,unsupported>0)]:
    n=_native.Substrate();q=policy(n,p,probes);under=q['decision'];final='request_help' if incomplete and under=='accept_behavior_class' else under;scores=[]
    for t in p['terms']:
     bad=invalid=0
     for r in p['holdout']:
      y=classify(n.evaluate(t['term'],dict(zip(KEYS,r))));label=bool(truth(p['task'],r))
      if y is None:invalid+=1
      elif y is not label:bad+=1
     scores.append({'id':t['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
    arms.append({'policy':name,'incomplete':incomplete,'probe_rows':probes,'events':q['events'],'survivor_ids':q['survivor_ids'],'underlying_decision':under,'decision':final,'native_evaluations':q['native_evaluations'],'wall_ns':q['wall_ns'],'cpu_ns':q['cpu_ns'],'holdout_scores':scores})
   workers.append({'name':p['name'],'unsupported_expected':p['unsupported_expected'],'witness':p['witness'],'clause_proposals':rows,'proposal_analysis':cost,'arms':arms})
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'ClauseAwareGeneratedGuardsV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':workers,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
