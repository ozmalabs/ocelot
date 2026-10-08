#!/usr/bin/env python3
"""Parity gates and timed response-cost summaries for v2.2."""
import json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/vision_multiseed_response_cost_replay_v2_2_20260927.json'
OUT=ROOT/'evaluation/reports/vision_multiseed_response_cost_replay_v2_2_analysis_20260927.json'
sys.path.insert(0,str(ROOT/'scripts'))
import substrate_vision_multiseed_response_cost_replay_v2_2 as runner
d=json.loads(RAW.read_text());ref=json.loads(runner.V21.read_text());locked=runner.source_inputs()
expected={}
for s in runner.SEEDS:
 expected[str(s)]={x['condition']:x for x in ref['seeds'][str(s)]}
rows=[x for s in runner.SEEDS for x in d['seeds'][str(s)]['conditions']]
parity_fields=('termination','passes_completed','progress_steps','cycle_start_pass_index','cycle_period_passes','initial_graph_sha256','checkpoint_sha256')
def same(a,b):return a==b
parity=[]
for r in rows:
 refrow=expected[str(r['seed'])][r['condition']]
 parity.append(all(same(r[k],refrow[k]) for k in parity_fields) and r['rate_write_snapshot']['state']==refrow['rate_write_snapshot']['state'] and r['rate_write_snapshot']['equation_mismatches']==len(refrow['rate_write_snapshot']['equation_mismatches']))
def finite_positive(x):return isinstance(x,(int,float)) and math.isfinite(x) and x>0
checks={
 'source_stable_and_locked':d.get('source_stable') is True and d['locked_inputs']==locked,
 'three_isolated_seed_processes_complete':d.get('complete') is True and all(d['seeds'][str(s)].get('complete') and len(d['seeds'][str(s)]['conditions'])==25 for s in runner.SEEDS),
 'all_75_conditions_match_v2_1_exactly':len(rows)==75 and all(parity),
 'all_delivered_pixels_and_rate_equations_valid':all(r['a_pixels']==r['a_retinal_bursts'] and r['b_pixels']==r['b_retinal_bursts'] and r['rate_write_snapshot'] is not None and r['rate_write_snapshot']['equation_mismatches']==0 for r in rows),
 'all_terminations_inside_registered_bounds':all(r['termination'] in ('fixed_point','repeated_graph_state') and r['passes_completed']<=512 and r['progress_steps']<=1_600_000 for r in rows),
 'timings_finite_and_accounted':all(all(finite_positive(r[k]) for k in ('condition_wall_seconds','condition_process_cpu_seconds','engine_call_wall_seconds','engine_call_process_cpu_seconds')) and r['engine_call_wall_seconds']<=r['condition_wall_seconds']*1.01 and r['engine_call_process_cpu_seconds']<=r['condition_process_cpu_seconds']*1.01 for r in rows),
 'memory_measurements_present':all(r['rss_before_bytes'] and r['rss_after_bytes'] and r['process_peak_rss_bytes']>=r['rss_after_bytes'] for r in rows),
}
by_seed={}
for s in runner.SEEDS:
 rs=d['seeds'][str(s)]['conditions']
 def stats(key):return {'median':statistics.median(r[key] for r in rs),'min':min(r[key] for r in rs),'max':max(r[key] for r in rs),'total':sum(r[key] for r in rs)}
 peak=d['seeds'][str(s)]['process_peak_rss_bytes']
 by_seed[str(s)]={'condition_count':len(rs),'termination_counts':{k:sum(r['termination']==k for r in rs) for k in ('fixed_point','repeated_graph_state')},'engine_call_wall_seconds':stats('engine_call_wall_seconds'),'engine_call_process_cpu_seconds':stats('engine_call_process_cpu_seconds'),'whole_condition_wall_seconds':stats('condition_wall_seconds'),'whole_condition_process_cpu_seconds':stats('condition_process_cpu_seconds'),'process_peak_rss_bytes':peak,'process_peak_rss_mib':peak/(1024**2),'wall_by_condition':{r['condition']:r['condition_wall_seconds'] for r in rs}}
types={'blank':lambda c:c=='both_blank','single_sheet':lambda c:c!='both_blank' and (c.endswith('_A_only') or c.endswith('_B_only')),'joint_sheet':lambda c:c.endswith('_both')}
by_class={}
for label,pred in types.items():
 rs=[r for r in rows if pred(r['condition'])]
 by_class[label]={}
 for key in ('engine_call_wall_seconds','engine_call_process_cpu_seconds','condition_wall_seconds','condition_process_cpu_seconds'):
  by_class[label][key]={'median':statistics.median(r[key] for r in rs),'min':min(r[key] for r in rs),'max':max(r[key] for r in rs),'n':len(rs)}
result={'run_id':'vision-multiseed-response-cost-replay-v2.2-analysis','input':str(RAW.relative_to(ROOT)),'checks':checks,'pass':all(checks.values()),'trial_count':len(rows),'parity_failure_count':sum(not x for x in parity),'by_seed':by_seed,'by_stimulus_class':by_class,'interpretation':'These host-specific timings include all CPU consumed by native engine calls on the process (including native worker threads) and separately time the run_rules_report calls. Whole-condition totals include graph construction/restoration, input injection, exact graph serialization and hashing for cycle detection, and state extraction. RSS is a per-seed worker process high-water mark; it is not attribution to an individual condition or native routine. No natural-workload or larger-frame performance claim follows.'}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':result['pass'],'checks':checks,'parity_failure_count':result['parity_failure_count'],'by_seed':{s:{'termination_counts':x['termination_counts'],'engine_call_wall_seconds':x['engine_call_wall_seconds'],'whole_condition_wall_seconds':x['whole_condition_wall_seconds'],'process_peak_rss_mib':x['process_peak_rss_mib']} for s,x in by_seed.items()},'by_stimulus_class':by_class},indent=2))
if not result['pass']:raise SystemExit('v2.2 cost replay integrity failure')
