#!/usr/bin/env python3
"""Test direct-comparison clause proposals against literal-product controls."""
import hashlib,json,math,platform,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/CLAUSE_AWARE_LITERAL_PROPOSALS_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_clause_aware_literal_proposals_v1.py';BUDGET=ROOT/'evaluation/substrate_capability/literal_proposal_budget_stress_v1.py';BUDGET_LOCK=ROOT/'evaluation/substrate_capability/literal_proposal_budget_stress_v1_lock_20261004.json';BUDGET_RAW=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_20261004.json';BUDGET_ANALYSIS=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/clause_aware_literal_proposals_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/clause_aware_literal_proposals_v1_20261004.json';CAP=8;KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,BUDGET,BUDGET_LOCK,BUDGET_RAW,BUDGET_ANALYSIS,ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1.py',ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def cmp_constraints(branch):
 out=[]
 for item in branch.get('items',[]):
  if not isinstance(item,dict) or item.get('type') not in ('Eq','Lt','Lte','Gt','Gte'):return []
  a=item.get('a',{});b=item.get('b',{})
  if a.get('type')=='Var' and b.get('type')=='Lit' and isinstance(b.get('value'),(int,float)):out.append((a['name'],item['type'],float(b['value'])))
  elif b.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):
   inv={'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'};out.append((b['name'],inv[item['type']],float(a['value'])))
  else:return []
 return out
def clauses(term):
 found=[]
 def walk(x):
  if isinstance(x,dict):
   if x.get('type')=='And':
    c=cmp_constraints(x)
    if c:found.append(c)
   for z in x.values():walk(z)
  elif isinstance(x,list):
   for z in x:walk(z)
 walk(term)
 uniq=[]
 for c in found:
  if c not in uniq:uniq.append(c)
 return uniq
def satisfies(v,cs):
 for op,x in cs:
  if op=='Eq' and not v==x:return False
  if op=='Lt' and not v<x:return False
  if op=='Lte' and not v<=x:return False
  if op=='Gt' and not v>x:return False
  if op=='Gte' and not v>=x:return False
 return True
def clause_rows(panel,base):
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 denied={fpkey(x['row']) for x in panel['training']}|{fpkey(x) for x in panel['prior_pool']}|{fpkey(x) for x in panel['holdout']}|{fpkey(x) for x in base};rows=[];checks=0;branch_count=0
 n=_native.Substrate()
 for term in (h['term'] for h in panel['terms']):
  for branch in clauses(term):
   branch_count+=1;by={}
   for v,op,x in branch:by.setdefault(v,[]).append((op,x))
   env={k:0. for k in KEYS};valid=True
   for v,cs in by.items():
    cands=set()
    for _,x in cs:cands.update((x,math.nextafter(x,-math.inf),math.nextafter(x,math.inf)))
    matches=[]
    for c in sorted(cands):
     checks+=len(cs)
     if satisfies(c,cs):matches.append(c)
    if not matches:valid=False;break
    env[v]=matches[0]
   if not valid:continue
   row=[env[k] for k in KEYS]
   if fpkey(row) in denied or row in rows:continue
   # Retain only a disagreement candidate: the synthetic oracle is identity.
   if env['ax']==env['ex']:continue
   rows.append(row)
 return rows,{'branch_count':branch_count,'constraint_checks':checks}
def main():
 import literal_proposal_budget_stress_v1 as b
 import term_literal_probe_repair_v1 as h
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(BUDGET_ANALYSIS.read_text()).get('passed'):raise SystemExit('upstream budget analysis invalid')
  p=b.panel();base,extra=b.all_joint(p);LOCK.write_text(json.dumps({'schema':'ClauseAwareLiteralProposalsV1Lock','sources':source_map(),'upstream_lock_sha256':sha(BUDGET_LOCK),'upstream_capture_sha256':sha(BUDGET_RAW),'panel_sha256':hashlib.sha256(canon(p)).hexdigest(),'joint_product_size':len(extra)},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text());p=b.panel();base,extra=b.all_joint(p)
  if source_map()!=lock['sources'] or sha(BUDGET_RAW)!=lock['upstream_capture_sha256'] or hashlib.sha256(canon(p)).hexdigest()!=lock['panel_sha256']:raise SystemExit('source/panel drift')
  gen_wall=time.perf_counter_ns();gen_cpu=time.process_time_ns();rows,cost=clause_rows(p,base);cost['wall_ns']=time.perf_counter_ns()-gen_wall;cost['cpu_ns']=time.process_time_ns()-gen_cpu
  arms=[b.arm(p,'exhaustive',base+extra,False),b.arm(p,'budgeted_64',base+extra[:b.BUDGET],len(extra)>b.BUDGET),b.arm(p,'clause_aware',base+rows,False)]
  res={'schema':'ClauseAwareLiteralProposalsV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'panel':p,'joint_product_size':len(extra),'pairwise_base_count':len(base),'clause_rows':rows,'clause_generation':cost,'arms':arms,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
