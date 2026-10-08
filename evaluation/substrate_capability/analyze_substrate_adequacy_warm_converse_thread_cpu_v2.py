#!/usr/bin/env python3
"""Independent validation and summaries for external thread CPU samples."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v2_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v2_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v2.py'
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_CPU_V2_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v2_lock_20261002.json'
CALLER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
SCHEDULE=[['default',1],['one_thread',2],['one_thread',3],['default',4],['default',5],['one_thread',6]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=cap['rows']
 sources={'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'caller_runner':sha(CALLER),'caller_lock_file':sha(CALLER_LOCK)}
 gates={
  'six_unique_fresh_processes':len(rows)==6 and len({r['caller_worker']['worker']['pid'] for r in rows})==6,
  'source_stable':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after'],
  'schedule_matches_lock':[[r['mode'],r['rep']] for r in rows]==SCHEDULE and lock['schedule']==SCHEDULE,
  'rayon_size_matches_setting':all(r['caller_worker']['observed']['rayon_pool_threads']['after_target']==(1 if r['mode']=='one_thread' else 24) for r in rows),
  'semantic_refusal_and_oracle_controls':all(r['caller_worker']['worker']['shape_delta']==0 and r['caller_worker']['worker']['state_before']==r['caller_worker']['worker']['state_after'] and all(x['prediction']==x['expected'] for x in r['caller_worker']['worker']['heldout']) for r in rows),
  'parent_sample_minimum_and_unique_thread_keys':all(r['thread_cpu']['sample_count']>=20 and len({(t['tid'],t['starttime_ticks']) for t in r['thread_cpu']['threads']})==r['thread_cpu']['unique_thread_instances'] for r in rows),
  'finite_nonnegative_thread_runtime':all(t['sampled_runtime_delta_ns']>=0 for r in rows for t in r['thread_cpu']['threads']),
  'sampled_cpu_under_process_cpu_tolerance':all(r['thread_cpu']['sampled_thread_runtime_sum_ns']<=r['caller_worker']['worker']['timing_ns']['target_cpu']+100_000_000 for r in rows),
  'tooling_source_lock_matches':{k:lock['sources'][k] for k in sources}==sources and lock['sample_interval_ms']==2.0}
 summary={}
 for mode in ('default','one_thread'):
  rr=[r for r in rows if r['mode']==mode];med=lambda f:statistics.median(f(r) for r in rr)
  summary[mode]={'n':len(rr),'median_target_wall_ms':med(lambda r:r['caller_worker']['worker']['timing_ns']['target_wall']/1e6),
   'median_process_cpu_ms':med(lambda r:r['caller_worker']['worker']['timing_ns']['target_cpu']/1e6),
   'median_caller_cpu_ms':med(lambda r:r['caller_worker']['caller_cpu']['caller_thread_cpu_ns']/1e6),
   'median_parent_samples':med(lambda r:r['thread_cpu']['sample_count']),
   'median_thread_instances':med(lambda r:r['thread_cpu']['unique_thread_instances']),
   'median_sampled_thread_cpu_ms':med(lambda r:r['thread_cpu']['sampled_thread_runtime_sum_ns']/1e6),
   'median_sampled_cpu_fraction_of_process':med(lambda r:r['thread_cpu']['sampled_thread_runtime_sum_ns']/max(1,r['caller_worker']['worker']['timing_ns']['target_cpu'])),
   'top_thread_cpu_ms_by_worker':[[round(t['sampled_runtime_delta_ns']/1e6,2) for t in r['thread_cpu']['threads'][:10]] for r in rr]}
 result={'schema':'WarmConverseThreadCpuV2Analysis','gates':gates,'summary':summary,
  'interpretation':'External per-thread scheduler counters estimate sampled CPU by thread instance; they do not attribute operations or source call stacks.',
  'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
 if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
