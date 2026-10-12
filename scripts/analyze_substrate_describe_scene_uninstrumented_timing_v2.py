#!/usr/bin/env python3
"""Recompute integrity gates and robust descriptive summaries for timing v2."""
import json, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/describe_scene_uninstrumented_timing_v2_20260927.json'
OUT=ROOT/'evaluation/reports/describe_scene_uninstrumented_timing_v2_analysis_20260927.json'
d=json.loads(RAW.read_text());runs=d['runs'];locked=d['locked_inputs']
expected='I see the grey thing stays, the yellow counter, and the blue thing moves.'
checks={
 'five_distinct_workers':len(runs)==5 and len({r['pid'] for r in runs})==5,
 'source_and_native_lock_stable':d['post_run_inputs']==locked and all(r['locked_inputs']==locked==r['post_run_inputs'] for r in runs),
 'workers_joined_without_errors':all(r['threads_joined'] and not r['thread_errors'] for r in runs),
 'two_expected_calls_per_worker':all(r['request_count']==2 and set(r['replies'])=={'A','B'} and all(x==expected for x in r['replies'].values()) for r in runs),
 'request_goals_resolved':all(len(r['requests'])==2 and all(q['goal_count']==1 and q['statuses']==['resolved'] and q['events']==['selection','execution','action_result'] and q['public_reply']==expected for q in r['requests']) for r in runs),
}
def stats(vals):
 return {'median':statistics.median(vals),'min':min(vals),'max':max(vals),'replicates':vals}
summaries={}
for who in ('A','B'):
 summaries[who]={'wall_ms':stats([r['thread_timings'][who]['wall_ns']/1e6 for r in runs]),'thread_cpu_ms':stats([r['thread_timings'][who]['thread_cpu_ns']/1e6 for r in runs])}
for field in ('boot_wall_ns','boot_process_cpu_ns','peak_rss_bytes'):
 summaries[field]=stats([r[field] for r in runs])
summaries['boot_phase_high_water_rss_bytes']=stats([r['boot_phase_high_water_rss_bytes'] for r in runs])
paired_wall=sorted([max(r['thread_timings'][x]['wall_ns'] for x in ('A','B')) for r in runs])
paired_cpu=sorted([sum(r['thread_timings'][x]['thread_cpu_ns'] for x in ('A','B')) for r in runs])
high_cpu=sorted([max(r['thread_timings'][x]['thread_cpu_ns'] for x in ('A','B')) for r in runs])
low_cpu=sorted([min(r['thread_timings'][x]['thread_cpu_ns'] for x in ('A','B')) for r in runs])
summaries['two_call_schedule']={
 'max_caller_wall_ms':stats([x/1e6 for x in paired_wall]),
 'combined_thread_cpu_ms':stats([x/1e6 for x in paired_cpu]),
 'higher_cpu_thread_ms':stats([x/1e6 for x in high_cpu]),
 'lower_cpu_thread_ms':stats([x/1e6 for x in low_cpu]),
 'note':'Which label (A/B) receives the high-CPU request varies by replicate; report role-sorted values for workload behavior, not fixed-label medians.'}
out={'schema_version':1,'run_id':'describe-scene-uninstrumented-timing-v2-analysis-20260927','source_raw':str(RAW.relative_to(ROOT)),'checks':checks,'all_checks_pass':all(checks.values()),'classification':'valid_five_process_fixture_measurement' if all(checks.values()) else 'censored_or_integrity_failure','summaries':summaries,'interpretation':'Caller wall and thread CPU values are measured during two simultaneously launched calls against one adapter. They include scheduling/serialization effects and must not be read as isolated single-request service time. Five replicates quantify this fixture and schedule only.','instrumentation':'No native access tracing, per-rule audit counters, selection barrier, or graph output readback is used in the timed interval.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'summaries':summaries},indent=2))
if not out['all_checks_pass']:raise SystemExit('timing v2 independent audit failed')
