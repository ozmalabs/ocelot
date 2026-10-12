#!/usr/bin/env python3
"""Audit seed->native-rule range attribution against live access UIDs."""
import collections, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/seed_rule_provenance_live_capture_v1_20260927.json'
OUT=ROOT/'evaluation/reports/seed_rule_provenance_live_capture_v1_analysis_20260927.json'
d=json.loads(RAW.read_text());intervals=d['seed_load_intervals'];rules=d['native_rules'];trace=d['trace_rows']
owner_by_idx={};range_conflicts=[];range_gaps=[]
for i,row in enumerate(intervals):
 if row['rule_index_end_exclusive']<row['rule_index_start'] or row['new_rule_count']!=row['rule_index_end_exclusive']-row['rule_index_start']:
  range_conflicts.append({'interval':i,'row':row})
 if i and intervals[i-1]['rule_index_end_exclusive']!=row['rule_index_start']:
  range_gaps.append({'after':intervals[i-1]['seed_id'],'before':row['seed_id'],'prev_end':intervals[i-1]['rule_index_end_exclusive'],'next_start':row['rule_index_start']})
 for idx in range(row['rule_index_start'],row['rule_index_end_exclusive']):
  if idx in owner_by_idx:range_conflicts.append({'rule_index':idx,'first':owner_by_idx[idx],'second':row['seed_id']})
  owner_by_idx[idx]=row['seed_id']
idx_to_rule={int(r['rule_index']):r for r in rules};uid_to_rule={int(r['rule_uid']):r for r in rules}
faculty_indices=set()
for build in d.get('faculty_builds',[]):
 faculty_indices.update(range(int(build['rule_count_before']),int(build['rule_count_after'])))
conceptualizer_indices=set()
for build in d.get('conceptualizer_builds',[]):
 conceptualizer_indices.update(range(int(build['rule_count_before']),int(build['rule_count_after'])))
seed_events=collections.Counter();rule_events=collections.Counter();event_kinds=collections.Counter();unassigned=collections.Counter()
for row in trace:
 uid=int(row['rule_uid']);cnt=int(row['count']);rule=uid_to_rule.get(uid);idx=int(rule['rule_index']) if rule else None
 if idx is not None and idx<d['initial_native_rule_count']:seed='<bootstrap_rules>'
 elif idx is not None and idx<d['seed_terminal_rule_count']:seed=owner_by_idx.get(idx)
 elif idx is not None and idx<d['scene_terminal_rule_count']:seed='<scene_attachment_rules>'
 elif idx is not None and idx<d['native_rule_count'] and idx in faculty_indices:seed='<lazy_describe_faculty_rules>'
 elif idx is not None and idx<d['native_rule_count'] and idx in conceptualizer_indices:seed='<scene_conceptualizer_rules>'
 elif idx is not None and idx<d['native_rule_count']:seed='<conversation_runtime_rules>'
 else:seed=owner_by_idx.get(idx) if idx is not None else None
 if seed is None:seed='<unmapped_rule_index>';unassigned[uid]+=cnt
 seed_events[seed]+=cnt;rule_events[(seed,rule['name'] if rule else f'uid:{uid}')]+=cnt;event_kinds[(seed,row['kind'])]+=cnt
trace_uids={int(r['rule_uid']) for r in trace};rule_uids=set(uid_to_rule)
checks={
 'source_stable':d['source_stable'] and d['post_run_inputs']==d['locked_inputs'],
 'two_expected_calls_and_resolved_lifecycles':d['threads_joined'] and not d['thread_errors'] and d['replies']=={'A':'I see the grey thing stays, the yellow counter, and the blue thing moves.','B':'I see the grey thing stays, the yellow counter, and the blue thing moves.'} and len(d['requests'])==2 and all(x['goal_count']==1 and x['statuses']==['resolved'] and x['events']==['selection','execution','action_result'] for x in d['requests']),
 'seed_index_ranges_are_contiguous':not range_conflicts and not range_gaps,
 'interval_rule_counts_reconcile':sum(x['new_rule_count'] for x in intervals)==d['seed_terminal_rule_count']-d['initial_native_rule_count'],
 'final_rule_index_table_complete':len(rules)==d['native_rule_count'] and sorted(int(r['rule_index']) for r in rules)==list(range(d['native_rule_count'])),
 'uid_names_unique':len(uid_to_rule)==len(rules),
 'phase_rule_boundaries_ordered':d['initial_native_rule_count']<=d['seed_terminal_rule_count']<=d['scene_terminal_rule_count']<=d['native_rule_count'],
 'lazy_and_conceptualizer_rule_deltas_reconcile':sum(int(x['new_rules']) for x in d.get('faculty_builds',[]))+sum(int(x['new_rules']) for x in d.get('conceptualizer_builds',[]))==len(faculty_indices|conceptualizer_indices)==d['native_rule_count']-d['scene_terminal_rule_count'] and not (faculty_indices & conceptualizer_indices),
 'all_access_events_reconcile':sum(int(x['count']) for x in trace)==d['trace_event_count'] and d['trace_dropped']==0,
 'every_traced_uid_in_final_rule_table':trace_uids<=rule_uids,
}
checks['integrity_gates_pass']=all(checks.values())
observed_rules=[{'seed_id':sid,'rule_name':name,'event_count':n} for (sid,name),n in rule_events.most_common(100)]
out={'schema_version':1,'run_id':'seed-rule-provenance-live-capture-v1-analysis-20260927','source_capture':str(RAW.relative_to(ROOT)),'checks':checks,'integrity_gates_pass':checks['integrity_gates_pass'],'source_world_adapter_sha256':d['locked_inputs']['runtime_inputs']['source_sha256']['world_adapter'],'loaded_seed_count':d['boot_report']['loaded'],'boot_failures':d['boot_report']['failed'],'initial_native_rule_count':d['initial_native_rule_count'],'seed_terminal_rule_count':d['seed_terminal_rule_count'],'scene_terminal_rule_count':d['scene_terminal_rule_count'],'final_native_rule_count':d['native_rule_count'],'traced_uid_count':len(trace_uids),'trace_event_count':d['trace_event_count'],'rule_access_events_by_source':[{'source_class':sid,'event_count':n} for sid,n in seed_events.most_common()],'top_observed_source_rules':observed_rules,'unmapped_trace_uids':dict(unassigned),'range_conflicts':range_conflicts[:20],'range_gaps':range_gaps[:20],'interpretation':'Each native rule UID is assigned to its seed only when its rule index was created during that seed manifest load interval. Bootstrap and post-seed runtime rules are separately labeled. Observed access counts describe one current-source fixture and do not establish necessity or causal contribution.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'top_seeds':out['rule_access_events_by_source'][:12],'unassigned_uid_count':len(unassigned),'top_rules':observed_rules[:15]},indent=2))
if not checks['integrity_gates_pass']:raise SystemExit('seed rule provenance integrity audit failed')
