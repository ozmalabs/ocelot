#!/usr/bin/env python3
"""Independent parity, source-lock, cap, and cost analysis."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_event_effect_cost_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_effect_cost_v1_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_effect_cost_v1.py'
LOCKED_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_event_effect_cost_v1.py'
ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];iso=d['isolated'];modes=lock['modes'];fixtures=lock['fixtures']
 checks={'schema':d['schema']=='ThoughtexperimentEventEffectCostV1','lock_hash':d['lock_sha256']==sha(LOCK),'three_locked_workers':len(workers)==3 and len({w['pid'] for w in workers})==3 and all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'isolated_arms_locked':len(iso)==45 and len({x['pid'] for x in iso})==45 and all(x['sources_before']==x['sources_after']==lock['sources'] for x in iso),'runner_and_analyzer_match_lock':lock['sources']['files'][str(RUNNER.relative_to(ROOT))]==sha(RUNNER) and lock['sources']['files'][str(LOCKED_ANALYZER.relative_to(ROOT))]==sha(LOCKED_ANALYZER) and sha(LOCKED_ANALYZER)==json.loads(LOCK.read_text())['sources']['files'][str(LOCKED_ANALYZER.relative_to(ROOT))]}
 by_worker=[{(r['fixture'],r['mode']):r for r in w['rows']} for w in workers]
 checks['exact_fixture_mode_matrix']=all(set(x)=={(f,m) for f in fixtures for m in modes} for x in by_worker)
 checks['worker_semantics_replicate']=all(by_worker[0][k]['semantic']==by_worker[i][k]['semantic'] for i in (1,2) for k in by_worker[0])
 checks['mode_final_graph_parity']=all(len({by_worker[w][(f,m)]['semantic']['graph_sha256'] for m in modes})==1 for w in range(3) for f in fixtures)
 multi=by_worker[0][('same_event_multiwrite','effects')]['events'];event_only=by_worker[0][('same_event_multiwrite','events')]['events'];combined=by_worker[0][('same_event_multiwrite','combined')]['events']
 e=next((x for x in multi if x['rule_name']=='multiwrite_then_remove'),None)
 effects=e.get('effect_snapshots',[]) if e else []
 chain=[(x['effect_index'],n['before']['attrs'].get('value'),n['after']['attrs'].get('value')) for x in effects for n in x.get('node_values',[]) if n['before'] and n['after']]
 deletions=[(x['effect_index'],edge['before'],edge['after']) for x in effects for edge in x.get('edge_values',[])]
 checks['event_only_disables_effect_values']=bool(event_only) and all(not x.get('effect_snapshots') for x in event_only)
 checks['effect_trace_transition_chain']=chain==[(0,0,1),(1,1,2)]
 checks['effect_trace_edge_deletion']=deletions==[(2,{},None)] and all(not x.get('values_truncated',True) for x in effects)
 checks['combined_effect_trace_matches_effect_mode']=combined==multi
 checks['whole_event_still_reports_endpoints']=bool(e and [(n['before']['attrs'].get('value'),n['after']['attrs'].get('value')) for n in e['node_values'] if n['before'] and n['after']]==[(0,2)])
 caps=[by_worker[0][('report_object_cap',m)] for m in ('events','effects','combined')]
 checks['event_mode_effect_cost_zero']=all(x['effect_snapshot_bytes']==x['effect_snapshot_objects']==0 for x in caps if x['mode']=='events')
 eff=by_worker[0][('report_object_cap','effects')]
 checks['effect_cap_respected_and_truncation_visible']=eff['effect_snapshot_bytes']<=eff['effect_snapshot_budget_bytes'] and eff['effect_snapshot_objects']<=eff['effect_snapshot_budget_objects'] and eff['effect_truncated']>0
 checks['isolated_semantics_match_workers']=all(x['semantic']==[by_worker[0][(x['fixture'],x['mode'])]['semantic'][k] for k in ('status','progress_steps','passes_completed')] for x in iso)
 stats={}
 for f in fixtures:
  stats[f]={}
  for m in modes:
   cells=[x for x in iso if x['fixture']==f and x['mode']==m]
   stats[f][m]={'median_wall_ms':statistics.median(x['wall_ns'] for x in cells)/1e6,'median_cpu_ms':statistics.median(x['cpu_ns'] for x in cells)/1e6,'median_rss_delta_kib':statistics.median(x['rss_delta_kib'] for x in cells),'median_pss_delta_kib':statistics.median(x['pss_delta_kib'] for x in cells),'median_event_json_mib':statistics.median(x['event_json_bytes'] for x in cells)/1048576,'median_effect_payload_bytes':statistics.median(x['effect_snapshot_bytes'] for x in cells),'median_effect_objects':statistics.median(x['effect_snapshot_objects'] for x in cells)}
 out={'schema':'ThoughtexperimentEventEffectCostV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(LOCKED_ANALYZER),'correction_analyzer_sha256':sha(ANALYZER),'checks':checks,'passed':all(checks.values()),'costs':stats,'effect_over_event_cost':{f:{'median_wall_ratio':stats[f]['effects']['median_wall_ms']/max(stats[f]['events']['median_wall_ms'],1e-9),'median_rss_delta_difference_kib':stats[f]['effects']['median_rss_delta_kib']-stats[f]['events']['median_rss_delta_kib'],'median_pss_delta_difference_kib':stats[f]['effects']['median_pss_delta_kib']-stats[f]['events']['median_pss_delta_kib']} for f in fixtures},'claim_limit':'Effect and endpoint observers are compared on three authored fixtures in isolated processes under an opt-level 3, non-LTO, 16-codegen-unit build. These measurements do not establish natural-task prevalence, general tractability, or diagnosis utility.'}
 dest=ROOT/'evaluation/reports/thoughtexperiment_event_effect_cost_v1_analysis_correction_20261005.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'costs':stats},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
