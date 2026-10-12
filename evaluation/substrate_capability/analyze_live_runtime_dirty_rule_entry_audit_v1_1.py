#!/usr/bin/env python3
"""Amended per-call dirty-count alignment with scheduler pass counts."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAP=ROOT/'evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_20261004.json';CAP_LOCK=ROOT/'evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1_lock_20261004.json';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_DIRTY_RULE_ENTRY_AUDIT_V1_1_AMENDMENT_20261004.md';RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/live_runtime_dirty_rule_entry_audit_v1_1_analysis_lock_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_1_analysis_20261004.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs():return {'protocol_sha256':sha(PROTOCOL),'analyzer_sha256':sha(RUNNER),'capture_sha256':sha(CAP),'capture_lock_sha256':sha(CAP_LOCK)}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite dirty-rule amendment')
  LOCK.write_text(json.dumps({'schema':'LiveRuntimeDirtyRuleEntryAuditV1_1AnalysisLock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale amendment analysis lock')
 cap=json.loads(CAP.read_text());rows=[];errors=[]
 for req_i,(req,work) in enumerate(zip(cap.get('requests',[]),cap.get('work_rows',[])),1):
  selected=[r for r in work if r['name']=='scheduler_selected_rules'];passes={int(r['operation_id']):int(r['value']) for r in work if r['name']=='scheduler_pass'};pairs=[]
  for i,call in enumerate(req.get('calls',[])):
   if i>=len(selected):errors.append(f'missing selected row request={req_i} call={i}');continue
   s=selected[i];n=int(s['value']);p=passes.get(int(s['operation_id']));dirty=int(call['dirty_rule_count']);names=len(call.get('dirty_rule_names',[]));mapped=len(call.get('dirty_rule_local_indices',[]));ambiguous=len(call.get('ambiguous_names',[]))
   pairs.append({'call_index':i,'operation_id':s['operation_id'],'scheduler_passes':p,'entry_dirty_rule_count':dirty,'entry_dirty_name_rows':names,'mapped_local_slots':mapped,'ambiguous_name_rows':ambiguous,'scheduler_selected_rules':n,'later_pass_selections':n-dirty,'first_pass_count_exact':(p==1 and n==dirty),'later_pass_selection_nonnegative':(p==2 and n>=dirty),'dirty_names_partition_count':mapped+ambiguous==dirty})
  rows.append({'request':req_i,'call_count':len(req.get('calls',[])),'selection_count':len(selected),'all_dirty_name_rows_equal_count':all(x['entry_dirty_name_rows']==x['entry_dirty_rule_count'] for x in pairs),'all_dirty_names_partitioned':all(x['dirty_names_partition_count'] for x in pairs),'single_pass_calls_match_entry_dirty_count':all(x['first_pass_count_exact'] for x in pairs if x['scheduler_passes']==1),'two_pass_calls_explain_excess_as_later_pass_selection':all(x['later_pass_selection_nonnegative'] for x in pairs if x['scheduler_passes']==2),'later_pass_selections_total':sum(x['later_pass_selections'] for x in pairs if x['scheduler_passes']==2),'pairs':pairs})
 parity=cap.get('parent_parity',{});checks={'two_requests':len(rows)==2,'source_stable':cap.get('source_stable') is True,'parent_parity':all(parity.values()) and len(parity)==4,'call_selection_rows_align':all(x['call_count']==x['selection_count'] for x in rows),'dirty_names_rows_count':all(x['all_dirty_name_rows_equal_count'] for x in rows),'dirty_names_partitioned':all(x['all_dirty_names_partitioned'] for x in rows),'first_pass_dirty_selection_exact':all(x['single_pass_calls_match_entry_dirty_count'] for x in rows),'later_pass_excess_explained':all(x['two_pass_calls_explain_excess_as_later_pass_selection'] for x in rows),'analysis_source_stable':locked==inputs()}
 result={'schema':'LiveRuntimeDirtyRuleEntryAuditV1_1Analysis','locked_inputs':locked,'post_run_inputs':inputs(),'checks':checks,'passed':all(checks.values()),'requests':rows,'later_pass_selected_rule_rows_total':sum(x['later_pass_selections_total'] for x in rows),'claim_limit':'dirty rule bits explain first-pass selected counts; this does not capture dirty-node sets, cursor/cache state, mutation protection, or make the replay complete'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'later_pass_selections':[x['later_pass_selections_total'] for x in rows]}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
