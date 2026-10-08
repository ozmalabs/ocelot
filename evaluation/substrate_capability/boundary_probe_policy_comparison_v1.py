#!/usr/bin/env python3
"""Compare current, abstain, directed-boundary, and fixed-grid probe policies."""
import hashlib,json,os,platform,subprocess,sys,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/BOUNDARY_PROBE_POLICY_COMPARISON_V1_PREREG_20261004.md'
AN=ROOT/'evaluation/substrate_capability/analyze_boundary_probe_policy_comparison_v1.py'
POLICY=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
ULOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json';URAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UOUT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
FLOCK=ROOT/'evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json';FRAW=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json'
FOUT=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/boundary_probe_policy_comparison_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/boundary_probe_policy_comparison_v1_20261004.json'
KEYS=('ax','ay','ex','ey');TASKS=('additive','product');THRESHOLDS=(3.75,5.,8.);WIDE_SEED=418204;WIDE_PAIRS=1024
SOURCES=('docs/research/engine_substrate/BOUNDARY_PROBE_POLICY_COMPARISON_V1_PREREG_20261004.md','evaluation/substrate_capability/boundary_probe_policy_comparison_v1.py','evaluation/substrate_capability/analyze_boundary_probe_policy_comparison_v1.py','evaluation/substrate_capability/coverage_aware_class_return_v1.py','evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json','evaluation/reports/coverage_aware_class_return_v1_20261003.json','evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json','evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json','evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json','evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','domains/engine_provenance.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smap():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 b=Path(_native.__file__).resolve()
 return {'files':{x:sha(ROOT/x) for x in SOURCES},'binary':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def upstream():
 l=json.loads(ULOCK.read_text());r=json.loads(URAW.read_text());a=json.loads(UOUT.read_text());fl=json.loads(FLOCK.read_text());fr=json.loads(FRAW.read_text());fa=json.loads(FOUT.read_text())
 if not a.get('passed') or not fa.get('passed') or fa['summary'].get('false_safe_class_returns')!=5:raise RuntimeError('upstream evidence invalid')
 if r.get('lock_sha256')!=sha(ULOCK) or r.get('sources')!=l.get('sources') or a.get('capture_sha256')!=sha(URAW):raise RuntimeError('policy provenance mismatch')
 if fr.get('lock_sha256')!=sha(FLOCK) or fr.get('sources')!=fl.get('sources') or fa.get('capture_sha256')!=sha(FRAW):raise RuntimeError('false-control provenance mismatch')
 return [p for p in l['panels'] if p['task'] in TASKS]
def V(x):return {'type':'Var','name':x}
def plus(a,b):return {'type':'Plus','items':[a,b]}
def times(a,b):return {'type':'Times','items':[a,b]}
def eq(a,b):return {'type':'Eq','a':a,'b':b}
def make_terms(task,c):
 if task=='additive':
  a=eq(plus(V('ax'),V('ay')),plus(V('ex'),V('ey')));b=eq(plus(V('ay'),V('ax')),plus(V('ey'),V('ex')))
 else:
  a=eq(times(V('ax'),V('ay')),times(V('ex'),V('ey')));b=eq(times(V('ay'),V('ax')),times(V('ey'),V('ex')))
 lit={'type':'Lit','value':c};guard={'type':'And','items':[a,{'type':'Lt','a':V('ax'),'b':lit}]}
 return [{'id':task+'_direct','family':'authored_exact','term':a},{'id':task+'_commuted','family':'authored_exact','term':b},{'id':task+'_bounded','family':'near_equivalent','term':guard}]
def truth(task,row):
 a,b,c,d=row
 return a+b==c+d if task=='additive' else a*b==c*d
def instantiate(task,x):return {'ax':float(x),'ay':0. if task=='additive' else 1.,'ex':float(x),'ey':0. if task=='additive' else 1.}
def adapt_base(task,base):
 out=dict(base)
 for key in ('original_selection_pool','original_selection_order','original_challenge_order','zero_selection_pool','zero_selection_order','zero_challenge_pool','zero_challenge_order'):
  rows=[]
  for ax,ay,ex,ey in base[key]:
   ax,ay,ex,ey=map(float,(ax,ay,ex,ey))
   rows.append([ax,ay,ax+ay-ey,ey] if task=='additive' else [ax,ay,ax,ay])
  out[key]=rows
 return out
def loadpolicy():
 s=importlib.util.spec_from_file_location('coverage_aware_class_return_v1',POLICY);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
def worker(panel):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 m=loadpolicy();native=_native.Substrate();task=panel['task'];c=float(panel['threshold']);terms=panel['candidate_terms'];base=adapt_base(task,panel['base_panel']);old={**base,'initial_hypotheses':terms}
 current=m.run_policy(old)
 probes_directed=[instantiate(task,x) for x in (c-.5,c,c+.5)]
 probes_fixed=[instantiate(task,x) for x in range(-16,17,2)]
 def select_arm(probes):
  t=time.perf_counter_ns();choice=select_discriminating_input(lambda term,e:native.evaluate(term,e),terms,probes,[]);elapsed=time.perf_counter_ns()-t
  if not choice.get('ok'):return {'choice':choice,'selection_ns':elapsed,'survivors':[],'partition':None,'label':None}
  q=choice['query'];row=[float(q[k]) for k in KEYS];label=truth(task,tuple(row));survivors=[]
  for h in terms:
   try:v=native.evaluate(h['term'],q)
   except Exception:v=None
   if type(v)is bool and v is label:survivors.append(h)
  covered=base['original_selection_pool']+base['original_challenge_order']+base['zero_selection_pool']+base['zero_challenge_pool']+[row]
  part=partition_hypotheses_by_behavior(lambda term,e:native.evaluate(term,e),survivors,[m.env(x) for x in dict.fromkeys(tuple(z) for z in covered)])
  return {'choice':choice,'selection_ns':elapsed,'query_row':row,'label':label,'survivor_ids':[h['id'] for h in survivors],'partition':part,'candidate_evaluations':len(terms)*len(probes)}
 directed=select_arm(probes_directed);fixed=select_arm(probes_fixed)
 max_abs=max(abs(float(r[0])) for r in base['original_selection_pool']+base['original_challenge_order']+base['zero_selection_pool']+base['zero_challenge_pool'])
 abstain={'action':'abstain' if c>max_abs else 'insufficient_reason_to_abstain','reason':'threshold_outside_observed_ax_support','observed_abs_ax_max':max_abs}
 return {'task':task,'worker':panel['worker'],'threshold':c,'candidate_terms':terms,'arms':{'current':current,'directed':directed,'fixed':fixed,'abstain':abstain},
  'probe_counts':{'directed':len(probes_directed),'fixed':len(probes_fixed)},'wider_seed':WIDE_SEED,'wider_pairs':WIDE_PAIRS}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  ps=upstream();panels=[]
  for task in TASKS:
   for p in ps:
    if p['task']==task:
     for c in THRESHOLDS:panels.append({'task':task,'worker':p['worker'],'threshold':c,'base_panel':p,'candidate_terms':make_terms(task,c)})
  LOCK.write_text(json.dumps({'schema':'BoundaryProbePolicyComparisonV1Lock','sources':smap(),'upstream_lock_sha256':sha(ULOCK),'false_control_lock_sha256':sha(FLOCK),'panels':panels,'thresholds':THRESHOLDS,'fixed_grid':list(range(-16,17,2)),'wide_seed':WIDE_SEED,'wide_pairs':WIDE_PAIRS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text())
  expected=[]
  for task in TASKS:
   for p in upstream():
    if p['task']==task:
     for c in THRESHOLDS:expected.append({'task':task,'worker':p['worker'],'threshold':c,'base_panel':p,'candidate_terms':make_terms(task,c)})
  if smap()!=l['sources'] or expected!=l['panels']:raise SystemExit('source/panel drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i,p in enumerate(l['panels']):
   q=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
   if q.returncode:raise RuntimeError(q.stderr[-3000:])
   rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if smap()!=l['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'BoundaryProbePolicyComparisonV1Results','lock_sha256':sha(LOCK),'sources':smap(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':
  l=json.loads(LOCK.read_text());return_worker=worker(l['panels'][int(a[1])]);print(json.dumps(return_worker,sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
