#!/usr/bin/env python3
"""Analyze exact write scope, equation, and spatial task effect of rate refresh."""
import hashlib,json,math,statistics
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/natural_image_rate_refresh_intervention_v1_20260929_raw.json'
LOCK=ROOT/'evaluation/substrate_capability/natural_image_rate_refresh_intervention_v1_20260929_lock.json'
OUT=ROOT/'evaluation/reports/natural_image_rate_refresh_intervention_v1_20260929_analysis.json'
SEEDS=(20260935,20260936,20260937);SCOPES=('global','root_scoped');IMAGE='101085.jpg'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame():return np.asarray(Image.open(ROOT/'data/vision_curriculum/BSDS300/images/test'/IMAGE).convert('L').resize((16,16),Image.Resampling.BILINEAR),np.float32)/255.0
def relerr(a,b):return float(np.abs(np.asarray(a)-np.asarray(b)).sum()/(np.abs(b).sum()+1e-9))
def main():
 data=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];workers=data['workers'];img=frame();rot=np.rot90(img,2).copy();blank=np.zeros((16,16),np.float32)
 expected={(s,c,l) for s in SEEDS for c in SCOPES for l in ('original','rotated_180','blank')}
 keys={(w['seed'],w['scope'],w['label']) for w in workers};matrix={}
 eq_res=[];valid=True
 for w in workers:
  input_img={'original':img,'rotated_180':rot,'blank':blank}[w['label']]
  valid &= w['input_sha256']==hashlib.sha256(input_img.tobytes()).hexdigest()
  valid &= w['checkpoint_graph_sha256']==lock['checkpoint_graph_sha256'][str(w['seed'])]
  d=w['intervention_graph_diff'];valid &= d['node_inventory_equal'] and d['edge_inventory_equal'] and d['only_allowed_target_attrs']
  valid &= all(c['node_id'] in w['target_unit_ids'] and c['key'] in ('rate','rate_step') for c in d['attr_changes'])
  valid &= w['act_unchanged'] and w['delivered_pixels_exact'] and w['intervention_fired'] and w['step_return']>0
  before=w['default_state'];after=w['refreshed_state']
  valid &= before['act']==after['act'] and before['theta']==after['theta'] and before['act_step']==after['act_step']
  valid &= all(abs(a-max(v-t,0.0))<=1e-9 for a,v,t in zip(after['rate'],after['act'],after['theta']))
  valid &= all(abs(st-w['root_step'])<1e-9 for st in after['rate_step'])
  eq_res.extend(abs(a-max(v-t,0.0)) for a,v,t in zip(after['rate'],after['act'],after['theta']))
  matrix[(w['seed'],w['scope'],w['label'])]=w
 scores={}
 for scope in SCOPES:
  for readout in ('default','refreshed'):
   errors=[];identity=[];delta=[];wins=0
   for seed in SEEDS:
    o=matrix[(seed,scope,'original')][readout+'_state']['rate']
    r=matrix[(seed,scope,'rotated_180')][readout+'_state']['rate']
    b=matrix[(seed,scope,'blank')][readout+'_state']['rate']
    od=np.asarray(o)-np.asarray(b);rd=np.asarray(r)-np.asarray(b)
    e=relerr(np.rot90(od.reshape(4,4),2),rd.reshape(4,4));i=relerr(od,rd)
    errors.append(e);identity.append(i);delta.append((float(np.abs(od).sum()),float(np.abs(rd).sum())))
    wins+=e<i
   scores[f'{scope}:{readout}']={'checkpoint_count':3,'permutation_wins':wins,
     'median_expected_permutation_error':statistics.median(errors),'median_identity_error':statistics.median(identity),
     'original_blank_delta_l1_by_seed':[x[0] for x in delta],'rotated_blank_delta_l1_by_seed':[x[1] for x in delta]}
 checks={'worker_matrix_complete':len(workers)==18 and keys==expected,
   'capture_lock_matches':data.get('locked_inputs')==lock,'source_stable':data.get('source_stable') is True,
   'checkpoint_hashes_and_images_valid':valid,
   'exact_intended_write_footprint':all(w['intervention_graph_diff']['only_allowed_target_attrs'] and w['intervention_graph_diff']['node_inventory_equal'] and w['intervention_graph_diff']['edge_inventory_equal'] for w in workers),
   'activation_unchanged':all(w['act_unchanged'] and w['default_state']['act']==w['refreshed_state']['act'] for w in workers),
   'equation_and_stamp_oracle':all(abs(a-max(v-t,0.0))<=1e-9 for w in workers for a,v,t in zip(w['refreshed_state']['rate'],w['refreshed_state']['act'],w['refreshed_state']['theta'])) and all(abs(st-w['root_step'])<1e-9 for w in workers for st in w['refreshed_state']['rate_step'])}
 out={'run_id':data['run_id'],'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),'integrity_pass':all(checks.values()),
  'workers':len(workers),'rate_equation_max_abs_residual':max(eq_res,default=None),'spatial_task_scores':scores,
  'claim_boundary':'Post-settlement invocation of the existing rate rule after a one-step natural-image input. It is an explicit intervention, not a production scheduler change; one image and three adapted checkpoints only.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':len(checks),'spatial_task_scores':scores},indent=2))
 if not out['integrity_pass']:raise SystemExit('rate-refresh intervention integrity gate failed')
if __name__=='__main__':main()
