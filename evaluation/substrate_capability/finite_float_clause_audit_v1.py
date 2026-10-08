#!/usr/bin/env python3
"""Seeded finite-binary64 differential audit for direct unary clauses."""
import hashlib,json,math,platform,random,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/FINITE_FLOAT_CLAUSE_AUDIT_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_finite_float_clause_audit_v1.py';SOLVER=ROOT/'evaluation/substrate_capability/clause_contradiction_aliasing_v1.py';SLOCK=ROOT/'evaluation/substrate_capability/clause_contradiction_aliasing_v1_lock_20261004.json';SRAW=ROOT/'evaluation/reports/clause_contradiction_aliasing_v1_20261004.json';SAN=ROOT/'evaluation/reports/clause_contradiction_aliasing_v1_analysis_20261004.json';LOCK=ROOT/'evaluation/substrate_capability/finite_float_clause_audit_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/finite_float_clause_audit_v1_20261004.json';SEED=20261004;NCASES=4096;VARS=('ax','ay');OPS=('Eq','Lt','Lte','Gt','Gte')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,SOLVER,SLOCK,SRAW,SAN]
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def random_finite(rng):
 if rng.random()<.75:
  bits=rng.getrandbits(64);x=struct.unpack('>d',bits.to_bytes(8,'big'))[0]
  if math.isfinite(x):return x
 pool=[-sys.float_info.max,math.nextafter(-sys.float_info.max,0.),-1e308,-1.,-math.ulp(0.),-0.,0.,math.ulp(0.),math.nextafter(1.,0.),1.,math.nextafter(1.,math.inf),1e308,math.nextafter(sys.float_info.max,0.),sys.float_info.max]
 return rng.choice(pool)
def cases():
 rng=random.Random(SEED);out=[]
 for i in range(NCASES):
  nv=1 if i%3 else 2;selected=VARS[:nv];mode=i%4;cons=[]
  for v in selected:
   a=random_finite(rng);b=random_finite(rng)
   if mode==0:
    lo,hi=sorted((a,b));cons.extend([(v,'Gte',lo),(v,'Lte',hi)])
   elif mode==1:
    lo,hi=sorted((a,b));cons.extend([(v,'Gt',hi),(v,'Lt',lo)])
   elif mode==2:
    cons.extend([(v,'Eq',a),(v,'Eq',b)])
   else:
    for _ in range(rng.randint(1,4)):cons.append((v,rng.choice(OPS),random_finite(rng)))
  target_len=max(len(cons),rng.randint(1,8))
  while len(cons)<target_len:
   v=rng.choice(selected);cons.append((v,rng.choice(OPS),random_finite(rng)))
  # Keep clauses bounded to eight atoms and ensure deterministic variable layout.
  cons=cons[:8]
  out.append({'id':i,'constraints':cons})
 return out
def term_for(cs):
 items=[]
 for v,op,x in cs:items.append({'type':op,'a':{'type':'Var','name':v},'b':{'type':'Lit','value':x}})
 return {'type':'And','items':items}
def holds(value,op,bound):
 if op=='Eq':return value==bound
 if op=='Lt':return value<bound
 if op=='Lte':return value<=bound
 if op=='Gt':return value>bound
 if op=='Gte':return value>=bound
 raise ValueError(op)
def main():
 from clause_contradiction_aliasing_v1 import solve_clause
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 a=sys.argv[1:];panel=cases()
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(SAN.read_text()).get('passed'):raise SystemExit('upstream proof-fragment analysis invalid')
  LOCK.write_text(json.dumps({'schema':'FiniteFloatClauseAuditV1Lock','sources':source_map(),'upstream_lock_sha256':sha(SLOCK),'upstream_capture_sha256':sha(SRAW),'seed':SEED,'case_count':NCASES,'cases':panel},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources'] or canon(panel)!=canon(lock['cases']) or sha(SRAW)!=lock['upstream_capture_sha256']:raise SystemExit('source/case drift')
  n=_native.Substrate();started=time.perf_counter_ns();cpu=time.process_time_ns();workers=[];native_calls=0;comparisons=0
  for c in panel:
   cs=c['constraints'];clause=[(v,op,x) for v,op,x in cs];status,row,checks=solve_clause(clause);comparisons+=len(cs);witness=None;native_result=None;python_result=None
   if status=='satisfiable':
    witness={v:float(row[VARS.index(v)]) for v in VARS};python_result=all(holds(witness[v],op,x) for v,op,x in cs)
    native_result=classify(n.evaluate(term_for(cs),witness));native_calls+=1
   workers.append({'id':c['id'],'solver_status':status,'witness':witness,'python_witness_valid':python_result,'native_witness_result':native_result,'constraint_checks':checks})
  result={'schema':'FiniteFloatClauseAuditV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':workers,'cases':NCASES,'constraint_count':comparisons,'native_witness_evaluations':native_calls,'wall_ns':time.perf_counter_ns()-started,'cpu_ns':time.process_time_ns()-cpu,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
  if source_map()!=lock['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
