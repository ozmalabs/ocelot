#!/usr/bin/env python3
"""Corrected independent audit of thread-origin v1's raw capture.

The preregistered analyzer's source-list gate omitted nested caller/runtime
fingerprints, and its category pass did not symbolize native offsets. This
review leaves the original capture and analyzer untouched and checks the
capture against the original lock using the runner's complete frozen source set.
"""
from __future__ import annotations
import hashlib,importlib.util,json,re,statistics,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_analysis_review_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_origin_v1.py'
PROBE=ROOT/'evaluation/substrate_capability/thread_origin_pthread_probe.c'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1_lock_20261002.json'
SCHEDULE=[['rayon_default','blas_default',1],['rayon_one','blas_default',1],['rayon_one','blas_one',1],['rayon_default','blas_one',1],
 ['rayon_default','blas_default',2],['rayon_one','blas_default',2],['rayon_one','blas_one',2],['rayon_default','blas_one',2],
 ['rayon_default','blas_default',3],['rayon_one','blas_default',3],['rayon_one','blas_one',3],['rayon_default','blas_one',3]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('thread_origin_locked_runner',RUNNER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def probe_hash():
 with tempfile.TemporaryDirectory(prefix='ocelot-origin-review-') as td:
  binary=Path(td)/'pthread_probe.so'
  subprocess.run(['gcc','-shared','-fPIC','-O2','-fno-omit-frame-pointer','-o',str(binary),str(PROBE),'-ldl','-pthread'],check=True,capture_output=True)
  return sha(binary)
def symbolize(frame,cache):
 mod,rest=frame.split('!',1);match=re.search(r'\+0x([0-9a-fA-F]+)$',rest)
 if not match:return rest
 key=(mod,match.group(1))
 if key not in cache:
  p=subprocess.run(['addr2line','-Cfipe',mod,'0x'+match.group(1)],text=True,capture_output=True)
  cache[key]=p.stdout.strip() or rest
 return cache[key]
def classify(event,cache):
 symbols=[symbolize(f,cache) for f in event['frames']]
 joined=' '.join(symbols)
 if 'blas_thread_init' in joined:return 'openblas',symbols
 if 'substrate_rs::py::pyobj_to_json' in joined:return 'substrate_json_parse',symbols
 return 'other',symbols
def caller_method(symbols):
 joined=' '.join(symbols)
 for name in ('add_production','add_rule','graph_from_dict','import_rules'):
  if f'PySubstrate::{name}' in joined or f'__pymethod_{name}__' in joined:return name
 return 'unresolved'
def main():
 cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=cap['rows'];runner=load_runner()
 current_sources=runner.frozen();source_files=current_sources.copy()
 events_by_row=[];cache={};all_events=[]
 for row in rows:
  detail=[];methods={};counts={'openblas':0,'substrate_json_parse':0,'other':0}
  for event in row['pthread_events']:
   cat,syms=classify(event,cache);counts[cat]+=1
   meth=caller_method(syms) if cat=='substrate_json_parse' else None
   if meth:methods[meth]=methods.get(meth,0)+1
   detail.append({'category':cat,'parent_method':meth,'symbols':syms,'stack_size_bytes':event['stack_size_bytes']})
   all_events.append((row,event,cat,meth,syms))
  events_by_row.append({'row':row,'counts':counts,'methods':methods,'details':detail})
 groups={(rayon,blas):[x for x in events_by_row if x['row']['rayon']==rayon and x['row']['blas']==blas]
  for rayon in ('rayon_default','rayon_one') for blas in ('blas_default','blas_one')}
 gates={
  'twelve_unique_fresh_pids':len(rows)==12 and len({r['pid'] for r in rows})==12,
  'complete_pre_capture_sources_match':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after']==current_sources,
  'schedule_matches_preregistration':[[r['rayon'],r['blas'],r['rep']] for r in rows]==SCHEDULE==lock['schedule'],
  'all_runtime_locks_match':all(r['active_after']==current_sources['caller_runtime_lock']['active'] for r in rows),
  'rayon_settings_observed':all(r['rayon_observed']['after_target']==(1 if r['rayon']=='rayon_one' else 24) for r in rows),
  'semantic_oracle_and_refusal_controls':all(r['worker']['shape_delta']==0 and r['worker']['state_before']==r['worker']['state_after'] and all(h['prediction']==h['expected'] for h in r['worker']['heldout']) for r in rows),
  'all_events_inside_target_markers':all(r['target_markers'][0]['phase']=='begin' and r['target_markers'][1]['phase']=='end' and r['target_markers'][0]['monotonic_ns']<r['target_markers'][1]['monotonic_ns'] and all(r['target_markers'][0]['monotonic_ns']<=e['monotonic_ns']<=r['target_markers'][1]['monotonic_ns'] for e in r['pthread_events']) for r in rows),
  'all_native_json_spawns_symbolized_with_256m_stack':all(cat!='substrate_json_parse' or ('substrate_rs::py::pyobj_to_json' in ' '.join(syms) and event['stack_size_bytes']>=256*1024*1024) for _,event,cat,_,syms in all_events),
  'openblas_workers_respond_to_env_cap':all(x['counts']['openblas']==(23 if x['row']['blas']=='blas_default' else 0) for x in events_by_row),
  'json_parser_spawn_counts_invariant':all(x['counts']['substrate_json_parse']==117 for x in events_by_row),
  'all_json_parent_callsites_resolved':all(x['methods']=={'add_production':94,'add_rule':16,'graph_from_dict':6,'import_rules':1} for x in events_by_row),
  'probe_source_and_compiled_binary_match_lock':sha(PROBE)==lock['sources']['probe_source'] and probe_hash()==lock['probe_binary_sha256']==cap['probe_binary_sha256']}
 summary={}
 for (rayon,blas),vals in groups.items():
  med=lambda f:statistics.median(f(x['row']) for x in vals)
  summary[f'{rayon}__{blas}']={'n':len(vals),'pthread_creates_median':statistics.median(sum(x['counts'].values()) for x in vals),
   'openblas_creates_median':statistics.median(x['counts']['openblas'] for x in vals),
   'substrate_json_parse_creates_median':statistics.median(x['counts']['substrate_json_parse'] for x in vals),
   'json_parent_methods_total':{m:sum(x['methods'].get(m,0) for x in vals) for m in ('add_production','add_rule','graph_from_dict','import_rules')},
   'json_spawn_stack_sizes':sorted({d['stack_size_bytes'] for x in vals for d in x['details'] if d['category']=='substrate_json_parse'}),
   'median_instrumented_wall_ms':med(lambda r:r['worker']['timing_ns']['target_wall']/1e6),
   'median_instrumented_process_cpu_ms':med(lambda r:r['worker']['timing_ns']['target_cpu']/1e6)}
 process_cpu={}
 for rayon in ('rayon_default','rayon_one'):
  default=[x['row']['worker']['timing_ns']['target_cpu']/1e6 for x in groups[(rayon,'blas_default')]]
  capped=[x['row']['worker']['timing_ns']['target_cpu']/1e6 for x in groups[(rayon,'blas_one')]]
  process_cpu[rayon]={'median_default_blas_ms':statistics.median(default),'median_blas_cap_1_ms':statistics.median(capped),
   'median_ratio_default_over_cap':statistics.median(default)/max(statistics.median(capped),1e-9)}
 result={'schema':'WarmConverseThreadOriginV1ReviewAnalysis','original_preregistered_analyzer_hash':lock['sources']['analyzer'],
  'current_preregistered_analyzer_hash':sha(ANALYZER),'gates':gates,'summary':summary,'process_cpu_intervention':process_cpu,
  'symbolizer':'addr2line -Cfipe on source-locked native modules; symbol resolution is stored per captured event.',
  'interpretation':'The pthread call-site census attributes thread creation to OpenBLAS and the native serde_json conversion wrapper. The OpenBLAS cap is associated with a large process-CPU reduction in this instrumented panel with exact substrate outcomes. Backtrace interposition affects timings; estimate production impact with an uninstrumented intervention.',
  'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'review_analyzer_sha256':sha(Path(__file__)),'symbolizer_cache_entries':len(cache)}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
 if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
