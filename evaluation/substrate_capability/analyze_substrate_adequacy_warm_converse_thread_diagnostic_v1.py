#!/usr/bin/env python3
"""Independent analysis for warm converse thread-limit diagnostic v1."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_diagnostic_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_thread_diagnostic_v1_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_diagnostic_v1.py'
ANALYZER=Path(__file__).resolve()
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_diagnostic_v1_lock_20261002.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_DIAGNOSTIC_V1_PREREG_20261002.md'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());expected={'runner':sha(RUNNER),'analyzer':sha(ANALYZER),'protocol':sha(PROTOCOL),'base_runner':sha(ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'),'base_lock':sha(BASE),'parent_active':json.loads(BASE.read_text())['active']}
    rows=cap['rows'];gates={
      'six_rows_and_unique_pids':len(rows)==6 and len({r['pid'] for r in rows})==6,
      'locked_sources_stable':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after'],
      'expected_schedule':[(r['mode'],i) for i,r in enumerate(rows,1)]==[('default',1),('one_thread',2),('one_thread',3),('default',4),('default',5),('one_thread',6)],
      'worker_active_source_lock':all(r['active_after']==lock['sources']['parent_active'] for r in rows),
      'missing_evidence_refuses_without_shape_growth':all(r['condition']=='missing_evidence' and r['shape_delta']==0 and r['state_before']==r['state_after'] for r in rows),
      'heldout_native_matches_oracle':all(x['prediction']==x['expected'] for r in rows for x in r['heldout']),
      'finite_timings_and_thread_counts':all(r['timing_ns']['target_wall']>0 and r['timing_ns']['target_cpu']>=0 and r['max_os_threads_observed']>0 for r in rows),
      'capture_tooling_lock_matches':lock['sources']==expected and lock['schedule']==[['default',1],['one_thread',2],['one_thread',3],['default',4],['default',5],['one_thread',6]] and lock['sample_interval_ms']==5}
    summary={}
    for mode in ('default','one_thread'):
        rr=[r for r in rows if r['mode']==mode]
        vals=lambda f:[f(r) for r in rr]
        summary[mode]={'n':len(rr),'median_target_wall_ms':statistics.median(vals(lambda r:r['timing_ns']['target_wall']/1e6)),
          'range_target_wall_ms':[min(vals(lambda r:r['timing_ns']['target_wall']/1e6)),max(vals(lambda r:r['timing_ns']['target_wall']/1e6))],
          'median_target_process_cpu_ms':statistics.median(vals(lambda r:r['timing_ns']['target_cpu']/1e6)),
          'range_target_process_cpu_ms':[min(vals(lambda r:r['timing_ns']['target_cpu']/1e6)),max(vals(lambda r:r['timing_ns']['target_cpu']/1e6))],
          'median_cpu_wall_ratio':statistics.median(vals(lambda r:r['timing_ns']['target_cpu']/r['timing_ns']['target_wall'])),
          'median_max_os_threads_observed':statistics.median(vals(lambda r:r['max_os_threads_observed']))}
    result={'schema':'WarmConverseThreadDiagnosticV1Analysis','gates':gates,'summary':summary,
      'interpretation':'Diagnostic only: process CPU is aggregate; sampled OS-thread count does not attribute per-thread work.',
      'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
    if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
