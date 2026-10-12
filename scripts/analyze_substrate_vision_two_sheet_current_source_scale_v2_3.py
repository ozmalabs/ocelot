#!/usr/bin/env python3
"""Independent scaling, parity, counter, timing, and memory analysis for v2.3."""
import json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'evaluation/reports/vision_two_sheet_current_source_scale_v2_3_20260927.json';LOCK=ROOT/'evaluation/substrate_capability/vision_two_sheet_current_source_scale_v2_3_lock_20260927.json';OUT=ROOT/'evaluation/reports/vision_two_sheet_current_source_scale_v2_3_analysis_20260927.json'
d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());cells=d['cells'];by={x['cell_id']:x for x in cells}
def cid(seed,n,scope,b,mode):return f's{seed}_n{n}_{scope}_b{int(b)}_{mode}'
expected={cid(s,n,sc,b,m) for s in (4101,7301,10703) for n in (2,4,8,16) for sc in ('global','scoped') for b in (0.0,1.0) for m in ('plain','audit')}
pairs=[]
for seed in (4101,7301,10703):
 for n in (2,4,8,16):
  for sc in ('global','scoped'):
   for b in (0.0,1.0):
    a=by.get(cid(seed,n,sc,b,'plain'));z=by.get(cid(seed,n,sc,b,'audit'))
    if a and z:pairs.append((a,z))
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
src_inputs=d['locked_inputs']
checks={
 'source_lock_matches_and_run_stable':src_inputs==lock['locked_inputs'] and d.get('source_stable') and all(x['source_stable'] and x['source_lock_sha256']==__import__('hashlib').sha256(LOCK.read_bytes()).hexdigest() for x in cells),
 'all_96_unique_registered_cells':len(cells)==96 and len(by)==96 and set(by)==expected and d.get('complete'),
 'exact_plain_audit_graph_semantic_parity':len(pairs)==48 and all(a['progress']==z['progress'] and a['act_next_A']==z['act_next_A'] and a['act_next_B']==z['act_next_B'] and a['members_per_root']==z['members_per_root'] and a['graph_nodes']==z['graph_nodes'] and a['graph_edges']==z['graph_edges'] for a,z in pairs),
 'all_root_memberships_and_equations_valid':all(x['members_per_root']==[x['units_per_sheet']]*2 and x['max_equation_residual']<=1e-12 for x in cells),
 'all_closures_below_cap':all(0<x['progress']<x['budget'] and not x['budget_exit'] for x in cells),
 'counter_conservation_and_closed_form':all((sum(y['count'] for y in x['per_rule_counters'] if y['metric']==metric)==x['global_counters'].get(global_key,0)) for x in cells if x['mode']=='audit' for metric,global_key in (('candidate_tests','cand_tested'),('candidate_pairs','cand_enum'),('term_units','term_units_total'),('term_evaluations','term_evals_total'),('where_evaluations','where_evals'),('effect_attr_set_attempts','rule_effect_attr_set_attempts'),('rule_enumerations','rule_enumerations'))) and all(x['global_counters'].get('term_unit:NodesOfType',0)==(2*x['units_per_sheet']*(4*x['units_per_sheet']+1) if x['scope']=='global' else 2*x['units_per_sheet']) for x in cells if x['mode']=='audit'),
 'global_coupling_and_scoped_independence':all(max(abs(x['act_next_A'][i]-y['act_next_A'][i]) for i in range(len(x['act_next_A'])))>0 for x,y in [(by[cid(s,n,'global',0.0,'plain')],by[cid(s,n,'global',1.0,'plain')]) for s in (4101,7301,10703) for n in (2,4,8,16)]) and all(by[cid(s,n,'scoped',0.0,'plain')]['act_next_A']==by[cid(s,n,'scoped',1.0,'plain')]['act_next_A'] for s in (4101,7301,10703) for n in (2,4,8,16)),
 'time_and_memory_measurements_present':all(finite(x['closure_wall_seconds']) and x['closure_wall_seconds']>0 and finite(x['closure_process_cpu_seconds']) and x['closure_process_cpu_seconds']>0 and x['rss_before_build_bytes'] and x['rss_after_build_bytes'] and x['rss_after_graph_snapshot_bytes'] and x['process_peak_rss_bytes'] for x in cells),
}
summary=[]
for n in (2,4,8,16):
 for scope in ('global','scoped'):
  for mode in ('plain','audit'):
   xs=[x for x in cells if x['n_side']==n and x['scope']==scope and x['mode']==mode]
   ctr=[x['global_counters'].get('term_unit:NodesOfType',0) for x in xs]
   summary.append({'n_side':n,'units_total':2*n*n,'aggregate_input_units_per_output':2*n*n if scope=='global' else n*n,'scope':scope,'mode':mode,'replicates':len(xs),'median_progress':statistics.median(x['progress'] for x in xs),'median_closure_wall_seconds':statistics.median(x['closure_wall_seconds'] for x in xs),'min_closure_wall_seconds':min(x['closure_wall_seconds'] for x in xs),'max_closure_wall_seconds':max(x['closure_wall_seconds'] for x in xs),'median_closure_process_cpu_seconds':statistics.median(x['closure_process_cpu_seconds'] for x in xs),'median_process_peak_rss_mib':statistics.median(x['process_peak_rss_bytes'] for x in xs)/(1024**2),'max_graph_nodes':max(x['graph_nodes'] for x in xs),'median_nodesoftype_work':statistics.median(ctr) if ctr else None,'median_term_evaluations_total':statistics.median(x['global_counters'].get('term_evals_total',0) for x in xs) if ctr else None})
