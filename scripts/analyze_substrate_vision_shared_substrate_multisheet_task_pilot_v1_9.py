#!/usr/bin/env python3
"""Independent integrity and response summaries for the frozen-state panel."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_20260927.json'
d=json.loads(p.read_text());scopes=d['scope_results'];root={x['condition']:x for x in scopes['root_scoped']};glob={x['condition']:x for x in scopes['global']}
expected={'both_blank'}
for theta in (0,45,90,135):
 for ph in (0.0,1.570796):
  tag=f'theta_{theta}_phase_{ph:.6f}';expected|={f'{tag}_{mode}' for mode in ('A_only','B_only','both')}
rate_mismatches=sum(len(x['rate_write_snapshot']['equation_mismatches']) for ss in scopes.values() for x in ss if x['rate_write_snapshot'])
missing_rate=sum(x['rate_write_snapshot'] is None for ss in scopes.values() for x in ss)
summary={}
for scope,rows in scopes.items():
 summary[scope]={}
 for x in rows:
  if x['condition']=='both_blank':continue
  rw=x['rate_write_snapshot'];terminal=x['terminal_state'];orbit=x['post_settle_orbit_statistics']
  last=x['pass_records'][-1];prior=x['pass_records'][-2] if len(x['pass_records'])>1 else last
  cap_delta=max((abs(float(a)-float(b)) for layer in ('A','B') for a,b in zip(last['state'][layer]['act'],prior['state'][layer]['act'])),default=0.0)
  if x['termination']=='repeated_graph_state':post_a=sum(orbit['A']['act']['unit_mean']);post_b=sum(orbit['B']['act']['unit_mean']);peak_a=max(orbit['A']['act']['unit_max'],default=0.0);peak_b=max(orbit['B']['act']['unit_max'],default=0.0)
  elif x['termination']=='fixed_point':post_a=sum(terminal['A']['act']);post_b=sum(terminal['B']['act']);peak_a=max(terminal['A']['act'],default=0.0);peak_b=max(terminal['B']['act'],default=0.0)
  else:post_a=post_b=peak_a=peak_b=None
  summary[scope][x['condition']]={'termination':x['termination'],'passes':x['passes_completed'],'progress_steps':x['progress_steps'],'cycle_period':x['cycle_period_passes'],'terminal_pass_act_changes':sum(last['changed_units'][layer]['act'] for layer in ('A','B')),'last_two_pass_max_abs_act_delta':cap_delta,
   'rate_write_pass':rw['pass'] if rw else None,'A_rate_write_sum':sum(rw['state']['A']['rate']) if rw else None,'B_rate_write_sum':sum(rw['state']['B']['rate']) if rw else None,
   'A_act_at_rate_write_sum':sum(rw['state']['A']['act']) if rw else None,'B_act_at_rate_write_sum':sum(rw['state']['B']['act']) if rw else None,
   'A_postsettle_act_mean_sum':post_a,'B_postsettle_act_mean_sum':post_b,
   'A_postsettle_act_peak':peak_a,'B_postsettle_act_peak':peak_b}
checks={
 'source_stable':d['source_stable'] and d['locked_inputs']==d['post_run_inputs'],
 'all_50_conditions_present':len(root)==25 and len(glob)==25 and set(root)==expected and set(glob)==expected,
 'matched_prepared_graph_per_condition':all(root[k]['initial_graph_sha256']==glob[k]['initial_graph_sha256'] for k in expected),
 'input_bursts_match_active_pixels':all(x['a_pixels']==x['a_retinal_bursts'] and x['b_pixels']==x['b_retinal_bursts'] for ss in scopes.values() for x in ss),
 'rate_write_snapshot_present':missing_rate==0,
 'rate_equation_holds_at_write':rate_mismatches==0,
 'step_stamps_consistent':all(x['retina_step']==23010 and all(int(z)==23010 for layer in ('A','B') for z in x['rate_write_snapshot']['state'][layer]['rate_step']) and all(int(z)==23010 for layer in ('A','B') for z in x['rate_write_snapshot']['state'][layer]['act_step']) for ss in scopes.values() for x in ss),
 'all_terminations_classified':all(x['termination'] in ('fixed_point','repeated_graph_state','pass_cap_reached','progress_cap_reached') for ss in scopes.values() for x in ss),
 'cycle_orbit_stats_present':all(x['termination']!='repeated_graph_state' or (x['cycle_period_passes'] and x['post_settle_orbit_statistics']['A']['act']['unit_min']) for ss in scopes.values() for x in ss),
 'progress_within_cap':all(x['progress_steps']<=1_600_000 and x['passes_completed']<=512 for ss in scopes.values() for x in ss),
}
result={'input':str(p.relative_to(ROOT)),'checks':checks,'pass':all(checks.values()),'rate_write_mismatch_count':rate_mismatches,'missing_rate_write_count':missing_rate,'termination_counts':{s:{k:sum(x['termination']==k for x in rows) for k in ('fixed_point','repeated_graph_state','pass_cap_reached','progress_cap_reached')} for s,rows in scopes.items()},'response_summary':summary,
 'interpretation':'This is a frozen-state stimulus response panel, not a learning generalization or prevalence estimate. Rate-write equation and input-delivery gates establish the declared phase-specific measurements. Post-settle activation is reported as a fixed-point value or cycle-orbit statistic. Scope differences are conditional on one root-scoped-adapted graph.'}
out=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_analysis_20260927.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'pass':result['pass'],'rate_write_mismatch_count':rate_mismatches,'termination_counts':result['termination_counts']},indent=2))
if not result['pass']:raise SystemExit(1)
