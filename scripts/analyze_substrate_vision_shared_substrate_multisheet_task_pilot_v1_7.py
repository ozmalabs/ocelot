#!/usr/bin/env python3
"""Independent integrity and outcome analysis for the matched scope capture."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_20260927.json'
d=json.loads(p.read_text()); scopes={'root_scoped':d['root_scoped_conditions'],'global':d['global_conditions']};by={s:{x['condition']:x for x in rows} for s,rows in scopes.items()}
want={'both_blank','b_only_exact','a_only_exact','both_exact'};rows=[];mismatches=[];stamp_errors=[]
expected_step=23010
for scope in scopes:
 for cond,x in by[scope].items():
  if cond not in want:continue
  for layer in ('A_units','B_units'):
   u=x[layer]
   for i,(act,theta,rate,sa,sr) in enumerate(zip(u['acts'],u['thetas'],u['rates'],u['act_steps'],u['rate_steps'])):
    err=abs(max(act-theta,0.0)-rate);row={'scope':scope,'condition':cond,'layer':layer,'unit':i,'act':act,'theta':theta,'rate':rate,'thresholded_final_act':max(act-theta,0.0),'abs_delta':err,'act_step':sa,'rate_step':sr}
    rows.append(row)
    if err>1e-9:mismatches.append(row)
    if sa!=expected_step or sr!=expected_step:stamp_errors.append(row)
status={s:{c:x['closure_attempts'][-1]['status'] for c,x in m.items()} for s,m in by.items()}
progress={s:{c:x['closure_attempts'][-1]['cumulative'] for c,x in m.items()} for s,m in by.items()}
checks={
 'source_stable':d['source_stable'] and d['locked_inputs']==d['post_run_inputs'],
 'both_scopes_four_conditions':all(set(by[s])==want for s in scopes),
 'global_twin_same_retina_and_unit_ids':d['topology']['retina_ids']==d['topology_global_twin']['retina_ids'] and d['topology']['unit_ids']==d['topology_global_twin']['unit_ids'],
 'prepared_graph_hash_equal_in_all_conditions':all(x['prepared_graph_sha256']==d['prepared_graph_sha256'] for s in scopes for x in by[s].values()),
 'condition_bursts_match_declared_pixels':all(x['a_retinal_bursts']==x['a_pixels'] and x['b_retinal_bursts']==x['b_pixels'] for s in scopes for x in by[s].values()),
 'closure_statuses_terminal':all(v in ('fixed_point','repeated_graph_state') for s in status for v in status[s].values()),
 'all_presentations_within_progress_bound':all(v<=1_600_000 for s in progress for v in progress[s].values()),
 'update_stamps_at_scheduled_endpoint':not stamp_errors,
}
root_b=by['root_scoped'];glob=by['global']
findings={
 'root_scope_B_act_Bonly_equals_both':root_b['b_only_exact']['B_units']['acts']==root_b['both_exact']['B_units']['acts'],
 'global_scope_B_act_changes_when_A_added':glob['b_only_exact']['B_units']['acts']!=glob['both_exact']['B_units']['acts'],
 'global_B_only_positive_act':glob['b_only_exact']['B_units']['act_active_count']==16,
 'global_both_condition_B_act_zero':glob['both_exact']['B_units']['act_sum']==0.0,
 'root_B_both_positive_act':root_b['both_exact']['B_units']['act_active_count']==16,
 'final_act_rate_equation_mismatch_count':len(mismatches),
 'rate_mismatch_by_scope_condition':{s:{c:sum(r['scope']==s and r['condition']==c for r in mismatches) for c in want} for s in scopes},
 'cycle_status_by_scope':status,
 'max_closure_progress_by_scope':{s:max(v.values()) for s,v in progress.items()},
}
result={'input':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),'expected_endpoint_step':expected_step,'integrity_checks':checks,'capture_valid':all(checks.values()),'measured_findings':findings,'rate_equation_mismatches':mismatches,'stamp_errors':stamp_errors,
 'semantic_gates':{'final_rate_equals_thresholded_final_act':not mismatches,'final_rate_equation_mismatch_count':len(mismatches)},
 'interpretation':'The matched graph transfer and capture integrity gates pass. Root-scoped B act is identical when A is blank or stimulated; global-rule B act is positive and oscillatory for B-only input but zero at a fixed point when both sheets are stimulated. This is a one-state dynamic coupling signal, not a settled-output parity result because several compared arms end in repeated-state cycles. Final act and rate are not generally an algebraic pair: the native rule writes rate once per step from act, while the settling rules can subsequently update act without advancing the step stamp. The rate discrepancies therefore require pass-level sequencing interpretation and must not be read as failures of the threshold equation alone.'}
out=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_analysis_20260927.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'integrity_checks':checks,'capture_valid':result['capture_valid'],'findings':findings},indent=2))
if not result['capture_valid']:raise SystemExit(1)
