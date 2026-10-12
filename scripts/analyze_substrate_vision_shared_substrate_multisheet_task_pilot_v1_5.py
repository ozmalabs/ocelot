#!/usr/bin/env python3
"""Independent checks for the fixed-frame multi-sheet diagnostic."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_5_20260927.json'
d=json.loads(p.read_text()); by={x['condition']:x for x in d['conditions']}
checks={
 'source_stable':d['source_stable'] and d['locked_inputs']==d['post_run_inputs'],
 'four_conditions_complete':set(by)=={'both_blank','b_only_exact','a_only_exact','both_exact'},
 'same_prepared_state':len({x['prepared_graph_sha256'] for x in by.values()})==1,
 'blank_control_inactive':by['both_blank']['B_units']['act_sum']==0.0,
 'fixed_B_grating_activates_all_B_units':by['b_only_exact']['b_retinal_bursts']==128.0 and by['b_only_exact']['B_units']['act_active_count']==16,
 'A_stimulus_does_not_change_fixed_B_activation':by['b_only_exact']['B_units']['acts']==by['both_exact']['B_units']['acts'],
 'A_blank_B_units_inactive':by['a_only_exact']['B_units']['act_sum']==0.0,
 'B_rate_field_zero_in_B_conditions':all(by[k]['B_units']['rate_sum']==0.0 for k in ('b_only_exact','both_exact')),
 'closure_terminated':all(x['closure_attempts'][-1]['status'] in ('fixed_point','repeated_graph_state') for x in by.values()),
}
result={'input':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),'checks':checks,'pass':all(checks.values()),
 'interpretation':'The exact B grating evokes positive endpoint act in all B SUnits. The per-unit B act vector is identical with A blank and A stimulated. B rate remains zero in both conditions; v1.6 subsequently shows the exact-frame activations are below learned theta, so this rate is expected. This rejects measurable A-to-B suppression in this one fixed-frame, root-scoped endpoint comparison; it does not generalize beyond the fixture.'}
out=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_5_analysis_20260927.json'
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if not result['pass']:raise SystemExit(1)
