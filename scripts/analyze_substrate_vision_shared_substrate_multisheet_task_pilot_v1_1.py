#!/usr/bin/env python3
"""Independent analyzer for the shared-substrate multi-sheet task pilot."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_1_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_1_analysis_20260927.json'
TOL=1e-10

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def osi(curve):
    x=np.asarray(curve,dtype=float);j=int(np.argmax(x));jo=(j+len(x)//2)%len(x);den=x[j]+x[jo]
    return float((x[j]-x[jo])/den) if den>1e-9 else 0.0
def delta(a,b): return float(np.max(np.abs(np.asarray(a,dtype=float)-np.asarray(b,dtype=float))))

def main():
    d=json.loads(RAW.read_text());arms=d['worker']['arms'];by={(a['scope'],a['b_condition']):a for a in arms}
    audits=[]
    for a in arms:
        before=np.asarray(a['readout_weight_before'],dtype=float);after=np.asarray(a['readout_weight_after'],dtype=float)
        valid=before.shape==after.shape and before.ndim==2 and before.shape[0]==16
        md=float(np.max(np.abs(before-after))) if valid else float('inf')
        audits.append({'scope':a['scope'],'b_condition':a['b_condition'],'shape':list(before.shape),'max_abs_delta':md,'zero_drift':valid and md==0.0})
    scope_delta={scope:delta(by[(scope,'blank')]['tuning'],by[(scope,'grating')]['tuning']) for scope in ('global','root_scoped')}
    osi_recompute=all(np.allclose(np.asarray(a['osi_per_unit']),np.asarray([osi(x) for x in a['tuning']]),atol=TOL,rtol=0) for a in arms)
    preprobe_same=all(np.array_equal(np.asarray(by[(scope,'blank')]['readout_weight_before']),np.asarray(by[(scope,'grating')]['readout_weight_before'])) for scope in ('global','root_scoped'))
    checks={
        'driver_fixture_and_provenance_gates_pass':d.get('pass') is True,
        'four_scope_context_arms':set(by)=={('global','blank'),('global','grating'),('root_scoped','blank'),('root_scoped','grating')},
        'all_arm_tuning_shape_16_by_12':all(np.asarray(a['tuning']).shape==(16,12) for a in arms),
        'all_arm_outputs_finite_and_nonzero':all(np.isfinite(np.asarray(a['tuning'])).all() and np.max(np.asarray(a['tuning']))>0 for a in arms),
        'osi_independently_recomputed':osi_recompute,
        'zero_readout_weight_drift':len(audits)==4 and all(x['zero_drift'] for x in audits),
        'same_preprobe_state_across_b_context_within_scope':preprobe_same,
        'b_stimulus_control_changes_inputs':by[('global','blank')]['b_frame_active_pixels']==0 and by[('global','grating')]['b_frame_active_pixels']>0,
        'root_scoped_a_response_invariant':scope_delta['root_scoped']<=TOL,
        'global_fold_a_response_changes':scope_delta['global']>1e-8,
    }
    payload={'schema_version':1,'raw_sha256':sha(RAW),'checks':checks,'scope_a_tuning_max_abs_delta':scope_delta,'weight_audits':audits,
        'osi_by_arm':{f'{s}/{b}':float(np.mean(by[(s,b)]['osi_per_unit'])) for s,b in by},
        'pass':all(checks.values()),
        'interpretation':'A pass supports the registered B-to-A interference contrast on one shared-substrate two-sheet visual fixture. A failure of the directional contrast is a meaningful negative or underpowered pilot, not evidence of global scope safety in general.'}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'scope_a_tuning_max_abs_delta':scope_delta,'osi_by_arm':payload['osi_by_arm']},indent=2))
    if not payload['pass']: raise SystemExit('independent shared-substrate task analysis failed')
if __name__=='__main__':main()
