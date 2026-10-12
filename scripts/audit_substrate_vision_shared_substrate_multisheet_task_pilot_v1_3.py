#!/usr/bin/env python3
"""Independent audit of the completed v1.3 two-sheet capture.

Recomputes the manifest-tag gate correctly: a seed with zero executable rules
has zero rules to tag, rather than failing a positive-count requirement.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
RAW=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_3_audit_20260927.json'
TOL=1e-10
SEEDS=('vision_waves','vision_settle','vision_onoff','vision_lateral','vision_compose')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def osi(curve):
 x=np.asarray(curve,dtype=float);j=int(np.argmax(x));jo=(j+len(x)//2)%len(x);den=x[j]+x[jo]
 return float((x[j]-x[jo])/den) if den>1e-9 else 0.0
def maxdelta(a,b):return float(np.max(np.abs(np.asarray(a,dtype=float)-np.asarray(b,dtype=float))))
def main():
 from substrate.seed_loader import manifest_for
 expected={sid:sum(1 for r in manifest_for(sid).get('rules',[]) if 'match' in r) for sid in SEEDS}
 d=json.loads(RAW.read_text());scopes=d['worker']['scopes'];by={(s['scope'],c['context']):c for s in scopes for c in s['contexts']}
 scope_delta={s:maxdelta(by[(s,'blank')]['tuning'],by[(s,'grating')]['tuning']) for s in ('global','root_scoped')}
 replay_delta={s:maxdelta(by[(s,'blank')]['tuning'],by[(s,'blank_replay')]['tuning']) for s in ('global','root_scoped')}
 osi_ok=all(np.allclose(c['osi_per_unit'],[osi(row) for row in c['tuning']],atol=TOL,rtol=0) for c in by.values())
 topology=[];work_rows=0;retry_rows=[];work_ok=True
 for s in scopes:
  t=s['topology'];tag_counts=t['manifest_tag_counts'];members=t['root_membership_counts'];units=t['unit_ids'];roots=t['retina_ids']
  topology.append({'scope':s['scope'],'root_membership_counts':members,'retina_count':len(set(roots)),'unit_count_per_root':[len(v) for v in units],
   'unit_roots_disjoint':not (set(units[0])&set(units[1])),'singleton_counts':t['singleton_counts'],
   'manifest_executable_counts':expected,'manifest_tag_counts':tag_counts,
   'manifest_tag_counts_match_executable_rules':tag_counts==expected,
   'selected_rule_latency_classes':t['selected_rule_latency_classes']})
  records=s['presentation_work'];work_rows+=len(records)
  retry_rows.extend({'scope':s['scope'],**r} for r in records if r['intermediate_budget_hits'])
  work_ok &= len(records)==3440 and all(r['final_status'] in ('fixed_point','repeated_graph_state') and r['cumulative_progress']<=1_600_000 and r['attempt_count']==r['intermediate_budget_hits']+1 for r in records)
 checks={
  'capture_source_stable':d['checks']['source_stable'] and d['checks']['native_source_matches'],
  'both_scope_captures_complete':set(by)=={(s,c) for s in ('global','root_scoped') for c in ('blank','blank_replay','grating')},
  'two_full_disjoint_roots_and_singletons':all(x['root_membership_counts']==[16,16] and x['retina_count']==2 and x['unit_count_per_root']==[16,16] and x['unit_roots_disjoint'] and all(v==1 for v in x['singleton_counts'].values()) for x in topology),
  'all_executable_rules_tagged':all(x['manifest_tag_counts_match_executable_rules'] and all(v=='hard_realtime' for v in x['selected_rule_latency_classes'].values()) for x in topology),
  'development_and_calibration_valid':all(s['development_end_steps']==[3000.0,3000.0] and min(s['retinal_channel_activity_after_adaptation'].values())>0 and all(np.max(np.abs(g))>0.01 for g in s['calibration_gains'].values()) for s in scopes),
  'batch_frame_writes_equivalent':all(s['batch_writer_scalar_equivalence'] for s in scopes),
  'all_presentations_terminal_under_registered_bound':work_ok,
  'response_curves_finite_nonzero_16_by_12':all(np.asarray(c['tuning']).shape==(16,12) and np.isfinite(c['tuning']).all() and np.max(c['tuning'])>0 for c in by.values()),
  'osi_independently_recomputed':osi_ok,
  'blank_restore_replay_exact':all(v==0.0 for v in replay_delta.values()),
  'readout_weights_unchanged':all(c['readout_weight_max_abs_delta']==0.0 and c['readout_weight_before']==c['readout_weight_after'] for c in by.values()),
  'B_input_and_retinal_channels_verified':all(by[(s,'blank')]['b_frame_active_pixels']==0 and by[(s,'grating')]['b_frame_active_pixels']==128 and by[(s,'grating')]['b_bursting_after_readout']==128 and min(next(x for x in scopes if x['scope']==s)['retinal_channel_activity_after_adaptation'][k] for k in ('B_on','B_off'))>0 for s in ('global','root_scoped')),
  'root_scoped_A_response_invariant':scope_delta['root_scoped']<=TOL,
  'global_scope_A_response_changes_with_B':scope_delta['global']>1e-8,
 }
 # The last item is an outcome prediction, not a fixture-validity condition.
 fixture_checks={k:v for k,v in checks.items() if k!='global_scope_A_response_changes_with_B'}
 result={'schema_version':1,'run_id':'vision-shared-substrate-multisheet-task-pilot-v1.3-independent-audit-20260927',
  'raw_sha256':sha(RAW),'locked_runner_sha256':d['locked_inputs']['runner_sha256'],'locked_analyzer_sha256':d['locked_inputs']['analyzer_sha256'],
  'legacy_driver_gate_issue':'The captured driver used all(manifest_tag_counts.values() > 0), which falsely rejects vision_compose (zero rules with a match field). Independent source check confirms zero executable vision_compose rules and exact tag-count equality for every seed.',
  'manifest_executable_counts':expected,'topology_audit':topology,'checks':checks,'fixture_valid':all(fixture_checks.values()),
  'task_contrast':{'global_A_tuning_max_abs_delta_blank_vs_B_grating':scope_delta['global'],'root_scoped_A_tuning_max_abs_delta_blank_vs_B_grating':scope_delta['root_scoped'],
   'global_interference_prediction_supported':checks['global_scope_A_response_changes_with_B'],'interpretation':'No A tuning change was detected in either scope when B received the registered grating. This is a negative result for the predicted global-versus-root-scoped interference contrast on this fixture; it does not establish general scope safety.'},
  'blank_replay_max_abs_delta':replay_delta,'work_audit':{'presentation_records':work_rows,'budget_retry_events':retry_rows,'max_cumulative_progress':max((x['cumulative_progress'] for s in scopes for x in s['presentation_work']),default=0)},
  'limitations':['B retinal ON/OFF channels and actual B retinal input bursts were verified, but B SUnit response was not separately measured.','One seed and one two-sheet vision fixture; no prevalence or general scope-safety claim.','The run is valid for independent audit but the legacy driver pass bit is false due solely to the zero-rule manifest gate; preserve that original raw field.'],
  'pass_fixture_audit':all(fixture_checks.values()),'pass_task_prediction':checks['global_scope_A_response_changes_with_B']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'fixture_valid':result['fixture_valid'],'task_contrast':result['task_contrast'],'work_audit':result['work_audit'],'checks':checks},indent=2))
 if not result['fixture_valid']:raise SystemExit('independent v1.3 fixture audit failed')
if __name__=='__main__':main()
