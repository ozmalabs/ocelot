#!/usr/bin/env python3
"""Independently compare restored per-store work with live counters."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAP=ROOT/'evaluation/reports/live_runtime_store_replay_v1_20261004.json';OUT=ROOT/'evaluation/reports/live_runtime_store_replay_v1_analysis_20261004.json'
def main():
 cap=json.loads(CAP.read_text());rows=[];errors=[]
 for r in cap.get('runs',[]):
  exp=r.get('expected_per_rule',{});got=r.get('replay_per_rule',{});metrics=sorted({m for slot in exp.values() for m in slot}|{m for slot in got.values() for m in slot});
  metric_rows=[]
  for m in metrics:
   e=sum(int(v.get(m,0)) for v in exp.values());g=sum(int(v.get(m,0)) for v in got.values());metric_rows.append({'metric':m,'live':e,'replay':g,'delta':g-e,'exact':g==e})
  ekeys={(int(i),m) for i,v in exp.items() for m in v};gkeys={(int(i),m) for i,v in got.items() for m in v};union=ekeys|gkeys;exact_keys=sum(1 for i,m in union if int(exp.get(str(i),exp.get(i,{})).get(m,0))==int(got.get(str(i),got.get(i,{})).get(m,0)))
  row={'request':r.get('request'),'store_id':r.get('store_id'),'restore_ok':r.get('graph_roundtrip') is True and r.get('rule_roundtrip') is True and r.get('indices_contiguous') is True,'rule_count':r.get('rule_count'),'live_active_rules':len(exp),'replay_active_rules':len(got),'live_metric_cells':len(ekeys),'replay_metric_cells':len(gkeys),'metric_union_cells':len(union),'exact_metric_cells':exact_keys,'exact_metric_cell_fraction':(exact_keys/len(union) if union else 1.0),'candidate_tests':next((x for x in metric_rows if x['metric']=='candidate_tests'),None),'term_evaluations':next((x for x in metric_rows if x['metric']=='term_evaluations'),None),'rule_enumerations':next((x for x in metric_rows if x['metric']=='rule_enumerations'),None),'metric_rows':metric_rows,'replay_calls':r.get('replay_calls'),'elapsed_s':r.get('elapsed_s'),'error':r.get('error')}
  rows.append(row)
 checks={'14_store_rows':len(rows)==14,'all_restore_roundtrips':all(x['restore_ok'] for x in rows),'capture_source_stable':cap.get('source_stable') is True,'per_store_counter_exact':all(x['exact_metric_cell_fraction']==1 for x in rows)}
 result={'schema':'LiveRuntimeStoreReplayV1Analysis','checks':checks,'replay_procedure_passed':all(checks[k] for k in ('14_store_rows','all_restore_roundtrips','capture_source_stable')),'exact_per_store_counter_replay':checks['per_store_counter_exact'],'rows':rows,'all_store_metric_cells':sum(x['metric_union_cells'] for x in rows),'overall_exact_metric_cell_fraction':sum(x['exact_metric_cells'] for x in rows)/max(1,sum(x['metric_union_cells'] for x in rows)),'claim_limit':cap.get('claim_limit')}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'replay_procedure_passed':result['replay_procedure_passed'],'exact_per_store_counter_replay':result['exact_per_store_counter_replay'],'overall_exact_metric_cell_fraction':result['overall_exact_metric_cell_fraction'],'restore_failures':sum(not x['restore_ok'] for x in rows),'stores':len(rows)}));return 0 if result['replay_procedure_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
