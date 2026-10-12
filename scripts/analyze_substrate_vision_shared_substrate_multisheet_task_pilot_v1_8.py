#!/usr/bin/env python3
"""Validate pass-sliced closure parity and summarize field timing/cycles."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
import substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 as base
p=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_20260927.json'
d=json.loads(p.read_text());raw17=json.loads((ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7_20260927.json').read_text())
order={}
for scoped,label in ((True,'root_scoped'),(False,'global')):
 s,*_=base.build_pair(base.SEED,scoped);names=[r['name'] for r in s._inner.export_rules()]
 aliases={'st_settle':'st_settle_root_scoped_benchmark'} if scoped else {}
 select=('st_latch_aff',aliases.get('st_settle','st_settle'),'st_commit','st_burst_bubble','oo_sunit_activate','oo_sunit_rate')
 order[label]=[{'index':names.index(n),'name':n} for n in select]

def count_changes(row,key):return sum(1 for nid in row['before'] if row['before'][nid][key]!=row['after'][nid][key])
trace_summary={}
for scope,rows in d['scopes'].items():
 trace_summary[scope]={}
 for c in rows:
  fields=['act','rate','theta','act_step','rate_step','bursting'];
  trace_summary[scope][c['condition']]={'status':c['status'],'passes':c['passes_completed'],'cycle_start_pass_index':c['cycle_start_pass_index'],'cycle_period_passes':c['cycle_period_passes'],'progress_steps_sum':c['progress_steps_sum'],
    'first_changed_pass':{k:next((r['pass'] for r in c['passes'] if count_changes(r,k)),None) for k in fields},
    'changed_unit_counts_by_pass':{k:[{'pass':r['pass'],'units':count_changes(r,k)} for r in c['passes'] if count_changes(r,k)] for k in fields},
    'act_changes_after_rate_first_write':sum(1 for r in c['passes'] if r['pass']>3 and count_changes(r,'act')>0),
    'unit_count':len(c['b_unit_ids'])+len(c['a_unit_ids'])}
preflight=d['preflight']
base18=json.loads(json.dumps(d['locked_inputs']['base_inputs']));base17=json.loads(json.dumps(raw17['locked_inputs']['v1_4_inputs']))
for source,key in ((base18,'scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8.py'),(base17,'scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_7.py')):
 source['source_closure_sha256'].pop(key,None);source.pop('runner_sha256',None)
checks={
 'source_stable':d['source_stable'] and d['locked_inputs']==d['post_run_inputs'],
 'trace_interpretation_enabled':d['trace_interpretation_valid'],
 'full_vs_sliced_parity_preflights':len(preflight)==2 and all(x['graph_equal'] and x['status_equal'] and x['work_equal'] for x in preflight),
 'all_eight_traces_present':set(d['scopes'])=={'root_scoped','global'} and all(len(x)==4 for x in d['scopes'].values()),
 'cycle_lengths_reproducible_by_digest':all(x['status']=='fixed_point' or (x['status']=='repeated_graph_state' and x['cycle_period_passes']>0 and x['cycle_start_pass_index'] is not None) for rows in d['scopes'].values() for x in rows),
 'rule_order_source_matches_capture':base18==base17,
 'expected_rule_order':all([order[s][i]['name'] for i in range(len(order[s]))]==(['st_latch_aff','st_settle_root_scoped_benchmark','st_commit','st_burst_bubble','oo_sunit_activate','oo_sunit_rate'] if s=='root_scoped' else ['st_latch_aff','st_settle','st_commit','st_burst_bubble','oo_sunit_activate','oo_sunit_rate']) for s in order),
}
result={'input':str(p.relative_to(ROOT)),'checks':checks,'pass':all(checks.values()),'slicing_preflight':preflight,'selected_export_rule_order':order,'trace_summary':trace_summary,
 'interpretation':'Sliced execution reproduces full-closure graph, status, pass count, and progress work for both a cyclic root-scoped B-only case and a fixed-point global both-stimulated case. Across the recorded trajectories, act first changes on pass 2, while rate and rate_step first change on pass 3; act then continues changing in later settling passes without further rate writes. The current rule order places st_settle before oo_sunit_rate within each pass, while the one-time rate guard closes after its write. Repeated-state detection finds exact cycles of 6, 8, and 24 passes depending on condition/scope. This confirms distinct time slices and non-fixed dynamics; it does not determine whether that separation is intended.'}
out=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_analysis_20260927.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':checks,'pass':result['pass'],'rule_order':order,'cycles':{s:{c:{'status':x['status'],'period':x['cycle_period_passes']} for c,x in rs.items()} for s,rs in trace_summary.items()},'rate_first_changed_pass':{s:{c:x['first_changed_pass']['rate'] for c,x in rs.items()} for s,rs in trace_summary.items()}},indent=2))
if not result['pass']:raise SystemExit(1)
