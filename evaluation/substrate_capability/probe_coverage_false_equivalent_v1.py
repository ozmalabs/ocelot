#!/usr/bin/env python3
"""Falsify finite coverage with a candidate that diverges beyond its range."""
import hashlib,json,os,platform,subprocess,sys,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/PROBE_COVERAGE_FALSE_EQUIVALENT_V1_PREREG_20261004.md'
AN=ROOT/'evaluation/substrate_capability/analyze_probe_coverage_false_equivalent_v1.py'
COV=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
ULOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
URAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UAN=ROOT/'evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py'
UOUT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
DIST=ROOT/'evaluation/substrate_capability/distinct_term_equivalence_class_v1.py'
DISTLOCK=ROOT/'evaluation/substrate_capability/distinct_term_equivalence_class_v1_lock_20261004.json'
DISTRAW=ROOT/'evaluation/reports/distinct_term_equivalence_class_v1_20261004.json'
DISTAN=ROOT/'evaluation/substrate_capability/analyze_distinct_term_equivalence_class_v1.py'
DISTOUT=ROOT/'evaluation/reports/distinct_term_equivalence_class_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json'
V=lambda x:{'type':'Var','name':x};L=lambda x:{'type':'Lit','value':x}
BASE={'type':'Eq','a':V('ax'),'b':{'type':'Neg','arg':V('ex')}}
SWAPPED={'type':'Eq','a':{'type':'Neg','arg':V('ax')},'b':V('ex')}
RESTRICTED={'type':'And','items':[BASE,{'type':'Lt','a':V('ax'),'b':L(4)}]}
TERMS=[{'id':'opposition_direct','family':'authored_exact','term':BASE},
 {'id':'opposition_swapped_negation','family':'authored_exact','term':SWAPPED},
 {'id':'opposition_bounded_x_lt_4','family':'near_equivalent_control','term':RESTRICTED}]
SOURCES=('docs/research/engine_substrate/PROBE_COVERAGE_FALSE_EQUIVALENT_V1_PREREG_20261004.md',
 'evaluation/substrate_capability/probe_coverage_false_equivalent_v1.py','evaluation/substrate_capability/analyze_probe_coverage_false_equivalent_v1.py',
 'evaluation/substrate_capability/coverage_aware_class_return_v1.py','evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json',
 'evaluation/reports/coverage_aware_class_return_v1_20261003.json','evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py',
 'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json',
 'evaluation/substrate_capability/distinct_term_equivalence_class_v1.py','evaluation/substrate_capability/distinct_term_equivalence_class_v1_lock_20261004.json',
 'evaluation/reports/distinct_term_equivalence_class_v1_20261004.json','evaluation/substrate_capability/analyze_distinct_term_equivalence_class_v1.py',
 'evaluation/reports/distinct_term_equivalence_class_v1_analysis_20261004.json','runners/dsl/python/substrate_rs/__init__.py',
 'runners/dsl/python/substrate_rs/_native.build.json','domains/engine_provenance.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 b=Path(_native.__file__).resolve()
 return {'files':{x:sha(ROOT/x) for x in SOURCES},'binary':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def upstream():
 l=json.loads(ULOCK.read_text());r=json.loads(URAW.read_text());a=json.loads(UOUT.read_text())
 if not a.get('passed') or a.get('errors') or r.get('lock_sha256')!=sha(ULOCK) or r.get('sources')!=l.get('sources') or a.get('capture_sha256')!=sha(URAW):raise RuntimeError('coverage-policy source evidence invalid')
 return [p for p in l['panels'] if p['task']=='opposition']
def load_policy():
 s=importlib.util.spec_from_file_location('coverage_aware_class_return_v1',COV);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
def worker(i):
 p=upstream()[i];result=load_policy().run_policy({**p,'initial_hypotheses':TERMS})
 return {'task':p['task'],'worker':p['worker'],'candidate_terms':TERMS,'result':result}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  panels=upstream();LOCK.write_text(json.dumps({'schema':'ProbeCoverageFalseEquivalentV1Lock','sources':source_map(),'upstream_lock_sha256':sha(ULOCK),'upstream_capture_sha256':sha(URAW),'panels':panels,'candidate_terms':TERMS,'wide_seed':418204,'balanced_pairs':1500},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources'] or upstream()!=l['panels']:raise SystemExit('source or panel drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i in range(len(l['panels'])):
   q=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
   if q.returncode:raise RuntimeError(q.stderr[-2500:])
   rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'ProbeCoverageFalseEquivalentV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
