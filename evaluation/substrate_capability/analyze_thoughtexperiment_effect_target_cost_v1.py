#!/usr/bin/env python3
"""Verify parity, target attribution, source lock, truncation and cost summaries."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_effect_target_cost_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_target_cost_v1_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_effect_target_cost_v1.py'
ANALYZER=Path(__file__).resolve()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(CAPTURE.read_text()); lock=json.loads(LOCK.read_text()); ws=d['workers']; iso=d['isolated']; modes=lock['modes']; fixtures=lock['fixtures']
 checks={
  'schema':d['schema']=='ThoughtexperimentEffectTargetCostV1',
  'capture_lock':d['lock_sha256']==sha(LOCK),
  'workers_source_locked':len(ws)==3 and len({w['pid'] for w in ws})==3 and all(w['sources_before']==w['sources_after']==lock['sources'] for w in ws),
  'isolated_source_locked':len(iso)==27 and len({x['pid'] for x in iso})==27 and all(x['sources_before']==x['sources_after']==lock['sources'] for x in iso),
  'runner_analyzer_hashes':lock['sources']['files'][str(RUNNER.relative_to(ROOT))]==sha(RUNNER) and lock['sources']['files'][str(ANALYZER.relative_to(ROOT))]==sha(ANALYZER),
 }
 maps=[{(r['fixture'],r['mode']):r for r in w['rows']} for w in ws]
 checks['matrix_complete']=all(set(m)=={(f,x) for f in fixtures for x in modes} for m in maps)
 checks['cross_mode_graph_parity']=all(len({m[(f,x)]['semantic']['graph_sha256'] for x in modes})==1 for i,m in enumerate(maps) for f in fixtures)
 checks['worker_replicate_parity']=all(maps[0][k]['semantic']==maps[i][k]['semantic'] for i in (1,2) for k in maps[0])
 checks['isolated_worker_parity']=all(list(x['semantic'])==[maps[0][(x['fixture'],x['mode'])]['semantic'][k] for k in ('status','progress_steps','passes_completed')] for x in iso)
 target_rows=[r for r in maps[0].values() if r['mode']=='targets']
 snaps=[e for r in target_rows for ev in r['events'] for e in ev.get('effect_snapshots',[])]
 checks['target_mode_has_indexed_locations']=bool(snaps) and sum(len(e.get('node_ids',[]))+len(e.get('edges',[])) for e in snaps)>0
 checks['target_mode_has_no_values']=bool(snaps) and all(not e.get('node_values') and not e.get('edge_values') for e in snaps)
 checks['target_mode_zero_value_payload']=all(r['effect_snapshot_bytes']==0 for r in target_rows)
 checks['multiwrite_effect_partition']=sorted((e['effect_index'],bool(e.get('node_ids')),bool(e.get('edges'))) for ev in maps[0][('same_event_multiwrite','targets')]['events'] for e in ev.get('effect_snapshots',[]) if e.get('node_ids') or e.get('edges'))==[(0,True,False),(1,True,False),(2,False,True)]
 cap=maps[0][('report_object_cap','targets')]
 checks['target_cap_bounded_and_visible']=cap['effect_snapshot_objects']<=cap['effect_snapshot_budget_objects'] and cap['effect_truncated']>0
 stats={}
 for f in fixtures:
  stats[f]={}
  for mode in modes:
   rows=[x for x in iso if x['fixture']==f and x['mode']==mode]
   stats[f][mode]={'median_wall_ms':statistics.median(x['wall_ns'] for x in rows)/1e6,'median_cpu_ms':statistics.median(x['cpu_ns'] for x in rows)/1e6,'median_rss_delta_kib':statistics.median(x['rss_delta_kib'] for x in rows),'median_pss_delta_kib':statistics.median(x['pss_delta_kib'] for x in rows),'median_event_json_mib':statistics.median(x['event_json_bytes'] for x in rows)/1048576,'median_effect_value_bytes':statistics.median(x['effect_snapshot_bytes'] for x in rows),'median_effect_objects':statistics.median(x['effect_snapshot_objects'] for x in rows),'median_target_ids':statistics.median(x['effect_target_ids'] for x in rows)}
 out={'schema':'ThoughtexperimentEffectTargetCostV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'costs':stats,'claim_limit':'This source-locked comparison uses three authored observer fixtures and isolated processes; it does not establish natural-task prevalence or thoughtexperiment capability.'}
 dest=ROOT/'evaluation/reports/thoughtexperiment_effect_target_cost_v1_analysis_20261005.json'; dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'passed':out['passed'],'checks':checks,'costs':stats},indent=2)); return 0 if out['passed'] else 2
if __name__=='__main__': raise SystemExit(main())
