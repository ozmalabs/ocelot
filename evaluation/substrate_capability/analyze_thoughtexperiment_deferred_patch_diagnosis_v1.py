#!/usr/bin/env python3
"""Independent queue-origin, diagnosis, parity, isolation, and cost gates."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_deferred_patch_diagnosis_v1_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_patch_diagnosis_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_deferred_patch_diagnosis_v1.py';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());workers=d['workers'];iso=d['isolated'];arms=lock['arms']
 checks={'schema':d['schema']=='ThoughtexperimentDeferredPatchDiagnosisV1','lock_sha':d['lock_sha256']==sha(LOCK),'workers_locked':len(workers)==3 and len({w['pid'] for w in workers})==3 and all(w['sources_before']==w['sources_after']==lock['sources'] for w in workers),'isolated_locked':len(iso)==12 and len({x['pid'] for x in iso})==12 and all(x['sources_before']==x['sources_after']==lock['sources'] for x in iso),'runner_analyzer_hash':lock['sources']['files'][str(RUNNER.relative_to(ROOT))]==sha(RUNNER) and lock['sources']['files'][str(ANALYZER.relative_to(ROOT))]==sha(ANALYZER)}
 maps=[{r['arm']:r for r in w['rows']} for w in workers];allrows=[r for m in maps for r in m.values()]+iso
 checks['arm_matrix']=all(set(m)==set(arms) for m in maps) and len(iso)==3*len(arms)
 checks['deferred_stale_receipt']=all(r['patch_status']=='refused' and r['patch_reason']=='stale_revision' and r['deferred_event_count']==1 for r in allrows)
 checks['all_arms_cure_and_preserve_survivors']=all(r['found']==3 and r['outcomes'][-1]['cured'] and r['outcomes'][-1]['healthy_survivors'] for r in allrows)
 checks['exact_cured_graph_parity']=len({r['cured_graph_digest'] for r in allrows})==1
 checks['primary_isolation']=all(r['primary_unchanged'] for r in allrows)
 checks['fixed_point']=all(r['status']=='fixed_point' for r in allrows)
 checks['rematcher_unique_binding']=all(r['rematch_matches']==1 and r['candidates']==[2,3,5] for r in allrows if r['arm']=='endpoint_rematch')
 checks['target_origin_and_write_attribution']=all(r['deferred_effect_origins']==[{'effect_index':3,'rule_name':'sc_canary_requests_commit'}] and any(x['effect_index']==3 and x['node_ids'] and not x['node_values'] and not x['edge_values'] for x in r['deferred_effect_snapshots']) and r['effect_value_bytes']==0 for r in allrows if r['arm']=='target_trace')
 checks['value_transition_attribution']=all(r['deferred_effect_origins']==[{'effect_index':3,'rule_name':'sc_canary_requests_commit'}] and any(x['effect_index']==3 and any(n['before']['attrs'].get('status')=='pending' and n['after']['attrs'].get('status')=='refused' for n in x['node_values']) for x in r['deferred_effect_snapshots']) and r['candidates']==[3] and r['attempts']==1 for r in allrows if r['arm']=='value_trace')
 checks['target_trace_uses_deferred_origin_first']=all(r['candidates']==[3,2,5] and r['attempts']==1 and r['found']==3 for r in allrows if r['arm']=='target_trace')
 checks['blind_search_reference']=all(r['candidates']==list(range(7)) and r['attempts']==4 for r in allrows if r['arm']=='endpoint_blind')
 checks['worker_candidate_parity']=all({a:maps[i][a]['candidates'] for a in arms}=={a:maps[0][a]['candidates'] for a in arms} for i in (1,2))
 stats={}
 for arm in arms:
  rs=[r for r in iso if r['arm']==arm];stats[arm]={'median_wall_ms':statistics.median(r['wall_ns'] for r in rs)/1e6,'median_cpu_ms':statistics.median(r['cpu_ns'] for r in rs)/1e6,'median_branches':statistics.median(r['attempts'] for r in rs),'median_report_bytes':statistics.median(r['report_json_bytes'] for r in rs)}
 out={'schema':'ThoughtexperimentDeferredPatchDiagnosisV1Analysis','capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'checks':checks,'passed':all(checks.values()),'costs':stats,'claim_limit':'One production seed rule and one authored stale-patch fixture establish bounded attribution across one deferred queue. They do not establish multi-origin behavior, other deferred queues, natural task frequency, or general self-repair.'}
 (ROOT/'evaluation/reports/thoughtexperiment_deferred_patch_diagnosis_v1_analysis_20261005.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'costs':stats},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
