#!/usr/bin/env python3
"""Independent validation and call-site grouping for pthread-origin capture."""
from __future__ import annotations
import hashlib,json,statistics,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1.py'
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_ORIGIN_V1_PREREG_20261002.md'
PROBE=ROOT/'evaluation/substrate_capability/thread_origin_pthread_probe.c'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1_lock_20261002.json'
CALLER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=[['rayon_default','blas_default',1],['rayon_one','blas_default',1],['rayon_one','blas_one',1],['rayon_default','blas_one',1],
 ['rayon_default','blas_default',2],['rayon_one','blas_default',2],['rayon_one','blas_one',2],['rayon_default','blas_one',2],
 ['rayon_default','blas_default',3],['rayon_one','blas_default',3],['rayon_one','blas_one',3],['rayon_default','blas_one',3]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compiler():return subprocess.run(['gcc','--version'],text=True,capture_output=True,check=True).stdout.splitlines()[0]
def compile_probe_hash():
 with tempfile.TemporaryDirectory(prefix='ocelot-probe-analysis-') as td:
  binary=Path(td)/'pthread_probe.so'
  subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-omit-frame-pointer','-o',str(binary),str(PROBE),'-ldl','-pthread'],check=True,capture_output=True)
  return sha(binary)
def sources():
 return {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'probe_source':sha(PROBE),
  'caller_runner':sha(CALLER),'caller_lock_file':sha(CALLER_LOCK),'base_runner':sha(BASE),'base_lock_file':sha(BASE_LOCK),'compiler':compiler()}
def category(event):
 frames=event['frames'];
 if any('libscipy_openblas' in f or 'blas_thread_init' in f for f in frames):return 'openblas'
 if any('substrate_rs::py::pyobj_to_json' in f for f in frames):return 'substrate_json_parse'
 return 'other'
def parent_method(event):
 for frame in event['frames']:
  for name in ('add_production','add_rule','graph_from_dict','import_rules'):
   if f'PySubstrate::{name}' in frame:return name
 return 'unresolved'
def main():
 cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=cap['rows']
 grouped={(r,b):[x for x in rows if x['rayon']==r and x['blas']==b] for r in ('rayon_default','rayon_one') for b in ('blas_default','blas_one')}
 cats={};methods={}
 for row in rows:
  cc={k:0 for k in ('openblas','substrate_json_parse','other')};mm={}
  for ev in row['pthread_events']:
   cc[category(ev)]+=1
   if category(ev)=='substrate_json_parse':mm[parent_method(ev)]=mm.get(parent_method(ev),0)+1
  cats[(row['rayon'],row['blas'],row['rep'])]=cc;methods[(row['rayon'],row['blas'],row['rep'])]=mm
 lock_sources=lock['sources']
 gates={
  'twelve_unique_fresh_processes':len(rows)==12 and len({r['pid'] for r in rows})==12,
  'source_and_runtime_fingerprints_stable':cap['source_stable'] and cap['source_before']==lock_sources and cap['source_after']==lock_sources and all(r['active_after']==lock_sources['caller_runtime_lock']['active'] for r in rows),
  'schedule_matches_lock':[[r['rayon'],r['blas'],r['rep']] for r in rows]==SCHEDULE and lock['schedule']==SCHEDULE,
  'rayon_setting_observed':all(r['rayon_observed']['after_target']==(1 if r['rayon']=='rayon_one' else 24) for r in rows),
  'task_semantics_and_refusal':all(r['worker']['shape_delta']==0 and r['worker']['state_before']==r['worker']['state_after'] and all(h['prediction']==h['expected'] for h in r['worker']['heldout']) for r in rows),
  'target_markers_and_event_timestamps_valid':all([m['phase'] for m in r['target_markers']]==['begin','end'] and all(r['target_markers'][0]['monotonic_ns']<=e['monotonic_ns']<=r['target_markers'][1]['monotonic_ns'] for e in r['pthread_events']) for r in rows),
  'successful_thread_creation_records_well_formed':all(e['pthread_handle'] and e['stack_size_bytes']>=0 and len(e['frames'])>=2 for r in rows for e in r['pthread_events']),
  'json_threads_use_large_stack_guard':all(e['stack_size_bytes']>=256*1024*1024 for r in rows for e in r['pthread_events'] if category(e)=='substrate_json_parse'),
  'openblas_setting_intervention_matches':all((cats[(r['rayon'],r['blas'],r['rep'])]['openblas']>0)==(r['blas']=='blas_default') for r in rows),
  'tooling_and_probe_binary_hash_match':sources()==lock_sources and lock['probe_binary_sha256']==cap['probe_binary_sha256']==compile_probe_hash()}
 summary={}
 for key,rr in grouped.items():
  med=lambda f:statistics.median(f(r) for r in rr)
  cc=[cats[(r['rayon'],r['blas'],r['rep'])] for r in rr]
  method_totals={}
  for r in rr:
   for method,n in methods[(r['rayon'],r['blas'],r['rep'])].items():method_totals[method]=method_totals.get(method,0)+n
  name=f'{key[0]}__{key[1]}'
  summary[name]={'n':len(rr),'median_wall_ms_instrumented':med(lambda r:r['worker']['timing_ns']['target_wall']/1e6),
   'median_process_cpu_ms_instrumented':med(lambda r:r['worker']['timing_ns']['target_cpu']/1e6),
   'median_total_pthread_creates':med(lambda r:r['pthread_event_count']),
   'median_openblas_creates':statistics.median(x['openblas'] for x in cc),
   'median_substrate_json_parse_creates':statistics.median(x['substrate_json_parse'] for x in cc),
   'median_other_creates':statistics.median(x['other'] for x in cc),'json_parse_caller_methods_total':method_totals,
   'stack_bytes_by_category':{'openblas':sorted({e['stack_size_bytes'] for r in rr for e in r['pthread_events'] if category(e)=='openblas'}),
    'substrate_json_parse':sorted({e['stack_size_bytes'] for r in rr for e in r['pthread_events'] if category(e)=='substrate_json_parse'})}}
 result={'schema':'WarmConverseThreadOriginV1Analysis','gates':gates,'summary':summary,
  'source_files':sources(),'interpretation':'Thread creation call sites are identified; these counts do not measure each worker\'s later CPU or establish production performance.',
  'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
 if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
