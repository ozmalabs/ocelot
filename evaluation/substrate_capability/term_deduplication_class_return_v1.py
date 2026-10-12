#!/usr/bin/env python3
"""Rerun frozen coverage-aware panels after exact Term-JSON deduplication."""
import hashlib,json,os,platform,subprocess,sys,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_DEDUPLICATION_CLASS_RETURN_V1_PREREG_20261004.md'
AN=ROOT/'evaluation/substrate_capability/analyze_term_deduplication_class_return_v1.py'
COV=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UPAN=ROOT/'evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py'
UPREPORT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
OUTLOCK=ROOT/'evaluation/substrate_capability/term_deduplication_class_return_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/term_deduplication_class_return_v1_20261004.json'
SOURCES=('docs/research/engine_substrate/TERM_DEDUPLICATION_CLASS_RETURN_V1_PREREG_20261004.md',
 'evaluation/substrate_capability/term_deduplication_class_return_v1.py','evaluation/substrate_capability/analyze_term_deduplication_class_return_v1.py',
 'evaluation/substrate_capability/coverage_aware_class_return_v1.py','evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json',
 'evaluation/reports/coverage_aware_class_return_v1_20261003.json','evaluation/substrate_capability/analyze_coverage_aware_class_return_v1_1.py',
 'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json','runners/dsl/python/substrate_rs/__init__.py',
 'runners/dsl/python/substrate_rs/_native.build.json','domains/engine_provenance.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 b=Path(_native.__file__).resolve()
 return {'files':{x:sha(ROOT/x) for x in SOURCES},'binary':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def upstream():
 l=json.loads(LOCK.read_text());r=json.loads(RAW.read_text());a=json.loads(UPREPORT.read_text())
 if not a.get('passed') or a.get('errors') or r.get('lock_sha256')!=sha(LOCK) or r.get('sources')!=l.get('sources') or a.get('capture_sha256')!=sha(RAW):raise RuntimeError('upstream capture/analyzer invalid')
 return l,r,a
def canonical(term):return json.dumps(term,sort_keys=True,separators=(',',':'))
def load_cov():
 spec=importlib.util.spec_from_file_location('coverage_aware_class_return_v1',COV);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def worker(i):
 l,_,_=upstream();p=l['panels'][i];cov=load_cov();seen=set();unique=[]
 for h in p['initial_hypotheses']:
  k=canonical(h['term'])
  if k not in seen:seen.add(k);unique.append(h)
 result=cov.run_policy({**p,'initial_hypotheses':unique})
 return {'task':p['task'],'worker':p['worker'],'initial_count':len(p['initial_hypotheses']),'unique_term_count':len(unique),
  'removed_duplicates':len(p['initial_hypotheses'])-len(unique),'unique_hypotheses':unique,'result':result}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if OUTLOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  l,_,_=upstream();OUTLOCK.write_text(json.dumps({'schema':'TermDeduplicationClassReturnV1Lock','sources':source_map(),'upstream_lock_sha256':sha(LOCK),'upstream_capture_sha256':sha(RAW),'panels':[{'task':p['task'],'worker':p['worker'],'initial_hypotheses':p['initial_hypotheses']} for p in l['panels']]},indent=2,sort_keys=True)+'\n');print(OUTLOCK.relative_to(ROOT));return 0
 if args==['--run']:
  l=json.loads(OUTLOCK.read_text())
  if source_map()!=l['sources'] or l['upstream_lock_sha256']!=sha(LOCK) or l['upstream_capture_sha256']!=sha(RAW):raise SystemExit('source drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i,_ in enumerate(l['panels']):
   proc=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if proc.returncode:raise RuntimeError(proc.stderr[-2500:])
   rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'TermDeduplicationClassReturnV1Results','lock_sha256':sha(OUTLOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
