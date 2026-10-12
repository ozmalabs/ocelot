#!/usr/bin/env python3
"""Independent analysis of Rayon pool and process-thread diagnostic v1."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_rayon_pool_v1_raw_20261002.json'
OUT=ROOT/'evaluation/reports/substrate_adequacy_warm_converse_rayon_pool_v1_analysis_20261002.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1.py'
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_ADEQUACY_WARM_CONVERSE_RAYON_POOL_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1_lock_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/substrate_adequacy_warm_converse_cost_v1_lock_20261002.json'
SCHEDULE=[['default',1],['one_thread',2],['one_thread',3],['default',4],['default',5],['one_thread',6]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cap=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=cap['rows']
    expected={'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
      'base_runner':sha(BASE),'base_lock_file':sha(BASE_LOCK)}
    active=lock['sources']['base_runtime_lock']['active']
    gates={
      'six_unique_fresh_processes':len(rows)==6 and len({r['worker']['pid'] for r in rows})==6,
      'source_lock_stable':cap['source_stable'] and cap['source_before']==lock['sources']==cap['source_after'],
      'runtime_sources_stable':all(r['worker']['active_after']==active for r in rows),
      'schedule_matches_preregistration':[[r['worker']['mode'],r['worker']['rep']] for r in rows]==SCHEDULE,
      'pool_setting_observed':all(r['observed']['rayon_pool_threads'].get('after_warm')==(1 if r['worker']['mode']=='one_thread' else 24) and r['observed']['rayon_pool_threads'].get('after_target')==(1 if r['worker']['mode']=='one_thread' else 24) for r in rows),
      'thread_observations_complete':all(r['worker']['max_os_threads_sampled']>0 and all(v>0 for v in r['observed']['phase_os_threads'].values()) for r in rows),
      'missing_evidence_no_codebook_growth':all(r['worker']['condition']=='missing_evidence' and r['worker']['shape_delta']==0 and r['worker']['state_before']==r['worker']['state_after'] for r in rows),
      'heldouts_match_oracle':all(x['prediction']==x['expected'] for r in rows for x in r['worker']['heldout']),
      'tooling_lock_matches':{k:lock['sources'][k] for k in expected}==expected and lock['schedule']==SCHEDULE and lock['sample_interval_ms']==5}
    summary={}
    for mode in ('default','one_thread'):
        rr=[r for r in rows if r['worker']['mode']==mode]
        med=lambda fn:statistics.median(fn(r) for r in rr)
        summary[mode]={'n':len(rr),'rayon_pool_threads':sorted(set(r['observed']['rayon_pool_threads']['after_target'] for r in rr)),
          'median_os_threads_by_phase':{phase:med(lambda r:r['observed']['phase_os_threads'][phase]) for phase in rr[0]['observed']['phase_os_threads']},
          'median_peak_os_threads_sampled':med(lambda r:r['worker']['max_os_threads_sampled']),
          'median_target_wall_ms':med(lambda r:r['worker']['timing_ns']['target_wall']/1e6),
          'median_target_process_cpu_ms':med(lambda r:r['worker']['timing_ns']['target_cpu']/1e6),
          'median_cpu_wall_ratio':med(lambda r:r['worker']['timing_ns']['target_cpu']/r['worker']['timing_ns']['target_wall'])}
    result={'schema':'WarmConverseRayonPoolV1Analysis','gates':gates,'summary':summary,
      'interpretation':'Diagnostic only: pool size is known, but process-thread ownership and per-thread CPU are not measured.',
      'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK)}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True))
    if not all(gates.values()):raise SystemExit(1)
if __name__=='__main__':main()
