#!/usr/bin/env python3
"""Independent gates and summaries for the per-thread CPU diagnostic."""
from __future__ import annotations
import hashlib, json, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v1_raw_20261002.json'
OUT = ROOT / 'evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v1_analysis_20261002.json'
RUNNER = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v1.py'
ANALYZER = Path(__file__).resolve()
PROTOCOL = ROOT / 'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_CPU_V1_PREREG_20261002.md'
LOCK = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v1_lock_20261002.json'
CALLER = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1.py'
CALLER_LOCK = ROOT / 'evaluation/substrate_capability/substrate_adequacy_warm_converse_caller_cpu_v1_lock_20261002.json'
SCHEDULE = [['default',1],['one_thread',2],['one_thread',3],['default',4],['default',5],['one_thread',6]]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cap = json.loads(RAW.read_text()); lock = json.loads(LOCK.read_text()); rows = cap['rows']
    sources = {'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
               'caller_runner':sha(CALLER),'caller_lock_file':sha(CALLER_LOCK)}
    worker = [r['caller_worker'] for r in rows]
    gates = {
        'six_unique_fresh_processes':len(rows)==6 and len({r['caller_worker']['worker']['pid'] for r in rows})==6,
        'source_stable':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after'],
        'schedule_matches_lock':[[r['mode'],r['rep']] for r in rows]==SCHEDULE and lock['schedule']==SCHEDULE,
        'rayon_settings_observed':all(r['observed']['rayon_pool_threads']['after_target']==(1 if row['mode']=='one_thread' else 24) for r,row in zip(worker,rows)),
        'semantics_and_refusal_preserved':all(row['worker']['shape_delta']==0 and row['worker']['state_before']==row['worker']['state_after'] and all(x['prediction']==x['expected'] for x in row['worker']['heldout']) for row in worker),
        'minimum_sampling_and_unique_thread_keys':all(r['thread_cpu']['sample_count']>=10 and len({(t['tid'],t['starttime_ticks']) for t in r['thread_cpu']['threads']})==r['thread_cpu']['unique_thread_instances'] for r in rows),
        'per_thread_deltas_finite_nonnegative':all(t['sampled_runtime_delta_ns']>=0 for r in rows for t in r['thread_cpu']['threads']),
        'sampled_cpu_within_aggregate_tolerance':all(r['thread_cpu']['sampled_thread_runtime_sum_ns']<=r['caller_worker']['worker']['timing_ns']['target_cpu']+100_000_000 for r in rows),
        'tooling_lock_matches':{k:lock['sources'][k] for k in sources}==sources and lock['sample_interval_ms']==2.0}
    summary={}
    for mode in ('default','one_thread'):
        rr=[r for r in rows if r['mode']==mode]
        median=lambda f:statistics.median(f(r) for r in rr)
        summaries=[sorted((t['sampled_runtime_delta_ns'] for t in r['thread_cpu']['threads']),reverse=True) for r in rr]
        summary[mode]={'n':len(rr),'median_samples':median(lambda r:r['thread_cpu']['sample_count']),
          'median_unique_thread_instances':median(lambda r:r['thread_cpu']['unique_thread_instances']),
          'median_sampled_thread_cpu_ms':median(lambda r:r['thread_cpu']['sampled_thread_runtime_sum_ns']/1e6),
          'median_process_cpu_ms':median(lambda r:r['caller_worker']['worker']['timing_ns']['target_cpu']/1e6),
          'median_caller_cpu_ms':median(lambda r:r['caller_worker']['caller_cpu']['caller_thread_cpu_ns']/1e6),
          'median_top_thread_cpu_ms':median(lambda r:(r['thread_cpu']['threads'][0]['sampled_runtime_delta_ns'] if r['thread_cpu']['threads'] else 0)/1e6),
          'top_threads_per_worker_ms':[[round(v/1e6,3) for v in s[:12]] for s in summaries]}
    result={'schema':'WarmConverseThreadCpuV1Analysis','gates':gates,'summary':summary,
      'interpretation':'Per-thread schedstat sampling estimates where CPU accrued; it does not identify stacks, operations, or subsystem ownership.',
      'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
    if not all(gates.values()): raise SystemExit(1)
if __name__=='__main__': main()
