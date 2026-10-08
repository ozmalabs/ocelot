#!/usr/bin/env python3
"""Check thresholded SUnit rate semantics and endpoint stamps."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_6_20260927.json'
d=json.loads(p.read_text());by={x['condition']:x for x in d['conditions']}
expected_step=3000+2000*10+10
rows=[];mismatches=[];stale=[]
for name in ('b_only_exact','both_exact'):
 for i,(act,theta,rate,sa,sr) in enumerate(zip(by[name]['B_units']['acts'],by[name]['B_units']['thetas'],by[name]['B_units']['rates'],by[name]['B_units']['act_steps'],by[name]['B_units']['rate_steps'])):
  predicted=max(act-theta,0.0);delta=abs(predicted-rate)
  rows.append({'condition':name,'unit':i,'act':act,'theta':theta,'predicted_rate':predicted,'observed_rate':rate,'abs_error':delta,'act_step':sa,'rate_step':sr})
  if delta>1e-9:mismatches.append(rows[-1])
  if sa!=expected_step or sr!=expected_step:stale.append(rows[-1])
checks={
 'source_stable':d['source_stable'] and d['locked_inputs']==d['post_run_inputs'],
 'all_conditions_present':set(by)=={'both_blank','b_only_exact','a_only_exact','both_exact'},
 'same_prepared_state':len({x['prepared_graph_sha256'] for x in by.values()})==1,
 'exact_B_grating_activates_all_units':by['b_only_exact']['B_units']['act_active_count']==16 and by['both_exact']['B_units']['act_active_count']==16,
 'A_stimulus_does_not_change_B_act':by['b_only_exact']['B_units']['acts']==by['both_exact']['B_units']['acts'],
 'threshold_equation_matches':not mismatches,
 'update_stamps_match_endpoint_step':not stale,
 'blank_controls_inactive':by['both_blank']['B_units']['act_sum']==0 and by['a_only_exact']['B_units']['act_sum']==0,
 'closures_terminal':all(x['closure_attempts'][-1]['status'] in ('fixed_point','repeated_graph_state') for x in by.values()),
}
result={'input':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),'expected_endpoint_step':expected_step,'checks':checks,'pass':all(checks.values()),'unit_rows':rows,'mismatches':mismatches,'stale_stamps':stale,
 'interpretation':'For this fixture, rate is exactly max(act-theta,0); the measured thresholds exceed the exact-frame activations, so zero rate is expected despite positive act. Both update stamps equal the step implied by the registered schedule. This explains the v1.4/v1.5 rate-act distinction for the root-scoped exact-frame endpoint; it does not establish cross-scope agreement or broader visual capability.'}
out=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_6_analysis_20260927.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'pass':result['pass'],'expected_endpoint_step':expected_step,'theta_range':[min(x['theta'] for x in rows),max(x['theta'] for x in rows)],'act_range':[min(x['act'] for x in rows),max(x['act'] for x in rows)],'mismatch_count':len(mismatches),'stale_stamp_count':len(stale)},indent=2))
if not result['pass']:raise SystemExit(1)
