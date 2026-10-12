#!/usr/bin/env python3
"""Independent analysis of the v1.4 paired A-task and B-stack readouts."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_4_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_4_analysis_20260927.json'
TOL=1e-10
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def osi(curve):
 x=np.asarray(curve,dtype=float);j=int(np.argmax(x));jo=(j+len(x)//2)%len(x);den=x[j]+x[jo]
 return float((x[j]-x[jo])/den) if den>1e-9 else 0.0
def delta(a,b):return float(np.max(np.abs(np.asarray(a,dtype=float)-np.asarray(b,dtype=float))))
def main():
 d=json.loads(RAW.read_text());scopes=d['worker']['scopes'];by={(s['scope'],c['context']):c for s in scopes for c in s['contexts']}
 contexts={(s,c) for s in ('global','root_scoped') for c in ('blank','blank_replay','grating')}
 a_delta={s:delta(by[(s,'blank')]['tuning'],by[(s,'grating')]['tuning']) for s in ('global','root_scoped')}
 b_delta={s:delta(by[(s,'blank')]['b_tuning'],by[(s,'grating')]['b_tuning']) for s in ('global','root_scoped')}
 a_replay={s:delta(by[(s,'blank')]['tuning'],by[(s,'blank_replay')]['tuning']) for s in ('global','root_scoped')}
 b_replay={s:delta(by[(s,'blank')]['b_tuning'],by[(s,'blank_replay')]['b_tuning']) for s in ('global','root_scoped')}
 osi_a=all(np.allclose(c['osi_per_unit'],[osi(x) for x in c['tuning']],atol=TOL,rtol=0) for c in by.values())
 osi_b=all(np.allclose(c['b_osi_per_unit'],[osi(x) for x in c['b_tuning']],atol=TOL,rtol=0) for c in by.values())
 work_ok=True;work_count=0;retry_count=0;maxwork=0
 weight_audits=[]
 for s in scopes:
  w=s['presentation_work'];work_count+=len(w);retry_count+=sum(x['intermediate_budget_hits'] for x in w)
  maxwork=max(maxwork,max(x['cumulative_progress'] for x in w))
  work_ok &= len(w)==4880 and all(x['final_status'] in ('fixed_point','repeated_graph_state') and x['attempt_count']==x['intermediate_budget_hits']+1 and x['cumulative_progress']<=1_600_000 for x in w)
  for c in s['contexts']:
   for side in ('a','b'):
    before=np.asarray(c[f'{side}_readout_weight_before'],float);after=np.asarray(c[f'{side}_readout_weight_after'],float)
    shape_ok=before.shape==after.shape and before.ndim==2 and before.shape[0]==16
    md=float(np.max(np.abs(before-after))) if shape_ok else float('inf')
    weight_audits.append({'scope':s['scope'],'context':c['context'],'side':side,'shape':list(before.shape),'max_abs_delta':md,'zero_drift':shape_ok and md==0.0})
 checks={
  'driver_fixture_gates_pass':d.get('pass') is True,
  'source_stable':d['checks'].get('source_stable') is True,
  'two_scopes_three_contexts':set(by)==contexts,
  'A_and_B_tuning_shapes_16_by_12':all(np.asarray(c['tuning']).shape==(16,12) and np.asarray(c['b_tuning']).shape==(16,12) for c in by.values()),
  'all_A_B_curves_finite':all(np.isfinite(c[k]).all() for c in by.values() for k in ('tuning','b_tuning')),
  'A_OSI_independently_recomputed':osi_a,
  'B_OSI_independently_recomputed':osi_b,
  'all_presentations_settled_under_cumulative_bound':work_ok,
  'all_A_B_readout_weights_unchanged':len(weight_audits)==12 and all(x['zero_drift'] for x in weight_audits),
  'A_blank_replay_exact':all(v==0.0 for v in a_replay.values()),
  'B_blank_replay_exact':all(v==0.0 for v in b_replay.values()),
  'B_grating_reaches_B_SUnits':all(np.max(by[(s,'grating')]['b_tuning'])>1e-9 and sum(x>1e-9 for x in by[(s,'grating')]['joint_b_unit_state_during_a_readout']['rates'])>0 for s in ('global','root_scoped')),
  'B_input_frame_reaches_retinal_cells':all(by[(s,'blank')]['joint_b_bursting_after_a_readout']==0 and by[(s,'grating')]['joint_b_bursting_after_a_readout']==128 and by[(s,'grating')]['b_frame_active_pixels']==128 for s in ('global','root_scoped')),
 }
 fixture_checks={k:v for k,v in checks.items() if k not in ('B_grating_reaches_B_SUnits',)}
 out={'schema_version':1,'raw_sha256':sha(RAW),'checks':checks,'fixture_valid':all(fixture_checks.values()),
  'a_global_blank_to_grating_max_abs_delta':a_delta,'b_global_blank_to_grating_max_abs_delta':b_delta,
  'a_root_scoped_blank_to_grating_max_abs_delta':a_delta['root_scoped'],'b_root_scoped_blank_to_grating_max_abs_delta':b_delta['root_scoped'],
  'A_blank_replay_max_abs_delta':a_replay,'B_blank_replay_max_abs_delta':b_replay,
  'mean_osi':{},
  'weight_audits':weight_audits,'work_audit':{'presentation_records':work_count,'budget_retry_invocations':retry_count,'max_cumulative_progress_per_presentation':maxwork},
  'interpretation':'B SUnit activity validates the intervention route if its activity gate passes. A null A response contrast remains a negative outcome for the registered global-interference prediction, not general evidence of scope safety.'}
 # Fix labels to be legible and stable in the serialized report.
 out['mean_osi']={f'{s}/{c}/A':float(np.mean(by[(s,c)]['osi_per_unit'])) for s,c in by}|{f'{s}/{c}/B':float(np.mean(by[(s,c)]['b_osi_per_unit'])) for s,c in by}
 out['pass']=all(checks.values())
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'fixture_valid':out['fixture_valid'],'pass':out['pass'],'checks':checks,'A_delta':a_delta,'B_delta':b_delta,'work_audit':out['work_audit']},indent=2))
 if not out['fixture_valid']:raise SystemExit('v1.4 fixture analysis failed')
if __name__=='__main__':main()
