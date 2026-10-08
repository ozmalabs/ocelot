#!/usr/bin/env python3
"""Probe boundary recovery from authored candidate Term syntax, without a bound side channel."""
import hashlib,json,os,platform,subprocess,sys,time,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_DERIVED_PROBE_GENERATION_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_derived_probe_generation_v1.py'
POL=ROOT/'evaluation/substrate_capability/boundary_probe_policy_comparison_v1.py';ULOCK=ROOT/'evaluation/substrate_capability/boundary_probe_policy_comparison_v1_lock_20261004.json';URAW=ROOT/'evaluation/reports/boundary_probe_policy_comparison_v1_20261004.json';UAN=ROOT/'evaluation/reports/boundary_probe_policy_comparison_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/term_derived_probe_generation_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_derived_probe_generation_v1_20261004.json'
TASKS=('additive','product');THRESHOLDS=(3.75,5.,8.);ENCODINGS=('lt','not_ge','reverse_gt','affine_lt');OFFSETS={'affine_lt':2.5};SEED=744103;N=512
SOURCES=('docs/research/engine_substrate/TERM_DERIVED_PROBE_GENERATION_V1_PREREG_20261004.md','evaluation/substrate_capability/term_derived_probe_generation_v1.py','evaluation/substrate_capability/analyze_term_derived_probe_generation_v1.py','evaluation/substrate_capability/boundary_probe_policy_comparison_v1.py','evaluation/substrate_capability/boundary_probe_policy_comparison_v1_lock_20261004.json','evaluation/reports/boundary_probe_policy_comparison_v1_20261004.json','evaluation/reports/boundary_probe_policy_comparison_v1_analysis_20261004.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','domains/engine_provenance.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 b=Path(_native.__file__).resolve();return {'files':{p:sha(ROOT/p) for p in SOURCES},'binary':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def V(n):return {'type':'Var','name':n}
def L(x):return {'type':'Lit','value':x}
def cmp(op,a,b):return {'type':op,'a':a,'b':b}
def base_relation(task):
 op='Plus' if task=='additive' else 'Times'
 def f(x,y):return {'type':op,'items':[V(x),V(y)]}
 return cmp('Eq',f('ax','ay'),f('ex','ey')),cmp('Eq',f('ay','ax'),f('ey','ex'))
def guard(encoding,c):
 k=OFFSETS.get(encoding,0.0)
 if encoding=='lt':return cmp('Lt',V('ax'),L(c))
 if encoding=='not_ge':return {'type':'Not','arg':cmp('Gte',V('ax'),L(c))}
 if encoding=='reverse_gt':return cmp('Gt',L(c),V('ax'))
 return cmp('Lt',{'type':'Plus','items':[V('ax'),L(k)]},L(c+k))
def candidates(task,encoding,c):
 a,b=base_relation(task);g=guard(encoding,c)
 return [{'id':'exact_a','term':a},{'id':'exact_b','term':b},{'id':'bounded','term':{'type':'And','items':[a,g]}}]
def affine(t):
 if not isinstance(t,dict):return None
 if t.get('type')=='Var' and t.get('name')=='ax':return (1.0,0.0)
 if t.get('type')=='Lit' and isinstance(t.get('value'),(int,float)):return (0.0,float(t['value']))
 if t.get('type') in ('Plus','Minus'):
  xs=t.get('items') if t['type']=='Plus' else [t.get('a'),t.get('b')]
  if not isinstance(xs,list) or len(xs)!=2:return None
  x,y=affine(xs[0]),affine(xs[1])
  if x is None or y is None:return None
  return (x[0]+y[0],x[1]+y[1]) if t['type']=='Plus' else (x[0]-y[0],x[1]-y[1])
 return None
def extract(t):
 if t.get('type')=='Not' and isinstance(t.get('arg'),dict):
  q=t['arg']
  if q.get('type')=='Gte' and q.get('a')==V('ax') and q.get('b',{}).get('type')=='Lit':return float(q['b']['value'])
 if t.get('type')=='Lt':
  left,right=affine(t.get('a')),affine(t.get('b'))
  if left and right and left[0]==1 and right[0]==0:return right[1]-left[1]
 if t.get('type')=='Gt':
  left,right=affine(t.get('a')),affine(t.get('b'))
  if left and right and left[0]==0 and right[0]==1:return left[1]-right[1]
 return None
def env(task,x):return {'ax':float(x),'ay':0. if task=='additive' else 1.,'ex':float(x),'ey':0. if task=='additive' else 1.}
def build_panels():
 u=json.loads(ULOCK.read_text());pairs=[]
 for task in TASKS:
  src=list({p['worker']:p['base_panel'] for p in u['panels'] if p['task']==task}.values())
  for base in src:
   for c in THRESHOLDS:
    for encoding in ENCODINGS:pairs.append({'task':task,'worker':base['worker'],'threshold':c,'encoding':encoding,'base_panel':base,'candidate_terms':candidates(task,encoding,c)})
 return pairs
def worker(p):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 pol=__import__('boundary_probe_policy_comparison_v1');native=_native.Substrate();task=p['task'];terms=p['candidate_terms']
 derived=extract(terms[2]['term']['items'][1]);probes=[env(task,x) for x in (derived-.5,derived,derived+.5)] if derived is not None else []
 t=time.perf_counter_ns();choice=select_discriminating_input(lambda term,e:native.evaluate(term,e),terms,probes,[]);elapsed=time.perf_counter_ns()-t
 if not choice.get('ok'):return {'task':task,'worker':p['worker'],'threshold':p['threshold'],'encoding':p['encoding'],'derived_bound':derived,'probes':probes,'choice':choice,'selection_ns':elapsed,'survivor_ids':[],'wide_errors':None}
 q=choice['query'];label=(q['ax']+q['ay']==q['ex']+q['ey']) if task=='additive' else (q['ax']*q['ay']==q['ex']*q['ey'])
 survivors=[h['id'] for h in terms if native.evaluate(h['term'],q) is label]
 rng=random.Random(SEED+p['worker']+int(p['threshold']*100)+ENCODINGS.index(p['encoding'])+(10000 if task=='product' else 0));cases=[]
 for _ in range(N):
  x=rng.randint(-12,12)
  cases.append(env(task,x))
 wide_errors=sum(native.evaluate(terms[2]['term'],e) is not True for e in cases)
 return {'task':task,'worker':p['worker'],'threshold':p['threshold'],'encoding':p['encoding'],'derived_bound':derived,'probes':probes,'choice':choice,'selection_ns':elapsed,'query':q,'label':label,'survivor_ids':survivors,'wide_bounded_errors':wide_errors,'wide_n':len(cases)}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  panels=build_panels();LOCK.write_text(json.dumps({'schema':'TermDerivedProbeGenerationV1Lock','sources':source_map(),'upstream_lock_sha256':sha(ULOCK),'panels':panels,'thresholds':THRESHOLDS,'encodings':ENCODINGS,'seed':SEED,'wide_n':N},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());ps=build_panels()
  if source_map()!=l['sources'] or ps!=l['panels']:raise SystemExit('lock/source/panel drift')
  rows=[];e={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
  for i,p in enumerate(ps):
   x=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=e,text=True,capture_output=True,timeout=60)
   if x.returncode:raise RuntimeError(x.stderr[-2000:])
   rows.append(json.loads(x.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'TermDerivedProbeGenerationV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':rows,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':
  print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(a[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
