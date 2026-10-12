#!/usr/bin/env python3
"""Independent analysis of warm converse caller/other-thread CPU split."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_caller_cpu_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_caller_cpu_v1_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py';ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_CALLER_CPU_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
POOL=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1.py';POOL_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1_lock_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py';BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=[['default',1],['one_thread',2],['one_thread',3],['default',4],['default',5],['one_thread',6]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=cap['rows']
    sources={'runner':sha(RUNNER),'analyzer':sha(ANALYZER),'protocol':sha(PROTOCOL),'pool_runner':sha(POOL),'pool_lock':sha(POOL_LOCK),'base_runner':sha(BASE),'base_lock_file':sha(BASE_LOCK)}
    active=lock['sources']['base_runtime_lock']['active']
    gates={
      'six_unique_fresh_processes':len(rows)==6 and len({r['worker']['pid'] for r in rows})==6,
      'source_stable':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after'],
      'worker_fingerprints_stable':all(r['worker']['active_after']==active for r in rows),
      'schedule_matches_lock':[[r['worker']['mode'],r['worker']['rep']] for r in rows]==SCHEDULE and lock['schedule']==SCHEDULE,
      'rayon_setting_observed':all(r['observed']['rayon_pool_threads']['after_target']==(1 if r['worker']['mode']=='one_thread' else 24) for r in rows),
      'task_semantics_and_refusal':all(r['worker']['shape_delta']==0 and r['worker']['state_before']==r['worker']['state_after'] and all(x['prediction']==x['expected'] for x in r['worker']['heldout']) for r in rows),
      'cpu_split_reconciles_within_10ms':all(abs((r['caller_cpu']['caller_thread_cpu_ns']+r['caller_cpu']['other_thread_aggregate_cpu_ns'])-r['worker']['timing_ns']['target_cpu'])<=10_000_000 for r in rows),
      'tooling_lock_matches':{k:lock['sources'][k] for k in sources}==sources and lock['sample_interval_ms']==5}
    summary={}
    for mode in ('default','one_thread'):
        rr=[r for r in rows if r['worker']['mode']==mode]
        med=lambda f:statistics.median(f(r) for r in rr)
        summary[mode]={'n':len(rr),'rayon_threads':sorted({r['observed']['rayon_pool_threads']['after_target'] for r in rr}),
          'median_target_wall_ms':med(lambda r:r['worker']['timing_ns']['target_wall']/1e6),
          'median_process_cpu_ms':med(lambda r:r['worker']['timing_ns']['target_cpu']/1e6),
          'median_caller_thread_cpu_ms':med(lambda r:r['caller_cpu']['caller_thread_cpu_ns']/1e6),
          'median_other_thread_aggregate_cpu_ms':med(lambda r:r['caller_cpu']['other_thread_aggregate_cpu_ns']/1e6),
          'median_other_thread_fraction':med(lambda r:r['caller_cpu']['other_thread_aggregate_cpu_ns']/max(1,r['worker']['timing_ns']['target_cpu'])),
          'median_peak_os_threads':med(lambda r:r['worker']['max_os_threads_sampled'])}
    result={'schema':'WarmConverseCallerCpuV1Analysis','gates':gates,'summary':summary,
      'interpretation':'Diagnostic only: caller CPU is separated; the residual aggregates all other threads and does not name a rule or pool.',
      'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
    if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
