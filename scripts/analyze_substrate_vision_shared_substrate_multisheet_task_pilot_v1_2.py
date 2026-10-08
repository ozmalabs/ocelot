#!/usr/bin/env python3
"""Independent analyzer for shared-substrate multi-sheet task pilot v1.2."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_2_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_2_analysis_20260927.json'
TOL=1e-10
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def osi(curve):
 x=np.asarray(curve,dtype=float);j=int(np.argmax(x));jo=(j+len(x)//2)%len(x);den=x[j]+x[jo]
 return float((x[j]-x[jo])/den) if den>1e-9 else 0.0
def delta(a,b):return float(np.max(np.abs(np.asarray(a,dtype=float)-np.asarray(b,dtype=float))))
def main():
 d=json.loads(RAW.read_text());scopes=d['worker']['scopes'];by={(s['scope'],c['context']):c for s in scopes for c in s['contexts']}
 audits=[]
 for (scope,context),c in by.items():
  before=np.asarray(c['readout_weight_before'],dtype=float);after=np.asarray(c['readout_weight_after'],dtype=float)
  valid=before.shape==after.shape and before.ndim==2 and before.shape[0]==16
  md=float(np.max(np.abs(before-after))) if valid else float('inf')
  audits.append({'scope':scope,'context':context,'shape':list(before.shape),'max_abs_delta':md,'zero_drift':valid and md==0.0})
 scope_delta={s:delta(by[(s,'blank')]['tuning'],by[(s,'grating')]['tuning']) for s in ('global','root_scoped')}
 replay={s:delta(by[(s,'blank')]['tuning'],by[(s,'blank_replay')]['tuning']) for s in ('global','root_scoped')}
 osi_ok=all(np.allclose(np.asarray(c['osi_per_unit']),np.asarray([osi(x) for x in c['tuning']]),atol=TOL,rtol=0) for c in by.values())
 checks={
  'driver_gates_pass':d.get('pass') is True,
  'two_scopes_three_contexts':set(by)=={(s,c) for s in ('global','root_scoped') for c in ('blank','blank_replay','grating')},
  'all_tuning_shape_16_by_12':all(np.asarray(c['tuning']).shape==(16,12) for c in by.values()),
  'finite_nonzero_outputs':all(np.isfinite(np.asarray(c['tuning'])).all() and np.max(np.asarray(c['tuning']))>0 for c in by.values()),
  'osi_independently_recomputed':osi_ok,
  'zero_weight_drift':len(audits)==6 and all(a['zero_drift'] for a in audits),
  'blank_restore_replay_exact':all(v==0.0 for v in replay.values()),
  'root_scoped_a_response_invariant':scope_delta['root_scoped']<=TOL,
  'global_fold_a_response_changes':scope_delta['global']>1e-8,
  'b_stimulus_control_changes_inputs':all(by[(s,'blank')]['b_frame_active_pixels']==0 and by[(s,'grating')]['b_frame_active_pixels']>0 and by[(s,'grating')]['b_bursting_after_readout']==by[(s,'grating')]['b_frame_active_pixels'] for s in ('global','root_scoped')),
 }
 result={'schema_version':1,'raw_sha256':sha(RAW),'checks':checks,'scope_a_tuning_max_abs_delta':scope_delta,'blank_replay_max_abs_delta':replay,'weight_audits':audits,'mean_osi_by_scope_context':{f'{s}/{c}':float(np.mean(by[(s,c)]['osi_per_unit'])) for s,c in by},'pass':all(checks.values()),'interpretation':'A pass supports the registered B-to-A interference contrast for one shared-substrate two-sheet fixture. It does not establish prevalence, scaling, or general scope safety.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'scope_a_tuning_max_abs_delta':scope_delta,'blank_replay_max_abs_delta':replay},indent=2))
 if not result['pass']:raise SystemExit('independent v1.2 analysis failed')
if __name__=='__main__':main()
