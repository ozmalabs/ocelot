#!/usr/bin/env python3
"""Independent validation and summary of the uninstrumented BLAS panel."""
from __future__ import annotations
import hashlib,importlib.util,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_openblas_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_openblas_v1_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_openblas_v1.py'
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_OPENBLAS_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_openblas_v1_lock_20261002.json'
SCHEDULE=[['unset',1],['one_thread',2],['one_thread',3],['unset',4],['unset',5],['one_thread',6]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_runner():
 spec=importlib.util.spec_from_file_location('openblas_locked_runner',RUNNER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=cap['rows'];sources=load_runner().frozen()
 gates={
  'six_unique_fresh_processes':len(rows)==6 and len({r['worker']['pid'] for r in rows})==6,
  'complete_source_and_runtime_locks_match':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after']==sources,
  'interleaved_schedule_matches_lock':[[r['worker']['mode'],r['worker']['rep']] for r in rows]==SCHEDULE and lock['schedule']==SCHEDULE,
  'no_rayon_override_and_pool_is_default':all(r['observed']['rayon_pool_threads']['after_target']==24 for r in rows) and lock['environment_baseline']['RAYON_NUM_THREADS'] is None,
  'only_blas_setting_varies':lock['environment_baseline']['OPENBLAS_NUM_THREADS'] is None and lock['environment_baseline']['LD_PRELOAD'] is None,
  'exact_task_semantics_and_refusal':all(r['worker']['shape_delta']==0 and r['worker']['state_before']==r['worker']['state_after'] and all(h['prediction']==h['expected'] for h in r['worker']['heldout']) for r in rows),
  'cpu_split_reconciles_within_10ms':all(abs(r['worker']['timing_ns']['target_cpu']-r['caller_cpu']['caller_thread_cpu_ns']-r['caller_cpu']['other_thread_aggregate_cpu_ns'])<=10_000_000 for r in rows),
  'finite_positive_measurements':all(r['worker']['timing_ns']['target_wall']>0 and r['worker']['timing_ns']['target_cpu']>0 and r['caller_cpu']['caller_thread_cpu_ns']>=0 for r in rows),
  'analysis_tools_match_lock':{'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER)}=={k:lock['sources'][k] for k in ('runner','protocol','analyzer')}}
 summary={}
 for mode in ('unset','one_thread'):
  rr=[r for r in rows if r['worker']['mode']==mode];med=lambda f:statistics.median(f(r) for r in rr)
  cpu=[r['worker']['timing_ns']['target_cpu']/1e6 for r in rr];wall=[r['worker']['timing_ns']['target_wall']/1e6 for r in rr]
  caller=[r['caller_cpu']['caller_thread_cpu_ns']/1e6 for r in rr];other=[r['caller_cpu']['other_thread_aggregate_cpu_ns']/1e6 for r in rr]
  summary[mode]={'n':len(rr),'median_target_wall_ms':statistics.median(wall),'range_target_wall_ms':[min(wall),max(wall)],
   'median_process_cpu_ms':statistics.median(cpu),'range_process_cpu_ms':[min(cpu),max(cpu)],
   'median_caller_cpu_ms':statistics.median(caller),'median_other_thread_cpu_ms':statistics.median(other),
   'median_other_thread_share':statistics.median(o/max(1,c0) for o,c0 in zip(other,cpu)),
   'median_process_cpu_over_wall':statistics.median(c0/max(1,w0) for c0,w0 in zip(cpu,wall))}
 ratio=summary['unset']['median_process_cpu_ms']/max(summary['one_thread']['median_process_cpu_ms'],1e-9)
 result={'schema':'WarmConverseOpenblasV1Analysis','gates':gates,'summary':summary,
  'median_process_cpu_reduction_ratio_unset_over_one_thread':ratio,
  'interpretation':'Uninstrumented process-CPU response to OPENBLAS_NUM_THREADS=1 under one source-locked authored route; one host and three samples per arm.',
  'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
 if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
