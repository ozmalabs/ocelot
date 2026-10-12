#!/usr/bin/env python3
"""Compare pre-call dirty counts with same-request scheduler selections."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAP=ROOT/'evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_dirty_rule_entry_audit_v1_analysis_20261004.json'
def main():
 cap=json.loads(CAP.read_text());rows=[]
 for req_i,(req,work) in enumerate(zip(cap['requests'],cap['work_rows']),1):
  selected=[int(x['value']) for x in work if x['name']=='scheduler_selected_rules'];passes=[int(x['value']) for x in work if x['name']=='scheduler_pass'];calls=req['calls'];pairs=[]
  for i,call in enumerate(calls):pairs.append({'call_index':i,'dirty_rule_count':call['dirty_rule_count'],'scheduler_selected_rules':selected[i] if i<len(selected) else None,'difference':call['dirty_rule_count']-selected[i] if i<len(selected) else None,'dirty_names_mapped':len(call['dirty_rule_local_indices']),'ambiguous_names':len(call['ambiguous_names'])})
  rows.append({'request':req_i,'calls':len(calls),'scheduler_selection_rows':len(selected),'dirty_count_equals_selected_count':len(calls)==len(selected) and all(x['difference']==0 for x in pairs),'all_dirty_names_mapped':all(not x['ambiguous_names'] and x['dirty_names_mapped']==x['dirty_rule_count'] for x in calls),'scheduler_passes':passes,'pairs':pairs})
 checks={'two_requests':len(rows)==2,'route_parity':all(cap.get('parent_parity',{}).values()),'source_stable':cap.get('source_stable') is True,'call_counts_align':all(x['calls']==x['scheduler_selection_rows'] for x in rows)}
 result={'schema':'LiveRuntimeDirtyRuleEntryAuditV1Analysis','checks':checks,'passed':all(checks.values()),'dirty_counts_explain_selections':all(x['dirty_count_equals_selected_count'] for x in rows),'dirty_names_map_to_slots':all(x['all_dirty_names_mapped'] for x in rows),'requests':rows}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'dirty_counts_explain_selections':result['dirty_counts_explain_selections'],'dirty_names_map_to_slots':result['dirty_names_map_to_slots'],'pairs':[x['pairs'] for x in rows]}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
