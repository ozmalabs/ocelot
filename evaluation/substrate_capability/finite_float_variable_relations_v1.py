#!/usr/bin/env python3
"""Generate and capture two-variable finite-float relation stress cases."""
import hashlib,itertools,json,math,platform,random,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/FINITE_FLOAT_VARIABLE_RELATIONS_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_finite_float_variable_relations_v1.py';BASE=ROOT/'evaluation/substrate_capability/finite_float_clause_audit_v1.py';BLOCK=ROOT/'evaluation/substrate_capability/finite_float_clause_audit_v1_lock_20261004.json';BRAW=ROOT/'evaluation/reports/finite_float_clause_audit_v1_20261004.json';BAN=ROOT/'evaluation/reports/finite_float_clause_audit_v1_analysis_20261004.json';SOLVER=ROOT/'evaluation/substrate_capability/clause_contradiction_aliasing_v1.py';SLOCK=ROOT/'evaluation/substrate_capability/clause_contradiction_aliasing_v1_lock_20261004.json';LOCK=ROOT/'evaluation/substrate_capability/finite_float_variable_relations_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/finite_float_variable_relations_v1_20261004.json';SEED=20261005;NCASES=1024;VARS=('ax','ay');OPS=('Eq','Lt','Lte','Gt','Gte')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,BASE,BLOCK,BRAW,BAN,SOLVER,SLOCK]
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def finite(rng):
 if rng.random()<.7:
  x=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
  if math.isfinite(x):return x
 pool=[-sys.float_info.max,math.nextafter(-sys.float_info.max,0.),-1e308,-1.,-math.ulp(0.),-0.,0.,math.ulp(0.),math.nextafter(1.,0.),1.,math.nextafter(1.,math.inf),1e308,math.nextafter(sys.float_info.max,0.),sys.float_info.max]
 return rng.choice(pool)
def cases():
 rng=random.Random(SEED);out=[]
 for i in range(NCASES):
  atoms=[];n=rng.randint(1,8);j=rng.randrange(n)
  for k in range(n):
   op=rng.choice(OPS)
   if k==j or rng.random()<.35:
    atoms.append({'a':{'type':'Var','name':rng.choice(VARS)},'op':op,'b':{'type':'Var','name':rng.choice(VARS)}})
   else:
    atoms.append({'a':{'type':'Var','name':rng.choice(VARS)},'op':op,'b':{'type':'Lit','value':finite(rng)}})
  out.append({'id':i,'atoms':atoms})
 return out
def term(case):return {'type':'And','items':[{'type':a['op'],'a':a['a'],'b':a['b']} for a in case['atoms']]}
def values(case):
 pool={-sys.float_info.max,sys.float_info.max,-0.,0.}
 for a in case['atoms']:
  if a['b']['type']!='Lit':continue
  x=float(a['b']['value']);pool.add(x)
  y=x
  for _ in range(2):
   y=math.nextafter(y,-math.inf)
   if math.isfinite(y):pool.add(y)
  y=x
  for _ in range(2):
   y=math.nextafter(y,math.inf)
   if math.isfinite(y):pool.add(y)
 return sorted(pool)
def holds(x,op,y):
 if op=='Eq':return x==y
 if op=='Lt':return x<y
 if op=='Lte':return x<=y
 if op=='Gt':return x>y
 if op=='Gte':return x>=y
 raise ValueError(op)
def main():
 from clause_contradiction_aliasing_v1 import parse_clause
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 a=sys.argv[1:];cs=cases()
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(BAN.read_text()).get('passed'):raise SystemExit('upstream finite audit invalid')
  LOCK.write_text(json.dumps({'schema':'FiniteFloatVariableRelationsV1Lock','sources':source_map(),'upstream_lock_sha256':sha(BLOCK),'upstream_capture_sha256':sha(BRAW),'seed':SEED,'case_count':NCASES,'cases':cs},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources'] or canon(cs)!=canon(lock['cases']) or sha(BRAW)!=lock['upstream_capture_sha256']:raise SystemExit('source/case drift')
  n=_native.Substrate();started=time.perf_counter_ns();cpu=time.process_time_ns();workers=[];total_pairs=0;native_calls=0
  for case in cs:
   vals=values(case);total_pairs+=len(vals)*len(vals);witness=None
   for x,y in itertools.product(vals,repeat=2):
    env={'ax':x,'ay':y}
    if all(holds(env[a['a']['name']],a['op'],env[a['b']['name']]) if a['b']['type']=='Var' else holds(env[a['a']['name']],a['op'],float(a['b']['value'])) for a in case['atoms']):witness=env;break
   status='satisfiable' if witness is not None else 'no_representative_witness'
   constraints=[]
   for a in case['atoms']:
    if a['a']['type']=='Var' and a['b']['type']=='Lit':constraints.append((a['a']['name'],a['op'],float(a['b']['value'])))
    elif a['b']['type']=='Var' and a['a']['type']=='Lit':constraints.append((a['b']['name'],{'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'}[a['op']],float(a['a']['value'])))
    else:constraints=[];break
   parse_status='unresolved' if parse_clause({'type':'And','items':term(case)['items']}) is None else 'supported'
   native_result=None
   if witness is not None:native_result=classify(n.evaluate(term(case),witness));native_calls+=1
   workers.append({'id':case['id'],'reference_status':status,'witness':witness,'parse_status':parse_status,'native_result':native_result,'representative_domain_size':len(vals)})
  result={'schema':'FiniteFloatVariableRelationsV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':workers,'cases':NCASES,'representative_pairs':total_pairs,'native_witness_evaluations':native_calls,'wall_ns':time.perf_counter_ns()-started,'cpu_ns':time.process_time_ns()-cpu,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