for n in (2,4,8,16):
 for scope in ('global','scoped'):
  plain=[x for x in cells if x['n_side']==n and x['scope']==scope and x['mode']=='plain'];audit=[x for x in cells if x['n_side']==n and x['scope']==scope and x['mode']=='audit']
  for x,z in zip(sorted(plain,key=lambda x:(x['seed'],x['b_initial_act'])),sorted(audit,key=lambda x:(x['seed'],x['b_initial_act']))):x['paired_audit_wall_ratio']=z['closure_wall_seconds']/x['closure_wall_seconds']
result={'run_id':'vision-two-sheet-current-source-scale-v2.3-analysis','raw_sha256':__import__('hashlib').sha256(RAW.read_bytes()).hexdigest(),'checks':checks,'pass':all(checks.values()),'cell_count':len(cells),'paired_cell_count':len(pairs),'by_size_scope_mode':summary,'audit_wall_ratios':{f'n{n}_{sc}':{'median':statistics.median(x['paired_audit_wall_ratio'] for x in cells if x['n_side']==n and x['scope']==sc and x['mode']=='plain'),'min':min(x['paired_audit_wall_ratio'] for x in cells if x['n_side']==n and x['scope']==sc and x['mode']=='plain'),'max':max(x['paired_audit_wall_ratio'] for x in cells if x['n_side']==n and x['scope']==sc and x['mode']=='plain')} for n in (2,4,8,16) for sc in ('global','scoped')},'interpretation':'For this one authored rule, the global output directly reads an aggregate of all T SUnits while the scoped output reads an aggregate of N SUnits from its own sheet. The term_unit:NodesOfType counter measures only NodesOfType collection work; it omits Neighbours result cardinality, so its large global/scoped ratio is not a like-for-like total-work ratio. Total term evaluations and counter-off wall time are the more comparable measures here. Audit-on/off semantics match exactly. These current-host measurements on one controlled factor are not a natural-task scaling law.'}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':result['pass'],'checks':checks,'cells':len(cells),'by_size_scope_mode':summary,'audit_wall_ratios':result['audit_wall_ratios']},indent=2))
if not result['pass']:raise SystemExit('v2.3 scaling analysis gate failure')
