#!/usr/bin/env python3
"""Independent gate checks for production-derived thoughtexperiment diagnosis."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_production_rule_diagnosis_v1_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_production_rule_diagnosis_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_production_rule_diagnosis_v1.py';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];iso=d['isolated'];arms=lock['arms']
 checks={'schema':d['schema']=='ThoughtexperimentProductionRuleDiagnosisV1','lock_sha':d['lock_sha256']==sha(LOCK),'workers_source_locked':len(workers)==3 and len({w['pid'] for w in workers})==3 and all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'isolated_source_locked':len(iso)==12 and len({x['pid'] for x in iso})==12 and all(x['sources_before']==x['sources_after']==lock['sources'] for x in iso),'runner_analyzer_hash':lock['sources']['files'][str(RUNNER.relative_to(ROOT))]==sha(RUNNER) and lock['sources']['files'][str(ANALYZER.relative_to(ROOT))]==sha(ANALYZER)}
 checks['exact_arm_matrix']=all({r['arm'] for r in w['rows']}==set(arms) for w in workers) and len(iso)==3*len(arms)
 allrows=[r for w in workers for r in w['rows']]+iso
 checks['all_arms_cure_fault']=all(r['found']==2 and r['attempts']>0 and r['outcomes'][-1]['cured'] and r['fault_effect_index']==2 for r in allrows)
 checks['cured_graphs_exactly_match']=len({r['cured_graph_digest'] for r in allrows})==1 and all(r['outcomes'][-1]['healthy_survivors'] for r in allrows)
 checks['all_primary_graphs_isolated']=all(r['primary_unchanged'] for r in allrows)
 checks['report_fixedpoint']=all(r['status']=='fixed_point' and r['progress_steps']==1 for r in allrows)
 checks['target_arm_has_only_targets']=all(r['arm']!='target_trace' or (r['effect_value_bytes']==0 and r['effect_snapshot_objects']>=5) for r in allrows)
 checks['value_arm_has_value_receipts']=all(r['arm']!='value_trace' or (r['effect_value_bytes']>0 and r['effect_snapshot_objects']>=5) for r in allrows)
 checks['value_trace_single_candidate']=all(r['candidates']==[2] and r['attempts']==1 for r in allrows if r['arm']=='value_trace')
 checks['full_rematch_has_one_guarded_binding']=all(r['rematch_matches']==1 and r['candidates']==list(range(7)) for r in allrows if r['arm']=='endpoint_rematch')
 checks['candidate_sets_replicate']=all({r['arm']:r['candidates'] for r in w['rows']}=={r['arm']:r['candidates'] for r in workers[0]['rows']} for w in workers[1:])
 costs={}
 for arm in arms:
  rows=[r for r in iso if r['arm']==arm];costs[arm]={'median_total_wall_ms':statistics.median(r['wall_ns'] for r in rows)/1e6,'median_total_cpu_ms':statistics.median(r['cpu_ns'] for r in rows)/1e6,'median_branch_attempts':statistics.median(r['attempts'] for r in rows),'median_report_json_bytes':statistics.median(r['report_json_bytes'] for r in rows),'median_report_events':statistics.median(r['report_event_count'] for r in rows)}
 out={'schema':'ThoughtexperimentProductionRuleDiagnosisV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'costs':costs,'claim_limit':'One exact production seed rule is used in an authored one-binding graph with a single fault-injected outcome. This does not establish diagnosis prevalence, deferred-queue behavior, general self-repair, or natural-task utility.'}
 (ROOT/'evaluation/reports/thoughtexperiment_production_rule_diagnosis_v1_analysis_20261005.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'costs':costs},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
