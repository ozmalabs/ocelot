#!/usr/bin/env python3
"""Supplemental post-hoc analysis of rate-rule ordering and refresh counterfactual."""
import hashlib,json,statistics
from pathlib import Path
import numpy as np
from analyze_substrate_natural_image_act_rate_phase_diagnostic_v1 import phase_state,relerr
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/natural_image_act_rate_phase_diagnostic_v1_20260929_lock.json'
OUT=ROOT/'evaluation/reports/natural_image_act_rate_phase_diagnostic_v1_1_analysis_20260929.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 data=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];rows=[];orders=[]
 for w in data['workers']:
  arms={i['label']:i['traced'] for i in w['inputs']};states={label:{phase:phase_state(arm,phase,w['seed'],w['scope']) for phase in ('after_rate','after_settle','final')} for label,arm in arms.items()}
  for label,arm in arms.items():
   events=[e for rep in arm['trace_reports'] for e in rep['events']]
   rate_pos=[i for i,e in enumerate(events) if e['rule_name']=='oo_sunit_rate']
   settle_name='st_settle' if w['scope']=='global' else 'st_settle_root_scoped_benchmark'
   settle_pos=[i for i,e in enumerate(events) if e['rule_name']==settle_name]
   if rate_pos and settle_pos:
    orders.append({'seed':w['seed'],'scope':w['scope'],'input':label,'rate_event_order':rate_pos[-1],
      'last_settle_event_order':settle_pos[-1],'rate_precedes_last_settle':rate_pos[-1]<settle_pos[-1],
      'rate_progress_step':events[rate_pos[-1]]['progress_step'],'last_settle_progress_step':events[settle_pos[-1]]['progress_step']})
  ev=states['original']['after_rate'];rv=states['rotated_180']['after_rate']
  residual=[]
  for label in ('original','rotated_180','blank'):
   st=states[label]['after_rate']
   residual.extend(np.abs(np.asarray(st['rate'])-np.maximum(np.asarray(st['act'])-np.asarray(st['theta']),0)).tolist())
  final={label:states[label]['final'] for label in ('original','rotated_180','blank')}
  refreshed={label:np.maximum(np.asarray(st['act'],float)-np.asarray(st['theta'],float),0) for label,st in final.items()}
  d=refreshed['original']-refreshed['blank'];dr=refreshed['rotated_180']-refreshed['blank']
  actual_d=np.asarray(final['original']['rate'])-np.asarray(final['blank']['rate'])
  rows.append({'seed':w['seed'],'scope':w['scope'],'post_rate_equation_max_abs_residual':float(max(residual,default=0)),
   'post_rate_matching_stamp_nodes':int(np.sum(np.asarray(ev['act_step'])==np.asarray(ev['rate_step']))),
    'final_actual_rate_delta_l1':float(np.abs(actual_d).sum()),
    'counterfactual_refreshed_rate_delta_l1_original':float(np.abs(d).sum()),
    'counterfactual_refreshed_rate_delta_l1_rotated':float(np.abs(dr).sum()),
    'counterfactual_refreshed_equivariance_relative_l1':relerr(np.rot90(d.reshape(4,4),2),dr.reshape(4,4)),
    'counterfactual_refreshed_identity_relative_l1':relerr(d,dr),
    'counterfactual_permutation_wins':relerr(np.rot90(d.reshape(4,4),2),dr.reshape(4,4))<relerr(d,dr)})
 summary={}
 for scope in ('global','root_scoped'):
  rr=[r for r in rows if r['scope']==scope]
  oo=[r for r in orders if r['scope']==scope]
  summary[scope]={'checkpoint_count':len(rr),'rate_precedes_last_settle_count':int(sum(x['rate_precedes_last_settle'] for x in oo)),
    'calls_with_rule_equation_residual_above_1e_9':int(sum(x['post_rate_equation_max_abs_residual']>1e-9 for x in rr)),
    'counterfactual_refreshed_permutation_wins':int(sum(x['counterfactual_permutation_wins'] for x in rr)),
    'median_counterfactual_refreshed_equivariance_error':statistics.median(x['counterfactual_refreshed_equivariance_relative_l1'] for x in rr),
    'median_counterfactual_refreshed_identity_error':statistics.median(x['counterfactual_refreshed_identity_relative_l1'] for x in rr)}
 out={'run_id':'natural_image_act_rate_phase_diagnostic_v1_20260929','analysis_version':'v1.1_supplemental_posthoc',
  'raw_capture_locked_inputs_match':data.get('locked_inputs')==lock,'supplemental_analyzer_sha256':sha(__file__),
  'event_order_records':orders,'checkpoint_diagnostics':rows,'summary':summary,
  'interpretation':'The rate rule computes its declared equation exactly at the observed post-rule snapshots, but its last observed invocation precedes the last settlement invocation in every recorded input. Settlement therefore continues to change act after rate is stamped for the step. The counterfactual refreshed rates are computed offline from final act and theta using the seed equation; no graph is mutated and this is not a measured intervention. Root-scoped results favor the rotation permutation in 3/3 checkpoint cells on this one image; global refreshed rates are degenerate in two of three cells. Theta is held fixed across the paired input presentations, so rectification need not preserve spatial equivariance.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'raw_lock_matches':out['raw_capture_locked_inputs_match'],'summary':summary},indent=2))
if __name__=='__main__':main()
