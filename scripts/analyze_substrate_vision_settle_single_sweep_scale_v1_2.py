#!/usr/bin/env python3
"""Independent checks and scale summary for the one-sweep vision probe."""
from __future__ import annotations
import hashlib,json,statistics,importlib.util
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_2_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_settle_single_sweep_scale_v1_2_lock_20260927.json'
RUNNER=ROOT/'scripts/substrate_vision_settle_single_sweep_scale_v1_2.py'
OUT=ROOT/'evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_2_analysis_20260927.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def recompute(arm,n):
 act=arm['act_before'];aff=arm['aff'];global_mean=sum(act)/len(act);expected=[]
 for i in range(n):
  for j in range(n):
   q=i*n+j;ns=[y*n+x for y in range(max(0,i-1),min(n,i+2)) for x in range(max(0,j-1),min(n,j+2)) if (y,x)!=(i,j)]
   local=sum(act[k] for k in ns)/len(ns) if ns else 0.0
   expected.append(max(aff[q]+local-global_mean,0.0))
 return expected
def main():
 spec=importlib.util.spec_from_file_location('vision_sweep_runner',RUNNER);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];runs=raw['runs'];checks={}
 checks['locked_sources_match_current_and_capture']=lock==mod.lock_inputs()==raw['locked_inputs']==raw['post_run_inputs']
 checks['runner_source_hash_locked']=lock['runner_sha256']==sha(RUNNER)
 checks['three_distinct_workers']=len(runs)==3 and len({r['pid'] for r in runs})==3
 checks['worker_fingerprints_match_lock']=all(r['worker_started_inputs']==lock==r['worker_finished_inputs'] for r in runs)
 checks['registered_size_seed_matrix']=all([(c['n_side'],c['seed']) for c in r['cases']]==[(n,s) for n in mod.SIZES for s in mod.SEEDS] for r in runs)
 all_arms=[a for r in runs for c in r['cases'] for a in c['arms']]
 checks['all_progress_and_root_membership']=all(a['one_batch_application_progress'] and a['root_membership_count']==a['unit_count']==a['n_side']**2 for a in all_arms)
 checks['one_step_outputs_match_independent_equation']=all(max(abs(x-y) for x,y in zip(a['act_next'],recompute(a,a['n_side'])))<=1e-12 for a in all_arms)
 checks['paired_global_and_root_scoped_outputs_equal']=all(c['arms'][0]['act_next']==c['arms'][1]['act_next'] for r in runs for c in r['cases'])
 checks['expected_rules_only']=all(set(a['retained_rule_names'])==({'st_settle','st_commit'} if a['variant']=='global' else {'st_settle_root_scoped_benchmark','st_commit'}) for a in all_arms)
 checks['row_frame_and_global_cross_dependency_arithmetic']=all(a['row_frame_count']==a['n_side'] and a['units_per_row_frame']==a['n_side'] and a['global_fold_cross_row_dependency_incidence_count']==a['unit_count']*(a['unit_count']-a['n_side']) and a['global_fold_dependency_treewidth']==a['unit_count']-1 for a in all_arms)
 checks['exact_matcher_candidate_count']=all(sum(int(v) for _,m,v in a['audit_per_rule'] if m=='candidate_tests')==a['unit_count'] for a in all_arms)
 checks['term_evaluation_conservation']=all(sum(int(v) for _,m,v in a['audit_per_rule'] if m=='term_evaluations')==a['audit_global'].get('term_evals_total',-1)==sum(int(v) for k,v in a['audit_global'].items() if k.startswith('term_eval:')) for a in all_arms)
 checks['term_unit_conservation']=all(a['audit_global'].get('term_units_total',-1)==sum(int(v) for k,v in a['audit_global'].items() if k.startswith('term_unit:'))+a['audit_global'].get('term_units_unattributed',0) for a in all_arms)
 checks['global_fold_node_visits_match_two_all_unit_folds']=all(a['audit_global'].get('term_unit:NodesOfType',-1)==(2*a['unit_count']**2+a['unit_count'] if a['variant']=='global' else a['unit_count']) for a in all_arms)
 checks['work_counter_and_trace_payload_repeats']=len({json.dumps([(c['n_side'],c['seed'],[(a['variant'],{k:v for k,v in a['audit_global'].items() if not k.endswith('_ns')},a['audit_per_rule'],a['audit_per_clause'],a['access_trace_counts_by_kind_resource'],a['access_trace_dropped']) for a in c['arms']]) for c in r['cases']],sort_keys=True) for r in runs})==1
 def trace_ok(a):
  tr=a['access_trace_counts_by_kind_resource'];edges=tr.get('term_edge_read',{});types=tr.get('term_type_read',{});n=a['unit_count'];E=a['runtime_edge_type_counts'].get('sunit_neighbour',0)
  return (a['access_trace_dropped']==0 and a['access_trace_rule_uid_count']==1 and edges.get('sunit_neighbour',0)==2*E and edges.get('has_sunit',0)==(2*n*n if a['variant']=='root_scoped' else 0) and types.get('SettleParams',0)==n and types.get('SUnit',0)==(2*n*n if a['variant']=='global' else 0))
 checks['access_trace_visits_match_independent_edge_and_type_counts']=all(trace_ok(a) for a in all_arms)
 summaries=[]
 for n in mod.SIZES:
  rows=[]
  for seed in mod.SEEDS:
   samples=[next(c for c in r['cases'] if c['n_side']==n and c['seed']==seed)['arms'] for r in runs]
   for arm_i,variant in enumerate(('global','root_scoped')):
    arms=[s[arm_i] for s in samples];candidate=[];term=[]
    for a in arms:
     candidate.append(sum(int(v) for _,m,v in a['audit_per_rule'] if m=='candidate_tests'))
     term.append(sum(int(v) for _,m,v in a['audit_per_rule'] if m=='term_evaluations'))
    rows.append({'seed':seed,'variant':variant,'unit_count':n*n,'global_fold_cross_row_dependency_incidences':arms[0]['global_fold_cross_row_dependency_incidence_count'],
     'candidate_tests_per_worker':candidate,'term_evaluations_per_worker':term,'audit_disabled_apply_ns_per_worker':[a['audit_disabled_apply_ns_median'] for a in arms],
     'nodesoftype_term_units_per_worker':[a['audit_global'].get('term_unit:NodesOfType',0) for a in arms],
     'runtime_typed_edge_cut_incidence_count_per_worker':[a['runtime_typed_edge_cut_incidence_count'] for a in arms],
     'sunit_neighbour_edge_visits_per_worker':[a['access_trace_counts_by_kind_resource'].get('term_edge_read',{}).get('sunit_neighbour',0) for a in arms],
     'has_sunit_edge_visits_per_worker':[a['access_trace_counts_by_kind_resource'].get('term_edge_read',{}).get('has_sunit',0) for a in arms],
     'sunit_type_index_items_per_worker':[a['access_trace_counts_by_kind_resource'].get('term_type_read',{}).get('SUnit',0) for a in arms],
     'local_neighbor_cross_row_edges_per_worker':[a['local_neighbor_cross_row_edge_count'] for a in arms]})
  summaries.append({'n_side':n,'unit_count':n*n,'by_seed_variant':rows})
 payload={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analysis_sha256':sha(Path(__file__).resolve()),'checks':checks,
  'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_gates_pass':all(checks.values()),'scale_summary':summaries,
  'claim_boundary':'Exact counters characterize one batched st_settle application on authored one-sheet graphs. Row frames are imposed by the protocol and are not learned. Cross-row global-factor incidence and complete dependency width follow the independently checked rule equation. Timings exclude construction and iterative settling and remain fixture-specific.'}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'all_gates_pass':payload['all_gates_pass'],'checks_passed':payload['checks_passed'],'checks_total':payload['checks_total'],'scale_summary':summaries},indent=2))
 if not payload['all_gates_pass']:raise SystemExit('vision single-sweep independent analysis failed')
if __name__=='__main__':main()
