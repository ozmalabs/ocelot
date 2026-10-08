#!/usr/bin/env python3
"""Independent per-rule reconciliation for primary closure-entry replay."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAP=ROOT/'evaluation/reports/live_runtime_closure_entry_states_v3_20261004.json';REPLAY=ROOT/'evaluation/reports/live_runtime_closure_entry_replay_v5_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_closure_entry_replay_v5_analysis_20261004.json'
def main():
 cap=json.loads(CAP.read_text());replay=json.loads(REPLAY.read_text());requests=[]
 for req_i in (1,2):
  obs=cap['native_counter_observations'][req_i-1]['counter_rows'];ids={int(a):(int(s),int(i)) for a,s,i in obs['identities']};expected={}
  for aid,metric,count in obs['per_rule']:
   identity=ids.get(int(aid))
   if identity and identity[0]==1:expected.setdefault(identity[1],{})[str(metric)]=int(count)
  actual={int(i):{str(m):int(v) for m,v in row.items()} for i,row in replay['requests'][req_i-1]['aggregate_per_rule'].items()}
  keys={(i,m) for i,row in expected.items() for m in row}|{(i,m) for i,row in actual.items() for m in row};diff=[]
  for i,m in sorted(keys):
   e=int(expected.get(i,{}).get(m,0));a=int(actual.get(i,{}).get(m,0))
   if e!=a:diff.append({'local_rule_index':i,'metric':m,'live':e,'replay':a,'delta':a-e})
  totals={}
  for metric in ('candidate_tests','candidate_pairs','term_evaluations','rule_enumerations','where_evaluations','where_rejections'):
   e=sum(int(row.get(metric,0)) for row in expected.values());a=sum(int(row.get(metric,0)) for row in actual.values());totals[metric]={'live':e,'replay':a,'delta':a-e,'exact':e==a}
  requests.append({'request':req_i,'live_active_rules':len(expected),'replayed_active_rules':len(actual),'live_metric_cells':sum(len(x) for x in expected.values()),'replay_metric_cells':sum(len(x) for x in actual.values()),'union_metric_cells':len(keys),'exact_metric_cells':len(keys)-len(diff),'exact_metric_cell_fraction':(len(keys)-len(diff))/max(1,len(keys)),'metric_totals':totals,'differing_cells':len(diff),'largest_absolute_differences':sorted(diff,key=lambda x:abs(x['delta']),reverse=True)[:20],'per_rule_differences':diff})
 checks={'both_requests':len(requests)==2,'all_calls_replayed':replay.get('all_calls_replayed') is True,'source_stable':replay.get('source_stable') is True,'parent_capture_valid':cap.get('source_stable') is True and all(cap.get('parent_parity',{}).values())}
 exact=all(r['differing_cells']==0 for r in requests);result={'schema':'LiveRuntimeClosureEntryReplayV5Analysis','checks':checks,'replay_procedure_passed':all(checks.values()),'exact_primary_counter_replay':exact,'requests':requests,'total_metric_cells':sum(x['union_metric_cells'] for x in requests),'exact_metric_cells':sum(x['exact_metric_cells'] for x in requests),'overall_exact_metric_cell_fraction':sum(x['exact_metric_cells'] for x in requests)/max(1,sum(x['union_metric_cells'] for x in requests)),'claim_limit':replay.get('claim_limit')}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'replay_procedure_passed':result['replay_procedure_passed'],'exact_primary_counter_replay':exact,'cell_fraction':result['overall_exact_metric_cell_fraction'],'requests':[{'request':x['request'],'cells':x['exact_metric_cells'],'union':x['union_metric_cells'],'totals':x['metric_totals']} for x in requests]}));return 0 if result['replay_procedure_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
