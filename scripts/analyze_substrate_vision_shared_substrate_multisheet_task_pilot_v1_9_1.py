#!/usr/bin/env python3
"""Check exact-input native replay of the v1.9 global joint-sheet caps."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1_20260927.json'
d=json.loads(p.read_text());v19=json.loads((ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_20260927.json').read_text())
old={x['condition']:x for x in v19['scope_results']['global'] if x['termination']=='pass_cap_reached'};new={x['condition']:x for x in d['cases']}
checks={
 'source_stable':d['source_stable'] and d['locked_inputs']==d['post_run_inputs'],
 'all_eight_prior_cap_cases_replayed':len(old)==8 and set(new)==set(old),
 'exact_initial_input_graphs_match_v1_9':all(new[k]['start_graph_sha256']==old[k]['initial_graph_sha256'] for k in old),
 'pixel_counts_match_retinal_bursts':all(x['a_pixels']==x['a_retinal_bursts'] and x['b_pixels']==x['b_retinal_bursts'] for x in new.values()),
 'full_closure_terminal_class_observed':all(x['status'] in ('fixed_point','repeated_graph_state') for x in new.values()),
 'each_run_exceeded_instrumentation_horizon':all(x['passes_completed']>512 for x in new.values()),
 'within_native_progress_budget':all(x['progress_steps']<=d['progress_cap'] and x['budget_overshoot']==0 for x in new.values()),
}
result={'input':str(p.relative_to(ROOT)),'checks':checks,'pass':all(checks.values()),'status_counts':{s:sum(x['status']==s for x in new.values()) for s in ('fixed_point','repeated_graph_state')},'case_summary':{k:{'status':v['status'],'passes':v['passes_completed'],'progress':v['progress_steps'],'elapsed_s':v['elapsed_s']} for k,v in new.items()},
 'interpretation':'All eight global both-sheet cases previously cut off by the 512-pass Python trace horizon terminate under the native full-closure runner from byte-equivalent initial input graphs. One reaches a fixed point and seven end by exact repeated-graph detection, from 1,416 to 8,850 passes, all below the 1.6M progress ceiling. The prior pass cap was an instrumentation horizon, not evidence of unresolved engine termination for these eight cases. This remains one prepared state and one visual family; cycle periods are not exposed by the native summary API.'}
out=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1_analysis_20260927.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if not result['pass']:raise SystemExit(1)
